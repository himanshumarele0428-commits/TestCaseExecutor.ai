import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';
import type { DashboardStats, ModuleStat, DailyTrend } from '../../types';

interface Props {
  stats: DashboardStats | null;
  modules: ModuleStat[];
  trends: DailyTrend[];
}

const COLORS = ['#22c55e', '#ef4444', '#3b82f6', '#eab308'];

export default function DashboardCharts({ stats, modules, trends }: Props) {
  const pieData = stats
    ? [
        { name: 'Passed', value: stats.passed },
        { name: 'Failed', value: stats.failed },
        { name: 'Running', value: stats.running },
        { name: 'Blocked', value: stats.blocked },
      ].filter((d) => d.value > 0)
    : [];

  const moduleData = modules.map((m) => ({
    name: m.module,
    Passed: m.passed,
    Failed: m.failed,
  }));

  const trendData = trends.map((t) => ({
    date: t.date,
    Passed: t.passed,
    Failed: t.failed,
  }));

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Pass vs Fail</h3>
        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={5} dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
              {pieData.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Module-wise Statistics</h3>
        {moduleData.length > 0 ? (
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={moduleData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="name" stroke="#9ca3af" fontSize={12} />
              <YAxis stroke="#9ca3af" fontSize={12} />
              <Tooltip />
              <Legend />
              <Bar dataKey="Passed" fill="#22c55e" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Failed" fill="#ef4444" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-gray-500 text-center py-20">No module data yet</p>
        )}
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 lg:col-span-2">
        <h3 className="text-lg font-semibold text-white mb-4">Execution Trend</h3>
        {trendData.length > 0 ? (
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="date" stroke="#9ca3af" fontSize={12} />
              <YAxis stroke="#9ca3af" fontSize={12} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="Passed" stroke="#22c55e" strokeWidth={2} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="Failed" stroke="#ef4444" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-gray-500 text-center py-20">No trend data yet</p>
        )}
      </div>
    </div>
  );
}
