import { Link } from "react-router";
import { motion } from "motion/react";
import { ChevronLeft, HelpCircle, Search, ChevronDown } from "lucide-react";
import { useState } from "react";
import { cn } from "../utils";

const FAQS = [
  {
    q: "How do I level up my companion?",
    a: "You gain XP by sending messages and interacting with your companion. Once you reach the XP threshold, you will automatically level up and potentially unlock new memory episodes."
  },
  {
    q: "Can I reset my progress?",
    a: "Currently, progress resets are not supported on a per-companion basis. Deleting your account will clear all progress permanently."
  },
  {
    q: "How do I change my companion's avatar?",
    a: "Navigate to the companion's profile page and hover over their circular avatar. A 'Change Photo' prompt will appear, allowing you to upload your own custom image."
  },
  {
    q: "Is my chat data private?",
    a: "Yes. We use industry-standard encryption, and your chat data is securely stored in your personal account."
  }
];

export default function SupportHelpCenter() {
  const [openFaq, setOpenFaq] = useState<number | null>(0);

  return (
    <div className="flex-1 overflow-y-auto bg-zinc-950 p-4 sm:p-6 md:p-8 text-zinc-50 relative h-full">
      <div className="max-w-3xl mx-auto space-y-8">
        
        <header className="flex items-center gap-4 border-b border-zinc-800/50 pb-6">
          <Link to="/app/me" className="p-2 bg-zinc-900 hover:bg-zinc-800 rounded-full transition-colors">
            <ChevronLeft className="w-5 h-5 text-zinc-400" />
          </Link>
          <div>
            <h1 className="text-2xl font-light tracking-tight">Help Center</h1>
            <p className="text-sm text-zinc-400">Find answers and get support</p>
          </div>
        </header>

        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-8"
        >
          {/* Search */}
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <Search className="w-5 h-5 text-zinc-500" />
            </div>
            <input 
              type="text" 
              className="w-full pl-12 pr-4 py-4 bg-zinc-900/50 border border-zinc-800 rounded-2xl focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none transition-all text-zinc-200"
              placeholder="Search for articles, guides, or FAQs..."
            />
          </div>

          {/* FAQs */}
          <div>
            <h2 className="text-lg font-medium mb-4 flex items-center gap-2">
              <HelpCircle className="w-5 h-5 text-zinc-400" />
              Frequently Asked Questions
            </h2>
            <div className="space-y-3">
              {FAQS.map((faq, i) => (
                <div key={i} className="bg-zinc-900/30 border border-zinc-800 rounded-2xl overflow-hidden transition-colors hover:border-zinc-700">
                  <button 
                    onClick={() => setOpenFaq(openFaq === i ? null : i)}
                    className="w-full flex items-center justify-between p-5 text-left"
                  >
                    <span className="font-medium text-zinc-200">{faq.q}</span>
                    <ChevronDown className={cn("w-5 h-5 text-zinc-500 transition-transform", openFaq === i ? "rotate-180" : "")} />
                  </button>
                  {openFaq === i && (
                    <div className="px-5 pb-5 pt-1 text-sm text-zinc-400 leading-relaxed border-t border-zinc-800/50 mt-1">
                      {faq.a}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
          
          <div className="bg-zinc-900/50 border border-zinc-800 rounded-3xl p-8 text-center mt-12">
            <h3 className="text-lg font-medium mb-2">Still need help?</h3>
            <p className="text-zinc-400 text-sm mb-6">Our support team is always ready to help you with any specific issues.</p>
            <Link 
              to="/app/support/contact"
              className="inline-flex px-6 py-3 bg-white text-zinc-950 font-medium rounded-xl hover:bg-zinc-200 transition-colors"
            >
              Contact Support
            </Link>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
