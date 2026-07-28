import { AnimatePresence, motion } from 'motion/react';
import { X } from 'lucide-react';
import { useToast } from '../useToast';
import { cn } from '../utils';

export default function ToastContainer() {
  const { toasts, removeToast } = useToast();

  const getColors = (type: string) => {
    switch (type) {
      case 'success':
        return 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300';
      case 'warning':
        return 'bg-amber-500/20 border-amber-500/50 text-amber-300';
      case 'error':
        return 'bg-rose-500/20 border-rose-500/50 text-rose-300';
      default:
        return 'bg-indigo-500/20 border-indigo-500/50 text-indigo-300';
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-[1000] flex flex-col gap-3">
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => (
          <motion.div
            key={toast.id}
            initial={{ opacity: 0, x: 50, scale: 0.95 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 50, scale: 0.95 }}
            className={cn(
              'flex items-center gap-3 px-5 py-3 rounded-xl border backdrop-blur-md shadow-lg',
              getColors(toast.type)
            )}
          >
            <p className="text-sm font-medium">{toast.message}</p>
            <button
              onClick={() => removeToast(toast.id)}
              className="p-1 rounded-full hover:bg-white/10 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
