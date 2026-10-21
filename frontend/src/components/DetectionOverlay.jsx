import MediaPreview from "./MediaPreview";

export default function DetectionOverlay({ mode, src, isAnnotated, status }) {
  const scanning = status === "uploading" || status === "processing";

  return (
    <div className="viewport">
      <MediaPreview mode={mode} src={src} isAnnotated={isAnnotated} />

      <span className="viewport__bracket viewport__bracket--tl" />
      <span className="viewport__bracket viewport__bracket--tr" />
      <span className="viewport__bracket viewport__bracket--bl" />
      <span className="viewport__bracket viewport__bracket--br" />

      {scanning && <span className="scanline" />}

      {src && (
        <span className="viewport__badge">
          {isAnnotated ? "annotated result" : "source preview"}
        </span>
      )}
    </div>
  );
}
