import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Navbar from './components/Layout/Navbar';
import ProtectedRoute from './components/Layout/ProtectedRoute';
import ErrorBoundary from './components/Common/ErrorBoundary';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import DashboardPage from './pages/DashboardPage';
import TestExecutionPage from './pages/TestExecutionPage';
import ExecutionHistoryPage from './pages/ExecutionHistoryPage';
import ExecutionDetailPage from './pages/ExecutionDetailPage';
import ScreenshotsPage from './pages/ScreenshotsPage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import ResetPasswordPage from './pages/ResetPasswordPage';
import AIConfigPage from './pages/AIConfigPage';

function AppLayout() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen bg-gray-950">
      {isAuthenticated && <Navbar />}
      <ErrorBoundary>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/execute" element={<TestExecutionPage />} />
            <Route path="/history" element={<ExecutionHistoryPage />} />
            <Route path="/execution/:id" element={<ExecutionDetailPage />} />
            <Route path="/screenshots" element={<ScreenshotsPage />} />
            <Route path="/ai-config" element={<AIConfigPage />} />
          </Route>
          <Route path="*" element={<Navigate to={isAuthenticated ? '/dashboard' : '/login'} replace />} />
        </Routes>
      </ErrorBoundary>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppLayout />
    </AuthProvider>
  );
}
