import { useState, useEffect } from "react";
import { useParams } from "react-router";
import { motion } from "motion/react";
import { Lock, CheckCircle2, Clock } from "lucide-react";
import { useJournalStore } from "../useJournalStore";
import { useStore } from "../store";
import { cn } from "../utils";

const STAGES = [
  { name: "Stranger", color: "slate" },
  { name: "Curious", color: "blue" },
  { name: "Friend", color: "emerald" },
  { name: "Close Friend", color: "amber" },
  { name: "Confidant", color: "rose" },
];

const BORDER_COLORS: Record<string, string> = {
  slate: "border-l-slate-500",
  blue: "border-l-blue-500",
  emerald: "border-l-emerald-500",
  amber: "border-l-amber-500",
  rose: "border-l-rose-500",
};

const BADGE_COLORS: Record<string, string> = {
  slate: "bg-slate-500/20 text-slate-400 border-slate-600",
  blue: "bg-blue-500/20 text-blue-400 border-blue-600",
  emerald: "bg-emerald-500/20 text-emerald-400 border-emerald-600",
  amber: "bg-amber-500/20 text-amber-400 border-amber-600",
  rose: "bg-rose-500/20 text-rose-400 border-rose-600",
};

interface JournalTimelineProps {
  companionId: string;
}

export default function JournalTimeline({ companionId }: JournalTimelineProps) {
  const { journals, isLoading, fetchJournals, markAsRead } = useJournalStore();
  const allCompanions = useStore(state => state.companions);
  const myCompanions = useStore(state => state.myCompanions);
  const [expandedStage, setExpandedStage] = useState<number | null>(null);

  const companion = myCompanions.find(c => c.id === companionId) || allCompanions.find(c => c.id === companionId);
  const userStage = companion?.relationshipStage || "Stranger";
  const userStageIndex = STAGES.findIndex(s => s.name === userStage);

  useEffect(() => {
    if (companionId) {
      fetchJournals(companionId);
    }
  }, [companionId, fetchJournals]);

  const handleToggleStage = async (stage: number, journal?: { is_unlocked: boolean; is_read: boolean }) => {
    if (!journal?.is_unlocked) return;
    if (expandedStage === stage) {
      setExpandedStage(null);
      return;
    }
    setExpandedStage(stage);
    if (journal && !journal.is_read) {
      await markAsRead(companionId, stage);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-2xl font-light tracking-tight text-white">
            {companion?.name}'s Journal
          </h2>
          <p className="text-slate-400 text-sm mt-1">
            Their thoughts about your relationship
          </p>
        </div>
        {isLoading && <div className="text-sm text-slate-400">Loading entries...</div>}
      </div>

      <div className="space-y-6">
        {STAGES.map((stage, index) => {
          const journal = journals.find(j => j.stage === index);
          const isUnlocked = index <= userStageIndex;
          const isRead = journal?.is_read ?? false;
          const isExpanded = expandedStage === index;

          return (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <div
                onClick={() => handleToggleStage(index, journal)}
                className={cn(
                  "relative pl-8 pr-6 py-6 rounded-2xl border transition-all cursor-pointer group",
                  isUnlocked
                    ? cn(
                        "bg-slate-800/50 border-slate-700 hover:border-slate-600",
                        BORDER_COLORS[stage.color]
                      )
                    : "bg-slate-900/50 border-slate-800 border-dashed opacity-60"
                )}
              >
                {/* Timeline dot */}
                <div
                  className={cn(
                    "absolute left-0 top-8 w-3 h-3 rounded-full border-4 border-slate-900 z-10",
                    isUnlocked
                      ? BADGE_COLORS[stage.color].split(" ")[0]
                      : "bg-slate-700"
                  )}
                />

                <div className="flex justify-between items-start gap-4">
                  <div>
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-medium text-white">{stage.name}</h3>
                      {isUnlocked && (
                        <div className="flex items-center gap-2">
                          {!isRead && (
                            <span className="flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-indigo-500/20 text-indigo-400 border border-indigo-500/50 shadow-[0_0_10px_rgba(99,102,241,0.3)]">
                              New
                            </span>
                          )}
                          {isRead && (
                            <span className="flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium text-slate-500">
                              <CheckCircle2 className="w-3 h-3" />
                              Read
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                    {isUnlocked && journal?.generated_at && (
                      <p className="text-xs text-slate-500 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(journal.generated_at).toLocaleDateString(undefined, {
                          year: "numeric",
                          month: "long",
                          day: "numeric",
                        })}
                      </p>
                    )}
                  </div>
                  {!isUnlocked && (
                    <div className="flex items-center gap-2 text-slate-500 text-sm">
                      <Lock className="w-4 h-4" />
                      Reach {stage.name} to unlock
                    </div>
                  )}
                </div>

                {isUnlocked && isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    className="mt-4"
                  >
                    <p className="text-slate-300 leading-relaxed font-serif italic">
                      "{journal?.entry_text}"
                    </p>
                  </motion.div>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
