"use client";

import { useEffect, useRef, useState } from "react";

import { AngleSlider } from "../components/angle-slider";
import { EngineeringPanel } from "../components/engineering-panel";
import { ResultView } from "../components/result-view";
import { UploadForm } from "../components/upload-form";
import {
  createJob,
  createWorkerAction,
  getDiagnostics,
  getJob,
  getRuntimeConfig,
  updateRuntimeConfig,
  uploadAsset
} from "../lib/api-client";
import {
  JobRecord,
  LocalRuntimeConfig,
  ShadowModel,
  SystemDiagnosticsResponse,
  WorkerControlAction
} from "../lib/types";

type InterfaceMode = "min" | "max" | "engineering";

type ShadowDraft = {
  model: ShadowModel;
  angle_deg: number;
  elevation_deg: number;
};

type ClientTiming = {
  upload_ms?: number;
  create_job_ms?: number;
  initial_get_job_ms?: number;
  last_poll_ms?: number;
  polls?: number;
  total_until_job_ms?: number;
  total_until_image_ms?: number;
  image_after_job_ms?: number;
  cache_hit?: boolean;
  reused_upload?: boolean;
  reused_completed_job?: boolean;
};

const DEFAULT_ANGLE = 45;
const DEFAULT_ELEVATION = 35;

function formatDurationMs(value: number | undefined): string {
  if (value === undefined) {
    return "n/a";
  }
  return `${Math.max(0, Math.round(value))} ms`;
}

function buildTimingRows(timing: ClientTiming | null): Array<[string, string]> {
  if (!timing) {
    return [];
  }
  return [
    ["upload", timing.reused_upload ? "reused" : formatDurationMs(timing.upload_ms)],
    ["create job", formatDurationMs(timing.create_job_ms)],
    ["initial get", formatDurationMs(timing.initial_get_job_ms)],
    ["polls", String(timing.polls ?? 0)],
    ["last poll", formatDurationMs(timing.last_poll_ms)],
    ["cache", timing.cache_hit ? "hit" : "miss"],
    ["job visible", formatDurationMs(timing.total_until_job_ms)],
    ["image visible", formatDurationMs(timing.total_until_image_ms)],
    ["image after job", formatDurationMs(timing.image_after_job_ms)]
  ];
}

function isJobStillProcessing(job: JobRecord | null): boolean {
  return Boolean(job && ["queued", "running"].includes(job.status));
}

