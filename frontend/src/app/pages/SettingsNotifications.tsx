import { Link } from "react-router";
import { motion } from "motion/react";
import { ChevronLeft, Bell, Smartphone, Mail } from "lucide-react";
import { useState } from "react";
import { cn } from "../utils";

function Toggle({ checked, onChange }: { checked: boolean; onChange: () => void }) {
  return (
    <button 
      onClick={onChange}
      className={cn(
        "w-12 h-6 rounded-full transition-colors relative",
        checked ? "bg-emerald-500" : "bg-zinc-700"
      )}
    >
      <div 
        className={cn(
          "w-4 h-4 bg-white rounded-full absolute top-1 transition-transform",
          checked ? "translate-x-7" : "translate-x-1"
        )}
      />
    </button>
  );
}

export default function SettingsNotifications() {
  const [emailNotifs, setEmailNotifs] = useState({
    newMessages: true,
    levelUps: true,
    promotions: false
  });
  
  const [pushNotifs, setPushNotifs] = useState({
    newMessages: true,
    levelUps: true
  });

  return (
    <div className="flex-1 overflow-y-auto bg-zinc-950 p-4 sm:p-6 md:p-8 text-zinc-50 relative h-full">
      <div className="max-w-2xl mx-auto space-y-8">
        
        <header className="flex items-center gap-4 border-b border-zinc-800/50 pb-6">
          <Link to="/app/me" className="p-2 bg-zinc-900 hover:bg-zinc-800 rounded-full transition-colors">
            <ChevronLeft className="w-5 h-5 text-zinc-400" />
          </Link>
          <div>
            <h1 className="text-2xl font-light tracking-tight">Notifications</h1>
            <p className="text-sm text-zinc-400">Manage email and push notifications</p>
          </div>
        </header>

        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          {/* Email Notifications */}
          <div className="bg-zinc-900/30 border border-zinc-800 rounded-3xl p-6 sm:p-8">
            <h2 className="text-lg font-medium mb-6 flex items-center gap-2">
              <Mail className="w-5 h-5 text-zinc-400" />
              Email Notifications
            </h2>
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-zinc-200">New Messages</div>
                  <div className="text-xs text-zinc-500">Get notified when companions send you a message while you're away.</div>
                </div>
                <Toggle 
                  checked={emailNotifs.newMessages} 
                  onChange={() => setEmailNotifs(s => ({...s, newMessages: !s.newMessages}))} 
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-zinc-200">Level Up Summaries</div>
                  <div className="text-xs text-zinc-500">Receive an email summary of newly unlocked memories and episodes.</div>
                </div>
                <Toggle 
                  checked={emailNotifs.levelUps} 
                  onChange={() => setEmailNotifs(s => ({...s, levelUps: !s.levelUps}))} 
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-zinc-200">Promotions & Updates</div>
                  <div className="text-xs text-zinc-500">Occasional updates on new companions and app features.</div>
                </div>
                <Toggle 
                  checked={emailNotifs.promotions} 
                  onChange={() => setEmailNotifs(s => ({...s, promotions: !s.promotions}))} 
                />
              </div>
            </div>
          </div>

          {/* Push Notifications */}
          <div className="bg-zinc-900/30 border border-zinc-800 rounded-3xl p-6 sm:p-8">
            <h2 className="text-lg font-medium mb-6 flex items-center gap-2">
              <Smartphone className="w-5 h-5 text-zinc-400" />
              Push Notifications
            </h2>
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-zinc-200">New Messages</div>
                  <div className="text-xs text-zinc-500">Push notifications for direct messages from companions.</div>
                </div>
                <Toggle 
                  checked={pushNotifs.newMessages} 
                  onChange={() => setPushNotifs(s => ({...s, newMessages: !s.newMessages}))} 
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-zinc-200">Level Ups</div>
                  <div className="text-xs text-zinc-500">Instant notification when your relationship level increases.</div>
                </div>
                <Toggle 
                  checked={pushNotifs.levelUps} 
                  onChange={() => setPushNotifs(s => ({...s, levelUps: !s.levelUps}))} 
                />
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
