import { useStore } from '../store';

export interface StudyBuddyProfile {
  id: string;
  user_id: string;
  country: string;
  city: string;
  campus_university: string;
  major: string;
  academic_year: string;
  strong_subjects: string[];
  weak_subjects: string[];
  bio?: string;
  avatar_id?: string;
  is_online: boolean;
  last_active?: string;
  created_at: string;
  updated_at: string;
}

export interface MatchReason {
  reason: 'strong_weak' | 'same_campus' | 'same_major' | 'same_year' | 'related_subjects';
  description: string;
}

export interface StudyBuddyMatch {
  user_id: string;
  full_name: string;
  email: string;
  avatar_url?: string;
  compatibility_score: number;
  match_reasons: MatchReason[];
  strong_subjects_overlap: string[];
  weak_subjects_help: string[];
  // Public profile information
  country: string;
  city: string;
  campus_university: string;
  major: string;
  academic_year: string;
  strong_subjects: string[];
  weak_subjects: string[];
  // Connection state
  connectionState?: 'not_connected' | 'sending' | 'sent' | 'error';
}

export interface MatchResponse {
  matches: StudyBuddyMatch[];
  total_matches: number;
}

export interface ConnectionRequest {
  id: string;
  sender_id: string;
  recipient_id: string;
  status: 'pending' | 'accepted' | 'rejected' | 'cancelled';
  message?: string;
  sender_full_name: string;
  sender_avatar_url?: string;
  created_at: string;
}

export interface Connection {
  id: string;
  user_id: string;
  full_name: string;
  avatar_url?: string;
  country: string;
  city: string;
  campus_university: string;
  major: string;
  academic_year: string;
  is_online: boolean;
}

export interface Conversation {
  conversation_id: string;
  other_user_id: string;
  other_user_name: string;
  other_user_email: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  sender_id: string;
  content: string;
  message_type: 'text';
  is_read: boolean;
  read_at: string | null;
  created_at: string;
}

export interface ConversationMessagesResponse {
  messages: Message[];
  meta: {
    page: number;
    per_page: number;
    total: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

export interface ConversationsResponse {
  conversations: Conversation[];
  meta: {
    page: number;
    per_page: number;
    total: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

export const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL ?? 'http://localhost:8000';

export const studyBuddyService = {
  // Profile
  async getProfile(): Promise<StudyBuddyProfile> {
    const token = useStore.getState().authToken;
    const response = await fetch(`${API_BASE_URL}/api/study-buddy/profile`, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    });
    const data = await response.json();
    if (!data.success) {
      const errorMessage = data.detail?.message || data.message || 'Failed to get profile';
      throw new Error(errorMessage);
    }
    return data.data;
  },

  async createProfile(data: Partial<StudyBuddyProfile>): Promise<StudyBuddyProfile> {
    const token = useStore.getState().authToken;
    const response = await fetch(`${API_BASE_URL}/api/study-buddy/profile`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    const result = await response.json();
    if (!result.success) {
      const errorMessage = result.detail?.message || result.message || 'Failed to create profile';
      throw new Error(errorMessage);
    }
    return result.data;
  },

  async updateProfile(data: Partial<StudyBuddyProfile>): Promise<StudyBuddyProfile> {
    const token = useStore.getState().authToken;
    const response = await fetch(`${API_BASE_URL}/api/study-buddy/profile`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    const result = await response.json();
    if (!result.success) {
      const errorMessage = result.detail?.message || result.message || 'Failed to update profile';
      throw new Error(errorMessage);
    }
    return result.data;
  },

  // Matching
  async findMatches(limit: number = 20): Promise<MatchResponse> {
    const token = useStore.getState().authToken;
    const response = await fetch(`${API_BASE_URL}/api/study-buddy/match?limit=${limit}`, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.message || 'Failed to find matches');
    }
    return data.data;
  },

  // Connections
  async sendConnectionRequest(
    recipientId: string,
    message?: string
  ): Promise<ConnectionRequest> {
    const token = useStore.getState().authToken;
    const tokenExists = !!token;

    console.log('=== SEND REQUEST FETCH ===');
    console.log('endpoint:', `${API_BASE_URL}/api/study-buddy/request/send`);
    console.log('recipientId:', recipientId);
    console.log('message:', message);
    console.log('current auth token exists:', tokenExists);

    const response = await fetch(`${API_BASE_URL}/api/study-buddy/request/send`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ recipient_id: recipientId, message }),
    });

    console.log('=== SEND REQUEST RESPONSE ===');
    console.log('HTTP status:', response.status);
    console.log('HTTP statusText:', response.statusText);

    const result = await response.json();
    console.log('=== SEND REQUEST BODY ===');
    console.log('HTTP status:', response.status);
    console.log('HTTP statusText:', response.statusText);
    console.log('complete response body (stringified):', JSON.stringify(result, null, 2));
    console.log('complete response body (object):', result);
    console.log('result.success:', result.success);
    console.log('result.message:', result.message);
    console.log('result.detail:', result.detail);
    console.log('result.data:', result.data);
    console.log('result.error:', result.error);

    if (!result.success) {
      console.log('=== SEND REQUEST ERROR ===');
      console.log('response body (stringified):', JSON.stringify(result, null, 2));
      console.log('HTTP status:', response.status);
      console.log('Error message:', result.message);
      console.log('Error detail:', result.detail);
      console.log('Error object:', result);
      throw new Error(result.message || result.detail?.message || 'Failed to send connection request');
    }
    return result.data;
  },

  async getPendingRequests(): Promise<ConnectionRequest[]> {
    const token = useStore.getState().authToken;
    const response = await fetch(`${API_BASE_URL}/api/study-buddy/request/pending`, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.message || 'Failed to get pending requests');
    }
    return data.data;
  },

