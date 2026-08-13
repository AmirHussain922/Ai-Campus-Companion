import { useState, useEffect } from "react";
import { motion } from "motion/react";
import { useParams, useNavigate } from "react-router";
import { Users, MessageCircle, Settings, Plus } from "lucide-react";
import { studyBuddyService, Conversation } from "../services/studyBuddyService";
import { useStore } from "../store";
import { cn } from "../utils";
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import ConversationList from "../components/ConversationList";
import MessageChat from "../components/MessageChat";

export default function StudyBuddyDM() {
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const user = useStore(state => state.user);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user) {
      setError("Please log in to access DMs");
      return;
    }
    loadConversations();
  }, [user]);

  // Handle URL parameter selection
  useEffect(() => {
    if (conversationId && conversations.length > 0) {
      const found = conversations.find(c => c.conversation_id === conversationId);
      if (found) {
        setSelectedConversation(found);
      }
    }
  }, [conversationId, conversations]);

  const loadConversations = async () => {
    try {
      setLoading(true);
      setError("");
      const data = await studyBuddyService.getConversations();
      setConversations(data.conversations);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load conversations");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectConversation = (conversation: Conversation) => {
    setSelectedConversation(conversation);
    navigate(`/app/study-buddy/dm/${conversation.conversation_id}`);
  };

  const handleNewConversation = () => {
    // Navigate to matches page
    window.location.href = "/app/study-buddy/matches";
  };

  if (loading && conversations.length === 0) {
    return (
      <div className="flex items-center justify-center h-full bg-zinc-950">
        <div className="flex items-center gap-2 text-zinc-500">
          <MessageCircle className="w-5 h-5 animate-spin" />
          Loading DM system...
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-zinc-950">
      {/* Header */}
      <div className="p-3 sm:p-4 border-b border-zinc-800 bg-zinc-900/50">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 sm:gap-3 min-w-0">
            <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-purple-600/20 flex items-center justify-center flex-shrink-0">
              <Users className="w-4 h-4 sm:w-5 sm:h-5 text-purple-400" />
            </div>
            <div className="min-w-0">
              <h1 className="text-base sm:text-lg font-semibold truncate">Study Buddy DM</h1>
              <p className="text-[10px] sm:text-xs text-zinc-500 truncate">Real-time messaging</p>
            </div>
          </div>
          <Button onClick={handleNewConversation} variant="outline" size="sm" className="gap-1 sm:gap-2 text-xs sm:text-sm h-8 sm:h-9 flex-shrink-0">
            <Plus className="w-3 h-3 sm:w-4 sm:h-4" />
            <span className="hidden xs:inline">New Conversation</span>
            <span className="xs:hidden">New</span>
          </Button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-2 sm:p-3 bg-red-900/20 border-b border-red-800 text-[10px] sm:text-xs text-red-400"
        >
          {error}
        </motion.div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Conversation List (Left Panel) */}
        <div className={cn(
          "w-full md:w-80 border-r border-zinc-800 flex-shrink-0 transition-all duration-300",
          selectedConversation && "hidden md:flex"
        )}>
          <ConversationList
            conversations={conversations}
            selectedConversationId={selectedConversation?.conversation_id || null}
            onSelect={handleSelectConversation}
          />
        </div>

        {/* Message Chat (Right Panel) */}
        <div className={cn(
          "flex-1 flex flex-col bg-zinc-950 transition-all duration-300",
          !selectedConversation && "hidden md:flex"
        )}>
          {selectedConversation ? (
            <MessageChat
              conversation={selectedConversation}
              onBack={() => setSelectedConversation(null)}
            />
          ) : (
            <div className="flex-1 flex items-center justify-center bg-zinc-950 p-4">
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="text-center max-w-md"
              >
                <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-full bg-zinc-800 flex items-center justify-center mx-auto mb-3 sm:mb-4">
                  <MessageCircle className="w-8 h-8 sm:w-10 sm:h-10 text-zinc-600" />
                </div>
                <h2 className="text-lg sm:text-xl font-medium mb-1 sm:mb-2 text-zinc-200">
                  Select a conversation
                </h2>
                <p className="text-xs sm:text-sm text-zinc-500 mb-4 sm:mb-6">
                  Choose a conversation to start messaging
                </p>
                <Button
                  onClick={handleNewConversation}
                  variant="outline"
                  size="sm"
                  className="gap-2 sm:text-base sm:h-11 px-4 sm:px-6"
                >
                  <Plus className="w-4 h-4" />
                  Find Study Buddies
                </Button>
              </motion.div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
