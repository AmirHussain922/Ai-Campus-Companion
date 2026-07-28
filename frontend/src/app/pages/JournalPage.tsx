import { useParams, Link } from "react-router";
import { ChevronLeft } from "lucide-react";
import JournalTimeline from "../components/JournalTimeline";

export default function JournalPage() {
  const { companionId } = useParams<{ companionId: string }>();

  if (!companionId) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <p className="text-slate-400">Companion not found</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 text-slate-50 px-6 py-12">
      <div className="max-w-6xl mx-auto">
        <Link
          to={`/app/companion/${companionId}/profile`}
          className="inline-flex items-center gap-2 text-slate-400 hover:text-white transition-colors mb-8"
        >
          <ChevronLeft className="w-4 h-4" />
          Back to Profile
        </Link>
        <JournalTimeline companionId={companionId} />
      </div>
    </div>
  );
}
