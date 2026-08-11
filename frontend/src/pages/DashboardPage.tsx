import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, RadialBarChart, RadialBar,
} from 'recharts';
import api from '../api/client';
import { Loading } from '../components/Common/Loading';
import ErrorBoundary from '../components/Common/ErrorBoundary';
import StatusBadge from '../components/Common/StatusBadge';
import type { ExecutionListItem, ExecutionDashboardStats, ExecutionDashboardTestCase } from '../types';
import {
  FileText, CheckCircle, XCircle, Clock, AlertTriangle, Activity,
  BarChart3, Play, Search, Percent, SkipForward, Calendar,
  Layers, Zap, Timer, User, Building, Globe, Hash,
} from 'lucide-react';

const DONUT_COLORS: Record<string, string> = {
  Passed: '#22c55e',
  Failed: '#ef4444',
  Blocked: '#3b82f6',
  Pending: '#eab308',
  Skipped: '#8b5cf6',
  Queued: '#6b7280',
};

const KPI_CONFIG = [
  { key: 'total_test_cases', label: 'Total Test Cases', icon: FileText, color: 'blue', suffix: '% of total cases', suffixKey: null, pctKey: null },
  { key: 'executed', label: 'Executed', icon: Play, color: 'purple', suffix: '% of total cases', suffixKey: null, pctKey: 'executed_percentage' as const },
  { key: 'pending', label: 'Pending', icon: Clock, color: 'yellow', suffix: '% of total cases', suffixKey: null, pctKey: 'pending_percentage' as const },
  { key: 'passed', label: 'Passed', icon: CheckCircle, color: 'green', suffix: '% of executed', suffixKey: null, pctKey: 'pass_rate_of_executed' as const },
  { key: 'failed', label: 'Failed', icon: XCircle, color: 'red', suffix: '% of executed', suffixKey: null, pctKey: 'fail_percentage' as const },
  { key: 'blocked', label: 'Blocked', icon: AlertTriangle, color: 'slate', suffix: '% of total cases', suffixKey: null, pctKey: 'blocked_percentage' as const },
] as const;

const colorMap: Record<string, { border: string; bg: string; icon: string; bar: string }> = {
  blue: { border: 'border-l-blue-500', bg: 'bg-blue-500/10', icon: 'text-blue-400', bar: 'bg-blue-500' },
  purple: { border: 'border-l-purple-500', bg: 'bg-purple-500/10', icon: 'text-purple-400', bar: 'bg-purple-500' },
  yellow: { border: 'border-l-yellow-500', bg: 'bg-yellow-500/10', icon: 'text-yellow-400', bar: 'bg-yellow-500' },
  green: { border: 'border-l-green-500', bg: 'bg-green-500/10', icon: 'text-green-400', bar: 'bg-green-500' },
  red: { border: 'border-l-red-500', bg: 'bg-red-500/10', icon: 'text-red-400', bar: 'bg-red-500' },
  slate: { border: 'border-l-slate-500', bg: 'bg-slate-500/10', icon: 'text-slate-400', bar: 'bg-slate-500' },
};

const FAILED_COLUMNS = [
  { key: 'name' as const, label: 'Test Case Name', className: '' },
  { key: 'module' as const, label: 'Module', className: '' },
  { key: 'priority' as const, label: 'Priority', className: '' },
  { key: 'failed_steps' as const, label: 'Failed Steps', className: '' },
];

