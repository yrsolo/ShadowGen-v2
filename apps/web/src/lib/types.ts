export type JobStatus =
  | "queued"
  | "running"
  | "succeeded"
  | "failed"
  | "canceled";

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
}

export interface RenderResult {
  images: AssetRef[];
  debug_images: AssetRef[];
  metrics: {
    total_ms: number;
  };
  warnings: string[];
}

export interface JobRecord {
  job_id: string;
  status: JobStatus;
  created_at: string;
  updated_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  error?: {
    code: string;
    message: string;
  } | null;
  result?: RenderResult | null;
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
      version?: {
        git_branch?: string | null;
        git_commit?: string | null;
        image_tag?: string | null;
        container_name?: string | null;
      } | null;
      last_action?: WorkerActionRecord | null;
    } | null;
    recent_completed_jobs: WorkerJobSummary[];
    failed_jobs_count: number;
    recent_failures: JobRecord[];
    recent_actions: WorkerActionRecord[];
  };
  runtime_config: {
    legacy_ml_base_url?: string | null;
  };
  recent_jobs: JobRecord[];
}

export interface LocalRuntimeConfig {
  legacy_ml_base_url?: string | null;
}

export type WorkerControlAction =
  | "restart_worker_process"
  | "restart_container"
  | "git_update_rebuild_restart"
  | "clear_runtime_override";

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
