import { useState, useEffect } from 'react';
import api from '../api/client';
import { Loading } from '../components/Common/Loading';
import Toast from '../components/Common/Toast';
import type { AiConfigResponse } from '../types';
import { Key, Trash2, Wifi, Loader2, CheckCircle, XCircle } from 'lucide-react';

export default function AIConfigPage() {
  const [config, setConfig] = useState<AiConfigResponse | null>(null);
  const [apiKey, setApiKey] = useState('');
  const [model, setModel] = useState('llama-3.3-70b-versatile');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const res = await api.get<AiConfigResponse>('/ai-config');
      setConfig(res.data);
      if (res.data.model) setModel(res.data.model);
    } catch {
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!apiKey.trim()) {
      setToast({ message: 'API key is required', type: 'error' });
      return;
    }
    setSaving(true);
    try {
      await api.post('/ai-config', { api_key: apiKey, model });
      setToast({ message: 'API key saved successfully', type: 'success' });
      await loadConfig();
      setApiKey('');
    } catch (err: any) {
      setToast({ message: err.response?.data?.detail || 'Failed to save', type: 'error' });
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    const key = apiKey.trim() || '';
    if (!key && !config?.configured) {
      setTestResult({ success: false, message: 'Enter an API key to test' });
      return;
    }
    setTesting(true);
    setTestResult(null);
    try {
      const res = await api.post('/ai-config/test', { api_key: key || 'use-stored', model });
      setTestResult({ success: true, message: res.data.message });
    } catch (err: any) {
      setTestResult({ success: false, message: err.response?.data?.detail || 'Connection failed' });
    } finally {
      setTesting(false);
    }
  };

  const handleRemove = async () => {
    try {
      await api.delete('/ai-config');
      setToast({ message: 'API key removed', type: 'success' });
      await loadConfig();
    } catch {
      setToast({ message: 'Failed to remove key', type: 'error' });
    }
  };

  if (loading) return <Loading message="Loading AI configuration..." />;

  return (
    <div className="max-w-xl mx-auto px-4 py-8">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      <h1 className="text-2xl font-bold text-white mb-6">AI Configuration</h1>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
        <div className="flex items-center gap-3 pb-4 border-b border-gray-800">
          <Key className="w-5 h-5 text-indigo-400" />
          <div>
            <p className="text-white font-medium">Groq API</p>
            <p className="text-sm">
              {config?.configured ? (
                <span className="text-green-400 flex items-center gap-1">
                  <CheckCircle className="w-3 h-3" /> Connected
                </span>
              ) : (
                <span className="text-gray-500 flex items-center gap-1">
                  <XCircle className="w-3 h-3" /> Not Configured
                </span>
              )}
            </p>
          </div>
        </div>

        {config?.key_preview && (
          <div className="bg-gray-800 rounded-lg p-3">
            <p className="text-gray-400 text-xs mb-1">Stored Key</p>
            <p className="text-indigo-400 font-mono text-sm">{config.key_preview}</p>
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Groq API Key</label>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:ring-2 focus:ring-indigo-500 outline-none"
            placeholder={config?.configured ? 'Enter new key to update...' : 'gsk_...'}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Model</label>
          <select
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-indigo-500 outline-none"
          >
            <option value="llama-3.3-70b-versatile">llama-3.3-70b-versatile</option>
            <option value="llama-3.1-8b-instant">llama-3.1-8b-instant</option>
            <option value="mixtral-8x7b-32768">mixtral-8x7b-32768</option>
            <option value="gemma2-9b-it">gemma2-9b-it</option>
          </select>
        </div>

        {testResult && (
          <div className={`p-3 rounded-lg text-sm ${testResult.success ? 'bg-green-900/30 border border-green-700 text-green-400' : 'bg-red-900/30 border border-red-700 text-red-400'}`}>
            {testResult.message}
          </div>
        )}

        <div className="flex gap-2">
          <button
            onClick={handleSave}
            disabled={saving || !apiKey.trim()}
            className="flex-1 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-700 text-white rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Key className="w-4 h-4" />}
            Save
          </button>
          <button
            onClick={handleTest}
            disabled={testing}
            className="flex-1 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            {testing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wifi className="w-4 h-4" />}
            Test Connection
          </button>
          {config?.configured && (
            <button
              onClick={handleRemove}
              className="py-2 px-3 bg-red-900/50 hover:bg-red-800 text-red-400 rounded-lg transition-colors"
              title="Remove API Key"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
