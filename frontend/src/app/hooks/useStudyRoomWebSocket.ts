import { useEffect, useRef, useCallback } from "react";
import { useStore } from "../store";
import { API_BASE_URL } from "../services/studyRoomService";

export interface RoomMessage {
  id: string;
  room_id: string;
  sender_id: string;
  content: string;
  message_type: "text";
  is_read: boolean;
  read_at: string | null;
  created_at: string;
}

export interface WSMessage {
  type: "connected" | "disconnected" | "message_sent" | "new_message" | "message_read" | "room_ended" | "user_joined" | "user_left" | "error";
  room_id?: string;
  user_id?: string;
  reason?: string;
  message?: RoomMessage;
  participants?: string[];
}

interface UseStudyRoomWebSocketOptions {
  roomId: string;
  onMessage: (message: RoomMessage) => void;
  onConnected: () => void;
  onDisconnected: () => void;
  onRoomEnded: () => void;
  onUserJoined?: (userIds: string[]) => void;
  onUserLeft?: (userIds: string[]) => void;
}

export function useStudyRoomWebSocket({
  roomId,
  onMessage,
  onConnected,
  onDisconnected,
  onRoomEnded,
  onUserJoined,
  onUserLeft,
}: UseStudyRoomWebSocketOptions) {
  const { authToken } = useStore();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(async () => {
    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Build WebSocket URL with authentication
    const wsUrl = `${API_BASE_URL.replace("http://", "ws://").replace("https://", "wss://")}/api/study-buddy/ws/rooms/${roomId}?token=${encodeURIComponent(authToken || '')}`;

    try {
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log(`[Study Room WS] Connected to room: ${roomId}`);
        reconnectAttemptsRef.current = 0;
        onConnected?.();
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data: WSMessage = JSON.parse(event.data);
          console.log(`[Study Room WS] Received message:`, data);

          switch (data.type) {
            case "connected":
              console.log(`[Study Room WS] Connected to room: ${data.room_id}`);
              onConnected?.();
              break;

            case "disconnected":
              console.log(`[Study Room WS] Disconnected:`, data.reason);
              onDisconnected?.();
              break;

            case "new_message":
              if (data.message) {
                onMessage?.(data.message);
              }
              break;

            case "message_sent":
              console.log(`[Study Room WS] Message sent successfully`);
              break;

            case "room_ended":
              console.log(`[Study Room WS] Room ended`);
              onRoomEnded?.();
              break;

            case "user_joined":
              if (data.user_id && onUserJoined) {
                onUserJoined([data.user_id]);
              }
              break;

            case "user_left":
              if (data.user_id && onUserLeft) {
                onUserLeft([data.user_id]);
              }
              break;

            case "error":
              console.error(`[Study Room WS] Error:`, data.error);
              break;

            default:
              console.warn(`[Study Room WS] Unknown message type:`, data.type);
          }
        } catch (error) {
          console.error("[Study Room WS] Error parsing message:", error);
        }
      };

      wsRef.current.onclose = (event) => {
        console.log(`[Study Room WS] Disconnected:`, event.code, event.reason);
        onDisconnected?.();

        // Attempt reconnection
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          console.log(`[Study Room WS] Attempting reconnection (${reconnectAttemptsRef.current + 1}/${maxReconnectAttempts})...`);
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current += 1;
            connect();
          }, 1000 * reconnectAttemptsRef.current); // Exponential backoff
        } else {
          console.log(`[Study Room WS] Max reconnection attempts reached`);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error("[Study Room WS] Error:", error);
      };
    } catch (error) {
      console.error("[Study Room WS] Failed to connect:", error);
      onDisconnected?.();
    }
  }, [roomId, authToken, onMessage, onConnected, onDisconnected, onRoomEnded, onUserJoined, onUserLeft]);

  const sendMessage = useCallback((content: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.error("[Study Room WS] Not connected");
      return false;
    }

    try {
      wsRef.current.send(JSON.stringify({
        type: "send_message",
        content: content,
      }));
      return true;
    } catch (error) {
      console.error("[Study Room WS] Error sending message:", error);
      return false;
    }
  }, []);

  const leaveRoom = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.send(JSON.stringify({
        type: "leave_room",
      }));
    }
  }, []);

  useEffect(() => {
    if (!authToken || !roomId) {
      return;
    }

    // Connect to conversation
    connect();

    // Cleanup on unmount
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };
  }, [authToken, roomId, connect]);

  return {
    connect,
    sendMessage,
    leaveRoom,
    isConnected: wsRef.current?.readyState === WebSocket.OPEN,
  };
}
