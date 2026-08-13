export const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL ?? 'http://localhost:8000';

export interface StudyRoom {
  id: string;
  host_id: string;
  host_full_name: string;
  major: string;
  subject: string;
  title: string;
  description: string | null;
  status: "active" | "ended";
  participant_ids: string[];
  participant_count: number;
  max_participants: number;
  created_at: string;
  started_at: string | null;
  ended_at: string | null;
}

export interface StudyRoomParticipant {
  id: string;
  user_id: string;
  full_name: string;
  joined_at: string;
}

export const studyRoomService = {
  // Get active study rooms
  async getActiveRooms(page: number = 1, perPage: number = 50): Promise<{
    rooms: StudyRoom[];
    meta: {
      page: number;
      per_page: number;
      total: number;
      total_pages: number;
      has_next: boolean;
      has_prev: boolean;
    };
  }> {
    const response = await fetch(
      `${API_BASE_URL}/api/study-buddy/study-rooms/active?page=${page}&per_page=${perPage}`,
      {
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${localStorage.getItem("token")}`,
        },
      }
    );

    const data = await response.json();
    if (!response.ok || !data.success) {
      throw new Error(data.message || "Failed to load study rooms");
    }

    return data.data;
  },

  // Create a new study room
  async createRoom(data: {
    major: string;
    subject: string;
    title: string;
    description?: string;
  }): Promise<StudyRoom> {
    const response = await fetch(`${API_BASE_URL}/api/study-buddy/study-rooms`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${localStorage.getItem("token")}`,
      },
      body: JSON.stringify(data),
    });

    const result = await response.json();
    if (!response.ok || !result.success) {
      throw new Error(result.message || "Failed to create room");
    }

    return result.data;
  },

  // Join a study room
  async joinRoom(roomId: string): Promise<StudyRoomParticipant> {
    const response = await fetch(`${API_BASE_URL}/api/study-buddy/study-rooms/${roomId}/join`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${localStorage.getItem("token")}`,
      },
      body: JSON.stringify({ room_id: roomId }),
    });

    const result = await response.json();
    if (!response.ok || !result.success) {
      throw new Error(result.message || "Failed to join room");
    }

    return result.data;
  },

  // Leave a study room
  async leaveRoom(roomId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/study-buddy/study-rooms/${roomId}/leave`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${localStorage.getItem("token")}`,
      },
    });

    const result = await response.json();
    if (!response.ok || !result.success) {
      throw new Error(result.message || "Failed to leave room");
    }
  },

  // End a study room (host only)
  async endRoom(roomId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/study-buddy/study-rooms/${roomId}/end`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${localStorage.getItem("token")}`,
      },
    });

    const result = await response.json();
    if (!response.ok || !result.success) {
      throw new Error(result.message || "Failed to end room");
    }
  },

  // Get room details
  async getRoom(roomId: string): Promise<StudyRoom> {
    const response = await fetch(`${API_BASE_URL}/api/study-buddy/study-rooms/${roomId}`, {
      headers: {
        "Authorization": `Bearer ${localStorage.getItem("token")}`,
      },
    });

    const data = await response.json();
    if (!response.ok || !data.success) {
      throw new Error(data.message || "Failed to get room");
    }

    return data.data;
  },

  // Get room messages
  async getRoomMessages(
    roomId: string,
    page: number = 1,
    perPage: number = 50
  ): Promise<{
    messages: any[];
    meta: {
      page: number;
      per_page: number;
      total: number;
      total_pages: number;
      has_next: boolean;
      has_prev: boolean;
    };
  }> {
    const response = await fetch(
      `${API_BASE_URL}/api/study-buddy/study-rooms/${roomId}/messages?page=${page}&per_page=${perPage}`,
      {
        headers: {
          "Authorization": `Bearer ${localStorage.getItem("token")}`,
        },
      }
    );

    const data = await response.json();
    if (!response.ok || !data.success) {
      throw new Error(data.message || "Failed to load room messages");
    }

    return data.data;
  },

  // Send message to room
  async sendRoomMessage(roomId: string, content: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/study-buddy/study-rooms/${roomId}/messages`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${localStorage.getItem("token")}`,
      },
      body: JSON.stringify({ content }),
    });

    const result = await response.json();
    if (!response.ok || !result.success) {
      throw new Error(result.message || "Failed to send message");
    }

    return result.data;
  },
};
