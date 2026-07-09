"use client";

import { useEffect, useId, useRef, useState } from "react";

interface UploadFormProps {
  onFileSelected: (file: File | null) => void;
  onClear?: () => void;
  selectedFileName: string | null;
  previewUrl: string | null;
  variant?: "min" | "max";
}

export function UploadForm({
  onFileSelected,
  onClear,
  selectedFileName,
  previewUrl,
  variant = "max"
}: UploadFormProps) {
  const fileInputId = useId();
  const cameraInputId = useId();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const cameraInputRef = useRef<HTMLInputElement | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const cameraStreamRef = useRef<MediaStream | null>(null);
  const [cameraOpen, setCameraOpen] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const compact = variant === "min";

  useEffect(() => {
    return () => stopCameraStream();
  }, []);

  useEffect(() => {
    if (!cameraOpen || !videoRef.current || !cameraStreamRef.current) {
      return;
    }
    videoRef.current.srcObject = cameraStreamRef.current;
    void videoRef.current.play().catch(() => {
      setCameraError("Tap Capture after the camera preview appears.");
    });
  }, [cameraOpen]);

  function stopCameraStream() {
    cameraStreamRef.current?.getTracks().forEach((track) => track.stop());
    cameraStreamRef.current = null;
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  }

  function handlePickedFile(file: File | null, source: "file" | "camera") {
    onFileSelected(file);
    const target = source === "camera" ? cameraInputRef.current : fileInputRef.current;
    if (target) {
      target.value = "";
    }
  }

  function openFilePicker() {
    fileInputRef.current?.click();
  }

  async function openCamera() {
    setCameraError(null);
    if (!navigator.mediaDevices?.getUserMedia) {
      cameraInputRef.current?.click();
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: "environment" }
        },
        audio: false
      });
      cameraStreamRef.current = stream;
      setCameraOpen(true);
    } catch {
      setCameraError("Camera is unavailable. Falling back to device picker.");
      cameraInputRef.current?.click();
    }
  }

  function closeCamera() {
    stopCameraStream();
    setCameraOpen(false);
  }

  async function captureCameraFrame() {
    const video = videoRef.current;
    if (!video || video.videoWidth === 0 || video.videoHeight === 0) {
      setCameraError("Camera is not ready yet.");
      return;
    }
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const context = canvas.getContext("2d");
    if (!context) {
      setCameraError("Camera capture failed.");
      return;
    }
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.92));
    if (!blob) {
      setCameraError("Camera capture failed.");
      return;
    }
    const file = new File([blob], `camera-${Date.now()}.jpg`, { type: "image/jpeg" });
    handlePickedFile(file, "camera");
    closeCamera();
  }

  return (
    <section className={`stack ${compact ? "upload-form-min" : ""}`}>
      {!compact ? <div className="panel-label">Upload image</div> : null}
      <div className={`preview-frame ${compact ? "preview-frame-min" : ""}`}>
        <div className="preview-stage">
          {cameraOpen ? (
            <div className="camera-panel" role="dialog" aria-modal="true" aria-label="Camera capture">
              <video ref={videoRef} className="camera-preview" playsInline muted autoPlay />
              <div className="camera-actions">
                <button className="file-trigger" type="button" onClick={captureCameraFrame}>Capture</button>
                <button className="ghost-button preview-action-button" type="button" onClick={closeCamera}>Cancel</button>
              </div>
            </div>
          ) : previewUrl ? (
            <>
              <img src={previewUrl} alt="Source preview" />
              {onClear ? (
                <button
                  className="preview-clear-button"
                  type="button"
                  aria-label="Clear selected image"
                  onClick={onClear}
                >
                  x
                </button>
              ) : null}
            </>
          ) : (
            <div className={`preview-empty ${compact ? "preview-empty-min" : ""}`}>
              <strong>Source preview</strong>
              <span>Choose an image to see the original input here.</span>
              <div className={`preview-entry-actions ${compact ? "preview-entry-actions-min" : ""}`}>
                <button className="file-trigger" type="button" onClick={openFilePicker}>
                  Upload image
                </button>
                <button className="ghost-button preview-action-button" type="button" onClick={openCamera}>
                  Use camera
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      <input
        ref={fileInputRef}
        id={fileInputId}
        type="file"
        accept="image/*"
        onChange={(event) => handlePickedFile(event.target.files?.[0] ?? null, "file")}
        hidden
      />
      <input
        ref={cameraInputRef}
        id={cameraInputId}
        type="file"
        accept="image/*;capture=camera"
        capture="environment"
        onChange={(event) => handlePickedFile(event.target.files?.[0] ?? null, "camera")}
        hidden
      />

      {compact ? null : (
        <div className="upload-row">
          <button className="file-trigger" type="button" onClick={openFilePicker}>Upload image</button>
          <button className="ghost-button preview-action-button" type="button" onClick={openCamera}>Use camera</button>
          <span className="muted">{selectedFileName ?? "No file selected"}</span>
        </div>
      )}

      {cameraError ? <span className="muted">{cameraError}</span> : null}
      {compact && selectedFileName ? <span className="muted compact-file-name">{selectedFileName}</span> : null}
    </section>
  );
}
