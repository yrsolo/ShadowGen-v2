import {
  CreateAssetResponse,
  CreateJobRequest,
  CreateJobResponse,
  CreateWorkerActionResponse,
  GetJobResponse,
  GetJobResultResponse,
  LocalRuntimeConfig,
  SystemDiagnosticsResponse,
  WorkerControlAction,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export function getAssetContentUrl(assetId: string): string {
  return `${API_BASE}/v1/assets/${assetId}/content`;
}

export async function createJob(payload: CreateJobRequest): Promise<CreateJobResponse> {
  const response = await fetch(`${API_BASE}/v1/jobs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(`Failed to create job: ${response.status}`);
  }

  return response.json();
}

export async function uploadAsset(file: File): Promise<CreateAssetResponse> {
  const form = new FormData();
  form.append("file", file);

  const response = await fetch(`${API_BASE}/v1/assets`, {
    method: "POST",
    body: form
  });

  if (!response.ok) {
    throw new Error(`Failed to upload asset: ${response.status}`);
  }

  return response.json();
}

export async function getJob(jobId: string): Promise<GetJobResponse> {
  const response = await fetch(`${API_BASE}/v1/jobs/${jobId}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to get job: ${response.status}`);
  }
  return response.json();
}

export async function getJobResult(jobId: string): Promise<GetJobResultResponse> {
  const response = await fetch(`${API_BASE}/v1/jobs/${jobId}/result`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to get job result: ${response.status}`);
  }
  return response.json();
}

export async function getDiagnostics(): Promise<SystemDiagnosticsResponse> {
  const response = await fetch(`${API_BASE}/v1/system/diagnostics`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to get diagnostics: ${response.status}`);
  }
  return response.json();
}

export async function getRuntimeConfig(): Promise<LocalRuntimeConfig> {
  const response = await fetch(`${API_BASE}/v1/system/runtime-config`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to get runtime config: ${response.status}`);
  }
  return response.json();
}

export async function updateRuntimeConfig(payload: LocalRuntimeConfig): Promise<LocalRuntimeConfig> {
  const response = await fetch(`${API_BASE}/v1/system/runtime-config`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw new Error(`Failed to update runtime config: ${response.status}`);
  }
  const data = await response.json();
  return data.config;
}

export async function createWorkerAction(action: WorkerControlAction): Promise<CreateWorkerActionResponse> {
  const response = await fetch(`${API_BASE}/v1/system/worker-actions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ action })
  });
  if (!response.ok) {
    throw new Error(`Failed to create worker action: ${response.status}`);
  }
  return response.json();
}
