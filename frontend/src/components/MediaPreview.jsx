export default function MediaPreview({ mode, src, isAnnotated }) {
  if (!src) {
    return (
      <p className="viewport__placeholder">
        Nothing loaded yet.
        <br />
        Upload {mode === "image" ? "a photo" : "a clip"} to see it here.
      </p>
    );
  }

  return mode === "image" ? (
    <img className="viewport__media" src={src} alt={isAnnotated ? "Annotated detection result" : "Selected upload preview"} />
  ) : (
    <video className="viewport__media" src={src} controls autoPlay={isAnnotated} loop={isAnnotated} muted={isAnnotated} />
  );
}
