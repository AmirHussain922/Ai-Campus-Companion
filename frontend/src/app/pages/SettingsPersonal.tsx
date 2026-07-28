import { Link } from "react-router";
import { motion } from "motion/react";
import { ChevronLeft, User as UserIcon, Save } from "lucide-react";
import { useStore } from "../store";

export default function SettingsPersonal() {
  const user = useStore(state => state.user);

  return (
    <div className="flex-1 overflow-y-auto bg-zinc-950 p-4 sm:p-6 md:p-8 text-zinc-50 relative h-full">
      <div className="max-w-2xl mx-auto space-y-8">
        
        <header className="flex items-center gap-4 border-b border-zinc-800/50 pb-6">
          <Link to="/app/me" className="p-2 bg-zinc-900 hover:bg-zinc-800 rounded-full transition-colors">
            <ChevronLeft className="w-5 h-5 text-zinc-400" />
          </Link>
          <div>
            <h1 className="text-2xl font-light tracking-tight">Personal Information</h1>
            <p className="text-sm text-zinc-400">Update your name and profile details</p>
          </div>
        </header>

        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-zinc-900/30 border border-zinc-800 rounded-3xl p-6 sm:p-8 space-y-6"
        >
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-zinc-400 mb-2">Display Name</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <UserIcon className="w-4 h-4 text-zinc-500" />
                </div>
                <input 
                  type="text" 
                  defaultValue={user?.name || ""}
                  className="w-full pl-11 pr-4 py-3 bg-zinc-950 border border-zinc-800 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none transition-all text-zinc-200"
                  placeholder="Your Name"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-400 mb-2">Email Address</label>
              <input 
                type="email" 
                defaultValue={user?.email || ""}
                disabled
                className="w-full px-4 py-3 bg-zinc-950/50 border border-zinc-800/50 rounded-xl text-zinc-500 cursor-not-allowed"
              />
              <p className="text-xs text-zinc-500 mt-2">Email addresses cannot be changed directly. Contact support for assistance.</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-zinc-400 mb-2">Bio / Description</label>
              <textarea 
                className="w-full px-4 py-3 bg-zinc-950 border border-zinc-800 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none transition-all text-zinc-200 min-h-[100px] resize-none"
                placeholder="Tell us a little about yourself..."
              ></textarea>
            </div>
          </div>

          <div className="pt-4 border-t border-zinc-800/50 flex justify-end">
            <button className="flex items-center gap-2 px-6 py-2.5 bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 border border-emerald-500/20 rounded-xl transition-colors font-medium">
              <Save className="w-4 h-4" />
              Save Changes
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
