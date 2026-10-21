const MESSAGES = {
  uploading: "Uploading\u2026",
  processing: "Running detection\u2026 this can take a moment for longer clips.",
};

export default function ProcessingStatus({ status }) {
  if (status !== "uploading" && status !== "processing") return null;

  return (
    <p className="processing">
      <span className="status-dot status-dot--busy" />
      {MESSAGES[status]}
    </p>
  );
}
