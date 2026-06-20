"use client";

import { useEffect, useState } from "react";

import { getAssetContentUrl } from "../lib/api-client";
import { JobRecord, LocalRuntimeConfig, LostJobDiagnostic, SystemDiagnosticsResponse, WorkerControlAction } from "../lib/types";

interface EngineeringPanelProps {
  diagnostics: SystemDiagnosticsResponse | null;
  onRefresh: () => void;
  loading: boolean;
  runtimeConfig: LocalRuntimeConfig | null;
  onSaveRuntimeConfig: (config: LocalRuntimeConfig, adminToken: string) => Promise<void>;
  onTriggerWorkerAction: (action: WorkerControlAction, adminToken: string) => Promise<void>;
  onMarkJobFailed: (jobId: string, reason: string, adminToken: string) => Promise<void>;
  onDeleteJob: (jobId: string, adminToken: string) => Promise<void>;
}

function formatDateTime(value?: string | null): string {
  if (!value) {
    return "n/a";
  }
  return new Date(value).toLocaleString();
}

function durationMs(job: JobRecord): number | null {
  if (!job.started_at || !job.finished_at) {
    return null;
  }
  return Math.max(0, new Date(job.finished_at).getTime() - new Date(job.started_at).getTime());
}

function lastMeaningfulStage(job: JobRecord): string {
  const failed = [...(job.trace ?? [])].reverse().find((stage) => stage.status === "failed");
  if (failed) {
    return `${failed.name}: ${failed.error ?? failed.message ?? "failed"}`;
  }
  const running = [...(job.trace ?? [])].reverse().find((stage) => stage.status === "running");
  if (running) {
    return `${running.name}: running`;
  }
  const last = job.trace?.[job.trace.length - 1];
  return last ? `${last.name}: ${last.status}` : "No trace";
}

function JobDiagnosticsCard({ job }: { job: JobRecord }) {
  const finalImage = job.result?.images?.[0] ?? null;
  const duration = durationMs(job);
  const cacheLabel = job.reused_existing_job ? job.cache_status ?? "cache-hit" : job.cache_status ?? "fresh";
  const mlMetrics = Object.entries(job.result?.metrics ?? {}).filter(([, value]) => value != null);

  async function copyJobId() {
    await navigator.clipboard.writeText(job.job_id);
  }

  return (
    <details className="diagnostic-job-card">
      <summary className="diagnostic-job-summary">
        {finalImage ? (
          <img className="diagnostic-job-preview" src={getAssetContentUrl(finalImage.asset_id)} alt="Result preview" />
        ) : (
          <div className="diagnostic-job-preview diagnostic-job-preview-empty">no preview</div>
        )}
        <div className="diagnostic-job-main">
          <div className="diagnostic-job-title">
            <strong>{formatDateTime(job.created_at)}</strong>
            <span className={`status-pill ${job.status === "succeeded" ? "success" : job.status === "failed" ? "failed" : ""}`}>
              {job.status}
            </span>
          </div>
          <div className="diagnostic-job-meta">
            <span>{duration == null ? "duration n/a" : `${duration} ms`}</span>
            <span>{cacheLabel}</span>
            <span>{lastMeaningfulStage(job)}</span>
          </div>
        </div>
      </summary>
      <div className="diagnostic-job-details">
        <button className="ghost-button compact-button" type="button" onClick={copyJobId}>Copy job id</button>
        <div className="kv">
          <div><span className="muted">Job id</span><strong>{job.job_id}</strong></div>
          <div><span className="muted">Updated</span><strong>{formatDateTime(job.updated_at)}</strong></div>
          <div><span className="muted">Finished</span><strong>{formatDateTime(job.finished_at)}</strong></div>
          <div><span className="muted">Cache key</span><strong>{job.request_cache_key ?? "n/a"}</strong></div>
        </div>
        {job.error ? <div className="error-box">Error: {job.error.message}</div> : null}
        {mlMetrics.length ? (
          <div className="diagnostic-timeline">
            <strong>ML metrics</strong>
            {mlMetrics.map(([name, value]) => (
              <div className="diagnostic-stage" key={`${job.job_id}-metric-${name}`}>
                <span>{name}</span>
                <strong>{value} ms</strong>
                <small />
                <small />
              </div>
            ))}
          </div>
        ) : null}
        <div className="diagnostic-timeline">
          {(job.trace ?? []).length ? job.trace.map((stage, index) => (
            <div className="diagnostic-stage" key={`${job.job_id}-${stage.name}-${index}`}>
              <span>{stage.name}</span>
              <strong>{stage.status}</strong>
              <small>{stage.duration_ms == null ? "n/a" : `${stage.duration_ms} ms`}</small>
              <small>{stage.error ?? stage.message ?? ""}</small>
            </div>
          )) : <div className="muted">No trace recorded for this job.</div>}
        </div>
      </div>
    </details>
  );
}