export default function HomePage() {
  const [interfaceMode, setInterfaceMode] = useState<InterfaceMode>("min");
  const [file, setFile] = useState<File | null>(null);
  const [shadowModel, setShadowModel] = useState<ShadowModel>("v1-gan");
  const [advancedMode, setAdvancedMode] = useState(false);
  const [angle, setAngle] = useState(DEFAULT_ANGLE);
  const [elevation, setElevation] = useState(DEFAULT_ELEVATION);
  const [job, setJob] = useState<JobRecord | null>(null);
  const [lastCompletedJob, setLastCompletedJob] = useState<JobRecord | null>(null);
  const [diagnostics, setDiagnostics] = useState<SystemDiagnosticsResponse | null>(null);
  const [runtimeConfig, setRuntimeConfig] = useState<LocalRuntimeConfig | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [diagnosticsBusy, setDiagnosticsBusy] = useState(false);
  const [sourcePreviewUrl, setSourcePreviewUrl] = useState<string | null>(null);
  const [uploadedSourceAssetId, setUploadedSourceAssetId] = useState<string | null>(null);
  const [uploadedFileFingerprint, setUploadedFileFingerprint] = useState<string | null>(null);
  const [processingStartedAt, setProcessingStartedAt] = useState<number | null>(null);
  const [elapsedMs, setElapsedMs] = useState(0);
  const [lastRunElapsedMs, setLastRunElapsedMs] = useState<number | null>(null);
  const [lastClientTiming, setLastClientTiming] = useState<ClientTiming | null>(null);
  const lastSubmittedShadowRef = useRef<ShadowDraft | null>(null);
  const currentRunStartedAtRef = useRef<number | null>(null);
  const resultReadyAtRef = useRef<number | null>(null);

  function getFileFingerprint(value: File): string {
    return [value.name, value.size, value.lastModified, value.type].join(":");
  }

  function getEffectiveShadowDraft(nextDraft?: Partial<ShadowDraft>): ShadowDraft {
    const legacyOnly = diagnostics?.worker.ml_core_mode === "legacy-sync";
    const draft: ShadowDraft = {
      model: legacyOnly ? "v1-gan" : nextDraft?.model ?? shadowModel,
      angle_deg: nextDraft?.angle_deg ?? angle,
      elevation_deg: nextDraft?.elevation_deg ?? elevation
    };

    if (draft.model === "v2-diff") {
      return {
        model: draft.model,
        angle_deg: DEFAULT_ANGLE,
        elevation_deg: DEFAULT_ELEVATION
      };
    }

    return draft;
  }

  function resetSourceSelection() {
    setFile(null);
    setJob(null);
    setUploadedSourceAssetId(null);
    setUploadedFileFingerprint(null);
    lastSubmittedShadowRef.current = null;
    if (sourcePreviewUrl) {
      URL.revokeObjectURL(sourcePreviewUrl);
    }
    setSourcePreviewUrl(null);
  }

  function handleFileSelected(nextFile: File | null) {
    setFile(nextFile);
    setJob(null);
    setUploadedSourceAssetId(null);
    setUploadedFileFingerprint(nextFile ? getFileFingerprint(nextFile) : null);
    lastSubmittedShadowRef.current = null;
    if (sourcePreviewUrl) {
      URL.revokeObjectURL(sourcePreviewUrl);
    }
    setSourcePreviewUrl(nextFile ? URL.createObjectURL(nextFile) : null);
  }

  async function ensureUploadedSourceAssetId(): Promise<string> {
    if (!file) {
      throw new Error("Select an image first.");
    }
    const fingerprint = getFileFingerprint(file);
    if (uploadedSourceAssetId && uploadedFileFingerprint === fingerprint) {
      return uploadedSourceAssetId;
    }
    const assetResponse = await uploadAsset(file);
    setUploadedSourceAssetId(assetResponse.asset.asset_id);
    setUploadedFileFingerprint(fingerprint);
    return assetResponse.asset.asset_id;
  }

  async function submitJob(requestedShadow: ShadowDraft) {
    if (!file) {
      setError("Select an image first.");
      return;
    }

    const shadow = getEffectiveShadowDraft(requestedShadow);
    const startedAt = Date.now();
    const timing: ClientTiming = {};
    currentRunStartedAtRef.current = startedAt;
    resultReadyAtRef.current = null;
    setBusy(true);
    setError(null);
    setProcessingStartedAt(startedAt);
    setElapsedMs(0);
    setLastClientTiming(null);

    try {
      const fingerprint = getFileFingerprint(file);
      timing.reused_upload = Boolean(uploadedSourceAssetId && uploadedFileFingerprint === fingerprint);
      const uploadStartedAt = Date.now();
      const sourceAssetId = await ensureUploadedSourceAssetId();
      timing.upload_ms = timing.reused_upload ? 0 : Date.now() - uploadStartedAt;

      const createStartedAt = Date.now();
      const createResponse = await createJob({
        render: {
          source_asset_id: sourceAssetId,
          pipeline_version: "legacy-black-box-v1",
          shadow: {
            model: shadow.model,
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
      timing.create_job_ms = Date.now() - createStartedAt;

      if (lastCompletedJob && createResponse.job_id === lastCompletedJob.job_id) {
        setJob(lastCompletedJob);
        lastSubmittedShadowRef.current = shadow;
        const finishedAt = Date.now();
        timing.cache_hit = true;
        timing.reused_completed_job = true;
        timing.total_until_job_ms = finishedAt - startedAt;
        setLastRunElapsedMs(timing.total_until_job_ms);
        setLastClientTiming({ ...timing });
        setProcessingStartedAt(null);
        return;
      }

      const getStartedAt = Date.now();
      const currentJob = await getJob(createResponse.job_id);
      timing.initial_get_job_ms = Date.now() - getStartedAt;
      timing.cache_hit = currentJob.job.status === "succeeded";
      setJob(currentJob.job);
      lastSubmittedShadowRef.current = shadow;

      if (!["queued", "running"].includes(currentJob.job.status)) {
        const finishedAt = Date.now();
        timing.total_until_job_ms = finishedAt - startedAt;
        setLastRunElapsedMs(timing.total_until_job_ms);
        setProcessingStartedAt(null);
      }

      if (currentJob.job.status === "succeeded" && currentJob.job.result?.images?.length) {
        setLastCompletedJob(currentJob.job);
        resultReadyAtRef.current = Date.now();
      }

      setLastClientTiming({ ...timing });
    } catch (cause) {
      timing.total_until_job_ms = Date.now() - startedAt;
      setLastRunElapsedMs(timing.total_until_job_ms);
      setLastClientTiming({ ...timing });
      setProcessingStartedAt(null);
      setError(cause instanceof Error ? cause.message : "Unknown error");
    } finally {
      setBusy(false);
    }
  }

  async function handleSubmit() {
    await submitJob(getEffectiveShadowDraft());
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

  async function handleSaveRuntimeConfig(config: LocalRuntimeConfig, adminToken: string) {
    setError(null);
    try {
      const nextConfig = await updateRuntimeConfig(config, adminToken);
      setRuntimeConfig(nextConfig);
      await refreshDiagnostics();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Failed to save runtime config");
    }
  }

  async function handleTriggerWorkerAction(action: WorkerControlAction, adminToken: string) {
    setError(null);
    try {
      await createWorkerAction(action, adminToken);
      await refreshDiagnostics();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Failed to trigger worker action");
    }
  }

  useEffect(() => {
    if (!job || !isJobStillProcessing(job)) {
      return;
    }

    const timer = window.setInterval(async () => {
      try {
        const pollStartedAt = Date.now();
        const updated = await getJob(job.job_id);
        const pollElapsedMs = Date.now() - pollStartedAt;

        setLastClientTiming((current) => ({
          ...(current ?? {}),
          polls: (current?.polls ?? 0) + 1,
          last_poll_ms: pollElapsedMs
        }));
        setJob(updated.job);

        if (updated.job.status === "succeeded" && updated.job.result?.images?.length) {
          setLastCompletedJob(updated.job);
          const finishedAt = Date.now();
          resultReadyAtRef.current = finishedAt;
          if (processingStartedAt) {
            const totalUntilJobMs = finishedAt - processingStartedAt;
            setLastRunElapsedMs(totalUntilJobMs);
            setLastClientTiming((current) => ({
              ...(current ?? {}),
              total_until_job_ms: totalUntilJobMs
            }));
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
    }, 350);

    return () => window.clearInterval(timer);
  }, [job, processingStartedAt]);

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
    void refreshDiagnostics();
  }, []);

  useEffect(() => {
    if (diagnostics?.worker.ml_core_mode === "legacy-sync" && shadowModel !== "v1-gan") {
      setShadowModel("v1-gan");
    }
  }, [diagnostics?.worker.ml_core_mode, shadowModel]);

  useEffect(() => {
    const nextShadow = getEffectiveShadowDraft();
    const lastSubmittedShadow = lastSubmittedShadowRef.current;

    if (
      interfaceMode === "engineering" ||
      !file ||
      lastSubmittedShadow === null ||
      (
        nextShadow.model === lastSubmittedShadow.model &&
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
  }, [angle, elevation, file, shadowModel, interfaceMode]);

  const processing = busy || isJobStillProcessing(job);
  const compactMode = interfaceMode === "min";
  const legacyOnlyMode = diagnostics?.worker.ml_core_mode === "legacy-sync";
  const modelDescription =
    legacyOnlyMode
      ? "Legacy ML service is active; only Top/manual shadow direction is supported."
      : shadowModel === "v1-gan"
      ? "Top view with manual shadow direction."
      : "Side view with automatic shadow placement.";

  const userControls = (
    <>
      <div className={`topbar ${compactMode ? "topbar-min" : ""}`}>
        <h1 className="brand-title">{compactMode ? "SdwGen" : "Shadow Generator"}</h1>
        <div className="model-toggle" role="tablist" aria-label="Shadow model">
          <button
            className={`mode-pill ${shadowModel === "v1-gan" ? "active" : ""}`}
            type="button"
            onClick={() => setShadowModel("v1-gan")}
          >
            Top
          </button>
          <button
            className={`mode-pill ${shadowModel === "v2-diff" ? "active" : ""}`}
            type="button"
            disabled={legacyOnlyMode}
            title={legacyOnlyMode ? "Side is unavailable on the legacy ML service." : undefined}
            onClick={() => setShadowModel("v2-diff")}
          >
            Side
          </button>
        </div>
      </div>

      {!compactMode ? (
        <section className="hero hero-inline">
          <p>{modelDescription} Switch to `Min` for the compact mobile flow, or keep `Max` for the full desktop workspace.</p>
        </section>
      ) : null}

      {error ? <div className="error-box">{error}</div> : null}

      <section className={compactMode ? "min-shell" : "layout-grid"}>
        <div className="panel control-stack">
          <UploadForm
            onFileSelected={handleFileSelected}
            onClear={sourcePreviewUrl ? resetSourceSelection : undefined}
            selectedFileName={file?.name ?? null}
            previewUrl={sourcePreviewUrl}
            variant={compactMode ? "min" : "max"}
          />

          <div className={`action-strip ${compactMode ? "action-strip-min" : ""}`}>
            <button className="primary-button" type="button" onClick={() => void handleSubmit()} disabled={busy}>
              {busy ? "Processing..." : "Process"}
            </button>
            <button
              className="secondary-button"
              type="button"
              onClick={() => setAngle((value) => Math.max(0, value - 20))}
              disabled={shadowModel !== "v1-gan"}
            >
              -20
            </button>
            <button
              className="secondary-button"
              type="button"
              onClick={() => setAngle((value) => Math.min(360, value + 20))}
              disabled={shadowModel !== "v1-gan"}
            >
              +20
            </button>
            <div className="inline-slider-card">
              <input
                className="slider inline-angle-slider"
                type="range"
                min={0}
                max={360}
                value={angle}
                onChange={(event) => setAngle(Number(event.target.value))}
                disabled={shadowModel !== "v1-gan"}
                aria-label="Shadow angle"
              />
            </div>
            <div className="angle-chip">{shadowModel === "v1-gan" ? angle : "Auto"}</div>
          </div>

          {!compactMode ? (
            <>
              <div className="stack">
                <div className="slider-readout">
                  <span>Selected model</span>
                  <strong>{legacyOnlyMode ? "Top (legacy)" : shadowModel === "v1-gan" ? "Top" : "Side"}</strong>
                </div>
                <p className="helper-copy">{modelDescription}</p>
              </div>

              <button
                className={`ghost-button compact-toggle ${advancedMode ? "active" : ""}`}
                type="button"
                onClick={() => setAdvancedMode((value) => !value)}
              >
                {advancedMode ? "Hide advanced" : "Open advanced"}
              </button>

              {advancedMode ? (
                <section className="advanced-panel">
                  <div className="advanced-heading">
                    <div>
                      <div className="section-kicker">Advanced</div>
                      <h3 className="section-title">Manual controls</h3>
                    </div>
                    <span className="advanced-note">Desktop-compatible view with the previous detailed controls.</span>
                  </div>
                  <AngleSlider
                    label="Shadow angle"
                    min={0}
                    max={360}
                    value={angle}
                    valueLabel={shadowModel === "v1-gan" ? `${angle} deg` : "ignored by Side"}
                    onChange={setAngle}
                  />
                  <AngleSlider
                    label="Light elevation"
                    min={0}
                    max={90}
                    value={elevation}
                    valueLabel={shadowModel === "v1-gan" ? `${elevation} deg` : "ignored by Side"}
                    onChange={setElevation}
                  />
                  <p className="helper-copy">
                    The product request stays richer than some current models. Worker-side adapters decide which shadow controls are actually forwarded to the active backend.
                  </p>
                </section>
              ) : null}
            </>
          ) : null}
        </div>

        <ResultView
          job={job}
          displayJob={lastCompletedJob}
          processing={processing}
          elapsedMs={elapsedMs}
          lastElapsedMs={lastRunElapsedMs}
          clientTimings={buildTimingRows(lastClientTiming)}
          variant={compactMode ? "min" : "max"}
          onResultImageLoad={() => {
            const startedAt = currentRunStartedAtRef.current;
            const readyAt = resultReadyAtRef.current;
            const loadedAt = Date.now();
            if (!startedAt) {
              return;
            }
            setLastClientTiming((current) => ({
              ...(current ?? {}),
              total_until_image_ms: loadedAt - startedAt,
              image_after_job_ms: readyAt ? loadedAt - readyAt : current?.image_after_job_ms
            }));
          }}
        />
      </section>
    </>
  );

  return (
    <main className="shell">
      {interfaceMode === "engineering" ? (
        <>
          <section className="hero hero-inline">
            <h1>Shadow Generator</h1>
            <p>Engineering diagnostics and worker control stay unchanged; switch back to `Min` or `Max` below for the user-facing flows.</p>
          </section>
          {error ? <div className="error-box">{error}</div> : null}
          <EngineeringPanel
            diagnostics={diagnostics}
            onRefresh={refreshDiagnostics}
            loading={diagnosticsBusy}
            runtimeConfig={runtimeConfig}
            onSaveRuntimeConfig={handleSaveRuntimeConfig}
            onTriggerWorkerAction={handleTriggerWorkerAction}
          />
        </>
      ) : userControls}

      <section className="panel interface-mode-panel">
        <div className="ui-switch-row">
          <span className="muted ui-switch-label">UI:</span>
          <div className="ui-toggle" role="tablist" aria-label="Interface mode">
            <button
              className={`mode-pill ${interfaceMode === "min" ? "active" : ""}`}
              type="button"
              onClick={() => setInterfaceMode("min")}
            >
              Min
            </button>
            <button
              className={`mode-pill ${interfaceMode === "max" ? "active" : ""}`}
              type="button"
              onClick={() => setInterfaceMode("max")}
            >
              Max
            </button>
            <button
              className={`mode-pill ${interfaceMode === "engineering" ? "active" : ""}`}
              type="button"
              onClick={() => setInterfaceMode("engineering")}
            >
              Engineering
            </button>
          </div>
        </div>
      </section>
    </main>
  );
}
