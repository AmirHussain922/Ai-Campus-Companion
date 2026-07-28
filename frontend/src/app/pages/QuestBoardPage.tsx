import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ScrollText, Target, Trophy, Calendar, Sparkles, CheckCircle2, Clock, Circle } from 'lucide-react';
import { useStore } from '../store';
import { useQuestStore } from '../stores/useQuestStore';
import { QuestCard } from '../components/QuestCard';
import { cn } from '../utils';

export default function QuestBoardPage() {
  const authToken = useStore(state => state.authToken);
  const { 
    activeQuests, 
    questHistory, 
    isLoading, 
    fetchActiveQuests, 
    completeQuest,
    fetchHistory,
    getDailyProgress
  } = useQuestStore();
  
  const [activeTab, setActiveTab] = useState<'active' | 'history'>('active');
  const [completingQuestId, setCompletingQuestId] = useState<string | null>(null);
  const [showToast, setShowToast] = useState<{ xp: number; companionName: string } | null>(null);

  const dailyProgress = getDailyProgress();
  const today = new Date();
  const formattedDate = today.toLocaleDateString('en-US', { 
    weekday: 'long', 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric' 
  });

  useEffect(() => {
    fetchActiveQuests(authToken);
  }, [authToken, fetchActiveQuests]);

  useEffect(() => {
    if (activeTab === 'history') {
      fetchHistory(7, authToken);
    }
  }, [activeTab, authToken, fetchHistory]);

  const handleCompleteQuest = async (questId: string, reportText: string): Promise<boolean> => {
    setCompletingQuestId(questId);
    
    const success = await completeQuest(questId, reportText, authToken);
    
    if (success) {
      // Find the quest to get XP and companion name for toast
      const quest = activeQuests.find(q => q.id === questId);
      if (quest) {
        setShowToast({ 
          xp: quest.xp_reward, 
          companionName: quest.companion_name || 'Your companion' 
        });
        setTimeout(() => setShowToast(null), 4000);
      }
    }
    
    setCompletingQuestId(null);
    return success;
  };

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <div className="sticky top-0 z-20 bg-slate-950/80 backdrop-blur-xl border-b border-slate-800">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white flex items-center gap-3">
                <ScrollText className="w-7 h-7 text-indigo-400" />
                Today's Quests
              </h1>
              <p className="text-slate-400 text-sm mt-1 flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                {formattedDate}
              </p>
            </div>
            
            {/* Daily Progress */}
            <div className="hidden sm:flex items-center gap-4 bg-slate-900/50 rounded-xl px-4 py-3 border border-slate-800">
              <div className="text-center">
                <p className="text-2xl font-bold text-white">{dailyProgress.completed}</p>
                <p className="text-xs text-slate-500">Completed</p>
              </div>
              <div className="w-px h-10 bg-slate-700" />
              <div className="text-center">
                <p className="text-2xl font-bold text-amber-400">{dailyProgress.xp}</p>
                <p className="text-xs text-slate-500">XP Earned</p>
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 mt-4">
            <button
              onClick={() => setActiveTab('active')}
              className={cn(
                "px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center gap-2",
                activeTab === 'active'
                  ? "bg-indigo-600 text-white"
                  : "text-slate-400 hover:text-white hover:bg-slate-800"
              )}
            >
              <Target className="w-4 h-4" />
              Active Quests
              {activeQuests.length > 0 && (
                <span className="ml-1 px-1.5 py-0.5 bg-white/20 rounded text-xs">
                  {activeQuests.length}
                </span>
              )}
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={cn(
                "px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center gap-2",
                activeTab === 'history'
                  ? "bg-indigo-600 text-white"
                  : "text-slate-400 hover:text-white hover:bg-slate-800"
              )}
            >
              <Trophy className="w-4 h-4" />
              History
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6">
        <AnimatePresence mode="wait">
          {activeTab === 'active' ? (
            <motion.div
              key="active"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-6"
            >
              {isLoading ? (
                <div className="text-center py-12">
                  <div className="animate-spin w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full mx-auto mb-4" />
                  <p className="text-slate-500">Loading quests...</p>
                </div>
              ) : activeQuests.length === 0 ? (
                <div className="text-center py-16 bg-slate-900/50 rounded-2xl border border-slate-800">
                  <CheckCircle2 className="w-16 h-16 text-emerald-500 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-white mb-2">All Caught Up!</h3>
                  <p className="text-slate-400 max-w-md mx-auto">
                    You&apos;ve completed all your quests for today. Check back tomorrow for new challenges!
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {activeQuests.map((quest, index) => (
                    <motion.div
                      key={quest.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                    >
                      <QuestCard
                        quest={quest}
                        onComplete={handleCompleteQuest}
                        isCompleting={completingQuestId === quest.id}
                      />
                    </motion.div>
                  ))}
                </div>
              )}
            </motion.div>
          ) : (
            <motion.div
              key="history"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-4"
            >
              {questHistory.length === 0 ? (
                <div className="text-center py-16 bg-slate-900/50 rounded-2xl border border-slate-800">
                  <Clock className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-white mb-2">No History Yet</h3>
                  <p className="text-slate-400 max-w-md mx-auto">
                    Your completed quests will appear here. Start working on today&apos;s quests!
                  </p>
                </div>
              ) : (
                questHistory.map((entry, index) => (
                  <motion.div
                    key={entry.date}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="bg-slate-800/50 border border-slate-700 rounded-xl p-4"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <h4 className="text-white font-medium">
                          {new Date(entry.date).toLocaleDateString('en-US', { 
                            weekday: 'long', 
                            month: 'short', 
                            day: 'numeric' 
                          })}
                        </h4>
                      </div>
                      <div className="flex items-center gap-4 text-sm">
                        <span className="text-emerald-400 font-medium">
                          {entry.completed_count} completed
                        </span>
                        <span className="text-amber-400 font-medium">
                          {entry.total_xp} XP
                        </span>
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      {entry.quests.map(quest => (
                        <div 
                          key={quest.id}
                          className="flex items-center gap-3 p-2 bg-slate-900/50 rounded-lg"
                        >
                          <div className={cn(
                            "w-8 h-8 rounded-full flex items-center justify-center",
                            quest.status === 'completed' ? "bg-emerald-500/20" : "bg-rose-500/20"
                          )}>
                            {quest.status === 'completed' ? (
                              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                            ) : (
                              <Circle className="w-4 h-4 text-rose-400" />
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-white truncate">{quest.title}</p>
                            <p className="text-xs text-slate-500">+{quest.xp_reward} XP</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                ))
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Completion Toast */}
      <AnimatePresence>
        {showToast && (
          <motion.div
            initial={{ opacity: 0, y: 50, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.9 }}
            className="fixed bottom-8 left-1/2 -translate-x-1/2 z-50"
          >
            <div className="bg-slate-800 border border-emerald-500/30 rounded-xl px-6 py-4 shadow-2xl shadow-emerald-500/10 flex items-center gap-3">
              <div className="p-2 bg-emerald-500/20 rounded-full">
                <Sparkles className="w-5 h-5 text-emerald-400" />
              </div>
              <div>
                <p className="text-white font-medium">
                  +{showToast.xp} XP earned!
                </p>
                <p className="text-sm text-slate-400">
                  {showToast.companionName} is impressed.
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
