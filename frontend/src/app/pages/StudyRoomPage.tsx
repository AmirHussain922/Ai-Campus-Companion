import { useEffect, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BookOpen, Trophy, Zap, Target, AlertTriangle, Sparkles, Image as ImageIcon, Upload, Send, Clock, MessageSquare } from 'lucide-react';
import { useStore } from '../store';
import { useStudyStore, StudyMode } from '../stores/useStudyStore';
import { StudyTimer } from '../components/StudyTimer';
import { cn } from '../utils';
import confetti from 'canvas-confetti';
import axios from 'axios';

const API_BASE_URL = ((import.meta as any).env?.VITE_API_BASE_URL ?? 'http://localhost:8000') + '/api';

// Companion data for study room
const studyCompanions: Record<StudyMode, { 
  name: string; 
  avatar: string; 
  color: string;
  messages: string[];
}> = {
  supportive: {
    name: 'Oliver',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Oliver',
    color: 'emerald',
    messages: [
      "You've got this! I believe in you! 🌟",
      "Every minute of focus brings you closer to your goals.",
      "Take a deep breath. You're doing amazing!",
      "Remember why you started. You're capable of great things!",
      "Your dedication inspires me. Keep going! 💪"
    ]
  },
  challenger: {
    name: 'Victoria',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Victoria',
    color: 'rose',
    messages: [
      "Distractions are for the weak. Focus! 💢",
      "Your competitors are studying right now. Are you?",
      "Push through the discomfort. That's where growth happens.",
      "Don't you dare give up. You're stronger than this.",
      "Prove to yourself what you're capable of. No excuses! 🔥"
    ]
  }
};

