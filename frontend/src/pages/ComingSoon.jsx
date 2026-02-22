import { useState } from 'react';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { FiMail, FiBook, FiStar, FiHeart, FiArrowRight } from 'react-icons/fi';
import { toast } from 'sonner';

export default function ComingSoon() {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email) return;
    
    // Store email for waitlist (in production, send to backend)
    try {
      // For now, just show success
      setSubmitted(true);
      toast.success('You\'re on the list! We\'ll notify you when we launch.');
    } catch (error) {
      toast.error('Something went wrong. Please try again.');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0612] via-[#1a0a2e] to-[#0f0520] flex flex-col items-center justify-center p-6 overflow-hidden relative">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Floating orbs */}
        <motion.div
          animate={{ y: [0, -30, 0], x: [0, 20, 0] }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
          className="absolute top-1/4 left-1/4 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl"
        />
        <motion.div
          animate={{ y: [0, 40, 0], x: [0, -30, 0] }}
          transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
          className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-pink-500/10 rounded-full blur-3xl"
        />
        <motion.div
          animate={{ y: [0, -20, 0] }}
          transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
          className="absolute top-1/2 right-1/3 w-48 h-48 bg-amber-500/10 rounded-full blur-3xl"
        />
        
        {/* Stars */}
        {[...Array(50)].map((_, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0.2 }}
            animate={{ opacity: [0.2, 0.8, 0.2] }}
            transition={{ duration: 2 + Math.random() * 3, repeat: Infinity, delay: Math.random() * 2 }}
            className="absolute w-1 h-1 bg-white rounded-full"
            style={{
              top: `${Math.random() * 100}%`,
              left: `${Math.random() * 100}%`,
            }}
          />
        ))}
      </div>

      {/* Main content */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="relative z-10 max-w-2xl mx-auto text-center"
      >
        {/* Logo */}
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mb-8"
        >
          <h1 className="text-5xl md:text-7xl font-serif font-bold bg-gradient-to-r from-amber-200 via-purple-300 to-pink-300 bg-clip-text text-transparent">
            Azories
          </h1>
          <div className="flex items-center justify-center gap-2 mt-2">
            <FiBook className="w-5 h-5 text-purple-400" />
            <span className="text-purple-300 text-sm tracking-widest uppercase">Digital Storytelling</span>
            <FiStar className="w-5 h-5 text-amber-400" />
          </div>
        </motion.div>

        {/* Coming Soon Badge */}
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ duration: 0.5, delay: 0.4, type: "spring" }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-purple-500/30 mb-8"
        >
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-purple-500"></span>
          </span>
          <span className="text-purple-200 text-sm font-medium">Coming Soon</span>
        </motion.div>

        {/* Main heading */}
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="text-3xl md:text-4xl font-serif text-white mb-6"
        >
          Where Stories Come Alive
        </motion.h2>

        {/* Description */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.6 }}
          className="text-lg text-white/60 mb-8 max-w-lg mx-auto leading-relaxed"
        >
          Create magical illustrated books, explore our immersive 3D library, 
          and bring your stories to life with AI-powered tools. 
          Join the waitlist to be the first to experience the magic.
        </motion.p>

        {/* Features preview */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.7 }}
          className="grid grid-cols-3 gap-4 mb-10"
        >
          {[
            { icon: FiBook, label: '3D Library', color: 'purple' },
            { icon: FiStar, label: 'AI Art Studio', color: 'amber' },
            { icon: FiHeart, label: 'Audiobooks', color: 'pink' },
          ].map((feature, i) => (
            <div
              key={i}
              className={`p-4 rounded-2xl bg-${feature.color}-500/10 border border-${feature.color}-500/20`}
            >
              <feature.icon className={`w-6 h-6 mx-auto mb-2 text-${feature.color}-400`} />
              <span className="text-xs text-white/60">{feature.label}</span>
            </div>
          ))}
        </motion.div>

        {/* Email signup */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.8 }}
        >
          {!submitted ? (
            <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
              <div className="relative flex-1">
                <FiMail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
                <Input
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="pl-12 h-14 rounded-full bg-white/5 border-white/10 text-white placeholder:text-white/40 focus:border-purple-500"
                  required
                />
              </div>
              <Button
                type="submit"
                className="h-14 px-8 rounded-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white font-medium shadow-lg shadow-purple-500/25"
              >
                Join Waitlist
                <FiArrowRight className="ml-2 w-4 h-4" />
              </Button>
            </form>
          ) : (
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="p-6 rounded-2xl bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-purple-500/30"
            >
              <FiHeart className="w-10 h-10 text-pink-400 mx-auto mb-3" />
              <h3 className="text-xl font-medium text-white mb-2">You're on the list!</h3>
              <p className="text-white/60">We'll send you an email when Azories launches.</p>
            </motion.div>
          )}
        </motion.div>

        {/* Footer */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 1 }}
          className="mt-12 text-sm text-white/30"
        >
          © 2025 Azories. All rights reserved.
        </motion.p>
      </motion.div>
    </div>
  );
}
