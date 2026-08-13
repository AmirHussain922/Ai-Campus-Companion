import { useState } from "react";
import { X, Image as ImageIcon, Loader2, Upload } from "lucide-react";
import { qaService } from "../services/qaService";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Textarea } from "./ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "./ui/dialog";
import { cn } from "../utils";

interface CreateQuestionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function CreateQuestionModal({ isOpen, onClose, onSuccess }: CreateQuestionModalProps) {
  const [content, setContent] = useState("");
  const [subject, setSubject] = useState("");
  const [images, setImages] = useState<string[]>([]);
  const [uploading, setUploading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const subjects = ["Programming", "Mathematics", "Physics", "Chemistry", "Biology", "Literature", "History", "Other"];

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setUploading(true);
      setError("");
      const imageUrl = await qaService.uploadImage(file);
      setImages(prev => [...prev, imageUrl]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to upload image");
    } finally {
      setUploading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim() || !subject) {
      setError("Please fill in all required fields");
      return;
    }

    try {
      setSubmitting(true);
      setError("");
      await qaService.createQuestion({
        content: content.trim(),
        subject,
        images,
      });
      setContent("");
      setSubject("");
      setImages([]);
      onSuccess();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create question");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-zinc-950 border-zinc-800 text-zinc-50 max-w-2xl max-h-[95vh] overflow-y-auto custom-scrollbar">
        <DialogHeader>
          <DialogTitle className="text-2xl font-light tracking-tighter">Ask a Question</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6 py-4">
          {error && (
            <div className="p-3 bg-red-900/20 border border-red-800 rounded-lg text-red-400 text-sm">
              {error}
            </div>
          )}

          <div className="space-y-2">
            <label className="text-sm font-medium text-zinc-300">Subject</label>
            <div className="flex flex-wrap gap-2">
              {subjects.map(s => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setSubject(s)}
                  className={cn(
                    "px-3 py-1.5 rounded-lg text-sm transition-all border",
                    subject === s
                      ? "bg-purple-600 border-purple-600 text-white"
                      : "bg-zinc-900 border-zinc-800 text-zinc-300 hover:border-zinc-700"
                  )}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-zinc-300">Your Question</label>
            <Textarea
              placeholder="What would you like to ask? Be as specific as possible."
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className="min-h-[150px] bg-zinc-900 border-zinc-800 focus:border-purple-500 transition-colors resize-none text-zinc-100"
              required
            />
          </div>

          <div className="space-y-4">
            <label className="text-sm font-medium text-zinc-300">Images (Optional)</label>
            <div className="flex flex-wrap gap-4">
              {images.map((url, idx) => (
                <div key={idx} className="relative group w-24 h-24 rounded-lg overflow-hidden border border-zinc-800">
                  <img src={url} alt={`Upload ${idx}`} className="w-full h-full object-cover" />
                  <button
                    type="button"
                    onClick={() => setImages(prev => prev.filter((_, i) => i !== idx))}
                    className="absolute top-1 right-1 p-1 bg-black/50 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <X className="w-3 h-3 text-white" />
                  </button>
                </div>
              ))}
              {images.length < 3 && (
                <label className={cn(
                  "w-24 h-24 rounded-lg border border-dashed border-zinc-800 flex flex-col items-center justify-center cursor-pointer hover:border-purple-500 transition-colors",
                  uploading && "opacity-50 cursor-not-allowed"
                )}>
                  {uploading ? (
                    <Loader2 className="w-6 h-6 text-purple-500 animate-spin" />
                  ) : (
                    <>
                      <Upload className="w-6 h-6 text-zinc-500 mb-1" />
                      <span className="text-[10px] text-zinc-500">Upload</span>
                    </>
                  )}
                  <input
                    type="file"
                    className="hidden"
                    accept="image/*"
                    onChange={handleImageUpload}
                    disabled={uploading}
                  />
                </label>
              )}
            </div>
          </div>

          <DialogFooter className="pt-4 border-t border-zinc-900">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              className="border-zinc-800 text-zinc-400 hover:text-white"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={submitting || !content.trim() || !subject}
              className="bg-purple-600 hover:bg-purple-700 text-white min-w-[120px]"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Posting...
                </>
              ) : (
                "Post Question"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
