import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Send, LogOut, Users, User, MoreHorizontal, Power, Volume2 } from "lucide-react";
import { studyRoomService, StudyRoom } from "../services/studyRoomService";
import { useStudyRoomWebSocket, RoomMessage } from "../hooks/useStudyRoomWebSocket";
import { cn } from "../utils";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Card } from "./ui/card";
import { useStore } from "../store";

interface StudyRoomChatProps {
  room: StudyRoom;
  onBack: () => void;
}

export default function StudyRoomChat({ room, onBack }: StudyRoomChatProps) {
  const user = useStore(state => state.user);
  const [messages, setMessages] = useState<RoomMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [hasMore, setHasMore] = useState(true);
  const [page, setPage] = useState(1);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Load initial messages
  useEffect(() => {
    loadMessages();
  }, [room.id, page]);

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
  }, [hasMore, loading]);

  const loadMessages = async () => {
    try {
      setLoading(true);
      setError("");
      const data = await studyRoomService.getRoomMessages(room.id, page, 50);
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
  const { sendMessage: wsSendMessage, isConnected } = useStudyRoomWebSocket({
    roomId: room.id,
    onMessage: (message) => {
      setMessages(prev => [...prev, message]);
    },
    onConnected: () => {
      console.log("WebSocket connected");
    },
    onDisconnected: () => {
      console.log("WebSocket disconnected");
    },
    onRoomEnded: () => {
      // Reload rooms to update status
      onBack();
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
        await studyRoomService.sendRoomMessage(room.id, input.trim());
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

  const handleLeaveRoom = async () => {
    if (confirm("Are you sure you want to leave this study room?")) {
      await studyRoomService.leaveRoom(room.id);
      onBack();
    }
  };

  const handleEndRoom = async () => {
    if (confirm("Are you sure you want to end this study room? All participants will be disconnected.")) {
      await studyRoomService.endRoom(room.id);
      onBack();
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

  const isOwnMessage = (message: RoomMessage) => {
    return message.sender_id === room.host_id;
  };

  if (loading && messages.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="flex items-center gap-2 text-zinc-500">
          <Users className="w-5 h-5 animate-spin" />
          Loading room...
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-zinc-950">
      {/* Header */}
      <div className="p-4 border-b border-zinc-800 bg-zinc-900/50">
        <div className="flex items-center gap-3">
          <Button onClick={onBack} variant="ghost" size="icon" className="text-zinc-400 hover:text-white">
            <Users className="w-5 h-5" />
          </Button>
          <div className="flex-1 min-w-0">
            <h3 className="font-medium text-sm truncate">{room.title}</h3>
            <p className="text-xs text-zinc-500 truncate">
              {room.subject} • {room.major}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1 text-xs text-zinc-500 mr-2">
              <Users className="w-3 h-3" />
              <span>{room.participant_count} / {room.max_participants}</span>
            </div>
            {user?.id === room.host_id ? (
              <Button
                onClick={handleEndRoom}
                variant="ghost"
                size="icon"
                className="text-zinc-400 hover:text-red-400"
                title="End Room"
              >
                <Power className="w-5 h-5" />
              </Button>
            ) : (
              <Button
                onClick={handleLeaveRoom}
                variant="ghost"
                size="icon"
                className="text-zinc-400 hover:text-white"
                title="Leave Room"
              >
                <LogOut className="w-5 h-5" />
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Messages */}
      <div
        className="flex-1 overflow-y-auto p-4 space-y-4"
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
                    "max-w-[80%] rounded-2xl px-4 py-2",
                    own ? "bg-blue-600 text-zinc-950" : "bg-zinc-800 text-zinc-100"
                  )}
                >
                  <p className="text-sm whitespace-pre-wrap break-words">{message.content}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs opacity-70">
                      {formatDate(message.created_at)}
                    </span>
                    {own && (
                      <span className="text-xs opacity-70">
                        {message.is_read ? "✓✓" : "✓"}
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
            <Users className="w-5 h-5 text-zinc-500 animate-spin" />
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-zinc-800 bg-zinc-900/50">
        <div className="flex items-center gap-2">
          <Input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type a message..."
            disabled={sending || !isConnected}
            className="flex-1"
          />
          <Button
            onClick={handleSendMessage}
            disabled={!input.trim() || sending || !isConnected}
            size="icon"
            className="bg-blue-600 hover:bg-blue-700"
          >
            <Send className="w-5 h-5" />
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
