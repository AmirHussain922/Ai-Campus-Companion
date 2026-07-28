import { useEffect, useState, useCallback } from "react";
import axios from "axios";

const API_BASE_URL =
  ((import.meta as any).env?.VITE_API_BASE_URL ?? "http://localhost:8000") +
  "/api";

export interface ProactiveMessage {
  id: string;
  companion_id: string;
  trigger_type:
    | "good_morning"
    | "miss_you"
    | "milestone_congrats"
    | "quest_reminder"
    | "story_nudge";
  content: string;
  sent_at: string;
  is_read: boolean;
}

export interface ChatMessage {
  id: string;
  companionId: string;
  sender: "user" | "companion" | "system";
  text: string;
  timestamp: number;
  feedback?: -1 | 1;
  isProactive?: boolean;
  triggerType?: string;
}

export function useProactiveMessages(
  companionId: string | undefined,
  authToken: string | null
) {
  const [proactiveMessages, setProactiveMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchProactiveHistory = useCallback(async () => {
    if (!companionId || !authToken) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await axios.get(
        `${API_BASE_URL}/proactive/history/${companionId}?page=1&per_page=50`,
        {
          headers: {
            Authorization: `Bearer ${authToken}`,
          },
        }
      );

      const historyData = response.data;
      const messages: ChatMessage[] = historyData.messages.map(
        (msg: ProactiveMessage) => ({
          id: `proactive-${msg.id}`,
          companionId: msg.companion_id,
          sender: "companion",
          text: msg.content,
          timestamp: new Date(msg.sent_at).getTime(),
          isProactive: true,
          triggerType: msg.trigger_type,
        })
      );

      // Sort by timestamp (oldest first to blend into chat history)
      messages.sort((a, b) => a.timestamp - b.timestamp);

      setProactiveMessages(messages);
    } catch (err) {
      console.error("Failed to fetch proactive message history:", err);
      setError("Failed to load message history");
    } finally {
      setIsLoading(false);
    }
  }, [companionId, authToken]);

  // Fetch proactive messages when companionId or authToken changes
  useEffect(() => {
    fetchProactiveHistory();
  }, [fetchProactiveHistory]);

  // Merge proactive messages with regular messages
  const mergeWithMessages = useCallback(
    (regularMessages: ChatMessage[]): ChatMessage[] => {
      if (proactiveMessages.length === 0) return regularMessages;

      // Combine both arrays
      const combined = [...regularMessages, ...proactiveMessages];

      // Remove duplicates (in case a proactive message was already added to the store)
      const seen = new Set<string>();
      const unique = combined.filter((msg) => {
        if (seen.has(msg.id)) return false;
        seen.add(msg.id);
        return true;
      });

      // Sort by timestamp (oldest first)
      unique.sort((a, b) => a.timestamp - b.timestamp);

      return unique;
    },
    [proactiveMessages]
  );

  return {
    proactiveMessages,
    isLoading,
    error,
    fetchProactiveHistory,
    mergeWithMessages,
  };
}
