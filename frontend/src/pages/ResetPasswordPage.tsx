import { useState } from 'react';
import { Link, useSearchParams, Navigate } from 'react-router-dom';
import api from '../api/client';
import Toast from '../components/Common/Toast';
import { Bot, Loader2, Lock, CheckCircle } from 'lucide-react';

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  if (!token) return <Navigate to="/login" replace />;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post('/auth/reset-password', { token, new_password: password });
      setDone(true);
      setToast({ message: 'Password reset successfully', type: 'success' });
    } catch {
      setToast({ message: 'Invalid or expired token', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Bot className="w-12 h-12 text-indigo-400 mx-auto mb-3" />
          <h1 className="text-2xl font-bold text-white">Testcase Executor.AI</h1>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          {done ? (
            <div className="text-center py-4">
              <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-3" />
              <h2 className="text-lg font-semibold text-white mb-2">Password updated!</h2>
              <p className="text-gray-400 text-sm mb-6">
                Your password has been changed successfully.
              </p>
              <Link to="/login" className="text-indigo-400 hover:text-indigo-300 text-sm font-medium">
                &larr; Sign in with new password
              </Link>
            </div>
          ) : (
            <>
              <div className="mb-6">
                <h2 className="text-lg font-semibold text-white">Set new password</h2>
                <p className="text-gray-400 text-sm mt-1">
                  Enter your new password below.
                </p>
              </div>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">New Password</label>
                  <div className="relative">
                    <Lock className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      minLength={6}
                      placeholder="At least 6 characters"
                      className="w-full pl-10 pr-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
                    />
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-800 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                  Reset Password
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
