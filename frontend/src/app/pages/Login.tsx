import { useState } from "react";
import { motion } from "motion/react";
import { Link, useNavigate } from "react-router";
import { useStore } from "../store";

export default function Login() {
  const authLogin = useStore(state => state.authLogin);
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  // Prevent double submission
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();

    // Prevent if already loading or already submitted
    if (loading || !email || !password) {
      console.warn('Login prevented: form incomplete or already submitting');
      return;
    }

    setError('');
    setLoading(true);

    console.log('Login started for:', email);

    try {
      const result = await authLogin(email, password);

      console.log('Login result:', result);

      if (result.success) {
        console.log('Login successful, navigating to /select');
        // Use a slight delay to ensure the state is fully updated
        setTimeout(() => {
          navigate('/select');
        }, 100);
      } else {
        console.error('Login failed:', result.message);
        setError(result.message);
      }
    } catch (err) {
      console.error('Login error:', err);
      setError('An unexpected error occurred during login');
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="bg-zinc-900/40 p-10 rounded-3xl border border-zinc-800/50 backdrop-blur-xl shadow-2xl"
    >
      <button
        onClick={() => navigate('/')}
        className="mb-6 flex items-center gap-2 text-zinc-400 hover:text-white transition-colors"
      >
        <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M19 12H5M12 19l-7-7 7-7" />
        </svg>
        Back to Home
      </button>
      
      <div className="mb-10 text-center">
        <h2 className="text-3xl font-light tracking-tight mb-2">Welcome Back</h2>
        <p className="text-zinc-400 text-sm">Sign in to continue your journey</p>
      </div>

      {error && (
        <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm text-center">
          {error}
        </div>
      )}

      <form onSubmit={handleLogin} className="space-y-6">
        <div className="space-y-1 relative group">
          <label className="text-xs font-medium text-zinc-500 uppercase tracking-wider ml-1">Email</label>
          <input 
            type="email" 
            required
            value={email}
            onChange={e => setEmail(e.target.value)}
            className="w-full bg-zinc-950/50 border border-zinc-800 rounded-xl px-4 py-3 text-white placeholder-zinc-600 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 transition-all shadow-inner group-focus-within:bg-zinc-900/80" 
            placeholder="student@university.edu"
          />
        </div>
        
        <div className="space-y-1 relative group">
          <label className="text-xs font-medium text-zinc-500 uppercase tracking-wider ml-1">Password</label>
          <div className="relative">
            <input 
              type={showPassword ? "text" : "password"} 
              required
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="w-full bg-zinc-950/50 border border-zinc-800 rounded-xl px-4 py-3 pr-12 text-white placeholder-zinc-600 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 transition-all shadow-inner group-focus-within:bg-zinc-900/80" 
              placeholder="••••••••"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-white transition-colors"
            >
              {showPassword ? (
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                  <line x1="1" y1="1" x2="23" y2="23" />
                </svg>
              ) : (
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                  <circle cx="12" cy="12" r="3" />
                </svg>
              )}
            </button>
          </div>
        </div>

        <div className="flex justify-end">
          <Link to="/forgot-password" className="text-xs text-zinc-400 hover:text-white transition-colors">
            Forgot Password?
          </Link>
        </div>

        <button
          type="submit"
          disabled={loading || !email || !password}
          className="w-full bg-white text-zinc-950 font-medium rounded-xl py-3 hover:bg-zinc-200 transition-colors mt-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-zinc-700 disabled:text-zinc-500 disabled:shadow-none"
        >
          {loading ? 'Signing In...' : 'Sign In'}
        </button>
      </form>

      <div className="mt-8 flex items-center justify-center gap-2">
        <div className="h-px bg-zinc-800 flex-1" />
        <span className="text-xs text-zinc-600 font-medium px-2">OR</span>
        <div className="h-px bg-zinc-800 flex-1" />
      </div>

      <button 
        disabled
        className="w-full mt-6 bg-zinc-800/50 text-zinc-500 font-medium rounded-xl py-3 cursor-not-allowed flex items-center justify-center gap-3 relative group"
        title="Coming Soon"
      >
        <svg viewBox="0 0 24 24" className="w-5 h-5" fill="currentColor">
          <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
          <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
          <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
          <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
        </svg>
        Continue with Google
        <span className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-zinc-900 text-zinc-300 text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
          Coming Soon
        </span>
      </button>

      <p className="mt-8 text-center text-sm text-zinc-500">
        Don't have an account? <Link to="/signup" className="text-white hover:underline">Sign up</Link>
      </p>
    </motion.div>
  );
}
