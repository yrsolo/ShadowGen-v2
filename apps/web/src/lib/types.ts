export type JobStatus =
  | "queued"
  | "running"
  | "succeeded"
  | "failed"
  | "canceled";

export type ShadowModel = "v1-gan" | "v2-diff";

export interface AssetRef {
  asset_id: string;
  kind: "source" | "final" | "debug";
  mime_type: string;
  url?: string | null;
}

export interface CreateAssetResponse {
  asset: AssetRef;
}

export interface CreateJobRequest {
  render: {
    source_asset_id: string;
    pipeline_version: string;
    shadow: {
      model: ShadowModel;
      angle_deg: number;
      elevation_deg: number;
      softness: number;
      opacity: number;
      reflection: number;
    };
    background: {
      mode: "solid" | "transparent";
      color_hex: string;
    };
    output: {
      format: "png" | "jpeg";
      width?: number | null;
      height?: number | null;
      return_debug: boolean;
    };
  };
}

export interface CreateJobResponse {
  job_id: string;
  status: JobStatus;
  cache_status?: string | null;
  reused_existing_job: boolean;
}

export interface RenderResult {
  images: AssetRef[];
  debug_images: AssetRef[];
  metrics: {
    total_ms: number;
    decode_ms?: number | null;
    geometry_ms?: number | null;
    detection_ms?: number | null;
    segmentation_ms?: number | null;
    foreground_refinement_ms?: number | null;
    depth_ms?: number | null;
    normals_ms?: number | null;
    shadow_ms?: number | null;
    composition_ms?: number | null;
    encode_ms?: number | null;
    cache_ms?: number | null;
  };
  warnings: string[];
}

export interface JobRecord {
  job_id: string;
  status: JobStatus;
  request_cache_key?: string | null;
  created_at: string;
  updated_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  error?: {
    code: string;
    message: string;
  } | null;
  result?: RenderResult | null;
  trace: JobTraceStage[];
  cache_status?: string | null;
  reused_existing_job: boolean;
}

export interface JobTraceStage {
  name: string;
  status: "running" | "succeeded" | "failed" | "skipped";
  started_at: string;
  finished_at?: string | null;
  duration_ms?: number | null;
  message?: string | null;
  error?: string | null;
}

export interface GetJobResponse {
  job: JobRecord;
}

export interface GetJobResultResponse {
  job_id: string;
  status: JobStatus;
  result?: RenderResult | null;
}

export interface SystemDiagnosticsResponse {
  app_env: string;
  storage: {
    backend: string;
    bucket?: string | null;
    prefix?: string | null;
    notes: string[];
  };
  queue: {
    backend: string;
    queued_count?: number | null;
    in_flight_count?: number | null;
    notes: string[];
  };
  worker: {
    render_backend: string;
    legacy_base_url?: string | null;
    effective_legacy_base_url?: string | null;
    live_legacy_available?: boolean | null;
    ml_core_mode?: string | null;
    async_enabled?: boolean | null;
    heartbeat_age_sec?: number | null;
    heartbeat_is_stale?: boolean | null;
    runtime_state?: {
      status: string;
      last_job_id?: string | null;
      last_error?: string | null;
      updated_at?: string | null;
      startup_at?: string | null;
      current_job_id?: string | null;
      current_job_started_at?: string | null;
      last_completed_job_id?: string | null;
      last_completed_duration_ms?: number | null;
      effective_legacy_base_url?: string | null;
      ml_core_mode?: string | null;
      async_enabled?: boolean | null;
      capability_refresh_error?: string | null;
      last_submit_error?: string | null;
      last_poll_error?: string | null;
      transition_fallback_active?: boolean;
      in_flight_jobs?: Array<{
        business_job_id: string;
        mode: string;
        status: string;
        ml_core_job_id?: string | null;
        request_id?: string | null;
        submit_started_at?: string | null;
        last_poll_at?: string | null;
        ttl_deadline_at?: string | null;
        retry_count: number;
        last_error?: string | null;
      }>;
      version?: {
        git_branch?: string | null;
        git_commit?: string | null;
        image_tag?: string | null;
        container_name?: string | null;
      } | null;
      last_action?: WorkerActionRecord | null;
      last_worker_probe?: WorkerDiagnosticProbe | null;
      last_ml_probe?: WorkerDiagnosticProbe | null;
    } | null;
    capabilities_refreshed_at?: string | null;
    capability_refresh_error?: string | null;
    in_flight_count: number;
    recent_completed_jobs: WorkerJobSummary[];
    failed_jobs_count: number;
    recent_failures: JobRecord[];
    recent_actions: WorkerActionRecord[];
  };
  runtime_config: {
    legacy_ml_base_url?: string | null;
  };
  recent_jobs: JobRecord[];
  lost_jobs: LostJobDiagnostic[];
}

export interface LostJobDiagnostic {
  job: JobRecord;
  age_sec: number;
  reason: string;
  evidence: string[];
  suggested_action: "mark_failed" | "delete" | string;
}

export interface LocalRuntimeConfig {
  legacy_ml_base_url?: string | null;
}

export type WorkerControlAction =
  | "restart_worker_process"
  | "restart_container"
  | "git_update_rebuild_restart"
  | "clear_runtime_override"
  | "diagnostic_probe";

export interface WorkerDiagnosticProbe {
  checked_at: string;
  ok: boolean;
  target_url?: string | null;
  latency_ms?: number | null;
  mode?: string | null;
  error?: string | null;
}

export interface WorkerJobSummary {
  job_id: string;
  status: string;
  started_at?: string | null;
  finished_at?: string | null;
  duration_ms?: number | null;
  error_message?: string | null;
}

export interface WorkerActionRecord {
  command_id: string;
  action: WorkerControlAction;
  requested_at: string;
  requested_by: string;
  validation_marker?: string | null;
  payload: Record<string, string>;
  status: "queued" | "running" | "succeeded" | "failed";
  started_at?: string | null;
  finished_at?: string | null;
  summary?: string | null;
  error_text?: string | null;
  log_excerpt?: string | null;
}

export interface CreateWorkerActionResponse {
  command: WorkerActionRecord;
}

export interface JobMutationResponse {
  job_id: string;
  status?: JobStatus | null;
  deleted: boolean;
}
