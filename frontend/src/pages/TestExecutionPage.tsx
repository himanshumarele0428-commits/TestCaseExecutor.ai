import { useState, useEffect, useRef } from 'react';
import api from '../api/client';
import FileUpload from '../components/Execution/FileUpload';
import TestCasePreview from '../components/Execution/TestCasePreview';
import ExecutionProgress from '../components/Execution/ExecutionProgress';
import ExecutionConsole from '../components/Execution/ExecutionConsole';
import CompletionPopup from '../components/Execution/CompletionPopup';
import { useSSE } from '../hooks/useSSE';
import RAILWAY_URL from '../config';
import type { FileUploadResponse, ExecutionCreateResponse } from '../types';
import { Play, Loader2, Monitor, MonitorOff, ExternalLink } from 'lucide-react';

export default function TestExecutionPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [parsed, setParsed] = useState<FileUploadResponse | null>(null);
  const [execution, setExecution] = useState<ExecutionCreateResponse | null>(null);
  const [uploading, setUploading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [error, setError] = useState('');
  const [showCompletion, setShowCompletion] = useState(false);
  const [headless, setHeadless] = useState(false);

  const { events, connected, done, finalStatus, reset, addEvent } = useSSE(execution?.id ?? null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const startPolling = (execId: string) => {
    pollRef.current = setInterval(async () => {
      try {
        const res = await api.get(`/executions/${execId}`);
        const status = res.data.status;
        if (status === 'COMPLETED' || status === 'FAILED') {
          addEvent({
            type: 'execution_completed',
            execution_id: execId,
            status,
            passed: res.data.passed,
            failed: res.data.failed,
            blocked: res.data.blocked ?? 0,
            duration_seconds: res.data.duration_seconds,
          });
          if (pollRef.current) clearInterval(pollRef.current);
        }
      } catch {
        // ignore
      }
    }, 1500);
  };

  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  useEffect(() => {
    return stopPolling;
  }, []);

  useEffect(() => {
    if (done && executing) {
      setExecuting(false);
      setShowCompletion(true);
      stopPolling();
    }
  }, [done, executing]);

  const handleFileSelect = (file: File | null) => {
    setSelectedFile(file);
    setParsed(null);
    setExecution(null);
    setError('');
    setShowCompletion(false);
    stopPolling();
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setError('');
    setUploading(true);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const res = await api.post<FileUploadResponse>('/files/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setParsed(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to parse file');
    } finally {
      setUploading(false);
    }
  };

  const handleExecute = async () => {
    if (!parsed) return;
    setError('');
    setExecuting(true);
    setShowCompletion(false);
    stopPolling();
    reset();

    try {
      const createRes = await api.post<ExecutionCreateResponse>('/executions', {
        filename: parsed.filename,
        file_content: parsed.file_content,
        parsed_test_cases: parsed.test_cases,
      });
      setExecution(createRes.data);

      await api.post(`/executions/${createRes.data.id}/execute`, { headless });
      startPolling(createRes.data.id);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start execution');
      setExecuting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-white mb-6">Test Execution</h1>

      {!parsed && (
        <FileUpload
          onFileSelect={handleFileSelect}
          onUpload={handleUpload}
          selectedFile={selectedFile}
          uploading={uploading}
          disabled={uploading}
        />
      )}

      {error && (
        <div className="mt-4 p-3 bg-red-900/30 border border-red-700 rounded-lg">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {parsed && (
        <div className="mt-6 space-y-6">
          <TestCasePreview
            filename={parsed.filename}
            testCasesCount={parsed.test_cases_count}
            totalSteps={parsed.total_steps}
            testCases={parsed.test_cases}
          />

          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h3 className="text-white font-semibold mb-3">Browser Mode</h3>
            <div className="flex gap-3">
              <button
                onClick={() => setHeadless(false)}
                disabled={executing}
                className={`flex-1 py-3 rounded-xl font-medium transition-colors flex items-center justify-center gap-2 text-sm ${
                  !headless
                    ? 'bg-indigo-600 text-white border-2 border-indigo-400'
                    : 'bg-gray-800 text-gray-400 border-2 border-gray-700 hover:border-gray-600'
                }`}
              >
                <Monitor className="w-5 h-5" />
                <div className="text-left">
                  <div className="font-semibold">Headed Mode</div>
                  <div className="text-xs opacity-70">See browser execution live</div>
                </div>
              </button>
              <button
                onClick={() => setHeadless(true)}
                disabled={executing}
                className={`flex-1 py-3 rounded-xl font-medium transition-colors flex items-center justify-center gap-2 text-sm ${
                  headless
                    ? 'bg-indigo-600 text-white border-2 border-indigo-400'
                    : 'bg-gray-800 text-gray-400 border-2 border-gray-700 hover:border-gray-600'
                }`}
              >
                <MonitorOff className="w-5 h-5" />
                <div className="text-left">
                  <div className="font-semibold">Headless Mode</div>
                  <div className="text-xs opacity-70">Run silently in background</div>
                </div>
              </button>
            </div>
          </div>

          <button
            onClick={handleExecute}
            disabled={executing}
            className="w-full py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-700 text-white font-semibold rounded-xl transition-colors flex items-center justify-center gap-2 text-lg"
          >
            {executing ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" /> Executing...
              </>
            ) : (
              <>
                <Play className="w-5 h-5" /> Test Execute
              </>
            )}
          </button>

          {executing && !headless && RAILWAY_URL && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
              <div className="flex items-center justify-between p-3 border-b border-gray-800">
                <h3 className="text-white font-semibold flex items-center gap-2">
                  <Monitor className="w-4 h-4 text-indigo-400" /> Live Browser
                </h3>
                <a
                  href={`${RAILWAY_URL}/browser`}
                  target="_blank"
                  rel="noreferrer"
                  className="text-indigo-400 hover:text-indigo-300 text-xs flex items-center gap-1"
                >
                  Open in new tab <ExternalLink className="w-3 h-3" />
                </a>
              </div>
              <iframe
                src={`${RAILWAY_URL}/browser`}
                title="Live Browser"
                className="w-full h-[480px] bg-black"
              />
            </div>
          )}

          {execution && (
            <>
              <ExecutionProgress
                events={events}
                connected={connected}
                done={done}
                finalStatus={finalStatus}
                totalTestCases={execution.total_test_cases}
              />
              <ExecutionConsole events={events} />
            </>
          )}
        </div>
      )}

      <CompletionPopup
        open={showCompletion}
        onClose={() => setShowCompletion(false)}
        executionId={execution?.id ?? ''}
        events={events}
        finalStatus={finalStatus}
      />
    </div>
  );
}
