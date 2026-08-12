import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import api from '../api/client';
import { Loading } from '../components/Common/Loading';
import StatusBadge from '../components/Common/StatusBadge';
import Modal from '../components/Common/Modal';
import type { ExecutionResponse, StepResponse } from '../types';
import { Clock, CheckCircle, XCircle, SkipForward, Image, ChevronDown, ChevronRight, Download } from 'lucide-react';

export default function ExecutionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [execution, setExecution] = useState<ExecutionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedTC, setExpandedTC] = useState<string | null>(null);
  const [previewScreenshot, setPreviewScreenshot] = useState<{ stepId: string; filename: string } | null>(null);

  useEffect(() => {
    if (!id) return;
    api.get(`/executions/${id}`)
      .then((res) => setExecution(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <Loading message="Loading execution details..." />;
  if (!execution) return <p className="text-center text-red-400 py-20">Execution not found</p>;

  const getScreenshotUrl = (stepId: string) => {
    const token = localStorage.getItem('token');
    const railwayUrl = import.meta.env.VITE_RAILWAY_URL || '';
    if (railwayUrl) {
      return `${railwayUrl}/screenshots/${execution.id}/${stepId}?token=${token}`;
    }
    return `/api/v1/screenshots/${execution.id}/${stepId}?token=${token}`;
  };

  const StepRow = ({ step }: { step: StepResponse }) => (
    <div className="border-t border-gray-700/50 py-2">
      <div className="flex items-center gap-3">
        <span className="text-gray-500 text-xs font-mono w-6">#{step.order_index}</span>
        <div className="flex-1">
          <p className="text-gray-300 text-sm">{step.description}</p>
          {step.error_message && <p className="text-red-400 text-xs mt-0.5">{step.error_message}</p>}
        </div>
        <StatusBadge status={step.status} />
        {step.duration_ms && <span className="text-gray-500 text-xs">{(step.duration_ms / 1000).toFixed(1)}s</span>}
        {step.screenshots.length > 0 && (
          <button
            onClick={() => setPreviewScreenshot({ stepId: step.id, filename: step.screenshots[0].filename })}
            className="text-indigo-400 hover:text-indigo-300"
            title="View screenshot"
          >
            <Image className="w-4 h-4" />
          </button>
        )}
        <span className="flex-shrink-0">
          {step.status === 'PASSED' ? <CheckCircle className="w-4 h-4 text-green-400" /> :
           step.status === 'FAILED' ? <XCircle className="w-4 h-4 text-red-400" /> :
           step.status === 'SKIPPED' ? <SkipForward className="w-4 h-4 text-yellow-400" /> :
           <Clock className="w-4 h-4 text-gray-500" />}
        </span>
      </div>
    </div>
  );

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Execution Details</h1>
        <button
          onClick={async () => {
            try {
              const res = await api.get(`/executions/${execution.id}/export`, { responseType: 'blob' });
              const url = window.URL.createObjectURL(new Blob([res.data]));
              const a = document.createElement('a');
              a.href = url;
              a.download = `execution_${execution.id.slice(0, 8)}_report.csv`;
              document.body.appendChild(a);
              a.click();
              window.URL.revokeObjectURL(url);
              document.body.removeChild(a);
            } catch {
              alert('Failed to export report');
            }
          }}
          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm rounded-lg flex items-center gap-2 transition-colors"
        >
          <Download className="w-4 h-4" /> Export CSV
        </button>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div><p className="text-gray-400 text-xs">File</p><p className="text-white">{execution.filename}</p></div>
          <div><p className="text-gray-400 text-xs">Status</p><StatusBadge status={execution.status} /></div>
          <div><p className="text-gray-400 text-xs">Duration</p><p className="text-white">{execution.duration_seconds?.toFixed(1) ?? '-'}s</p></div>
          <div><p className="text-gray-400 text-xs">Date</p><p className="text-white">{execution.created_at ? new Date(execution.created_at).toLocaleString() : '-'}</p></div>
        </div>
        <div className="grid grid-cols-4 gap-4 mt-4 pt-4 border-t border-gray-800">
          <div className="text-center"><p className="text-2xl font-bold text-white">{execution.total_test_cases}</p><p className="text-xs text-gray-400">Total</p></div>
          <div className="text-center"><p className="text-2xl font-bold text-green-400">{execution.passed}</p><p className="text-xs text-gray-400">Passed</p></div>
          <div className="text-center"><p className="text-2xl font-bold text-red-400">{execution.failed}</p><p className="text-xs text-gray-400">Failed</p></div>
          <div className="text-center"><p className="text-2xl font-bold text-yellow-400">{execution.blocked}</p><p className="text-xs text-gray-400">Blocked</p></div>
        </div>
      </div>

      <div className="space-y-4">
        {execution.test_cases.map((tc) => (
          <div key={tc.id} className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
            <button
              onClick={() => setExpandedTC(expandedTC === tc.id ? null : tc.id)}
              className="w-full flex items-center justify-between p-4 hover:bg-gray-800/50 transition-colors"
            >
              <div className="flex items-center gap-3">
                {expandedTC === tc.id ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />}
                <span className="text-white font-medium">{tc.name}</span>
                {tc.module && <span className="text-xs text-indigo-400 bg-indigo-900/30 px-2 py-0.5 rounded">{tc.module}</span>}
              </div>
              <div className="flex items-center gap-3">
                <span className="text-sm text-gray-400">{tc.passed_steps}/{tc.total_steps} passed</span>
                <StatusBadge status={tc.status} />
              </div>
            </button>
            {expandedTC === tc.id && (
              <div className="px-4 pb-4 border-t border-gray-800">
                {tc.steps.map((step) => (
                  <StepRow key={step.id} step={step} />
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <Modal
        open={!!previewScreenshot}
        onClose={() => setPreviewScreenshot(null)}
        title="Screenshot"
        size="lg"
      >
        {previewScreenshot && (
          <img
            src={getScreenshotUrl(previewScreenshot.stepId)}
            alt={`Step screenshot`}
            className="w-full rounded-lg"
          />
        )}
      </Modal>
    </div>
  );
}