  async respondToRequest(requestId: string, action: 'accept' | 'reject'): Promise<ConnectionRequest> {
    const token = useStore.getState().authToken;
    const response = await fetch(
      `${API_BASE_URL}/api/study-buddy/request/respond?request_id=${requestId}&action=${action}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      }
    );
    const result = await response.json();
    if (!result.success) {
      throw new Error(result.message || 'Failed to respond to request');
    }
    return result.data;
  },

  async getConnections(): Promise<Connection[]> {
    const token = useStore.getState().authToken;
    const response = await fetch(`${API_BASE_URL}/api/study-buddy/connections`, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.message || 'Failed to get connections');
    }
    return data.data;
  },

  // Conversations
  async getConversations(page: number = 1, perPage: number = 50): Promise<ConversationsResponse> {
    const token = useStore.getState().authToken;
    const response = await fetch(`${API_BASE_URL}/api/study-buddy/conversations?page=${page}&per_page=${perPage}`, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.message || 'Failed to get conversations');
    }
    
    // Map backend 'id' to 'conversation_id'
    const conversations = data.data.conversations.map((conv: any) => ({
      ...conv,
      conversation_id: conv.id || conv.conversation_id
    }));
    
    return {
      ...data.data,
      conversations
    };
  },

  async getConversation(conversationId: string): Promise<Conversation> {
    const token = useStore.getState().authToken;
    const response = await fetch(`${API_BASE_URL}/api/study-buddy/conversations/${conversationId}`, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.message || 'Failed to get conversation');
    }
    
    return {
      ...data.data,
      conversation_id: data.data.id || data.data.conversation_id
    };
  },

  async createConversation(otherUserId: string): Promise<Conversation> {
    const token = useStore.getState().authToken;
    const response = await fetch(`${API_BASE_URL}/api/study-buddy/conversations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ other_user_id: otherUserId }),
    });
    const result = await response.json();
    if (!result.success) {
      throw new Error(result.message || 'Failed to create conversation');
    }
    
    return {
      ...result.data,
      conversation_id: result.data.id || result.data.conversation_id
    };
  },

  // Messages
  async getMessages(conversationId: string, page: number = 1, perPage: number = 50): Promise<ConversationMessagesResponse> {
    const token = useStore.getState().authToken;
    const response = await fetch(`${API_BASE_URL}/api/study-buddy/conversations/${conversationId}/messages?page=${page}&per_page=${perPage}`, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.message || 'Failed to get messages');
    }
    return data.data;
  },

  async sendMessage(conversationId: string, content: string): Promise<Message> {
    const token = useStore.getState().authToken;
    const response = await fetch(`${API_BASE_URL}/api/study-buddy/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        conversation_id: conversationId,
        content: content,
      }),
    });
    const result = await response.json();
    if (!result.success) {
      throw new Error(result.message || 'Failed to send message');
    }
    return result.data;
  },

  async markAsRead(conversationId: string): Promise<number> {
    const token = useStore.getState().authToken;
    const response = await fetch(`${API_BASE_URL}/api/study-buddy/conversations/${conversationId}/read`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.message || 'Failed to mark as read');
    }
    return data.data.messages_read;
  },

  async deleteConversation(conversationId: string): Promise<void> {
    const token = useStore.getState().authToken;
    const response = await fetch(`${API_BASE_URL}/api/study-buddy/conversations/${conversationId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    });
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.message || 'Failed to delete conversation');
    }
  },

  async cancelConnectionRequest(requestId: string): Promise<ConnectionRequest> {
    const token = useStore.getState().authToken;
    const response = await fetch(`${API_BASE_URL}/api/study-buddy/request/cancel?request_id=${requestId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    });
    const result = await response.json();
    if (!result.success) {
      throw new Error(result.message || 'Failed to cancel connection request');
    }
    return result.data;
  },
};
