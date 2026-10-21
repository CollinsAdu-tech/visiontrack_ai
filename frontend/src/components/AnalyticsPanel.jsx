import ObjectStats from "./ObjectStats";

export default function AnalyticsPanel({ mode, result }) {
  if (!result) {
    return <p className="dropzone__hint">Run detection to see analytics here.</p>;
  }

  if (mode === "image") {
    return (
      <>
        <div className="stat-row" style={{ gridTemplateColumns: "1fr" }}>
          <div className="stat">
            <div className="stat__value">{result.detections.length}</div>
            <div className="stat__label">objects detected</div>
          </div>
        </div>
        <ObjectStats objectCounts={result.object_counts} />
      </>
    );
  }

  const a = result.analytics;
  return (
    <>
      <div className="stat-row">
        <div className="stat">
          <div className="stat__value">{a.current_objects}</div>
          <div className="stat__label">current objects</div>
        </div>
        <div className="stat">
          <div className="stat__value stat__value--entry">{a.entries}</div>
          <div className="stat__label">entries</div>
        </div>
        <div className="stat">
          <div className="stat__value stat__value--exit">{a.exits}</div>
          <div className="stat__label">exits</div>
        </div>
      </div>

      <ObjectStats objectCounts={a.object_counts} />

      <div className="meta-row">
        <span>{a.unique_tracked_objects} unique tracked</span>
        <span>{a.processing_fps.toFixed(1)} fps &middot; {a.processing_seconds.toFixed(1)}s</span>
      </div>
    </>
  );
}
