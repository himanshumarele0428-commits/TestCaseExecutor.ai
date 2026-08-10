import { useState, useEffect } from 'react';
import api from '../api/client';
import { Loading } from '../components/Common/Loading';
import Modal from '../components/Common/Modal';
import ConfirmModal from '../components/Common/ConfirmModal';
import { Image, Download, Camera, Trash2, Trash } from 'lucide-react';

interface ScreenshotInfo {
  id: string;
  step_id: string;
  execution_id: string;
  filename: string;
  captured_at: string;
}

interface ExecutionGroup {
  execution_id: string;
  screenshots: ScreenshotInfo[];
}

export default function ScreenshotsPage() {
  const [groups, setGroups] = useState<ExecutionGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [preview, setPreview] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const [deleteAllTarget, setDeleteAllTarget] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    loadScreenshots();
  }, []);

  const loadScreenshots = async () => {
    try {
      const execRes = await api.get('/executions', { params: { page: 1, page_size: 1000 } });
      const executions = execRes.data.items ?? execRes.data;

      const allGroups: ExecutionGroup[] = [];
      for (const exec of executions) {
        try {
          const ssRes = await api.get(`/screenshots?execution_id=${exec.id}`);
          if (ssRes.data.length > 0) {
            allGroups.push({ execution_id: exec.id, screenshots: ssRes.data });
          }
        } catch {}
      }
      setGroups(allGroups);
    } catch {
    } finally {
      setLoading(false);
    }
  };

  const getScreenshotUrl = (executionId: string, stepId: string) => {
    const token = localStorage.getItem('token');
    return `/api/v1/screenshots/${executionId}/${stepId}?token=${token}`;
  };

  const handleDeleteSingle = async (screenshotId: string) => {
    setDeleting(true);
    try {
      await api.delete(`/screenshots/${screenshotId}`);
      loadScreenshots();
      setDeleteTarget(null);
    } catch {
      alert('Failed to delete screenshot');
    } finally {
      setDeleting(false);
    }
  };

  const handleDeleteAll = async (executionId: string) => {
    setDeleting(true);
    try {
      await api.delete(`/screenshots/execution/${executionId}`);
      loadScreenshots();
      setDeleteAllTarget(null);
    } catch {
      alert('Failed to delete screenshots');
    } finally {
      setDeleting(false);
    }
  };

  const handleDownload = async (screenshotId: string, filename: string) => {
    try {
      const res = await api.get(`/screenshots/download/${screenshotId}`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch {
      alert('Failed to download screenshot');
    }
  };

  if (loading) return <Loading message="Loading screenshots..." />;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-white mb-6">Screenshots</h1>

      {groups.length === 0 ? (
        <div className="text-center py-20 text-gray-500">
          <Camera className="w-12 h-12 mx-auto mb-3 text-gray-600" />
          <p className="text-lg mb-2">No screenshots yet</p>
          <p className="text-sm">Screenshots are captured automatically during test execution</p>
        </div>
      ) : (
        <div className="space-y-6">
          {groups.map((group) => (
            <div key={group.execution_id} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-white font-medium">
                  Execution: <span className="font-mono text-sm text-indigo-400">{group.execution_id.slice(0, 12)}...</span>
                  <span className="text-gray-500 ml-2">({group.screenshots.length} screenshots)</span>
                </h3>
                <button
                  onClick={() => setDeleteAllTarget(group.execution_id)}
                  disabled={deleting}
                  className="flex items-center gap-1 px-3 py-1.5 text-xs bg-red-900/30 hover:bg-red-900/50 text-red-400 border border-red-800 rounded-lg transition-colors disabled:opacity-50"
                >
                  <Trash className="w-3 h-3" /> Delete All
                </button>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
                {group.screenshots.map((ss) => (
                  <div key={ss.id} className="group relative bg-gray-800 rounded-lg overflow-hidden border border-gray-700 hover:border-indigo-500 transition-colors cursor-pointer">
                    <img
                      src={getScreenshotUrl(group.execution_id, ss.step_id)}
                      alt={ss.filename}
                      className="w-full h-32 object-cover"
                      onClick={() => setPreview(getScreenshotUrl(group.execution_id, ss.step_id))}
                    />
                    <div className="p-2">
                      <p className="text-gray-400 text-xs truncate">{ss.filename}</p>
                      <p className="text-gray-600 text-[10px]">{new Date(ss.captured_at).toLocaleString()}</p>
                    </div>
                    <div className="absolute top-1 right-1 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={(e) => { e.preventDefault(); handleDownload(ss.id, ss.filename); }}
                        className="bg-gray-900/80 rounded p-1 text-indigo-400 hover:text-indigo-300"
                        title="Download"
                      >
                        <Download className="w-3 h-3" />
                      </button>
                      <button
                        onClick={(e) => { e.preventDefault(); setDeleteTarget(ss.id); }}
                        className="bg-gray-900/80 rounded p-1 text-red-400 hover:text-red-300"
                        title="Delete"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal open={!!preview} onClose={() => setPreview(null)} title="Screenshot Preview" size="lg">
        {preview && <img src={preview} alt="Screenshot preview" className="w-full rounded-lg" />}
      </Modal>

      <ConfirmModal
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={() => handleDeleteSingle(deleteTarget!)}
        title="Delete Screenshot"
        message="Are you sure you want to delete this screenshot? This action cannot be undone."
        confirmLabel="Delete"
        loading={deleting}
      />

      <ConfirmModal
        open={!!deleteAllTarget}
        onClose={() => setDeleteAllTarget(null)}
        onConfirm={() => handleDeleteAll(deleteAllTarget!)}
        title="Delete All Screenshots"
        message="Are you sure you want to delete all screenshots from this execution? This action cannot be undone."
        confirmLabel="Delete All"
        loading={deleting}
      />
    </div>
  );
}
