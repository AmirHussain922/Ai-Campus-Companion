import { motion } from 'motion/react';
import { cn } from '../../utils';

interface MangaBubbleProps {
  children: React.ReactNode;
  direction?: 'left' | 'right' | 'center';
  tailColor?: string;
  size?: 'sm' | 'md' | 'lg';
  emotion?: 'happy' | 'sad' | 'angry' | 'shock' | 'calm';
}

const sizeClasses = {
  sm: 'text-xs px-3 py-2 rounded-lg',
  md: 'text-sm px-4 py-3 rounded-xl',
  lg: 'text-base px-6 py-4 rounded-2xl',
};

const emotionEffects = {
  happy: 'from-yellow-400/20 to-orange-400/20 border-yellow-400/30',
  sad: 'from-blue-400/20 to-cyan-400/20 border-blue-400/30',
  angry: 'from-red-400/20 to-pink-400/20 border-red-400/30',
  shock: 'from-purple-400/20 to-violet-400/20 border-purple-400/30',
  calm: 'from-emerald-400/20 to-teal-400/20 border-emerald-400/30',
};

const tailPositions = {
  left: 'rounded-br-md',
  right: 'rounded-bl-md',
  center: 'rounded-2xl',
};

export function MangaBubble({
  children,
  direction = 'left',
  tailColor = '#ffffff',
  size = 'md',
  emotion = 'calm',
}: MangaBubbleProps) {
  const isCenter = direction === 'center';

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      className="relative"
    >
      {/* Speech Bubble */}
      <div
        className={cn(
          'relative bg-gradient-to-br backdrop-blur-sm p-3 shadow-lg border-2',
          emotionEffects[emotion],
          sizeClasses[size],
          tailPositions[direction]
        )}
        style={{ borderColor: tailColor }}
      >
        {children}
      </div>

      {/* Bubble Tail (Pointer) */}
      {!isCenter && (
        <div
          className="absolute w-0 h-0"
          style={{
            borderLeft: `${size === 'sm' ? '10px' : size === 'md' ? '15px' : '20px'} solid transparent`,
            borderRight: `${size === 'sm' ? '10px' : size === 'md' ? '15px' : '20px'} solid transparent`,
            borderTop: `${size === 'sm' ? '10px' : size === 'md' ? '15px' : '20px'} solid ${tailColor}`,
            position: 'absolute',
          }}
        />
      )}

      {/* Comic-style braces */}
      {!isCenter && (
        <div className="absolute -left-3 top-0 bottom-0 flex flex-col justify-between">
          <div className={cn('w-3 h-3 rounded-full', direction === 'left' ? 'bg-zinc-900' : 'bg-zinc-950')} />
          <div className={cn('w-3 h-3 rounded-full', direction === 'left' ? 'bg-zinc-900' : 'bg-zinc-950')} />
          <div className={cn('w-3 h-3 rounded-full', direction === 'left' ? 'bg-zinc-900' : 'bg-zinc-950')} />
        </div>
      )}
    </motion.div>
  );
}
