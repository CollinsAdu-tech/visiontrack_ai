import { useCallback, useState } from "react";
import { detectImage, trackVideo } from "../services/api";

/**
 * Drives the whole upload -> process -> result workflow. `status` is the
 * single source of truth the UI renders from: "idle" | "uploading" |
 * "processing" | "completed" | "failed". Kept as one hook (rather than
 * scattering fetch calls through components) so App.jsx and ResultsPanel
 * only ever read state, never orchestrate it.
 */
export function useVisionTrack() {
  const [mode, setMode] = useState("image"); // "image" | "video"
  const [file, setFile] = useState(null);
  const [countingEnabled, setCountingEnabled] = useState(true);
  const [status, setStatus] = useState("idle");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const selectFile = useCallback((selected) => {
    setFile(selected);
    setStatus("idle");
    setResult(null);
    setError(null);
  }, []);

  const reset = useCallback(() => {
    setFile(null);
    setStatus("idle");
    setResult(null);
    setError(null);
  }, []);

  const run = useCallback(async () => {
    if (!file) return;
    setStatus("uploading");
    setError(null);

    try {
      // The backend does the whole detect/track pipeline in one request,
      // so "uploading" and "processing" are really the same network call
      // from here -- we flip to "processing" right away so the UI doesn't
      // sit on "uploading" for a 30-second video.
      setStatus("processing");
      const response =
        mode === "image" ? await detectImage(file) : await trackVideo(file, { countingEnabled });
      setResult(response);
      setStatus("completed");
    } catch (err) {
      setError(err.message || "Something went wrong.");
      setStatus("failed");
    }
  }, [file, mode, countingEnabled]);

  return {
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
  };
}
