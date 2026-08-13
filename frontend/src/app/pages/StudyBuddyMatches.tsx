import { useState, useEffect } from "react";
import { motion } from "motion/react";
import { RefreshCw, Users, MessageSquare, MessageCircle } from "lucide-react";
import { studyBuddyService, StudyBuddyMatch, MatchReason } from "../services/studyBuddyService";
import { useStore } from "../store";
import { cn } from "../utils";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";

export default function StudyBuddyMatches() {
  const user = useStore(state => state.user);
  const [matches, setMatches] = useState<StudyBuddyMatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [selectedMatch, setSelectedMatch] = useState<StudyBuddyMatch | null>(null);

  useEffect(() => {
    if (!user) {
      setError("Please log in to view matches");
      return;
    }
    loadMatches();
  }, [user]);

  const loadMatches = async () => {
    try {
      setLoading(true);
      setError("");
      const data = await studyBuddyService.findMatches(20);
      setMatches(data.matches);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load matches");
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    try {
      setRefreshing(true);
      setError("");
      await loadMatches();
    } finally {
      setRefreshing(false);
    }
  };

  const handleConnect = async (match: StudyBuddyMatch) => {
    try {
      await studyBuddyService.sendConnectionRequest(match.user_id);
      // Refresh matches after sending request
      await loadMatches();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to send connection request");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-zinc-950">
        <div className="flex items-center gap-2 text-zinc-500">
          <RefreshCw className="w-5 h-5 animate-spin" />
          Finding your study buddies...
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto bg-zinc-950 p-4 sm:p-6 md:p-8 custom-scrollbar h-full">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl sm:text-4xl font-light tracking-tighter">
              Find Your Study Buddy
            </h1>
            <p className="text-zinc-400 text-sm mt-2">
              We found {matches.length} study buddy matches for you based on your profile
            </p>
          </div>
          <Button
            onClick={handleRefresh}
            disabled={refreshing}
            variant="outline"
            className="gap-2"
          >
            <RefreshCw className={cn("w-4 h-4", refreshing && "animate-spin")} />
            Refresh
          </Button>
        </div>

        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 p-4 bg-red-900/20 border border-red-800 rounded-xl"
          >
            <p className="text-red-400 text-sm">{error}</p>
          </motion.div>
        )}

        {matches.length === 0 && !error ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center py-20 border border-dashed border-zinc-800 rounded-3xl bg-zinc-900/20"
          >
            <Users className="w-16 h-16 mx-auto mb-6 text-zinc-600" />
            <h2 className="text-2xl font-medium mb-2">No Matches Yet</h2>
            <p className="text-zinc-500 max-w-md mx-auto mb-8">
              Complete your profile to start getting study buddy recommendations
            </p>
            <a
              href="/app/study-buddy/profile"
              className="inline-block px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-xl transition-colors"
            >
              Complete Your Profile
            </a>
          </motion.div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {matches.map((match, index) => (
              <motion.div
                key={match.user_id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <Card className="bg-zinc-900/50 border-zinc-800 overflow-hidden">
                  <CardContent className="p-6">
                    {/* Match Score Header */}
                    <div className="flex items-center justify-between mb-4">
                      <div className="text-3xl font-light text-zinc-100">{match.compatibility_score}%</div>
                      <div className="text-xs text-zinc-400">Match Score</div>
                    </div>

                    {/* User Info */}
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-12 h-12 rounded-full bg-zinc-800 flex items-center justify-center">
                        <Users className="w-6 h-6 text-zinc-400" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-zinc-100">{match.full_name}</h3>
                        <p className="text-xs text-zinc-500">User ID: {match.user_id.slice(-6)}</p>
                      </div>
                    </div>

                    {/* Match Reasons */}
                    <div className="mb-4 space-y-2">
                      {match.match_reasons.slice(0, 3).map((reason) => (
                        <div
                          key={reason.reason}
                          className="flex items-start gap-2 text-sm"
                        >
                          <MessageCircle className="w-4 h-4 text-purple-400 mt-0.5 flex-shrink-0" />
                          <span className="text-zinc-300">{reason.description}</span>
                        </div>
                      ))}
                      {match.match_reasons.length > 3 && (
                        <div className="text-xs text-zinc-500">
                          +{match.match_reasons.length - 3} more reasons
                        </div>
                      )}
                    </div>

                    {/* Strong Subjects Overlap */}
                    {match.strong_subjects_overlap.length > 0 && (
                      <div className="mb-4">
                        <div className="text-xs text-zinc-400 mb-2">Common Strong Subjects</div>
                        <div className="flex flex-wrap gap-1">
                          {match.strong_subjects_overlap.map(subject => (
                            <span
                              key={subject}
                              className="px-2 py-1 bg-purple-900/30 text-purple-300 rounded text-xs"
                            >
                              {subject}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Ways They Can Help */}
                    {match.weak_subjects_help.length > 0 && (
                      <div className="mb-4">
                        <div className="text-xs text-zinc-400 mb-2">Ways They Can Help You</div>
                        <div className="flex flex-wrap gap-1">
                          {match.weak_subjects_help.map(subject => (
                            <span
                              key={subject}
                              className="px-2 py-1 bg-blue-900/30 text-blue-300 rounded text-xs"
                            >
                              {subject}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Action */}
                    <Button
                      onClick={() => handleConnect(match)}
                      className="w-full"
                      size="sm"
                    >
                      <MessageSquare className="w-4 h-4 mr-2" />
                      Connect
                    </Button>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
