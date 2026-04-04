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
    <div className="mt-8 space-y-6">
      {/* 1. Accuracy Card */}
      <div className="p-6 bg-gray-800 rounded-xl border border-gray-700 text-center">
        <h3 className="text-gray-400 text-sm uppercase">Pitch Accuracy</h3>
        <p className="text-4xl font-bold text-indigo-400">{accuracy}%</p>
      </div>

      {/* 2. The Chart Container - THIS IS THE FIX */}
      <div className="h-[400px] w-full bg-gray-900 p-4 rounded-xl border border-gray-800">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <XAxis dataKey="note" stroke="#94a3b8" />
            <YAxis hide />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: 'none',
                borderRadius: '8px',
              }}
              itemStyle={{ color: '#818cf8' }}
            />
            <Bar dataKey="intensity" radius={[4, 4, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.isTarget ? '#fbbf24' : '#334155'}
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
