import { useEffect, useRef, useCallback } from "react";
import { useStore } from "../store";
import { API_BASE_URL } from "../services/studyBuddyService";

export interface Message {
  id: string;
  conversation_id: string;
  sender_id: string;
  content: string;
  message_type: "text";
  is_read: boolean;
  read_at: string | null;
  created_at: string;
}

export interface Conversation {
  conversation_id: string;
  other_user_id: string;
  other_user_name: string;
  other_user_email: string;
  created_at: string;
  updated_at: string;
}

export interface WSMessage {
  type: "connected" | "disconnected" | "message_sent" | "new_message" | "message_read" | "error";
  conversation_id?: string;
  user_id?: string;
  reason?: string;
  message?: Message;
  error?: string;
}

interface UseStudyBuddyWebSocketOptions {
  conversationId: string;
  onMessage?: (message: Message) => void;
  onConnected?: () => void;
  onDisconnected?: () => void;
}

export function useStudyBuddyWebSocket({
  conversationId,
  onMessage,
  onConnected,
  onDisconnected,
}: UseStudyBuddyWebSocketOptions) {
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
    const wsUrl = `${API_BASE_URL.replace("http://", "ws://").replace("https://", "wss://")}/api/study-buddy/ws?conversation_id=${conversationId}&token=${encodeURIComponent(authToken || '')}`;

    try {
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log(`[Study Buddy WS] Connected to conversation: ${conversationId}`);
        reconnectAttemptsRef.current = 0;
        onConnected?.();
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data: WSMessage = JSON.parse(event.data);
          console.log(`[Study Buddy WS] Received message:`, data);

          switch (data.type) {
            case "connected":
              console.log(`[Study Buddy WS] Connected to conversation: ${data.conversation_id}`);
              onConnected?.();
              break;

            case "disconnected":
              console.log(`[Study Buddy WS] Disconnected:`, data.reason);
              onDisconnected?.();
              break;

            case "new_message":
              if (data.message) {
                onMessage?.(data.message);
              }
              break;

            case "error":
              console.error(`[Study Buddy WS] Error:`, data.error);
              break;

            default:
              console.warn(`[Study Buddy WS] Unknown message type:`, data.type);
          }
        } catch (error) {
          console.error("[Study Buddy WS] Error parsing message:", error);
        }
      };

      wsRef.current.onclose = (event) => {
        console.log(`[Study Buddy WS] Disconnected:`, event.code, event.reason);
        onDisconnected?.();

        // Attempt reconnection
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          console.log(`[Study Buddy WS] Attempting reconnection (${reconnectAttemptsRef.current + 1}/${maxReconnectAttempts})...`);
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current += 1;
            connect();
          }, 1000 * reconnectAttemptsRef.current); // Exponential backoff
        } else {
          console.log(`[Study Buddy WS] Max reconnection attempts reached`);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error("[Study Buddy WS] Error:", error);
      };
    } catch (error) {
      console.error("[Study Buddy WS] Failed to connect:", error);
      onDisconnected?.();
    }
  }, [conversationId, onMessage, onConnected, onDisconnected]);

  const sendMessage = useCallback((content: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.error("[Study Buddy WS] Not connected");
      return false;
    }

    try {
      wsRef.current.send(JSON.stringify({
        type: "send_message",
        content: content,
      }));
      return true;
    } catch (error) {
      console.error("[Study Buddy WS] Error sending message:", error);
      return false;
    }
  }, []);

  const leaveConversation = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.send(JSON.stringify({
        type: "leave_conversation",
      }));
    }
  }, []);

  useEffect(() => {
    if (!authToken || !conversationId) {
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
  }, [authToken, conversationId, connect]);

  return {
    connect,
    sendMessage,
    leaveConversation,
    isConnected: wsRef.current?.readyState === WebSocket.OPEN,
  };
}
