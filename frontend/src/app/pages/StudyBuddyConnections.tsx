import { useState, useEffect } from "react";
import { motion } from "motion/react";
import { useNavigate } from "react-router";
import { Users, CheckCircle, XCircle, MessageCircle } from "lucide-react";
import { studyBuddyService, Connection, ConnectionRequest } from "../services/studyBuddyService";
import { useStore } from "../store";
import { cn } from "../utils";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";

export default function StudyBuddyConnections() {
  const user = useStore(state => state.user);
  const navigate = useNavigate();
  const [connections, setConnections] = useState<Connection[]>([]);
  const [incomingRequests, setIncomingRequests] = useState<ConnectionRequest[]>([]);
  const [outgoingRequests, setOutgoingRequests] = useState<ConnectionRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user) {
      setError("Please log in to view connections");
      return;
    }
    loadData();
  }, [user]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError("");
      const [connections, incoming] = await Promise.all([
        studyBuddyService.getConnections(),
        studyBuddyService.getPendingRequests(),
      ]);
      setConnections(connections);
      setIncomingRequests(incoming);
      setOutgoingRequests(incoming.filter(r => r.sender_id === user?.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load connections");
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async (buddyId: string) => {
    try {
      setActionLoading(buddyId);
      const conversation = await studyBuddyService.createConversation(buddyId);
      navigate(`/app/study-buddy/dm/${conversation.conversation_id}`);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to start conversation");
    } finally {
      setActionLoading(null);
    }
  };

  const handleAcceptRequest = async (requestId: string) => {
    try {
      setActionLoading(requestId);
      setError("");
      await studyBuddyService.respondToRequest(requestId, "accept");
      await loadData();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to accept request");
    } finally {
      setActionLoading(null);
    }
  };

  const handleRejectRequest = async (requestId: string) => {
    if (!confirm("Are you sure you want to reject this connection request?")) {
      return;
    }

    try {
      setActionLoading(requestId);
      setError("");
      await studyBuddyService.respondToRequest(requestId, "reject");
      await loadData();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to reject request");
    } finally {
      setActionLoading(null);
    }
  };

  const handleCancelRequest = async (requestId: string) => {
    if (!confirm("Are you sure you want to cancel this request?")) {
      return;
    }

    try {
      setActionLoading(requestId);
      setError("");
      await studyBuddyService.respondToRequest(requestId, "reject");
      await loadData();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to cancel request");
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-zinc-950">
        <div className="flex items-center gap-2 text-zinc-500">
          <Users className="w-5 h-5 animate-spin" />
          Loading connections...
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto bg-zinc-950 p-4 sm:p-6 md:p-8 custom-scrollbar h-full">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl sm:text-4xl font-light tracking-tighter">
            Study Buddy Connections
          </h1>
          <p className="text-zinc-400 text-sm mt-2">
            Manage your study buddy connections and incoming requests
          </p>
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

        <Tabs defaultValue="connections" className="space-y-6">
          <TabsList className="grid w-full max-w-md grid-cols-3 bg-zinc-900 border-zinc-800">
            <TabsTrigger value="connections" className="text-zinc-400 data-[state=active]:bg-purple-600 data-[state=active]:text-white">
              Connections ({connections.length})
            </TabsTrigger>
            <TabsTrigger value="incoming" className="text-zinc-400 data-[state=active]:bg-purple-600 data-[state=active]:text-white">
              Incoming ({incomingRequests.length})
            </TabsTrigger>
            <TabsTrigger value="outgoing" className="text-zinc-400 data-[state=active]:bg-purple-600 data-[state=active]:text-white">
              Outgoing ({outgoingRequests.length})
            </TabsTrigger>
          </TabsList>

          {/* Connections */}
          <TabsContent value="connections">
            {connections.length === 0 ? (
              <div className="text-center py-20 border border-dashed border-zinc-800 rounded-3xl bg-zinc-900/20">
                <Users className="w-16 h-16 mx-auto mb-6 text-zinc-600" />
                <h2 className="text-2xl font-medium mb-2">No Connections Yet</h2>
                <p className="text-zinc-500 max-w-md mx-auto mb-8">
                  Start connecting with study buddies by finding matches and sending requests
                </p>
                <a
                  href="/app/study-buddy/matches"
                  className="inline-block px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-xl transition-colors"
                >
                  Find Study Buddies
                </a>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {connections.map((connection, index) => (
                  <motion.div
                    key={connection.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    <Card className="bg-zinc-900/50 border-zinc-800">
                      <CardContent className="p-6">
                        {/* User Info */}
                        <div className="flex items-center gap-3 mb-4">
                          <div className="w-12 h-12 rounded-full bg-zinc-800 flex items-center justify-center">
                            <Users className="w-6 h-6 text-zinc-400" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <h3 className="font-semibold text-zinc-100 truncate">{connection.full_name}</h3>
                            <p className="text-xs text-zinc-500">{connection.campus_university}</p>
                          </div>
                          {connection.is_online && (
                            <div className="w-3 h-3 bg-emerald-500 rounded-full" />
                          )}
                        </div>

                        {/* Details */}
                        <div className="space-y-2 mb-4">
                          <div className="flex justify-between text-sm">
                            <span className="text-zinc-400">Major:</span>
                            <span className="text-zinc-200">{connection.major}</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-zinc-400">Year:</span>
                            <span className="text-zinc-200">{connection.academic_year}</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-zinc-400">Location:</span>
                            <span className="text-zinc-200">{connection.city}, {connection.country}</span>
                          </div>
                        </div>

                        {/* Message */}
                        <Button 
                          variant="outline" 
                          className="w-full" 
                          size="sm"
                          onClick={() => handleSendMessage(connection.user_id)}
                          disabled={actionLoading === connection.user_id}
                        >
                          <MessageCircle className="w-4 h-4 mr-2" />
                          {actionLoading === connection.user_id ? "Starting..." : "Send Message"}
                        </Button>
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Incoming Requests */}
          <TabsContent value="incoming">
            {incomingRequests.length === 0 ? (
              <div className="text-center py-20 border border-dashed border-zinc-800 rounded-3xl bg-zinc-900/20">
                <Users className="w-16 h-16 mx-auto mb-6 text-zinc-600" />
                <h2 className="text-2xl font-medium mb-2">No Incoming Requests</h2>
                <p className="text-zinc-500 max-w-md mx-auto">
                  You'll see connection requests from other users here
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {incomingRequests.map((request) => (
                  <motion.div
                    key={request.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-full bg-zinc-800 flex items-center justify-center">
                          <Users className="w-6 h-6 text-zinc-500" />
                        </div>
                        <div>
                          <h3 className="font-semibold">{request.sender_full_name}</h3>
                          <p className="text-xs text-zinc-500">User ID: {request.sender_id.slice(-6)}</p>
                        </div>
                      </div>
                      <span className="text-xs text-zinc-600">{new Date(request.created_at).toLocaleDateString()}</span>
                    </div>

                    {request.message && (
                      <p className="text-sm text-zinc-400 mb-4">{request.message}</p>
                    )}

                    <div className="flex gap-3">
                      <Button
                        onClick={() => handleAcceptRequest(request.id)}
                        disabled={actionLoading === request.id}
                        className="flex-1"
                        size="sm"
                      >
                        {actionLoading === request.id ? (
                          "Processing..."
                        ) : (
                          <>
                            <CheckCircle className="w-4 h-4 mr-2" />
                            Accept
                          </>
                        )}
                      </Button>
                      <Button
                        onClick={() => handleRejectRequest(request.id)}
                        disabled={actionLoading === request.id}
                        variant="outline"
                        className="flex-1"
                        size="sm"
                      >
                        {actionLoading === request.id ? (
                          "Processing..."
                        ) : (
                          <>
                            <XCircle className="w-4 h-4 mr-2" />
                            Reject
                          </>
                        )}
                      </Button>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Outgoing Requests */}
          <TabsContent value="outgoing">
            {outgoingRequests.length === 0 ? (
              <div className="text-center py-20 border border-dashed border-zinc-800 rounded-3xl bg-zinc-900/20">
                <Users className="w-16 h-16 mx-auto mb-6 text-zinc-600" />
                <h2 className="text-2xl font-medium mb-2">No Outgoing Requests</h2>
                <p className="text-zinc-500 max-w-md mx-auto">
                  You haven't sent any connection requests yet
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {outgoingRequests.map((request) => (
                  <motion.div
                    key={request.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-full bg-zinc-800 flex items-center justify-center">
                          <Users className="w-6 h-6 text-zinc-500" />
                        </div>
                        <div>
                          <h3 className="font-semibold">{request.sender_full_name}</h3>
                          <p className="text-xs text-zinc-500">User ID: {request.sender_id.slice(-6)}</p>
                        </div>
                      </div>
                      <span className="text-xs px-2 py-1 bg-yellow-900/30 text-yellow-400 rounded">
                        Pending
                      </span>
                    </div>

                    {request.message && (
                      <p className="text-sm text-zinc-400 mt-3">{request.message}</p>
                    )}

                    <Button
                      onClick={() => handleCancelRequest(request.id)}
                      disabled={actionLoading === request.id}
                      variant="outline"
                      className="w-full mt-4"
                      size="sm"
                    >
                      {actionLoading === request.id ? (
                        "Processing..."
                      ) : (
                        "Cancel Request"
                      )}
                    </Button>
                  </motion.div>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
