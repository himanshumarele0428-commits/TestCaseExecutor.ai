import { useState, useEffect } from 'react';
import api from '../api/client';
import { Loading } from '../components/Common/Loading';
import Modal from '../components/Common/Modal';
import { useAuth } from '../contexts/AuthContext';
import { Image, Download, Camera } from 'lucide-react';

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
  const { user } = useAuth();

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

  const getScreenshotUrl = (executionId: string, stepId: string) =>
    `/api/v1/screenshots/${executionId}/${stepId}`;

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
              <h3 className="text-white font-medium mb-3">
                Execution: <span className="font-mono text-sm text-indigo-400">{group.execution_id.slice(0, 12)}...</span>
                <span className="text-gray-500 ml-2">({group.screenshots.length} screenshots)</span>
              </h3>
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
                    <a
                      href={`/api/v1/screenshots/download/${ss.id}`}
                      download
                      className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 bg-gray-900/80 rounded p-1 text-indigo-400 hover:text-indigo-300"
                    >
                      <Download className="w-3 h-3" />
                    </a>
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
    </div>
  );
}
