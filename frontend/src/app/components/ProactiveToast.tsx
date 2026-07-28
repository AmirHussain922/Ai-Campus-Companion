import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router";
import { motion, AnimatePresence } from "framer-motion";
import { X, Mail, Clock, Trophy, BookOpen, Check } from "lucide-react";
import { useStore } from "../store";
import { useProactiveStore, ProactiveMessage } from "../stores/useProactiveStore";
import { companionColorClasses, cn } from "../utils";

interface ToastMessage {
  id: string;
  message: ProactiveMessage;
  companionName: string;
  companionColor: string;
}

export default function ProactiveToast() {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const [lastCheckTime, setLastCheckTime] = useState<number>(Date.now());
  const navigate = useNavigate();

  const authToken = useStore((state) => state.authToken);
  const companions = useStore((state) => state.companions);
  const { unreadMessages, getNewMessagesSince, fetchUnread, markAsRead } = useProactiveStore();

  // Check for new messages on mount and when unreadMessages changes
  useEffect(() => {
    if (!authToken) return;

    const checkForNewMessages = () => {
      const newMessages = getNewMessagesSince(lastCheckTime);

      if (newMessages.length > 0) {
        const newToasts: ToastMessage[] = newMessages.map((message) => {
          const companion = companions.find((c) => c.id === message.companion_id);
          return {
            id: `toast-${message.id}-${Date.now()}`,
            message,
            companionName: companion?.name || "Companion",
            companionColor: companion?.color || "blue",
          };
        });

        setToasts((prev) => [...prev, ...newToasts]);
      }

      setLastCheckTime(Date.now());
    };

    // Check immediately
    checkForNewMessages();

    // Also set up interval to check periodically
    const interval = setInterval(checkForNewMessages, 30000); // Check every 30 seconds

    return () => clearInterval(interval);
  }, [authToken, companions, getNewMessagesSince, lastCheckTime, unreadMessages]);

  // Remove toast after auto-dismiss
  useEffect(() => {
    if (toasts.length === 0) return;

    const timers = toasts.map((toast) =>
      setTimeout(() => {
        removeToast(toast.id);
      }, 5000)
    );

    return () => {
      timers.forEach(clearTimeout);
    };
  }, [toasts]);

  const removeToast = (toastId: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== toastId));
  };

  const handleToastClick = async (toast: ToastMessage) => {
    // Mark as read
    if (authToken && !toast.message.is_read) {
      await markAsRead(toast.message.id, authToken);
    }

    // Navigate to chat
    navigate(`/app/chat/${toast.message.companion_id}`);

    // Remove toast
    removeToast(toast.id);
  };

  const getTriggerIcon = (triggerType: string) => {
    switch (triggerType) {
      case "good_morning":
        return <Clock className="w-3 h-3" />;
      case "miss_you":
        return <Mail className="w-3 h-3" />;
      case "milestone_congrats":
        return <Trophy className="w-3 h-3" />;
      case "quest_reminder":
        return <Check className="w-3 h-3" />;
      case "story_nudge":
        return <BookOpen className="w-3 h-3" />;
      default:
        return <Mail className="w-3 h-3" />;
    }
  };

  const getTriggerLabel = (triggerType: string) => {
    switch (triggerType) {
      case "good_morning":
        return "Good Morning";
      case "miss_you":
        return "Miss You";
      case "milestone_congrats":
        return "Milestone";
      case "quest_reminder":
        return "Quest";
      case "story_nudge":
        return "Story";
      default:
        return "Message";
    }
  };

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      <AnimatePresence>
        {toasts.map((toast) => (
          <motion.div
            key={toast.id}
            initial={{ opacity: 0, x: 100, scale: 0.9 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 100, scale: 0.9 }}
            onClick={() => handleToastClick(toast)}
            className={cn(
              "w-80 p-4 rounded-xl shadow-2xl cursor-pointer border-l-4",
              "bg-slate-800 border-slate-600 hover:bg-slate-750 transition-colors"
            )}
            style={{
              borderLeftColor:
                companionColorClasses[toast.companionColor as keyof typeof companionColorClasses]?.border.replace('border-', '') || '#60a5fa',
            }}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <div
                  className={cn(
                    "w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold shrink-0",
                    companionColorClasses[toast.companionColor as keyof typeof companionColorClasses]?.bg,
                    companionColorClasses[toast.companionColor as keyof typeof companionColorClasses]?.text
                  )}
                >
                  {toast.companionName.charAt(0)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="font-medium text-white text-sm truncate">
                      {toast.companionName}
                    </span>
                    <span className="text-xs text-slate-500 flex items-center gap-0.5">
                      {getTriggerIcon(toast.message.trigger_type)}
                      {getTriggerLabel(toast.message.trigger_type)}
                    </span>
                  </div>
                  <p className="text-slate-400 text-xs line-clamp-2 mt-0.5">
                    {toast.message.content}
                  </p>
                </div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  removeToast(toast.id);
                }}
                className="p-1 hover:bg-slate-700 rounded transition-colors shrink-0"
              >
                <X className="w-4 h-4 text-slate-500" />
              </button>
            </div>
            
            {/* Progress bar for auto-dismiss */}
            <div className="mt-3 h-0.5 bg-slate-700 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: "100%" }}
                animate={{ width: "0%" }}
                transition={{ duration: 5, ease: "linear" }}
                className="h-full bg-blue-500"
              />
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}