const STATUS_COPY = {
  idle: "ready",
  uploading: "uploading",
  processing: "processing",
  completed: "done",
  failed: "failed",
};

export default function Header({ status }) {
  const dotClass =
    status === "failed"
      ? "status-dot status-dot--failed"
      : status === "processing" || status === "uploading"
      ? "status-dot status-dot--busy"
      : status === "completed"
      ? "status-dot status-dot--ready"
      : "status-dot";

  return (
    <header className="header">
      <div>
        <h1 className="header__title">
          VisionTrack <span>AI</span>
        </h1>
        <p className="header__tagline">See. Track. Understand.</p>
      </div>
      <span className="status-pill">
        <span className={dotClass} />
        {STATUS_COPY[status] ?? "ready"}
      </span>
    </header>
  );
}
