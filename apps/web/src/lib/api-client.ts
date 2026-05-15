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
const TARGET_UPLOAD_IMAGE_SHORT_SIDE = 1024;
const JPEG_UPLOAD_QUALITY = 0.9;

function jsonHeaders(adminToken?: string): HeadersInit {
  const headers: Record<string, string> = {
    "Content-Type": "application/json"
  };
  if (adminToken) {
    headers["X-Admin-Token"] = adminToken;
  }
  return headers;
}

function loadImage(file: File): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image();
    const url = URL.createObjectURL(file);
    image.onload = () => {
      URL.revokeObjectURL(url);
      resolve(image);
    };
    image.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("Failed to read selected image."));
    };
    image.src = url;
  });
}

function canvasToBlob(canvas: HTMLCanvasElement, mimeType: string, quality?: number): Promise<Blob> {
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => {
        if (blob) {
          resolve(blob);
          return;
        }
        reject(new Error("Failed to prepare selected image."));
      },
      mimeType,
      quality
    );
  });
}

async function prepareImageForUpload(file: File): Promise<{ blob: Blob; filename: string }> {
  if (!file.type.startsWith("image/")) {
    return { blob: file, filename: file.name };
  }

  const image = await loadImage(file);
  const shortestSide = Math.min(image.naturalWidth, image.naturalHeight);
  if (shortestSide <= TARGET_UPLOAD_IMAGE_SHORT_SIDE) {
    return { blob: file, filename: file.name };
  }

  const scale = TARGET_UPLOAD_IMAGE_SHORT_SIDE / shortestSide;
  const width = Math.max(1, Math.round(image.naturalWidth * scale));
  const height = Math.max(1, Math.round(image.naturalHeight * scale));
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;

  const context = canvas.getContext("2d");
  if (!context) {
    return { blob: file, filename: file.name };
  }

  context.drawImage(image, 0, 0, width, height);
  const outputType = file.type === "image/png" ? "image/png" : "image/jpeg";
  const blob = await canvasToBlob(
    canvas,
    outputType,
    outputType === "image/jpeg" ? JPEG_UPLOAD_QUALITY : undefined
  );
  const extension = outputType === "image/png" ? "png" : "jpg";
  const filename = file.name.replace(/\.[^.]+$/, "") || "source";
  return { blob, filename: `${filename}.${extension}` };
}

export function getAssetContentUrl(assetId: string): string {
  return `${API_BASE}/v1/assets/${assetId}/content`;
}

export async function createJob(payload: CreateJobRequest): Promise<CreateJobResponse> {
  const response = await fetch(`${API_BASE}/v1/jobs`, {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(`Failed to create job: ${response.status}`);
  }

  return response.json();
}

export async function uploadAsset(file: File): Promise<CreateAssetResponse> {
  const prepared = await prepareImageForUpload(file);
  const form = new FormData();
  form.append("file", prepared.blob, prepared.filename);

  let response: Response;
  try {
    response = await fetch(`${API_BASE}/v1/assets`, {
      method: "POST",
      body: form
    });
  } catch (cause) {
    throw new Error("Failed to upload asset: network error or image payload was too large.");
  }

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

export async function updateRuntimeConfig(payload: LocalRuntimeConfig, adminToken: string): Promise<LocalRuntimeConfig> {
  const response = await fetch(`${API_BASE}/v1/system/runtime-config`, {
    method: "PUT",
    headers: jsonHeaders(adminToken),
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw new Error(`Failed to update runtime config: ${response.status}`);
  }
  const data = await response.json();
  return data.config;
}

export async function createWorkerAction(action: WorkerControlAction, adminToken: string): Promise<CreateWorkerActionResponse> {
  const response = await fetch(`${API_BASE}/v1/system/worker-actions`, {
    method: "POST",
    headers: jsonHeaders(adminToken),
    body: JSON.stringify({ action })
  });
  if (!response.ok) {
    throw new Error(`Failed to create worker action: ${response.status}`);
  }
  return response.json();
}
