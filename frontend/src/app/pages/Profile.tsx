import { useState, useRef } from "react";
import { useParams, Link, useNavigate } from "react-router";
import { motion, AnimatePresence } from "motion/react";
import { ChevronLeft, ChevronRight, Lock, Unlock, MessageSquare, Plus, X, Camera } from "lucide-react";
import { useStore, StoryEpisode } from "../store";
import { companionColorClasses, cn, getPersonalizedEpisodeDetails } from "../utils";
import { episodeDetails } from "../storyData";

export default function Profile() {
  const { id } = useParams();
  const navigate = useNavigate();
  const allCompanions = useStore(state => state.companions);
  const myCompanions = useStore(state => state.myCompanions);
  const addCompanion = useStore(state => state.selectCompanion);
  const updateCompanionAvatar = useStore(state => state.updateCompanionAvatar);
  
  const [activeEpisode, setActiveEpisode] = useState<StoryEpisode | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Find in owned companions first for progress/level, fallback to base
  const ownedCompanion = myCompanions.find(c => c.id === id);
  const baseCompanion = allCompanions.find(c => c.id === id);
  const companion = ownedCompanion || baseCompanion;
  
  // Decide which list to use for navigation (owned if owned, all if not)
  const listToUse = ownedCompanion ? myCompanions : allCompanions;
  const currentIndex = listToUse.findIndex(c => c.id === id);
  
  const prevCompanion = currentIndex > 0 ? listToUse[currentIndex - 1] : listToUse[listToUse.length - 1];
  const nextCompanion = currentIndex < listToUse.length - 1 ? listToUse[currentIndex + 1] : listToUse[0];

  if (!companion) {
    return (
      <div className="flex-1 flex items-center justify-center bg-zinc-950">
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

  return (
    <div className="flex-1 flex flex-col bg-zinc-950 text-zinc-50 relative overflow-y-auto h-full">
      {/* Cinematic Hero */}
      <div className="relative h-[40vh] min-h-[300px] w-full shrink-0">
        <div className="absolute inset-0">
          <img src={companion.avatarUrl} alt="" className="w-full h-full object-cover opacity-40 blur-sm" />
          <div className="absolute inset-0 bg-gradient-to-t from-zinc-950 via-zinc-950/80 to-transparent" />
        </div>
        
        {/* Top left navigation */}
        <div className="absolute top-6 left-4 sm:left-6 z-10 flex gap-2 sm:gap-4 items-center">
          <Link to="/app" className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors bg-zinc-950/50 px-3 sm:px-4 py-2 rounded-full backdrop-blur-md border border-zinc-800">
            <ChevronLeft className="w-4 h-4" />
            <span className="text-xs sm:text-sm font-medium hidden sm:inline">Dashboard</span>
          </Link>
          
          {listToUse.length > 1 && (
            <div className="flex items-center gap-1 bg-zinc-950/50 rounded-full backdrop-blur-md border border-zinc-800 px-1 py-1">
              <button onClick={() => navigate(`/app/profile/${prevCompanion.id}`)} className="p-1.5 sm:p-2 hover:bg-zinc-800 rounded-full transition-colors text-zinc-400 hover:text-white">
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button onClick={() => navigate(`/app/profile/${nextCompanion.id}`)} className="p-1.5 sm:p-2 hover:bg-zinc-800 rounded-full transition-colors text-zinc-400 hover:text-white">
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
            <div className="relative w-28 h-28 sm:w-40 sm:h-40 rounded-full overflow-hidden border-4 border-zinc-950 z-10 bg-zinc-900">
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
              <span className="text-zinc-400 text-xs sm:text-sm">Theme: {companion.theme}</span>
            </div>
          </motion.div>
        </div>
        
        <div className="absolute bottom-6 right-6 sm:right-12 z-10">
          {ownedCompanion ? (
            <Link 
              to={`/app/chat/${companion.id}`}
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
                navigate(`/app/chat/${companion.id}`);
              }}
              className="flex items-center gap-2 px-4 py-2 sm:px-6 sm:py-3 bg-white text-zinc-950 font-medium rounded-xl hover:bg-zinc-200 transition-colors shadow-lg text-sm sm:text-base"
            >
              <Plus className="w-4 h-4 sm:w-5 sm:h-5" />
              <span className="hidden sm:inline">Add Companion</span>
              <span className="sm:hidden">Add</span>
            </button>
          )}
        </div>
      </div>

      <div className="pt-24 sm:pt-24 px-6 sm:px-12 pb-12 max-w-6xl w-full mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8 sm:gap-12 z-10 relative">
        {/* Left Column: Stats & Traits */}
        <div className="space-y-8">
          <section className="bg-zinc-900/30 border border-zinc-800 rounded-3xl p-6">
            <h3 className="text-lg font-medium mb-2">About</h3>
            <p className="text-zinc-400 text-sm leading-relaxed mb-6">{companion.description}</p>
            
            <div className="space-y-4">
              <div>
                <h4 className="text-xs text-zinc-500 uppercase tracking-wider mb-2">Traits</h4>
                <div className="flex flex-wrap gap-2">
                  {companion.traits.map(trait => (
                    <span key={trait} className="px-3 py-1.5 bg-zinc-800/80 rounded-lg text-sm text-zinc-300 border border-zinc-700/50">
                      {trait}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </section>

          <section className="bg-zinc-900/50 border border-zinc-800 rounded-3xl p-6 relative overflow-hidden">
            <div className={cn("absolute -top-10 -right-10 w-32 h-32 rounded-full blur-3xl opacity-20", colors.bg)} />
            
            <div className="flex justify-between items-end mb-6">
              <div>
                <h3 className="text-sm font-medium text-zinc-400 uppercase tracking-wider">Relationship Level</h3>
                <div className="text-4xl font-light mt-1 text-white">{companion.level}</div>
              </div>
              <div className={cn("text-sm font-medium", colors.text)}>
                {companion.xp} / {companion.nextLevelXp} XP
              </div>
            </div>

            <div className="h-2 w-full bg-zinc-950 rounded-full overflow-hidden mb-2">
              <motion.div 
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 1, delay: 0.2 }}
                className={cn("h-full rounded-full", colors.bg, colors.glowStrong)}
              />
            </div>
            <p className="text-xs text-zinc-500 text-center mt-4">
              Chat to gain XP and unlock new story episodes.
            </p>
          </section>
        </div>

        {/* Right Column: Story Timeline */}
        <div className="lg:col-span-2">
          <section>
            <h2 className="text-2xl font-light tracking-tight mb-8">Story Timeline</h2>
            
            <div className="relative border-l border-zinc-800 ml-4 space-y-12 pb-12">
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
                      "absolute -left-3 top-1 w-6 h-6 rounded-full border-4 border-zinc-950 flex items-center justify-center",
                      isUnlocked ? colors.bg : "bg-zinc-800"
                    )}>
                      {isUnlocked ? (
                        <Unlock className="w-2.5 h-2.5 text-zinc-950" />
                      ) : (
                        <Lock className="w-2.5 h-2.5 text-zinc-500" />
                      )}
                    </div>
                    
                    <div className={cn(
                      "p-6 rounded-2xl border transition-all",
                      isUnlocked 
                        ? cn("bg-zinc-900/50 border-zinc-800 hover:border-zinc-700") 
                        : "bg-zinc-950 border-zinc-800/50 border-dashed"
                    )}>
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="text-lg font-medium">{episode.title}</h4>
                        <span className="text-xs font-semibold px-2 py-1 rounded-md bg-zinc-800 text-zinc-400">
                          Unlocks at Level {episode.unlockLevel}
                        </span>
                      </div>
                      <p className="text-zinc-400 text-sm">{episode.description}</p>
                      
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

      {/* Memory Details Modal */}
      <AnimatePresence>
        {activeEpisode && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-zinc-950/80 backdrop-blur-sm"
          >
            <motion.div
              initial={{ scale: 0.95, y: 20, opacity: 0 }}
              animate={{ scale: 1, y: 0, opacity: 1 }}
              exit={{ scale: 0.95, y: 20, opacity: 0 }}
              className="bg-zinc-900 border border-zinc-800 rounded-3xl w-full max-w-2xl overflow-hidden shadow-2xl relative"
            >
              <button 
                onClick={() => setActiveEpisode(null)}
                className="absolute top-4 right-4 p-2 text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-full transition-colors z-10"
              >
                <X className="w-5 h-5" />
              </button>

              <div className="p-8 sm:p-10">
                <div className="flex items-center gap-3 mb-6">
                  <div className={cn("w-10 h-10 rounded-full flex items-center justify-center", colors.bgLight)}>
                    <Unlock className={cn("w-5 h-5", colors.text)} />
                  </div>
                  <div>
                    <div className="text-xs font-semibold tracking-wider text-zinc-500 uppercase">Memory Unlocked</div>
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
                          <h3 className="text-sm font-medium text-zinc-400 uppercase tracking-wider mb-2">Scenario</h3>
                          <p className="text-zinc-200 leading-relaxed bg-zinc-950/50 p-4 rounded-xl border border-zinc-800/50">
                            {details?.scenario}
                          </p>
                        </div>
                        
                        <div>
                          <h3 className="text-sm font-medium text-zinc-400 uppercase tracking-wider mb-2">Backstory</h3>
                          <p className="text-zinc-200 leading-relaxed bg-zinc-950/50 p-4 rounded-xl border border-zinc-800/50">
                            {details?.backstory}
                          </p>
                        </div>

                        <div>
                          <h3 className="text-sm font-medium text-zinc-400 uppercase tracking-wider mb-2">Scene Narration</h3>
                          <p className="text-zinc-200 leading-relaxed bg-zinc-950/50 p-4 rounded-xl border border-zinc-800/50 italic border-l-2 border-l-emerald-500">
                            "{details?.narration}"
                          </p>
                        </div>
                      </div>
                    );
                  })()
                ) : (
                  <p className="text-zinc-400 text-center py-8 italic">Memory details are currently hazy...</p>
                )}

                <div className="mt-8 flex justify-end">
                  <button 
                    onClick={() => setActiveEpisode(null)}
                    className="px-6 py-2 bg-white text-zinc-950 font-medium rounded-xl hover:bg-zinc-200 transition-colors"
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
