import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Pause, Play, RotateCcw } from 'lucide-react';
import { cn } from '../utils';

interface StudyTimerProps {
  duration: number; // in seconds
  isActive: boolean;
  isPaused?: boolean;
  onComplete: () => void;
  onPause?: () => void;
  onResume?: () => void;
  onReset?: () => void;
  size?: number;
  strokeWidth?: number;
}

export function StudyTimer({
  duration,
  isActive,
  isPaused = false,
  onComplete,
  onPause,
  onResume,
  onReset,
  size = 240,
  strokeWidth = 8
}: StudyTimerProps) {
  const [remaining, setRemaining] = useState(duration);
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;

  // Color based on remaining time
  const getColor = () => {
    const percentage = remaining / duration;
    if (percentage > 0.5) return { stroke: '#10b981', glow: 'shadow-emerald-500/30', text: 'text-emerald-400' };
    if (percentage > 0.15) return { stroke: '#f59e0b', glow: 'shadow-amber-500/30', text: 'text-amber-400' };
    return { stroke: '#f43f5e', glow: 'shadow-rose-500/30', text: 'text-rose-400' };
  };

  const colors = getColor();
  const progress = remaining / duration;
  const strokeDashoffset = circumference * (1 - progress);

  // Format time as MM:SS
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  useEffect(() => {
    if (!isActive || isPaused) return;

    const interval = setInterval(() => {
      setRemaining(prev => {
        if (prev <= 1) {
          clearInterval(interval);
          onComplete();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isActive, isPaused, onComplete]);

  // Reset timer when duration changes
  useEffect(() => {
    setRemaining(duration);
  }, [duration]);

  return (
    <div className="relative flex flex-col items-center">
      {/* Timer Circle */}
      <div className={cn("relative", colors.glow, "shadow-2xl rounded-full")}>
        <svg
          width={size}
          height={size}
          className="transform -rotate-90"
        >
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth={strokeWidth}
            className="text-slate-800"
          />
          
          {/* Progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={colors.stroke}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            className="transition-all duration-1000 ease-linear"
          />
        </svg>

        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.div
            key={remaining}
            initial={{ scale: 0.9, opacity: 0.5 }}
            animate={{ scale: 1, opacity: 1 }}
            className={cn(
              "text-5xl font-bold tracking-tight font-mono",
              colors.text,
              remaining <= 60 && "animate-pulse"
            )}
          >
            {formatTime(remaining)}
          </motion.div>
          
          <p className="text-slate-500 text-sm mt-1">
            {isPaused ? 'Paused' : isActive ? 'Focusing...' : 'Ready to start'}
          </p>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-3 mt-6">
        {isActive && (
          <button
            onClick={onReset}
            className="p-3 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-all"
            title="Reset timer"
          >
            <RotateCcw className="w-5 h-5" />
          </button>
        )}

        <button
          onClick={isPaused ? onResume : onPause}
          disabled={!isActive}
          className={cn(
            "px-8 py-3 rounded-full font-medium transition-all duration-200 flex items-center gap-2",
            isPaused
              ? "bg-emerald-600 hover:bg-emerald-500 text-white"
              : "bg-amber-600 hover:bg-amber-500 text-white",
            !isActive && "opacity-50 cursor-not-allowed"
          )}
        >
          {isPaused ? (
            <>
              <Play className="w-5 h-5" />
              Resume
            </>
          ) : (
            <>
              <Pause className="w-5 h-5" />
              Pause
            </>
          )}
        </button>
      </div>
    </div>
  );
}

export default StudyTimer;
