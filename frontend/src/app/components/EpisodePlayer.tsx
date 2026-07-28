import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router';
import { useEpisodeStore, EpisodeChoiceResponse } from '../useEpisodeStore';
import { useStore } from '../store';
import { ArrowLeft, Loader2, Trophy, X } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

export default function EpisodePlayer() {
  const { companionId, episodeId } = useParams<{ companionId: string; episodeId: string }>();
  const {
    currentEpisode,
    currentNode,
    isLoading,
    fetchEpisodes,
    fetchEpisodeState,
    startEpisode,
    makeChoice,
    resetCurrentEpisode
  } = useEpisodeStore();
  const { companions } = useStore();
  const [showCompletion, setShowCompletion] = useState(false);
  const [totalXp, setTotalXp] = useState(0);

  const companion = companions.find(c => c.id === companionId);

  useEffect(() => {
    resetCurrentEpisode();
    if (companionId) {
      fetchEpisodes(companionId).then(() => {
        if (episodeId) {
          startEpisode(episodeId).then(() => {
            fetchEpisodeState(episodeId);
          });
        }
      });
    }
  }, [companionId, episodeId]);

  const handleChoice = async (choiceId: string) => {
    if (!episodeId) return;
    const result = await makeChoice(episodeId, choiceId);
    if (result) {
      setTotalXp(result.total_xp_earned);
      if (result.is_completed) {
        setShowCompletion(true);
        // Try to trigger confetti
        try {
          const confetti = (await import('canvas-confetti')).default;
          confetti({
            particleCount: 150,
            spread: 70,
            origin: { y: 0.6 }
          });
        } catch (e) {
          console.log('Confetti not available');
        }
      }
    }
  };

  if (!currentEpisode || !currentNode) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-900">
        <Loader2 className="w-10 h-10 animate-spin text-indigo-500" />
      </div>
    );
  }

  if (showCompletion) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="max-w-md w-full bg-slate-800 border border-slate-700 rounded-2xl p-8 text-center"
        >
          <div className="w-20 h-20 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full flex items-center justify-center mx-auto mb-6">
            <Trophy className="w-10 h-10 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-white mb-2">Story Complete!</h2>
          <p className="text-slate-400 mb-6">{currentEpisode.title}</p>
          <div className="bg-slate-700/50 rounded-xl p-4 mb-8">
            <p className="text-2xl font-bold text-indigo-400">+{totalXp} XP</p>
            <p className="text-slate-500 text-sm mt-1">Total XP earned</p>
          </div>
          <Link
            to={`/app/companion/${companionId}/profile`}
            className="inline-flex items-center justify-center w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-200"
          >
            Return to Profile
          </Link>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col">
      {/* Header */}
      <header className="p-4 border-b border-slate-700 bg-slate-800/50 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto flex items-center gap-4">
          <Link
            to={`/app/companion/${companionId}/profile`}
            className="p-2 rounded-lg hover:bg-slate-700 text-slate-300 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          {companion && (
            <div className="flex items-center gap-3">
              <img
                src={companion.avatarUrl}
                alt={companion.name}
                className="w-10 h-10 rounded-full object-cover"
              />
              <div>
                <h3 className="text-white font-semibold">{companion.name}</h3>
                <p className="text-slate-400 text-xs">{currentEpisode.title}</p>
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Content */}
      <main className="flex-1 max-w-4xl mx-auto w-full p-6 flex flex-col justify-center">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentNode.node_id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-8"
          >
            {/* Dialogue Bubble */}
            <div className="bg-slate-800 border border-slate-700 rounded-2xl p-8 max-w-2xl mx-auto shadow-xl">
              <p className="text-lg text-slate-200 leading-relaxed">
                {currentNode.companion_dialogue}
              </p>
            </div>

            {/* Choices */}
            {isLoading ? (
              <div className="flex justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
              </div>
            ) : (
              <div className="space-y-3 max-w-2xl mx-auto">
                {currentNode.choices.map((choice) => (
                  <motion.button
                    key={choice.choice_id}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => handleChoice(choice.choice_id)}
                    className="w-full text-left bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white p-5 rounded-xl font-medium shadow-lg transition-all duration-200"
                  >
                    <div className="flex items-center justify-between">
                      <span>{choice.choice_text}</span>
                      {choice.xp_reward > 0 && (
                        <span className="text-sm bg-white/20 px-2 py-1 rounded-full">
                          +{choice.xp_reward} XP
                        </span>
                      )}
                    </div>
                  </motion.button>
                ))}
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}
