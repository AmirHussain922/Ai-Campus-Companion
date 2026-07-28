import { Link } from "react-router";
import { motion } from "motion/react";
import { ChevronLeft, Key, Shield, AlertTriangle } from "lucide-react";

export default function SettingsSecurity() {
  return (
    <div className="flex-1 overflow-y-auto bg-zinc-950 p-4 sm:p-6 md:p-8 text-zinc-50 relative h-full">
      <div className="max-w-2xl mx-auto space-y-8">
        
        <header className="flex items-center gap-4 border-b border-zinc-800/50 pb-6">
          <Link to="/app/me" className="p-2 bg-zinc-900 hover:bg-zinc-800 rounded-full transition-colors">
            <ChevronLeft className="w-5 h-5 text-zinc-400" />
          </Link>
          <div>
            <h1 className="text-2xl font-light tracking-tight">Security & Password</h1>
            <p className="text-sm text-zinc-400">Change your password and secure your account</p>
          </div>
        </header>

        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          {/* Change Password */}
          <div className="bg-zinc-900/30 border border-zinc-800 rounded-3xl p-6 sm:p-8">
            <h2 className="text-lg font-medium mb-6 flex items-center gap-2">
              <Key className="w-5 h-5 text-zinc-400" />
              Change Password
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-2">Current Password</label>
                <input 
                  type="password" 
                  className="w-full px-4 py-3 bg-zinc-950 border border-zinc-800 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none transition-all text-zinc-200"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-2">New Password</label>
                <input 
                  type="password" 
                  className="w-full px-4 py-3 bg-zinc-950 border border-zinc-800 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none transition-all text-zinc-200"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-2">Confirm New Password</label>
                <input 
                  type="password" 
                  className="w-full px-4 py-3 bg-zinc-950 border border-zinc-800 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none transition-all text-zinc-200"
                />
              </div>
              <div className="pt-4 flex justify-end">
                <button className="px-6 py-2.5 bg-white text-zinc-950 hover:bg-zinc-200 rounded-xl transition-colors font-medium">
                  Update Password
                </button>
              </div>
            </div>
          </div>

          {/* Two-Factor Authentication */}
          <div className="bg-zinc-900/30 border border-zinc-800 rounded-3xl p-6 sm:p-8 flex flex-col sm:flex-row gap-6 items-start sm:items-center justify-between">
            <div>
              <h2 className="text-lg font-medium mb-1 flex items-center gap-2">
                <Shield className="w-5 h-5 text-emerald-400" />
                Two-Factor Authentication
              </h2>
              <p className="text-sm text-zinc-400 max-w-md">Add an extra layer of security to your account by enabling two-factor authentication (2FA).</p>
            </div>
            <button className="px-5 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-xl transition-colors font-medium whitespace-nowrap">
              Enable 2FA
            </button>
          </div>
          
          {/* Danger Zone */}
          <div className="bg-red-500/5 border border-red-500/20 rounded-3xl p-6 sm:p-8">
            <h2 className="text-lg font-medium text-red-400 mb-2 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5" />
              Danger Zone
            </h2>
            <p className="text-sm text-zinc-400 mb-6">Permanently delete your account and all associated data. This action cannot be undone.</p>
            <button className="px-5 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 rounded-xl transition-colors font-medium">
              Delete Account
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
