import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router';
import { useEpisodeStore } from '../useEpisodeStore';
import { useStore } from '../store';
import EpisodeCard from '../components/EpisodeCard';
import { ArrowLeft } from 'lucide-react';
import { INITIAL_COMPANIONS } from '../store';

type Filter = 'all' | 'available' | 'in_progress' | 'completed';

export default function EpisodesListPage() {
  const { companionId } = useParams<{ companionId: string }>();
  const [filter, setFilter] = useState<Filter>('all');
  const {
    episodes,
    completedEpisodes,
    isLoading,
    fetchEpisodes,
    fetchCompletedEpisodes
  } = useEpisodeStore();
  const { companions, myCompanions } = useStore();

  const companion = myCompanions.find(c => c.id === companionId) ||
    INITIAL_COMPANIONS.find(c => c.id === companionId);

  const userRelationshipStage = companion?.relationshipStage || 'Stranger';
  const stageToInt: Record<string, number> = {
    Stranger: 0,
    Curious: 1,
    Friend: 2,
    'Close Friend': 3,
    Confidant: 4
  };
  const userStageInt = stageToInt[userRelationshipStage] || 0;

  useEffect(() => {
    if (companionId) {
      fetchEpisodes(companionId);
      fetchCompletedEpisodes(companionId);
    }
  }, [companionId]);

  const completedIds = new Set(completedEpisodes.map(p => p.episode_id));
  const inProgressIds = new Set(completedEpisodes.filter(p => p.status === 'in_progress').map(p => p.episode_id));

  const filteredEpisodes = episodes.filter(ep => {
    switch (filter) {
      case 'available':
        return ep.required_relationship_stage <= userStageInt && !completedIds.has(ep._id);
      case 'in_progress':
        return inProgressIds.has(ep._id);
      case 'completed':
        return completedIds.has(ep._id);
      default:
        return true;
    }
  });

  return (
    <div className="min-h-screen bg-slate-900 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link
            to={`/app/companion/${companionId}/profile`}
            className="inline-flex items-center gap-2 text-slate-400 hover:text-white transition-colors mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Profile
          </Link>
          <h1 className="text-3xl font-bold text-white mb-2">
            Stories with {companion?.name || 'Your Companion'}
          </h1>
          <p className="text-slate-400">Choose a story to start your adventure</p>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2 mb-8 bg-slate-800 p-1.5 rounded-xl w-fit">
          {(['all', 'available', 'in_progress', 'completed'] as Filter[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                filter === tab
                  ? 'bg-indigo-600 text-white shadow-lg'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {tab.replace('_', ' ').charAt(0).toUpperCase() + tab.replace('_', ' ').slice(1)}
            </button>
          ))}
        </div>

        {/* Grid */}
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredEpisodes.map((episode) => (
              <EpisodeCard
                key={episode._id}
                episode={episode}
                progress={completedEpisodes.find(p => p.episode_id === episode._id)}
                companionId={companionId!}
                isLocked={episode.required_relationship_stage > userStageInt}
              />
            ))}
          </div>
        )}

        {!isLoading && filteredEpisodes.length === 0 && (
          <div className="text-center py-20 text-slate-400">
            <p className="text-lg">No stories found for this filter</p>
          </div>
        )}
      </div>
    </div>
  );
}
