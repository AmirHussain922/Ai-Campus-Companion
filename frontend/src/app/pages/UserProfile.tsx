import { motion } from "motion/react";
import { useStore } from "../store";
import { LogOut, User as UserIcon, Settings, Shield, Bell, HelpCircle, Mail, Key } from "lucide-react";
import { useNavigate, Link } from "react-router";

export default function UserProfile() {
  const user = useStore(state => state.user);
  const myCompanions = useStore(state => state.myCompanions);
  const logout = useStore(state => state.logout);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  const totalLevels = myCompanions.reduce((acc, curr) => acc + curr.level, 0);
  const storiesUnlocked = myCompanions.reduce((acc, curr) => acc + curr.episodes.filter(e => e.unlocked).length, 0);
  
  const initials = user?.name?.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase() || 'U';

  return (
    <div className="flex-1 overflow-y-auto bg-zinc-950 p-4 sm:p-6 md:p-8 text-zinc-50 relative h-full">
      <div className="max-w-4xl mx-auto space-y-8">
        
        {/* Header */}
        <header className="flex flex-col sm:flex-row items-center sm:items-start sm:justify-between gap-6 pb-8 border-b border-zinc-800/50">
          <div className="flex flex-col sm:flex-row items-center sm:items-center gap-6 text-center sm:text-left">
            <motion.div 
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="relative"
            >
              <div className="absolute inset-0 bg-white/10 rounded-full blur-xl" />
              <div className="w-24 h-24 sm:w-32 sm:h-32 rounded-full bg-zinc-800 border-4 border-zinc-900 flex items-center justify-center text-3xl sm:text-5xl font-light text-zinc-400 relative z-10 shadow-xl">
                {initials}
              </div>
            </motion.div>
            
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.1 }}
            >
              <h1 className="text-3xl sm:text-4xl font-light tracking-tighter mb-2">{user?.name || 'User'}</h1>
              <p className="text-zinc-400 flex items-center gap-2 justify-center sm:justify-start">
                <Mail className="w-4 h-4" />
                {user?.email || 'user@example.com'}
              </p>
              <div className="mt-4 inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900 border border-zinc-800 text-xs font-medium text-emerald-400">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Online
              </div>
            </motion.div>
          </div>

          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="flex sm:flex-col gap-3"
          >
            <button 
              onClick={handleLogout}
              className="flex items-center gap-2 px-4 py-2 bg-red-500/10 text-red-400 hover:bg-red-500/20 border border-red-500/20 rounded-xl transition-colors text-sm font-medium"
            >
              <LogOut className="w-4 h-4" />
              Sign Out
            </button>
          </motion.div>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          
          {/* Main Content Area */}
          <div className="md:col-span-2 space-y-8">
            {/* Stats Overview */}
            <motion.section 
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="bg-zinc-900/30 border border-zinc-800 rounded-3xl p-6 sm:p-8"
            >
              <h2 className="text-lg font-medium mb-6 flex items-center gap-2">
                <UserIcon className="w-5 h-5 text-zinc-400" />
                Your Campus Journey
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                <div className="bg-zinc-950 p-4 rounded-2xl border border-zinc-800/50">
                  <div className="text-3xl font-light text-white mb-1">{myCompanions.length}</div>
                  <div className="text-xs text-zinc-500 uppercase tracking-wider font-semibold">Active Companions</div>
                </div>
                <div className="bg-zinc-950 p-4 rounded-2xl border border-zinc-800/50">
                  <div className="text-3xl font-light text-white mb-1">{totalLevels}</div>
                  <div className="text-xs text-zinc-500 uppercase tracking-wider font-semibold">Total Levels</div>
                </div>
                <div className="bg-zinc-950 p-4 rounded-2xl border border-zinc-800/50">
                  <div className="text-3xl font-light text-white mb-1">{storiesUnlocked}</div>
                  <div className="text-xs text-zinc-500 uppercase tracking-wider font-semibold">Stories Unlocked</div>
                </div>
              </div>
            </motion.section>

            {/* Account Settings */}
            <motion.section 
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.4 }}
              className="bg-zinc-900/30 border border-zinc-800 rounded-3xl p-6 sm:p-8"
            >
              <h2 className="text-lg font-medium mb-6 flex items-center gap-2">
                <Settings className="w-5 h-5 text-zinc-400" />
                Account Settings
              </h2>
              <div className="space-y-4">
                <Link to="/app/settings/personal" className="w-full flex items-center justify-between p-4 bg-zinc-950 rounded-2xl border border-zinc-800/50 hover:border-zinc-700 transition-colors group">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-zinc-900 rounded-lg group-hover:bg-zinc-800 transition-colors">
                      <UserIcon className="w-4 h-4 text-zinc-400" />
                    </div>
                    <div className="text-left">
                      <div className="text-sm font-medium text-zinc-200">Personal Information</div>
                      <div className="text-xs text-zinc-500">Update your name and profile details</div>
                    </div>
                  </div>
                  <span className="text-zinc-600 group-hover:text-zinc-400 transition-colors">→</span>
                </Link>

                <Link to="/app/settings/security" className="w-full flex items-center justify-between p-4 bg-zinc-950 rounded-2xl border border-zinc-800/50 hover:border-zinc-700 transition-colors group">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-zinc-900 rounded-lg group-hover:bg-zinc-800 transition-colors">
                      <Key className="w-4 h-4 text-zinc-400" />
                    </div>
                    <div className="text-left">
                      <div className="text-sm font-medium text-zinc-200">Security & Password</div>
                      <div className="text-xs text-zinc-500">Change your password and secure your account</div>
                    </div>
                  </div>
                  <span className="text-zinc-600 group-hover:text-zinc-400 transition-colors">→</span>
                </Link>

                <Link to="/app/settings/notifications" className="w-full flex items-center justify-between p-4 bg-zinc-950 rounded-2xl border border-zinc-800/50 hover:border-zinc-700 transition-colors group">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-zinc-900 rounded-lg group-hover:bg-zinc-800 transition-colors">
                      <Bell className="w-4 h-4 text-zinc-400" />
                    </div>
                    <div className="text-left">
                      <div className="text-sm font-medium text-zinc-200">Notifications</div>
                      <div className="text-xs text-zinc-500">Manage email and push notifications</div>
                    </div>
                  </div>
                  <span className="text-zinc-600 group-hover:text-zinc-400 transition-colors">→</span>
                </Link>
              </div>
            </motion.section>
          </div>

          {/* Right Sidebar */}
          <div className="space-y-8">
            {/* Privacy & Support */}
            <motion.section 
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.5 }}
              className="bg-zinc-900/30 border border-zinc-800 rounded-3xl p-6"
            >
              <h3 className="text-sm font-medium text-zinc-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                <Shield className="w-4 h-4" />
                Privacy & Data
              </h3>
              <p className="text-sm text-zinc-500 mb-4">
                Your chat data and campus journey are securely stored and encrypted.
              </p>
              <button className="text-sm text-purple-400 hover:text-purple-300 transition-colors font-medium">
                Manage Data Preferences
              </button>
            </motion.section>

            <motion.section 
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.6 }}
              className="bg-zinc-900/30 border border-zinc-800 rounded-3xl p-6"
            >
              <h3 className="text-sm font-medium text-zinc-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                <HelpCircle className="w-4 h-4" />
                Support
              </h3>
              <ul className="space-y-3">
                <li>
                  <Link to="/app/support/help" className="text-sm text-zinc-300 hover:text-white transition-colors block py-1">Help Center</Link>
                </li>
                <li>
                  <Link to="/app/support/contact" className="text-sm text-zinc-300 hover:text-white transition-colors block py-1">Contact Support</Link>
                </li>
                <li>
                  <Link to="/app/support/terms" className="text-sm text-zinc-300 hover:text-white transition-colors block py-1">Terms of Service</Link>
                </li>
              </ul>
            </motion.section>
          </div>

        </div>
      </div>
    </div>
  );
}
