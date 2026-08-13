import { useState } from "react";
import StudyRoomList from "../components/StudyRoomList";
import StudyRoomChat from "../components/StudyRoomChat";
import { StudyRoom } from "../services/studyRoomService";
import { motion, AnimatePresence } from "motion/react";

export default function StudyRoomPage() {
  const [activeRoom, setActiveRoom] = useState<StudyRoom | null>(null);

  return (
    <div className="flex h-full overflow-hidden bg-zinc-950">
      <AnimatePresence mode="wait">
        {!activeRoom ? (
          <motion.div
            key="list"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="w-full h-full"
          >
            <StudyRoomList onSelectRoom={(room) => setActiveRoom(room)} />
          </motion.div>
        ) : (
          <motion.div
            key="chat"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="w-full h-full"
          >
            <StudyRoomChat 
              room={activeRoom} 
              onBack={() => setActiveRoom(null)} 
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
