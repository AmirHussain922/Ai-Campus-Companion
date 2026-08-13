import { create } from 'zustand';
import { useStore } from './store';
import { useToast } from './useToast';

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

const STAGE_NAMES = ['Stranger', 'Curious', 'Friend', 'Close Friend', 'Confidant'];

export interface JournalEntry {
  _id: string;
  user_id: string;
  companion_id: string;
  stage: number;
  entry_text: string;
  is_unlocked: boolean;
  unlocked_at?: string;
  is_read: boolean;
  generated_at: string;
  read_at?: string;
}

interface JournalStore {
  journals: JournalEntry[];
  isLoading: boolean;
  error: string | null;
  previousUnlockedStages: Set<number>;
  fetchJournals: (companionId: string) => Promise<void>;
  markAsRead: (companionId: string, stage: number) => Promise<void>;
}

export const useJournalStore = create<JournalStore>()((set, get) => ({
  journals: [],
  isLoading: false,
  error: null,
  previousUnlockedStages: new Set(),

  fetchJournals: async (companionId: string) => {
    set({ isLoading: true, error: null });
    try {
      const companion = useStore.getState().companions.find(c => c.id === companionId) || 
                        useStore.getState().myCompanions.find(c => c.id === companionId);
      const backendId = toBackendCompanionId(companion?.personality);

      const resp = await fetch(`${API_BASE_URL}/journals/${backendId}`, {
        headers: authHeaders(),
      });
      if (!resp.ok) throw new Error('Failed to fetch journals');
      const data = await resp.json();
      
      const previousUnlocked = get().previousUnlockedStages;
      const newUnlocked = new Set<number>();
      
      data.forEach((j: JournalEntry) => {
        if (j.is_unlocked) newUnlocked.add(j.stage);
      });
      
      const newlyUnlocked = Array.from(newUnlocked).filter(s => !previousUnlocked.has(s));
      if (newlyUnlocked.length > 0 && companion) {
        const highestStage = Math.max(...newlyUnlocked);
        const { addToast } = useToast.getState();
        addToast({
          message: `🔓 ${companion.name} wrote something about you! Check their journal for the ${STAGE_NAMES[highestStage]} stage!`,
          type: 'success'
        });
      }
      
      set({ 
        journals: data, 
        isLoading: false,
        previousUnlockedStages: newUnlocked
      });
    } catch (e) {
      set({ error: e instanceof Error ? e.message : 'Failed to fetch journals', isLoading: false });
    }
  },

  markAsRead: async (companionId: string, stage: number) => {
    set({ isLoading: true, error: null });
    try {
      const companion = useStore.getState().companions.find(c => c.id === companionId) || 
                        useStore.getState().myCompanions.find(c => c.id === companionId);
      const backendId = toBackendCompanionId(companion?.personality);

      const resp = await fetch(`${API_BASE_URL}/journals/${backendId}/${stage}/read`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
      });
      if (!resp.ok) throw new Error('Failed to mark as read');
      const updated = await resp.json();
      
      set((state) => ({
        journals: state.journals.map(j => 
          j.stage === stage ? { ...j, is_read: true, read_at: updated.read_at } : j
        ),
        isLoading: false,
      }));
    } catch (e) {
      set({ error: e instanceof Error ? e.message : 'Failed to mark as read', isLoading: false });
    }
  }
}));
