"use client";

import { useId, useRef } from "react";

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
  const compact = variant === "min";

  function handlePickedFile(file: File | null, source: "file" | "camera") {
    onFileSelected(file);
    const target = source === "camera" ? cameraInputRef.current : fileInputRef.current;
    if (target) {
      target.value = "";
    }
  }

  return (
    <section className={`stack ${compact ? "upload-form-min" : ""}`}>
      {!compact ? <div className="panel-label">Upload image</div> : null}
      <div className={`preview-frame ${compact ? "preview-frame-min" : ""}`}>
        <div className="preview-stage">
          {previewUrl ? (
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
                <label className="file-trigger" htmlFor={fileInputId}>
                  Upload image
                </label>
                <label className="ghost-button preview-action-button" htmlFor={cameraInputId}>
                  Use camera
                </label>
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
        accept="image/*"
        capture="environment"
        onChange={(event) => handlePickedFile(event.target.files?.[0] ?? null, "camera")}
        hidden
      />

      {compact ? null : (
        <div className="upload-row">
          <label className="file-trigger" htmlFor={fileInputId}>Upload image</label>
          <label className="ghost-button preview-action-button" htmlFor={cameraInputId}>Use camera</label>
          <span className="muted">{selectedFileName ?? "No file selected"}</span>
        </div>
      )}

      {compact && selectedFileName ? <span className="muted compact-file-name">{selectedFileName}</span> : null}
    </section>
  );
}
