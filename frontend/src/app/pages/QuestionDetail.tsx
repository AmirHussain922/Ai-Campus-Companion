import { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router";
import { motion, AnimatePresence } from "motion/react";
import { 
  ArrowLeft, 
  MessageSquare, 
  Trash2, 
  Edit3, 
  Loader2, 
  Send,
  Image as ImageIcon,
  ExternalLink,
  MoreVertical,
  User,
  Reply,
  CornerDownRight,
  X
} from "lucide-react";
import { qaService, Question, Answer, Comment } from "../services/qaService";
import { useStore } from "../store";
import { cn, formatDate } from "../utils";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { Badge } from "../components/ui/badge";
import { Card, CardContent } from "../components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";

export default function QuestionDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const user = useStore(state => state.user);
  
  const [question, setQuestion] = useState<Question | null>(null);
  const [answers, setAnswers] = useState<Answer[]>([]);
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  
  // Answer form state
  const [answerContent, setAnswerContent] = useState("");
  const [submittingAnswer, setSubmittingAnswer] = useState(false);
  const [answerError, setAnswerError] = useState("");

  // Comment form state
  const [commentContent, setCommentContent] = useState("");
  const [submittingComment, setSubmittingComment] = useState(false);
  const [replyTo, setReplyTo] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadData();
    }
  }, [id]);

  const loadData = async () => {
    if (!id) return;
    try {
      setLoading(true);
      setError("");
      const [qData, aData, cData] = await Promise.all([
        qaService.getQuestion(id),
        qaService.listAnswers(id),
        qaService.listComments(id)
      ]);
      setQuestion(qData);
      setAnswers(aData);
      setComments(cData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load question details");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitAnswer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !answerContent.trim()) return;

    try {
      setSubmittingAnswer(true);
      setAnswerError("");
      const newAnswer = await qaService.createAnswer({
        question_id: id,
        content: answerContent.trim()
      });
      setAnswers(prev => [...prev, newAnswer]);
      setAnswerContent("");
      // Update local question answer count
      if (question) {
        setQuestion({ ...question, answers_count: question.answers_count + 1 });
      }
    } catch (err) {
      setAnswerError(err instanceof Error ? err.message : "Failed to post answer");
    } finally {
      setSubmittingAnswer(false);
    }
  };

  const handleDeleteQuestion = async () => {
    if (!id || !window.confirm("Are you sure you want to delete this question?")) return;
    
    try {
      await qaService.deleteQuestion(id);
      navigate("/app/qa");
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to delete question");
    }
  };

  const handleDeleteAnswer = async (answerId: string) => {
    if (!window.confirm("Are you sure you want to delete this answer?")) return;
    
    try {
      await qaService.deleteAnswer(answerId);
      setAnswers(prev => prev.filter(a => a._id !== answerId));
      if (question) {
        setQuestion({ ...question, answers_count: question.answers_count - 1 });
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to delete answer");
    }
  };

  const handleSubmitComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !commentContent.trim()) return;

    try {
      setSubmittingComment(true);
      const newComment = await qaService.createComment({
        question_id: id,
        content: commentContent.trim(),
        parent_id: replyTo || undefined
      });
      setComments(prev => [...prev, newComment]);
      setCommentContent("");
      setReplyTo(null);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to post comment");
    } finally {
      setSubmittingComment(false);
    }
  };

  const handleDeleteComment = async (commentId: string) => {
    if (!window.confirm("Are you sure you want to delete this comment?")) return;
    
    try {
      await qaService.deleteComment(commentId);
      // Recursively remove replies if we want, or just let backend handle it and we filter local state
      setComments(prev => prev.filter(c => c._id !== commentId && c.parent_id !== commentId));
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to delete comment");
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-zinc-950">
        <Loader2 className="w-8 h-8 text-purple-500 animate-spin mb-4" />
        <p className="text-zinc-500">Loading discussion details...</p>
      </div>
    );
  }

  if (error || !question) {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-zinc-950 p-6">
        <div className="max-w-md text-center">
          <p className="text-red-400 mb-6">{error || "Question not found"}</p>
          <Button variant="outline" onClick={() => navigate("/app/qa")}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Q&A
          </Button>
        </div>
      </div>
    );
  }

  const isAuthor = user?.email === question.author_id;

  return (
    <div className="flex-1 overflow-y-auto bg-zinc-950 p-4 sm:p-6 md:p-8 text-zinc-50 relative h-full">
      <div className="max-w-4xl mx-auto">
        {/* Back link */}
        <Link to="/app/qa" className="inline-flex items-center gap-2 text-zinc-400 hover:text-white mb-6 transition-colors">
          <ArrowLeft className="w-4 h-4" />
          Back to Discussions
        </Link>

        {/* Question Section */}
        <section className="mb-12">
          <div className="flex justify-between items-start gap-4 mb-4">
            <div className="space-y-2">
              <Badge variant="outline" className="bg-purple-950/20 text-purple-300 border-purple-900/30">
                {question.subject}
              </Badge>
              <h1 className="text-2xl sm:text-3xl font-medium tracking-tight leading-tight text-zinc-100">
                {question.content}
              </h1>
            </div>
            
            {isAuthor && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" className="text-zinc-400 hover:text-white hover:bg-zinc-900">
                    <MoreVertical className="w-5 h-5" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="bg-zinc-900 border-zinc-800 text-zinc-50">
                  <DropdownMenuItem className="focus:bg-zinc-800 cursor-pointer">
                    <Edit3 className="w-4 h-4 mr-2" />
                    Edit Question
                  </DropdownMenuItem>
                  <DropdownMenuItem 
                    className="focus:bg-red-900/20 text-red-400 focus:text-red-400 cursor-pointer"
                    onClick={handleDeleteQuestion}
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Delete Question
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-zinc-400 mb-6">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-zinc-800 flex items-center justify-center text-[10px] font-bold text-zinc-300 border border-zinc-700 flex-shrink-0">
                {question.author_full_name.charAt(0)}
              </div>
              <span className="text-zinc-200 font-medium truncate max-w-[150px] sm:max-w-none">{question.author_full_name}</span>
            </div>
            <span className="hidden sm:inline text-zinc-700">•</span>
            <span className="text-xs sm:text-sm">Asked {formatDate(question.created_at)}</span>
          </div>

          {question.images.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
              {question.images.map((url, idx) => (
                <div key={idx} className="rounded-2xl overflow-hidden border border-zinc-800 bg-zinc-900/50 aspect-video">
                  <img src={url} alt="Question visual" className="w-full h-full object-cover" />
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Comments Section */}
        <section className="mb-12">
          <div className="flex items-center gap-2 mb-6 border-b border-zinc-800 pb-2">
            <h3 className="text-sm font-medium text-zinc-300 uppercase tracking-wider">Comments</h3>
            <Badge variant="secondary" className="bg-zinc-900 text-zinc-400 text-[10px] h-4 border border-zinc-800">
              {comments.length}
            </Badge>
          </div>

          <div className="space-y-4 mb-6">
            {comments.filter(c => !c.parent_id).map(comment => (
              <div key={comment._id} className="space-y-4">
                <CommentItem 
                  comment={comment} 
                  currentUserEmail={user?.email} 
                  onDelete={handleDeleteComment}
                  onReply={(id) => {
                    setReplyTo(id);
                    // Focus comment input
                    document.getElementById('comment-input')?.focus();
                  }}
                />
                
                {/* Replies */}
                <div className="pl-8 border-l border-zinc-800 space-y-4">
                  {comments.filter(c => c.parent_id === comment._id).map(reply => (
                    <CommentItem 
                      key={reply._id}
                      comment={reply} 
                      currentUserEmail={user?.email} 
                      onDelete={handleDeleteComment}
                      isReply
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>

          <form onSubmit={handleSubmitComment} className="relative">
            {replyTo && (
              <div className="flex justify-between items-center px-3 py-1 bg-purple-900/20 rounded-t-lg border-x border-t border-purple-900/30 text-[10px] text-purple-300">
                <span>Replying to {comments.find(c => c._id === replyTo)?.author_full_name}</span>
                <button type="button" onClick={() => setReplyTo(null)} className="hover:text-white">
                  <X className="w-3 h-3" />
                </button>
              </div>
            )}
            <Input 
              id="comment-input"
              placeholder={replyTo ? "Write a reply..." : "Add a comment..."}
              value={commentContent}
              onChange={(e) => setCommentContent(e.target.value)}
              className={cn(
                "bg-zinc-900 border-zinc-800 pr-12 text-zinc-100",
                replyTo ? "rounded-t-none border-t-purple-900/30" : ""
              )}
            />
            <Button 
              type="submit"
              size="icon"
              disabled={submittingComment || !commentContent.trim()}
              className="absolute right-1 top-1 h-8 w-8 bg-transparent hover:bg-zinc-800 text-zinc-500 hover:text-purple-400"
            >
              {submittingComment ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </Button>
          </form>
        </section>

        {/* Answers Header */}
        <div className="flex items-center gap-2 mb-6 border-b border-zinc-800 pb-4">
          <h2 className="text-xl font-medium text-zinc-100">Answers</h2>
          <Badge variant="secondary" className="bg-zinc-900 text-zinc-300 font-normal border border-zinc-800">
            {question.answers_count}
          </Badge>
        </div>

        {/* Answer Form */}
        <div className="mb-12 bg-zinc-900/30 border border-zinc-800 rounded-2xl p-6">
          <h3 className="text-sm font-medium text-zinc-300 uppercase tracking-wider mb-4">Provide an Answer</h3>
          <form onSubmit={handleSubmitAnswer} className="space-y-4">
            {answerError && (
              <div className="p-3 bg-red-900/20 border border-red-800 rounded-lg text-red-400 text-sm">
                {answerError}
              </div>
            )}
            <Textarea
              placeholder="Share your knowledge or help out..."
              value={answerContent}
              onChange={(e) => setAnswerContent(e.target.value)}
              className="min-h-[100px] bg-zinc-950 border-zinc-800 focus:border-purple-500 transition-colors resize-none text-zinc-100"
              required
            />
            <div className="flex justify-end">
              <Button 
                type="submit" 
                disabled={submittingAnswer || !answerContent.trim()}
                className="bg-purple-600 hover:bg-purple-700 text-white min-w-[140px]"
              >
                {submittingAnswer ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Send className="w-4 h-4 mr-2" />
                )}
                Post Answer
              </Button>
            </div>
          </form>
        </div>

        {/* Answers List */}
        <div className="space-y-6">
          {answers.length === 0 ? (
            <div className="py-12 text-center text-zinc-600">
              <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-20" />
              <p>No answers yet. Be the first to help!</p>
            </div>
          ) : (
            answers.map((answer, idx) => (
              <motion.div
                key={answer._id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.1 }}
              >
                <Card className="bg-zinc-900/20 border-zinc-800 overflow-hidden">
                  <CardContent className="p-6">
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center text-xs font-bold text-zinc-300 border border-zinc-700">
                          {answer.author_full_name.charAt(0)}
                        </div>
                        <div>
                          <p className="text-sm font-medium text-zinc-100">{answer.author_full_name}</p>
                          <p className="text-[10px] text-zinc-400 uppercase tracking-tighter">
                            {formatDate(answer.created_at)}
                          </p>
                        </div>
                      </div>
                      
                      {user?.email === answer.author_id && (
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8 text-zinc-400 hover:text-white">
                              <MoreVertical className="w-4 h-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="bg-zinc-900 border-zinc-800 text-zinc-50">
                            <DropdownMenuItem className="focus:bg-zinc-800 cursor-pointer">
                              <Edit3 className="w-3 h-3 mr-2" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem 
                              className="focus:bg-red-900/20 text-red-400 focus:text-red-400 cursor-pointer"
                              onClick={() => handleDeleteAnswer(answer._id)}
                            >
                              <Trash2 className="w-3 h-3 mr-2" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      )}
                    </div>
                    
                    <div className="text-zinc-200 whitespace-pre-wrap leading-relaxed">
                      {answer.content}
                    </div>

                    {answer.links.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-zinc-800/50 flex flex-wrap gap-3">
                        {answer.links.map((link, lIdx) => (
                          <a 
                            key={lIdx}
                            href={link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1.5 text-xs text-purple-400 hover:text-purple-300 transition-colors"
                          >
                            <ExternalLink className="w-3 h-3" />
                            Resource {lIdx + 1}
                          </a>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

function CommentItem({ 
  comment, 
  currentUserEmail, 
  onDelete, 
  onReply, 
  isReply = false 
}: { 
  comment: Comment; 
  currentUserEmail?: string; 
  onDelete: (id: string) => void; 
  onReply?: (id: string) => void;
  isReply?: boolean;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(comment.content);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleUpdate = async () => {
    if (!editContent.trim()) return;
    try {
      setIsSubmitting(true);
      await qaService.updateComment(comment._id, editContent.trim());
      comment.content = editContent.trim(); // Optimistic update
      setIsEditing(false);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to update comment");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="group">
      <div className="flex gap-3">
        {!isReply ? (
          <div className="w-8 h-8 rounded-full bg-zinc-900 flex items-center justify-center text-[10px] font-bold text-zinc-400 border border-zinc-800">
            {comment.author_full_name.charAt(0)}
          </div>
        ) : (
          <CornerDownRight className="w-4 h-4 text-zinc-500 mt-2 ml-1" />
        )}
        
        <div className="flex-1 space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-zinc-200">{comment.author_full_name}</span>
            <span className="text-[10px] text-zinc-500">{formatDate(comment.created_at)}</span>
          </div>
          
          {isEditing ? (
            <div className="space-y-2 mt-1">
              <Input 
                value={editContent} 
                onChange={(e) => setEditContent(e.target.value)}
                className="bg-zinc-950 border-zinc-800 h-8 text-sm text-zinc-100"
                autoFocus
              />
              <div className="flex gap-2">
                <Button size="sm" className="h-7 text-[10px]" onClick={handleUpdate} disabled={isSubmitting}>
                  Save
                </Button>
                <Button size="sm" variant="ghost" className="h-7 text-[10px]" onClick={() => setIsEditing(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            <p className="text-sm text-zinc-300 leading-relaxed">{comment.content}</p>
          )}

          <div className="flex items-center gap-4 opacity-0 group-hover:opacity-100 transition-opacity pt-1">
            {onReply && (
              <button 
                onClick={() => onReply(comment._id)}
                className="text-[10px] text-zinc-500 hover:text-purple-400 flex items-center gap-1"
              >
                <Reply className="w-3 h-3" />
                Reply
              </button>
            )}
            
            {currentUserEmail === comment.author_id && (
              <>
                <button 
                  onClick={() => setIsEditing(true)}
                  className="text-[10px] text-zinc-500 hover:text-white flex items-center gap-1"
                >
                  <Edit3 className="w-3 h-3" />
                  Edit
                </button>
                <button 
                  onClick={() => onDelete(comment._id)}
                  className="text-[10px] text-zinc-500 hover:text-red-400 flex items-center gap-1"
                >
                  <Trash2 className="w-3 h-3" />
                  Delete
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
