import { create } from 'zustand';
import { useStore } from './store';

const API_BASE_URL = ((import.meta as any).env?.VITE_API_BASE_URL ?? 'http://localhost:8000') + '/api';

function toBackendCompanionId(personality: string | undefined): string {
  const p = (personality ?? '').toLowerCase();
  if (p === 'life-of-the-party' || p === 'chloe') return 'party_friend';
  if (p === 'night-owl philosopher' || p === 'julian') return 'philosopher';
  if (p === 'competitive rival' || p === 'victoria') return 'rival';
  if (p === 'clueless freshman' || p === 'toby') return 'freshman';
  return 'party_friend';
}

function authHeaders(): Record<string, string> {
  const token = useStore.getState().authToken;
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

export interface EpisodeNodeChoice {
  choice_id: string;
  choice_text: string;
  next_node_id?: string;
  xp_reward: number;
}

export interface EpisodeScriptNode {
  node_id: string;
  companion_dialogue: string;
  choices: EpisodeNodeChoice[];
  is_start_node: boolean;
  is_end_node: boolean;
}

export interface Episode {
  _id: string;
  companion_id: string;
  title: string;
  description: string;
  required_relationship_stage: number;
  script_nodes: EpisodeScriptNode[];
  created_at: string;
}

export interface EpisodeProgress {
  _id: string;
  user_id: string;
  episode_id: string;
  companion_id: string;
  status: 'not_started' | 'in_progress' | 'completed';
  current_node_id?: string;
  total_xp_earned: number;
  completed_at?: string;
}

export interface EpisodeChoiceResponse {
  success: boolean;
  next_node?: EpisodeScriptNode;
  xp_earned: number;
  total_xp_earned: number;
  is_completed: boolean;
}

interface EpisodeStore {
  episodes: Episode[];
  completedEpisodes: EpisodeProgress[];
  currentEpisode: Episode | null;
  currentNode: EpisodeScriptNode | null;
  currentProgress: EpisodeProgress | null;
  isLoading: boolean;
  error: string | null;
  
  fetchEpisodes: (companionId: string) => Promise<void>;
  fetchCompletedEpisodes: (companionId: string) => Promise<void>;
  startEpisode: (episodeId: string) => Promise<void>;
  fetchEpisodeState: (episodeId: string) => Promise<void>;
  makeChoice: (episodeId: string, choiceId: string) => Promise<EpisodeChoiceResponse | null>;
  resetCurrentEpisode: () => void;
}

export const useEpisodeStore = create<EpisodeStore>()((set, get) => ({
  episodes: [],
  completedEpisodes: [],
  currentEpisode: null,
  currentNode: null,
  currentProgress: null,
  isLoading: false,
  error: null,

  fetchEpisodes: async (companionId: string) => {
    set({ isLoading: true, error: null });
    try {
      const backendId = toBackendCompanionId(
        useStore.getState().myCompanions.find(c => c.id === companionId)?.personality ?? companionId
      );
      const resp = await fetch(`${API_BASE_URL}/episodes/${backendId}`, {
        headers: authHeaders(),
      });
      if (!resp.ok) throw new Error('Failed to fetch episodes');
      const data = await resp.json();
      set({ episodes: data, isLoading: false });
    } catch (e) {
      set({ error: e instanceof Error ? e.message : 'Failed to fetch episodes', isLoading: false });
    }
  },

  fetchCompletedEpisodes: async (companionId: string) => {
    set({ isLoading: true, error: null });
    try {
      const backendId = toBackendCompanionId(
        useStore.getState().myCompanions.find(c => c.id === companionId)?.personality ?? companionId
      );
      const resp = await fetch(`${API_BASE_URL}/episodes/completed/${backendId}`, {
        headers: authHeaders(),
      });
      if (!resp.ok) throw new Error('Failed to fetch completed episodes');
      const data = await resp.json();
      set({ completedEpisodes: data, isLoading: false });
    } catch (e) {
      set({ error: e instanceof Error ? e.message : 'Failed to fetch completed', isLoading: false });
    }
  },

  startEpisode: async (episodeId: string) => {
    set({ isLoading: true, error: null });
    try {
      const resp = await fetch(`${API_BASE_URL}/episodes/start?episode_id=${encodeURIComponent(episodeId)}`, {
        method: 'POST',
        headers: authHeaders(),
      });
      if (!resp.ok) throw new Error('Failed to start episode');
      const progress = await resp.json();
      const episode = get().episodes.find(e => e._id === episodeId) || null;
      const startNode = episode?.script_nodes.find(n => n.is_start_node) || null;
      set({ 
        currentProgress: progress, 
        currentEpisode: episode, 
        currentNode: startNode, 
        isLoading: false 
      });
    } catch (e) {
      set({ error: e instanceof Error ? e.message : 'Failed to start episode', isLoading: false });
    }
  },

  fetchEpisodeState: async (episodeId: string) => {
    set({ isLoading: true, error: null });
    try {
      const resp = await fetch(`${API_BASE_URL}/episodes/state/${encodeURIComponent(episodeId)}`, {
        headers: authHeaders(),
      });
      if (!resp.ok) throw new Error('Failed to get episode state');
      const node = await resp.json();
      const episode = get().episodes.find(e => e._id === episodeId) || null;
      set({ currentNode: node, currentEpisode: episode, isLoading: false });
    } catch (e) {
      set({ error: e instanceof Error ? e.message : 'Failed to get state', isLoading: false });
    }
  },

  makeChoice: async (episodeId: string, choiceId: string): Promise<EpisodeChoiceResponse | null> => {
    set({ isLoading: true, error: null });
    try {
      const resp = await fetch(`${API_BASE_URL}/episodes/choice`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders(),
        },
        body: JSON.stringify({ episode_id: episodeId, choice_id: choiceId }),
      });
      if (!resp.ok) throw new Error('Failed to make choice');
      const result = await resp.json();
      
      if (result.is_completed) {
        set({ currentNode: result.next_node, isLoading: false });
        // Update completed episodes
        await get().fetchCompletedEpisodes(
          get().currentEpisode?.companion_id || 
          useStore.getState().myCompanions.find(c => c.episodes.some(e => e.id === episodeId))?.id || ''
        );
      } else {
        set({ currentNode: result.next_node, isLoading: false });
      }
      
      return result;
    } catch (e) {
      set({ error: e instanceof Error ? e.message : 'Failed to make choice', isLoading: false });
      return null;
    }
  },

  resetCurrentEpisode: () => {
    set({ currentEpisode: null, currentNode: null, currentProgress: null, error: null });
  }
}));