export default function DashboardPage() {
  const navigate = useNavigate();
  const [executions, setExecutions] = useState<ExecutionListItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [execStats, setExecStats] = useState<ExecutionDashboardStats | null>(null);
  const [loadingExecs, setLoadingExecs] = useState(true);
  const [loadingStats, setLoadingStats] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const res = await api.get('/executions', { params: { page: 1, page_size: 100 } });
        setExecutions(res.data.items || []);
      } catch {
        setError('Failed to load executions');
      } finally {
        setLoadingExecs(false);
      }
    })();
  }, []);

  useEffect(() => {
    if (!selectedId) { setExecStats(null); return; }
    (async () => {
      setLoadingStats(true);
      setError('');
      try {
        const res = await api.get(`/dashboard/execution/${selectedId}`);
        setExecStats(res.data);
      } catch {
        setError('Failed to load execution statistics');
        setExecStats(null);
      } finally {
        setLoadingStats(false);
      }
    })();
  }, [selectedId]);

  if (loadingExecs) return <Loading message="Loading dashboard..." />;

  const failedTests: ExecutionDashboardTestCase[] = execStats?.test_cases.filter((tc) => tc.status === 'FAILED') ?? [];

  const donutData = execStats
    ? (['Passed', 'Failed', 'Blocked', 'Pending', 'Skipped'] as const)
        .map((name) => {
          const map: Record<string, number> = {
            Passed: execStats.passed, Failed: execStats.failed, Blocked: execStats.blocked,
            Pending: execStats.pending, Skipped: execStats.skipped,
          };
          return { name, value: map[name] };
        })
        .filter((d) => d.value > 0)
    : [];

  const moduleData = (execStats?.module_breakdown ?? []).map((m) => ({
    name: m.module,
    Passed: m.passed,
    Failed: m.failed,
    Pending: m.pending,
    Blocked: m.blocked,
  }));

  const handleExport = async () => {
    if (!selectedId) return;
    try {
      const res = await api.get(`/executions/${selectedId}/export`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `execution_${selectedId.slice(0, 8)}_report.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      setError('Failed to export report');
    }
  };
  const execTotal = execStats?.total_test_cases ?? 1;
  const execPct = execStats?.executed_percentage ?? 0;

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-[#0f172a] text-white">

        {/* ===== HEADER ===== */}
        <div className="px-6 py-6 border-b border-slate-800">
          <div className="max-w-[1600px] mx-auto flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Test Execution Dashboard</h1>
              <p className="text-slate-400 text-sm mt-1">Real-time overview of test execution status and results</p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => { setSelectedId(null); setExecStats(null); }}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-sm font-medium rounded-lg flex items-center gap-2 transition-colors"
              >
                <Zap className="w-4 h-4" /> Refresh
              </button>
              <button
                onClick={handleExport}
                disabled={!selectedId}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-sm font-medium rounded-lg flex items-center gap-2 transition-colors border border-slate-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <FileText className="w-4 h-4" /> Export Report
              </button>
            </div>
          </div>
        </div>

        <div className="max-w-[1600px] mx-auto px-6 py-6">

          {/* ===== FILTER BAR ===== */}
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 mb-6 flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <Hash className="w-4 h-4 text-slate-400" />
              <span className="text-slate-400 text-sm">Execution:</span>
              {executions.length === 0 ? (
                <span className="text-slate-500 text-sm ml-1">No executions available</span>
              ) : (
                <select
                  value={selectedId ?? ''}
                  onChange={(e) => setSelectedId(e.target.value || null)}
                  className="bg-slate-700 border border-slate-600 rounded-lg text-white text-sm px-3 py-1.5 focus:ring-2 focus:ring-blue-500 outline-none cursor-pointer min-w-[320px]"
                >
                  <option value="">-- Select execution --</option>
                  {executions.map((e) => (
                    <option key={e.id} value={e.id}>
                      {e.id.slice(0, 8)} — {e.filename} — {e.status}
                    </option>
                  ))}
                </select>
              )}
            </div>
            {execStats?.created_at && (
              <div className="flex items-center gap-2 text-slate-400 text-sm">
                <Calendar className="w-4 h-4" />
                <span>{new Date(execStats.created_at).toLocaleString()}</span>
              </div>
            )}
            {execStats && (
              <span className={`ml-auto text-xs font-medium px-3 py-1 rounded-full border ${
                execStats.status === 'COMPLETED' ? 'bg-green-500/10 text-green-400 border-green-700' :
                execStats.status === 'RUNNING' ? 'bg-blue-500/10 text-blue-400 border-blue-700' :
                execStats.status === 'FAILED' ? 'bg-red-500/10 text-red-400 border-red-700' :
                'bg-slate-500/10 text-slate-400 border-slate-700'
              }`}>
                {execStats.status}
              </span>
            )}
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-700 rounded-lg p-4 mb-6 flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          {!selectedId && executions.length > 0 && (
            <div className="text-center py-24">
              <BarChart3 className="w-20 h-20 text-slate-700 mx-auto mb-5" />
              <p className="text-slate-500 text-lg">Select an execution above to view its dashboard</p>
            </div>
          )}

          {selectedId && loadingStats && <Loading message="Loading execution stats..." />}

          {execStats && !loadingStats && (
            <>
              {/* ===== KPI CARDS ===== */}
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
                {KPI_CONFIG.map((card) => {
                  const c = colorMap[card.color];
                  const value = Number(execStats[card.key]) || 0;
                  let subtext = card.suffix;
                  if (card.pctKey) {
                    const pct = execStats[card.pctKey] ?? 0;
                    subtext = `${pct}% of ${card.key === 'passed' || card.key === 'failed' ? 'executed' : 'total cases'}`;
                  }
                  return (
                    <div
                      key={card.key}
                      className={`bg-slate-800/60 border border-slate-700 ${c.border} border-l-4 rounded-xl p-4 flex flex-col justify-between hover:border-slate-600 transition-colors`}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                          {card.label}
                        </span>
                        <card.icon className={`w-5 h-5 ${c.icon}`} />
                      </div>
                      <p className="text-2xl font-bold text-white">{value}</p>
                      <p className="text-xs text-slate-500 mt-1">{subtext}</p>
                    </div>
                  );
                })}
              </div>

              {/* ===== CHARTS ROW ===== */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">

                {/* --- Execution Summary Donut --- */}
                <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
                  <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                    <Activity className="w-4 h-4 text-blue-400" />
                    Execution Summary
                  </h3>
                  <div className="relative flex justify-center">
                    <ResponsiveContainer width="100%" height={220}>
                      <PieChart>
                        <Pie
                          data={donutData}
                          cx="50%" cy="50%" innerRadius={55} outerRadius={85}
                          paddingAngle={3} dataKey="value" stroke="none"
                        >
                          {donutData.map((entry) => (
                            <Cell key={entry.name} fill={DONUT_COLORS[entry.name] || '#6b7280'} />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#e2e8f0' }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                      <p className="text-2xl font-bold text-white">{execStats.pass_rate_of_executed}%</p>
                      <p className="text-xs text-slate-400">Pass Rate</p>
                    </div>
                  </div>
                  <div className="space-y-2 mt-4">
                    {donutData.map((entry) => {
                      const total = donutData.reduce((s, d) => s + d.value, 0);
                      const pct = total > 0 ? ((entry.value / execTotal) * 100).toFixed(1) : '0';
                      return (
                        <div key={entry.name} className="flex items-center justify-between text-xs">
                          <div className="flex items-center gap-2">
                            <span className="w-2.5 h-2.5 rounded-full" style={{ background: DONUT_COLORS[entry.name] }} />
                            <span className="text-slate-300">{entry.name}</span>
                          </div>
                          <span className="text-slate-400">{entry.value} ({pct}%)</span>
                        </div>
                      );
                    })}
                  </div>
                  <div className="mt-4 pt-3 border-t border-slate-700">
                    <div className="flex items-center justify-between text-xs mb-1.5">
                      <span className="text-slate-400">Execution Completion</span>
                      <span className="text-slate-300 font-medium">{execPct}%</span>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-2">
                      <div className="bg-blue-500 h-2 rounded-full transition-all duration-500" style={{ width: `${execPct}%` }} />
                    </div>
                  </div>
                </div>

                {/* --- Module-wise Bar Chart --- */}
                <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
                  <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                    <Layers className="w-4 h-4 text-purple-400" />
                    Module-wise Execution
                  </h3>
                  {moduleData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={280}>
                      <BarChart data={moduleData} layout="vertical" margin={{ left: 10, right: 10 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                        <XAxis type="number" stroke="#64748b" fontSize={11} />
                        <YAxis type="category" dataKey="name" stroke="#94a3b8" fontSize={11} width={90} />
                        <Tooltip
                          contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#e2e8f0', fontSize: 12 }}
                        />
                        <Legend wrapperStyle={{ fontSize: 11 }} />
                        <Bar dataKey="Passed" fill="#22c55e" radius={[0, 3, 3, 0]} barSize={14} />
                        <Bar dataKey="Failed" fill="#ef4444" radius={[0, 3, 3, 0]} barSize={14} />
                        <Bar dataKey="Pending" fill="#eab308" radius={[0, 3, 3, 0]} barSize={14} />
                        <Bar dataKey="Blocked" fill="#3b82f6" radius={[0, 3, 3, 0]} barSize={14} />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <p className="text-slate-500 text-center py-20">No module data</p>
                  )}
                </div>

                {/* --- Status Distribution Donut --- */}
                <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
                  <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-green-400" />
                    Status Distribution
                  </h3>
                  <div className="relative flex justify-center">
                    <ResponsiveContainer width="100%" height={220}>
                      <PieChart>
                        <Pie
                          data={donutData.filter(d => d.name !== 'Pending' && d.name !== 'Skipped')}
                          cx="50%" cy="50%" innerRadius={55} outerRadius={85}
                          paddingAngle={3} dataKey="value" stroke="none"
                        >
                          {donutData.filter(d => d.name !== 'Pending' && d.name !== 'Skipped').map((entry) => (
                            <Cell key={entry.name} fill={DONUT_COLORS[entry.name] || '#6b7280'} />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#e2e8f0' }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                      <p className="text-2xl font-bold text-white">{execStats.executed}</p>
                      <p className="text-xs text-slate-400">Executed</p>
                    </div>
                  </div>
                  <div className="space-y-2 mt-4">
                    {(['Passed', 'Failed', 'Blocked'] as const).map((name) => {
                      const map: Record<string, number> = { Passed: execStats.passed, Failed: execStats.failed, Blocked: execStats.blocked };
                      const pct = execTotal > 0 ? ((map[name] / execTotal) * 100).toFixed(1) : '0';
                      return (
                        <div key={name} className="flex items-center justify-between text-xs">
                          <div className="flex items-center gap-2">
                            <span className="w-2.5 h-2.5 rounded-full" style={{ background: DONUT_COLORS[name] }} />
                            <span className="text-slate-300">{name}</span>
                          </div>
                          <span className="text-slate-400">{pct}%</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* ===== BOTTOM ROW: Module Table + Failed Table + Execution Details ===== */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">

                {/* --- Module Wise Execution Table --- */}
                <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
                  <div className="px-5 py-3 border-b border-slate-700 flex items-center gap-2">
                    <Layers className="w-4 h-4 text-blue-400" />
                    <h3 className="text-sm font-semibold text-white">Module Wise Execution</h3>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-slate-700 text-xs text-slate-400 uppercase tracking-wider">
                          <th className="text-left px-4 py-2.5 font-medium">Module</th>
                          <th className="text-center px-4 py-2.5 font-medium">Total</th>
                          <th className="text-center px-4 py-2.5 font-medium">Passed</th>
                          <th className="text-center px-4 py-2.5 font-medium">Failed</th>
                          <th className="text-center px-4 py-2.5 font-medium">Pending</th>
                          <th className="text-center px-4 py-2.5 font-medium">Pass %</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(execStats?.module_breakdown ?? []).map((m) => {
                          const barColor = m.pass_pct >= 80 ? 'bg-green-500' : m.pass_pct >= 50 ? 'bg-yellow-500' : 'bg-red-500';
                          return (
                            <tr key={m.module} className="border-b border-slate-700/50 hover:bg-slate-700/30 transition-colors">
                              <td className="px-4 py-2.5 text-white font-medium">{m.module}</td>
                              <td className="px-4 py-2.5 text-center text-slate-300">{m.total}</td>
                              <td className="px-4 py-2.5 text-center text-green-400">{m.passed}</td>
                              <td className="px-4 py-2.5 text-center text-red-400">{m.failed}</td>
                              <td className="px-4 py-2.5 text-center text-yellow-400">{m.pending}</td>
                              <td className="px-4 py-2.5 text-center">
                                <div className="flex items-center gap-2">
                                  <div className="flex-1 bg-slate-700 rounded-full h-1.5 min-w-[40px]">
                                    <div className={`h-1.5 rounded-full ${barColor}`} style={{ width: `${m.pass_pct}%` }} />
                                  </div>
                                  <span className="text-xs text-slate-400 w-10 text-right">{m.pass_pct}%</span>
                                </div>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* --- Recent Failed Test Cases Table --- */}
                <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
                  <div className="px-5 py-3 border-b border-slate-700 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <XCircle className="w-4 h-4 text-red-400" />
                      <h3 className="text-sm font-semibold text-white">Failed Test Cases</h3>
                    </div>
                    <span className="bg-red-500/10 text-red-400 text-xs font-medium px-2 py-0.5 rounded-full border border-red-700">
                      {failedTests.length}
                    </span>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-slate-700 text-xs text-slate-400 uppercase tracking-wider">
                          {FAILED_COLUMNS.map((col) => (
                            <th key={col.key} className={`text-left px-4 py-2.5 font-medium ${col.className}`}>{col.label}</th>
                          ))}
                          <th className="text-center px-4 py-2.5 font-medium">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {failedTests.length === 0 ? (
                          <tr>
                            <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                              {execStats.executed > 0 ? 'No failed test cases' : 'No test cases executed yet'}
                            </td>
                          </tr>
                        ) : (
                          failedTests.slice(0, 5).map((tc) => (
                            <tr
                              key={tc.id}
                              onClick={() => navigate(`/execution/${execStats.execution_id}`)}
                              className="border-b border-slate-700/50 hover:bg-slate-700/30 cursor-pointer transition-colors"
                            >
                              <td className="px-4 py-2.5 text-white font-medium truncate max-w-[160px]">{tc.name}</td>
                              <td className="px-4 py-2.5 text-slate-300">{tc.module || '—'}</td>
                              <td className="px-4 py-2.5">
                                <StatusBadge status={tc.priority || '—'} />
                              </td>
                              <td className="px-4 py-2.5 text-red-400 font-medium">{tc.failed_steps}/{tc.total_steps}</td>
                              <td className="px-4 py-2.5 text-center">
                                <StatusBadge status="FAILED" />
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* --- Execution Details --- */}
                <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
                  <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                    <FileText className="w-4 h-4 text-indigo-400" />
                    Execution Details
                  </h3>
                  <div className="space-y-3">
                    {[
                      { label: 'Execution ID', value: execStats.execution_id.slice(0, 16) + '...', icon: Hash },
                      { label: 'File', value: execStats.filename, icon: FileText },
                      { label: 'Status', value: execStats.status, icon: Activity },
                      { label: 'Total Test Cases', value: String(execStats.total_test_cases), icon: Layers },
                      { label: 'Duration', value: execStats.duration || '—', icon: Timer },
                      { label: 'Started', value: execStats.started_at ? new Date(execStats.started_at).toLocaleString() : '—', icon: Calendar },
                      { label: 'Completed', value: execStats.completed_at ? new Date(execStats.completed_at).toLocaleString() : '—', icon: Calendar },
                    ].map((item) => (
                      <div key={item.label} className="flex items-start gap-3">
                        <item.icon className="w-4 h-4 text-slate-500 mt-0.5 flex-shrink-0" />
                        <div className="min-w-0">
                          <p className="text-xs text-slate-500">{item.label}</p>
                          <p className="text-sm text-slate-200 truncate">{item.value}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* ===== ALL TEST CASES TABLE ===== */}
              <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
                <div className="px-5 py-3 border-b border-slate-700 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-indigo-400" />
                    <h3 className="text-sm font-semibold text-white">All Test Cases</h3>
                  </div>
                  <span className="bg-slate-700 text-slate-400 text-xs font-medium px-2 py-0.5 rounded-full border border-slate-600">
                    {execStats.total_test_cases} total
                  </span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-700 text-xs text-slate-400 uppercase tracking-wider">
                        <th className="text-left px-4 py-2.5 font-medium w-10">#</th>
                        <th className="text-left px-4 py-2.5 font-medium">Test Case</th>
                        <th className="text-left px-4 py-2.5 font-medium">Module</th>
                        <th className="text-left px-4 py-2.5 font-medium">Priority</th>
                        <th className="text-center px-4 py-2.5 font-medium">Status</th>
                        <th className="text-center px-4 py-2.5 font-medium">Passed</th>
                        <th className="text-center px-4 py-2.5 font-medium">Failed</th>
                        <th className="text-left px-4 py-2.5 font-medium">Error</th>
                      </tr>
                    </thead>
                    <tbody>
                      {execStats.test_cases.map((tc, idx) => (
                        <tr
                          key={tc.id}
                          onClick={() => navigate(`/execution/${execStats.execution_id}`)}
                          className="border-b border-slate-700/50 hover:bg-slate-700/30 cursor-pointer transition-colors"
                        >
                          <td className="px-4 py-2.5 text-slate-500">{idx + 1}</td>
                          <td className="px-4 py-2.5 text-white font-medium truncate max-w-[220px]">{tc.name}</td>
                          <td className="px-4 py-2.5 text-slate-300">{tc.module || '—'}</td>
                          <td className="px-4 py-2.5">
                            <StatusBadge status={tc.priority || '—'} />
                          </td>
                          <td className="px-4 py-2.5 text-center">
                            <StatusBadge status={tc.status} />
                          </td>
                          <td className="px-4 py-2.5 text-center text-green-400 font-medium">{tc.passed_steps}</td>
                          <td className="px-4 py-2.5 text-center text-red-400 font-medium">{tc.failed_steps}</td>
                          <td className="px-4 py-2.5 text-slate-500 text-xs truncate max-w-[180px]">
                            {tc.error_message || '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </ErrorBoundary>
  );
}
