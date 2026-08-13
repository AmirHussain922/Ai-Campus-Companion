import { motion } from "motion/react";
import { Link } from "react-router";
import { MessageSquare, Users, BookOpen, ChevronRight } from "lucide-react";
import { useStore } from "../store";
import { companionColorClasses, cn } from "../utils";

export default function Dashboard() {
  const user = useStore(state => state.user);
  const myCompanions = useStore(state => state.myCompanions);

  return (
    <div className="flex-1 overflow-y-auto bg-zinc-950 p-4 sm:p-6 md:p-8 text-zinc-50 relative h-full">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <header className="mb-8 sm:mb-12 flex flex-col sm:flex-row sm:justify-between sm:items-end gap-4">
          <div>
            <h1 className="text-3xl sm:text-4xl font-light tracking-tighter mb-2">
              Welcome back, {user?.name.split(' ')[0] || 'Student'}
            </h1>
            <p className="text-zinc-400 text-sm sm:text-base">Here's your campus activity summary.</p>
          </div>
          
          <div className="flex gap-4">
            <div className="px-4 py-2 bg-zinc-900 rounded-full border border-zinc-800 text-xs sm:text-sm font-medium flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              Online
            </div>
          </div>
        </header>

        {myCompanions.length === 0 ? (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-center justify-center p-20 border border-dashed border-zinc-800 rounded-3xl bg-zinc-900/20 text-center"
          >
            <div className="w-16 h-16 rounded-full bg-zinc-800 flex items-center justify-center mb-6">
              <svg className="w-8 h-8 text-zinc-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </div>
            <h2 className="text-2xl font-medium mb-2">No Companions Yet</h2>
            <p className="text-zinc-400 max-w-md mx-auto mb-8">
              Start your journey by adding your first AI campus companion to chat, level up, and unlock stories.
            </p>
            <Link 
              to="/select"
              className="px-8 py-3 bg-white text-zinc-950 font-medium rounded-xl hover:bg-zinc-200 transition-colors"
            >
              Browse Companions
            </Link>
          </motion.div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left Column: Recent Companions */}
            <div className="lg:col-span-2 space-y-8">
              <section>
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-medium tracking-tight">Active Relationships</h2>
                  <Link to="/select" className="text-sm text-purple-400 hover:text-purple-300 transition-colors">
                    Add new
                  </Link>
                </div>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {myCompanions.map((comp, idx) => {
                    const colors = companionColorClasses[comp.color];
                    const progress = (comp.xp / comp.nextLevelXp) * 100;
                    
                    return (
                      <motion.div 
                        key={comp.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.1 }}
                        className={cn(
                          "group p-5 rounded-2xl bg-zinc-900/50 border border-zinc-800 relative overflow-hidden transition-all hover:border-zinc-700"
                        )}
                      >
                        <div className={cn("absolute inset-0 opacity-0 group-hover:opacity-10 transition-opacity duration-500 pointer-events-none", colors.bgLight)} />
                        
                        <div className="flex gap-4 items-center mb-4 relative z-10">
                          <img src={comp.avatarUrl} alt={comp.name} className="w-14 h-14 rounded-full object-cover ring-2 ring-zinc-800" />
                          <div className="flex-1">
                            <h3 className="font-semibold text-lg">{comp.name}</h3>
                            <p className="text-xs text-zinc-500">{comp.personality}</p>
                          </div>
                          <div className="text-right">
                            <div className={cn("text-xs font-bold px-2 py-1 rounded-md mb-1 inline-block", colors.bgLight, colors.text)}>
                              LVL {comp.level}
                            </div>
                          </div>
                        </div>

                        {/* XP Bar */}
                        <div className="mt-4 relative z-10">
                          <div className="flex justify-between text-xs mb-2">
                            <span className="text-zinc-400">Level Progress</span>
                            <span className="text-zinc-500">{comp.xp} / {comp.nextLevelXp} XP</span>
                          </div>
                          <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
                            <motion.div 
                              initial={{ width: 0 }}
                              animate={{ width: `${progress}%` }}
                              transition={{ duration: 1, ease: "easeOut" }}
                              className={cn("h-full rounded-full", colors.bg, colors.glow)}
                            />
                          </div>
                        </div>

                        <div className="mt-6 flex gap-2 relative z-10">
                          <Link 
                            to={`/app/chat/${comp.id}`}
                            className="flex-1 text-center py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm font-medium transition-colors"
                          >
                            Chat
                          </Link>
                          <Link 
                            to={`/app/profile/${comp.id}`}
                            className="flex-1 text-center py-2 bg-transparent border border-zinc-700 hover:border-zinc-500 rounded-lg text-sm font-medium transition-colors text-zinc-400 hover:text-white"
                          >
                            Profile
                          </Link>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              </section>

              {/* Story Unlocks Section */}
              <section>
                <h2 className="text-xl font-medium tracking-tight mb-6">Recent Story Milestones</h2>
                <div className="bg-zinc-900/30 border border-zinc-800 rounded-2xl p-6 space-y-6">
                  {myCompanions.flatMap(c => c.episodes.filter(e => e.unlocked).map(e => ({...e, compName: c.name, color: c.color})))
                    .sort((a, b) => b.unlockLevel - a.unlockLevel)
                    .slice(0, 3)
                    .map((episode, idx) => {
                      const colors = companionColorClasses[episode.color as keyof typeof companionColorClasses];
                      return (
                        <div key={idx} className="flex gap-4 items-start relative pb-6 last:pb-0 border-l-2 border-zinc-800 ml-3 pl-6">
                          <div className={cn("absolute -left-[5px] top-1.5 w-2 h-2 rounded-full ring-4 ring-zinc-950", colors.bg)} />
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <span className={cn("text-xs font-semibold uppercase tracking-wider", colors.text)}>
                                {episode.compName}
                              </span>
                              <span className="text-zinc-600 text-xs">• Episode {episode.unlockLevel}</span>
                            </div>
                            <h4 className="text-base font-medium text-zinc-200">{episode.title}</h4>
                            <p className="text-sm text-zinc-500 mt-1">{episode.description}</p>
                          </div>
                        </div>
                      );
                  })}
                  {myCompanions.length > 0 && myCompanions.every(c => !c.episodes.some(e => e.unlocked)) && (
                    <div className="text-zinc-500 text-sm py-4 text-center">
                      No story episodes unlocked yet. Chat with your companions to level up!
                    </div>
                  )}
                </div>
              </section>
            </div>

            {/* Right Column: Activity Summary & Stats */}
            <div className="space-y-6">
              <section className="bg-gradient-to-br from-zinc-900 to-zinc-900/50 border border-zinc-800 rounded-3xl p-6 relative overflow-hidden">
                <div className="absolute -top-10 -right-10 w-32 h-32 bg-purple-500/10 rounded-full blur-3xl" />
                <h3 className="text-sm font-medium text-zinc-400 uppercase tracking-wider mb-6">Global Progress</h3>
                
                <div className="space-y-6">
                  <div>
                    <div className="text-3xl font-light mb-1">
                      {myCompanions.reduce((acc, curr) => acc + curr.level, 0)}
                    </div>
                    <div className="text-xs text-zinc-500">Total Combined Levels</div>
                  </div>
                  
                  <div>
                    <div className="text-3xl font-light mb-1">
                      {myCompanions.reduce((acc, curr) => acc + curr.episodes.filter(e => e.unlocked).length, 0)}
                    </div>
                    <div className="text-xs text-zinc-500">Stories Unlocked</div>
                  </div>

                  <div>
                    <div className="text-3xl font-light mb-1">
                      {myCompanions.length}
                    </div>
                    <div className="text-xs text-zinc-500">Active Connections</div>
                  </div>
                </div>
              </section>

              <section className="bg-zinc-900/30 border border-zinc-800 rounded-3xl p-6">
                <h3 className="text-sm font-medium text-zinc-400 uppercase tracking-wider mb-4">Upcoming Unlocks</h3>
                <ul className="space-y-4">
                  {myCompanions.flatMap(c => c.episodes.filter(e => !e.unlocked).map(e => ({...e, compName: c.name, color: c.color, levelDiff: e.unlockLevel - c.level})))
                    .sort((a, b) => a.levelDiff - b.levelDiff)
                    .slice(0, 4)
                    .map((upcoming, idx) => {
                      const colors = companionColorClasses[upcoming.color as keyof typeof companionColorClasses];
                      return (
                        <li key={idx} className="flex justify-between items-center text-sm">
                          <div className="flex items-center gap-2">
                            <div className={cn("w-1.5 h-1.5 rounded-full", colors.bg)} />
                            <span className="text-zinc-300">{upcoming.compName}'s Story</span>
                          </div>
                          <span className="text-zinc-600 font-medium text-xs">Level {upcoming.unlockLevel}</span>
                        </li>
                      );
                  })}
                  {myCompanions.length === 0 && (
                     <div className="text-xs text-zinc-500 text-center">No upcoming unlocks</div>
                  )}
                </ul>
              </section>

              {/* Study Buddy Widget */}
              <section className="bg-gradient-to-br from-purple-900/20 to-zinc-900 border border-purple-800/50 rounded-3xl p-6 relative overflow-hidden">
                <div className="absolute -top-10 -right-10 w-32 h-32 bg-purple-500/10 rounded-full blur-3xl" />
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-medium text-zinc-400 uppercase tracking-wider">Study Buddies</h3>
                  <Link
                    to="/app/study-buddy/matches"
                    className="text-xs text-purple-400 hover:text-purple-300 transition-colors"
                  >
                    Find Matches
                  </Link>
                </div>

                <div className="space-y-3">
                  <Link
                    to="/app/qa"
                    className="block p-4 bg-zinc-900/50 border border-zinc-800 rounded-xl hover:border-purple-700 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-purple-600/20 flex items-center justify-center">
                        <MessageSquare className="w-5 h-5 text-purple-400" />
                      </div>
                      <div>
                        <div className="text-sm font-medium">Peer Q&A Forum</div>
                        <div className="text-xs text-zinc-500">Ask questions and help other students</div>
                      </div>
                      <ChevronRight className="w-4 h-4 ml-auto text-zinc-600" />
                    </div>
                  </Link>

                  <Link
                    to="/app/study-buddy/matches"
                    className="block p-4 bg-zinc-900/50 border border-zinc-800 rounded-xl hover:border-purple-700 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-purple-600/20 flex items-center justify-center">
                        <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                        </svg>
                      </div>
                      <div>
                        <div className="text-sm font-medium">Find Study Buddies</div>
                        <div className="text-xs text-zinc-500">Match with students who share your interests</div>
                      </div>
                      <svg className="w-4 h-4 ml-auto text-zinc-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </Link>

                  <Link
                    to="/app/study-buddy/connections"
                    className="block p-4 bg-zinc-900/50 border border-zinc-800 rounded-xl hover:border-purple-700 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-purple-600/20 flex items-center justify-center">
                        <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                        </svg>
                      </div>
                      <div>
                        <div className="text-sm font-medium">Your Connections</div>
                        <div className="text-xs text-zinc-500">Manage study buddy connections</div>
                      </div>
                      <svg className="w-4 h-4 ml-auto text-zinc-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </Link>
                </div>

                {myCompanions.length > 0 && (
                  <Link
                    to="/app/study-buddy/profile"
                    className="block mt-4 p-3 bg-zinc-900/50 border border-zinc-800 rounded-xl hover:border-purple-700 transition-colors"
                  >
                    <div className="flex items-center gap-2 text-sm text-zinc-400">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                      Complete Your Study Profile
                    </div>
                  </Link>
                )}
              </section>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
