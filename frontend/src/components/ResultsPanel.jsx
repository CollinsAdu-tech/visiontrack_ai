import AnalyticsPanel from "./AnalyticsPanel";
import ErrorMessage from "./ErrorMessage";
import ProcessingStatus from "./ProcessingStatus";

export default function ResultsPanel({ mode, status, result, error, onReset }) {
  return (
    <section className="panel">
      <h2 className="panel__title">Analytics</h2>

      <ProcessingStatus status={status} />
      <ErrorMessage message={status === "failed" ? error : null} />

      {status === "completed" && <AnalyticsPanel mode={mode} result={result} />}
      {status === "idle" && !result && <p className="dropzone__hint">Run detection to see analytics here.</p>}

      {(status === "completed" || status === "failed") && (
        <button
          type="button"
          onClick={onReset}
          className="mono"
          style={{
            marginTop: 16,
            background: "none",
            border: "none",
            color: "var(--text-muted)",
            cursor: "pointer",
            fontSize: 12.5,
            textDecoration: "underline",
            padding: 0,
          }}
        >
          Start over
        </button>
      )}
    </section>
  );
}
