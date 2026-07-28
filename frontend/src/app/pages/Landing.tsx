import { motion } from "motion/react";
import { Link } from "react-router";
import { INITIAL_COMPANIONS } from "../store";

export default function Landing() {
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-50 overflow-x-hidden selection:bg-purple-500/30">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 px-8 py-6 flex justify-between items-center bg-zinc-950/50 backdrop-blur-md border-b border-zinc-800/50">
        <div className="text-xl font-bold tracking-tighter text-white">
          AI Campus<span className="text-purple-500">.</span>
        </div>
        <div className="flex gap-4">
          <Link to="/login" className="px-5 py-2.5 text-sm font-medium text-zinc-300 hover:text-white transition-colors">
            Log In
          </Link>
          <Link to="/signup" className="px-5 py-2.5 text-sm font-medium bg-white text-zinc-950 rounded-full hover:bg-zinc-200 transition-colors">
            Get Started
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative min-h-screen flex flex-col justify-center items-center pt-20 px-8">
        {/* Cinematic Background Elements */}
        <div className="absolute inset-0 z-0 overflow-hidden">
          <div className="absolute top-[20%] left-[30%] w-[600px] h-[600px] bg-purple-600/10 rounded-full blur-[120px] mix-blend-screen" />
          <div className="absolute bottom-[20%] right-[30%] w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[100px] mix-blend-screen" />
          <div className="absolute top-0 w-full h-full bg-[linear-gradient(rgba(24,24,27,0)_0%,rgba(24,24,27,1)_100%)] z-10" />
        </div>

        <div className="relative z-20 text-center max-w-4xl mx-auto flex flex-col items-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
            className="inline-block mb-6 px-4 py-1.5 rounded-full border border-zinc-800 bg-zinc-900/50 backdrop-blur-sm text-xs font-semibold tracking-wider text-zinc-400 uppercase"
          >
            The Future of Connection
          </motion.div>
          
          <motion.h1 
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
            className="text-6xl md:text-8xl font-light tracking-tighter leading-tight text-transparent bg-clip-text bg-gradient-to-b from-white to-white/60 mb-8"
          >
            Your AI <br/>
            <span className="italic font-serif">Campus Companions</span>
          </motion.h1>
          
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="text-lg md:text-xl text-zinc-400 max-w-2xl font-light mb-12 leading-relaxed"
          >
            Experience a revolutionary platform where AI companions behave like real university students. 
            Level up relationships, unlock interactive stories, and discover unique personalities.
          </motion.p>
          
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.4, ease: [0.16, 1, 0.3, 1] }}
          >
            <Link 
              to="/signup" 
              className="group relative inline-flex items-center justify-center px-8 py-4 font-medium text-white bg-zinc-800 rounded-full overflow-hidden transition-all hover:bg-zinc-700"
            >
              <span className="relative z-10">Start Your Companion Journey</span>
              <div className="absolute inset-0 h-full w-full bg-gradient-to-r from-purple-500/20 to-blue-500/20 opacity-0 group-hover:opacity-100 transition-opacity" />
            </Link>
          </motion.div>
        </div>

        {/* Silhouettes/Avatars Preview */}
        <motion.div 
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1.5, delay: 0.6, ease: "easeOut" }}
          className="relative z-20 mt-24 flex justify-center -space-x-4"
        >
          {INITIAL_COMPANIONS.map((comp, idx) => (
            <div 
              key={comp.id} 
              className="w-20 h-20 md:w-24 md:h-24 rounded-full border-4 border-zinc-950 overflow-hidden relative"
              style={{ zIndex: INITIAL_COMPANIONS.length - idx }}
            >
              <img src={comp.avatarUrl} alt={comp.name} className="w-full h-full object-cover" />
              <div className="absolute inset-0 bg-zinc-900/20 mix-blend-overlay" />
            </div>
          ))}
        </motion.div>
      </section>

      {/* Features Section */}
      <section className="py-32 px-8 bg-zinc-950 relative z-20">
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-12">
          {[
            { title: "Deep Personalities", desc: "Interact with diverse character archetypes—from the Night-Owl Philosopher to the Clueless Freshman." },
            { title: "Level Up Relationships", desc: "Gain XP through meaningful conversations. Unlock new interactions and deeper trust as you progress." },
            { title: "Unlock Story Episodes", desc: "Experience episodic narrative milestones. Your choices shape the dynamic journey of college life." }
          ].map((feature, idx) => (
            <motion.div 
              key={idx}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, delay: idx * 0.2 }}
              className="p-8 rounded-3xl bg-zinc-900/30 border border-zinc-800/50 hover:bg-zinc-900/50 transition-colors"
            >
              <h3 className="text-xl font-medium mb-4">{feature.title}</h3>
              <p className="text-zinc-400 font-light leading-relaxed">{feature.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Subscription Plans Section */}
      <section className="py-24 px-8 bg-zinc-900/20 border-y border-zinc-800/50 relative z-20">
        <div className="max-w-5xl mx-auto text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-light tracking-tighter mb-4">Simple, Transparent Pricing</h2>
          <p className="text-zinc-400">Choose the plan that fits your campus journey.</p>
        </div>
        
        <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Free Plan */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="p-8 rounded-3xl bg-zinc-900/50 border border-zinc-800 flex flex-col"
          >
            <h3 className="text-2xl font-medium mb-2">Free Pass</h3>
            <div className="text-4xl font-light mb-6">Rs 0<span className="text-lg text-zinc-500">/mo</span></div>
            <ul className="space-y-4 mb-8 flex-1 text-zinc-300">
              <li className="flex items-center gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-zinc-500" />
                Access to all base companions
              </li>
              <li className="flex items-center gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-zinc-500" />
                Basic chat capabilities
              </li>
              <li className="flex items-center gap-3 text-zinc-500">
                <div className="w-1.5 h-1.5 rounded-full bg-zinc-700" />
                Limited to Level 1 progression
              </li>
              <li className="flex items-center gap-3 text-zinc-500">
                <div className="w-1.5 h-1.5 rounded-full bg-zinc-700" />
                No story episode unlocks
              </li>
            </ul>
            <Link to="/signup" className="w-full py-3 rounded-xl bg-zinc-800 text-white font-medium hover:bg-zinc-700 transition-colors text-center">
              Start Free
            </Link>
          </motion.div>

          {/* Pro Plan */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="p-8 rounded-3xl bg-gradient-to-b from-purple-900/20 to-zinc-900/50 border border-purple-500/30 flex flex-col relative overflow-hidden"
          >
            <div className="absolute top-0 right-0 px-4 py-1 bg-purple-500/20 text-purple-300 text-xs font-semibold tracking-wider rounded-bl-xl border-l border-b border-purple-500/30">
              POPULAR
            </div>
            <h3 className="text-2xl font-medium mb-2 text-purple-100">Campus Pro</h3>
            <div className="text-4xl font-light mb-6 text-white">Rs 100<span className="text-lg text-zinc-500">/mo</span></div>
            <ul className="space-y-4 mb-8 flex-1 text-zinc-300">
              <li className="flex items-center gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                Unlimited XP progression
              </li>
              <li className="flex items-center gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                Unlock all story episodes & memories
              </li>
              <li className="flex items-center gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                Customizable companion names & avatars
              </li>
              <li className="flex items-center gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                Priority AI response generation
              </li>
            </ul>
            <Link to="/upgrade" className="w-full py-3 rounded-xl bg-purple-600 text-white font-medium hover:bg-purple-500 transition-colors text-center shadow-[0_0_20px_rgba(168,85,247,0.3)]">
              Upgrade to Pro
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Support & Details Section */}
      <section className="py-24 px-8 bg-zinc-950 relative z-20">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-light mb-6">Need Assistance?</h2>
          <p className="text-zinc-400 mb-8 max-w-2xl mx-auto leading-relaxed">
            Whether you're experiencing technical issues, have questions about the subscription plans, or just want to share feedback about your campus journey, our support team is here to help.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
            <div className="flex flex-col items-center p-6 bg-zinc-900/50 rounded-2xl border border-zinc-800 w-full sm:w-64">
              <span className="text-zinc-500 text-sm font-medium tracking-wider uppercase mb-2">Email Support</span>
              <a href="mailto:support@aicampus.example.com" className="text-purple-400 hover:text-purple-300 font-medium">
                support@aicampus.com
              </a>
            </div>
            <div className="flex flex-col items-center p-6 bg-zinc-900/50 rounded-2xl border border-zinc-800 w-full sm:w-64">
              <span className="text-zinc-500 text-sm font-medium tracking-wider uppercase mb-2">Help Center</span>
              <Link to="/support/help" className="text-zinc-200 hover:text-white font-medium transition-colors">
                Browse FAQs
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t border-zinc-900 text-center text-zinc-600 text-sm font-light relative z-20">
        <p>© 2026 AI Campus Companions. A revolutionary startup experience.</p>
        <div className="flex justify-center gap-6 mt-4">
          <Link to="/support/terms" className="hover:text-zinc-400 transition-colors">Terms of Service</Link>
          <Link to="/support/privacy" className="hover:text-zinc-400 transition-colors">Privacy Policy</Link>
        </div>
      </footer>
    </div>
  );
}
