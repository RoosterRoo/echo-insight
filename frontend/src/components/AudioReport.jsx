import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';

const AudioReport = ({ data }) => {
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
  const chartData = data.chroma_data.map((value, index) => ({
    note: noteNames[index],
    intensity: parseFloat((value * 100).toFixed(2)),
  }));

  return (
    <div className="bg-gray-900 p-6 rounded-xl border border-gray-700 mt-6">
      <h3 className="text-xl font-bold text-white mb-4">
        Vocal Note Distribution
      </h3>
      <div style={{ width: '100%', height: 300 }}>
        <ResponsiveContainer>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="note" stroke="#9CA3AF" />
            <YAxis stroke="#9CA3AF" unit="%" />
            <Tooltip
              contentStyle={{ backgroundColor: '#1F2937', border: 'none' }}
              itemStyle={{ color: '#60A5FA' }}
            />
            <Bar dataKey="intensity" fill="#3B82F6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default AudioReport;
