from __future__ import annotations

import os
import subprocess

from shadowgen_contracts import WorkerVersionInfo


def _git_value(args: list[str], cwd: str) -> str | None:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
    except Exception:
        return None
    value = completed.stdout.strip()
    return value or None


def collect_worker_version_info(repo_path: str, image_tag: str | None, container_name: str | None) -> WorkerVersionInfo:
    effective_repo_path = repo_path if os.path.exists(repo_path) else os.getcwd()
    return WorkerVersionInfo(
        git_branch=_git_value(["rev-parse", "--abbrev-ref", "HEAD"], effective_repo_path),
        git_commit=_git_value(["rev-parse", "HEAD"], effective_repo_path),
        image_tag=image_tag,
        container_name=container_name or os.environ.get("HOSTNAME"),
    )
