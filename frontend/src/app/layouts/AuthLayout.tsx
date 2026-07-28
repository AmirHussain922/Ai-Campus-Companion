import { Outlet, Link } from "react-router";
import { motion } from "motion/react";

export default function AuthLayout() {
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-50 flex items-center justify-center relative overflow-hidden">
      {/* Animated background elements */}
      <motion.div 
        animate={{ 
          scale: [1, 1.2, 1],
          opacity: [0.3, 0.5, 0.3],
        }}
        transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
        className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-purple-900/20 rounded-full blur-[120px] pointer-events-none"
      />
      <motion.div 
        animate={{ 
          scale: [1, 1.5, 1],
          opacity: [0.2, 0.4, 0.2],
        }}
        transition={{ duration: 15, repeat: Infinity, ease: "easeInOut" }}
        className="absolute bottom-1/4 right-1/4 w-[600px] h-[600px] bg-blue-900/20 rounded-full blur-[150px] pointer-events-none"
      />

      <div className="w-full max-w-md p-8 z-10 relative">
        <div className="mb-8 text-center">
          <Link to="/" className="inline-block text-2xl font-bold tracking-tighter">
            AI Campus<span className="text-zinc-500">.</span>
          </Link>
        </div>
        <Outlet />
      </div>
    </div>
  );
}
