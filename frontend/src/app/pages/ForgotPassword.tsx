import { useState } from "react";
import { motion } from "motion/react";
import { Link, useNavigate } from "react-router";

const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";

type Step = "email" | "otp" | "success";

export default function ForgotPassword() {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>("email");
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const handleSendOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      console.log("Sending forgot password request to:", `${API_BASE_URL}/auth/forgot-password`);
      console.log("Email:", email);
      
      const resp = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      console.log("Response status:", resp.status);
      const data = await resp.json();
      console.log("Response data:", data);

      if (resp.ok && data.success) {
        setSuccessMessage(data.message);
        setStep("otp");
      } else {
        // Handle both cases: detail is an object with message, or detail is a string
        let errorMsg = "Failed to send reset code";
        if (data.detail) {
          if (typeof data.detail === "string") {
            errorMsg = data.detail;
          } else if (data.detail.message) {
            errorMsg = data.detail.message;
          }
        } else if (data.message) {
          errorMsg = data.message;
        }
        console.error("Error message:", errorMsg);
        setError(errorMsg);
      }
    } catch (err: any) {
      console.error("Network error:", err);
      setError("Network error. Please check your connection.");
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // Validate passwords match
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    // Validate password strength
    if (newPassword.length < 8) {
      setError("Password must be at least 8 characters long");
      return;
    }
    if (!/[A-Z]/.test(newPassword)) {
      setError("Password must contain at least one uppercase letter");
      return;
    }
    if (!/[a-z]/.test(newPassword)) {
      setError("Password must contain at least one lowercase letter");
      return;
    }
    if (!/[0-9]/.test(newPassword)) {
      setError("Password must contain at least one number");
      return;
    }
    if (!/[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(newPassword)) {
      setError("Password must contain at least one special character");
      return;
    }

    setLoading(true);

    try {
      const resp = await fetch(`${API_BASE_URL}/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          otp,
          new_password: newPassword,
        }),
      });

      const data = await resp.json();

      if (resp.ok && data.success) {
        setSuccessMessage(data.message);
        setStep("success");
      } else {
        setError(data.detail?.message || data.message || "Failed to reset password");
      }
    } catch (err: any) {
      setError("Network error. Please check your connection.");
    } finally {
      setLoading(false);
    }
  };

  const handleResendOTP = async () => {
    setError("");
    setLoading(true);

    try {
      const resp = await fetch(`${API_BASE_URL}/auth/resend-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          purpose: "password_reset",
        }),
      });

      const data = await resp.json();

      if (resp.ok && data.success) {
        setSuccessMessage("New code sent! Please check your email.");
      } else {
        setError(data.detail?.message || data.message || "Failed to resend code");
      }
    } catch (err: any) {
      setError("Network error. Please check your connection.");
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
      <div className="mb-10 text-center">
        <h2 className="text-3xl font-light tracking-tight mb-2">
          {step === "email" && "Reset Password"}
          {step === "otp" && "Enter Verification Code"}
          {step === "success" && "Password Reset Successful"}
        </h2>
        <p className="text-zinc-400 text-sm">
          {step === "email" && "We'll send a verification code to your email"}
          {step === "otp" && "Check your email for the 6-digit code"}
          {step === "success" && "You can now log in with your new password"}
        </p>
      </div>

      {error && (
        <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm text-center">
          {error}
        </div>
      )}

      {successMessage && (
        <div className="mb-4 p-3 rounded-xl bg-green-500/10 border border-green-500/30 text-green-400 text-sm text-center">
          {successMessage}
        </div>
      )}

      {step === "email" && (
        <form onSubmit={handleSendOTP} className="space-y-6">
          <div className="space-y-1 relative group">
            <label className="text-xs font-medium text-zinc-500 uppercase tracking-wider ml-1">
              Email Address
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-zinc-950/50 border border-zinc-800 rounded-xl px-4 py-3 text-white placeholder-zinc-600 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 transition-all shadow-inner group-focus-within:bg-zinc-900/80"
              placeholder="student@university.edu"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-white text-zinc-950 font-medium rounded-xl py-3 hover:bg-zinc-200 transition-colors mt-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Sending Code..." : "Send Verification Code"}
          </button>
        </form>
      )}

      {step === "otp" && (
        <form onSubmit={handleResetPassword} className="space-y-6">
          <div className="space-y-1 relative group">
            <label className="text-xs font-medium text-zinc-500 uppercase tracking-wider ml-1">
              Verification Code
            </label>
            <input
              type="text"
              required
              maxLength={6}
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
              className="w-full bg-zinc-950/50 border border-zinc-800 rounded-xl px-4 py-3 text-white placeholder-zinc-600 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 transition-all shadow-inner group-focus-within:bg-zinc-900/80 text-center text-2xl tracking-widest"
              placeholder="000000"
            />
          </div>

          <div className="space-y-1 relative group">
            <label className="text-xs font-medium text-zinc-500 uppercase tracking-wider ml-1">
              New Password
            </label>
            <input
              type="password"
              required
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full bg-zinc-950/50 border border-zinc-800 rounded-xl px-4 py-3 text-white placeholder-zinc-600 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 transition-all shadow-inner group-focus-within:bg-zinc-900/80"
              placeholder="••••••••"
            />
          </div>

          <div className="space-y-1 relative group">
            <label className="text-xs font-medium text-zinc-500 uppercase tracking-wider ml-1">
              Confirm New Password
            </label>
            <input
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full bg-zinc-950/50 border border-zinc-800 rounded-xl px-4 py-3 text-white placeholder-zinc-600 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 transition-all shadow-inner group-focus-within:bg-zinc-900/80"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-white text-zinc-950 font-medium rounded-xl py-3 hover:bg-zinc-200 transition-colors mt-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Resetting..." : "Reset Password"}
          </button>

          <div className="text-center">
            <button
              type="button"
              onClick={handleResendOTP}
              disabled={loading}
              className="text-sm text-zinc-400 hover:text-white transition-colors disabled:opacity-50"
            >
              Didn't receive code? Resend
            </button>
          </div>
        </form>
      )}

      {step === "success" && (
        <div className="space-y-6">
          <div className="text-center">
            <div className="mx-auto w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mb-4">
              <svg
                className="w-8 h-8 text-green-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
            <p className="text-zinc-300 text-sm">
              Your password has been reset successfully.
            </p>
          </div>

          <button
            onClick={() => navigate("/login")}
            className="w-full bg-white text-zinc-950 font-medium rounded-xl py-3 hover:bg-zinc-200 transition-colors"
          >
            Go to Login
          </button>
        </div>
      )}

      <p className="mt-8 text-center text-sm text-zinc-500">
        Remember your password?{" "}
        <Link to="/login" className="text-white hover:underline">
          Sign in
        </Link>
      </p>
    </motion.div>
  );
}
