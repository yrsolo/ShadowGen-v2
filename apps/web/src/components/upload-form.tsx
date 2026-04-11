"use client";

interface UploadFormProps {
  onFileSelected: (file: File | null) => void;
  selectedFileName: string | null;
  previewUrl: string | null;
}

export function UploadForm({ onFileSelected, selectedFileName, previewUrl }: UploadFormProps) {
  return (
    <section className="stack">
      <div className="panel-label">Upload image</div>
      <div className="preview-frame">
        <div className="preview-stage">
          {previewUrl ? (
            <img src={previewUrl} alt="Source preview" />
          ) : (
            <div className="preview-empty">
              <strong>Source preview</strong>
              <span>Choose an image to see the original input here.</span>
            </div>
          )}
        </div>
      </div>
      <div className="upload-row">
        <label className="file-trigger" htmlFor="source-file">Upload image</label>
        <input
          id="source-file"
          type="file"
          accept="image/*"
          onChange={(event) => onFileSelected(event.target.files?.[0] ?? null)}
        />
        <span className="muted">{selectedFileName ?? "No file selected"}</span>
      </div>
    </section>
  );
}
