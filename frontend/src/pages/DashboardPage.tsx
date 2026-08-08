import { useState, useEffect } from 'react';
import api from '../api/client';
import { Loading } from '../components/Common/Loading';
import ErrorBoundary from '../components/Common/ErrorBoundary';
import KPICard from '../components/Dashboard/KPICard';
import DashboardCharts from '../components/Dashboard/Charts';
import type { DashboardStats, ModuleStat, DailyTrend } from '../types';
import { CheckCircle, XCircle, Play, AlertTriangle, Percent, Activity } from 'lucide-react';

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [modules, setModules] = useState<ModuleStat[]>([]);
  const [trends, setTrends] = useState<DailyTrend[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const [statsRes, modRes, trendRes] = await Promise.all([
          api.get('/dashboard/stats'),
          api.get('/dashboard/module-stats'),
          api.get('/dashboard/trend'),
        ]);
        setStats(statsRes.data);
        setModules(modRes.data);
        setTrends(trendRes.data);
      } catch (err: any) {
        setError('Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) return <Loading message="Loading dashboard..." />;

  return (
    <ErrorBoundary>
      <div className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-white mb-6">Dashboard</h1>

        {error && <p className="text-red-400 mb-4">{error}</p>}

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <KPICard title="Total Executions" value={stats?.total_executions ?? 0} icon={<Activity className="w-5 h-5" />} color="indigo" />
          <KPICard title="Passed" value={stats?.passed ?? 0} icon={<CheckCircle className="w-5 h-5" />} color="green" />
          <KPICard title="Failed" value={stats?.failed ?? 0} icon={<XCircle className="w-5 h-5" />} color="red" />
          <KPICard title="Running" value={stats?.running ?? 0} icon={<Play className="w-5 h-5" />} color="blue" />
          <KPICard title="Blocked" value={stats?.blocked ?? 0} icon={<AlertTriangle className="w-5 h-5" />} color="yellow" />
          <KPICard title="Total Test Cases" value={stats?.total_test_cases ?? 0} icon={<Activity className="w-5 h-5" />} color="purple" />
          <KPICard title="Pass %" value={`${stats?.pass_percentage ?? 0}%`} icon={<Percent className="w-5 h-5" />} color="green" />
          <KPICard title="Fail %" value={`${stats?.fail_percentage ?? 0}%`} icon={<Percent className="w-5 h-5" />} color="red" />
        </div>

        <DashboardCharts stats={stats} modules={modules} trends={trends} />
      </div>
    </ErrorBoundary>
  );
}
