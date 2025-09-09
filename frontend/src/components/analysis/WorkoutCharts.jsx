import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const WorkoutCharts = ({ metrics }) => {
  if (!metrics?.time_series?.length) return null;

  // Process metrics data for charting
  const chartData = metrics.time_series.map(entry => ({
    time: new Date(entry.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    power: entry.avg_power,
    heartRate: entry.avg_heart_rate,
    cadence: entry.avg_cadence
  }));

  return (
    <div className="mt-6 space-y-6">
      <div className="h-64">
        <h4 className="font-medium mb-2">Power Output</h4>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis unit="W" />
            <Tooltip />
            <Line 
              type="monotone" 
              dataKey="power" 
              stroke="#10b981" 
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="h-64">
        <h4 className="font-medium mb-2">Heart Rate</h4>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis unit="bpm" />
            <Tooltip />
            <Line 
              type="monotone" 
              dataKey="heartRate" 
              stroke="#3b82f6" 
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="h-64">
        <h4 className="font-medium mb-2">Cadence</h4>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis unit="rpm" />
            <Tooltip />
            <Line 
              type="monotone" 
              dataKey="cadence" 
              stroke="#f59e0b" 
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default WorkoutCharts;