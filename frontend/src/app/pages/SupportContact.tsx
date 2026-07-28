import { Link } from "react-router";
import { motion } from "motion/react";
import { ChevronLeft, Mail, Send } from "lucide-react";
import { useState } from "react";

export default function SupportContact() {
  const [sent, setSent] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSent(true);
    setTimeout(() => setSent(false), 5000);
  };

  return (
    <div className="flex-1 overflow-y-auto bg-zinc-950 p-4 sm:p-6 md:p-8 text-zinc-50 relative h-full">
      <div className="max-w-2xl mx-auto space-y-8">
        
        <header className="flex items-center gap-4 border-b border-zinc-800/50 pb-6">
          <Link to="/app/me" className="p-2 bg-zinc-900 hover:bg-zinc-800 rounded-full transition-colors">
            <ChevronLeft className="w-5 h-5 text-zinc-400" />
          </Link>
          <div>
            <h1 className="text-2xl font-light tracking-tight">Contact Support</h1>
            <p className="text-sm text-zinc-400">Send us a message and we'll get back to you shortly</p>
          </div>
        </header>

        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-zinc-900/30 border border-zinc-800 rounded-3xl p-6 sm:p-8"
        >
          {sent ? (
            <motion.div 
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="py-12 flex flex-col items-center text-center space-y-4"
            >
              <div className="w-16 h-16 bg-emerald-500/10 rounded-full flex items-center justify-center mb-2">
                <Send className="w-8 h-8 text-emerald-400" />
              </div>
              <h2 className="text-xl font-medium text-white">Message Sent!</h2>
              <p className="text-zinc-400 max-w-sm">
                Thank you for reaching out. Our support team will review your message and reply via email within 24 hours.
              </p>
              <button 
                onClick={() => setSent(false)}
                className="mt-6 px-6 py-2.5 bg-zinc-800 hover:bg-zinc-700 text-white rounded-xl transition-colors font-medium"
              >
                Send Another Message
              </button>
            </motion.div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-2">Topic / Subject</label>
                <select className="w-full px-4 py-3 bg-zinc-950 border border-zinc-800 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none transition-all text-zinc-200 appearance-none">
                  <option>Account Issue</option>
                  <option>Billing & Subscriptions</option>
                  <option>Bug Report</option>
                  <option>Feature Request</option>
                  <option>Other</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-2">Message</label>
                <textarea 
                  required
                  className="w-full px-4 py-3 bg-zinc-950 border border-zinc-800 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none transition-all text-zinc-200 min-h-[200px] resize-none"
                  placeholder="Please describe your issue in detail..."
                ></textarea>
              </div>

              <div className="pt-4 flex justify-end">
                <button 
                  type="submit"
                  className="flex items-center gap-2 px-8 py-3 bg-white text-zinc-950 hover:bg-zinc-200 rounded-xl transition-colors font-medium"
                >
                  <Mail className="w-4 h-4" />
                  Send Message
                </button>
              </div>
            </form>
          )}
        </motion.div>
      </div>
    </div>
  );
}
