import { useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import Toast from '../components/Common/Toast';
import { Bot, Loader2, Mail, CheckCircle, ExternalLink } from 'lucide-react';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [devLink, setDevLink] = useState<string | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api.post('/auth/forgot-password', { email, origin: window.location.origin });
      setSent(true);
      if (res.data.dev_reset_link) {
        setDevLink(res.data.dev_reset_link);
        setToast({ message: 'Email delivery unavailable — use the link below', type: 'success' });
      } else {
        setToast({ message: 'Reset link sent to your email', type: 'success' });
      }
    } catch {
      setToast({ message: 'Failed to send reset link', type: 'error' });
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
          <p className="text-gray-400 mt-1">Reset your password</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          {sent ? (
            <div className="text-center py-4">
              <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-3" />
              <h2 className="text-lg font-semibold text-white mb-2">Check your email</h2>
              <p className="text-gray-400 text-sm mb-4">
                We've sent a password reset link to your email address.
              </p>
              {devLink && (
                <div className="mb-4 p-3 bg-gray-800 rounded-lg border border-gray-700">
                  <p className="text-yellow-400 text-xs mb-2">
                    Email delivery is restricted in dev mode. Use the link below:
                  </p>
                  <a
                    href={devLink}
                    className="text-indigo-400 hover:text-indigo-300 text-sm break-all inline-flex items-center gap-1"
                  >
                    <ExternalLink className="w-3 h-3 flex-shrink-0" />
                    {devLink}
                  </a>
                </div>
              )}
              <Link to="/login" className="text-indigo-400 hover:text-indigo-300 text-sm font-medium">
                &larr; Back to sign in
              </Link>
            </div>
          ) : (
            <>
              <div className="mb-6">
                <h2 className="text-lg font-semibold text-white">Forgot password?</h2>
                <p className="text-gray-400 text-sm mt-1">
                  Enter your email and we'll send you a reset link.
                </p>
              </div>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Email</label>
                  <div className="relative">
                    <Mail className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                      placeholder="you@company.com"
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
                  Send Reset Link
                </button>
              </form>
              <div className="mt-4 text-center">
                <Link to="/login" className="text-indigo-400 hover:text-indigo-300 text-sm">
                  &larr; Back to sign in
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
