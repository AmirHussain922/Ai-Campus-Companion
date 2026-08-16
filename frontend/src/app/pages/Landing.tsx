import { motion } from "motion/react";
import { Link } from "react-router";
import { INITIAL_COMPANIONS } from "../store";
import { useState, useEffect } from "react";
import { submitContactForm, type ContactFormData } from "../services/contactService";

export default function Landing() {
  // Form State
  const [formData, setFormData] = useState<ContactFormData>({
    name: "",
    email: "",
    feedback_type: "",
    message: ""
  });

  const [messageLength, setMessageLength] = useState(0);
  const [formState, setFormState] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');

  // Character counter
  useEffect(() => {
    setMessageLength(formData.message.length);
  }, [formData.message]);

  // Form Submission Handler
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate required fields
    if (!formData.feedback_type) {
      setFormState({
        status: 'error',
        error: 'Please select a feedback type'
      });
      return;
    }

    if (!formData.message) {
      setFormState({
        status: 'error',
        error: 'Message is required'
      });
      return;
    }

    setFormState({ status: 'loading', error: undefined });

    try {
      const response = await submitContactForm(formData);

      if (response.success) {
        setFormState({ status: 'success', error: undefined });

        // Reset form after 3 seconds
        setTimeout(() => {
          setFormData({
            name: "",
            email: "",
            feedback_type: "",
            message: ""
          });
          setFormState({ status: 'idle', error: undefined });
        }, 3000);
      } else {
        setFormState({
          status: 'error',
          error: response.message || 'Failed to submit. Please try again.'
        });
      }
    } catch (error: any) {
      setFormState({
        status: 'error',
        error: error.response?.data?.detail?.message ||
               error.response?.data?.message ||
               'We couldn\'t submit your feedback right now. Please try again.'
      });
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-50 selection:bg-purple-500/30">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 px-6 py-6 flex justify-between items-center bg-zinc-950/50 backdrop-blur-md border-b border-zinc-800/50">
        <Link
          to="/"
          className="flex items-center gap-2 group"
        >
          <div className="relative">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center group-hover:scale-105 transition-transform">
              <svg
                className="w-6 h-6 text-white"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                />
              </svg>
            </div>
          </div>
          <span className="text-xl font-semibold tracking-tight">
            AI Campus Companion
          </span>
        </Link>

        <div className="hidden md:flex items-center gap-8">
          <Link
            to="/app"
            className="text-sm font-medium text-zinc-400 hover:text-white transition-colors"
          >
            Features
          </Link>
          <Link
            to="/app"
            className="text-sm font-medium text-zinc-400 hover:text-white transition-colors"
          >
            How It Works
          </Link>
          <Link
            to="/app/study-buddy/matches"
            className="text-sm font-medium text-zinc-400 hover:text-white transition-colors"
          >
            Community
          </Link>
        </div>

        <div className="flex items-center gap-4">
          <Link
            to="/login"
            className="px-4 py-2 text-sm font-medium text-zinc-300 hover:text-white transition-colors"
          >
            Sign In
          </Link>
          <Link
            to="/signup"
            className="px-5 py-2.5 text-sm font-semibold bg-white text-zinc-950 rounded-lg hover:bg-zinc-200 transition-colors"
          >
            Get Started
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative min-h-screen flex flex-col justify-center items-center pt-32 pb-20 px-6 overflow-hidden">
        {/* Background Effects */}
        <div className="absolute inset-0 z-0 overflow-hidden">
          {/* Subtle gradient background */}
          <div className="absolute inset-0 bg-gradient-to-b from-purple-900/5 via-zinc-950 to-zinc-950" />

          {/* Top glow */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-purple-600/10 rounded-full blur-[120px] opacity-50" />

          {/* Bottom glow */}
          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-blue-600/10 rounded-full blur-[100px] opacity-50" />

          {/* Grid pattern */}
          <div className="absolute inset-0 opacity-5">
            <div className="w-full h-full" style={{
              backgroundImage: `
                linear-gradient(to right, rgba(255,255,255,0.1) 1px, transparent 1px),
                linear-gradient(to bottom, rgba(255,255,255,0.1) 1px, transparent 1px)
              `,
              backgroundSize: '60px 60px'
            }} />
          </div>
        </div>

        <div className="relative z-10 max-w-5xl mx-auto text-center">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-zinc-800 bg-zinc-900/50 backdrop-blur-sm text-sm font-medium text-zinc-400 mb-8"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-purple-500" />
            Explore Campus Life. Connect with Students. Build Your Network.
          </motion.div>

          {/* Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-5xl md:text-6xl font-semibold tracking-tight leading-tight mb-6 max-w-4xl mx-auto"
          >
            AI-Powered Campus Stories<br />Plus Real Student Community
          </motion.h1>

          {/* Subheadline */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-lg md:text-xl text-zinc-400 max-w-2xl mx-auto mb-10 leading-relaxed"
          >
            Explore campus life through interactive stories with AI characters, discover university
            mates based on shared interests, ask questions in peer Q&A, and connect directly with students.
          </motion.p>

          {/* CTAs */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16"
          >
            <Link
              to="/signup"
              className="w-full sm:w-auto px-8 py-4 text-base font-semibold bg-white text-zinc-950 rounded-lg hover:bg-zinc-200 transition-colors"
            >
              Join the Community
            </Link>
            <Link
              to="/app"
              className="w-full sm:w-auto px-8 py-4 text-base font-medium text-zinc-300 hover:text-white border border-zinc-700 hover:border-zinc-500 rounded-lg transition-colors"
            >
              Explore Features
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Student Community Features */}
      <section className="py-24 px-6 bg-zinc-900/20 border-y border-zinc-800 relative z-20">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-semibold tracking-tight mb-4">
              Connect. Ask. Build Together.
            </h2>
            <p className="text-lg text-zinc-400 max-w-2xl mx-auto">
              Find university mates, ask questions in peer Q&A, and connect directly with students.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                icon: (
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zM3 10l.747-1.53A2 2 0 015.302 6h13.396a2 2 0 011.555 2.47L17 10m-7 14v-2m0 0V6m0 0a2 2 0 102 0m-2 0H9" />
                  </svg>
                ),
                title: "Find University Mates",
                description: "Discover students who share your university, interests, subjects, and goals. Build your academic network.",
                color: "blue"
              },
              {
                icon: (
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                ),
                title: "Peer Q&A",
                description: "Ask questions and get answers directly from fellow students. Share knowledge and learn together.",
                color: "purple"
              },
              {
                icon: (
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                ),
                title: "Direct Chat",
                description: "Connect with students privately and continue conversations. Build relationships and network.",
                color: "emerald"
              }
            ].map((point, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: idx * 0.1 }}
                className="p-6 rounded-xl bg-zinc-900/50 border border-zinc-800 hover:border-zinc-700 transition-colors"
              >
                <div className={`w-12 h-12 rounded-lg bg-${point.color}-600/20 flex items-center justify-center mb-4`}>
                  {point.icon}
                </div>
                <h3 className="text-lg font-semibold mb-2">
                  {point.title}
                </h3>
                <p className="text-sm text-zinc-400 leading-relaxed">
                  {point.description}
                </p>
              </motion.div>
            ))}
          </div>

          {/* Campus Stories - moved to a secondary position */}
          <div className="mt-8 p-6 rounded-xl bg-zinc-900/50 border border-zinc-800 hover:border-zinc-700 transition-colors">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-purple-600/20 to-blue-600/20 flex items-center justify-center flex-shrink-0">
                <svg className="w-6 h-6 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div>
                <h3 className="text-lg font-semibold mb-2">Campus Stories</h3>
                <p className="text-sm text-zinc-400 leading-relaxed">
                  Explore campus life through interactive stories with AI-powered characters. Meet Oliver as the Study Buddy character and discover different perspectives of university life.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-24 px-6 bg-zinc-950 relative z-20">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-semibold tracking-tight mb-4">
              How It Works
            </h2>
            <p className="text-lg text-zinc-400">
              Get started in three simple steps
            </p>
          </div>

          <div className="space-y-12">
            {[
              {
                number: "01",
                title: "Create Your Account",
                description: "Sign up to join the student community and explore campus life through interactive stories."
              },
              {
                number: "02",
                title: "Discover Connections",
                description: "Find university mates based on shared academic interests, subjects, and goals."
              },
              {
                number: "03",
                title: "Connect & Participate",
                description: "Ask questions in peer Q&A, chat directly with students, and explore campus stories."
              }
            ].map((step, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: idx * 0.1 }}
                className="flex gap-8 items-start"
              >
                {/* Number */}
                <div className="flex-shrink-0">
                  <div className="w-16 h-16 rounded-xl bg-zinc-900 border border-zinc-800 flex items-center justify-center">
                    <span className="text-2xl font-semibold text-zinc-500">
                      {step.number}
                    </span>
                  </div>
                </div>

                {/* Content */}
                <div className="flex-1">
                  <h3 className="text-xl font-semibold mb-2">
                    {step.title}
                  </h3>
                  <p className="text-zinc-400 leading-relaxed">
                    {step.description}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Oliver - Study Buddy Character */}
      <section className="py-24 px-6 bg-zinc-900/20 border-y border-zinc-800 relative z-20">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            {/* Oliver Character Card */}
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="order-2 lg:order-1"
            >
              <div className="bg-zinc-900/80 border border-zinc-700 rounded-2xl p-8 relative overflow-hidden">
                {/* Story snippet background */}
                <div className="absolute inset-0 opacity-5">
                  <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-600 to-purple-600" />
                </div>

                {/* Character header */}
                <div className="flex items-center gap-4 mb-6">
                  <img
                    src="https://images.unsplash.com/photo-1614492898637-435e0f87cef8?w=1080&q=80"
                    alt="Oliver"
                    className="w-20 h-20 rounded-xl object-cover border-2 border-blue-500/50"
                  />
                  <div>
                    <h3 className="text-2xl font-semibold text-blue-400">Oliver</h3>
                    <p className="text-sm text-zinc-400">Study Buddy Character</p>
                    <div className="flex gap-2 mt-2">
                      {['Logical', 'Analytical', 'Calm'].map((trait, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 text-xs bg-blue-900/30 text-blue-300 rounded border border-blue-700/30"
                        >
                          {trait}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Story narrative */}
                <div className="mb-6">
                  <h4 className="text-sm font-medium text-zinc-400 uppercase tracking-wide mb-3">
                    Story Context
                  </h4>
                  <p className="text-zinc-300 leading-relaxed mb-4">
                    "A perfectionist driven by academic excellence. He relies on you to stay grounded when the pressure gets to be too much."
                  </p>
                  <p className="text-zinc-400 leading-relaxed text-sm">
                    Experience Oliver's journey through campus life—from library sessions to late-night debates. As you interact with him in stories, your conversations shape his development and unlock new story episodes.
                  </p>
                </div>

                {/* Story preview */}
                <div className="bg-zinc-950/50 rounded-lg p-4 border border-zinc-800">
                  <h4 className="text-sm font-medium text-zinc-400 uppercase tracking-wide mb-2">
                    Featured Episode: The First Library Session
                  </h4>
                  <p className="text-sm text-zinc-300 italic">
                    "You meet up to organize your semester syllabus. Oliver starts explaining his exact color-coding system..."
                  </p>
                </div>
              </div>
            </motion.div>

            {/* Text content */}
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="order-1 lg:order-2"
            >
              <h2 className="text-4xl md:text-5xl font-semibold tracking-tight mb-6">
                Meet Oliver,<br />Your Study Buddy Character
              </h2>
              <p className="text-lg text-zinc-400 mb-6 leading-relaxed">
                Oliver is not just another chatbot—he's a character in the campus-life story. As you explore his story, you'll discover different sides of university life.
              </p>
              <p className="text-lg text-zinc-400 mb-8 leading-relaxed">
                Through interactive story episodes, Oliver navigates the challenges of academic pressure, late-night study sessions, and campus adventures. Your conversations shape his development and unlock new story content.
              </p>
              <ul className="space-y-4">
                <li className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-blue-600/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg className="w-4 h-4 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <span className="text-zinc-300">
                    <strong className="text-zinc-200">Story-driven interactions</strong>—your choices shape Oliver's development
                  </span>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-blue-600/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg className="w-4 h-4 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <span className="text-zinc-300">
                    <strong className="text-zinc-200">Multiple story episodes</strong>—unlock new chapters as you progress
                  </span>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-blue-600/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <svg className="w-4 h-4 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <span className="text-zinc-300">
                    <strong className="text-zinc-200">Character development</strong>—build relationships and influence his journey
                  </span>
                </li>
              </ul>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Other Companions */}
      <section className="py-24 px-6 bg-zinc-950 relative z-20">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-semibold tracking-tight mb-4">
              More Campus Characters
            </h2>
            <p className="text-lg text-zinc-400 max-w-2xl mx-auto">
              Explore different sides of campus life through interactive stories with diverse characters.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {INITIAL_COMPANIONS.slice(1).map((comp, idx) => (
              <motion.div
                key={comp.id}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: idx * 0.1 }}
                className="group relative p-6 rounded-xl bg-zinc-900/50 border border-zinc-800 hover:border-zinc-700 transition-colors overflow-hidden"
              >
                {/* Background accent */}
                <div className="absolute inset-0 bg-gradient-to-br from-purple-900/10 to-blue-900/10 opacity-0 group-hover:opacity-100 transition-opacity" />

                <div className="relative">
                  {/* Avatar */}
                  <div className="w-16 h-16 rounded-full overflow-hidden mb-4 mx-auto">
                    <img
                      src={comp.avatarUrl}
                      alt={comp.name}
                      className="w-full h-full object-cover"
                    />
                  </div>

                  {/* Info */}
                  <h3 className="text-lg font-semibold text-center mb-1">
                    {comp.name}
                  </h3>
                  <p className="text-sm text-zinc-500 text-center mb-2">
                    {comp.personality}
                  </p>
                  <p className="text-xs text-zinc-400 text-center leading-relaxed">
                    {comp.story}
                  </p>

                  {/* Traits */}
                  <div className="flex flex-wrap gap-2 justify-center mt-4">
                    {comp.traits.slice(0, 3).map((trait, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 text-xs bg-zinc-800 text-zinc-400 rounded"
                      >
                        {trait}
                      </span>
                    ))}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          <div className="text-center mt-12">
            <Link
              to="/app"
              className="inline-flex items-center gap-2 text-sm font-medium text-purple-400 hover:text-purple-300 transition-colors"
            >
              Explore All Companions
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
              </svg>
            </Link>
          </div>
        </div>
      </section>

      {/* AI Companions Section */}
      <section className="py-24 px-6 bg-zinc-950 relative z-20">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-semibold tracking-tight mb-4">
              Experience Campus Life Through Stories
            </h2>
            <p className="text-lg text-zinc-400 max-w-2xl mx-auto">
              Meet AI-powered characters and explore different sides of campus life through interactive stories.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
            {INITIAL_COMPANIONS.slice(0, 5).map((comp, idx) => (
              <motion.div
                key={comp.id}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: idx * 0.1 }}
                className="group relative p-6 rounded-xl bg-zinc-900/50 border border-zinc-800 hover:border-zinc-700 transition-colors overflow-hidden"
              >
                {/* Background accent */}
                <div className="absolute inset-0 bg-gradient-to-br from-purple-900/10 to-blue-900/10 opacity-0 group-hover:opacity-100 transition-opacity" />

                <div className="relative">
                  {/* Avatar */}
                  <div className="w-16 h-16 rounded-full overflow-hidden mb-4 mx-auto">
                    <img
                      src={comp.avatarUrl}
                      alt={comp.name}
                      className="w-full h-full object-cover"
                    />
                  </div>

                  {/* Info */}
                  <h3 className="text-lg font-semibold text-center mb-1">
                    {comp.name}
                  </h3>
                  <p className="text-sm text-zinc-500 text-center mb-2">
                    {comp.personality}
                  </p>
                  <p className="text-xs text-zinc-400 text-center leading-relaxed">
                    {comp.story}
                  </p>

                  {/* Traits */}
                  <div className="flex flex-wrap gap-2 justify-center mt-4">
                    {comp.traits.slice(0, 3).map((trait, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 text-xs bg-zinc-800 text-zinc-400 rounded"
                      >
                        {trait}
                      </span>
                    ))}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          <div className="text-center">
            <Link
              to="/app"
              className="inline-flex items-center gap-2 text-sm font-medium text-purple-400 hover:text-purple-300 transition-colors"
            >
              Explore All Companions
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
              </svg>
            </Link>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6 bg-zinc-950 relative z-20">
        <div className="max-w-4xl mx-auto">
          <div className="text-center">
            <h2 className="text-4xl md:text-5xl font-semibold tracking-tight mb-6">
              Explore Campus Life Your Way
            </h2>
            <p className="text-lg text-zinc-400 mb-10 max-w-2xl mx-auto">
              Connect with students, ask questions in peer Q&A, and explore interactive campus stories.
              Start your campus community journey today.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                to="/signup"
                className="w-full sm:w-auto px-8 py-4 text-base font-semibold bg-white text-zinc-950 rounded-lg hover:bg-zinc-200 transition-colors"
              >
                Get Started
              </Link>
              <Link
                to="/app"
                className="w-full sm:w-auto px-8 py-4 text-base font-medium text-zinc-300 hover:text-white border border-zinc-700 hover:border-zinc-500 rounded-lg transition-colors"
              >
                Explore Features
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Feedback Section */}
      <section className="py-24 px-6 bg-zinc-900/20 border-y border-zinc-800 relative z-20">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-semibold tracking-tight mb-4">
              Your Feedback Matters
            </h2>
            <p className="text-lg text-zinc-400 max-w-2xl mx-auto">
              Help us improve AI Campus Companion by sharing your thoughts
            </p>
          </div>

          <div className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-8 md:p-12">
            {/* Success/Error Message */}
            {formState.status === 'success' && (
              <div className="mb-8 p-6 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-emerald-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <div>
                    <h4 className="font-medium text-emerald-500 mb-2">Success!</h4>
                    <p className="text-sm text-zinc-400">
                      Thank you! Your feedback has been submitted successfully.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {formState.status === 'error' && (
              <div className="mb-8 p-6 bg-red-500/10 border border-red-500/20 rounded-lg">
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <div>
                    <h4 className="font-medium text-red-500 mb-2">Error</h4>
                    <p className="text-sm text-zinc-400">
                      {formState.error || 'We couldn\'t submit your feedback right now. Please try again.'}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Feedback Form */}
            <form id="feedback-form" className="space-y-6" onSubmit={handleSubmit}>
              {/* Name (Optional) */}
              <div>
                <label htmlFor="feedback-name" className="block text-sm font-medium text-zinc-300 mb-2">
                  Name <span className="text-zinc-500">(optional)</span>
                </label>
                <input
                  type="text"
                  id="feedback-name"
                  name="name"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  className="w-full px-4 py-3 bg-zinc-950 border border-zinc-700 rounded-lg text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  placeholder="Your name"
                  maxLength={100}
                  disabled={formState.status === 'loading'}
                />
              </div>

              {/* Email */}
              <div>
                <label htmlFor="feedback-email" className="block text-sm font-medium text-zinc-300 mb-2">
                  Email <span className="text-zinc-500">(optional - for reply)</span>
                </label>
                <input
                  type="email"
                  id="feedback-email"
                  name="email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  className="w-full px-4 py-3 bg-zinc-950 border border-zinc-700 rounded-lg text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  placeholder="you@example.com"
                  disabled={formState.status === 'loading'}
                />
              </div>

              {/* Feedback Type */}
              <div>
                <label htmlFor="feedback-type" className="block text-sm font-medium text-zinc-300 mb-2">
                  Feedback Type <span className="text-zinc-500">*</span>
                </label>
                <select
                  id="feedback-type"
                  name="feedback_type"
                  value={formData.feedback_type}
                  onChange={(e) => setFormData({...formData, feedback_type: e.target.value as any})}
                  className="w-full px-4 py-3 bg-zinc-950 border border-zinc-700 rounded-lg text-sm text-zinc-100 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  required
                  disabled={formState.status === 'loading'}
                >
                  <option value="">Select a category</option>
                  <option value="general">General Feedback</option>
                  <option value="bug">Bug Report</option>
                  <option value="feature">Feature Request</option>
                  <option value="suggestion">Suggestion</option>
                  <option value="other">Other</option>
                </select>
              </div>

              {/* Feedback Message */}
              <div>
                <label htmlFor="feedback-message" className="block text-sm font-medium text-zinc-300 mb-2">
                  Your Message <span className="text-zinc-500">*</span>
                </label>
                <textarea
                  id="feedback-message"
                  name="message"
                  value={formData.message}
                  onChange={(e) => {
                    setFormData({...formData, message: e.target.value});
                    setMessageLength(e.target.value.length);
                  }}
                  rows={5}
                  className="w-full px-4 py-3 bg-zinc-950 border border-zinc-700 rounded-lg text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed resize-none"
                  placeholder="Share your thoughts, suggestions, or report any issues..."
                  required
                  maxLength={1000}
                  disabled={formState.status === 'loading'}
                />
                <div className="flex justify-end mt-2">
                  <span className={`text-xs ${messageLength >= 1000 ? 'text-red-500' : 'text-zinc-600'}`}>
                    {messageLength} / 1000 characters
                  </span>
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={formState.status === 'loading'}
                className="w-full px-8 py-4 text-base font-semibold bg-white text-zinc-950 rounded-lg hover:bg-zinc-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {formState.status === 'loading' ? (
                  <>
                    <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 3.582 0 8h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Submitting...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                    Submit Feedback
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t border-zinc-900 relative z-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-12">
            {/* Logo & Description */}
            <div className="md:col-span-2">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center">
                  <svg
                    className="w-5 h-5 text-white"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                    />
                  </svg>
                </div>
                <span className="text-lg font-semibold">
                  AI Campus Companion
                </span>
              </div>
              <p className="text-sm text-zinc-500 max-w-sm">
                Explore campus life through interactive stories, connect with students, and build meaningful relationships.
              </p>
            </div>

            {/* Product */}
            <div>
              <h4 className="font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-sm text-zinc-400">
                <li>
                  <Link
                    to="/app"
                    className="hover:text-white transition-colors"
                  >
                    Features
                  </Link>
                </li>
                <li>
                  <Link
                    to="/app"
                    className="hover:text-white transition-colors"
                  >
                    How It Works
                  </Link>
                </li>
                <li>
                  <Link
                    to="/app"
                    className="hover:text-white transition-colors"
                  >
                    Get Started
                  </Link>
                </li>
              </ul>
            </div>

            {/* Community */}
            <div>
              <h4 className="font-semibold mb-4">Community</h4>
              <ul className="space-y-2 text-sm text-zinc-400">
                <li>
                  <Link
                    to="/app/study-buddy/matches"
                    className="hover:text-white transition-colors"
                  >
                    Find University Mates
                  </Link>
                </li>
                <li>
                  <Link
                    to="/app/qa"
                    className="hover:text-white transition-colors"
                  >
                    Peer Q&A
                  </Link>
                </li>
                <li>
                  <Link
                    to="/app"
                    className="hover:text-white transition-colors"
                  >
                    Direct Chat
                  </Link>
                </li>
                <li>
                  <Link
                    to="/app"
                    className="hover:text-white transition-colors"
                  >
                    Campus Stories
                  </Link>
                </li>
              </ul>
            </div>
          </div>

          {/* Bottom */}
          <div className="pt-8 border-t border-zinc-900 flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-sm text-zinc-600">
              © 2026 AI Campus Companion. All rights reserved.
            </p>
            <div className="flex flex-wrap gap-6 text-sm text-zinc-600 justify-center">
              <Link
                to="/app/support/terms"
                className="hover:text-zinc-400 transition-colors"
              >
                Terms
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
