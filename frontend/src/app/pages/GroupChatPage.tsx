import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Users, Send, Loader2, MoreHorizontal, Smile } from 'lucide-react';
import { useStore } from '../store';
import { useGroupChatStore } from '../stores/useGroupChatStore';
import { GroupChatMessage } from '../components/GroupChatMessage';
import { cn } from '../utils';

// Companion data for the header
const campusCompanions = [
  { id: '1', name: 'Julian', color: 'purple', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Julian' },
  { id: '2', name: 'Victoria', color: 'red', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Victoria' },
  { id: '3', name: 'Oliver', color: 'emerald', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Oliver' },
  { id: '4', name: 'Chloe', color: 'pink', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Chloe' },
  { id: '5', name: 'Toby', color: 'amber', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Toby' },
];

export default function GroupChatPage() {
  const authToken = useStore(state => state.authToken);
  const currentUser = useStore(state => state.user);
  const {
    messages,
    isLoading,
    isSending,
    isTyping,
    typingCompanions,
    fetchMessages,
    sendMessage,
    receiveMessage,
    markAsRead
  } = useGroupChatStore();

  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Fetch messages on mount
  useEffect(() => {
    fetchMessages(50, undefined, authToken);
    markAsRead();
  }, [authToken, fetchMessages, markAsRead]);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSend = async () => {
    if (!inputValue.trim() || isSending) return;

    const success = await sendMessage(inputValue.trim(), undefined, authToken);
    if (success) {
      setInputValue('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const isCurrentUserMessage = (senderId: string) => {
    return senderId === currentUser?.id;
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col">
      {/* Header */}
      <div className="sticky top-0 z-20 bg-slate-950/80 backdrop-blur-xl border-b border-slate-800">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-indigo-500/10 rounded-xl border border-indigo-500/20">
                <Users className="w-6 h-6 text-indigo-400" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">Campus Lounge</h1>
                <p className="text-sm text-slate-400">Chat with all companions</p>
              </div>
            </div>

            {/* Companion Avatars */}
            <div className="flex items-center gap-2">
              <div className="flex -space-x-2">
                {campusCompanions.map((companion, i) => (
                  <motion.div
                    key={companion.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className={cn(
                      "w-8 h-8 rounded-full ring-2 ring-slate-950 overflow-hidden",
                      "hover:ring-indigo-500/50 transition-all cursor-pointer hover:scale-110"
                    )}
                    title={companion.name}
                  >
                    <img 
                      src={companion.avatar} 
                      alt={companion.name}
                      className="w-full h-full object-cover"
                    />
                  </motion.div>
                ))}
              </div>
              <div className="ml-2 px-2 py-1 bg-emerald-500/10 rounded-full border border-emerald-500/20">
                <span className="text-xs font-medium text-emerald-400">5 online</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full" />
            </div>
          ) : messages.length === 0 ? (
            <div className="text-center py-16">
              <Users className="w-16 h-16 text-slate-700 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">Welcome to Campus Lounge!</h3>
              <p className="text-slate-400 max-w-md mx-auto">
                Start a conversation with all your companions. Share your thoughts, ask questions, or just hang out!
              </p>
            </div>
          ) : (
            <div className="space-y-1">
              {messages.map((message, index) => {
                const isCurrentUser = isCurrentUserMessage(message.sender_id);
                const showAvatar = index === 0 || messages[index - 1].sender_id !== message.sender_id;

                return (
                  <GroupChatMessage
                    key={message.id}
                    message={message}
                    isCurrentUser={isCurrentUser}
                    showAvatar={showAvatar}
                  />
                );
              })}
              
              {/* Typing indicators */}
              {isTyping && typingCompanions.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center gap-2 ml-12 mb-4"
                >
                  <div className="flex gap-1 p-3 bg-slate-800 rounded-2xl rounded-tl-sm">
                    <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                  <span className="text-xs text-slate-500">
                    {typingCompanions.join(', ')} {typingCompanions.length === 1 ? 'is' : 'are'} typing...
                  </span>
                </motion.div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>

      {/* Input */}
      <div className="sticky bottom-0 z-20 bg-slate-950/80 backdrop-blur-xl border-t border-slate-800">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4">
          <div className="flex items-center gap-3">
            <button className="p-2.5 text-slate-500 hover:text-slate-300 hover:bg-slate-800 rounded-xl transition-colors">
              <MoreHorizontal className="w-5 h-5" />
            </button>
            
            <div className="flex-1 relative">
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type a message..."
                disabled={isSending}
                className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all disabled:opacity-50"
              />
            </div>
            
            <button className="p-2.5 text-slate-500 hover:text-slate-300 hover:bg-slate-800 rounded-xl transition-colors">
              <Smile className="w-5 h-5" />
            </button>
            
            <button
              onClick={handleSend}
              disabled={!inputValue.trim() || isSending}
              className={cn(
                "p-3 rounded-xl transition-all duration-200",
                inputValue.trim() && !isSending
                  ? "bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/25"
                  : "bg-slate-800 text-slate-500 cursor-not-allowed"
              )}
            >
              {isSending ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
