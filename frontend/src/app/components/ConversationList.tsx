import { useState, useEffect } from "react";
import { motion } from "motion/react";
import { Users, MessageCircle, Plus, Settings } from "lucide-react";
import { studyBuddyService, Conversation } from "../services/studyBuddyService";
import { useStore } from "../store";
import { cn } from "../utils";
import { Button } from "./ui/button";
import { Card } from "./ui/card";

interface ConversationListProps {
  conversations: Conversation[];
  selectedConversationId: string | null;
  onSelect: (conversation: Conversation) => void;
  loading?: boolean;
}

export default function ConversationList({ 
  conversations, 
  selectedConversationId, 
  onSelect,
  loading = false
}: ConversationListProps) {
  const handleNewConversation = () => {
    // For now, this will navigate to a page to find new Study Buddies
    window.location.href = "/app/study-buddy/matches";
  };

  if (loading && conversations.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="flex items-center gap-2 text-zinc-500">
          <MessageCircle className="w-5 h-5 animate-spin" />
          Loading conversations...
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-zinc-900/50 border-r border-zinc-800">
      {/* Header */}
      <div className="p-3 sm:p-4 border-b border-zinc-800">
        <div className="flex items-center justify-between mb-3 sm:mb-4">
          <h2 className="text-base sm:text-lg font-medium flex items-center gap-2">
            <Users className="w-4 h-4 sm:w-5 sm:h-5" />
            Conversations
          </h2>
          <Button onClick={handleNewConversation} variant="ghost" size="sm" className="gap-1 sm:gap-2 h-8 sm:h-9 text-xs sm:text-sm">
            <Plus className="w-3 h-3 sm:w-4 sm:h-4" />
            New
          </Button>
        </div>

        {/* Search */}
        <div className="relative">
          <input
            type="text"
            placeholder="Search..."
            className="w-full px-3 py-1.5 sm:px-4 sm:py-2 pl-9 sm:pl-10 bg-zinc-800 border border-zinc-700 rounded-lg text-xs sm:text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-500"
          />
          <MessageCircle className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
        </div>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {conversations.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full p-6 sm:p-8 text-center">
            <Users className="w-10 h-10 sm:w-12 sm:h-12 mb-2 sm:mb-3 text-zinc-600" />
            <h3 className="text-xs sm:text-sm font-medium text-zinc-400 mb-1">No conversations</h3>
            <p className="text-[10px] sm:text-xs text-zinc-500 mb-3 sm:mb-4">
              Start connecting with buddies!
            </p>
            <Button
              onClick={handleNewConversation}
              variant="outline"
              size="sm"
              className="gap-2 text-xs"
            >
              <Plus className="w-4 h-4" />
              Find Buddies
            </Button>
          </div>
        ) : (
          <div className="divide-y divide-zinc-800">
            {conversations.map((conversation) => (
              <motion.div
                key={conversation.conversation_id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className={cn(
                  "p-3 sm:p-4 hover:bg-zinc-800/50 cursor-pointer transition-colors",
                  selectedConversationId === conversation.conversation_id && "bg-zinc-800/80"
                )}
                onClick={() => onSelect(conversation)}
              >
                <div className="flex items-start gap-2 sm:gap-3">
                  {/* Avatar */}
                  <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-purple-600/20 flex items-center justify-center flex-shrink-0">
                    <Users className="w-4 h-4 sm:w-5 sm:h-5 text-purple-400" />
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-0.5 sm:mb-1">
                      <h3 className="font-medium text-xs sm:text-sm truncate">
                        {conversation.other_user_name}
                      </h3>
                      <span className="text-[10px] sm:text-xs text-zinc-500 flex-shrink-0 ml-2">
                        {new Date(conversation.updated_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                      </span>
                    </div>
                    <p className="text-[10px] sm:text-xs text-zinc-500 truncate">
                      {conversation.other_user_email}
                    </p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
