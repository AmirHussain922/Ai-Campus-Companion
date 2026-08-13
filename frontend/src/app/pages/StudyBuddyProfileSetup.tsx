import { useState, useEffect } from "react";
import { motion } from "motion/react";
import { ArrowLeft, Save, User } from "lucide-react";
import { Link } from "react-router";
import { studyBuddyService, StudyBuddyProfile, MatchReason } from "../services/studyBuddyService";
import { useStore } from "../store";
import { cn } from "../utils";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";

interface FormField {
  name: string;
  label: string;
  type: "text" | "select" | "textarea";
  options?: string[];
  required?: boolean;
}

const academicYears = ["Freshman", "Sophomore", "Junior", "Senior", "Graduate"];

export default function StudyBuddyProfileSetup() {
  const user = useStore(state => state.user);
  const [profile, setProfile] = useState<StudyBuddyProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Form state
  const [formData, setFormData] = useState({
    country: "",
    city: "",
    campus_university: "",
    major: "",
    academic_year: "",
    strong_subjects: [] as string[],
    weak_subjects: [] as string[],
    bio: "",
  });

  // Available subjects for selection
  const availableSubjects = [
    "Mathematics", "Physics", "Chemistry", "Biology", "Computer Science",
    "Engineering", "Literature", "History", "Psychology", "Economics",
    "Business", "Arts", "Music", "Languages", "Philosophy", "Politics",
    "Sociology", "Geography", "Education", "Health Sciences",
    "Environmental Science", "Sports Science"
  ];

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      setLoading(true);
      setError("");
      const profile = await studyBuddyService.getProfile();
      setProfile(profile);
      setFormData({
        country: profile.country || "",
        city: profile.city || "",
        campus_university: profile.campus_university || "",
        major: profile.major || "",
        academic_year: profile.academic_year || "",
        strong_subjects: profile.strong_subjects || [],
        weak_subjects: profile.weak_subjects || [],
        bio: profile.bio || "",
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load profile");
    } finally {
      setLoading(false);
    }
  };

  const toggleSubject = (subject: string, type: "strong" | "weak") => {
    const key = type === "strong" ? "strong_subjects" : "weak_subjects";
    setFormData(prev => {
      const subjects = Array.isArray(prev[key]) ? [...prev[key]] : [];
      const index = subjects.indexOf(subject);
      if (index > -1) {
        subjects.splice(index, 1);
      } else {
        subjects.push(subject);
      }
      return {
        ...prev,
        [key]: subjects,
      };
    });
  };

  const saveProfile = async () => {
    // Validate required fields
    if (!formData.campus_university || !formData.major || !formData.academic_year) {
      setError("Please fill in all required fields");
      return;
    }

    try {
      setSaving(true);
      setError("");
      setSuccess("");
      await studyBuddyService.updateProfile({
        country: formData.country,
        city: formData.city,
        campus_university: formData.campus_university,
        major: formData.major,
        academic_year: formData.academic_year,
        strong_subjects: formData.strong_subjects,
        weak_subjects: formData.weak_subjects,
        bio: formData.bio,
      });
      setSuccess("Profile saved successfully!");
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save profile");
    } finally {
      setSaving(false);
    }
  };

  const isFormComplete = () => {
    return formData.campus_university &&
           formData.major &&
           formData.academic_year;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-zinc-950">
        <div className="text-zinc-500">Loading profile...</div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto bg-zinc-950 p-4 sm:p-6 md:p-8 custom-scrollbar h-full">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link to="/app/me" className="inline-flex items-center gap-2 text-zinc-400 hover:text-white mb-4">
            <ArrowLeft className="w-4 h-4" />
            Back to Profile
          </Link>
          <h1 className="text-3xl sm:text-4xl font-light tracking-tighter">
            Create Your Study Buddy Profile
          </h1>
          <p className="text-zinc-400 text-sm mt-2">
            Tell us about yourself so we can find the perfect study partners
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

        {success && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 p-4 bg-emerald-900/20 border border-emerald-800 rounded-xl"
          >
            <p className="text-emerald-400 text-sm">{success}</p>
          </motion.div>
        )}

        <form onSubmit={(e) => { e.preventDefault(); saveProfile(); }} className="space-y-6">
          {/* Personal Information */}
          <section className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-6">
            <h2 className="text-lg font-medium mb-4 flex items-center gap-2">
              <User className="w-5 h-5" />
              Personal Information
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-zinc-300 mb-2">
                  Country <span className="text-red-400">*</span>
                </label>
                <Input
                  placeholder="e.g., United States"
                  value={formData.country}
                  onChange={(e) => setFormData({ ...formData, country: e.target.value })}
                />
              </div>

              <div>
                <label className="block text-sm text-zinc-300 mb-2">
                  City <span className="text-red-400">*</span>
                </label>
                <Input
                  placeholder="e.g., New York"
                  value={formData.city}
                  onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                />
              </div>
            </div>
          </section>

          {/* Academic Information */}
          <section className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-6">
            <h2 className="text-lg font-medium mb-4 flex items-center gap-2">
              <User className="w-5 h-5" />
              Academic Information
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-zinc-300 mb-2">
                  Campus / University <span className="text-red-400">*</span>
                </label>
                <Input
                  placeholder="e.g., Harvard University"
                  value={formData.campus_university}
                  onChange={(e) => setFormData({ ...formData, campus_university: e.target.value })}
                />
              </div>

              <div>
                <label className="block text-sm text-zinc-300 mb-2">
                  Major <span className="text-red-400">*</span>
                </label>
                <Input
                  placeholder="e.g., Computer Science"
                  value={formData.major}
                  onChange={(e) => setFormData({ ...formData, major: e.target.value })}
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm text-zinc-300 mb-2">
                  Academic Year <span className="text-red-400">*</span>
                </label>
                <select
                  value={formData.academic_year}
                  onChange={(e) => setFormData({ ...formData, academic_year: e.target.value })}
                  className="w-full px-4 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-100 focus:outline-none focus:border-zinc-500 text-sm"
                >
                  <option value="" className="text-zinc-500">Select your year</option>
                  {academicYears.map(year => (
                    <option key={year} value={year} className="text-zinc-100">{year}</option>
                  ))}
                </select>
              </div>
            </div>
          </section>

          {/* Subjects */}
          <section className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-6">
            <h2 className="text-lg font-medium mb-4">Subjects</h2>

            <div className="space-y-6">
              {/* Strong Subjects */}
              <div>
                <label className="block text-sm text-zinc-300 mb-2">
                  Subjects You're Strong In
                </label>
                <div className="flex flex-wrap gap-2">
                  {availableSubjects.map(subject => (
                    <button
                      key={subject}
                      type="button"
                      onClick={() => toggleSubject(subject, "strong")}
                      className={cn(
                        "px-3 py-1.5 rounded-lg text-sm transition-all",
                        formData.strong_subjects.includes(subject)
                          ? "bg-purple-600 text-white"
                          : "bg-zinc-800 text-zinc-300 hover:bg-zinc-700"
                      )}
                    >
                      {subject}
                    </button>
                  ))}
                </div>
              </div>

              {/* Weak Subjects */}
              <div>
                <label className="block text-sm text-zinc-300 mb-2">
                  Subjects You Need Help With
                </label>
                <div className="flex flex-wrap gap-2">
                  {availableSubjects.map(subject => (
                    <button
                      key={subject}
                      type="button"
                      onClick={() => toggleSubject(subject, "weak")}
                      className={cn(
                        "px-3 py-1.5 rounded-lg text-sm transition-all",
                        formData.weak_subjects.includes(subject)
                          ? "bg-blue-600 text-white"
                          : "bg-zinc-800 text-zinc-300 hover:bg-zinc-700"
                      )}
                    >
                      {subject}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </section>

          {/* Bio */}
          <section className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-6">
            <h2 className="text-lg font-medium mb-4">About You</h2>
            <Textarea
              placeholder="Tell potential study buddies about yourself, your study habits, or what you're looking for..."
              value={formData.bio}
              onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
              rows={4}
              className="resize-none"
            />
          </section>

          {/* Actions */}
          <div className="flex items-center justify-between pt-4">
            <Link
              to="/app/me"
              className="px-4 py-2 text-zinc-400 hover:text-white transition-colors"
            >
              Cancel
            </Link>
            <div className="flex gap-3">
              <Button
                type="button"
                onClick={saveProfile}
                disabled={!isFormComplete() || saving}
                className="bg-purple-600 hover:bg-purple-700"
              >
                {saving ? "Saving..." : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    Save Profile
                  </>
                )}
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
