import { useState, useEffect } from "react";
import { motion } from "motion/react";
import { Plus, MessageSquare, Search, Filter, Loader2, Image as ImageIcon } from "lucide-react";
import { Link } from "react-router";
import { qaService, Question } from "../services/qaService";
import { cn, formatDate } from "../utils";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "../components/ui/card";
import CreateQuestionModal from "../components/CreateQuestionModal";

export default function PeerQAList() {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSubject, setSelectedSubject] = useState<string>("All");
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const subjects = ["All", "Programming", "Mathematics", "Physics", "Chemistry", "Biology", "Literature", "History", "Other"];

  useEffect(() => {
    loadQuestions();
  }, [selectedSubject]);

  const loadQuestions = async () => {
    try {
      setLoading(true);
      setError("");
      const result = await qaService.listQuestions(1, 50, selectedSubject === "All" ? undefined : selectedSubject);
      setQuestions(result.questions);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load questions");
    } finally {
      setLoading(false);
    }
  };

  const filteredQuestions = questions.filter(q => 
    q.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
    q.subject.toLowerCase().includes(searchQuery.toLowerCase()) ||
    q.author_full_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex-1 overflow-y-auto bg-zinc-950 p-4 sm:p-6 md:p-8 text-zinc-50 relative h-full">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <header className="mb-8 flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
          <div>
            <h1 className="text-3xl sm:text-4xl font-light tracking-tighter mb-2">
              Peer Q&A
            </h1>
            <p className="text-zinc-400 text-sm sm:text-base">Ask questions and help your fellow students.</p>
          </div>
          
          <Button 
            onClick={() => setIsCreateModalOpen(true)}
            className="bg-purple-600 hover:bg-purple-700 text-white gap-2"
          >
            <Plus className="w-4 h-4" />
            Ask a Question
          </Button>
        </header>

        {/* Filters & Search */}
        <div className="flex flex-col md:flex-row gap-4 mb-8">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
            <Input 
              placeholder="Search questions, subjects, or authors..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 bg-zinc-900/50 border-zinc-800 focus:border-purple-500 transition-colors"
            />
          </div>
          <div className="flex gap-2 overflow-x-auto pb-2 md:pb-0 custom-scrollbar">
            {subjects.map(subject => (
              <Badge
                key={subject}
                variant={selectedSubject === subject ? "default" : "outline"}
                className={cn(
                  "cursor-pointer px-3 py-1.5 transition-all whitespace-nowrap",
                  selectedSubject === subject 
                    ? "bg-purple-600 text-white border-purple-600" 
                    : "bg-zinc-900/50 text-zinc-400 border-zinc-800 hover:border-zinc-700"
                )}
                onClick={() => setSelectedSubject(subject)}
              >
                {subject}
              </Badge>
            ))}
          </div>
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-purple-500 animate-spin mb-4" />
            <p className="text-zinc-500">Loading campus discussions...</p>
          </div>
        ) : error ? (
          <div className="p-8 bg-red-900/10 border border-red-900/20 rounded-2xl text-center">
            <p className="text-red-400 mb-4">{error}</p>
            <Button variant="outline" onClick={loadQuestions}>Retry</Button>
          </div>
        ) : filteredQuestions.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 border border-dashed border-zinc-800 rounded-3xl bg-zinc-900/20 text-center">
            <MessageSquare className="w-12 h-12 text-zinc-600 mb-4" />
            <h3 className="text-xl font-medium mb-2">No questions found</h3>
            <p className="text-zinc-500 max-w-md mx-auto mb-8">
              {searchQuery ? `No results for "${searchQuery}"` : "Be the first to ask a question in this subject!"}
            </p>
            <Button variant="outline" onClick={() => {setSearchQuery(""); setSelectedSubject("All");}}>
              Clear Filters
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {filteredQuestions.map((question, idx) => (
              <motion.div
                key={question._id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
              >
                <Link to={`/app/qa/${question._id}`}>
                  <Card className="bg-zinc-900/40 border-zinc-800 hover:border-purple-900/50 transition-all group overflow-hidden">
                    <CardHeader className="pb-2">
                      <div className="flex justify-between items-start gap-4">
                        <Badge variant="outline" className="bg-purple-950/20 text-purple-300 border-purple-900/30">
                          {question.subject}
                        </Badge>
                        <span className="text-xs text-zinc-400">
                          {formatDate(question.created_at)}
                        </span>
                      </div>
                      <CardTitle className="text-lg font-medium leading-tight mt-3 text-zinc-100 group-hover:text-purple-400 transition-colors">
                        {question.content.length > 150 ? question.content.substring(0, 150) + "..." : question.content}
                      </CardTitle>
                    </CardHeader>
                    <CardFooter className="flex justify-between items-center text-sm text-zinc-400 border-t border-zinc-800/50 mt-2 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded-full bg-zinc-800 flex items-center justify-center text-[10px] font-bold text-zinc-300 border border-zinc-700">
                          {question.author_full_name.charAt(0)}
                        </div>
                        <span className="text-zinc-300">{question.author_full_name}</span>
                      </div>
                      <div className="flex items-center gap-4">
                        {question.images.length > 0 && (
                          <div className="flex items-center gap-1 text-zinc-400">
                            <ImageIcon className="w-4 h-4" />
                            <span>{question.images.length}</span>
                          </div>
                        )}
                        <div className="flex items-center gap-1 text-zinc-400">
                          <MessageSquare className="w-4 h-4" />
                          <span>{question.answers_count} {question.answers_count === 1 ? 'answer' : 'answers'}</span>
                        </div>
                      </div>
                    </CardFooter>
                  </Card>
                </Link>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      <CreateQuestionModal 
        isOpen={isCreateModalOpen} 
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={loadQuestions}
      />
    </div>
  );
}
