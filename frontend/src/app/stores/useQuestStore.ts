import { create } from 'zustand';
import axios from 'axios';

const API_BASE_URL = ((import.meta as any).env?.VITE_API_BASE_URL ?? 'http://localhost:8000') + '/api';

export type QuestType = 'study' | 'social' | 'wellness' | 'rivalry';
export type QuestStatus = 'active' | 'completed' | 'failed';

export interface Quest {
  id: string;
  quest_id: string;
  title: string;
  description: string;
  quest_type: QuestType;
  xp_reward: number;
  companion_giver: string;
  companion_name?: string;
  companion_avatar?: string;
  status: QuestStatus;
  started_at: string;
  completed_at?: string;
  user_report_text?: string;
  verification_result?: boolean;
  retry_count: number;
  verification_method: 'auto' | 'manual' | 'openrouter';
  target_count?: number;
  progress_count?: number;
  trigger_event?: string;
}

export interface QuestHistoryEntry {
  date: string;
  quests: Quest[];
  total_xp: number;
  completed_count: number;
}

interface QuestState {
  // State
  activeQuests: Quest[];
  questHistory: QuestHistoryEntry[];
  isLoading: boolean;
  error: string | null;
  lastFetchedAt: number | null;
  
  // Actions
  fetchActiveQuests: (authToken: string | null) => Promise<void>;
  completeQuest: (questId: string, reportText: string, authToken: string | null) => Promise<boolean>;
  fetchHistory: (days: number, authToken: string | null) => Promise<void>;
  getQuestsByCompanion: (companionId: string) => Quest[];
  getDailyProgress: () => { total: number; completed: number; xp: number };
}

const companionInfo: Record<string, { name: string; avatar: string; color: string }> = {
  study_buddy: { name: 'Oliver', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Oliver', color: 'emerald' },
  party_friend: { name: 'Chloe', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Chloe', color: 'pink' },
  philosopher: { name: 'Julian', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Julian', color: 'violet' },
  rival: { name: 'Victoria', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Victoria', color: 'rose' },
  freshman: { name: 'Toby', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Toby', color: 'amber' },
};

export const useQuestStore = create<QuestState>((set, get) => ({
  // Initial state
  activeQuests: [],
  questHistory: [],
  isLoading: false,
  error: null,
  lastFetchedAt: null,

  fetchActiveQuests: async (authToken: string | null) => {
    if (!authToken) {
      set({ error: 'No authentication token' });
      return;
    }

    set({ isLoading: true, error: null });

    try {
      const response = await axios.get(`${API_BASE_URL}/quests/active`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });

      // Add companion info to quests
      const questsWithCompanionInfo = (response.data || []).map((quest: Quest) => ({
        ...quest,
        companion_name: companionInfo[quest.companion_giver]?.name,
        companion_avatar: companionInfo[quest.companion_giver]?.avatar,
      }));

      set({ 
        activeQuests: questsWithCompanionInfo,
        lastFetchedAt: Date.now()
      });
    } catch (error) {
      console.error('Failed to fetch active quests:', error);
      set({ error: 'Failed to fetch quests' });
    } finally {
      set({ isLoading: false });
    }
  },

  completeQuest: async (questId: string, reportText: string, authToken: string | null): Promise<boolean> => {
    if (!authToken) return false;

    try {
      const response = await axios.post(
        `${API_BASE_URL}/quests/complete/${questId}`,
        { report_text: reportText },
        { headers: { Authorization: `Bearer ${authToken}` } }
      );

      if (response.data.success) {
        // Update local state
        const { activeQuests } = get();
        const updatedQuests = activeQuests.map(q => 
          q.id === questId 
            ? { ...q, status: 'completed' as QuestStatus, completed_at: new Date().toISOString(), user_report_text: reportText }
            : q
        );
        set({ activeQuests: updatedQuests });
        return true;
      }
    } catch (error) {
      console.error('Failed to complete quest:', error);
    }
    return false;
  },

  fetchHistory: async (_days: number = 7, authToken: string | null) => {
    if (!authToken) return;

    set({ isLoading: true });

    try {
      const response = await axios.get(`${API_BASE_URL}/quests/history`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });

      // Format history for the UI
      const historyData = response.data;
      const formattedHistory: QuestHistoryEntry[] = [];
      
      // Group by date
      const grouped: Record<string, Quest[]> = {};
      [...historyData.active, ...historyData.completed, ...historyData.failed].forEach((quest: Quest) => {
        const date = new Date(quest.started_at).toDateString();
        if (!grouped[date]) grouped[date] = [];
        grouped[date].push({
          ...quest,
          companion_name: companionInfo[quest.companion_giver]?.name,
          companion_avatar: companionInfo[quest.companion_giver]?.avatar,
        });
      });

      for (const [date, quests] of Object.entries(grouped)) {
        const completed = quests.filter(q => q.status === 'completed');
        formattedHistory.push({
          date,
          quests,
          total_xp: completed.reduce((sum, q) => sum + q.xp_reward, 0),
          completed_count: completed.length,
        });
      }

      set({ questHistory: formattedHistory });
    } catch (error) {
      console.error('Failed to fetch quest history:', error);
    } finally {
      set({ isLoading: false });
    }
  },

  getQuestsByCompanion: (companionId: string) => {
    return get().activeQuests.filter(q => q.companion_giver === companionId);
  },

  getDailyProgress: () => {
    const today = new Date().toDateString();
    const todaysQuests = get().activeQuests.filter(q => 
      new Date(q.started_at).toDateString() === today
    );
    
    const completed = todaysQuests.filter(q => q.status === 'completed').length;
    const xp = todaysQuests
      .filter(q => q.status === 'completed')
      .reduce((sum, q) => sum + q.xp_reward, 0);

    return {
      total: todaysQuests.length,
      completed,
      xp
    };
  }
}));

export default useQuestStore;
