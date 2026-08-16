import { useState, useEffect } from "react";

// Simple component for temporary diagnostic logging
const ConsoleLogLine = ({ message }: { message: string }) => {
  useEffect(() => {
    console.log(message);
  }, [message]);
  return null;
};
import { motion } from "motion/react";
import { RefreshCw, Users, MessageCircle, MessageSquare, Loader2, Check, X } from "lucide-react";
import { studyBuddyService, StudyBuddyMatch, MatchReason } from "../services/studyBuddyService";
import { useStore } from "../store";
import { cn } from "../utils";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";
import { useToast } from "../useToast";

export default function StudyBuddyMatches() {
  const user = useStore(state => state.user);
  const { addToast, removeToast } = useToast();
  const [matches, setMatches] = useState<StudyBuddyMatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [selectedMatch, setSelectedMatch] = useState<StudyBuddyMatch | null>(null);
  const [sendingRequest, setSendingRequest] = useState<Set<string>>(new Set());
  const [cancellingRequest, setCancellingRequest] = useState<Set<string>>(new Set());
  const [pendingRequests, setPendingRequests] = useState<Map<string, ConnectionRequest>>(new Map());
  const [acceptingRequest, setAcceptingRequest] = useState<Set<string>>(new Set());
  const [rejectingRequest, setRejectingRequest] = useState<Set<string>>(new Set());

  // Observe pendingRequests changes to track when it's actually refreshed
  useEffect(() => {
    console.log('=== pendingRequests ACTUALLY CHANGED ===');
    console.log('pendingRequests map size:', pendingRequests.size);
    console.log('pendingRequests keys:', Array.from(pendingRequests.keys()));
    console.log('pendingRequests entries:', Array.from(pendingRequests.entries()).map(([k, v]) => ({
      key: k,
      id: v.id,
      sender_id: v.sender_id,
      recipient_id: v.recipient_id,
      status: v.status
    })));
  }, [pendingRequests]);

  useEffect(() => {
    if (!user) {
      setError("Please log in to view matches");
      return;
    }
    loadMatches();
    loadPendingRequests();
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
      await loadPendingRequests();
    } finally {
      setRefreshing(false);
    }
  };

  const loadPendingRequests = async () => {
    try {
      const requests = await studyBuddyService.getPendingRequests();
      const pendingMap = new Map<string, ConnectionRequest>();
      const currentUserId = user?.id;

      console.log('=== LOAD PENDING REQUESTS ===');
      console.log('currentUserId:', currentUserId);
      console.log('Number of requests from backend:', requests.length);

      requests.forEach((request, index) => {
        console.log(`Request ${index}:`);
        console.log('  - sender_id:', request.sender_id);
        console.log('  - recipient_id:', request.recipient_id);
        console.log('  - status:', request.status);
        console.log('  - does sender_id === currentUserId?', request.sender_id === currentUserId);

        // Store the request using the OTHER user's ID as the key
        const otherUserId = request.sender_id === currentUserId
          ? request.recipient_id
          : request.sender_id;

        console.log('  - calculated otherUserId:', otherUserId);
        pendingMap.set(otherUserId, request);
      });

      console.log('=== PENDING MAP KEYS ===');
      pendingMap.forEach((value, key) => {
        console.log('  - key:', key);
        console.log('  - value.id:', value.id);
        console.log('  - value.status:', value.status);
      });

      console.log('Map size:', pendingMap.size);
      console.log('Setting pendingRequests state with', pendingMap.size, 'entries');
      setPendingRequests(pendingMap);
    } catch (err) {
      console.error("Error loading pending requests:", err);
    }
  };

  const handleCancelRequest = async (match: StudyBuddyMatch) => {
    const requestId = pendingRequests.get(match.user_id)?.id;
    if (!requestId) {
      addToast({
        message: "No pending request to cancel",
        type: 'error',
      });
      return;
    }

    const matchId = match.user_id;
    if (cancellingRequest.has(matchId)) {
      return;
    }

    setCancellingRequest(prev => new Set(prev).add(matchId));

    try {
      await studyBuddyService.cancelConnectionRequest(requestId);
      addToast({
        message: "Connection request cancelled",
        type: 'info',
      });

      // Update local state to show Connect
      setMatches(prev =>
        prev.map(m =>
          m.user_id === matchId
            ? { ...m, connectionState: undefined }
            : m
        )
      );

      // Remove from pending requests
      setPendingRequests(prev => {
        const next = new Map(prev);
        next.delete(matchId);
        return next;
      });

      setCancellingRequest(prev => {
        const next = new Set(prev);
        next.delete(matchId);
        return next;
      });

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to cancel request";
      addToast({
        message: errorMessage,
        type: 'error',
      });

      // Do NOT remove from pendingRequests on failure - let the backend state be the source of truth
      setCancellingRequest(prev => {
        const next = new Set(prev);
        next.delete(matchId);
        return next;
      });
    }
  };

  const handleAcceptRequest = async (match: StudyBuddyMatch) => {
    const requestId = pendingRequests.get(match.user_id)?.id;
    if (!requestId) {
      addToast({
        message: "No pending request to accept",
        type: 'error',
      });
      return;
    }

    const matchId = match.user_id;
    if (acceptingRequest.has(matchId)) {
      return;
    }

    setAcceptingRequest(prev => new Set(prev).add(matchId));

    try {
      await studyBuddyService.respondToRequest(requestId, 'accept');
      addToast({
        message: "Connection request accepted!",
        type: 'success',
      });

      // Update local state to show connected
      setMatches(prev =>
        prev.map(m =>
          m.user_id === matchId
            ? { ...m, connectionState: 'accepted' as const }
            : m
        )
      );

      // Remove from pending requests
      setPendingRequests(prev => {
        const next = new Map(prev);
        next.delete(matchId);
        return next;
      });

      setAcceptingRequest(prev => {
        const next = new Set(prev);
        next.delete(matchId);
        return next;
      });

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to accept request";
      addToast({
        message: errorMessage,
        type: 'error',
      });

      // Do NOT remove from pendingRequests on failure - let the backend state be the source of truth
      setAcceptingRequest(prev => {
        const next = new Set(prev);
        next.delete(matchId);
        return next;
      });
    }
  };

  const handleRejectRequest = async (match: StudyBuddyMatch) => {
    console.log('=== REJECT REQUEST START ===');
    const requestId = pendingRequests.get(match.user_id)?.id;
    console.log('requestId:', requestId);
    console.log('pendingRequest:', pendingRequests.get(match.user_id));

    if (!requestId) {
      console.log('ERROR: No request ID found in pendingRequests');
      addToast({
        message: "No pending request to reject",
        type: 'error',
      });
      return;
    }

    const matchId = match.user_id;
    console.log('matchId:', matchId);

    if (rejectingRequest.has(matchId)) {
      console.log('Already rejecting this request, returning');
      return;
    }

    console.log('Setting rejectingRequest state for', matchId);
    setRejectingRequest(prev => new Set(prev).add(matchId));

    try {
      console.log('=== REJECT SUCCESS ===');
      console.log('Calling respondToRequest API for requestId:', requestId, 'action: reject');
      await studyBuddyService.respondToRequest(requestId, 'reject');
      console.log('Reject API call succeeded');

      addToast({
        message: "Connection request rejected",
        type: 'info',
      });

      console.log('=== REJECT STATE UPDATE ===');
      console.log('pendingRequests before removal:');
      console.log('  size:', pendingRequests.size);
      console.log('  has(matchId):', pendingRequests.has(matchId));
      console.log('  keys:', Array.from(pendingRequests.keys()));

      // Update local state to show rejected
      setMatches(prev =>
        prev.map(m =>
          m.user_id === matchId
            ? { ...m, connectionState: 'rejected' as const }
            : m
        )
      );

      console.log('Removing from pendingRequests for matchId:', matchId);
      // Remove from pending requests
      setPendingRequests(prev => {
        const next = new Map(prev);
        console.log('  Before delete - map has', next.has(matchId), 'entry for', matchId);
        next.delete(matchId);
        console.log('  After delete - map has', next.has(matchId), 'entry for', matchId);
        console.log('  After delete - map size:', next.size);
        console.log('  After delete - map keys:', Array.from(next.keys()));
        return next;
      });

      console.log('=== REJECT SUCCESS FINAL ===');
      console.log('pendingRequests after removal:');
      console.log('  size:', pendingRequests.size);
      console.log('  has(matchId):', pendingRequests.has(matchId));
      console.log('  keys:', Array.from(pendingRequests.keys()));

      setRejectingRequest(prev => {
        const next = new Set(prev);
        next.delete(matchId);
        return next;
      });

    } catch (err) {
      console.log('=== HANDLE REJECT REQUEST FAILED ===');
      const errorMessage = err instanceof Error ? err.message : "Failed to reject request";
      console.log('Error message:', errorMessage);
      addToast({
        message: errorMessage,
        type: 'error',
      });

      // Do NOT remove from pendingRequests on failure - let the backend state be the source of truth
      setRejectingRequest(prev => {
        const next = new Set(prev);
        next.delete(matchId);
        return next;
      });
    }
  };

  const handleConnect = async (match: StudyBuddyMatch) => {
    console.log('=== HANDLE CONNECT START ===');
    const matchId = match.user_id;

    console.log('=== HANDLE CONNECT START ===');
    console.log('matchId:', matchId);
    console.log('currentUserIdentifier:', user?.id);
    console.log('pendingRequests.has(matchId):', pendingRequests.has(matchId));
    console.log('pendingRequest:', pendingRequests.get(matchId));
    console.log('sendingRequest.has(matchId):', sendingRequest.has(matchId));

    // Prevent duplicate clicks
    if (sendingRequest.has(matchId)) {
      console.log('ALREADY SENDING REQUEST - returning early');
      return;
    }

    console.log('Setting sendingRequest state for', matchId);
    setSendingRequest(prev => new Set(prev).add(matchId));

    console.log('=== CONNECT CLICKED ===');
    console.log('match ID:', matchId);
    console.log('match.user_id:', match.user_id);
    console.log('current authenticated user ID:', user?.id);
    console.log('recipient ID being passed:', matchId);

    console.log('=== ABOUT TO SEND CONNECTION REQUEST ===');
    console.log('sender:', user?.id);
    console.log('recipient:', matchId);

    try {
      console.log('Calling sendConnectionRequest API...');
      const request = await studyBuddyService.sendConnectionRequest(matchId);

      console.log('=== CONNECTION API RESPONSE ===');
      console.log('status:', request.status);
      console.log('ok:', request.ok);
      console.log('raw response body:', request);
      console.log('=== PARSED CONNECTION RESPONSE ===');
      console.log('success:', request.success);
      console.log('message:', request.message);
      console.log('error_code:', request.error_code);
      console.log('data:', request.data);
      console.log('request.id:', request.id);
      console.log('request.sender_id:', request.sender_id);
      console.log('request.recipient_id:', request.recipient_id);
      console.log('request.status:', request.status);

      addToast({
        message: "Connection request sent",
        type: 'success',
      });

      console.log('Before setPendingRequests (success):');
      console.log('  pendingRequests size:', pendingRequests.size);

      // Update just this match's state to show as sent
      setMatches(prev =>
        prev.map(m =>
          m.user_id === matchId
            ? { ...m, connectionState: 'sent' as const }
            : m
        )
      );

      // Add request to pendingRequests Map so it can be cancelled immediately
      setPendingRequests(prev => {
        const next = new Map(prev);
        console.log('  Before adding to pendingRequests:');
        console.log('    - matchId:', matchId);
        console.log('    - map size:', next.size);
        console.log('    - map keys:', Array.from(next.keys()));
        // Use the match's user_id as the key
        next.set(matchId, request);
        console.log('  After adding to pendingRequests:');
        console.log('    - matchId:', matchId);
        console.log('    - map size:', next.size);
        console.log('    - map keys:', Array.from(next.keys()));
        return next;
      });

      console.log('Setting sendingRequest back to false');
      // Mark request as no longer sending
      setSendingRequest(prev => {
        const next = new Set(prev);
        next.delete(matchId);
        return next;
      });

      console.log('=== HANDLE CONNECT SUCCESS ===');

    } catch (err) {
      console.log('=== HANDLE CONNECT FAILED ===');
      const errorMessage = err instanceof Error ? err.message : "Failed to send connection request";

      console.log('=== CONNECTION API FAILURE ===');
      console.log('HTTP status:', err.status);
      console.log('backend message:', err.message);
      console.log('backend error_code:', err.error_code);
      console.log('frontend error:', errorMessage);
      console.log('match ID:', matchId);
      console.log('match.user_id:', match.user_id);
      console.log('current authenticated user ID:', user?.id);

      // Check if this is a duplicate request error
      if (errorMessage.includes("already exists") || errorMessage.includes("already sent")) {
        console.log('=== DUPLICATE REQUEST ERROR DETECTED ===');
        addToast({
          message: "You already sent a connection request to this user.",
          type: 'info',
        });

        console.log('Error message:', errorMessage);
        console.log('pendingRequests state when error occurred:');
        console.log('  has(matchId):', pendingRequests.has(matchId));
        if (pendingRequests.has(matchId)) {
          const req = pendingRequests.get(matchId);
          console.log('  request details:');
          console.log('    - id:', req.id);
          console.log('    - sender_id:', req.sender_id);
          console.log('    - recipient_id:', req.recipient_id);
          console.log('    - status:', req.status);
        }

        // Update state to show as sent even though API failed
        setMatches(prev =>
          prev.map(m =>
            m.user_id === matchId
              ? { ...m, connectionState: 'sent' as const }
              : m
          )
        );
      } else {
        addToast({
          message: errorMessage,
          type: 'error',
        });

        console.log('Restoring sendingRequest state');
        // Restore button state
        setSendingRequest(prev => {
          const next = new Set(prev);
          next.delete(matchId);
          return next;
        });
      }
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
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-zinc-100">{match.full_name}</h3>
                        <p className="text-xs text-zinc-500">User ID: {match.user_id.slice(-6)}</p>
                      </div>
                    </div>

                    {/* Profile Information */}
                    {(match.country || match.city || match.academic_year || match.major) && (
                      <div className="mb-4 space-y-1.5">
                        <div className="text-xs text-zinc-400 font-medium">PROFILE</div>
                        <div className="flex items-center gap-2 text-sm text-zinc-300">
                          {match.country && (
                            <span className="flex items-center gap-1">
                              <span className="text-purple-400">📍</span>
                              {match.country}
                            </span>
                          )}
                          {match.city && (
                            <span className="flex items-center gap-1">
                              <span className="text-purple-400">•</span>
                              {match.city}
                            </span>
                          )}
                        </div>
                        <div className="flex flex-wrap gap-3 text-xs text-zinc-400">
                          {match.academic_year && (
                            <span className="flex items-center gap-1">
                              <span className="text-purple-400">🎓</span>
                              {match.academic_year}
                            </span>
                          )}
                          {match.campus_university && (
                            <span className="flex items-center gap-1">
                              <span className="text-purple-400">🏫</span>
                              {match.campus_university}
                            </span>
                          )}
                          {match.major && (
                            <span className="flex items-center gap-1">
                              <span className="text-purple-400">📚</span>
                              {match.major}
                            </span>
                          )}
                        </div>
                      </div>
                    )}

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

                    {/* Strong Subjects */}
                    {match.strong_subjects && match.strong_subjects.length > 0 && (
                      <div className="mb-4">
                        <div className="text-xs text-zinc-400 mb-2">STRONG AT</div>
                        <div className="flex flex-wrap gap-1">
                          {match.strong_subjects.map(subject => (
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

                    {/* Weak Subjects */}
                    {match.weak_subjects && match.weak_subjects.length > 0 && (
                      <div className="mb-4">
                        <div className="text-xs text-zinc-400 mb-2">NEEDS HELP WITH</div>
                        <div className="flex flex-wrap gap-1">
                          {match.weak_subjects.map(subject => (
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
                    <div className="space-y-2">
                      {(() => {
                        const pendingRequest = pendingRequests.get(match.user_id);
                        const currentUserIdentifier = user?.id;

                        console.log('=== MATCH RENDER ===');
                        console.log('MATCH ID:', match.user_id);
                        console.log('CURRENT USER ID:', currentUserIdentifier);
                        console.log('PENDING HAS:', pendingRequests.has(match.user_id));
                        console.log('PENDING REQUEST:', pendingRequest);
                        console.log('ALL PENDING KEYS:', Array.from(pendingRequests.keys()));

                        const isOutgoingPending =
                            pendingRequest?.sender_id === currentUserIdentifier &&
                            pendingRequest?.status === 'pending';
                        const isIncomingPending =
                            pendingRequest?.recipient_id === currentUserIdentifier &&
                            pendingRequest?.status === 'pending';

                        console.log('DEBUG pendingRequest.sender_id:', pendingRequest?.sender_id);
                        console.log('DEBUG pendingRequest.recipient_id:', pendingRequest?.recipient_id);
                        console.log('DEBUG currentUserIdentifier:', currentUserIdentifier);
                        console.log('DEBUG pendingRequest.status:', pendingRequest?.status);
                        console.log('DEBUG sender === current:', pendingRequest?.sender_id === currentUserIdentifier);
                        console.log('DEBUG recipient === current:', pendingRequest?.recipient_id === currentUserIdentifier);
                        console.log('DEBUG isOutgoingPending:', isOutgoingPending);
                        console.log('DEBUG isIncomingPending:', isIncomingPending);

                        console.log('=== CONNECTION BUTTON STATE ===');
                        console.log('currentUserIdentifier:', currentUserIdentifier);
                        console.log('match.user_id:', match.user_id);
                        console.log('match.id:', match.id || match.user_id);
                        console.log('pendingRequests.has(match.user_id):', pendingRequests.has(match.user_id));
                        console.log('pendingRequest:', pendingRequest);
                        if (pendingRequest) {
                          console.log('pendingRequest.id:', pendingRequest.id);
                          console.log('pendingRequest.sender_id:', pendingRequest.sender_id);
                          console.log('pendingRequest.recipient_id:', pendingRequest.recipient_id);
                          console.log('pendingRequest.status:', pendingRequest.status);
                        }
                        console.log('isOutgoingPending:', isOutgoingPending);
                        console.log('isIncomingPending:', isIncomingPending);
                        console.log('sendingRequest.has(match.user_id):', sendingRequest.has(match.user_id));

                        let finalButton = null;
                        if (isOutgoingPending) {
                          console.log('FINAL BUTTON: Cancel');
                          finalButton = 'Cancel';
                        } else if (isIncomingPending) {
                          console.log('FINAL BUTTON: Accept/Reject');
                          finalButton = 'Accept/Reject';
                        } else if (!pendingRequests.has(match.user_id)) {
                          console.log('FINAL BUTTON: Connect');
                          finalButton = 'Connect';
                        } else {
                          console.log('FINAL BUTTON: None/Other');
                          finalButton = 'None/Other';
                        }

                        if (isOutgoingPending) {
                          return (
                            <Button
                              onClick={() => handleCancelRequest(match)}
                              disabled={cancellingRequest.has(match.user_id)}
                              className="w-full"
                              size="sm"
                              variant="outline"
                            >
                              {cancellingRequest.has(match.user_id) ? (
                                <>
                                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                  Canceling...
                                </>
                              ) : (
                                <>
                                  <MessageSquare className="w-4 h-4 mr-2" />
                                  Cancel Request
                                </>
                              )}
                            </Button>
                          );
                        }

                        if (isIncomingPending) {
                          return (
                            <div className="space-y-2">
                              <Button
                                onClick={() => handleAcceptRequest(match)}
                                disabled={acceptingRequest.has(match.user_id)}
                                className="w-full"
                                size="sm"
                                variant="default"
                              >
                                {acceptingRequest.has(match.user_id) ? (
                                  <>
                                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                    Accepting...
                                  </>
                                ) : (
                                  <>
                                    <Check className="w-4 h-4 mr-2" />
                                    Accept Request
                                  </>
                                )}
                              </Button>
                              <Button
                                onClick={() => handleRejectRequest(match)}
                                disabled={rejectingRequest.has(match.user_id)}
                                className="w-full"
                                size="sm"
                                variant="outline"
                              >
                                {rejectingRequest.has(match.user_id) ? (
                                  <>
                                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                    Rejecting...
                                  </>
                                ) : (
                                  <>
                                    <MessageSquare className="w-4 h-4 mr-2" />
                                    Reject Request
                                  </>
                                )}
                              </Button>
                            </div>
                          );
                        }

                        return null;
                      })()}

                      {!pendingRequests.has(match.user_id) && (
                        <>
                          <ConsoleLogLine
                            message={`=== BUTTON RENDER: match.user_id=${match.user_id}, pendingRequests.has=${pendingRequests.has(match.user_id)}, sendingRequest.has=${sendingRequest.has(match.user_id)}`}
                          />
                          <Button
                            onClick={() => handleConnect(match)}
                            disabled={sendingRequest.has(match.user_id)}
                            className="w-full"
                            size="sm"
                            type="button"
                          >
                            {sendingRequest.has(match.user_id) ? (
                              <>
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                Sending...
                              </>
                            ) : (
                              <>
                                <MessageSquare className="w-4 h-4 mr-2" />
                                Connect
                              </>
                            )}
                          </Button>
                        </>
                      )}
                    </div>
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
