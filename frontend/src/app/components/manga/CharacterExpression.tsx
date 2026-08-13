import { motion, useReducedMotion } from 'motion/react';
import { useState, useEffect } from 'react';
import { cn } from '../../utils';

export type Emotion = 'happy' | 'sad' | 'angry' | 'shock' | 'calm' | 'excited' | 'worried' | 'embarrassed';

interface CharacterExpressionProps {
  emotion?: Emotion;
  size?: 'sm' | 'md' | 'lg';
  showOutline?: boolean;
  blinkInterval?: number;
  className?: string;
}

const emotionStyles: Record<Emotion, { stroke: string; fill: string; expression: string }> = {
  happy: {
    stroke: '#FBBF24', // amber-400
    fill: '#FEF3C7', // amber-100
    expression: '😊',
  },
  sad: {
    stroke: '#60A5FA', // blue-400
    fill: '#DBEAFE', // blue-100
    expression: '😢',
  },
  angry: {
    stroke: '#F87171', // red-400
    fill: '#FEE2E2', // red-100
    expression: '😠',
  },
  shock: {
    stroke: '#C084FC', // purple-400
    fill: '#F3E8FF', // purple-100
    expression: '😲',
  },
  calm: {
    stroke: '#34D399', // emerald-400
    fill: '#D1FAE5', // emerald-100
    expression: '😌',
  },
  excited: {
    stroke: '#F472B6', // pink-400
    fill: '#FCE7F3', // pink-100
    expression: '🤩',
  },
  worried: {
    stroke: '#FB923C', // orange-400
    fill: '#FFEDD5', // orange-100
    expression: '😟',
  },
  embarrassed: {
    stroke: '#A78BFA', // violet-400
    fill: '#EDE9FE', // violet-100
    expression: '😳',
  },
};

const sizeClasses = {
  sm: 'w-6 h-6',
  md: 'w-8 h-8',
  lg: 'w-12 h-12',
};

export function CharacterExpression({
  emotion = 'calm',
  size = 'md',
  showOutline = true,
  blinkInterval = 3000,
  className,
}: CharacterExpressionProps) {
  const style = emotionStyles[emotion];

  return (
    <div className={cn('relative', className)}>
      <svg
        viewBox="0 0 64 64"
        className={cn(sizeClasses[size], emotionStyles[emotion].expression)}
        style={{
          filter: 'drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2))',
        }}
      >
        {/* Face outline */}
        {showOutline && (
          <circle
            cx="32"
            cy="32"
            r="28"
            fill={style.fill}
            stroke={style.stroke}
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        )}

        {/* Eyes */}
        <g className="eye-group">
          <circle cx="24" cy="28" r="4" fill={style.stroke} />
          <circle cx="40" cy="28" r="4" fill={style.stroke} />
        </g>

        {/* Mouth - emotion based */}
        <g>
          {emotion === 'happy' && (
            <path
              d="M 20 40 Q 32 52 44 40"
              stroke={style.stroke}
              strokeWidth="2"
              fill="none"
              strokeLinecap="round"
            />
          )}
          {emotion === 'sad' && (
            <path
              d="M 20 40 Q 32 28 44 40"
              stroke={style.stroke}
              strokeWidth="2"
              fill="none"
              strokeLinecap="round"
            />
          )}
          {emotion === 'angry' && (
            <path
              d="M 22 36 L 42 44"
              stroke={style.stroke}
              strokeWidth="2"
              fill="none"
              strokeLinecap="round"
            />
          )}
          {emotion === 'shock' && (
            <ellipse
              cx="32"
              cy="42"
              rx="12"
              ry="4"
              fill={style.stroke}
            />
          )}
          {emotion === 'calm' && (
            <path
              d="M 22 42 Q 32 48 42 42"
              stroke={style.stroke}
              strokeWidth="2"
              fill="none"
              strokeLinecap="round"
            />
          )}
          {emotion === 'excited' && (
            <path
              d="M 18 36 Q 32 52 46 36"
              stroke={style.stroke}
              strokeWidth="2"
              fill="none"
              strokeLinecap="round"
            />
          )}
          {emotion === 'worried' && (
            <path
              d="M 20 42 Q 32 52 44 42"
              stroke={style.stroke}
              strokeWidth="2"
              fill="none"
              strokeLinecap="round"
            />
          )}
          {emotion === 'embarrassed' && (
            <path
              d="M 24 42 L 40 42"
              stroke={style.stroke}
              strokeWidth="2"
              fill="none"
              strokeLinecap="round"
            />
          )}
        </g>
      </svg>
    </div>
  );
}

// Expression change hook
export function useCharacterExpression(
  emotion: Emotion,
  duration: number = 500
) {
  const [currentEmotion, setCurrentEmotion] = useState<Emotion>(emotion);

  useEffect(() => {
    let timeout: NodeJS.Timeout;

    const changeExpression = () => {
      setCurrentEmotion(emotion);
    };

    timeout = setTimeout(changeExpression, duration);

    return () => clearTimeout(timeout);
  }, [emotion, duration]);

  return currentEmotion;
}

// Blink effect hook
export function useBlink(interval: number = 3000) {
  const isReducedMotion = useReducedMotion();
  const [isBlinking, setIsBlinking] = useState(false);

  useEffect(() => {
    if (isReducedMotion) return;

    const blink = () => {
      setIsBlinking(true);
      setTimeout(() => setIsBlinking(false), 150);
    };

    const timer = setInterval(blink, interval);

    return () => clearInterval(timer);
  }, [interval, isReducedMotion]);

  return isBlinking;
}
