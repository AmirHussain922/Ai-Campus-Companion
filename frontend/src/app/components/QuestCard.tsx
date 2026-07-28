import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, Circle, Clock, Trophy, MessageSquare, Send, Loader2 } from 'lucide-react';
import { cn } from '../utils';
import type { Quest } from '../stores/useQuestStore';

interface QuestCardProps {
  quest: Quest;
  onComplete: (questId: string, reportText: string) => Promise<boolean>;
  isCompleting?: boolean;
}

const companionColors: Record<string, { bg: string; border: string; text: string; glow: string }> = {
  emerald: {
    bg: 'bg-emerald-500/10',
    border: 'border-emerald-500/30',
    text: 'text-emerald-400',
    glow: 'shadow-emerald-500/20'
  },
  pink: {
    bg: 'bg-pink-500/10',
    border: 'border-pink-500/30',
    text: 'text-pink-400',
    glow: 'shadow-pink-500/20'
  },
  rose: {
    bg: 'bg-rose-500/10',
    border: 'border-rose-500/30',
    text: 'text-rose-400',
    glow: 'shadow-rose-500/20'
  },
  violet: {
    bg: 'bg-violet-500/10',
    border: 'border-violet-500/30',
    text: 'text-violet-400',
    glow: 'shadow-violet-500/20'
  },
  amber: {
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/30',
    text: 'text-amber-400',
    glow: 'shadow-amber-500/20'
  }
};

// Map companion_giver to color
const companionGiverToColor: Record<string, string> = {
  study_buddy: 'emerald',
  party_friend: 'pink',
  philosopher: 'violet',
  rival: 'rose',
  freshman: 'amber'
};

const questTypeIcons: Record<string, React.ReactNode> = {
  study: <Clock className="w-4 h-4" />,
  social: <MessageSquare className="w-4 h-4" />,
  wellness: <Trophy className="w-4 h-4" />,
  rivalry: <Trophy className="w-4 h-4" />
};

// Safe fallback icon for unknown quest types
const defaultQuestTypeIcon: React.ReactNode = <Clock className="w-4 h-4" />;

export function QuestCard({ quest, onComplete, isCompleting = false }: QuestCardProps) {
  const [reportText, setReportText] = useState('');
  const [showReportForm, setShowReportForm] = useState(false);
  const [justCompleted, setJustCompleted] = useState(false);

  const companionColor = companionGiverToColor[quest.companion_giver] || 'emerald';
  const colors = companionColors[companionColor];
  const isCompleted = quest.status === 'completed' || justCompleted;
  const isFailed = quest.status === 'failed';
  const isManual = quest.verification_method === 'manual';
  const isAuto = quest.verification_method === 'auto';
  const isOpenRouter = quest.verification_method === 'openrouter';

  const handleSubmit = async () => {
    if (!reportText.trim() || isCompleted) return;

    const success = await onComplete(quest.id, reportText);
    if (success) {
      setJustCompleted(true);
      setShowReportForm(false);
      setReportText('');
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "relative rounded-xl border p-5 transition-all duration-300",
        "bg-slate-800 border-slate-700",
        colors.glow,
        isCompleted && "border-emerald-500/30 bg-emerald-500/5",
        isFailed && "border-rose-500/30 bg-rose-500/5"
      )}
    >
      {/* Status Badge */}
      <div className="absolute top-4 right-4">
        {isCompleted ? (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="flex items-center gap-1.5 text-emerald-400"
          >
            <CheckCircle2 className="w-5 h-5" />
            <span className="text-xs font-medium">Completed</span>
          </motion.div>
        ) : isFailed ? (
          <div className="flex items-center gap-1.5 text-rose-400">
            <Circle className="w-5 h-5" />
            <span className="text-xs font-medium">Failed</span>
          </div>
        ) : (
          <div className="flex items-center gap-1.5 text-slate-400">
            <Circle className="w-5 h-5" />
            <span className="text-xs font-medium">Active</span>
          </div>
        )}
      </div>

      {/* Header: Type Icon + Companion */}
      <div className="flex items-center gap-3 mb-3">
        <div className={cn(
          "p-2 rounded-lg",
          colors.bg,
          colors.text
        )}>
          {questTypeIcons[quest.quest_type] || defaultQuestTypeIcon}
        </div>

        {quest.companion_avatar && (
          <div className="flex items-center gap-2">
            <img
              src={quest.companion_avatar}
              alt={quest.companion_name}
              className="w-6 h-6 rounded-full object-cover ring-2 ring-slate-700"
            />
            <span className={cn("text-sm font-medium", colors.text)}>
              {quest.companion_name}
            </span>
          </div>
        )}
      </div>

      {/* Title & Description */}
      <h3 className="text-lg font-semibold text-white mb-1">
        {quest.title}
      </h3>
      <p className="text-slate-400 text-sm mb-4">
        {quest.description}
      </p>

      {/* XP Reward Badge + Progress */}
      <div className="flex flex-col gap-3 mb-4">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/30">
            <Trophy className="w-3.5 h-3.5 text-amber-400" />
            <span className="text-sm font-medium text-amber-400">+{quest.xp_reward} XP</span>
          </div>
          {isAuto && quest.target_count && (
            <span className="text-xs text-slate-400">
              {quest.progress_count || 0} / {quest.target_count}
            </span>
          )}
        </div>

        {isAuto && quest.target_count && (
          <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-emerald-500 transition-all duration-300"
              style={{ width: `${Math.min(100, ((quest.progress_count || 0) / quest.target_count) * 100)}%` }}
            />
          </div>
        )}
      </div>

      {/* Completion Report Form */}
      <AnimatePresence>
        {!isCompleted && !isFailed && (isManual || isOpenRouter) && !showReportForm && (
          <motion.button
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowReportForm(true)}
            className={cn(
              "w-full py-2.5 px-4 rounded-lg font-medium transition-all duration-200",
              "bg-slate-700 hover:bg-slate-600 text-white",
              "flex items-center justify-center gap-2"
            )}
          >
            <CheckCircle2 className="w-4 h-4" />
            {isOpenRouter ? 'Submit for Verification' : 'Mark as Complete'}
          </motion.button>
        )}

        {showReportForm && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-3"
          >
            <div className="relative">
              <MessageSquare className="absolute left-3 top-3 w-4 h-4 text-slate-500" />
              <textarea
                value={reportText}
                onChange={(e) => setReportText(e.target.value)}
                placeholder={
                  isOpenRouter
                    ? "Explain how you completed this quest. Be detailed so your companion can verify your work..."
                    : "How did it go? Share your experience..."
                }
                className="w-full pl-10 pr-4 py-2.5 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500/50 min-h-[80px]"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  setShowReportForm(false);
                  setReportText('');
                }}
                className="flex-1 py-2.5 px-4 rounded-lg font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                disabled={!reportText.trim() || isCompleting}
                className={cn(
                  "flex-1 py-2.5 px-4 rounded-lg font-medium transition-all duration-200 flex items-center justify-center gap-2",
                  reportText.trim() && !isCompleting
                    ? "bg-emerald-600 hover:bg-emerald-500 text-white"
                    : "bg-slate-700 text-slate-500 cursor-not-allowed"
                )}
              >
                {isCompleting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    Submit
                  </>
                )}
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export default QuestCard;
