import { motion } from 'framer-motion';
import { cn } from '../utils';
import type { GroupChatMessage as GroupChatMessageType } from '../stores/useGroupChatStore';

interface GroupChatMessageProps {
  message: GroupChatMessageType;
  isCurrentUser: boolean;
  showAvatar?: boolean;
}

const companionColors: Record<string, { bg: string; text: string; ring: string; bubble: string}> = {
  purple: {
    bg: 'bg-violet-500',
    text: 'text-violet-400',
    ring: 'ring-violet-500/50',
    bubble: 'bg-slate-700 border-slate-600'
  },
  red: {
    bg: 'bg-rose-500',
    text: 'text-rose-400',
    ring: 'ring-rose-500/50',
    bubble: 'bg-slate-700 border-slate-600'
  },
  emerald: {
    bg: 'bg-emerald-500',
    text: 'text-emerald-400',
    ring: 'ring-emerald-500/50',
    bubble: 'bg-slate-700 border-slate-600'
  },
  pink: {
    bg: 'bg-pink-500',
    text: 'text-pink-400',
    ring: 'ring-pink-500/50',
    bubble: 'bg-slate-700 border-slate-600'
  },
  amber: {
    bg: 'bg-amber-500',
    text: 'text-amber-400',
    ring: 'ring-amber-500/50',
    bubble: 'bg-slate-700 border-slate-600'
  },
  zinc: {
    bg: 'bg-zinc-500',
    text: 'text-zinc-400',
    ring: 'ring-zinc-500/50',
    bubble: 'bg-slate-700 border-slate-600'
  }
};

export function GroupChatMessage({ message, isCurrentUser, showAvatar = true }: GroupChatMessageProps) {
  const colors = companionColors[message.sender_color] || companionColors.purple;
  const initial = message.sender_name.charAt(0).toUpperCase();
  const timestamp = new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  if (isCurrentUser) {
    return (
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        className="flex justify-end mb-4"
      >
        <div className="flex items-end gap-2 max-w-[75%]">
          <div className="flex flex-col items-end">
            <div className="bg-indigo-600 text-white px-4 py-2.5 rounded-2xl rounded-br-md shadow-lg shadow-indigo-500/20">
              <p className="text-sm leading-relaxed">{message.content}</p>
            </div>
            <span className="text-xs text-slate-500 mt-1 px-1">{timestamp}</span>
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className="flex justify-start mb-4"
    >
      <div className="flex items-end gap-2 max-w-[75%]">
        {showAvatar && (
          <div className="flex flex-col items-center gap-1">
            <div className={cn(
              "w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold text-white",
              colors.bg,
              "ring-2",
              colors.ring
            )}>
              {message.sender_avatar ? (
                <img 
                  src={message.sender_avatar} 
                  alt={message.sender_name}
                  className="w-full h-full rounded-full object-cover"
                />
              ) : (
                initial
              )}
            </div>
          </div>
        )}
        
        <div className="flex flex-col">
          <div className={cn(
            "px-4 py-2.5 rounded-2xl rounded-bl-md border shadow-lg",
            colors.bubble
          )}>
            <p className="text-sm leading-relaxed text-slate-200">{message.content}</p>
          </div>
          <div className="flex items-center gap-2 mt-1 px-1">
            <span className={cn("text-xs font-medium", colors.text)}>
              {message.sender_name}
            </span>
            <span className="text-xs text-slate-500">{timestamp}</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export default GroupChatMessage;
