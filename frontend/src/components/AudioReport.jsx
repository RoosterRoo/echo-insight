import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

const AudioReport = ({ data, targetNote }) => {
  const noteNames = [
    'C',
    'C#',
    'D',
    'D#',
    'E',
    'F',
    'F#',
    'G',
    'G#',
    'A',
    'A#',
    'B',
  ];

  // Find the intensity of the target note
  const targetIndex = noteNames.indexOf(targetNote);
  const targetIntensity = data.chroma_data[targetIndex];
  const totalIntensity = data.chroma_data.reduce((a, b) => a + b, 0);

  // Calculate accuracy as a percentage of total energy
  const accuracy = ((targetIntensity / totalIntensity) * 100).toFixed(1);

  const chartData = data.chroma_data.map((value, index) => ({
    note: noteNames[index],
    intensity: parseFloat((value * 100).toFixed(2)),
    isTarget: noteNames[index] === targetNote,
  }));

  return (
    <div className="mt-8">
      <div className="mb-6 p-6 bg-blue-900/20 border border-blue-500/50 rounded-xl text-center">
        <h2 className="text-gray-400 uppercase text-xs tracking-widest">
          Target Accuracy
        </h2>
        <p className="text-5xl font-mono font-bold text-blue-400">
          {accuracy}%
        </p>
        <p className="text-sm text-gray-500 mt-2">
          {accuracy > 40
            ? 'Great job hitting the target!'
            : 'Keep practicing that pitch!'}
        </p>
      </div>

      <div style={{ width: '100%', height: 300 }}>
        <ResponsiveContainer>
          <BarChart data={chartData}>
            <XAxis dataKey="note" stroke="#9CA3AF" />
            <YAxis hide />
            <Tooltip cursor={{ fill: 'transparent' }} />
            <Bar dataKey="intensity">
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  // Highlight Target in Gold, others in Gray/Blue
                  fill={entry.isTarget ? '#FBBF24' : '#374151'}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default AudioReport;