export default function StudyRoomPage() {
  const authToken = useStore(state => state.authToken);
  const {
    session,
    timerRemaining,
    isActive,
    isPaused,
    interruptions,
    selectedMode,
    showAbandonConfirm,
    showCompleteModal,
    earnedXP,
    startSession,
    completeSession,
    abandonSession,
    pauseTimer,
    resumeTimer,
    setMode,
    setShowAbandonConfirm,
    setShowCompleteModal
  } = useStudyStore();

  const [topic, setTopic] = useState('');
  const [duration, setDuration] = useState(25); // minutes
  const [activeTab, setActiveTab] = useState<'study' | 'chat' | 'leaderboard'>('study');
  const [companionMessage, setCompanionMessage] = useState('');
  const [uploadedImages, setUploadedImages] = useState<string[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedSubject, setSelectedSubject] = useState<string>('math');
  const [chatMessages, setChatMessages] = useState<Array<{id: string, role: 'user' | 'companion', content: string}>>([
    { id: '1', role: 'companion', content: 'Hi there! I can help you with your studies! What do you need help with today?' }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  const messageTimerRef = useRef<NodeJS.Timeout | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const companion = studyCompanions[selectedMode];

  // Timer tick effect
  useEffect(() => {
    if (!isActive) return;
    
    const interval = setInterval(() => {
      // tickTimer is handled by the store
    }, 1000);

    return () => clearInterval(interval);
  }, [isActive, isPaused]);

  // Show companion message periodically during session
  useEffect(() => {
    if (!isActive || isPaused) {
      if (messageTimerRef.current) {
        clearInterval(messageTimerRef.current);
      }
      return;
    }

    // Initial message
    if (!companionMessage) {
      setCompanionMessage(companion.messages[0]);
    }

    messageTimerRef.current = setInterval(() => {
      const messages = companion.messages;
      const randomMessage = messages[Math.floor(Math.random() * messages.length)];
      setCompanionMessage(randomMessage);
    }, 45000); // Change every 45 seconds

    return () => {
      if (messageTimerRef.current) {
        clearInterval(messageTimerRef.current);
      }
    };
  }, [isActive, isPaused, companion.messages, companionMessage]);

  const handleStart = async () => {
    if (!topic.trim()) return;
    await startSession(duration, topic.trim(), authToken);
    setCompanionMessage(companion.messages[0]);
  };

  const handleComplete = async () => {
    await completeSession(authToken);
    
    // Trigger confetti
    confetti({
      particleCount: 150,
      spread: 70,
      origin: { y: 0.6 },
      colors: ['#10b981', '#f59e0b', '#ec4899', '#8b5cf6']
    });
  };

  const handleAbandon = () => {
    abandonSession(authToken);
    setShowAbandonConfirm(false);
    setTopic('');
    setCompanionMessage('');
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setIsUploading(true);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await axios.post(`${API_BASE_URL}/media/upload`, formData, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'multipart/form-data',
        },
      });
      
      if (response.data.success) {
        setUploadedImages([...uploadedImages, response.data.url]);
        setCompanionMessage(`${companion.name}: "Great notes! Let me take a look at that image and help you understand it better!"`);
      }
    } catch (error) {
      console.error('Failed to upload file:', error);
    } finally {
      setIsUploading(false);
    }
  };

  const handleChatSend = async () => {
    if (!chatInput.trim() || isChatLoading) return;

    const userMessageId = Date.now().toString();
    const newMessages = [...chatMessages, { id: userMessageId, role: 'user', content: chatInput.trim() }];
    setChatMessages(newMessages);
    setChatInput('');
    setIsChatLoading(true);

    try {
      const backendCompanionId = selectedMode === 'supportive' ? 'study_buddy' : 'rival';
      const response = await axios.post(`${API_BASE_URL}/chat`, {
        companion_key: selectedMode === 'supportive' ? 'c1' : 'c4',
        personality_id: backendCompanionId,
        message: `Subject: ${selectedSubject}\n${chatInput.trim()}`,
      }, {
        headers: { Authorization: `Bearer ${authToken}` },
      });

      const companionResponse = response.data?.reply || "I'm here to help! Could you clarify your question?";
      setChatMessages([...newMessages, { id: (Date.now() + 1).toString(), role: 'companion', content: companionResponse }]);
    } catch (error) {
      console.error('Chat failed:', error);
      setChatMessages([...newMessages, { id: (Date.now() + 1).toString(), role: 'companion', content: 'Sorry, I had trouble processing that. Please try again.' }]);
    } finally {
      setIsChatLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <div className="sticky top-0 z-20 bg-slate-950/80 backdrop-blur-xl border-b border-slate-800">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-indigo-500/10 rounded-xl border border-indigo-500/20">
                <BookOpen className="w-6 h-6 text-indigo-400" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">Study Room</h1>
                <p className="text-sm text-slate-400">Focus with your companions</p>
              </div>
            </div>

            {/* Mode Toggle */}
            <div className="flex items-center gap-2 bg-slate-900/50 p-1 rounded-xl border border-slate-800">
              <button
                onClick={() => setMode('supportive')}
                className={cn(
                  "px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200",
                  selectedMode === 'supportive'
                    ? "bg-emerald-500/20 text-emerald-400"
                    : "text-slate-400 hover:text-white"
                )}
              >
                Oliver
              </button>
              <button
                onClick={() => setMode('challenger')}
                className={cn(
                  "px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200",
                  selectedMode === 'challenger'
                    ? "bg-rose-500/20 text-rose-400"
                    : "text-slate-400 hover:text-white"
                )}
              >
                Victoria
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex items-center gap-1 mt-4 bg-slate-900/30 p-1 rounded-xl w-fit mx-auto">
            <button
              onClick={() => setActiveTab('study')}
              className={cn(
                "px-6 py-2 rounded-lg text-sm font-medium transition-all duration-200",
                activeTab === 'study'
                  ? "bg-slate-700 text-white"
                  : "text-slate-400 hover:text-white"
              )}
            >
              Focus Session
            </button>
            <button
              onClick={() => setActiveTab('chat')}
              className={cn(
                "px-6 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center gap-2",
                activeTab === 'chat'
                  ? "bg-slate-700 text-white"
                  : "text-slate-400 hover:text-white"
              )}
            >
              <MessageSquare className="w-4 h-4" />
              Study Help
            </button>
            <button
              onClick={() => setActiveTab('leaderboard')}
              className={cn(
                "px-6 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center gap-2",
                activeTab === 'leaderboard'
                  ? "bg-slate-700 text-white"
                  : "text-slate-400 hover:text-white"
              )}
            >
              <Trophy className="w-4 h-4" />
              Leaderboard
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        {/* Chat Tab */}
        {activeTab === 'chat' && (
          <div className="max-w-3xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 sm:p-8"
            >
              {/* Subject Selector */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-slate-300 mb-2">Select Subject</label>
                <div className="flex flex-wrap gap-2">
                  {[
                    { id: 'math', label: 'Mathematics' },
                    { id: 'physics', label: 'Physics' },
                    { id: 'chemistry', label: 'Chemistry' },
                    { id: 'biology', label: 'Biology' },
                    { id: 'computer_science', label: 'Computer Science' },
                    { id: 'history', label: 'History' },
                    { id: 'english', label: 'English' },
                  ].map((subject) => (
                    <button
                      key={subject.id}
                      onClick={() => setSelectedSubject(subject.id)}
                      className={cn(
                        "px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 border",
                        selectedSubject === subject.id
                          ? "bg-indigo-600 border-indigo-500 text-white"
                          : "bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700"
                      )}
                    >
                      {subject.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Chat Messages */}
              <div className="bg-slate-950/50 border border-slate-800 rounded-xl h-[400px] overflow-y-auto p-4 mb-4 space-y-4">
                {chatMessages.map((message) => (
                  <div
                    key={message.id}
                    className={cn(
                      "flex gap-3",
                      message.role === 'user' ? "justify-end" : "justify-start"
                    )}
                  >
                    {message.role === 'companion' && (
                      <div className={cn(
                        "w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0",
                        selectedMode === 'supportive' ? "bg-emerald-500/20 text-emerald-400" : "bg-rose-500/20 text-rose-400"
                      )}>
                        {companion.name.charAt(0)}
                      </div>
                    )}
                    <div className={cn(
                      "max-w-[80%] px-4 py-3 rounded-xl",
                      message.role === 'user'
                        ? "bg-indigo-600 text-white rounded-br-sm"
                        : "bg-slate-800 text-slate-200 rounded-bl-sm"
                    )}>
                      {message.content}
                    </div>
                    {message.role === 'user' && (
                      <div className="w-8 h-8 shrink-0" />
                    )}
                  </div>
                ))}
                {isChatLoading && (
                  <div className="flex gap-3 items-center">
                    <div className={cn(
                      "w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0",
                      selectedMode === 'supportive' ? "bg-emerald-500/20 text-emerald-400" : "bg-rose-500/20 text-rose-400"
                    )}>
                      {companion.name.charAt(0)}
                    </div>
                    <div className="bg-slate-800 px-4 py-3 rounded-xl rounded-bl-sm flex gap-1">
                      <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                )}
              </div>

              {/* Chat Input */}
              <div className="flex gap-3">
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') handleChatSend(); }}
                  placeholder={`Ask about ${selectedSubject}...`}
                  className="flex-1 px-4 py-3 bg-slate-950 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                />
                <button
                  onClick={handleChatSend}
                  disabled={!chatInput.trim() || isChatLoading}
                  className={cn(
                    "px-5 py-3 rounded-xl font-medium transition-all duration-200 flex items-center gap-2",
                    chatInput.trim() && !isChatLoading
                      ? "bg-indigo-600 hover:bg-indigo-500 text-white"
                      : "bg-slate-800 text-slate-500 cursor-not-allowed"
                  )}
                >
                  {isChatLoading ? (
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <Send className="w-5 h-5" />
                  )}
                </button>
              </div>
            </motion.div>
          </div>
        )}

        {/* Study Session Tab */}
        {activeTab === 'study' && (
          <>
            {!isActive ? (
              /* Setup View */
              <div className="max-w-2xl mx-auto">
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 sm:p-8"
                >
                  {/* Companion Preview */}
                  <div className="flex flex-col items-center mb-8">
                    <motion.div
                      initial={{ scale: 0.8, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      transition={{ delay: 0.2 }}
                      className="relative"
                    >
                      <div className={cn(
                        "w-24 h-24 rounded-full p-1",
                        selectedMode === 'supportive' ? "bg-emerald-500/20" : "bg-rose-500/20"
                      )}>
                        <img
                          src={companion.avatar}
                          alt={companion.name}
                          className="w-full h-full rounded-full object-cover bg-slate-800"
                        />
                      </div>
                      <motion.div
                        animate={{ scale: [1, 1.2, 1] }}
                        transition={{ duration: 2, repeat: Infinity }}
                        className={cn(
                          "absolute -bottom-1 -right-1 w-6 h-6 rounded-full flex items-center justify-center",
                          selectedMode === 'supportive' ? "bg-emerald-500" : "bg-rose-500"
                        )}>
                        <span className="text-xs">{selectedMode === 'supportive' ? '🌟' : '💢'}</span>
                      </motion.div>
                    </motion.div>
                    
                    <h3 className="mt-4 text-lg font-semibold text-white">{companion.name}</h3>
                    <p className="text-sm text-slate-400">
                      {selectedMode === 'supportive' 
                        ? 'Supportive mode - gentle encouragement' 
                        : 'Challenger mode - tough love motivation'}
                    </p>
                  </div>

                  {/* Topic Input */}
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      What are you focusing on?
                    </label>
                    <input
                      type="text"
                      value={topic}
                      onChange={(e) => setTopic(e.target.value)}
                      placeholder="e.g., Calculus homework, Reading chapter 3..."
                      className="w-full px-4 py-3 bg-slate-950 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
                    />
                  </div>

                  {/* Duration Selection */}
                  <div className="mb-8">
                    <label className="block text-sm font-medium text-slate-300 mb-3">
                      Duration
                    </label>
                    <div className="grid grid-cols-4 gap-3">
                      {[15, 25, 45, 60].map((mins) => (
                        <button
                          key={mins}
                          onClick={() => setDuration(mins)}
                          className={cn(
                            "py-3 px-2 rounded-xl text-sm font-medium transition-all duration-200",
                            duration === mins
                              ? "bg-indigo-600 text-white shadow-lg shadow-indigo-500/25"
                              : "bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white"
                          )}
                        >
                          {mins}m
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Media Upload */}
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Upload Notes or Images (Optional)
                    </label>
                    <input
                      type="file"
                      accept="image/*,.pdf,.txt,.md"
                      ref={fileInputRef}
                      onChange={handleFileUpload}
                      className="hidden"
                    />
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      disabled={isUploading}
                      className={cn(
                        "w-full py-3 rounded-xl font-medium flex items-center justify-center gap-2 transition-all",
                        isUploading 
                          ? "bg-slate-700 text-slate-400 cursor-not-allowed"
                          : "bg-slate-800 hover:bg-slate-700 text-slate-300"
                      )}
                    >
                      {isUploading ? (
                        <>
                          <div className="w-5 h-5 border-2 border-slate-500 border-t-slate-300 rounded-full animate-spin"></div>
                          Uploading...
                        </>
                      ) : (
                        <>
                          <Upload className="w-5 h-5" />
                          Upload Image/Notes
                        </>
                      )}
                    </button>
                    
                    {/* Uploaded Images */}
                    {uploadedImages.length > 0 && (
                      <div className="mt-3 grid grid-cols-2 gap-2">
                        {uploadedImages.map((url, idx) => (
                          <div key={idx} className="relative">
                            <img
                              src={url}
                              alt={`Uploaded note ${idx + 1}`}
                              className="w-full h-24 object-cover rounded-lg border border-slate-700"
                            />
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Start Button */}
                  <button
                    onClick={handleStart}
                    disabled={!topic.trim()}
                    className={cn(
                      "w-full py-4 rounded-xl font-semibold text-lg transition-all duration-200 flex items-center justify-center gap-2",
                      topic.trim()
                        ? "bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white shadow-xl shadow-indigo-500/25"
                        : "bg-slate-800 text-slate-500 cursor-not-allowed"
                    )}
                  >
                    <Target className="w-5 h-5" />
                    Start Focus Session
                  </button>
                </motion.div>
              </div>
            ) : (
              /* Active Session View */
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Main Timer */}
                <div className="lg:col-span-2">
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="bg-slate-900/50 border border-slate-800 rounded-3xl p-8 sm:p-12"
                  >
                    {/* Session Info */}
                    <div className="text-center mb-8">
                      <div className="inline-flex items-center gap-2 px-4 py-2 bg-slate-800/50 rounded-full border border-slate-700 mb-4">
                        <BookOpen className="w-4 h-4 text-indigo-400" />
                        <span className="text-sm text-slate-300">{session?.topic}</span>
                      </div>
                      <p className="text-slate-400 text-sm">
                        Mode: <span className={selectedMode === 'supportive' ? 'text-emerald-400' : 'text-rose-400'}>
                          {selectedMode === 'supportive' ? 'Supportive (Oliver)' : 'Challenger (Victoria)'}
                        </span>
                      </p>
                    </div>

                    {/* Timer */}
                    <StudyTimer
                      duration={timerRemaining}
                      isActive={isActive}
                      isPaused={isPaused}
                      onComplete={handleComplete}
                      onPause={pauseTimer}
                      onResume={resumeTimer}
                      onReset={() => {
                        setShowAbandonConfirm(true);
                      }}
                    />

                    {/* Abandon Button (when active) */}
                    {isActive && (
                      <div className="mt-6 text-center">
                        <button
                          onClick={() => setShowAbandonConfirm(true)}
                          className="px-6 py-2 text-rose-400 hover:text-rose-300 text-sm font-medium transition-colors"
                        >
                          Abandon Session
                        </button>
                      </div>
                    )}

                    {/* Interruptions */}
                    {interruptions > 0 && (
                      <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mt-6 text-center"
                      >
                        <p className="text-amber-400 text-sm">
                          Interruptions: {interruptions}
                        </p>
                      </motion.div>
                    )}
                  </motion.div>
                </div>

                {/* Sidebar */}
                <div className="space-y-6">
                  {/* Uploaded Notes */}
                  {uploadedImages.length > 0 && (
                    <motion.div
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.15 }}
                      className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6"
                    >
                      <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
                        <ImageIcon className="w-4 h-4 text-emerald-400" />
                        Your Notes
                      </h3>
                      <div className="space-y-2">
                        {uploadedImages.map((url, idx) => (
                          <div key={idx} className="rounded-lg overflow-hidden border border-slate-700">
                            <img src={url} alt={`Note ${idx + 1}`} className="w-full h-auto" />
                          </div>
                        ))}
                      </div>
                    </motion.div>
                  )}
                  
                  {/* Companion Card */}
                  <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6"
                  >
                    <div className="flex items-center gap-4 mb-4">
                      <div className={cn(
                        "w-16 h-16 rounded-full p-1",
                        selectedMode === 'supportive' ? "bg-emerald-500/20" : "bg-rose-500/20"
                      )}>
                        <img
                          src={companion.avatar}
                          alt={companion.name}
                          className="w-full h-full rounded-full object-cover bg-slate-800"
                        />
                      </div>
                      <div>
                        <h3 className="font-semibold text-white">{companion.name}</h3>
                        <p className={cn(
                          "text-sm",
                          selectedMode === 'supportive' ? "text-emerald-400" : "text-rose-400"
                        )}>
                          {selectedMode === 'supportive' ? 'Supportive' : 'Challenger'}
                        </p>
                      </div>
                    </div>

                    {/* Message Bubble */}
                    <AnimatePresence mode="wait">
                      {companionMessage && (
                        <motion.div
                          key={companionMessage}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -10 }}
                          className={cn(
                            "p-4 rounded-xl rounded-tl-sm text-sm",
                            selectedMode === 'supportive' 
                              ? "bg-emerald-500/10 border border-emerald-500/20 text-emerald-200"
                              : "bg-rose-500/10 border border-rose-500/20 text-rose-200"
                          )}
                        >
                          &ldquo;{companionMessage}&rdquo;
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>

                  {/* Quick Stats */}
                  <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.1 }}
                    className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6"
                  >
                    <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
                      <Zap className="w-4 h-4 text-amber-400" />
                      Quick Stats
                    </h3>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400 text-sm">Total Sessions</span>
                        <span className="text-white font-medium">12</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400 text-sm">Total Focus Time</span>
                        <span className="text-white font-medium">8h 45m</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400 text-sm">Avg. Session</span>
                        <span className="text-white font-medium">43m</span>
                      </div>
                    </div>
                  </motion.div>

                  {/* Mini Leaderboard */}
                  <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.2 }}
                    className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6"
                  >
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="font-semibold text-white flex items-center gap-2">
                        <Trophy className="w-4 h-4 text-amber-400" />
                        Top Focus Warriors
                      </h3>
                      <span className="text-xs text-slate-500">This week</span>
                    </div>
                    
                    <div className="space-y-2">
                      {[
                        { rank: 1, name: 'StudyMaster99', minutes: 1240, avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=1' },
                        { rank: 2, name: 'FocusQueen', minutes: 1085, avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=2' },
                        { rank: 3, name: 'BookWorm42', minutes: 920, avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=3' },
                      ].map((user) => (
                        <div
                          key={user.rank}
                          className={cn(
                            "flex items-center gap-3 p-2 rounded-lg",
                            user.rank === 1 && "bg-amber-500/10 border border-amber-500/20"
                          )}
                        >
                          <div className={cn(
                            "w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold",
                            user.rank === 1 ? "bg-amber-500 text-amber-950" :
                            user.rank === 2 ? "bg-slate-400 text-slate-900" :
                            "bg-amber-700 text-amber-100"
                          )}>
                            {user.rank}
                          </div>
                          <img
                            src={user.avatar}
                            alt={user.name}
                            className="w-8 h-8 rounded-full bg-slate-800"
                          />
                          <span className="flex-1 text-sm text-white font-medium">{user.name}</span>
                          <span className="text-xs text-slate-400">{Math.floor(user.minutes / 60)}h {user.minutes % 60}m</span>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                </div>
              </div>
            )}
          </>
        )}

        {/* Leaderboard Tab */}
        {activeTab === 'leaderboard' && (
          <div className="max-w-2xl mx-auto">
            <motion.div
              initial={{ opacity:0, y: 20 }}
              animate={{ opacity:1, y:0 }}
              className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 sm:p-8"
            >
              <div className="flex items-center gap-3 mb-6">
                <Trophy className="w-8 h-8 text-amber-400" />
                <h2 className="text-2xl font-bold text-white">Top Focus Warriors</h2>
              </div>
              <div className="space-y-3">
                {[
                  { rank:1, name:'StudyMaster99', minutes: 1240, avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=1' },
                  { rank:2, name:'FocusQueen', minutes: 1085, avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=2' },
                  { rank:3, name:'BookWorm42', minutes: 920, avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=3' },
                ].map((user, index) => (
                  <motion.div key={user.rank}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className={cn(
                      "flex items-center gap-4 p-4 rounded-xl",
                      user.rank === 1 && "bg-amber-500/10 border border-amber-500/20"
                    )}
                  >
                    <div className={cn(
                      "w-10 h-10 rounded-full flex items-center justify-center text-lg font-bold",
                      user.rank === 1 ? "bg-amber-500 text-amber-950" :
                      user.rank === 2 ? "bg-slate-400 text-slate-900" :
                      "bg-amber-700 text-amber-100"
                    )}>
                      {user.rank}
                    </div>
                    <img
                      src={user.avatar}
                      alt={user.name}
                      className="w-12 h-12 rounded-full bg-slate-800"
                    />
                    <div className="flex-1">
                      <p className="text-white font-semibold">{user.name}</p>
                      <p className="text-sm text-slate-400">{Math.floor(user.minutes / 60)}h {user.minutes % 60}m</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          </div>
        )}
      </div>

      {/* Abandon Confirmation Modal */}
      <AnimatePresence>
        {showAbandonConfirm && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-slate-900 border border-slate-700 rounded-2xl p-6 w-full max-w-md mx-4"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-rose-500/10 rounded-lg">
                  <AlertTriangle className="w-6 h-6 text-rose-400" />
                </div>
                <h3 className="text-xl font-bold text-white">Abandon Session?</h3>
              </div>
              
              <p className="text-slate-400 mb-6">
                {companion.name} is watching... If you leave now, you won't earn any XP for this session. Are you sure?
              </p>

              <div className="flex gap-3">
                <button
                  onClick={() => setShowAbandonConfirm(false)}
                  className="flex-1 py-3 px-4 bg-slate-800 hover:bg-slate-700 text-white rounded-xl font-medium transition-colors"
                >
                  Keep Going
                </button>
                <button
                  onClick={handleAbandon}
                  className="flex-1 py-3 px-4 bg-rose-600 hover:bg-rose-500 text-white rounded-xl font-medium transition-colors"
                >
                  Abandon
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Completion Modal */}
      <AnimatePresence>
        {showCompleteModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.9, opacity: 0, y: 20 }}
              className="bg-slate-900 border border-slate-700 rounded-3xl p-8 w-full max-w-lg mx-4 text-center relative overflow-hidden"
            >
              {/* Background glow */}
              <div className="absolute top-0 left-1/2 -translate-x-1/2 w-96 h-96 bg-emerald-500/20 rounded-full blur-[100px] -z-10" />
              
              {/* Confetti icon */}
              <motion.div
                initial={{ scale: 0, rotate: -180 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{ type: "spring", stiffness: 200, delay: 0.2 }}
                className="w-24 h-24 mx-auto mb-6 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-3xl flex items-center justify-center shadow-2xl shadow-emerald-500/30"
              >
                <Sparkles className="w-12 h-12 text-white" />
              </motion.div>

              <motion.h2
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="text-3xl font-bold text-white mb-2"
              >
                Session Complete!
              </motion.h2>

              <motion.p
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="text-slate-400 mb-8"
              >
                Great job staying focused! {companion.name} is proud of you.
              </motion.p>

              {/* Stats Grid */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className="grid grid-cols-3 gap-4 mb-8"
              >
                <div className="bg-slate-800/50 rounded-2xl p-4 border border-slate-700">
                  <div className="w-10 h-10 mx-auto mb-2 bg-emerald-500/10 rounded-xl flex items-center justify-center">
                    <Sparkles className="w-5 h-5 text-emerald-400" />
                  </div>
                  <p className="text-2xl font-bold text-white">+{earnedXP}</p>
                  <p className="text-xs text-slate-500">XP Earned</p>
                </div>

                <div className="bg-slate-800/50 rounded-2xl p-4 border border-slate-700">
                  <div className="w-10 h-10 mx-auto mb-2 bg-amber-500/10 rounded-xl flex items-center justify-center">
                    <Target className="w-5 h-5 text-amber-400" />
                  </div>
                  <p className="text-2xl font-bold text-white">{interruptions}</p>
                  <p className="text-xs text-slate-500">Interruptions</p>
                </div>

                <div className="bg-slate-800/50 rounded-2xl p-4 border border-slate-700">
                  <div className="w-10 h-10 mx-auto mb-2 bg-indigo-500/10 rounded-xl flex items-center justify-center">
                    <Clock className="w-5 h-5 text-indigo-400" />
                  </div>
                  <p className="text-2xl font-bold text-white">{session?.duration_minutes || 0}m</p>
                  <p className="text-xs text-slate-500">Focused Time</p>
                </div>
              </motion.div>

              {/* Close Button */}
              <motion.button
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 }}
                onClick={() => setShowCompleteModal(false)}
                className="w-full py-4 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white rounded-xl font-semibold transition-all duration-200 shadow-xl shadow-emerald-500/25"
              >
                Awesome! Back to Work
              </motion.button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}