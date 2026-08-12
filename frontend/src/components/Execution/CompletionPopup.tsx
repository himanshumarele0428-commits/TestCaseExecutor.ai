import { useNavigate } from 'react-router-dom';
import api from '../../api/client';
import Modal from '../Common/Modal';
import { CheckCircle, XCircle, Clock, BarChart3, Image, LayoutDashboard, Download } from 'lucide-react';
import type { SSEEvent } from '../../types';

interface Props {
  open: boolean;
  onClose: () => void;
  executionId: string;
  events: SSEEvent[];
  finalStatus: string | null;
}

export default function CompletionPopup({ open, onClose, executionId, events, finalStatus }: Props) {
  const navigate = useNavigate();
  const finalEvent = events.find((e) => e.type === 'execution_completed');
  const passed = finalEvent?.passed ?? 0;
  const failed = finalEvent?.failed ?? 0;
  const duration = finalEvent?.duration_seconds ?? 0;
  const error = finalEvent?.error;
  const isInfraFailure = finalStatus === 'FAILED';
  const total = passed + failed;
  const allPassed = !isInfraFailure && failed === 0 && passed > 0;

  const handleExport = async () => {
    try {
      const res = await api.get(`/executions/${executionId}/export`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `execution_${executionId.slice(0, 8)}_report.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch {
      alert('Failed to export report');
    }
  };

  return (
    <Modal open={open} onClose={onClose} title={isInfraFailure ? 'Test Execution Failed' : 'Test Execution Completed'} size="sm">
      <div className="text-center space-y-4">
        {allPassed ? (
          <CheckCircle className="w-12 h-12 text-green-400 mx-auto" />
        ) : (
          <XCircle className="w-12 h-12 text-red-400 mx-auto" />
        )}
        <div>
          <p className="text-white text-lg font-semibold">
            {allPassed ? 'All tests passed!' : isInfraFailure ? 'Execution could not be completed' : 'Test execution completed'}
          </p>
          <p className="text-gray-400 text-sm mt-1">Execution ID: {executionId}</p>
        </div>

        {isInfraFailure && error && (
          <div className="bg-red-900/20 border border-red-800 rounded-lg p-3">
            <p className="text-red-300 text-xs break-words">{error}</p>
          </div>
        )}

        <div className="grid grid-cols-3 gap-3">
          <div className="bg-gray-800 rounded-lg p-3">
            <p className="text-2xl font-bold text-white">{total}</p>
            <p className="text-xs text-gray-400">Total</p>
          </div>
          <div className="bg-gray-800 rounded-lg p-3">
            <p className="text-2xl font-bold text-green-400">{passed}</p>
            <p className="text-xs text-gray-400">Passed</p>
          </div>
          <div className="bg-gray-800 rounded-lg p-3">
            <p className="text-2xl font-bold text-red-400">{failed}</p>
            <p className="text-xs text-gray-400">Failed</p>
          </div>
        </div>

        <p className="text-gray-500 text-sm flex items-center justify-center gap-1">
          <Clock className="w-3 h-3" />
          Duration: {duration.toFixed(1)}s
        </p>

        <div className="flex flex-wrap gap-2 justify-center">
          <button
            onClick={() => navigate(`/execution/${executionId}`)}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm rounded-lg flex items-center gap-2"
          >
            <BarChart3 className="w-4 h-4" /> View Report
          </button>
          <button
            onClick={handleExport}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm rounded-lg flex items-center gap-2"
          >
            <Download className="w-4 h-4" /> Export CSV
          </button>
          <button
            onClick={() => navigate('/screenshots')}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded-lg flex items-center gap-2"
          >
            <Image className="w-4 h-4" /> Screenshots
          </button>
          <button
            onClick={() => navigate('/dashboard')}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded-lg flex items-center gap-2"
          >
            <LayoutDashboard className="w-4 h-4" /> Dashboard
          </button>
        </div>
      </div>
    </Modal>
  );
}
