import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Link, useNavigate } from "react-router";
import { ChevronLeft, CreditCard, Lock, CheckCircle2, AlertCircle } from "lucide-react";
import { cn } from "../utils";

export default function Payment() {
  const navigate = useNavigate();
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  
  const [formData, setFormData] = useState({
    name: "",
    cardNumber: "",
    expiry: "",
    cvc: ""
  });
  
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    
    // Simple formatting for demonstration
    let formattedValue = value;
    if (name === 'cardNumber') {
      formattedValue = value.replace(/\D/g, '').substring(0, 16);
      formattedValue = formattedValue.replace(/(\d{4})/g, '$1 ').trim();
    } else if (name === 'expiry') {
      formattedValue = value.replace(/\D/g, '').substring(0, 4);
      if (formattedValue.length > 2) {
        formattedValue = `${formattedValue.substring(0, 2)}/${formattedValue.substring(2, 4)}`;
      }
    } else if (name === 'cvc') {
      formattedValue = value.replace(/\D/g, '').substring(0, 3);
    }
    
    setFormData(prev => ({ ...prev, [name]: formattedValue }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: "" }));
    }
  };

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!formData.name.trim()) newErrors.name = "Name is required";
    if (formData.cardNumber.replace(/\s/g, '').length < 16) newErrors.cardNumber = "Incomplete card number";
    if (formData.expiry.length < 5) newErrors.expiry = "Incomplete expiry";
    if (formData.cvc.length < 3) newErrors.cvc = "Incomplete CVC";
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    
    setIsProcessing(true);
    
    // Simulate payment processing
    setTimeout(() => {
      setIsProcessing(false);
      setIsSuccess(true);
      
      // Redirect after success
      setTimeout(() => {
        navigate('/app');
      }, 2500);
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-50 flex flex-col py-10 sm:py-16 px-4 sm:px-8 relative overflow-hidden">
      <div className="absolute top-0 w-full h-full bg-[radial-gradient(ellipse_at_top,rgba(168,85,247,0.1)_0%,rgba(24,24,27,1)_80%)] z-0 pointer-events-none" />
      
      <div className="relative z-10 max-w-4xl mx-auto w-full pt-4">
        <Link 
          to="/" 
          className="absolute top-0 left-0 p-2 sm:px-4 sm:py-2 flex items-center gap-2 text-zinc-400 hover:text-white transition-colors bg-zinc-900/50 rounded-full backdrop-blur-md border border-zinc-800 z-20"
        >
          <ChevronLeft className="w-5 h-5" />
          <span className="text-sm font-medium hidden sm:inline">Back</span>
        </Link>

        <div className="text-center mb-10 sm:mb-16 mt-12 sm:mt-0">
          <motion.h1 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-3xl sm:text-4xl md:text-5xl font-light tracking-tighter mb-4 text-transparent bg-clip-text bg-gradient-to-b from-white to-white/60"
          >
            Upgrade to Pro
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-zinc-400 max-w-lg mx-auto"
          >
            Unlock the full potential of your AI Campus experience.
          </motion.p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
          {/* Order Summary */}
          <motion.div 
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="lg:col-span-2 order-2 lg:order-1 space-y-6"
          >
            <div className="p-6 rounded-3xl bg-zinc-900/50 border border-zinc-800 backdrop-blur-sm">
              <h2 className="text-lg font-medium mb-6 flex items-center gap-2">
                Order Summary
              </h2>
              
              <div className="flex justify-between items-start pb-4 border-b border-zinc-800/80 mb-4">
                <div>
                  <h3 className="font-medium text-white mb-1">Campus Pro Plan</h3>
                  <p className="text-sm text-zinc-400">Monthly Subscription</p>
                </div>
                <div className="text-right">
                  <div className="font-medium">Rs 100</div>
                  <div className="text-xs text-zinc-500">/month</div>
                </div>
              </div>

              <div className="space-y-3 mb-6">
                <div className="flex items-center gap-2 text-sm text-zinc-300">
                  <CheckCircle2 className="w-4 h-4 text-purple-500" />
                  <span>Unlimited XP progression</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-zinc-300">
                  <CheckCircle2 className="w-4 h-4 text-purple-500" />
                  <span>Unlock all story episodes</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-zinc-300">
                  <CheckCircle2 className="w-4 h-4 text-purple-500" />
                  <span>Customizable companion names</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-zinc-300">
                  <CheckCircle2 className="w-4 h-4 text-purple-500" />
                  <span>Priority AI response generation</span>
                </div>
              </div>

              <div className="flex justify-between items-center pt-4 border-t border-zinc-800/80 mt-4">
                <span className="text-zinc-400">Total today</span>
                <span className="text-2xl font-light">Rs 100</span>
              </div>
            </div>

            <div className="flex items-start gap-3 p-4 rounded-2xl bg-zinc-900/30 border border-zinc-800/50 text-xs text-zinc-500">
              <Lock className="w-4 h-4 shrink-0 mt-0.5" />
              <p>
                Guaranteed safe and secure checkout. Your connection is encrypted and your payment details are not stored on our servers.
              </p>
            </div>
          </motion.div>

          {/* Payment Form */}
          <motion.div 
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="lg:col-span-3 order-1 lg:order-2"
          >
            <div className="p-6 sm:p-8 rounded-3xl bg-zinc-900/80 border border-zinc-800 backdrop-blur-md relative overflow-hidden">
              <AnimatePresence mode="wait">
                {isSuccess ? (
                  <motion.div 
                    key="success"
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="flex flex-col items-center justify-center text-center py-12 h-full min-h-[400px]"
                  >
                    <div className="w-20 h-20 rounded-full bg-purple-500/20 flex items-center justify-center mb-6">
                      <CheckCircle2 className="w-10 h-10 text-purple-400" />
                    </div>
                    <h2 className="text-3xl font-light mb-4">Payment Successful!</h2>
                    <p className="text-zinc-400 max-w-xs">
                      Welcome to Campus Pro. You now have access to all premium features. Redirecting you...
                    </p>
                  </motion.div>
                ) : (
                  <motion.form 
                    key="form"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    onSubmit={handleSubmit}
                    className="space-y-6"
                  >
                    <div>
                      <h2 className="text-xl font-medium mb-1">Payment Details</h2>
                      <p className="text-sm text-zinc-400 mb-6">Enter your card information to complete the purchase.</p>
                    </div>

                    <div className="space-y-4">
                      {/* Name on Card */}
                      <div>
                        <label className="block text-sm font-medium text-zinc-400 mb-1.5">Name on Card</label>
                        <input 
                          type="text" 
                          name="name"
                          value={formData.name}
                          onChange={handleInputChange}
                          className={cn(
                            "w-full px-4 py-3 bg-zinc-950/50 border rounded-xl text-white placeholder:text-zinc-600 focus:outline-none focus:ring-2 transition-colors",
                            errors.name ? "border-red-500/50 focus:ring-red-500/30 focus:border-red-500" : "border-zinc-800 focus:border-purple-500 focus:ring-purple-500/30"
                          )}
                          placeholder="John Doe"
                        />
                        {errors.name && <p className="text-red-400 text-xs mt-1.5 flex items-center gap-1"><AlertCircle className="w-3 h-3" />{errors.name}</p>}
                      </div>

                      {/* Card Number */}
                      <div>
                        <label className="block text-sm font-medium text-zinc-400 mb-1.5">Card Number</label>
                        <div className="relative">
                          <input 
                            type="text" 
                            name="cardNumber"
                            value={formData.cardNumber}
                            onChange={handleInputChange}
                            maxLength={19}
                            className={cn(
                              "w-full pl-11 pr-4 py-3 bg-zinc-950/50 border rounded-xl text-white placeholder:text-zinc-600 focus:outline-none focus:ring-2 transition-colors font-mono",
                              errors.cardNumber ? "border-red-500/50 focus:ring-red-500/30 focus:border-red-500" : "border-zinc-800 focus:border-purple-500 focus:ring-purple-500/30"
                            )}
                            placeholder="0000 0000 0000 0000"
                          />
                          <CreditCard className="w-5 h-5 text-zinc-500 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                        </div>
                        {errors.cardNumber && <p className="text-red-400 text-xs mt-1.5 flex items-center gap-1"><AlertCircle className="w-3 h-3" />{errors.cardNumber}</p>}
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        {/* Expiry */}
                        <div>
                          <label className="block text-sm font-medium text-zinc-400 mb-1.5">Expiry Date</label>
                          <input 
                            type="text" 
                            name="expiry"
                            value={formData.expiry}
                            onChange={handleInputChange}
                            maxLength={5}
                            className={cn(
                              "w-full px-4 py-3 bg-zinc-950/50 border rounded-xl text-white placeholder:text-zinc-600 focus:outline-none focus:ring-2 transition-colors font-mono",
                              errors.expiry ? "border-red-500/50 focus:ring-red-500/30 focus:border-red-500" : "border-zinc-800 focus:border-purple-500 focus:ring-purple-500/30"
                            )}
                            placeholder="MM/YY"
                          />
                          {errors.expiry && <p className="text-red-400 text-xs mt-1.5 flex items-center gap-1"><AlertCircle className="w-3 h-3" />{errors.expiry}</p>}
                        </div>

                        {/* CVC */}
                        <div>
                          <label className="block text-sm font-medium text-zinc-400 mb-1.5">CVC</label>
                          <input 
                            type="text" 
                            name="cvc"
                            value={formData.cvc}
                            onChange={handleInputChange}
                            maxLength={3}
                            className={cn(
                              "w-full px-4 py-3 bg-zinc-950/50 border rounded-xl text-white placeholder:text-zinc-600 focus:outline-none focus:ring-2 transition-colors font-mono",
                              errors.cvc ? "border-red-500/50 focus:ring-red-500/30 focus:border-red-500" : "border-zinc-800 focus:border-purple-500 focus:ring-purple-500/30"
                            )}
                            placeholder="123"
                          />
                          {errors.cvc && <p className="text-red-400 text-xs mt-1.5 flex items-center gap-1"><AlertCircle className="w-3 h-3" />{errors.cvc}</p>}
                        </div>
                      </div>
                    </div>

                    <button
                      type="submit"
                      disabled={isProcessing}
                      className="w-full py-4 mt-6 bg-purple-600 text-white rounded-xl font-medium hover:bg-purple-500 transition-all focus:outline-none focus:ring-2 focus:ring-purple-500/50 disabled:opacity-70 disabled:cursor-not-allowed flex justify-center items-center gap-2 shadow-[0_0_20px_rgba(168,85,247,0.3)] relative overflow-hidden group"
                    >
                      {isProcessing ? (
                        <>
                          <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                          <span>Processing...</span>
                        </>
                      ) : (
                        <>
                          <span className="relative z-10">Pay Rs 100</span>
                          <Lock className="w-4 h-4 relative z-10" />
                          <div className="absolute inset-0 h-full w-full bg-gradient-to-r from-purple-500/20 to-blue-500/20 opacity-0 group-hover:opacity-100 transition-opacity" />
                        </>
                      )}
                    </button>
                    
                    <p className="text-center text-xs text-zinc-500 mt-4">
                      By confirming this payment, you agree to our <Link to="/support/terms" className="text-zinc-400 hover:text-white underline underline-offset-2">Terms of Service</Link>.
                    </p>
                  </motion.form>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
