import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { useNavigate, Link } from "react-router";
import { ChevronLeft } from "lucide-react";
import { useStore } from "../store";
import { companionColorClasses, cn } from "../utils";

export default function CompanionSelection() {
  const companions = useStore(state => state.companions);
  const selectCompanion = useStore(state => state.selectCompanion);
  const myCompanions = useStore(state => state.myCompanions);
  const navigate = useNavigate();

  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [customName, setCustomName] = useState<string>("");

  const handleSelect = (id: string) => {
    setSelectedId(id);
    setCustomName(companions.find(c => c.id === id)?.name || "");
  };

  const handleConfirm = () => {
    if (selectedId) {
      selectCompanion(selectedId, customName);
      navigate('/app');
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-50 flex flex-col py-10 sm:py-16 px-4 sm:px-8 relative overflow-hidden">
      <div className="absolute top-0 w-full h-full bg-[radial-gradient(ellipse_at_top,rgba(24,24,27,0)_0%,rgba(24,24,27,1)_80%)] z-0 pointer-events-none" />
      
      <div className="relative z-10 max-w-7xl mx-auto w-full pt-4">
        <Link 
          to="/app" 
          className="absolute top-0 left-0 p-2 sm:px-4 sm:py-2 flex items-center gap-2 text-zinc-400 hover:text-white transition-colors bg-zinc-900/50 rounded-full backdrop-blur-md border border-zinc-800"
        >
          <ChevronLeft className="w-5 h-5" />
          <span className="text-sm font-medium hidden sm:inline">Back</span>
        </Link>

        <div className="text-center mb-10 sm:mb-16 mt-8 sm:mt-0">
          <motion.h1 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-3xl sm:text-4xl md:text-5xl font-light tracking-tighter mb-4"
          >
            Choose Your Companion
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-zinc-400 max-w-lg mx-auto"
          >
            Select a companion to join you on your campus journey. Each brings a unique personality and story.
          </motion.p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
          {companions.map((comp, idx) => {
            const colors = companionColorClasses[comp.color];
            const isHovered = hoveredId === comp.id;
            const isSelected = selectedId === comp.id;
            const isAlreadyAdded = myCompanions.some(c => c.id === comp.id);

            return (
              <motion.div
                key={comp.id}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: idx * 0.1 }}
                onMouseEnter={() => setHoveredId(comp.id)}
                onMouseLeave={() => setHoveredId(null)}
                onClick={() => !isAlreadyAdded && handleSelect(comp.id)}
                className={cn(
                  "relative group rounded-3xl overflow-hidden cursor-pointer border border-zinc-800/50 bg-zinc-900/50 backdrop-blur-sm transition-all duration-500",
                  isSelected && "ring-2 ring-white scale-[1.02]",
                  isAlreadyAdded && "opacity-50 cursor-not-allowed"
                )}
              >
                {/* Background glow on hover */}
                <div className={cn(
                  "absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none",
                  colors.bgLight
                )} />

                <div className="h-64 relative overflow-hidden">
                  <img 
                    src={comp.avatarUrl} 
                    alt={comp.name} 
                    className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110" 
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-zinc-950 via-zinc-950/20 to-transparent" />
                  
                  <div className="absolute bottom-4 left-4 right-4">
                    <div className="flex items-center gap-2 mb-1">
                      <div className={cn("w-2 h-2 rounded-full", colors.bg, colors.glow)} />
                      <span className="text-xs font-medium tracking-wider uppercase text-zinc-300">
                        {comp.personality}
                      </span>
                    </div>
                    <h3 className="text-2xl font-semibold tracking-tight">{comp.name}</h3>
                  </div>
                </div>

                <div className="p-5">
                  <p className="text-sm text-zinc-400 mb-4 line-clamp-2">
                    {comp.description}
                  </p>

                  <div className="flex flex-wrap gap-2 mb-6">
                    {comp.traits.slice(0, 3).map(trait => (
                      <span key={trait} className="px-2 py-1 bg-zinc-800/80 rounded-md text-xs text-zinc-300">
                        {trait}
                      </span>
                    ))}
                  </div>

                  <AnimatePresence>
                    {(isHovered || isSelected) && !isAlreadyAdded && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="overflow-hidden"
                      >
                        <div className="text-xs text-zinc-500 mb-3 italic">
                          Theme: {comp.theme}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  <div className="flex gap-2">
                    <button 
                      disabled={isAlreadyAdded}
                      onClick={(e) => {
                        e.stopPropagation();
                        if (!isAlreadyAdded) handleSelect(comp.id);
                      }}
                      className={cn(
                        "flex-1 py-2.5 rounded-xl text-sm font-medium transition-colors",
                        isAlreadyAdded ? "bg-zinc-800 text-zinc-500" : "bg-white text-zinc-950 hover:bg-zinc-200"
                      )}
                    >
                      {isAlreadyAdded ? 'Added' : 'Select'}
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/app/companion/${comp.id}/profile`);
                      }}
                      className="flex-1 py-2.5 rounded-xl text-sm font-medium transition-colors bg-transparent border border-zinc-700 hover:border-zinc-500 text-zinc-300"
                    >
                      Profile
                    </button>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* Confirmation Modal */}
      <AnimatePresence>
        {selectedId && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-zinc-950/80 backdrop-blur-md"
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="bg-zinc-900 border border-zinc-800 p-8 rounded-3xl w-full max-w-md shadow-2xl"
            >
              <h2 className="text-2xl font-medium mb-2">Name Your Companion</h2>
              <p className="text-zinc-400 text-sm mb-6">You can keep their default name or give them a custom one.</p>
              
              <input 
                type="text" 
                value={customName}
                onChange={(e) => setCustomName(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 mb-6"
              />

              <div className="flex gap-3">
                <button 
                  onClick={() => setSelectedId(null)}
                  className="flex-1 py-3 rounded-xl border border-zinc-700 text-zinc-300 hover:bg-zinc-800 transition-colors"
                >
                  Cancel
                </button>
                <button 
                  onClick={handleConfirm}
                  className="flex-1 py-3 rounded-xl bg-white text-zinc-950 font-medium hover:bg-zinc-200 transition-colors"
                >
                  Confirm
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
