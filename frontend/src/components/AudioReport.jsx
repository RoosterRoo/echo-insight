const AudioReport = ({ data }) => {
  if (!data) return <p>No analysis data available.</p>;
  return (
    <div className="report-card">
      <h2>
        {data.filename
          ? `Vocal Analysis for ${data.filename}`
          : 'Upload a file'}
      </h2>

      <ul>
        <li>
          <strong>Tempo:</strong> {data?.tempo} BPM
        </li>
        <li>
          <strong>Key:</strong> {data?.key}
        </li>
        <li>
          <strong>Brightness:</strong> {data?.brightness}
        </li>
      </ul>
    </div>
  );
};

export default AudioReport;
