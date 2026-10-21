import { useEffect, useState } from "react";
import DetectionOverlay from "./components/DetectionOverlay";
import Header from "./components/Header";
import ResultsPanel from "./components/ResultsPanel";
import UploadPanel from "./components/UploadPanel";
import { useVisionTrack } from "./hooks/useVisionTrack";
import { mediaUrl } from "./services/api";

export default function App() {
  const {
    mode,
    setMode,
    file,
    selectFile,
    countingEnabled,
    setCountingEnabled,
    status,
    result,
    error,
    run,
    reset,
  } = useVisionTrack();

  const [previewUrl, setPreviewUrl] = useState(null);

  // Local object URL for whatever file is currently selected -- shown
  // until a result comes back, at which point the annotated output
  // (served from the backend) takes over the viewport.
  useEffect(() => {
    if (!file) {
      setPreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const showingResult = status === "completed" && result;
  const viewportSrc = showingResult ? mediaUrl(result.output_url) : previewUrl;

  const handleModeChange = (nextMode) => {
    setMode(nextMode);
    reset();
  };

  return (
    <div className="app">
      <Header status={status} />

      <div className="layout">
        <DetectionOverlay mode={mode} src={viewportSrc} isAnnotated={Boolean(showingResult)} status={status} />

        <div>
          <UploadPanel
            mode={mode}
            onModeChange={handleModeChange}
            file={file}
            onSelectFile={selectFile}
            countingEnabled={countingEnabled}
            onCountingEnabledChange={setCountingEnabled}
            status={status}
            onRun={run}
          />
          <ResultsPanel mode={mode} status={status} result={result} error={error} onReset={reset} />
        </div>
      </div>
    </div>
  );
}
