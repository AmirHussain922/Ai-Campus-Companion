import { create } from 'zustand';
import axios from 'axios';

const API_BASE_URL = ((import.meta as any).env?.VITE_API_BASE_URL ?? 'http://localhost:8000') + '/api';

export type ProactiveTriggerType = 
  | 'good_morning' 
  | 'miss_you' 
  | 'milestone_congrats' 
  | 'quest_reminder' 
  | 'story_nudge';

export interface ProactiveMessage {
  id: string;
  companion_id: string;
  trigger_type: ProactiveTriggerType;
  content: string;
  sent_at: string;
  is_read: boolean;
}

export interface UnreadByCompanion {
  companion_id: string;
  companion_name: string;
  unread_count: number;
  messages: ProactiveMessage[];
}

interface ProactiveState {
  // State
  unreadMessages: UnreadByCompanion[];
  unreadCount: number;
  isLoading: boolean;
  lastFetchedAt: number | null;
  
  // Actions
  fetchUnread: (authToken: string | null) => Promise<void>;
  markAsRead: (messageId: string, authToken: string | null) => Promise<boolean>;
  markAllForCompanionAsRead: (companionId: string, authToken: string | null) => Promise<void>;
  pollUnread: (authToken: string | null) => Promise<void>;
  getUnreadForCompanion: (companionId: string) => ProactiveMessage[];
  
  // For toast notifications
  getNewMessagesSince: (timestamp: number) => ProactiveMessage[];
}

export const useProactiveStore = create<ProactiveState>((set, get) => ({
  // Initial state
  unreadMessages: [],
  unreadCount: 0,
  isLoading: false,
  lastFetchedAt: null,

  // Fetch unread messages from API
  fetchUnread: async (authToken: string | null) => {
    if (!authToken) return;
    
    set({ isLoading: true });
    
    try {
      const response = await axios.get(`${API_BASE_URL}/proactive/unread`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
        },
      });
      
      const unreadMessages: UnreadByCompanion[] = response.data || [];
      const totalUnread = unreadMessages.reduce(
        (sum, group) => sum + group.unread_count, 
        0
      );
      
      set({ 
        unreadMessages, 
        unreadCount: totalUnread,
        lastFetchedAt: Date.now(),
        isLoading: false 
      });
    } catch (error) {
      console.error('Failed to fetch unread proactive messages:', error);
      set({ isLoading: false });
    }
  },

  // Mark a single message as read
  markAsRead: async (messageId: string, authToken: string | null) => {
    if (!authToken) return false;
    
    try {
      await axios.post(
        `${API_BASE_URL}/proactive/read/${messageId}`,
        {},
        {
          headers: {
            Authorization: `Bearer ${authToken}`,
          },
        }
      );
      
      // Update local state
      const { unreadMessages } = get();
      const updatedMessages = unreadMessages.map(group => ({
        ...group,
        messages: group.messages.filter(m => m.id !== messageId),
        unread_count: group.messages.filter(m => m.id !== messageId).length,
      })).filter(group => group.unread_count > 0);
      
      const totalUnread = updatedMessages.reduce(
        (sum, group) => sum + group.unread_count, 
        0
      );
      
      set({ 
        unreadMessages: updatedMessages, 
        unreadCount: totalUnread 
      });
      
      return true;
    } catch (error) {
      console.error('Failed to mark message as read:', error);
      return false;
    }
  },

  // Mark all messages for a companion as read
  markAllForCompanionAsRead: async (companionId: string, authToken: string | null) => {
    if (!authToken) return;
    
    const { unreadMessages, getUnreadForCompanion } = get();
    const messagesToMark = getUnreadForCompanion(companionId);
    
    // Mark each message as read
    await Promise.all(
      messagesToMark.map(msg => get().markAsRead(msg.id, authToken))
    );
  },

  // Poll for new unread messages (called every 5 minutes)
  pollUnread: async (authToken: string | null) => {
    if (!authToken) return;
    
    const { lastFetchedAt } = get();
    
    // Only poll if we haven't fetched recently (within last 4 minutes)
    if (lastFetchedAt && Date.now() - lastFetchedAt < 4 * 60 * 1000) {
      return;
    }
    
    await get().fetchUnread(authToken);
  },

  // Get unread messages for a specific companion
  getUnreadForCompanion: (companionId: string) => {
    const { unreadMessages } = get();
    const group = unreadMessages.find(g => g.companion_id === companionId);
    return group?.messages || [];
  },

  // Get new messages since a specific timestamp (for toast notifications)
  getNewMessagesSince: (timestamp: number) => {
    const { unreadMessages } = get();
    const newMessages: ProactiveMessage[] = [];
    
    unreadMessages.forEach(group => {
      group.messages.forEach(msg => {
        const msgTime = new Date(msg.sent_at).getTime();
        if (msgTime > timestamp) {
          newMessages.push(msg);
        }
      });
    });
    
    return newMessages;
  },
}));

export default useProactiveStore;