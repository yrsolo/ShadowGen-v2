from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import docker

from shadowgen_application.ports import RuntimeConfigStorePort, WorkerActionStorePort
from shadowgen_contracts import LocalRuntimeConfig, WorkerActionRecord

from shadowgen_adapters.runtime import build_runtime_adapters
from shadowgen_worker.config import WorkerConfig
from shadowgen_worker.metadata import collect_worker_version_info
from shadowgen_worker.state import WorkerStateService


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _summarize(text: str | None, limit: int = 1000) -> str | None:
    if not text:
        return None
    return text[:limit]


def _encode_env_payload(env_items: list[str]) -> str:
    return json.dumps(env_items)


@dataclass(slots=True)
class WorkerActionExecutor:
    config: WorkerConfig
    runtime_config_store: RuntimeConfigStorePort
    worker_action_store: WorkerActionStorePort
    state_service: WorkerStateService

    def execute(self, action: WorkerActionRecord) -> WorkerActionRecord:
        action.started_at = utc_now()
        action.status = "running"
        self.worker_action_store.update(action)
        self.state_service.action_state(action)

        try:
            match action.action:
                case "clear_runtime_override":
                    self.runtime_config_store.update(LocalRuntimeConfig(legacy_ml_base_url=None))
                    action.summary = "Runtime ML override cleared."
                    action.status = "succeeded"
                case "restart_worker_process":
                    action.summary = "Worker process restart requested."
                    action.status = "succeeded"
                    self.worker_action_store.update(action)
                    self.state_service.action_state(action)
                    self._restart_process_async()
                    return action
                case "restart_container":
                    if not self.config.worker_self_manage_enabled:
                        raise RuntimeError("Container self-management is disabled.")
                    action.summary = "Container restart requested."
                    action.status = "succeeded"
                    self.worker_action_store.update(action)
                    self.state_service.action_state(action)
                    self._restart_container_async()
                    return action
                case "git_update_rebuild_restart":
                    if not self.config.worker_self_manage_enabled:
                        raise RuntimeError("Container self-management is disabled.")
                    self._spawn_update_helper(action.command_id)
                    action.summary = "Detached update helper launched."
                    action.status = "running"
                    self.worker_action_store.update(action)
                    self.state_service.action_state(action)
                    return action
                case _:
                    raise RuntimeError(f"Unsupported action '{action.action}'.")
        except Exception as exc:
            action.status = "failed"
            action.error_text = str(exc)
            action.summary = f"Action failed: {exc}"
        finally:
            if action.status in {"succeeded", "failed"}:
                action.finished_at = utc_now()
                self.worker_action_store.update(action)
                self.state_service.action_state(action)
        return action

    def _restart_process_async(self) -> None:
        def restart() -> None:
            time.sleep(1.0)
            os.execv(sys.executable, [sys.executable, "-m", "shadowgen_worker.main"])

        threading.Thread(target=restart, daemon=True).start()

    def _restart_container_async(self) -> None:
        def restart() -> None:
            time.sleep(1.0)
            client = docker.from_env()
            container = client.containers.get(self.config.worker_container_name)
            container.restart(timeout=1)

        threading.Thread(target=restart, daemon=True).start()

    def _spawn_update_helper(self, command_id: str) -> None:
        client = docker.from_env()
        self_container = client.containers.get(os.environ.get("HOSTNAME", self.config.worker_container_name))
        workspace_mount = next((item for item in self_container.attrs.get("Mounts", []) if item.get("Destination") == self.config.worker_workspace_mount_dest), None)
        socket_mount = next((item for item in self_container.attrs.get("Mounts", []) if item.get("Destination") == "/var/run/docker.sock"), None)
        if workspace_mount is None or socket_mount is None:
            raise RuntimeError("Worker container must be started with workspace and docker socket mounts.")

        env_payload = _encode_env_payload(
            [
                item
                for item in self_container.attrs.get("Config", {}).get("Env", [])
                if not item.startswith(("HOSTNAME=", "PATH=", "PWD=", "SHLVL="))
            ]
        )

        helper_name = f"{self.config.worker_container_name}-helper-{command_id[:8]}"
        client.containers.run(
            self.config.worker_image_tag,
            command=["python", "-m", "shadowgen_worker.self_manage_helper"],
            name=helper_name,
            detach=True,
            remove=True,
            environment={
                "WORKER_HELPER_ACTION_ID": command_id,
                "WORKER_HELPER_TARGET_CONTAINER": self.config.worker_container_name,
                "WORKER_HELPER_TARGET_IMAGE": self.config.worker_image_tag,
                "WORKER_HELPER_TARGET_HOST_PORT": str(self.config.worker_control_host_port),
                "WORKER_HELPER_ENV_PAYLOAD": env_payload,
                "WORKER_HELPER_REPO_SOURCE": workspace_mount["Source"],
                "WORKER_HELPER_WORKSPACE_DEST": self.config.worker_workspace_mount_dest,
            },
            volumes={
                workspace_mount["Source"]: {"bind": self.config.worker_workspace_mount_dest, "mode": "rw"},
                socket_mount["Source"]: {"bind": "/var/run/docker.sock", "mode": "rw"},
            },
            working_dir=self.config.worker_workspace_mount_dest,
        )


