import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { LayoutDashboard, Play, History, Image, Settings, LogOut, Bot } from 'lucide-react';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
      isActive ? 'bg-indigo-600 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'
    }`;

  return (
    <nav className="bg-gray-900 border-b border-gray-800">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-2 text-white font-bold text-lg">
              <Bot className="w-6 h-6 text-indigo-400" />
              <span>Testcase Executor.AI</span>
            </div>
            <div className="hidden md:flex items-center gap-1">
              <NavLink to="/dashboard" className={linkClass}>
                <LayoutDashboard className="w-4 h-4" /> Dashboard
              </NavLink>
              <NavLink to="/execute" className={linkClass}>
                <Play className="w-4 h-4" /> Test Execution
              </NavLink>
              <NavLink to="/history" className={linkClass}>
                <History className="w-4 h-4" /> History
              </NavLink>
              <NavLink to="/screenshots" className={linkClass}>
                <Image className="w-4 h-4" /> Screenshots
              </NavLink>
              <NavLink to="/ai-config" className={linkClass}>
                <Settings className="w-4 h-4" /> AI Config
              </NavLink>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-gray-400 text-sm hidden sm:block">{user?.full_name}</span>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-3 py-2 text-sm text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" /> Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
