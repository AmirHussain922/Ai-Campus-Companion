import { useState, useRef, useEffect } from "react";
import { useParams, Link, useNavigate } from "react-router";
import { motion, AnimatePresence } from "motion/react";
import { ChevronLeft, ChevronRight, Lock, Unlock, MessageSquare, Plus, X, Camera, BookOpen, BookMarked } from "lucide-react";
import { useStore, StoryEpisode } from "../store";
import { useEpisodeStore } from "../useEpisodeStore";
import { useJournalStore } from "../useJournalStore";
import { companionColorClasses, cn, getPersonalizedEpisodeDetails } from "../utils";
import { episodeDetails } from "../storyData";
import EpisodeCard from "../components/EpisodeCard";
import JournalTimeline from "../components/JournalTimeline";

type Tab = 'chat' | 'stories' | 'journal';

export default function CompanionProfilePage() {
  const { companionId } = useParams<{ companionId: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<Tab>('chat');
  const allCompanions = useStore(state => state.companions);
  const myCompanions = useStore(state => state.myCompanions);
  const addCompanion = useStore(state => state.selectCompanion);
  const updateCompanionAvatar = useStore(state => state.updateCompanionAvatar);
  
  const { episodes, completedEpisodes, fetchEpisodes, fetchCompletedEpisodes } = useEpisodeStore();
  const { journals, fetchJournals } = useJournalStore();

  useEffect(() => {
    if (companionId) {
      fetchJournals(companionId);
    }
  }, [companionId, fetchJournals]);
  
  const [activeEpisode, setActiveEpisode] = useState<StoryEpisode | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Find in owned companions first for progress/level, fallback to base
  const ownedCompanion = myCompanions.find(c => c.id === companionId);
  const baseCompanion = allCompanions.find(c => c.id === companionId);
  const companion = ownedCompanion || baseCompanion;
  
  useEffect(() => {
    if (companionId) {
      fetchEpisodes(companionId);
      fetchCompletedEpisodes(companionId);
    }
  }, [companionId]);
  
  // Decide which list to use for navigation (owned if owned, all if not)
  const listToUse = ownedCompanion ? myCompanions : allCompanions;
  const currentIndex = listToUse.findIndex(c => c.id === companionId);
  
  const prevCompanion = currentIndex > 0 ? listToUse[currentIndex - 1] : listToUse[listToUse.length - 1];
  const nextCompanion = currentIndex < listToUse.length - 1 ? listToUse[currentIndex + 1] : listToUse[0];

  const userRelationshipStage = companion?.relationshipStage || 'Stranger';
  const stageToInt: Record<string, number> = {
    Stranger: 0,
    Curious: 1,
    Friend: 2,
    'Close Friend': 3,
    Confidant: 4
  };
  const userStageInt = stageToInt[userRelationshipStage] || 0;

  if (!companion) {
    return (
      <div className="flex-1 flex items-center justify-center bg-slate-900">
        <p>Companion not found.</p>
      </div>
    );
  }

  const colors = companionColorClasses[companion.color];
  const progress = (companion.xp / companion.nextLevelXp) * 100;

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !ownedCompanion) return;
    
    const reader = new FileReader();
    reader.onloadend = () => {
      const base64String = reader.result as string;
      updateCompanionAvatar(companion.id, base64String);
    };
    reader.readAsDataURL(file);
  };

  const completedIds = new Set(completedEpisodes.map(p => p.episode_id));
  const inProgressIds = new Set(completedEpisodes.filter(p => p.status === 'in_progress').map(p => p.episode_id));

  return (
    <div className="flex-1 flex flex-col bg-slate-900 text-slate-50 relative overflow-y-auto h-full">
      {/* Cinematic Hero */}
      <div className="relative h-[40vh] min-h-[300px] w-full shrink-0">
        <div className="absolute inset-0">
          <img src={companion.avatarUrl} alt="" className="w-full h-full object-cover opacity-40 blur-sm" />
          <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/80 to-transparent" />
        </div>
        
        {/* Top left navigation */}
        <div className="absolute top-6 left-4 sm:left-6 z-10 flex gap-2 sm:gap-4 items-center">
          <Link to="/app" className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors bg-slate-900/50 px-3 sm:px-4 py-2 rounded-full backdrop-blur-md border border-slate-800">
            <ChevronLeft className="w-4 h-4" />
            <span className="text-xs sm:text-sm font-medium hidden sm:inline">Dashboard</span>
          </Link>
          
          {listToUse.length > 1 && (
            <div className="flex items-center gap-1 bg-slate-900/50 rounded-full backdrop-blur-md border border-slate-800 px-1 py-1">
              <button onClick={() => navigate(`/app/companion/${prevCompanion.id}/profile`)} className="p-1.5 sm:p-2 hover:bg-slate-800 rounded-full transition-colors text-slate-400 hover:text-white">
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button onClick={() => navigate(`/app/companion/${nextCompanion.id}/profile`)} className="p-1.5 sm:p-2 hover:bg-slate-800 rounded-full transition-colors text-slate-400 hover:text-white">
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>

        <div className="absolute -bottom-16 left-6 sm:left-12 flex flex-col sm:flex-row items-start sm:items-end gap-4 sm:gap-8 z-10">
          <motion.div 
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            key={companion.id}
            className="relative group"
          >
            <div className={cn("absolute inset-0 rounded-full blur-xl opacity-50", colors.bg)} />
            <div className="relative w-28 h-28 sm:w-40 sm:h-40 rounded-full overflow-hidden border-4 border-slate-900 z-10 bg-slate-800">
              <img 
                src={companion.avatarUrl} 
                alt={companion.name} 
                className="w-full h-full object-cover" 
              />
              {ownedCompanion && (
                <div 
                  onClick={() => fileInputRef.current?.click()}
                  className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center cursor-pointer backdrop-blur-sm rounded-full"
                >
                  <Camera className="w-8 h-8 text-white mb-1" />
                  <span className="text-xs font-medium text-white">Change Photo</span>
                </div>
              )}
            </div>
            {ownedCompanion && (
              <input 
                type="file" 
                accept="image/*" 
                ref={fileInputRef}
                onChange={handleImageUpload}
                className="hidden" 
              />
            )}
          </motion.div>
          
          <motion.div 
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            key={`info-${companion.id}`}
            transition={{ delay: 0.1 }}
            className="pb-0 sm:pb-4 mt-2 sm:mt-0"
          >
            <h1 className="text-3xl sm:text-5xl font-light tracking-tighter mb-2">{companion.name}</h1>
            <div className="flex flex-wrap items-center gap-2 sm:gap-3">
              <span className={cn("px-2 py-1 sm:px-3 sm:py-1 rounded-md text-[10px] sm:text-xs font-semibold uppercase tracking-wider", colors.bgLight, colors.text)}>
                {companion.personality}
              </span>
              <span className="text-slate-400 text-xs sm:text-sm">Theme: {companion.theme}</span>
            </div>
          </motion.div>
        </div>
        
        <div className="absolute bottom-6 right-6 sm:right-12 z-10">
          {ownedCompanion ? (
            <Link 
              to={`/app/companion/${companion.id}/chat`}
              className="flex items-center gap-2 px-4 py-2 sm:px-6 sm:py-3 bg-white text-zinc-950 font-medium rounded-xl hover:bg-zinc-200 transition-colors shadow-lg text-sm sm:text-base"
            >
              <MessageSquare className="w-4 h-4 sm:w-5 sm:h-5" />
              <span className="hidden sm:inline">Continue Chat</span>
              <span className="sm:hidden">Chat</span>
            </Link>
          ) : (
            <button 
              onClick={() => {
                addCompanion(companion.id);
                navigate(`/app/companion/${companion.id}/chat`);
              }}
              className="flex items-center gap-2 px-4 py-2 sm:px-6 sm:py-3 bg-white text-slate-950 font-medium rounded-xl hover:bg-slate-200 transition-colors shadow-lg text-sm sm:text-base"
            >
              <Plus className="w-4 h-4 sm:w-5 sm:h-5" />
              <span className="hidden sm:inline">Add Companion</span>
              <span className="sm:hidden">Add</span>
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto px-6 sm:px-12">
          <div className="flex gap-1 -mb-px">
            <button
              onClick={() => setActiveTab('chat')}
              className={cn(
                "flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 transition-colors",
                activeTab === 'chat'
                  ? "border-indigo-500 text-indigo-400"
                  : "border-transparent text-slate-500 hover:text-slate-300 hover:border-slate-700"
              )}
            >
              <MessageSquare className="w-4 h-4" />
              Chat
            </button>
            <button
              onClick={() => setActiveTab('stories')}
              className={cn(
                "flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 transition-colors",
                activeTab === 'stories'
                  ? "border-indigo-500 text-indigo-400"
                  : "border-transparent text-slate-500 hover:text-slate-300 hover:border-slate-700"
              )}
            >
              <BookOpen className="w-4 h-4" />
              Stories
            </button>
            <button
              onClick={() => setActiveTab('journal')}
              className={cn(
                "relative flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 transition-colors",
                activeTab === 'journal'
                  ? "border-indigo-500 text-indigo-400"
                  : "border-transparent text-slate-500 hover:text-slate-300 hover:border-slate-700"
              )}
            >
              <BookMarked className="w-4 h-4" />
              Journal
              {journals.some(j => j.is_unlocked && !j.is_read) && (
                <span className="absolute top-3 right-3 w-2 h-2 bg-indigo-500 rounded-full shadow-[0_0_8px_rgba(99,102,241,0.7)]" />
              )}
            </button>
          </div>
        </div>
      </div>

      <div className="pt-8 px-6 sm:px-12 pb-12 max-w-6xl w-full mx-auto">
        <AnimatePresence mode="wait">
          {activeTab === 'chat' && (
            <motion.div
              key="chat"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 sm:gap-12">
                {/* Left Column: Stats & Traits */}
                <div className="space-y-8">
                  <section className="bg-slate-800/30 border border-slate-700 rounded-3xl p-6">
                    <h3 className="text-lg font-medium mb-2">About</h3>
                    <p className="text-slate-400 text-sm leading-relaxed mb-6">{companion.description}</p>
                    
                    <div className="space-y-4">
                      <div>
                        <h4 className="text-xs text-slate-500 uppercase tracking-wider mb-2">Traits</h4>
                        <div className="flex flex-wrap gap-2">
                          {companion.traits.map(trait => (
                            <span key={trait} className="px-3 py-1.5 bg-slate-700/80 rounded-lg text-sm text-slate-300 border border-slate-600/50">
                              {trait}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </section>

                  <section className="bg-slate-800/50 border border-slate-700 rounded-3xl p-6 relative overflow-hidden">
                    <div className={cn("absolute -top-10 -right-10 w-32 h-32 rounded-full blur-3xl opacity-20", colors.bg)} />
                    
                    <div className="flex justify-between items-end mb-6">
                      <div>
                        <h3 className="text-sm font-medium text-slate-400 uppercase tracking-wider">Relationship Level</h3>
                        <div className="text-4xl font-light mt-1 text-white">{companion.level}</div>
                      </div>
                      <div className={cn("text-sm font-medium", colors.text)}>
                        {companion.xp} / {companion.nextLevelXp} XP
                      </div>
                    </div>

                    <div className="h-2 w-full bg-slate-900 rounded-full overflow-hidden mb-2">
                      <motion.div 
                        initial={{ width: 0 }}
                        animate={{ width: `${progress}%` }}
                        transition={{ duration: 1, delay: 0.2 }}
                        className={cn("h-full rounded-full", colors.bg, colors.glowStrong)}
                      />
                    </div>
                    <p className="text-xs text-slate-500 text-center mt-4">
                      Chat to gain XP and unlock new story episodes.
                    </p>
                  </section>
                </div>

                {/* Right Column: Story Timeline */}
                <div className="lg:col-span-2">
                  <section>
                    <h2 className="text-2xl font-light tracking-tight mb-8">Story Timeline</h2>
                    
                    <div className="relative border-l border-slate-700 ml-4 space-y-12 pb-12">
                      {companion.episodes.map((episode, idx) => {
                        const isUnlocked = companion.level >= episode.unlockLevel;
                        
                        return (
                          <motion.div 
                            key={episode.id}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: idx * 0.15 }}
                            className={cn(
                              "relative pl-8 transition-opacity duration-500",
                              isUnlocked ? "opacity-100" : "opacity-40"
                            )}
                          >
                            {/* Timeline Node */}
                            <div className={cn(
                              "absolute -left-3 top-1 w-6 h-6 rounded-full border-4 border-slate-900 flex items-center justify-center",
                              isUnlocked ? colors.bg : "bg-slate-700"
                            )}>
                              {isUnlocked ? (
                                <Unlock className="w-2.5 h-2.5 text-slate-900" />
                              ) : (
                                <Lock className="w-2.5 h-2.5 text-slate-500" />
                              )}
                            </div>
                            
                            <div className={cn(
                              "p-6 rounded-2xl border transition-all",
                              isUnlocked 
                                ? cn("bg-slate-800/50 border-slate-700 hover:border-slate-600") 
                                : "bg-slate-900 border-slate-700/50 border-dashed"
                            )}>
                              <div className="flex justify-between items-start mb-2">
                                <h4 className="text-lg font-medium">{episode.title}</h4>
                                <span className="text-xs font-semibold px-2 py-1 rounded-md bg-slate-700 text-slate-400">
                                  Unlocks at Level {episode.unlockLevel}
                                </span>
                              </div>
                              <p className="text-slate-400 text-sm">{episode.description}</p>
                              
                              {isUnlocked && ownedCompanion && (
                                <button 
                                  onClick={() => setActiveEpisode(episode)}
                                  className="mt-4 text-sm font-medium hover:underline flex items-center gap-1"
                                >
                                  Replay Memory <ChevronLeft className="w-3 h-3 rotate-180" />
                                </button>
                              )}
                            </div>
                          </motion.div>
                        );
                      })}
                    </div>
                  </section>
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'stories' && (
            <motion.div
              key="stories"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h2 className="text-2xl font-light tracking-tight">Stories</h2>
                  <p className="text-slate-400 text-sm mt-1">Choose a story to start your adventure</p>
                </div>
                <Link
                  to={`/app/companion/${companionId}/episodes`}
                  className="text-sm font-medium text-indigo-400 hover:text-indigo-300 transition-colors"
                >
                  View All
                </Link>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {episodes.slice(0, 3).map((episode) => (
                  <EpisodeCard
                    key={episode._id}
                    episode={episode}
                    progress={completedEpisodes.find(p => p.episode_id === episode._id)}
                    companionId={companionId!}
                    isLocked={episode.required_relationship_stage > userStageInt}
                  />
                ))}
              </div>
            </motion.div>
          )}

          {activeTab === 'journal' && (
            <motion.div
              key="journal"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <JournalTimeline companionId={companionId!} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Memory Details Modal */}
      <AnimatePresence>
        {activeEpisode && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-900/80 backdrop-blur-sm"
          >
            <motion.div
              initial={{ scale: 0.95, y: 20, opacity: 0 }}
              animate={{ scale: 1, y: 0, opacity: 1 }}
              exit={{ scale: 0.95, y: 20, opacity: 0 }}
              className="bg-slate-800 border border-slate-700 rounded-3xl w-full max-w-2xl overflow-hidden shadow-2xl relative"
            >
              <button 
                onClick={() => setActiveEpisode(null)}
                className="absolute top-4 right-4 p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-full transition-colors z-10"
              >
                <X className="w-5 h-5" />
              </button>

              <div className="p-8 sm:p-10">
                <div className="flex items-center gap-3 mb-6">
                  <div className={cn("w-10 h-10 rounded-full flex items-center justify-center", colors.bgLight)}>
                    <Unlock className={cn("w-5 h-5", colors.text)} />
                  </div>
                  <div>
                    <div className="text-xs font-semibold tracking-wider text-slate-500 uppercase">Memory Unlocked</div>
                    <h2 className="text-2xl font-light text-white">{activeEpisode.title}</h2>
                  </div>
                </div>

                {activeEpisode && episodeDetails[activeEpisode.id] ? (
                  (() => {
                    const baseName = allCompanions.find(c => c.id === companion.id)?.name || companion.name;
                    const details = getPersonalizedEpisodeDetails(activeEpisode.id, baseName, companion.name);
                    return (
                      <div className="space-y-6">
                        <div>
                          <h3 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-2">Scenario</h3>
                          <p className="text-slate-200 leading-relaxed bg-slate-900/50 p-4 rounded-xl border border-slate-700/50">
                            {details?.scenario}
                          </p>
                        </div>
                        
                        <div>
                          <h3 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-2">Backstory</h3>
                          <p className="text-slate-200 leading-relaxed bg-slate-900/50 p-4 rounded-xl border border-slate-700/50">
                            {details?.backstory}
                          </p>
                        </div>

                        <div>
                          <h3 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-2">Scene Narration</h3>
                          <p className="text-slate-200 leading-relaxed bg-slate-900/50 p-4 rounded-xl border border-slate-700/50 italic border-l-2 border-l-emerald-500">
                            "{details?.narration}"
                          </p>
                        </div>
                      </div>
                    );
                  })()
                ) : (
                  <p className="text-slate-400 text-center py-8 italic">Memory details are currently hazy...</p>
                )}

                <div className="mt-8 flex justify-end">
                  <button 
                    onClick={() => setActiveEpisode(null)}
                    className="px-6 py-2 bg-white text-slate-900 font-medium rounded-xl hover:bg-slate-200 transition-colors"
                  >
                    Close Memory
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
