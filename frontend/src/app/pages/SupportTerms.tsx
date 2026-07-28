import { Link } from "react-router";
import { motion } from "motion/react";
import { ChevronLeft, FileText } from "lucide-react";

export default function SupportTerms() {
  return (
    <div className="flex-1 overflow-y-auto bg-zinc-950 p-4 sm:p-6 md:p-8 text-zinc-50 relative h-full">
      <div className="max-w-3xl mx-auto space-y-8">
        
        <header className="flex items-center gap-4 border-b border-zinc-800/50 pb-6 sticky top-0 bg-zinc-950/90 backdrop-blur-xl z-10 pt-2">
          <Link to="/app/me" className="p-2 bg-zinc-900 hover:bg-zinc-800 rounded-full transition-colors">
            <ChevronLeft className="w-5 h-5 text-zinc-400" />
          </Link>
          <div>
            <h1 className="text-2xl font-light tracking-tight">Terms of Service</h1>
            <p className="text-sm text-zinc-400">Last updated: {new Date().toLocaleDateString()}</p>
          </div>
        </header>

        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-zinc-900/30 border border-zinc-800 rounded-3xl p-6 sm:p-10 space-y-8 prose prose-invert prose-zinc max-w-none"
        >
          <div>
            <h2 className="text-xl font-medium text-white mb-4 flex items-center gap-2">
              <FileText className="w-5 h-5 text-zinc-400" />
              1. Acceptance of Terms
            </h2>
            <p className="text-zinc-400 leading-relaxed">
              By accessing and using this application, you accept and agree to be bound by the terms and provision of this agreement. 
              In addition, when using these particular services, you shall be subject to any posted guidelines or rules applicable to such services.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-medium text-white mb-4">2. Description of Service</h2>
            <p className="text-zinc-400 leading-relaxed">
              We provide users with access to a rich collection of resources, including various communications tools, forums, and personalized content. 
              You understand and agree that the Service is provided "AS-IS" and that we assume no responsibility for the timeliness, deletion, mis-delivery, or failure to store any user communications or personalization settings.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-medium text-white mb-4">3. Privacy Policy</h2>
            <p className="text-zinc-400 leading-relaxed">
              Registration data and certain other information about you are subject to our Privacy Policy. For more information, see our full privacy policy. 
              You understand that through your use of the Service you consent to the collection and use of this information.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-medium text-white mb-4">4. User Conduct</h2>
            <p className="text-zinc-400 leading-relaxed">
              You understand that all information, data, text, software, music, sound, photographs, graphics, video, messages, tags, or other materials ("Content"), 
              whether publicly posted or privately transmitted, are the sole responsibility of the person from whom such Content originated.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-medium text-white mb-4">5. Modifications to Service</h2>
            <p className="text-zinc-400 leading-relaxed">
              We reserve the right at any time and from time to time to modify or discontinue, temporarily or permanently, the Service (or any part thereof) with or without notice. 
              You agree that we shall not be liable to you or to any third party for any modification, suspension or discontinuance of the Service.
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
