import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';
import { Loading } from '../components/Common/Loading';
import StatusBadge from '../components/Common/StatusBadge';
import type { ExecutionListItem } from '../types';
import { Eye, RefreshCw, Trash2, ChevronLeft, ChevronRight } from 'lucide-react';

const PAGE_SIZE = 10;

export default function ExecutionHistoryPage() {
  const [executions, setExecutions] = useState<ExecutionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [rerunning, setRerunning] = useState<string | null>(null);
  const navigate = useNavigate();

  const fetchExecutions = useCallback(async (p: number) => {
    setLoading(true);
    try {
      const res = await api.get('/executions', { params: { page: p, page_size: PAGE_SIZE } });
      setExecutions(res.data.items);
      setTotalPages(res.data.total_pages);
      setTotal(res.data.total);
    } catch {
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchExecutions(page);
  }, [page, fetchExecutions]);

  const handleRerun = async (executionId: string) => {
    setRerunning(executionId);
    try {
      const res = await api.post(`/executions/${executionId}/rerun`);
      navigate(`/execution/${res.data.execution_id}`);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to re-run execution');
    } finally {
      setRerunning(null);
    }
  };

  const handleDelete = async (executionId: string) => {
    if (!confirm('Delete this execution and all its results?')) return;
    try {
      await api.delete(`/executions/${executionId}`);
      fetchExecutions(page);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete execution');
    }
  };

  if (loading && executions.length === 0) return <Loading message="Loading execution history..." />;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Execution History</h1>
        {total > 0 && <span className="text-gray-400 text-sm">{total} total executions</span>}
      </div>

      {executions.length === 0 ? (
        <div className="text-center py-20 text-gray-500">
          <p className="text-lg mb-2">No executions yet</p>
          <p className="text-sm">Upload a test file and execute it to see results here</p>
        </div>
      ) : (
        <>
          <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-800">
                    <th className="text-left px-4 py-3 text-gray-400 font-medium">ID</th>
                    <th className="text-left px-4 py-3 text-gray-400 font-medium">File</th>
                    <th className="text-left px-4 py-3 text-gray-400 font-medium">Date</th>
                    <th className="text-center px-4 py-3 text-gray-400 font-medium">Total</th>
                    <th className="text-center px-4 py-3 text-gray-400 font-medium">Passed</th>
                    <th className="text-center px-4 py-3 text-gray-400 font-medium">Failed</th>
                    <th className="text-center px-4 py-3 text-gray-400 font-medium">Duration</th>
                    <th className="text-center px-4 py-3 text-gray-400 font-medium">Status</th>
                    <th className="text-center px-4 py-3 text-gray-400 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {executions.map((exec) => (
                    <tr key={exec.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                      <td className="px-4 py-3 text-gray-300 font-mono text-xs">{exec.id.slice(0, 8)}...</td>
                      <td className="px-4 py-3 text-gray-300 max-w-[200px] truncate">{exec.filename}</td>
                      <td className="px-4 py-3 text-gray-400 whitespace-nowrap">
                        {exec.created_at ? new Date(exec.created_at).toLocaleString() : '-'}
                      </td>
                      <td className="px-4 py-3 text-center text-gray-300">{exec.total_test_cases}</td>
                      <td className="px-4 py-3 text-center text-green-400">{exec.passed}</td>
                      <td className="px-4 py-3 text-center text-red-400">{exec.failed}</td>
                      <td className="px-4 py-3 text-center text-gray-400">
                        {exec.duration_seconds != null ? `${exec.duration_seconds.toFixed(1)}s` : '-'}
                      </td>
                      <td className="px-4 py-3 text-center"><StatusBadge status={exec.status} /></td>
                      <td className="px-4 py-3 text-center">
                        <div className="flex items-center justify-center gap-2">
                          <button
                            onClick={() => navigate(`/execution/${exec.id}`)}
                            className="text-indigo-400 hover:text-indigo-300 p-1"
                            title="View details"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleRerun(executionId)}
                            disabled={rerunning === exec.id}
                            className="text-yellow-400 hover:text-yellow-300 p-1"
                            title="Re-run"
                          >
                            <RefreshCw className={`w-4 h-4 ${rerunning === exec.id ? 'animate-spin' : ''}`} />
                          </button>
                          <button
                            onClick={() => handleDelete(exec.id)}
                            className="text-red-400 hover:text-red-300 p-1"
                            title="Delete"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-4 mt-6">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="flex items-center gap-1 px-3 py-2 text-sm bg-gray-800 text-gray-300 rounded-lg hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-4 h-4" /> Prev
              </button>
              <span className="text-gray-400 text-sm">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="flex items-center gap-1 px-3 py-2 text-sm bg-gray-800 text-gray-300 rounded-lg hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Next <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
