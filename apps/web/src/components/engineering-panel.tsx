"use client";

import { useEffect, useState } from "react";

import { LocalRuntimeConfig, SystemDiagnosticsResponse, WorkerControlAction } from "../lib/types";

interface EngineeringPanelProps {
  diagnostics: SystemDiagnosticsResponse | null;
  onRefresh: () => void;
  loading: boolean;
  runtimeConfig: LocalRuntimeConfig | null;
  onSaveRuntimeConfig: (config: LocalRuntimeConfig) => Promise<void>;
  onTriggerWorkerAction: (action: WorkerControlAction) => Promise<void>;
}

export function EngineeringPanel({
  diagnostics,
  onRefresh,
  loading,
  runtimeConfig,
  onSaveRuntimeConfig,
  onTriggerWorkerAction
}: EngineeringPanelProps) {
  const [legacyUrl, setLegacyUrl] = useState(runtimeConfig?.legacy_ml_base_url ?? "");
  const [saving, setSaving] = useState(false);
  const [acting, setActing] = useState<WorkerControlAction | null>(null);

  useEffect(() => {
    setLegacyUrl(runtimeConfig?.legacy_ml_base_url ?? "");
  }, [runtimeConfig?.legacy_ml_base_url]);

  async function handleSave() {
    setSaving(true);
    try {
      await onSaveRuntimeConfig({
        legacy_ml_base_url: legacyUrl.trim() || null
      });
    } finally {
      setSaving(false);
    }
  }

  async function handleAction(action: WorkerControlAction) {
    setActing(action);
    try {
      await onTriggerWorkerAction(action);
    } finally {
      setActing(null);
    }
  }

  return (
    <section className="panel stack">
      <div className="engineering-header">
        <h2 className="engineering-title">Engineering</h2>
        <button className="ghost-button" type="button" onClick={onRefresh} disabled={loading}>
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      <div className="engineering-grid">
        <div className="stack engineering-left-column">
          <div className="panel engineering-subpanel stack">
            <label htmlFor="legacy-ml-url">ML server URL</label>
            <div className="engineering-url-row">
              <input
                className="input compact-input"
                id="legacy-ml-url"
                type="text"
                value={legacyUrl}
                onChange={(event) => setLegacyUrl(event.target.value)}
                placeholder="http://192.168.1.5:9001"
              />
              <button className="ghost-button compact-button" type="button" onClick={handleSave} disabled={saving}>
                {saving ? "Saving..." : "Save"}
              </button>
              <button className="ghost-button compact-button" type="button" onClick={() => setLegacyUrl("")} disabled={saving}>
                Clear
              </button>
            </div>
            <small className="muted">
              Optional override only. If empty, worker falls back to its own configured ML server URL.
            </small>
            <div className="button-row">
              <button className="secondary-button" type="button" onClick={() => handleAction("restart_worker_process")} disabled={acting !== null}>
                {acting === "restart_worker_process" ? "Queueing..." : "Restart worker"}
              </button>
              <button className="secondary-button" type="button" onClick={() => handleAction("git_update_rebuild_restart")} disabled={acting !== null}>
                {acting === "git_update_rebuild_restart" ? "Queueing..." : "Update from git"}
              </button>
              <button className="secondary-button" type="button" onClick={() => handleAction("clear_runtime_override")} disabled={acting !== null}>
                {acting === "clear_runtime_override" ? "Queueing..." : "Clear override"}
              </button>
            </div>
          </div>

          {!diagnostics ? <p className="muted">No diagnostics loaded yet.</p> : (
            <div className="panel engineering-subpanel stack">
              <div className="stack">
                <strong>Queue</strong>
                <div className="kv">
                  <div><span className="muted">Queue backend</span><strong>{diagnostics.queue.backend}</strong></div>
                  <div><span className="muted">Queued</span><strong>{diagnostics.queue.queued_count ?? "n/a"}</strong></div>
                  <div><span className="muted">In flight</span><strong>{diagnostics.queue.in_flight_count ?? "n/a"}</strong></div>
                </div>
                {diagnostics.queue.notes.length ? (
                  <ul className="meta-list">
                    {diagnostics.queue.notes.map((note) => (
                      <li key={note}>{note}</li>
                    ))}
                  </ul>
                ) : null}
              </div>
            </div>
          )}

          {!diagnostics ? null : (
            <div className="panel engineering-subpanel stack">
              <div className="stack">
                <strong>Recent jobs</strong>
                <div className="recent-job-list">
                  {diagnostics.recent_jobs.map((job) => (
                    <div className="recent-job-item" key={job.job_id}>
                      <span>{job.job_id}</span>
                      <strong>{job.status}</strong>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {!diagnostics ? <p className="muted">No diagnostics loaded yet.</p> : (
          <div className="stack engineering-right-column">
            <div className="panel engineering-subpanel stack">
              <div className="stack">
                <strong>Runtime</strong>
                <div className="kv">
                  <div><span className="muted">Environment</span><strong>{diagnostics.app_env}</strong></div>
                  <div><span className="muted">Configured override</span><strong>{diagnostics.runtime_config.legacy_ml_base_url ?? "not set"}</strong></div>
                  <div><span className="muted">Storage backend</span><strong>{diagnostics.storage.backend}</strong></div>
                  <div><span className="muted">Storage bucket</span><strong>{diagnostics.storage.bucket ?? "n/a"}</strong></div>
                  <div><span className="muted">Storage prefix</span><strong>{diagnostics.storage.prefix ?? "n/a"}</strong></div>
                </div>
                {diagnostics.storage.notes.length ? (
                  <ul className="meta-list">
                    {diagnostics.storage.notes.map((note) => (
                      <li key={note}>{note}</li>
                    ))}
                  </ul>
                ) : null}
              </div>

              <div className="stack">
                <strong>Worker</strong>
                <div className="kv">
                  <div><span className="muted">Render backend</span><strong>{diagnostics.worker.render_backend}</strong></div>
                  <div><span className="muted">ML-core mode</span><strong>{diagnostics.worker.ml_core_mode ?? diagnostics.worker.runtime_state?.ml_core_mode ?? "unknown"}</strong></div>
                  <div><span className="muted">Async enabled</span><strong>{diagnostics.worker.async_enabled == null ? "unknown" : String(diagnostics.worker.async_enabled)}</strong></div>
                  <div><span className="muted">Legacy URL</span><strong>{diagnostics.worker.legacy_base_url ?? "stub"}</strong></div>
                  <div><span className="muted">Legacy availability</span><strong>{diagnostics.worker.live_legacy_available == null ? "unknown" : String(diagnostics.worker.live_legacy_available)}</strong></div>
                  <div><span className="muted">Worker status</span><strong>{diagnostics.worker.runtime_state?.status ?? "unknown"}</strong></div>
                  <div><span className="muted">Effective ML URL</span><strong>{diagnostics.worker.effective_legacy_base_url ?? diagnostics.worker.legacy_base_url ?? "stub"}</strong></div>
                  <div><span className="muted">Capabilities refreshed</span><strong>{diagnostics.worker.capabilities_refreshed_at ?? "n/a"}</strong></div>
                  <div><span className="muted">In-flight jobs</span><strong>{diagnostics.worker.in_flight_count}</strong></div>
                  <div><span className="muted">Fallback active</span><strong>{diagnostics.worker.runtime_state?.transition_fallback_active == null ? "unknown" : String(diagnostics.worker.runtime_state.transition_fallback_active)}</strong></div>
                  <div><span className="muted">Last job</span><strong>{diagnostics.worker.runtime_state?.last_job_id ?? "n/a"}</strong></div>
                  <div><span className="muted">Last duration</span><strong>{diagnostics.worker.runtime_state?.last_completed_duration_ms == null ? "n/a" : `${diagnostics.worker.runtime_state.last_completed_duration_ms} ms`}</strong></div>
                  <div><span className="muted">Heartbeat age</span><strong>{diagnostics.worker.heartbeat_age_sec == null ? "n/a" : `${diagnostics.worker.heartbeat_age_sec}s`}</strong></div>
                  <div><span className="muted">Heartbeat stale</span><strong>{diagnostics.worker.heartbeat_is_stale == null ? "unknown" : String(diagnostics.worker.heartbeat_is_stale)}</strong></div>
                  <div><span className="muted">Failed jobs</span><strong>{diagnostics.worker.failed_jobs_count}</strong></div>
                </div>
                {diagnostics.worker.capability_refresh_error ? (
                  <div className="error-box">
                    Capability refresh issue: {diagnostics.worker.capability_refresh_error}
                  </div>
                ) : null}
                {diagnostics.worker.runtime_state?.last_error ? (
                  <div className="error-box">
                    Last worker error: {diagnostics.worker.runtime_state.last_error}
                  </div>
                ) : null}
              </div>

              <div className="stack">
                <strong>In-flight jobs</strong>
                <div className="recent-job-list">
                  {diagnostics.worker.runtime_state?.in_flight_jobs?.length ? diagnostics.worker.runtime_state.in_flight_jobs.map((job) => (
                    <div className="recent-job-item" key={job.business_job_id}>
                      <span>{job.business_job_id}</span>
                      <strong>{job.status}{job.mode ? ` / ${job.mode}` : ""}</strong>
                    </div>
                  )) : <div className="recent-job-item"><span>No in-flight jobs</span><strong>idle</strong></div>}
                </div>
              </div>

              <div className="stack">
                <strong>Recent completed jobs</strong>
                <div className="recent-job-list">
                  {diagnostics.worker.recent_completed_jobs.length ? diagnostics.worker.recent_completed_jobs.map((job) => (
                    <div className="recent-job-item" key={job.job_id}>
                      <span>{job.job_id}</span>
                      <strong>{job.duration_ms == null ? "n/a" : `${job.duration_ms} ms`}</strong>
                    </div>
                  )) : <div className="recent-job-item"><span>No completed jobs yet</span><strong>idle</strong></div>}
                </div>
              </div>

              <div className="stack">
                <strong>Recent failures</strong>
                <div className="recent-job-list">
                  {diagnostics.worker.recent_failures.length ? diagnostics.worker.recent_failures.map((job) => (
                    <div className="recent-job-item" key={job.job_id}>
                      <span>{job.job_id}</span>
                      <strong>{job.error?.message ?? job.status}</strong>
                    </div>
                  )) : <div className="recent-job-item"><span>No recent failures</span><strong>ok</strong></div>}
                </div>
              </div>

              <div className="stack">
                <strong>Worker actions</strong>
                <div className="recent-job-list">
                  {diagnostics.worker.recent_actions.length ? diagnostics.worker.recent_actions.map((action) => (
                    <div className="recent-job-item" key={action.command_id}>
                      <span>{action.action}</span>
                      <strong>{action.status}</strong>
                    </div>
                  )) : <div className="recent-job-item"><span>No actions yet</span><strong>idle</strong></div>}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
