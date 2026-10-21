export default function ErrorMessage({ message }) {
  if (!message) return null;

  return (
    <div className="error-box">
      <p className="error-box__title">Couldn't process that file</p>
      <p>{message}</p>
    </div>
  );
}
