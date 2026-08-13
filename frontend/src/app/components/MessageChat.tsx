import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Send, Check, CheckCheck, ArrowLeft, MoreHorizontal, User, MessageCircle } from "lucide-react";
import { studyBuddyService, Message, Conversation } from "../services/studyBuddyService";
import { useStudyBuddyWebSocket, Message as WSMessage } from "../hooks/useStudyBuddyWebSocket";
import { cn } from "../utils";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Card } from "./ui/card";

interface MessageChatProps {
  conversation: Conversation;
  onBack: () => void;
}

export default function MessageChat({ conversation, onBack }: MessageChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Load initial messages
  useEffect(() => {
    loadMessages();
  }, [conversation.conversation_id, page]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load more messages when scrolling to top
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const target = e.target as HTMLDivElement;
    if (target.scrollTop === 0 && hasMore && !loading) {
      setPage(prev => prev + 1);
    }
  }, [loading, hasMore]);

  const loadMessages = async () => {
    try {
      setLoading(true);
      setError("");
      const data = await studyBuddyService.getMessages(
        conversation.conversation_id,
        page,
        50
      );
      setMessages(data.messages);
      setHasMore(data.meta.has_next);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load messages");
    } finally {
      setLoading(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // WebSocket for real-time messages
  const { sendMessage: wsSendMessage, isConnected } = useStudyBuddyWebSocket({
    conversationId: conversation.conversation_id,
    onMessage: (message) => {
      setMessages(prev => [...prev, message]);
    },
    onConnected: () => {
      console.log("WebSocket connected");
    },
    onDisconnected: () => {
      console.log("WebSocket disconnected");
    },
  });

  const handleSendMessage = async () => {
    if (!input.trim() || sending) return;

    try {
      setSending(true);
      setError("");

      // Try WebSocket first (real-time)
      const sentViaWS = wsSendMessage(input.trim());

      if (!sentViaWS) {
        // Fallback to REST if WebSocket fails
        await studyBuddyService.sendMessage(conversation.conversation_id, input.trim());
      }

      setInput("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send message");
    } finally {
      setSending(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));

    if (hours < 1) {
      return "Just now";
    } else if (hours < 24) {
      return `${hours}h ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const isOwnMessage = (message: Message) => {
    return message.sender_id !== conversation.other_user_id;
  };

  if (loading && messages.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="flex items-center gap-2 text-zinc-500">
          <MessageCircle className="w-5 h-5 animate-spin" />
          Loading messages...
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-zinc-950">
      {/* Header */}
      <div className="p-2 sm:p-4 border-b border-zinc-800 bg-zinc-900/50">
        <div className="flex items-center gap-2 sm:gap-3">
          <Button onClick={onBack} variant="ghost" size="icon" className="h-8 w-8 sm:h-10 sm:w-10 text-zinc-400 hover:text-white">
            <ArrowLeft className="w-4 h-4 sm:w-5 sm:h-5" />
          </Button>
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <div className="w-7 h-7 sm:w-9 sm:h-9 rounded-full bg-purple-600/20 flex items-center justify-center flex-shrink-0">
              <User className="w-4 h-4 sm:w-5 sm:h-5 text-purple-400" />
            </div>
            <div className="min-w-0">
              <h3 className="font-medium text-xs sm:text-sm truncate">{conversation.other_user_name}</h3>
              <p className="text-[10px] sm:text-xs text-zinc-500 truncate">{conversation.other_user_email}</p>
            </div>
          </div>
          <Button variant="ghost" size="icon" className="h-8 w-8 sm:h-10 sm:w-10 text-zinc-400 hover:text-white">
            <MoreHorizontal className="w-4 h-4 sm:w-5 sm:h-5" />
          </Button>
        </div>
      </div>

      {/* Messages */}
      <div
        className="flex-1 overflow-y-auto p-3 sm:p-4 space-y-3 sm:space-y-4 custom-scrollbar"
        onScroll={handleScroll}
      >
        <AnimatePresence>
          {messages.map((message, index) => {
            const own = isOwnMessage(message);
            return (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className={`flex ${own ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={cn(
                    "max-w-[85%] sm:max-w-[80%] rounded-2xl px-3 py-1.5 sm:px-4 sm:py-2",
                    own ? "bg-purple-600 text-zinc-950" : "bg-zinc-800 text-zinc-100"
                  )}
                >
                  <p className="text-xs sm:text-sm whitespace-pre-wrap break-words leading-relaxed">{message.content}</p>
                  <div className="flex items-center gap-1.5 sm:gap-2 mt-0.5 sm:mt-1">
                    <span className="text-[10px] sm:text-xs opacity-70">
                      {formatDate(message.created_at)}
                    </span>
                    {own && (
                      <span className="text-[10px] sm:text-xs opacity-70">
                        {message.is_read ? <CheckCheck className="w-2.5 h-2.5 sm:w-3 sm:h-3 inline" /> : <Check className="w-2.5 h-2.5 sm:w-3 sm:h-3 inline" />}
                      </span>
                    )}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>

        {loading && page > 1 && (
          <div className="flex justify-center">
            <MessageCircle className="w-4 h-4 sm:w-5 sm:h-5 text-zinc-500 animate-spin" />
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-3 sm:p-4 border-t border-zinc-800 bg-zinc-900/50">
        <div className="flex items-center gap-2">
          <Input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Message..."
            disabled={sending}
            className="flex-1 h-8 sm:h-9 text-xs sm:text-sm px-3"
          />
          <Button
            onClick={handleSendMessage}
            disabled={!input.trim() || sending}
            size="icon"
            className="h-8 w-8 sm:h-9 sm:w-9 bg-purple-600 hover:bg-purple-700 flex-shrink-0"
          >
            <Send className="w-4 h-4 sm:w-5 sm:h-5" />
          </Button>
        </div>

        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-2 text-xs text-red-400"
          >
            {error}
          </motion.div>
        )}

        {!isConnected && (
          <div className="mt-2 text-xs text-yellow-500">
            ⚠️ Not connected to real-time messaging. Messages will be sent when reconnected.
          </div>
        )}
      </div>
    </div>
  );
}
