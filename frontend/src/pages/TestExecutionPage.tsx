import { useState, useEffect, useRef } from 'react';
import api from '../api/client';
import FileUpload from '../components/Execution/FileUpload';
import TestCasePreview from '../components/Execution/TestCasePreview';
import ExecutionProgress from '../components/Execution/ExecutionProgress';
import ExecutionConsole from '../components/Execution/ExecutionConsole';
import CompletionPopup from '../components/Execution/CompletionPopup';
import { useSSE } from '../hooks/useSSE';
import type { FileUploadResponse, ExecutionCreateResponse } from '../types';
import { Play, Loader2 } from 'lucide-react';

export default function TestExecutionPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [parsed, setParsed] = useState<FileUploadResponse | null>(null);
  const [execution, setExecution] = useState<ExecutionCreateResponse | null>(null);
  const [uploading, setUploading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [error, setError] = useState('');
  const [showCompletion, setShowCompletion] = useState(false);

  const { events, connected, done, reset, addEvent } = useSSE(execution?.id ?? null);
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

      await api.post(`/executions/${createRes.data.id}/execute`);
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

          {execution && (
            <>
              <ExecutionProgress
                events={events}
                connected={connected}
                done={done}
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
      />
    </div>
  );
}
