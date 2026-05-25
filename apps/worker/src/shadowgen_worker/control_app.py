from __future__ import annotations

from datetime import datetime, timezone
from html import escape

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from shadowgen_application.use_cases.create_worker_action import CreateWorkerActionUseCase
from shadowgen_contracts import CreateWorkerActionRequest, JobStatus


def _duration_ms(job) -> int | None:
    if job.started_at is None or job.finished_at is None:
        return None
    return int((job.finished_at - job.started_at).total_seconds() * 1000)


def _format_timestamp_seconds(value: datetime | None) -> str | None:
    if value is None:
        return None
    local_value = value.astimezone()
    timezone_name = local_value.tzname() or "local"
    return local_value.strftime(f"%Y-%m-%d %H:%M:%S {timezone_name}")


def _has_preview(job) -> bool:
    if job.result is None or not job.result.images:
        return False
    return True


def _copyable_job_id(job_id: str) -> str:
    return job_id


def _job_preview_url(job) -> str | None:
    return f"/api/jobs/{job.job_id}/preview" if _has_preview(job) else None


def create_worker_control_app(*, config, runtime, state_service, version_info) -> FastAPI:
    app = FastAPI(title="ShadowGen Worker Control", version="0.1.0")
    create_action = CreateWorkerActionUseCase(worker_action_store=runtime.worker_action_store)

    def require_token(x_worker_token: str | None) -> None:
        if x_worker_token != config.worker_control_token:
            raise HTTPException(status_code=401, detail="Invalid worker control token.")

    def status_payload() -> dict:
        state = runtime.worker_state_store.get()
        recent_jobs = runtime.job_repository.list_recent(limit=20)
        recent_job_cards = [
            {
                "job_id": job.job_id,
                "status": job.status.value,
                "created_at": job.created_at,
                "created_at_display": _format_timestamp_seconds(job.created_at),
                "updated_at": job.updated_at,
                "updated_at_display": _format_timestamp_seconds(job.updated_at),
                "finished_at": job.finished_at,
                "finished_at_display": _format_timestamp_seconds(job.finished_at),
                "duration_ms": _duration_ms(job),
                "cache_status": job.cache_status,
                "reused_existing_job": job.reused_existing_job,
                "preview_url": _job_preview_url(job),
                "error_message": job.error.message if job.error else None,
                "trace": [stage.model_dump(mode="json") for stage in job.trace],
            }
            for job in recent_jobs[:10]
        ]
        recent_completed = [
            {
                "job_id": job.job_id,
                "status": job.status.value,
                "duration_ms": _duration_ms(job),
                "finished_at": job.finished_at,
                "finished_at_display": _format_timestamp_seconds(job.finished_at),
                "preview_url": f"/api/jobs/{job.job_id}/preview" if _has_preview(job) else None,
            }
            for job in recent_jobs
            if job.status == JobStatus.SUCCEEDED
        ][:10]
        recent_failures = [
            {
                "job_id": job.job_id,
                "status": job.status.value,
                "error_message": job.error.message if job.error else None,
                "finished_at": job.finished_at,
                "finished_at_display": _format_timestamp_seconds(job.finished_at),
            }
            for job in recent_jobs
            if job.status == JobStatus.FAILED
        ][:10]
        actions = [item.model_dump(mode="json") for item in runtime.worker_action_store.list_recent(limit=10)]
        heartbeat_age_sec = None
        if state.updated_at is not None:
            heartbeat_age_sec = int((datetime.now(timezone.utc) - state.updated_at).total_seconds())
        return {
            "worker": state.model_dump(mode="json"),
            "heartbeat_age_sec": heartbeat_age_sec,
            "queue": runtime.job_queue.diagnostics().model_dump(mode="json"),
            "runtime_config": runtime.runtime_config_store.get().model_dump(mode="json"),
            "recent_completed_jobs": recent_completed,
            "recent_jobs": recent_job_cards,
            "recent_failures": recent_failures,
            "recent_actions": actions,
            "version": version_info.model_dump(mode="json"),
            "effective_legacy_base_url": state.effective_legacy_base_url or state_service.effective_legacy_base_url(),
            "self_management": {
                "enabled": config.worker_self_manage_enabled,
                "mode": "self-managed" if config.worker_self_manage_enabled else "self-contained",
            },
            "storage": {
                "backend": config.state_backend,
                "bucket": config.s3_bucket,
                "prefix": config.s3_prefix if config.state_backend == "s3" else None,
            },
        }

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/api/status")
    def api_status() -> dict:
        return status_payload()

    @app.get("/api/jobs/recent")
    def api_jobs_recent() -> list[dict]:
        return status_payload()["recent_completed_jobs"]

    @app.get("/api/jobs/{job_id}/preview")
    def api_job_preview(job_id: str):
        job = runtime.job_repository.get(job_id)
        if job is None or job.result is None or not job.result.images:
            raise HTTPException(status_code=404, detail="Preview not found.")
        image = job.result.images[0]
        if image.url:
            return RedirectResponse(image.url)
        try:
            image_bytes = runtime.asset_store.get_bytes(image.asset_id)
        except Exception as exc:
            raise HTTPException(status_code=404, detail="Preview not found.") from exc
        return Response(content=image_bytes, media_type=image.mime_type)

    @app.get("/api/failures/recent")
    def api_failures_recent() -> list[dict]:
        return status_payload()["recent_failures"]

    @app.get("/api/actions/recent")
    def api_actions_recent() -> list[dict]:
        return status_payload()["recent_actions"]

    @app.post("/api/actions/restart")
    def api_restart(payload: CreateWorkerActionRequest, x_worker_token: str | None = Header(default=None)) -> dict:
        require_token(x_worker_token)
        command = create_action.execute(action=payload.action, requested_by="local-ui", validation_marker="local-token")
        return {"command": command.model_dump(mode="json")}

    @app.post("/api/actions/update")
    def api_update(payload: CreateWorkerActionRequest, x_worker_token: str | None = Header(default=None)) -> dict:
        require_token(x_worker_token)
        command = create_action.execute(action=payload.action, requested_by="local-ui", validation_marker="local-token")
        return {"command": command.model_dump(mode="json")}

    @app.post("/api/actions/clear-override")
    def api_clear_override(payload: CreateWorkerActionRequest, x_worker_token: str | None = Header(default=None)) -> dict:
        require_token(x_worker_token)
        command = create_action.execute(action=payload.action, requested_by="local-ui", validation_marker="local-token")
        return {"command": command.model_dump(mode="json")}

    @app.get("/", response_class=HTMLResponse)
    def dashboard() -> str:
        payload = status_payload()
        recent_jobs_html = "".join(
            "<details class='job-card'>"
            + "<summary>"
            + (
                f"<img class='job-preview' src='{escape(item['preview_url'])}' alt='Result preview for {escape(item['job_id'])}' />"
                if item["preview_url"]
                else "<div class='job-preview job-preview-empty'>no preview</div>"
            )
            + "<div class='job-meta'>"
            + f"<div><strong>{escape(item['status'])}</strong> <span class='pill'>{escape(item['cache_status'] or 'fresh')}</span></div>"
            + f"<div class='muted'>Created: {escape(item['created_at_display'] or 'n/a')}</div>"
            + f"<div class='muted'>Finished: {escape(item['finished_at_display'] or item['updated_at_display'] or 'n/a')}</div>"
            + f"<div class='muted'>Duration: {item['duration_ms'] if item['duration_ms'] is not None else 'n/a'} ms</div>"
            + "</div>"
            + "</summary>"
            + f"<button class='copy-button' onclick=\"navigator.clipboard.writeText('{escape(_copyable_job_id(item['job_id']))}')\">Copy job id</button>"
            + (
                "<div class='trace'>"
                + "".join(
                    "<div class='trace-row'>"
                    + f"<span>{escape(stage.get('name', 'stage'))}</span>"
                    + f"<strong>{escape(stage.get('status', 'unknown'))}</strong>"
                    + f"<small>{escape(str(stage.get('duration_ms') if stage.get('duration_ms') is not None else 'n/a'))} ms</small>"
                    + f"<small>{escape(stage.get('error') or stage.get('message') or '')}</small>"
                    + "</div>"
                    for stage in item["trace"]
                )
                + "</div>"
                if item["trace"]
                else "<div class='muted'>No trace recorded for this job.</div>"
            )
            + "</details>"
            for item in payload["recent_jobs"]
        ) or "<div class='list-row'><span>No completed jobs yet</span><strong>idle</strong></div>"
        recent_failures_html = "".join(
            "<div class='list-row'>"
            + "<span>"
            + escape(item["job_id"])
            + f"<br><span class='muted'>Finished: {escape(item['finished_at_display'] or 'n/a')}</span>"
            + "</span>"
            + f"<strong>{escape(item['error_message'] or item['status'])}</strong>"
            + "</div>"
            for item in payload["recent_failures"]
        ) or "<div class='list-row'><span>No failures</span><strong>ok</strong></div>"
        recent_actions_html = "".join(
            f"<div class='list-row'><span>{escape(item['action'])}</span><strong>{escape(item['status'])}</strong></div>"
            for item in payload["recent_actions"]
        ) or "<div class='list-row'><span>No actions yet</span><strong>idle</strong></div>"
        in_flight_jobs_html = "".join(
            f"<div class='list-row'><span>{escape(item['business_job_id'])}</span><strong>{escape(item['status'])} / {escape(item['mode'])}</strong></div>"
            for item in payload["worker"].get("in_flight_jobs", [])
        ) or "<div class='list-row'><span>No in-flight jobs</span><strong>idle</strong></div>"
        update_button_attrs = "" if payload["self_management"]["enabled"] else "disabled title='Self-management is disabled in the self-contained container mode.'"
        self_management_note = (
            "Self-management enabled: repository and Docker socket mounts are expected."
            if payload["self_management"]["enabled"]
            else "Self-contained mode: no repository or Docker socket mounts. Git update/rebuild is disabled for stability."
        )
        capability_notes = payload["worker"].get("capabilities", {}).get("notes", []) if payload["worker"].get("capabilities") else []
        last_worker_probe = payload["worker"].get("last_worker_probe")
        last_ml_probe = payload["worker"].get("last_ml_probe")
        life_ok = payload["heartbeat_age_sec"] is not None and payload["heartbeat_age_sec"] <= 300 and payload["worker"].get("status") != "error"
        life_class = "life-ok" if life_ok else "life-bad"
        capability_footer = ""
        if payload["worker"].get("capability_refresh_error"):
            capability_footer = "<div class='footer danger'>Current capability refresh issue: " + escape(payload["worker"].get("capability_refresh_error")) + "</div>"
        elif capability_notes:
            capability_footer = "<div class='footer'>Capability status: " + escape("; ".join(capability_notes)) + "</div>"
        return f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>ShadowGen Worker</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #0f1117;
      --panel: #1c2130;
      --panel-2: #171b27;
      --border: rgba(255,255,255,0.09);
      --muted: #aeb7d0;
      --text: #f5f7fb;
      --accent: #7dd3fc;
      --ok: #71f79f;
      --warn: #ffb86b;
      --danger: #ff7d96;
    }}
    body {{ margin:0; background: radial-gradient(circle at top, #171a24 0%, var(--bg) 60%); color: var(--text); font: 16px/1.45 Inter, Segoe UI, sans-serif; }}
    .shell {{ max-width: 1240px; margin: 0 auto; padding: 28px; }}
    .hero h1 {{ margin: 0 0 8px; font-size: 52px; }}
    .hero p {{ margin: 0 0 24px; color: var(--muted); }}
    .grid {{ display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 20px; }}
    .panel {{ background: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01)); border: 1px solid var(--border); border-radius: 22px; padding: 22px; box-shadow: 0 12px 40px rgba(0,0,0,0.22); }}
    .section-title {{ margin: 0 0 14px; font-size: 30px; }}
    .subgrid {{ display: grid; gap: 16px; }}
    .kv {{ display: grid; gap: 12px; }}
    .kv div {{ display:flex; justify-content:space-between; gap:16px; padding: 10px 0; border-bottom: 1px solid var(--border); }}
    .muted {{ color: var(--muted); }}
    .list {{ display:grid; gap:10px; }}
    .list-row {{ display:flex; justify-content:space-between; gap:14px; align-items:flex-start; background: rgba(255,255,255,0.03); border:1px solid var(--border); border-radius: 16px; padding: 12px 14px; }}
    .job-card {{ display:flex; gap:12px; align-items:flex-start; background: rgba(255,255,255,0.03); border:1px solid var(--border); border-radius: 16px; padding: 12px 14px; }}
    details.job-card {{ display:block; }}
    details.job-card summary {{ display:flex; gap:12px; align-items:flex-start; cursor:pointer; list-style:none; }}
    details.job-card summary::-webkit-details-marker {{ display:none; }}
    .job-preview {{ width:72px; height:72px; object-fit:cover; border-radius: 12px; border:1px solid var(--border); background:#10131b; flex-shrink:0; }}
    .job-preview-empty {{ display:flex; align-items:center; justify-content:center; color:var(--muted); font-size:12px; text-transform:uppercase; }}
    .job-meta {{ display:grid; gap:4px; min-width:0; }}
    .actions {{ display:flex; gap:10px; flex-wrap:wrap; margin-top: 14px; }}
    .pill {{ display:inline-flex; align-items:center; border:1px solid var(--border); border-radius:999px; padding:2px 8px; color:var(--muted); font-size:12px; }}
    .life {{ width:10px; height:10px; border-radius:999px; display:inline-block; margin-right:8px; }}
    .life-ok {{ background: var(--ok); box-shadow:0 0 0 4px rgba(113,247,159,.12); }}
    .life-bad {{ background: var(--danger); box-shadow:0 0 0 4px rgba(255,125,150,.12); }}
    .trace {{ margin-top:12px; display:grid; gap:8px; }}
    .trace-row {{ display:grid; grid-template-columns: 1fr auto auto 1.5fr; gap:10px; border-top:1px solid var(--border); padding-top:8px; color:var(--muted); }}
    .copy-button {{ margin-top:12px; padding:6px 10px; font-size:12px; }}
    button {{ border:1px solid var(--border); background: #222838; color: var(--text); border-radius: 12px; padding: 10px 14px; cursor:pointer; }}
    button:hover {{ border-color: rgba(125,211,252,0.5); }}
    button:disabled {{ opacity: .45; cursor: not-allowed; }}
    .token-row {{ display:flex; gap:10px; margin-top: 14px; }}
    input {{ flex:1; background:#11151f; border:1px solid var(--border); border-radius: 12px; padding: 10px 14px; color: var(--text); }}
    .footer {{ margin-top: 18px; color: var(--muted); font-size: 14px; }}
    .danger {{ color: var(--danger); }}
    @media (max-width: 980px) {{ .grid {{ grid-template-columns: 1fr; }} .hero h1 {{ font-size: 38px; }} }}
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <h1>ShadowGen Worker</h1>
      <p>Local worker control plane with status, recent jobs, failures, and self-managed actions.</p>
    </section>
    <section class="grid">
      <div class="subgrid">
        <div class="panel">
          <h2 class="section-title">Runtime</h2>
          <div class="kv">
            <div><span class="muted">Status</span><strong>{escape(payload["worker"]["status"])}</strong></div>
            <div><span class="muted">Life</span><strong><span class="life {life_class}"></span>{'fresh' if life_ok else 'stale/error'}</strong></div>
            <div><span class="muted">Heartbeat age</span><strong>{payload["heartbeat_age_sec"] if payload["heartbeat_age_sec"] is not None else "n/a"}s</strong></div>
            <div><span class="muted">Current job</span><strong>{escape(payload["worker"].get("current_job_id") or "n/a")}</strong></div>
            <div><span class="muted">Last completed</span><strong>{escape(payload["worker"].get("last_completed_job_id") or "n/a")}</strong></div>
            <div><span class="muted">Last duration</span><strong>{payload["worker"].get("last_completed_duration_ms") or "n/a"} ms</strong></div>
            <div><span class="muted">Effective ML URL</span><strong>{escape(payload["effective_legacy_base_url"] or "stub")}</strong></div>
            <div><span class="muted">Env ML URL</span><strong>{escape(config.legacy_ml_base_url or "not set")}</strong></div>
            <div><span class="muted">Runtime ML override</span><strong>{escape(payload["runtime_config"].get("legacy_ml_base_url") or "not set")}</strong></div>
            <div><span class="muted">ML-core mode</span><strong>{escape(payload["worker"].get("ml_core_mode") or "unknown")}</strong></div>
            <div><span class="muted">Last worker probe</span><strong>{escape((last_worker_probe or {}).get("checked_at") or "n/a")}</strong></div>
            <div><span class="muted">Last ML probe</span><strong>{escape(str((last_ml_probe or {}).get("ok")) if last_ml_probe else "n/a")} / {escape(str((last_ml_probe or {}).get("latency_ms") or "n/a"))} ms</strong></div>
            <div><span class="muted">Async enabled</span><strong>{escape(str(payload["worker"].get("async_enabled")) if payload["worker"].get("async_enabled") is not None else "unknown")}</strong></div>
            <div><span class="muted">In-flight count</span><strong>{len(payload["worker"].get("in_flight_jobs", []))}</strong></div>
            <div><span class="muted">Queue backend</span><strong>{escape(payload["queue"]["backend"])}</strong></div>
            <div><span class="muted">Storage</span><strong>{escape(payload["storage"]["backend"])} / {escape(payload["storage"].get("bucket") or "n/a")}</strong></div>
            <div><span class="muted">Container mode</span><strong>{escape(payload["self_management"]["mode"])}</strong></div>
            <div><span class="muted">Git</span><strong>{escape(payload["version"].get("git_branch") or "n/a")} @ {escape((payload["version"].get("git_commit") or "n/a")[:12])}</strong></div>
          </div>
          {capability_footer}
          <div class="token-row">
            <input id="token" type="password" placeholder="Worker control token" />
          </div>
          <div class="actions">
            <button onclick="sendAction('/api/actions/restart','restart_worker_process')">Restart process</button>
            <button onclick="sendAction('/api/actions/restart','diagnostic_probe')">Probe worker + ML</button>
            <button {update_button_attrs} onclick="sendAction('/api/actions/update','git_update_rebuild_restart')">Update from git</button>
            <button onclick="sendAction('/api/actions/clear-override','clear_runtime_override')">Clear ML override</button>
          </div>
          <div class="footer">{escape(self_management_note)}</div>
          <div class="footer">JSON API: <code>/api/status</code>, <code>/api/jobs/recent</code>, <code>/api/failures/recent</code>, <code>/api/actions/recent</code></div>
        </div>
        <div class="panel">
          <h2 class="section-title">In-Flight Jobs</h2>
          <div class="list">{in_flight_jobs_html}</div>
        </div>
        <div class="panel">
          <h2 class="section-title">Recent Jobs</h2>
          <div class="list">{recent_jobs_html}</div>
        </div>
      </div>
      <div class="subgrid">
        <div class="panel">
          <h2 class="section-title">Recent Failures</h2>
          <div class="list">{recent_failures_html}</div>
        </div>
        <div class="panel">
          <h2 class="section-title">Actions</h2>
          <div class="list">{recent_actions_html}</div>
        </div>
      </div>
    </section>
  </main>
  <script>
    async function sendAction(path, action) {{
      const token = document.getElementById('token').value;
      const response = await fetch(path, {{
        method: 'POST',
        headers: {{
          'Content-Type': 'application/json',
          'X-Worker-Token': token
        }},
        body: JSON.stringify({{ action }})
      }});
      const text = await response.text();
      if (!response.ok) {{
        alert('Action failed: ' + text);
        return;
      }}
      alert('Action submitted.');
      location.reload();
    }}
  </script>
</body>
</html>
"""

    return app
