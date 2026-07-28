import { useState, useEffect, useRef, useMemo } from "react";
import { useParams, Link, useNavigate } from "react-router";
import { motion, AnimatePresence } from "motion/react";
import { Send, Image, MoreHorizontal, ChevronLeft, ChevronRight, ArrowUpCircle, Sparkles, BookOpen, FileText, ThumbsUp, ThumbsDown, Heart, Trash2, AlertTriangle, Mail } from "lucide-react";
import { useStore, StoryEpisode } from "../store";
import { useShallow } from 'zustand/react/shallow';
import { companionColorClasses, cn, getPersonalizedEpisodeDetails } from "../utils";
import { episodeDetails } from "../storyData";
import { useProactiveMessages } from "../hooks/useProactiveMessages";

// Constants
const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL ?? 'http://localhost:8000';
const LEVEL_UP_DURATION_MS = 4000;

import { useEpisodeStore } from '../useEpisodeStore';

export default function Chat() {
  const { id: companionId } = useParams<{ id: string }>();
  const id = companionId;
  const navigate = useNavigate();
  const user = useStore(state => state.user);
  const companions = useStore(state => state.myCompanions);
  const currentIndex = companions.findIndex(c => c.id === id);
  const companion = companions[currentIndex];
  
  const { completedEpisodes, fetchEpisodes, fetchCompletedEpisodes } = useEpisodeStore();
  
  useEffect(() => {
    if (id) {
      fetchEpisodes(id);
      fetchCompletedEpisodes(id);
    }
  }, [id]);
  
  const activeEpisode = completedEpisodes.find(p => p.status === 'in_progress');
  const deleteCompanion = useStore(state => state.deleteCompanion);
  
  const prevCompanion = currentIndex > 0 ? companions[currentIndex - 1] : companions[companions.length - 1];
  const nextCompanion = currentIndex < companions.length - 1 ? companions[currentIndex + 1] : companions[0];

  const messages = useStore(useShallow(state => state.messages.filter(m => m.companionId === id)));
  
  // Fetch proactive messages and merge with regular messages
  const authToken = useStore(state => state.authToken);
  const { mergeWithMessages } = useProactiveMessages(id, authToken);
  const allMessages = useMemo(() => mergeWithMessages(messages), [messages, mergeWithMessages]);
  
  const sendMessage = useStore(state => state.sendMessage);
  const addSystemMessage = useStore(state => state.addSystemMessage);
  const rateMessage = useStore(state => state.rateMessage);
  const unlockNextLevel = useStore(state => state.unlockNextLevel);
  const startScenario = useStore(state => state.startScenario);
  const maybeAbandonScenario = useStore(state => state.maybeAbandonScenario);

  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isUnlocking, setIsUnlocking] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Level up state
  const prevLevelRef = useRef<number | null>(null);
  const [showLevelUp, setShowLevelUp] = useState(false);
  const [levelUpData, setLevelUpData] = useState<{level: number, colorClass: any, unlockedEpisode?: StoryEpisode} | null>(null);

  useEffect(() => {
    if (companion) {
      if (prevLevelRef.current !== null && companion.level > prevLevelRef.current) {
        const newlyUnlocked = companion.episodes.find(e => e.unlockLevel === companion.level);
        setLevelUpData({ 
          level: companion.level, 
          colorClass: companionColorClasses[companion.color],
          unlockedEpisode: newlyUnlocked
        });
        
        setShowLevelUp(true);
        setTimeout(() => setShowLevelUp(false), LEVEL_UP_DURATION_MS);

        if (newlyUnlocked && episodeDetails[newlyUnlocked.id]) {
          const baseName = useStore.getState().companions.find(c => c.id === companion.id)?.name || companion.name;
          const details = getPersonalizedEpisodeDetails(newlyUnlocked.id, baseName, companion.name);
          if (details) {
            const systemText = `NEW SCENARIO UNLOCKED: ${newlyUnlocked.title}\n\nSCENARIO:\n${details.scenario}\n\nBACKSTORY:\n${details.backstory}\n\nNARRATION:\n${details.narration}`;
            addSystemMessage(companion.id, systemText);
            startScenario(companion.id, newlyUnlocked.id, newlyUnlocked.title);

            const userId = user?.email;
            if (userId) {
              void fetch(`${API_BASE_URL}/memory/scenario/unlock`, {
                method: 'POST',
                headers: { 
                  'Content-Type': 'application/json',
                  ...(useStore.getState().authToken ? { Authorization: `Bearer ${useStore.getState().authToken}` } : {}),
                },
                body: JSON.stringify({
                  user_id: userId,
                  companion_id: companion.id,
                  title: newlyUnlocked.title,
                  scenario: details.scenario,
                  backstory: details.backstory,
                  narration: details.narration
                })
              }).catch(() => {});
            }
          }
        }
      }
      prevLevelRef.current = companion.level;
    }
  }, [companion?.level, user?.email]);

  useEffect(() => {
    if (!id) return;
    const currentCompanions = useStore.getState().myCompanions;
    return () => {
      // Only call maybeAbandonScenario if companion is still in myCompanions
      const isCompanionStillThere = useStore.getState().myCompanions.some(c => c.id === id);
      if (isCompanionStillThere) {
        maybeAbandonScenario(id);
      }
    };
  }, [id]);

  const colors = companion ? companionColorClasses[companion.color] : companionColorClasses.blue;

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [allMessages, isTyping]);

  // Close dropdown when clicking outside
  useEffect(() => {
    // Add a small delay before enabling the click-outside handler
    // This prevents the dropdown from closing immediately when opened
    const timer = setTimeout(() => {
      if (!showDropdown) return;

      const handleClickOutside = (event: MouseEvent) => {
        const target = event.target as HTMLElement;
        console.log('[CLICK OUTSIDE HANDLER] showDropdown:', showDropdown, 'target closest dropdown-container:', target.closest('.dropdown-container'));
        if (showDropdown && !target.closest('.dropdown-container')) {
          console.log('[CLICK OUTSIDE HANDLER] Closing dropdown');
          setShowDropdown(false);
        }
      };

      document.addEventListener('mousedown', handleClickOutside);
      
      // Cleanup function
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }, 100); // 100ms delay

    return () => clearTimeout(timer);
  }, [showDropdown]);

  if (!companion) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-zinc-950 text-zinc-50">
        <h2 className="text-xl font-medium mb-4">Companion not found</h2>
        <Link to="/app" className="text-purple-400 hover:text-purple-300">Return to Dashboard</Link>
      </div>
    );
  }

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const currentInput = input;
    setInput("");
    
    // Optimistic user message
    setIsTyping(true);
    void sendMessage(companion.id, currentInput).finally(() => {
      setIsTyping(false);
    });
  };

  const handleFeedback = (messageId: string, rating: -1 | 1) => {
    const userId = user?.email;
    const idx = messages.findIndex(m => m.id === messageId);
    if (idx === -1) return;
    const assistantMsg = messages[idx];
    if (assistantMsg.sender !== 'companion') return;

    let userMessageText: string | null = null;
    for (let i = idx - 1; i >= 0; i -= 1) {
      const m = messages[i];
      if (m.sender === 'user') {
        userMessageText = m.text;
        break;
      }
    }

    rateMessage(messageId, rating);

    // Only send feedback to backend if user is authenticated
    if (userId) {
      void fetch(`${API_BASE_URL}/memory/feedback`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          ...(useStore.getState().authToken ? { Authorization: `Bearer ${useStore.getState().authToken}` } : {}),
        },
        body: JSON.stringify({
          user_id: userId,
          companion_id: companion.id,
          rating,
          user_message: userMessageText,
          assistant_message: assistantMsg.text
        })
      }).catch(() => {});
    }
  };

  const progress = (companion.xp / companion.nextLevelXp) * 100;
  const canUnlock = !!companion.pendingLevelUp;
  const relationshipPoints = companion.relationshipPoints ?? 0;
  const relationshipStage = relationshipPoints >= 500
    ? 'Confidant'
    : relationshipPoints >= 300
      ? 'Close Friend'
      : relationshipPoints >= 150
        ? 'Friend'
        : relationshipPoints >= 50
          ? 'Curious'
          : 'Stranger';

  return (
    <div className="flex-1 flex flex-col bg-zinc-950 text-zinc-50 relative h-full overflow-hidden">
      {/* Dynamic Background Glow based on companion color */}
      <div className={cn(
        "absolute top-0 right-0 w-[800px] h-[800px] rounded-full blur-[150px] opacity-10 pointer-events-none transition-colors duration-1000",
        colors.bg
      )} />

      {/* Level Up Overlay Animation */}
      <AnimatePresence>
        {showLevelUp && levelUpData && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-[100] pointer-events-none flex items-center justify-center bg-zinc-950/40 backdrop-blur-sm"
          >
            <motion.div
              initial={{ scale: 0.8, y: 50, opacity: 0 }}
              animate={{ scale: 1, y: 0, opacity: 1 }}
              exit={{ scale: 0.8, y: -50, opacity: 0 }}
              transition={{ type: "spring", stiffness: 300, damping: 25 }}
              className="relative"
            >
              {/* Starburst/glow behind */}
              <motion.div 
                animate={{ rotate: 360 }}
                transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
                className={cn("absolute -inset-20 rounded-full blur-[60px] opacity-40", levelUpData.colorClass.bg)} 
              />
              
              <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 sm:p-12 shadow-2xl relative flex flex-col items-center text-center w-[300px] sm:w-[400px]">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: [0, 1.2, 1] }}
                  transition={{ delay: 0.2, duration: 0.5 }}
                  className={cn("w-20 h-20 rounded-full flex items-center justify-center mb-6", levelUpData.colorClass.bgLight)}
                >
                  <ArrowUpCircle className={cn("w-10 h-10", levelUpData.colorClass.text)} />
                </motion.div>
                
                <h2 className="text-3xl font-bold tracking-tight mb-2 flex items-center gap-2">
                  <Sparkles className="w-6 h-6 text-yellow-500" />
                  Level Up!
                  <Sparkles className="w-6 h-6 text-yellow-500" />
                </h2>
                
                <p className="text-zinc-400 mb-6">
                  Your bond with <span className="font-semibold text-zinc-200">{companion.name}</span> has grown stronger.
                </p>
                
                <div className="flex items-center gap-4 text-5xl font-light">
                  <span className="text-zinc-500 line-through">{levelUpData.level - 1}</span>
                  <span className="text-zinc-600">→</span>
                  <motion.span 
                    initial={{ scale: 1 }}
                    animate={{ scale: [1, 1.5, 1] }}
                    transition={{ delay: 0.8, duration: 0.4 }}
                    className={cn("font-bold text-white", levelUpData.colorClass.text)}
                  >
                    {levelUpData.level}
                  </motion.span>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header */}
      <header className="px-4 sm:px-6 py-4 border-b border-zinc-800/50 bg-zinc-950/80 backdrop-blur-xl flex items-center justify-between z-20 shrink-0">
        <div className="flex items-center gap-2 sm:gap-4">
          <Link to="/app" className="p-2 hover:bg-zinc-900 rounded-full transition-colors mr-0 sm:mr-2 text-zinc-400 hover:text-white md:hidden">
            <ChevronLeft className="w-5 h-5" />
          </Link>

          {/* Previous Character Arrow */}
          {companions.length > 1 && (
            <button 
              onClick={() => navigate(`/app/companion/${prevCompanion.id}/chat`)}
              className="p-1 sm:p-2 hover:bg-zinc-900 rounded-full transition-colors text-zinc-400 hover:text-white"
            >
              <ChevronLeft className="w-4 h-4 sm:w-5 sm:h-5" />
            </button>
          )}
          
          <Link to={`/app/companion/${companion.id}/profile`} className="relative group shrink-0">
            <img 
              src={companion.avatarUrl} 
              alt={companion.name} 
              className={cn("w-10 h-10 sm:w-12 sm:h-12 rounded-full object-cover ring-2 ring-transparent transition-all", colors.ring)} 
            />
            <div className="absolute -bottom-1 -right-1 w-3 h-3 sm:w-4 sm:h-4 rounded-full border-2 border-zinc-950 bg-emerald-500" />
          </Link>
          
          <div className="min-w-0 flex-1">
            <Link to={`/app/companion/${companion.id}/profile`} className="hover:underline truncate block">
              <h2 className="font-semibold text-base sm:text-lg leading-tight truncate">{companion.name}</h2>
            </Link>
            <div className="text-[10px] sm:text-xs text-zinc-400 flex items-center gap-1.5 sm:gap-2 mt-0.5 whitespace-nowrap overflow-hidden text-ellipsis">
              <span className="truncate">{companion.personality}</span>
              <span className="w-1 h-1 rounded-full bg-zinc-600 shrink-0" />
              <span className={cn("font-medium shrink-0", colors.text)}>Level {companion.level}</span>
              <span className="w-1 h-1 rounded-full bg-zinc-600 shrink-0" />
              <span className="shrink-0 flex items-center gap-1">
                <Heart className="w-3 h-3 text-pink-400" />
                <span>{relationshipStage}</span>
              </span>
            </div>
          </div>

          {/* Next Character Arrow */}
          {companions.length > 1 && (
            <button 
              onClick={() => navigate(`/app/companion/${nextCompanion.id}/chat`)}
              className="p-1 sm:p-2 hover:bg-zinc-900 rounded-full transition-colors text-zinc-400 hover:text-white"
            >
              <ChevronRight className="w-4 h-4 sm:w-5 sm:h-5" />
            </button>
          )}
        </div>

        <div className="flex items-center gap-4 hidden sm:flex">
          <div className="w-32 text-right">
            <div className="flex justify-between text-[10px] uppercase font-bold text-zinc-500 mb-1 tracking-widest">
              <span>XP</span>
              <span>{companion.xp}/{companion.nextLevelXp}</span>
            </div>
            <div className="h-1.5 w-full bg-zinc-900 rounded-full overflow-hidden">
              <motion.div 
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.5, ease: "easeOut" }}
                className={cn("h-full rounded-full", colors.bg, colors.glow)}
              />
            </div>
          </div>
          
          <div className="relative dropdown-container" ref={dropdownRef}>
            <button 
              onClick={() => {
                console.log('[DROPDOWN BUTTON CLICKED] current showDropdown:', showDropdown, 'toggling to:', !showDropdown);
                setShowDropdown(!showDropdown);
              }}
              className="p-2 text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-full transition-colors"
            >
              <MoreHorizontal className="w-5 h-5" />
            </button>

            {showDropdown && (
              <div className="absolute right-0 top-full mt-2 bg-zinc-900 border border-zinc-700 rounded-xl shadow-xl p-2 min-w-[180px] z-50">
                <button
                  type="button"
                  onClick={() => {
                    console.log('[DELETE COMPANION BUTTON CLICKED] in dropdown');
                    console.log('[DELETE COMPANION] Setting showDropdown to false, showDeleteConfirm to true');
                    setShowDropdown(false);
                    setShowDeleteConfirm(true);
                    console.log('[DELETE COMPANION] showDeleteConfirm should now be true');
                  }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                  Delete Companion
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Delete Confirmation Dialog */}
      <AnimatePresence>
        {showDeleteConfirm && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-[110] flex items-center justify-center bg-black/60 backdrop-blur-sm"
            onClick={() => setShowDeleteConfirm(false)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20, opacity: 0 }}
              animate={{ scale: 1, y: 0, opacity: 1 }}
              exit={{ scale: 0.9, y: -20, opacity: 0 }}
              className="bg-zinc-900 border border-zinc-700 rounded-3xl p-6 sm:p-8 shadow-2xl w-[90%] sm:w-[450px]"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-center gap-3 mb-4">
                <div className="p-3 rounded-full bg-red-500/10">
                  <AlertTriangle className="w-8 h-8 text-red-400" />
                </div>
              </div>
              
              <h2 className="text-xl font-bold text-center mb-2">Delete {companion.name}?</h2>
              
              <p className="text-zinc-400 text-center mb-6">
                This will delete all your messages, progress, and memories with {companion.name}. This action cannot be undone.
              </p>
              
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowDeleteConfirm(false)}
                  className="flex-1 px-4 py-3 rounded-xl bg-zinc-800 text-zinc-300 font-medium hover:bg-zinc-700 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  disabled={isDeleting}
                  onClick={async () => {
                    console.log('[DELETE BUTTON CLICKED] companion.id:', companion.id, 'companion.name:', companion.name);
                    try {
                      setIsDeleting(true);
                      console.log('[DELETE] Calling deleteCompanion...');
                      await deleteCompanion(companion.id);
                      console.log('[DELETE] deleteCompanion completed, navigating to /app');
                      navigate('/app');
                    } catch (e) {
                      console.error('[DELETE ERROR]', e);
                      alert('Failed to delete companion. Check console for details.');
                    } finally {
                      setIsDeleting(false);
                      console.log('[DELETE] isDeleting set to false');
                    }
                  }}
                  className={cn("flex-1 px-4 py-3 rounded-xl bg-red-600 text-white font-medium hover:bg-red-500 transition-colors", isDeleting && "opacity-70 cursor-not-allowed")}
                >
                  {isDeleting ? "Deleting..." : "Delete"}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Active Story Banner */}
      {activeEpisode && (
        <div className="mx-4 sm:mx-6 my-4 bg-gradient-to-r from-indigo-600/20 to-purple-600/20 border border-indigo-500/30 rounded-2xl p-4 flex items-center gap-3">
          <BookOpen className="w-6 h-6 text-indigo-400 shrink-0" />
          <div className="flex-1">
            <p className="text-sm font-medium text-indigo-200">
              📖 Active Story: Your choices affect the narrative
            </p>
          </div>
          <Link 
            to={`/app/companion/${id}/episodes/play/${activeEpisode.episode_id}`}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-xl transition-colors"
          >
            Continue Story
          </Link>
        </div>
      )}
      
      <div className="flex-1 overflow-y-auto p-6 scroll-smooth z-10 space-y-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center max-w-sm mx-auto opacity-50">
            <img src={companion.avatarUrl} alt="" className="w-24 h-24 rounded-full object-cover mb-6 grayscale opacity-50" />
            <h3 className="text-xl font-medium mb-2">Say Hello to {companion.name}</h3>
            <p className="text-sm">Start a conversation to learn more about them, level up, and unlock their story episodes.</p>
          </div>
        ) : (
          <AnimatePresence initial={false}>
            {allMessages.map((msg, idx) => {
              const isUser = msg.sender === 'user';
              const isSystem = msg.sender === 'system';

              if (isSystem) {
                // Check if it's a Companion Profile message
                if (msg.text.startsWith('COMPANION PROFILE:')) {
                  const parts = msg.text.split('\n\n');
                  const namePart = parts[0]?.replace('COMPANION PROFILE: ', '');
                  const agePart = parts[1]?.replace('AGE:\n', '');
                  const relationshipPart = parts[2]?.replace('RELATIONSHIP:\n', '');
                  const storyPart = parts[3]?.replace('STORY:\n', '');
                  const characteristicsPart = parts[4]?.replace('CHARACTERISTICS:\n', '');

                  return (
                    <motion.div
                      key={msg.id}
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="w-full flex justify-center my-8"
                    >
                      <div className="bg-zinc-900/80 border border-zinc-800/80 rounded-2xl p-6 w-full max-w-[90%] sm:max-w-[75%] shadow-xl">
                        <div className="flex items-center justify-center gap-2 mb-2">
                          <FileText className={cn("w-4 h-4", colors.text)} />
                          <h3 className={cn("text-xs font-bold tracking-widest uppercase", colors.text)}>Dossier</h3>
                        </div>
                        
                        <h4 className="text-xl font-medium text-white text-center mb-6">{namePart}</h4>
                        
                        <div className="grid grid-cols-2 gap-4 mb-4">
                          <div className="bg-zinc-950/50 p-3 rounded-xl border border-zinc-800/50">
                            <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider block mb-1">Age</span>
                            <span className="text-zinc-200 text-sm font-medium">{agePart}</span>
                          </div>
                          <div className="bg-zinc-950/50 p-3 rounded-xl border border-zinc-800/50">
                            <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider block mb-1">Relationship</span>
                            <span className="text-zinc-200 text-sm font-medium">{relationshipPart}</span>
                          </div>
                        </div>

                        <div className="space-y-4 text-[13px] sm:text-[14px] leading-relaxed">
                          <div className="bg-zinc-950/50 p-4 rounded-xl border border-zinc-800/50">
                            <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider block mb-1">Story</span>
                            <span className="text-zinc-300">{storyPart}</span>
                          </div>
                          <div className="bg-zinc-950/50 p-4 rounded-xl border border-zinc-800/50">
                            <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider block mb-2">Characteristics</span>
                            <div className="flex flex-wrap gap-2">
                              {characteristicsPart?.split(', ').map((trait, i) => (
                                <span key={i} className={cn("px-2 py-1 rounded-md text-[10px] font-semibold uppercase tracking-wider", colors.bgLight, colors.text)}>
                                  {trait}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  );
                }

                // Check if it's the formatted scenario message
                if (msg.text.startsWith('NEW SCENARIO UNLOCKED:')) {
                  const parts = msg.text.split('\n\n');
                  const titlePart = parts[0]?.replace('NEW SCENARIO UNLOCKED: ', '');
                  const scenarioPart = parts[1]?.replace('SCENARIO:\n', '');
                  const backstoryPart = parts[2]?.replace('BACKSTORY:\n', '');
                  const narrationPart = parts[3]?.replace('NARRATION:\n', '');

                  return (
                    <motion.div
                      key={msg.id}
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="w-full flex justify-center my-8"
                    >
                      <div className="bg-zinc-900/80 border border-zinc-800/80 rounded-2xl p-6 w-full max-w-[90%] sm:max-w-[75%] shadow-xl">
                        <div className="flex items-center justify-center gap-2 mb-2">
                          <BookOpen className="w-4 h-4 text-emerald-400" />
                          <h3 className="text-xs font-bold tracking-widest text-emerald-400 uppercase">New Memory Unlocked</h3>
                        </div>
                        
                        <h4 className="text-lg font-medium text-white text-center mb-6">{titlePart}</h4>
                        
                        <div className="space-y-4 text-[13px] sm:text-[14px] leading-relaxed">
                          <div>
                            <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider block mb-1">Scenario</span>
                            <span className="text-zinc-200">{scenarioPart}</span>
                          </div>
                          <div>
                            <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider block mb-1">Backstory</span>
                            <span className="text-zinc-300">{backstoryPart}</span>
                          </div>
                          <div className="border-l-2 border-emerald-500/50 pl-4 py-1 italic text-zinc-400 mt-4 bg-zinc-950/30 rounded-r-lg">
                            "{narrationPart}"
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  );
                }

                // Fallback for simple system messages
                return (
                  <motion.div
                    key={msg.id}
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="w-full flex justify-center my-4"
                  >
                    <div className="px-4 py-1.5 rounded-full bg-zinc-900/50 border border-zinc-800 text-xs text-zinc-400 font-medium">
                      {msg.text}
                    </div>
                  </motion.div>
                );
              }
              
              return (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 10, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  transition={{ duration: 0.3, type: "spring", stiffness: 200, damping: 20 }}
                  className={cn("flex w-full", isUser ? "justify-end" : "justify-start")}
                >
                  <div className={cn("flex max-w-[80%] items-end gap-3", isUser ? "flex-row-reverse" : "flex-row")}>
                    {!isUser && (
                      <img src={companion.avatarUrl} alt="" className="w-8 h-8 rounded-full object-cover flex-shrink-0 mb-1" />
                    )}
                    
                    <div 
                      className={cn(
                        "px-5 py-3.5 rounded-2xl text-[15px] leading-relaxed relative group",
                        isUser 
                          ? "bg-zinc-800 text-white rounded-br-sm" 
                          : msg.isProactive
                            ? "bg-gradient-to-br from-slate-700/80 to-slate-800/80 text-zinc-100 rounded-bl-sm border border-slate-600/50 backdrop-blur-md"
                            : cn(colors.bgLight, "text-zinc-100 rounded-bl-sm border border-white/5 backdrop-blur-md")
                      )}
                    >
                      {/* Proactive message indicator */}
                      {msg.isProactive && (
                        <div className="flex items-center gap-1.5 mb-2 pb-2 border-b border-slate-600/50">
                          <Mail className="w-3 h-3 text-slate-400" />
                          <span className="text-[10px] text-slate-400 uppercase tracking-wider font-medium">
                            From {companion.name}
                          </span>
                        </div>
                      )}
                      {msg.text}
                      {msg.sender === 'companion' && (
                        <div className="mt-2 flex items-center justify-end gap-1 opacity-70 hover:opacity-100 transition-opacity">
                          <button
                            type="button"
                            onClick={() => handleFeedback(msg.id, 1)}
                            className={cn(
                              "p-1 rounded-md hover:bg-white/10 transition-colors",
                              msg.feedback === 1 ? "text-emerald-300" : "text-zinc-300"
                            )}
                            aria-label="Thumbs up"
                          >
                            <ThumbsUp className="w-4 h-4" />
                          </button>
                          <button
                            type="button"
                            onClick={() => handleFeedback(msg.id, -1)}
                            className={cn(
                              "p-1 rounded-md hover:bg-white/10 transition-colors",
                              msg.feedback === -1 ? "text-red-300" : "text-zinc-300"
                            )}
                            aria-label="Thumbs down"
                          >
                            <ThumbsDown className="w-4 h-4" />
                          </button>
                        </div>
                      )}
                      <span className="absolute -bottom-5 text-[10px] text-zinc-600 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                        {new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                      </span>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        )}

        {/* Typing Indicator */}
        <AnimatePresence>
          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.2 } }}
              className="flex w-full justify-start"
            >
              <div className="flex items-end gap-3 max-w-[80%]">
                <img src={companion.avatarUrl} alt="" className="w-8 h-8 rounded-full object-cover flex-shrink-0 mb-1" />
                <div className={cn("px-5 py-4 rounded-2xl rounded-bl-sm flex items-center gap-1.5", colors.bgLight)}>
                  <motion.div animate={{ y: [0, -4, 0] }} transition={{ repeat: Infinity, duration: 0.6, delay: 0 }} className={cn("w-1.5 h-1.5 rounded-full", colors.bg)} />
                  <motion.div animate={{ y: [0, -4, 0] }} transition={{ repeat: Infinity, duration: 0.6, delay: 0.2 }} className={cn("w-1.5 h-1.5 rounded-full", colors.bg)} />
                  <motion.div animate={{ y: [0, -4, 0] }} transition={{ repeat: Infinity, duration: 0.6, delay: 0.4 }} className={cn("w-1.5 h-1.5 rounded-full", colors.bg)} />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        <div ref={messagesEndRef} className="h-4" />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-zinc-950/80 backdrop-blur-xl border-t border-zinc-800/50 z-10">
        <div className="max-w-4xl mx-auto relative">
          {canUnlock && (
            <div className="mb-3 flex items-center justify-between gap-3 bg-zinc-900/60 border border-zinc-800 rounded-2xl px-4 py-3">
              <div className="text-sm text-zinc-300">
                XP is full. Unlock the next level to start the next story episode.
              </div>
              <button
                type="button"
                disabled={isUnlocking}
                onClick={async () => {
                  setIsUnlocking(true);
                  await unlockNextLevel(companion.id);
                  setIsUnlocking(false);
                }}
                className={cn("px-3 py-2 rounded-xl text-sm font-semibold text-white transition-all", colors.bg, colors.glow, isUnlocking && "opacity-70 cursor-not-allowed")}
              >
                {isUnlocking ? "Unlocking..." : `Unlock Level ${companion.level + 1}`}
              </button>
            </div>
          )}
          <form onSubmit={handleSend} className="relative flex items-end bg-zinc-900 border border-zinc-800 rounded-3xl p-1 shadow-lg focus-within:ring-2 focus-within:ring-zinc-700 transition-all">
            <button type="button" className="p-3 text-zinc-500 hover:text-zinc-300 transition-colors shrink-0">
              <Image className="w-5 h-5" />
            </button>
            
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend(e);
                }
              }}
              placeholder={`Message ${companion.name}...`}
              className="flex-1 max-h-32 min-h-[44px] bg-transparent resize-none focus:outline-none text-[15px] py-3 px-2 text-zinc-200 placeholder-zinc-500 custom-scrollbar"
              rows={1}
            />
            
            <button 
              type="submit" 
              disabled={!input.trim()}
              className={cn(
                "p-3 rounded-full flex items-center justify-center shrink-0 transition-all m-1",
                input.trim() 
                  ? cn(colors.bg, "text-white", colors.glow) 
                  : "bg-zinc-800 text-zinc-500"
              )}
            >
              <Send className="w-5 h-5 ml-0.5" />
            </button>
          </form>
          <div className="text-center mt-2">
            <span className="text-[10px] text-zinc-600 font-medium tracking-widest uppercase">
              {canUnlock ? "XP is full — unlock the next level to continue progression." : `Thoughtful messages earn XP; low-effort/toxic messages can lose XP.`}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
