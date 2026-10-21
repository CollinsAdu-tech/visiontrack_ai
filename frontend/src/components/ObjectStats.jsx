export default function ObjectStats({ objectCounts }) {
  const entries = Object.entries(objectCounts || {}).sort((a, b) => b[1] - a[1]);

  if (entries.length === 0) {
    return <p className="dropzone__hint">No objects detected.</p>;
  }

  return (
    <ul className="class-list">
      {entries.map(([className, count]) => (
        <li key={className}>
          <span>{className}</span>
          <span className="count mono">{count}</span>
        </li>
      ))}
    </ul>
  );
}
