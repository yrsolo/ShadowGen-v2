"use client";

import { getAssetContentUrl } from "../lib/api-client";
import { JobRecord } from "../lib/types";

interface ResultViewProps {
  job: JobRecord | null;
  displayJob: JobRecord | null;
  processing: boolean;
  elapsedMs: number;
  lastElapsedMs: number | null;
}

function formatElapsed(elapsedMs: number): string {
  const totalSeconds = Math.floor(elapsedMs / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  const centiseconds = Math.floor((elapsedMs % 1000) / 10);
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}.${String(centiseconds).padStart(2, "0")}`;
}

export function ResultView({ job, displayJob, processing, elapsedMs, lastElapsedMs }: ResultViewProps) {
  const finalImage = displayJob?.result?.images.find((image) => image.kind === "final") ?? displayJob?.result?.images[0];
  const visibleJob = job ?? displayJob;
  const timerLabel = processing ? formatElapsed(elapsedMs) : lastElapsedMs !== null ? formatElapsed(lastElapsedMs) : "--:--.--";

  if (!visibleJob) {
    return (
      <section className="panel result-grid">
        <div className="result-header">
          <h2>Result</h2>
          <div className="result-header-meta">
            <div className="status-pill">Status: idle</div>
            <div className="metric-chip processing-chip">Processing time: {timerLabel}</div>
          </div>
        </div>
        <div className="preview-frame">
          <div className="preview-stage">
            <div className="preview-empty">
              <strong>No result yet</strong>
              <span>Run a job to render the processed output preview.</span>
            </div>
          </div>
        </div>
      </section>
    );
  }

  const statusClass =
    visibleJob.status === "succeeded" ? "status-pill success" :
    visibleJob.status === "failed" ? "status-pill failed" :
    "status-pill";

  return (
    <section className="panel result-grid">
      <div className="result-header">
        <h2>Job Result</h2>
        <div className="result-header-meta">
          <div className={statusClass}>Status: {visibleJob.status}</div>
          <div className="metric-chip processing-chip">Processing time: {timerLabel}</div>
        </div>
      </div>
      <div className="preview-frame">
        <div className="preview-stage">
          {finalImage ? (
            <img src={getAssetContentUrl(finalImage.asset_id)} alt="Rendered result preview" />
          ) : (
            <div className="preview-empty">
              <strong>Result preview unavailable</strong>
              <span>The current job has no final image artifact yet.</span>
            </div>
          )}
        </div>
      </div>
      {visibleJob.error ? <div className="error-box">Error: {visibleJob.error.message}</div> : null}
      <div className="inline-metrics">
        <div className="metric-chip">Job ID: {visibleJob.job_id}</div>
        <div className="metric-chip">Updated: {new Date(visibleJob.updated_at).toLocaleString()}</div>
        <div className="metric-chip">Total ms: {visibleJob.result?.metrics.total_ms ?? 0}</div>
      </div>
      {visibleJob.result?.warnings?.length ? (
        <div>
          <strong>Warnings</strong>
          <ul className="warning-list">
            {visibleJob.result.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {visibleJob.result?.images?.length ? (
        <div>
          <strong>Artifacts</strong>
          <ul className="meta-list">
            {visibleJob.result.images.map((image) => (
              <li key={image.asset_id}>{image.asset_id} ({image.kind})</li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
