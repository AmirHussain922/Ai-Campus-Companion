import { Link } from 'react-router';
import { Check, Lock, Play } from 'lucide-react';
import { Episode, EpisodeProgress } from '../useEpisodeStore';

interface EpisodeCardProps {
  episode: Episode;
  progress?: EpisodeProgress;
  companionId: string;
  isLocked?: boolean;
}

export default function EpisodeCard({ episode, progress, companionId, isLocked }: EpisodeCardProps) {
  const status = progress?.status || 'not_started';
  const buttonText = status === 'completed' ? 'Replay' : status === 'in_progress' ? 'Continue' : 'Start Story';

  return (
    <div className="relative bg-slate-800 border border-slate-700 rounded-xl p-6 hover:border-indigo-500 transition-all duration-200 group">
      {isLocked && (
        <div className="absolute inset-0 bg-slate-900/70 rounded-xl flex items-center justify-center z-10">
          <div className="text-center">
            <Lock className="w-10 h-10 text-slate-400 mx-auto mb-2" />
            <p className="text-slate-400 text-sm">Relationship Stage {episode.required_relationship_stage + 1} Required</p>
          </div>
        </div>
      )}

      {status === 'completed' && (
        <div className="absolute top-4 right-4 bg-green-500/20 p-2 rounded-full">
          <Check className="w-5 h-5 text-green-400" />
        </div>
      )}

      <div className="mb-4">
        <div className="flex items-start justify-between gap-2">
          <h3 className="text-lg font-semibold text-white">{episode.title}</h3>
          <span className="text-xs font-medium px-2 py-1 bg-slate-700 text-slate-300 rounded-full">
            Stage {episode.required_relationship_stage + 1}
          </span>
        </div>
        <p className="text-slate-400 text-sm mt-2">{episode.description}</p>
      </div>

      {status === 'in_progress' && (
        <div className="mb-4">
          <div className="w-full bg-slate-700 rounded-full h-2.5">
            <div className="bg-indigo-500 h-2.5 rounded-full w-1/3 animate-pulse" />
          </div>
          <p className="text-xs text-slate-400 mt-1">In progress...</p>
        </div>
      )}

      <Link
        to={isLocked ? '#' : `/app/companion/${companionId}/episodes/play/${episode._id}`}
        className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
          isLocked
            ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
            : 'bg-indigo-600 hover:bg-indigo-500 text-white hover:scale-105'
        }`}
      >
        {status === 'in_progress' ? <Play className="w-4 h-4" /> : null}
        {buttonText}
      </Link>
    </div>
  );
}