def run_self_manage_helper() -> int:
    command_id = os.environ["WORKER_HELPER_ACTION_ID"]
    target_container_name = os.environ["WORKER_HELPER_TARGET_CONTAINER"]
    target_image = os.environ["WORKER_HELPER_TARGET_IMAGE"]
    host_port = int(os.environ["WORKER_HELPER_TARGET_HOST_PORT"])
    repo_source = os.environ["WORKER_HELPER_REPO_SOURCE"]
    workspace_dest = os.environ["WORKER_HELPER_WORKSPACE_DEST"]
    env_items = json.loads(os.environ["WORKER_HELPER_ENV_PAYLOAD"])

    config = WorkerConfig()
    runtime = build_runtime_adapters(
        state_backend=config.state_backend,
        queue_backend=config.queue_backend,
        state_dir=config.state_dir,
        s3_endpoint_url=config.s3_endpoint_url,
        s3_bucket=config.s3_bucket,
        s3_region=config.s3_region,
        s3_access_key_id=config.s3_access_key_id,
        s3_secret_access_key=config.s3_secret_access_key,
        s3_prefix=config.s3_prefix,
        ymq_endpoint=config.ymq_endpoint,
        ymq_queue_url=config.ymq_queue_url,
        ymq_region=config.ymq_region,
        ymq_access_key_id=config.ymq_access_key_id,
        ymq_secret_access_key=config.ymq_secret_access_key,
        queue_poll_wait_sec=config.queue_poll_wait_sec,
    )
    state_service = WorkerStateService(
        worker_state_store=runtime.worker_state_store,
        runtime_config_store=runtime.runtime_config_store,
        config_legacy_base_url=config.legacy_ml_base_url,
        version_info=collect_worker_version_info(workspace_dest, target_image, target_container_name),
    )
    action = next((item for item in runtime.worker_action_store.list_recent(limit=50) if item.command_id == command_id), None)
    if action is None:
        raise RuntimeError(f"Action '{command_id}' not found.")

    try:
        git_pull = subprocess.run(["git", "pull"], cwd=workspace_dest, capture_output=True, text=True, check=True)
        client = docker.from_env()
        image, build_logs = client.images.build(path=workspace_dest, dockerfile="apps/worker/Dockerfile", tag=target_image, rm=True)
        _ = image
        target = client.containers.get(target_container_name)
        target.stop(timeout=3)
        target.remove(force=True)
        client.containers.run(
            target_image,
            command=["python", "-m", "shadowgen_worker.main"],
            name=target_container_name,
            detach=True,
            remove=True,
            environment={item.split("=", 1)[0]: item.split("=", 1)[1] for item in env_items if "=" in item},
            volumes={
                repo_source: {"bind": workspace_dest, "mode": "rw"},
                "/var/run/docker.sock": {"bind": "/var/run/docker.sock", "mode": "rw"},
            },
            ports={"8081/tcp": host_port},
            working_dir=workspace_dest,
        )
        action.status = "succeeded"
        action.summary = "Worker container rebuilt from git and restarted."
        action.log_excerpt = _summarize(git_pull.stdout + "\n" + "".join(str(item) for item in build_logs))
    except Exception as exc:
        action.status = "failed"
        action.error_text = str(exc)
        action.summary = f"Update helper failed: {exc}"
    action.finished_at = utc_now()
    runtime.worker_action_store.update(action)
    state_service.action_state(action)
    return 0 if action.status == "succeeded" else 1
