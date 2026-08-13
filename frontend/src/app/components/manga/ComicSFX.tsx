import { motion, AnimatePresence } from 'motion/react';

type SFXType =
  | 'BAM' | 'POW' | 'WHAM'
  | 'WHOOSH' | 'SWISH'
  | 'TING' | 'BING' | 'DING'
  | 'CRACK' | 'SPLAT'
  | 'ZAP' | 'FLASH'
  | 'THUMP' | 'THUD';

interface ComicSFXProps {
  type: SFXType;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  scale?: number;
  rotation?: number;
  duration?: number;
  delay?: number;
}

const sfxStyles: Record<SFXType, string> = {
  BAM: 'text-3xl font-black text-red-500 tracking-tighter italic',
  POW: 'text-4xl font-black text-yellow-500 tracking-tighter italic',
  WHAM: 'text-3xl font-black text-red-600 tracking-tighter italic',
  SWISH: 'text-2xl font-bold text-cyan-400 tracking-wider italic',
  WHOOSH: 'text-2xl font-bold text-cyan-400 tracking-wider italic',
  TING: 'text-xl font-semibold text-yellow-400 tracking-wider',
  BING: 'text-xl font-semibold text-blue-400 tracking-wider',
  DING: 'text-xl font-semibold text-yellow-400 tracking-wider',
  CRACK: 'text-xl font-black text-orange-500 tracking-tighter',
  SPLAT: 'text-xl font-black text-purple-500 tracking-tighter',
  ZAP: 'text-2xl font-bold text-yellow-400 tracking-tighter italic',
  FLASH: 'text-2xl font-black text-white tracking-tighter bg-gradient-to-r from-white to-yellow-200',
  THUMP: 'text-3xl font-black text-red-600 tracking-tighter italic',
  THUD: 'text-3xl font-black text-amber-600 tracking-tighter italic',
};

const positionClasses: Record<string, string> = {
  'top-right': 'top-4 right-4',
  'top-left': 'top-4 left-4',
  'bottom-right': 'bottom-4 right-4',
  'bottom-left': 'bottom-4 left-4',
};

export function ComicSFX({
  type,
  position = 'top-right',
  scale = 1,
  rotation = 0,
  duration = 0.5,
  delay = 0,
}: ComicSFXProps) {
  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, scale: 0, rotate: rotation - 45 }}
        animate={{
          opacity: [0, 1, 0],
          scale: [0, scale, scale * 0.5],
          rotate: [rotation - 45, rotation, rotation],
        }}
        exit={{ opacity: 0, scale: 0 }}
        transition={{
          duration,
          delay,
          times: [0, 0.3, 1],
          ease: 'easeOut',
        }}
        className={`absolute ${positionClasses[position]} select-none pointer-events-none ${sfxStyles[type]}`}
        style={{ fontFamily: 'Impact, "Arial Black", sans-serif' }}
      >
        {type}
      </motion.div>
    </AnimatePresence>
  );
}

// Special visual effects
export function ZoomEffect({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
  return (
    <motion.div
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      exit={{ scale: 1.5, opacity: 0 }}
      transition={{
        type: 'spring',
        stiffness: 200,
        damping: 20,
        delay,
      }}
    >
      {children}
    </motion.div>
  );
}

export function ShakeEffect({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      animate={{
        x: [0, -10, 10, -10, 10, 0],
      }}
      transition={{
        duration: 0.4,
        repeat: 3,
        ease: 'easeInOut',
      }}
    >
      {children}
    </motion.div>
  );
}

export function FlashEffect({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 1.5 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 1, scale: 0.5 }}
      transition={{
        duration: 0.3,
        delay,
        times: [0, 0.1, 1],
      }}
    >
      {children}
    </motion.div>
  );
}
