import { motion } from 'motion/react';
import { cn } from '../../utils';

interface ComicPanelProps {
  children: React.ReactNode;
  number?: number;
  index?: number;
  total?: number;
  layout?: 'single' | 'horizontal' | 'vertical' | 'grid';
  dashed?: boolean;
  showBorder?: boolean;
}

export function ComicPanel({
  children,
  number,
  index = 0,
  total = 1,
  layout = 'single',
  dashed = false,
  showBorder = true,
}: ComicPanelProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className="relative"
    >
      {/* Panel */}
      <div
        className={cn(
          'bg-white/10 backdrop-blur-sm',
          layout === 'single' && 'rounded-3xl',
          layout === 'horizontal' && 'rounded-2xl',
          layout === 'vertical' && 'rounded-2xl',
          layout === 'grid' && 'rounded-2xl',
          showBorder && 'border-4',
          showBorder && dashed && 'border-dashed',
          showBorder && 'border-zinc-300',
          !showBorder && 'border border-zinc-400/50'
        )}
        style={{
          backgroundImage: 'linear-gradient(45deg, transparent 25%, rgba(255,255,255,0.03) 25%, rgba(255,255,255,0.03) 50%, transparent 50%, transparent 75%, rgba(255,255,255,0.03) 75%)',
          backgroundSize: '20px 20px',
        }}
      >
        {children}
      </div>

      {/* Panel Number */}
      {number !== undefined && (
        <div className="absolute -top-3 -right-3 bg-white rounded-full w-10 h-10 flex items-center justify-center shadow-lg font-black text-zinc-900 text-lg">
          {number}
        </div>
      )}

      {/* Layout indicators */}
      {layout !== 'single' && (
        <div className="absolute top-2 left-2 flex gap-1">
          {[...Array(4)].map((_, i) => (
            <div
              key={i}
              className={cn(
                'w-2 h-2 rounded-full',
                i < total ? 'bg-zinc-900' : 'bg-zinc-300'
              )}
            />
          ))}
        </div>
      )}

      {/* Bleed marks */}
      {showBorder && (
        <>
          <div className="absolute -top-1 -left-1 w-4 h-4 border-t-2 border-l-2 border-zinc-900 rounded-tl-lg" />
          <div className="absolute -top-1 -right-1 w-4 h-4 border-t-2 border-r-2 border-zinc-900 rounded-tr-lg" />
          <div className="absolute -bottom-1 -left-1 w-4 h-4 border-b-2 border-l-2 border-zinc-900 rounded-bl-lg" />
          <div className="absolute -bottom-1 -right-1 w-4 h-4 border-b-2 border-r-2 border-zinc-900 rounded-br-lg" />
        </>
      )}
    </motion.div>
  );
}

// Word bubble for captions
interface WordBubbleProps {
  children: React.ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right' | 'corner';
  bgColor?: string;
  textColor?: string;
}

export function WordBubble({
  children,
  position = 'corner',
  bgColor = '#FFFFFF',
  textColor = '#1F2937',
}: WordBubbleProps) {
  const bubbleStyles = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
    corner: 'top-4 right-4',
  };

  return (
    <div
      className={cn(
        'relative px-4 py-2 rounded-lg shadow-lg font-black text-xl',
        bubbleStyles[position],
        position === 'corner' && 'absolute'
      )}
      style={{
        backgroundColor: bgColor,
        color: textColor,
      }}
    >
      {children}
      {/* Bubble tail */}
      {position !== 'corner' && (
        <div
          className="absolute w-3 h-3"
          style={{
            backgroundColor: bgColor,
            clipPath: position === 'top' || position === 'bottom' ? 'polygon(0 0, 100% 0, 50% 100%)' : 'polygon(0 0, 0 100%, 100% 50%)',
          }}
        />
      )}
    </div>
  );
}

// Onomatopoeia panel
interface OnomatopoeiaPanelProps {
  text: string;
  color?: string;
  size?: 'sm' | 'md' | 'lg';
  overlay?: boolean;
}

export function OnomatopoeiaPanel({
  text,
  color = '#FF6B6B',
  size = 'lg',
  overlay = false,
}: OnomatopoeiaPanelProps) {
  const sizeClasses = {
    sm: 'text-3xl',
    md: 'text-4xl',
    lg: 'text-6xl',
  };

  return (
    <motion.div
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      exit={{ scale: 1.5, opacity: 0 }}
      className={cn(
        'font-black italic tracking-tighter flex items-center justify-center',
        overlay && 'absolute inset-0',
        sizeClasses[size]
      )}
      style={{
        fontFamily: 'Impact, "Arial Black", sans-serif',
        color,
        textShadow: overlay ? '4px 4px 0px rgba(0,0,0,0.3)' : '2px 2px 0px rgba(0,0,0,0.1)',
      }}
    >
      {text}
    </motion.div>
  );
}

// Speed lines
interface SpeedLinesProps {
  direction?: 'horizontal' | 'vertical' | 'diagonal';
  count?: number;
  length?: number;
  opacity?: number;
}

export function SpeedLines({
  direction = 'horizontal',
  count = 8,
  length = 40,
  opacity = 0.6,
}: SpeedLinesProps) {
  const lines = Array.from({ length }, (_, i) => {
    const angle = direction === 'horizontal'
      ? 0
      : direction === 'vertical'
        ? 90
        : 45 + (i * 10 - 45);

    return (
      <div
        key={i}
        className="absolute bg-zinc-300/50 rounded-full"
        style={{
          width: direction === 'horizontal' ? length : 3,
          height: direction === 'horizontal' ? 3 : length,
          transform: `rotate(${angle}deg)`,
          transformOrigin: 'center',
        }}
      />
    );
  });

  return (
    <div className="relative w-full h-full overflow-hidden">
      {lines}
    </div>
  );
}
