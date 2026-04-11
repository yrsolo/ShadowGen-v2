"use client";

import { useEffect, useRef, useState } from "react";

import { AngleSlider } from "../components/angle-slider";
import { EngineeringPanel } from "../components/engineering-panel";
import { ResultView } from "../components/result-view";
import { UploadForm } from "../components/upload-form";
import { createJob, createWorkerAction, getDiagnostics, getJob, getRuntimeConfig, updateRuntimeConfig, uploadAsset } from "../lib/api-client";
import { JobRecord, LocalRuntimeConfig, SystemDiagnosticsResponse } from "../lib/types";

type Tab = "user" | "engineering";
type ShadowDraft = {
  angle_deg: number;
  elevation_deg: number;
};

export default function HomePage() {
  const [tab, setTab] = useState<Tab>("user");
  const [file, setFile] = useState<File | null>(null);
  const [angle, setAngle] = useState(45);
  const [elevation, setElevation] = useState(45);
  const [job, setJob] = useState<JobRecord | null>(null);
  const [lastCompletedJob, setLastCompletedJob] = useState<JobRecord | null>(null);
  const [diagnostics, setDiagnostics] = useState<SystemDiagnosticsResponse | null>(null);
  const [runtimeConfig, setRuntimeConfig] = useState<LocalRuntimeConfig | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [diagnosticsBusy, setDiagnosticsBusy] = useState(false);
  const [sourcePreviewUrl, setSourcePreviewUrl] = useState<string | null>(null);
  const [processingStartedAt, setProcessingStartedAt] = useState<number | null>(null);
  const [elapsedMs, setElapsedMs] = useState(0);
  const [lastRunElapsedMs, setLastRunElapsedMs] = useState<number | null>(null);
  const lastSubmittedShadowRef = useRef<ShadowDraft | null>(null);

  function handleFileSelected(nextFile: File | null) {
    setFile(nextFile);
    setJob(null);
    lastSubmittedShadowRef.current = null;
    if (sourcePreviewUrl) {
      URL.revokeObjectURL(sourcePreviewUrl);
    }
    setSourcePreviewUrl(nextFile ? URL.createObjectURL(nextFile) : null);
  }

  async function submitJob(shadow: ShadowDraft) {
    if (!file) {
      setError("Select an image first.");
      return;
    }

    const startedAt = Date.now();
    setBusy(true);
    setError(null);
    setProcessingStartedAt(startedAt);
    setElapsedMs(0);
    try {
      const assetResponse = await uploadAsset(file);
      const createResponse = await createJob({
        render: {
          source_asset_id: assetResponse.asset.asset_id,
          pipeline_version: "legacy-black-box-v1",
          shadow: {
            angle_deg: shadow.angle_deg,
            elevation_deg: shadow.elevation_deg,
            softness: 0.5,
            opacity: 0.6,
            reflection: 0.0
          },
          background: {
            mode: "solid",
            color_hex: "#FFFFFF"
          },
          output: {
            format: "png",
            width: null,
            height: null,
            return_debug: false
          }
        }
      });
      const currentJob = await getJob(createResponse.job_id);
      setJob(currentJob.job);
      lastSubmittedShadowRef.current = shadow;
      if (!["queued", "running"].includes(currentJob.job.status)) {
        setLastRunElapsedMs(Date.now() - startedAt);
        setProcessingStartedAt(null);
      }
      if (currentJob.job.status === "succeeded" && currentJob.job.result?.images?.length) {
        setLastCompletedJob(currentJob.job);
      }
    } catch (cause) {
      setLastRunElapsedMs(Date.now() - startedAt);
      setProcessingStartedAt(null);
      setError(cause instanceof Error ? cause.message : "Unknown error");
    } finally {
      setBusy(false);
    }
  }

  async function handleSubmit() {
    await submitJob({ angle_deg: angle, elevation_deg: elevation });
  }

  async function refreshDiagnostics() {
    setDiagnosticsBusy(true);
    try {
      const [nextDiagnostics, nextRuntimeConfig] = await Promise.all([
        getDiagnostics(),
        getRuntimeConfig()
      ]);
      setDiagnostics(nextDiagnostics);
      setRuntimeConfig(nextRuntimeConfig);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Failed to load diagnostics");
    } finally {
      setDiagnosticsBusy(false);
    }
  }

  async function handleSaveRuntimeConfig(config: LocalRuntimeConfig) {
    setError(null);
    try {
      const nextConfig = await updateRuntimeConfig(config);
      setRuntimeConfig(nextConfig);
      await refreshDiagnostics();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Failed to save runtime config");
    }
  }

  async function handleTriggerWorkerAction(action: "restart_worker_process" | "restart_container" | "git_update_rebuild_restart" | "clear_runtime_override") {
    setError(null);
    try {
      await createWorkerAction(action);
      await refreshDiagnostics();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Failed to trigger worker action");
    }
  }

  useEffect(() => {
    if (!job || !["queued", "running"].includes(job.status)) {
      return;
    }

    const timer = window.setInterval(async () => {
      try {
        const updated = await getJob(job.job_id);
        setJob(updated.job);
        if (updated.job.status === "succeeded" && updated.job.result?.images?.length) {
          setLastCompletedJob(updated.job);
          if (processingStartedAt) {
            setLastRunElapsedMs(Date.now() - processingStartedAt);
          }
          setProcessingStartedAt(null);
        } else if (updated.job.status === "failed" || updated.job.status === "canceled") {
          if (processingStartedAt) {
            setLastRunElapsedMs(Date.now() - processingStartedAt);
          }
          setProcessingStartedAt(null);
        }
      } catch {
        window.clearInterval(timer);
      }
    }, 1500);

    return () => window.clearInterval(timer);
  }, [job]);

  useEffect(() => {
    if (!processingStartedAt) {
      return;
    }

    const timer = window.setInterval(() => {
      setElapsedMs(Date.now() - processingStartedAt);
    }, 200);

    return () => window.clearInterval(timer);
  }, [processingStartedAt]);

  useEffect(() => {
    refreshDiagnostics();
  }, []);

  useEffect(() => {
    const nextShadow = { angle_deg: angle, elevation_deg: elevation };
    const lastSubmittedShadow = lastSubmittedShadowRef.current;

    if (
      !file ||
      lastSubmittedShadow === null ||
      (
        nextShadow.angle_deg === lastSubmittedShadow.angle_deg &&
        nextShadow.elevation_deg === lastSubmittedShadow.elevation_deg
      )
    ) {
      return;
    }

    const timer = window.setTimeout(() => {
      void submitJob(nextShadow);
    }, 500);

    return () => window.clearTimeout(timer);
  }, [angle, elevation, file]);

  return (
    <main className="shell">
      <section className="hero">
        <h1>Shadow Generator</h1>
        <p>Upload an image, tune the shadow angle, run the job, and compare source and result previews.</p>
      </section>

      <div className="tab-row">
        <button className={`tab-button ${tab === "user" ? "active" : ""}`} type="button" onClick={() => setTab("user")}>User</button>
        <button className={`tab-button ${tab === "engineering" ? "active" : ""}`} type="button" onClick={() => setTab("engineering")}>Engineering</button>
      </div>

      {error ? <div className="error-box">{error}</div> : null}

      {tab === "user" ? (
        <section className="layout-grid">
          <div className="panel control-stack">
            <UploadForm
              onFileSelected={handleFileSelected}
              selectedFileName={file?.name ?? null}
              previewUrl={sourcePreviewUrl}
            />
            <AngleSlider
              label="Shadow angle"
              min={0}
              max={360}
              value={angle}
              valueLabel={`${angle} deg`}
              onChange={setAngle}
            />
            <AngleSlider
              label="Light elevation"
              min={0}
              max={90}
              value={elevation}
              valueLabel={`${elevation} deg`}
              onChange={setElevation}
            />
            <div className="button-row">
              <button className="primary-button" type="button" onClick={handleSubmit} disabled={busy}>
                {busy ? "Processing..." : "Process"}
              </button>
              <button className="secondary-button" type="button" onClick={() => setAngle((value) => Math.max(0, value - 20))}>
                -20
              </button>
              <button className="secondary-button" type="button" onClick={() => setAngle((value) => Math.min(360, value + 20))}>
                +20
              </button>
            </div>
          </div>
          <ResultView
            job={job}
            displayJob={lastCompletedJob}
            processing={busy || Boolean(job && ["queued", "running"].includes(job.status))}
            elapsedMs={elapsedMs}
            lastElapsedMs={lastRunElapsedMs}
          />
        </section>
      ) : (
        <EngineeringPanel
          diagnostics={diagnostics}
          onRefresh={refreshDiagnostics}
          loading={diagnosticsBusy}
          runtimeConfig={runtimeConfig}
          onSaveRuntimeConfig={handleSaveRuntimeConfig}
          onTriggerWorkerAction={handleTriggerWorkerAction}
        />
      )}

      <p className="footer-note">Use via API and local worker runtime. Styled for a clean Gradio-like local workflow.</p>
    </main>
  );
}