function formatAge(ageSec: number): string {
  if (ageSec < 60) {
    return `${ageSec}s`;
  }
  if (ageSec < 3600) {
    return `${Math.floor(ageSec / 60)}m ${ageSec % 60}s`;
  }
  return `${Math.floor(ageSec / 3600)}h ${Math.floor((ageSec % 3600) / 60)}m`;
}

function LostJobCard({
  item,
  busy,
  onMarkFailed,
  onDelete
}: {
  item: LostJobDiagnostic;
  busy: boolean;
  onMarkFailed: (item: LostJobDiagnostic) => void;
  onDelete: (item: LostJobDiagnostic) => void;
}) {
  return (
    <details className="lost-job-card" open>
      <summary className="diagnostic-job-summary">
        <div className="diagnostic-job-preview diagnostic-job-preview-empty">lost</div>
        <div className="diagnostic-job-main">
          <div className="diagnostic-job-title">
            <strong>{formatDateTime(item.job.created_at)}</strong>
            <span className="status-pill failed">{item.job.status}</span>
            <span className="status-pill">age {formatAge(item.age_sec)}</span>
          </div>
          <div className="diagnostic-job-meta">
            <span>{item.reason}</span>
          </div>
        </div>
      </summary>
      <div className="diagnostic-job-details">
        <div className="error-box">
          This job is live only in metadata. Worker/queue state does not show matching active work.
        </div>
        <ul className="meta-list">
          {item.evidence.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
        <div className="button-row">
          <button className="secondary-button" type="button" disabled={busy} onClick={() => onMarkFailed(item)}>
            Mark failed
          </button>
          <button className="ghost-button compact-button danger-button" type="button" disabled={busy} onClick={() => onDelete(item)}>
            Delete metadata
          </button>
          <button className="ghost-button compact-button" type="button" onClick={() => navigator.clipboard.writeText(item.job.job_id)}>
            Copy job id
          </button>
        </div>
        <div className="kv">
          <div><span className="muted">Job id</span><strong>{item.job.job_id}</strong></div>
          <div><span className="muted">Updated</span><strong>{formatDateTime(item.job.updated_at)}</strong></div>
          <div><span className="muted">Cache key</span><strong>{item.job.request_cache_key ?? "n/a"}</strong></div>
        </div>
      </div>
    </details>
  );
}

export function EngineeringPanel({
  diagnostics,
  onRefresh,
  loading,
  runtimeConfig,
  onSaveRuntimeConfig,
  onTriggerWorkerAction,
  onMarkJobFailed,
  onDeleteJob
}: EngineeringPanelProps) {
  const [legacyUrl, setLegacyUrl] = useState(runtimeConfig?.legacy_ml_base_url ?? "");
  const [adminToken, setAdminToken] = useState("");
  const [saving, setSaving] = useState(false);
  const [acting, setActing] = useState<WorkerControlAction | null>(null);
  const [mutatingJobId, setMutatingJobId] = useState<string | null>(null);

  useEffect(() => {
    setLegacyUrl(runtimeConfig?.legacy_ml_base_url ?? "");
  }, [runtimeConfig?.legacy_ml_base_url]);

  async function handleSave() {
    setSaving(true);
    try {
      await onSaveRuntimeConfig({
        legacy_ml_base_url: legacyUrl.trim() || null
      }, adminToken);
    } finally {
      setSaving(false);
    }
  }

  async function handleAction(action: WorkerControlAction) {
    setActing(action);
    try {
      await onTriggerWorkerAction(action, adminToken);
    } finally {
      setActing(null);
    }
  }

  async function handleMarkFailed(item: LostJobDiagnostic) {
    setMutatingJobId(item.job.job_id);
    try {
      await onMarkJobFailed(
        item.job.job_id,
        `Marked failed from engineering diagnostics. ${item.reason}`,
        adminToken
      );
    } finally {
      setMutatingJobId(null);
    }
  }

  async function handleDelete(item: LostJobDiagnostic) {
    if (!window.confirm(`Delete metadata for job ${item.job.job_id}? This cannot be undone.`)) {
      return;
    }
    setMutatingJobId(item.job.job_id);
    try {
      await onDeleteJob(item.job.job_id, adminToken);
    } finally {
      setMutatingJobId(null);
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
            <label htmlFor="admin-api-token">Admin token</label>
            <input
              className="input compact-input"
              id="admin-api-token"
              type="password"
              value={adminToken}
              onChange={(event) => setAdminToken(event.target.value)}
              placeholder="Required for operator actions"
            />
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
              <button className="secondary-button" type="button" onClick={() => handleAction("diagnostic_probe")} disabled={acting !== null}>
                {acting === "diagnostic_probe" ? "Queueing..." : "Probe worker + ML"}
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
                {diagnostics.lost_jobs.length ? (
                  <>
                    <strong>Lost jobs</strong>
                    <div className="diagnostic-job-list">
                      {diagnostics.lost_jobs.map((item) => (
                        <LostJobCard
                          key={item.job.job_id}
                          item={item}
                          busy={mutatingJobId === item.job.job_id}
                          onMarkFailed={handleMarkFailed}
                          onDelete={handleDelete}
                        />
                      ))}
                    </div>
                  </>
                ) : null}
                <strong>Recent jobs</strong>
                <div className="diagnostic-job-list">
                  {diagnostics.recent_jobs.length ? diagnostics.recent_jobs.map((job) => (
                    <JobDiagnosticsCard key={job.job_id} job={job} />
                  )) : <div className="recent-job-item"><span>No jobs yet</span><strong>idle</strong></div>}
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
                {(() => {
                  const stale = diagnostics.worker.heartbeat_is_stale ?? true;
                  const error = diagnostics.worker.runtime_state?.status === "error";
                  const alive = !stale && !error;
                  return (
                    <div className={`worker-life ${alive ? "ok" : "bad"}`}>
                      <span className="worker-life-dot" />
                      <strong>{alive ? "Worker fresh" : "Worker stale/error"}</strong>
                      <span>{diagnostics.worker.runtime_state?.updated_at ? formatDateTime(diagnostics.worker.runtime_state.updated_at) : "no heartbeat"}</span>
                    </div>
                  );
                })()}
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
                  <div><span className="muted">Last worker probe</span><strong>{diagnostics.worker.runtime_state?.last_worker_probe ? formatDateTime(diagnostics.worker.runtime_state.last_worker_probe.checked_at) : "n/a"}</strong></div>
                  <div><span className="muted">Last ML probe</span><strong>{diagnostics.worker.runtime_state?.last_ml_probe ? `${diagnostics.worker.runtime_state.last_ml_probe.ok ? "ok" : "failed"} / ${diagnostics.worker.runtime_state.last_ml_probe.latency_ms ?? "n/a"} ms` : "n/a"}</strong></div>
                  <div><span className="muted">Failed jobs</span><strong>{diagnostics.worker.failed_jobs_count}</strong></div>
                </div>
                {diagnostics.worker.runtime_state?.last_ml_probe?.error ? (
                  <div className="error-box">
                    Last ML probe: {diagnostics.worker.runtime_state.last_ml_probe.error}
                  </div>
                ) : null}
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
                {diagnostics.worker.runtime_state?.last_submit_error ? (
                  <div className="error-box">
                    Last ML submit error: {diagnostics.worker.runtime_state.last_submit_error}
                  </div>
                ) : null}
                {diagnostics.worker.runtime_state?.last_poll_error ? (
                  <div className="error-box">
                    Last ML poll error: {diagnostics.worker.runtime_state.last_poll_error}
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
                      <span>{formatDateTime(job.finished_at)}</span>
                      <strong>{job.duration_ms == null ? "n/a" : `${job.duration_ms} ms`}</strong>
                    </div>
                  )) : <div className="recent-job-item"><span>No completed jobs yet</span><strong>idle</strong></div>}
                </div>
              </div>

              <div className="stack">
                <strong>Recent failures</strong>
                <div className="recent-job-list">
                  {diagnostics.worker.recent_failures.length ? diagnostics.worker.recent_failures.map((job) => (
                    <JobDiagnosticsCard key={job.job_id} job={job} />
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
