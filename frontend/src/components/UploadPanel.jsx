import { useCallback, useRef, useState } from "react";

const ACCEPT = {
  image: ".jpg,.jpeg,.png,.bmp",
  video: ".mp4,.mov,.avi,.mkv",
};

function formatSize(bytes) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function UploadPanel({
  mode,
  onModeChange,
  file,
  onSelectFile,
  countingEnabled,
  onCountingEnabledChange,
  status,
  onRun,
}) {
  const inputRef = useRef(null);
  const [dragActive, setDragActive] = useState(false);
  const busy = status === "uploading" || status === "processing";

  const handleFiles = useCallback(
    (fileList) => {
      const picked = fileList?.[0];
      if (picked) onSelectFile(picked);
    },
    [onSelectFile]
  );

  const handleDrop = useCallback(
    (event) => {
      event.preventDefault();
      setDragActive(false);
      handleFiles(event.dataTransfer.files);
    },
    [handleFiles]
  );

  return (
    <section className="panel">
      <h2 className="panel__title">Upload</h2>

      <div className="mode-toggle" role="group" aria-label="Media type">
        <button
          type="button"
          aria-pressed={mode === "image"}
          onClick={() => onModeChange("image")}
          disabled={busy}
        >
          Image
        </button>
        <button
          type="button"
          aria-pressed={mode === "video"}
          onClick={() => onModeChange("video")}
          disabled={busy}
        >
          Video
        </button>
      </div>

      <div
        className={`dropzone${dragActive ? " dropzone--active" : ""}`}
        onDragOver={(event) => {
          event.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") inputRef.current?.click();
        }}
      >
        <p>
          Drop a {mode === "image" ? "photo" : "clip"} here, or{" "}
          <span className="dropzone__browse">browse</span>
        </p>
        <p className="dropzone__hint">
          {mode === "image" ? "JPG, PNG, BMP" : "MP4, MOV, AVI, MKV"} &middot; up to 100 MB
        </p>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT[mode]}
          hidden
          onChange={(event) => handleFiles(event.target.files)}
        />
      </div>

      {file && (
        <div className="file-chip mono">
          <span>
            {file.name} &middot; {formatSize(file.size)}
          </span>
          <button type="button" onClick={() => onSelectFile(null)} disabled={busy} aria-label="Remove file">
            ✕
          </button>
        </div>
      )}

      {mode === "video" && (
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={countingEnabled}
            onChange={(event) => onCountingEnabledChange(event.target.checked)}
            disabled={busy}
          />
          Count objects crossing the line
        </label>
      )}

      <button type="button" className="run-button" onClick={onRun} disabled={!file || busy}>
        {busy ? "Running\u2026" : mode === "image" ? "Run detection" : "Run tracking"}
      </button>
    </section>
  );
}
