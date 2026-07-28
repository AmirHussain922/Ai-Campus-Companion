import { create } from 'zustand';
import axios from 'axios';

const API_BASE_URL = ((import.meta as any).env?.VITE_API_BASE_URL ?? 'http://localhost:8000') + '/api';

export type GroupChatSenderType = 'user' | 'companion';

export interface GroupChatMessage {
  id: string;
  content: string;
  sender_type: GroupChatSenderType;
  sender_id: string;
  sender_name: string;
  sender_avatar?: string;
  sender_color: 'purple' | 'red' | 'emerald' | 'pink' | 'amber';
  timestamp: string;
  is_edited?: boolean;
  reply_to_id?: string;
  reply_to_preview?: string;
}

interface GroupChatState {
  // State
  messages: GroupChatMessage[];
  isLoading: boolean;
  isSending: boolean;
  error: string | null;
  hasMore: boolean;
  lastFetchedAt: number | null;
  unreadCount: number;
  isTyping: boolean;
  typingCompanions: string[];
  
  // Actions
  fetchMessages: (limit?: number, before?: string, authToken?: string | null) => Promise<void>;
  sendMessage: (content: string, replyToId?: string, authToken?: string | null) => Promise<boolean>;
  receiveMessage: (message: GroupChatMessage) => void;
  markAsRead: () => void;
  setTyping: (isTyping: boolean, companionName?: string) => void;
  clearError: () => void;
  reset: () => void;
}

const initialState = {
  messages: [],
  isLoading: false,
  isSending: false,
  error: null,
  hasMore: true,
  lastFetchedAt: null,
  unreadCount: 0,
  isTyping: false,
  typingCompanions: []
};

export const useGroupChatStore = create<GroupChatState>((set, get) => ({
  ...initialState,

  fetchMessages: async (limit: number = 50, before?: string, authToken?: string | null) => {
    if (!authToken) {
      set({ error: 'No authentication token' });
      return;
    }

    set({ isLoading: true, error: null });

    try {
      const params = new URLSearchParams({ limit: limit.toString() });
      if (before) params.append('before', before);

      const response = await axios.get(`${API_BASE_URL}/group-chat/messages?${params}`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });

      const newMessages = response.data.messages || [];
      const hasMore = newMessages.length === limit;

      set(state => ({
        messages: before ? [...state.messages, ...newMessages] : newMessages,
        hasMore,
        lastFetchedAt: Date.now()
      }));
    } catch (error) {
      console.error('Failed to fetch group chat messages:', error);
      set({ error: 'Failed to fetch messages' });
    } finally {
      set({ isLoading: false });
    }
  },

  sendMessage: async (content: string, replyToId?: string, authToken?: string | null): Promise<boolean> => {
    if (!authToken || !content.trim()) return false;

    set({ isSending: true, error: null });

    try {
      const response = await axios.post(
        `${API_BASE_URL}/group-chat/messages`,
        { content: content.trim(), reply_to_id: replyToId },
        { headers: { Authorization: `Bearer ${authToken}` } }
      );

      if (response.data.success) {
        // Add user message
        if (response.data.user_message) {
          get().receiveMessage(response.data.user_message);
        }
        // Add companion replies with a small delay for a more natural feel
        if (response.data.companion_replies && response.data.companion_replies.length > 0) {
          // Set typing indicator first
          set({ 
            isTyping: true, 
            typingCompanions: response.data.companion_replies.map((r: any) => {
              // Map companion_id to name
              const companionNames: Record<string, string> = {
                study_buddy: 'Oliver',
                party_friend: 'Chloe',
                philosopher: 'Julian',
                rival: 'Victoria',
                freshman: 'Toby'
              };
              return companionNames[r.companion_id] || 'Companion';
            }) 
          });
          
          // Add replies one by one after a short delay
          for (let i = 0; i < response.data.companion_replies.length; i++) {
            await new Promise(resolve => setTimeout(resolve, 800 + i * 600));
            get().receiveMessage(response.data.companion_replies[i]);
          }
          
          // Clear typing indicator
          set({ isTyping: false, typingCompanions: [] });
        }
        return true;
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      set({ error: 'Failed to send message', isTyping: false, typingCompanions: [] });
    } finally {
      set({ isSending: false });
    }
    return false;
  },

  receiveMessage: (message: GroupChatMessage) => {
    set(state => {
      // Avoid duplicates
      if (state.messages.some(m => m.id === message.id)) {
        return state;
      }
      
      const isUserMessage = message.sender_type === 'user';
      
      return {
        messages: [...state.messages, message],
        unreadCount: isUserMessage ? state.unreadCount : state.unreadCount + 1
      };
    });
  },

  markAsRead: () => {
    set({ unreadCount: 0 });
  },

  setTyping: (isTyping: boolean, companionName?: string) => {
    set(state => {
      let typingCompanions = [...state.typingCompanions];
      
      if (companionName) {
        if (isTyping && !typingCompanions.includes(companionName)) {
          typingCompanions.push(companionName);
        } else if (!isTyping) {
          typingCompanions = typingCompanions.filter(name => name !== companionName);
        }
      }
      
      return {
        isTyping: typingCompanions.length > 0,
        typingCompanions
      };
    });
  },

  clearError: () => set({ error: null }),
  
  reset: () => set(initialState)
}));

export default useGroupChatStore;
