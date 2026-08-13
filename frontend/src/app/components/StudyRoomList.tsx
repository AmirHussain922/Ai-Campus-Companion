import { useState, useEffect } from "react";
import { motion } from "motion/react";
import { Users, BookOpen, Calendar, Plus, X } from "lucide-react";
import { useStore } from "../store";
import { studyRoomService, StudyRoom } from "../services/studyRoomService";
import { cn } from "../utils";
import { Button } from "./ui/button";
import { Card } from "./ui/card";

interface StudyRoomListProps {
  onSelectRoom: (room: StudyRoom) => void;
}

export default function StudyRoomList({ onSelectRoom }: StudyRoomListProps) {
  const user = useStore(state => state.user);
  const [rooms, setRooms] = useState<StudyRoom[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newRoom, setNewRoom] = useState({
    title: "",
    subject: "",
    major: "",
    description: ""
  });
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (!user) {
      setError("Please log in to view study rooms");
      return;
    }
    loadRooms();
  }, [user]);

  const loadRooms = async () => {
    try {
      setLoading(true);
      setError("");
      const data = await studyRoomService.getActiveRooms();
      setRooms(data.rooms);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load rooms");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRoom = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRoom.title || !newRoom.subject || !newRoom.major) return;

    try {
      setCreating(true);
      const room = await studyRoomService.createRoom(newRoom);
      setShowCreateModal(false);
      setNewRoom({ title: "", subject: "", major: "", description: "" });
      loadRooms();
      onSelectRoom(room);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create room");
    } finally {
      setCreating(false);
    }
  };

  const handleJoinRoom = async (room: StudyRoom) => {
    try {
      if (room.participant_ids.includes(user?.id || "")) {
        onSelectRoom(room);
        return;
      }
      
      if (room.participant_count >= room.max_participants) {
        alert("Room is full");
        return;
      }

      await studyRoomService.joinRoom(room.id);
      onSelectRoom(room);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to join room");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="flex items-center gap-2 text-zinc-500">
          <Users className="w-5 h-5 animate-spin" />
          Loading study rooms...
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-zinc-900/50 border-r border-zinc-800">
      {/* Header */}
      <div className="p-4 border-b border-zinc-800">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-medium flex items-center gap-2">
            <Users className="w-5 h-5" />
            Study Rooms
          </h2>
          <Button
            onClick={() => setShowCreateModal(true)}
            variant="ghost"
            size="sm"
            className="gap-2"
          >
            <Plus className="w-4 h-4" />
            Create
          </Button>
        </div>
      </div>

      {/* Room List */}
      <div className="flex-1 overflow-y-auto">
        {rooms.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full p-8 text-center">
            <Users className="w-12 h-12 mb-3 text-zinc-600" />
            <h3 className="text-sm font-medium text-zinc-400 mb-1">
              No active study rooms
            </h3>
            <p className="text-xs text-zinc-500 mb-4">
              Create a study room to start collaborating
            </p>
            <Button
              onClick={() => setShowCreateModal(true)}
              variant="outline"
              size="sm"
              className="gap-2"
            >
              <Plus className="w-4 h-4" />
              Create Study Room
            </Button>
          </div>
        ) : (
          <div className="divide-y divide-zinc-800">
            {rooms.map((room) => (
              <motion.div
                key={room.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                onClick={() => handleJoinRoom(room)}
                className="p-4 hover:bg-zinc-800/50 cursor-pointer transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-full bg-blue-600/20 flex items-center justify-center flex-shrink-0">
                    <BookOpen className="w-5 h-5 text-blue-400" />
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <h3 className="font-medium text-sm truncate">
                        {room.title}
                      </h3>
                      <span className="text-xs text-zinc-500 flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {new Date(room.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <p className="text-xs text-zinc-400 mb-2">
                      {room.subject} • {room.major}
                    </p>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-xs text-zinc-500">
                        <Users className="w-3 h-3" />
                        <span>
                          {room.participant_count} / {room.max_participants} participants
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* Create Room Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="w-full max-w-md bg-zinc-900 border border-zinc-800 rounded-2xl p-6 shadow-2xl"
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold">Create Study Room</h2>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setShowCreateModal(false)}
                className="text-zinc-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </Button>
            </div>

            <form onSubmit={handleCreateRoom} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-1.5">
                  Title
                </label>
                <input
                  type="text"
                  required
                  value={newRoom.title}
                  onChange={(e) => setNewRoom({ ...newRoom, title: e.target.value })}
                  placeholder="E.g., Midterm Prep Session"
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-zinc-400 mb-1.5">
                    Subject
                  </label>
                  <input
                    type="text"
                    required
                    value={newRoom.subject}
                    onChange={(e) => setNewRoom({ ...newRoom, subject: e.target.value })}
                    placeholder="E.g., Calculus II"
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-zinc-400 mb-1.5">
                    Major
                  </label>
                  <input
                    type="text"
                    required
                    value={newRoom.major}
                    onChange={(e) => setNewRoom({ ...newRoom, major: e.target.value })}
                    placeholder="E.g., CS"
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-1.5">
                  Description (Optional)
                </label>
                <textarea
                  value={newRoom.description}
                  onChange={(e) => setNewRoom({ ...newRoom, description: e.target.value })}
                  placeholder="What are we studying?"
                  rows={3}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 resize-none"
                />
              </div>

              <div className="pt-2">
                <Button
                  type="submit"
                  disabled={creating || !newRoom.title || !newRoom.subject || !newRoom.major}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2"
                >
                  {creating ? "Creating..." : "Create Room"}
                </Button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  );
}
