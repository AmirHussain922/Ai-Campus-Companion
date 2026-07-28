import { create } from 'zustand';
import axios from 'axios';

const API_BASE_URL = ((import.meta as any).env?.VITE_API_BASE_URL ?? 'http://localhost:8000') + '/api';

export type StudyMode = 'supportive' | 'challenger';
export type StudySessionStatus = 'idle' | 'active' | 'paused' | 'completed';

export interface StudySession {
  id: string;
  user_id: string;
  duration_minutes: number;
  topic: string;
  mode: StudyMode;
  started_at: string;
  ended_at?: string;
  status: StudySessionStatus;
  interruptions: number;
  xp_earned: number;
  companion_id?: string;
}

export interface LeaderboardEntry {
  rank: number;
  user_id: string;
  display_name: string;
  avatar_url?: string;
  total_minutes: number;
  sessions_count: number;
  xp_earned: number;
  is_current_user?: boolean;
}

interface StudyState {
  // State
  session: StudySession | null;
  timerRemaining: number; // seconds
  isActive: boolean;
  isPaused: boolean;
  interruptions: number;
  selectedMode: StudyMode;
  leaderboard: LeaderboardEntry[];
  isLoading: boolean;
  error: string | null;
  showAbandonConfirm: boolean;
  showCompleteModal: boolean;
  earnedXP: number;
  
  // Actions
  startSession: (durationMinutes: number, topic: string, authToken: string | null) => Promise<boolean>;
  checkStatus: (sessionId: string, authToken: string | null) => Promise<void>;
  completeSession: (authToken: string | null) => Promise<void>;
  abandonSession: (authToken: string | null) => void;
  fetchLeaderboard: (period: 'week' | 'month' | 'all', authToken: string | null) => Promise<void>;
  tickTimer: () => void;
  pauseTimer: () => void;
  resumeTimer: () => void;
  incrementInterruption: () => void;
  setMode: (mode: StudyMode) => void;
  setShowAbandonConfirm: (show: boolean) => void;
  setShowCompleteModal: (show: boolean) => void;
  reset: () => void;
}

const initialState = {
  session: null,
  timerRemaining: 0,
  isActive: false,
  isPaused: false,
  interruptions: 0,
  selectedMode: 'supportive' as StudyMode,
  leaderboard: [],
  isLoading: false,
  error: null,
  showAbandonConfirm: false,
  showCompleteModal: false,
  earnedXP: 0
};

export const useStudyStore = create<StudyState>((set, get) => ({
  ...initialState,

  startSession: async (durationMinutes: number, topic: string, authToken: string | null): Promise<boolean> => {
    if (!authToken) return false;

    set({ isLoading: true, error: null });

    // Map mode to companion_id
    const companionId = get().selectedMode === 'supportive' ? 'study_buddy' : 'rival';

    try {
      const response = await axios.post(
        `${API_BASE_URL}/study/sessions`,
        {
          duration_minutes: durationMinutes,
          focus_topic: topic,
          companion_id: companionId
        },
        { headers: { Authorization: `Bearer ${authToken}` } }
      );

      if (response.data.success && response.data.session) {
        const session = response.data.session;
        set({
          session: {
            ...session,
            topic: session.focus_topic // map backend field to frontend's expected field
          },
          timerRemaining: session.duration_minutes * 60,
          isActive: true,
          isPaused: false,
          interruptions: 0,
          isLoading: false
        });
        return true;
      }
    } catch (error) {
      console.error('Failed to start study session:', error);
      set({ error: 'Failed to start session', isLoading: false });
    }
    return false;
  },

  checkStatus: async (sessionId: string, authToken: string | null) => {
    if (!authToken) return;

    try {
      const response = await axios.get(`${API_BASE_URL}/study/sessions/${sessionId}`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });

      if (response.data.session) {
        set({ session: response.data.session });
      }
    } catch (error) {
      console.error('Failed to check session status:', error);
    }
  },

  completeSession: async (authToken: string | null) => {
    const { session } = get();
    if (!session || !authToken) return;

    try {
      const response = await axios.post(
        `${API_BASE_URL}/study/sessions/${session.id}/complete`,
        {},
        { headers: { Authorization: `Bearer ${authToken}` } }
      );

      if (response.data.success && response.data.session) {
        const completedData = response.data.session;
        set({
          session: {
            ...session,
            status: 'completed',
            xp_earned: completedData.xp_earned || 0
          },
          isActive: false,
          showCompleteModal: true,
          earnedXP: completedData.xp_earned || 0
        });
      }
    } catch (error) {
      console.error('Failed to complete session:', error);
    }
  },

  abandonSession: (authToken: string | null) => {
    const { session } = get();
    if (!session || !authToken) return;

    // API call to abandon
    axios.post(
      `${API_BASE_URL}/study/sessions/${session.id}/abandon`,
      {},
      { headers: { Authorization: `Bearer ${authToken}` } }
    ).catch(error => console.error('Failed to abandon session:', error));

    set({
      session: null,
      timerRemaining: 0,
      isActive: false,
      isPaused: false,
      interruptions: 0,
      showAbandonConfirm: false
    });
  },

  fetchLeaderboard: async (period: 'week' | 'month' | 'all' = 'week', authToken: string | null) => {
    if (!authToken) return;

    set({ isLoading: true });

    try {
      const response = await axios.get(`${API_BASE_URL}/study/leaderboard?period=${period}`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });

      set({ leaderboard: response.data.leaderboard || [], isLoading: false });
    } catch (error) {
      console.error('Failed to fetch leaderboard:', error);
      set({ isLoading: false });
    }
  },

  tickTimer: () => {
    const { timerRemaining, isActive, isPaused } = get();
    if (!isActive || isPaused || timerRemaining <= 0) return;

    const newRemaining = timerRemaining - 1;
    set({ timerRemaining: newRemaining });

    if (newRemaining <= 0) {
      // Timer completed
      set({ isActive: false });
      // Don't auto-complete, let user claim it
    }
  },

  pauseTimer: () => set({ isPaused: true }),
  resumeTimer: () => set({ isPaused: false }),

  incrementInterruption: () => {
    set(state => ({ interruptions: state.interruptions + 1 }));
  },

  setMode: (mode: StudyMode) => set({ selectedMode: mode }),
  setShowAbandonConfirm: (show: boolean) => set({ showAbandonConfirm: show }),
  setShowCompleteModal: (show: boolean) => set({ showCompleteModal: show }),
  reset: () => set(initialState)
}));

export default useStudyStore;
