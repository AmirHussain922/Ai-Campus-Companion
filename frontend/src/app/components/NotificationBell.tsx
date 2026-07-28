import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router";
import { Bell, Check, Mail, Clock, Trophy, BookOpen, X } from "lucide-react";
import { useStore } from "../store";
import { useProactiveStore, UnreadByCompanion } from "../stores/useProactiveStore";
import { cn, companionColorClasses } from "../utils";

export default function NotificationBell() {
  const [isOpen, setIsOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  
  const authToken = useStore(state => state.authToken);
  const companions = useStore(state => state.companions);
  
  const { 
    unreadMessages, 
    unreadCount, 
    isLoading, 
    fetchUnread, 
    markAsRead,
    markAllForCompanionAsRead,
    pollUnread,
  } = useProactiveStore();

  // Check if mobile on mount and resize
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Initial fetch and polling
  useEffect(() => {
    if (authToken) {
      fetchUnread(authToken);
      
      // Poll every 5 minutes
      const pollInterval = setInterval(() => {
        pollUnread(authToken);
      }, 5 * 60 * 1000);
      
      return () => clearInterval(pollInterval);
    }
  }, [authToken, fetchUnread, pollUnread]);

  const handleMarkAsRead = async (messageId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (authToken) {
      await markAsRead(messageId, authToken);
    }
  };

  const handleMarkAllAsRead = async (companionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (authToken) {
      await markAllForCompanionAsRead(companionId, authToken);
    }
  };

  const handleMessageClick = async (message: any, companionId: string) => {
    // Mark as read
    if (authToken && !message.is_read) {
      await markAsRead(message.id, authToken);
    }
    
    // Navigate to chat
    navigate(`/app/chat/${companionId}`);
    setIsOpen(false);
  };

  const getTriggerIcon = (triggerType: string) => {
    switch (triggerType) {
      case 'good_morning':
        return <Clock className="w-3 h-3" />;
      case 'miss_you':
        return <Mail className="w-3 h-3" />;
      case 'milestone_congrats':
        return <Trophy className="w-3 h-3" />;
      case 'quest_reminder':
        return <Check className="w-3 h-3" />;
      case 'story_nudge':
        return <BookOpen className="w-3 h-3" />;
      default:
        return <Mail className="w-3 h-3" />;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  // Mobile slide-up modal
  if (isMobile && isOpen) {
    return (
      <>
        {/* Backdrop */}
        <div 
          className="fixed inset-0 bg-black/60 z-50"
          onClick={() => setIsOpen(false)}
        />
        {/* Slide-up panel */}
        <div className="fixed bottom-0 left-0 right-0 bg-slate-900 border-t border-slate-700 rounded-t-2xl z-50 max-h-[80vh] overflow-hidden">
          <div className="p-4 border-b border-slate-700 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bell className="w-5 h-5 text-slate-400" />
              <h3 className="font-semibold text-white">Notifications</h3>
              {unreadCount > 0 && (
                <span className="bg-red-500 text-white text-xs font-medium px-2 py-0.5 rounded-full">
                  {unreadCount}
                </span>
              )}
            </div>
            <button 
              onClick={() => setIsOpen(false)}
              className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-slate-400" />
            </button>
          </div>
          
          <div className="overflow-y-auto max-h-[60vh] p-4 space-y-4">
            {isLoading ? (
              <div className="text-center py-8">
                <div className="w-6 h-6 border-2 border-slate-600 border-t-slate-300 rounded-full animate-spin mx-auto mb-2" />
                <p className="text-slate-500 text-sm">Loading...</p>
              </div>
            ) : unreadMessages.length === 0 ? (
              <div className="text-center py-8">
                <Bell className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                <p className="text-slate-400">No new notifications</p>
              </div>
            ) : (
              unreadMessages.map((group) => (
                <div key={group.companion_id} className="bg-slate-800/50 rounded-xl p-3">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div className={cn(
                        "w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold",
                        companionColorClasses[group.companion_id === 'c1' ? 'blue' : 
                          group.companion_id === 'c2' ? 'pink' : 
                          group.companion_id === 'c3' ? 'purple' : 
                          group.companion_id === 'c4' ? 'red' : 'cyan'].bg,
                        companionColorClasses[group.companion_id === 'c1' ? 'blue' : 
                          group.companion_id === 'c2' ? 'pink' : 
                          group.companion_id === 'c3' ? 'purple' : 
                          group.companion_id === 'c4' ? 'red' : 'cyan'].text
                      )}>
                        {group.companion_name.charAt(0)}
                      </div>
                      <span className="font-medium text-white">{group.companion_name}</span>
                    </div>
                    <button
                      onClick={(e) => handleMarkAllAsRead(group.companion_id, e)}
                      className="text-xs text-slate-400 hover:text-white px-2 py-1 rounded hover:bg-slate-700"
                    >
                      Mark all
                    </button>
                  </div>
                  <div className="space-y-2">
                    {group.messages.map((message) => (
                      <button
                        key={message.id}
                        onClick={() => handleMessageClick(message, group.companion_id)}
                        className="w-full text-left p-3 rounded-lg bg-slate-700/50 hover:bg-slate-700 transition-colors"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <p className="text-sm text-slate-200 line-clamp-2 flex-1">{message.content}</p>
                          <span className="text-xs text-slate-500 shrink-0">
                            {formatTimestamp(message.sent_at)}
                          </span>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </>
    );
  }

  // Desktop dropdown
  return (
    <div ref={dropdownRef} className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "relative p-2 rounded-lg transition-colors",
          isOpen ? "bg-slate-800 text-white" : "text-slate-400 hover:text-white hover:bg-slate-800/50"
        )}
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full mt-2 w-96 bg-slate-800 border border-slate-700 rounded-xl shadow-xl z-50 overflow-hidden">
          <div className="p-3 border-b border-slate-700 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bell className="w-4 h-4 text-slate-400" />
              <h3 className="font-semibold text-white text-sm">Notifications</h3>
              {unreadCount > 0 && (
                <span className="bg-red-500 text-white text-xs font-medium px-1.5 py-0.5 rounded-full">
                  {unreadCount}
                </span>
              )}
            </div>
          </div>
          
          <div className="max-h-96 overflow-y-auto">
            {isLoading ? (
              <div className="text-center py-8">
                <div className="w-6 h-6 border-2 border-slate-600 border-t-slate-300 rounded-full animate-spin mx-auto mb-2" />
                <p className="text-slate-500 text-sm">Loading...</p>
              </div>
            ) : unreadMessages.length === 0 ? (
              <div className="text-center py-8">
                <Bell className="w-10 h-10 text-slate-600 mx-auto mb-2" />
                <p className="text-slate-400 text-sm">No new notifications</p>
              </div>
            ) : (
              <div className="divide-y divide-slate-700/50">
                {unreadMessages.map((group) => (
                  <div key={group.companion_id} className="p-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className={cn(
                          "w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold",
                          companionColorClasses[group.companion_id === 'c1' ? 'blue' : 
                            group.companion_id === 'c2' ? 'pink' : 
                            group.companion_id === 'c3' ? 'purple' : 
                            group.companion_id === 'c4' ? 'red' : 'cyan'].bg,
                          companionColorClasses[group.companion_id === 'c1' ? 'blue' : 
                            group.companion_id === 'c2' ? 'pink' : 
                            group.companion_id === 'c3' ? 'purple' : 
                            group.companion_id === 'c4' ? 'red' : 'cyan'].text
                        )}>
                          {group.companion_name.charAt(0)}
                        </div>
                        <span className="font-medium text-white text-sm">{group.companion_name}</span>
                        <span className="text-xs text-slate-500">({group.unread_count})</span>
                      </div>
                      <button
                        onClick={(e) => handleMarkAllAsRead(group.companion_id, e)}
                        className="text-xs text-slate-400 hover:text-white px-2 py-0.5 rounded hover:bg-slate-700 transition-colors"
                      >
                        Mark all
                      </button>
                    </div>
                    <div className="space-y-1.5">
                      {group.messages.slice(0, 3).map((message) => (
                        <button
                          key={message.id}
                          onClick={() => handleMessageClick(message, group.companion_id)}
                          className="w-full text-left p-2 rounded-lg bg-slate-700/30 hover:bg-slate-700/50 transition-colors group"
                        >
                          <div className="flex items-start gap-2">
                            <span className="text-slate-400 mt-0.5">{getTriggerIcon(message.trigger_type)}</span>
                            <p className="text-sm text-slate-200 line-clamp-2 flex-1 group-hover:text-white transition-colors">
                              {message.content}
                            </p>
                            <span className="text-xs text-slate-500 shrink-0">
                              {formatTimestamp(message.sent_at)}
                            </span>
                          </div>
                        </button>
                      ))}
                      {group.messages.length > 3 && (
                        <button
                          onClick={() => navigate(`/app/chat/${group.companion_id}`)}
                          className="w-full text-center py-1.5 text-xs text-slate-400 hover:text-white transition-colors"
                        >
                          +{group.messages.length - 3} more messages
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}