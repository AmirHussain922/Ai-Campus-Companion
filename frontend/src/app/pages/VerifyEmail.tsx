import { useState, useEffect } from "react";
import { motion } from "motion/react";
import { useNavigate, useSearchParams } from "react-router";
import { useStore } from "../store";

export default function VerifyEmail() {
  const authVerifyOtp = useStore(state => state.authVerifyOtp);
  const authResendOtp = useStore(state => state.authResendOtp);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const email = searchParams.get('email') ?? '';
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [countdown, setCountdown] = useState(60);

  // Redirect to signup if no email
  useEffect(() => {
    if (!email) navigate('/signup');
  }, [email, navigate]);

  // Countdown timer for resend button
  useEffect(() => {
    if (countdown <= 0) return;
    const timer = setTimeout(() => setCountdown(c => c - 1), 1000);
    return () => clearTimeout(timer);
  }, [countdown]);

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const result = await authVerifyOtp(email, otp);
    setLoading(false);

    if (result.success) {
      setSuccess('Email verified! Redirecting to login...');
      setTimeout(() => navigate('/login'), 2000);
    } else {
      setError(result.message);
    }
  };

  const handleResend = async () => {
    setError('');
    setResending(true);

    const result = await authResendOtp(email);
    setResending(false);

    if (result.success) {
      setSuccess('New code sent to your email.');
      setCountdown(60);
    } else {
      setError(result.message);
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="bg-zinc-900/40 p-10 rounded-3xl border border-zinc-800/50 backdrop-blur-xl shadow-2xl"
    >
      <div className="mb-10 text-center">
        <h2 className="text-3xl font-light tracking-tight mb-2">Verify Email</h2>
        <p className="text-zinc-400 text-sm">
          We sent a 6-digit code to<br />
          <span className="text-white font-medium">{email}</span>
        </p>
      </div>

      {error && (
        <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm text-center">
          {error}
        </div>
      )}

      {success && (
        <div className="mb-4 p-3 rounded-xl bg-green-500/10 border border-green-500/30 text-green-400 text-sm text-center">
          {success}
        </div>
      )}

      <form onSubmit={handleVerify} className="space-y-6">
        <div className="space-y-1 relative group">
          <label className="text-xs font-medium text-zinc-500 uppercase tracking-wider ml-1">Verification Code</label>
          <input 
            type="text" 
            required
            maxLength={6}
            value={otp}
            onChange={e => setOtp(e.target.value.replace(/\D/g, ''))}
            className="w-full bg-zinc-950/50 border border-zinc-800 rounded-xl px-4 py-3 text-white text-center text-2xl tracking-[0.5em] placeholder-zinc-600 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 transition-all shadow-inner group-focus-within:bg-zinc-900/80" 
            placeholder="000000"
            autoFocus
          />
        </div>

        <button 
          type="submit" 
          disabled={loading || otp.length < 6}
          className="w-full bg-white text-zinc-950 font-medium rounded-xl py-3 hover:bg-zinc-200 transition-colors mt-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Verifying...' : 'Verify Email'}
        </button>
      </form>

      <div className="mt-8 text-center">
        {countdown > 0 ? (
          <p className="text-sm text-zinc-500">
            Resend code in <span className="text-white">{countdown}s</span>
          </p>
        ) : (
          <button
            onClick={handleResend}
            disabled={resending}
            className="text-sm text-purple-400 hover:text-purple-300 disabled:opacity-50 transition-colors"
          >
            {resending ? 'Sending...' : 'Resend verification code'}
          </button>
        )}
      </div>

      <p className="mt-6 text-center text-sm text-zinc-500">
        Wrong email? <button onClick={() => navigate('/signup')} className="text-white hover:underline">Go back</button>
      </p>
    </motion.div>
  );
}
