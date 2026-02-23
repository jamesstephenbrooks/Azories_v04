import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { FiMail, FiLock, FiUser, FiArrowLeft, FiSend } from 'react-icons/fi';
import { Link } from 'react-router-dom';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

export default function Auth() {
  const [isLogin, setIsLogin] = useState(true);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [forgotEmail, setForgotEmail] = useState('');
  const [forgotSent, setForgotSent] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: ''
  });
  
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from || '/library';

  const handleForgotPassword = async (e) => {
    e.preventDefault();
    if (!forgotEmail.trim()) {
      toast.error('Please enter your email');
      return;
    }
    
    setLoading(true);
    try {
      await axios.post(`${API}/api/auth/forgot-password`, { email: forgotEmail });
      setForgotSent(true);
      toast.success('Reset link sent! Check your email.');
    } catch (error) {
      toast.error('Failed to send reset email. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      if (isLogin) {
        await login(formData.email, formData.password);
        toast.success('Welcome back!');
      } else {
        if (!formData.name.trim()) {
          toast.error('Please enter your name');
          setLoading(false);
          return;
        }
        await register(formData.email, formData.password, formData.name);
        toast.success('Account created successfully!');
      }
      // Small delay to ensure state is updated before navigation
      setTimeout(() => {
        navigate(from, { replace: true });
      }, 100);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4 py-12">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-secondary/5 rounded-full blur-3xl" />
      </div>
      
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md relative z-10"
      >
        {/* Back to home */}
        <Link 
          to="/" 
          className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground mb-8 transition-colors"
          data-testid="back-home-link"
        >
          <FiArrowLeft />
          <span className="font-ui">Back to Home</span>
        </Link>
        
        <Card className="border-border/50 shadow-xl">
          <CardHeader className="text-center pb-2">
            <Link to="/">
              <span className="font-heading text-3xl font-bold logo-text">Azories</span>
            </Link>
            <CardTitle className="font-heading text-2xl mt-4">
              {showForgotPassword 
                ? 'Reset Password' 
                : (isLogin ? 'Welcome Back' : 'Create Account')}
            </CardTitle>
            <CardDescription className="font-body">
              {showForgotPassword 
                ? "Enter your email and we'll send you a reset link"
                : (isLogin 
                  ? 'Sign in to continue your storytelling journey' 
                  : 'Start creating magical stories today')}
            </CardDescription>
          </CardHeader>
          
          <CardContent className="pt-6">
            {/* Forgot Password Form */}
            {showForgotPassword ? (
              forgotSent ? (
                <div className="text-center py-8">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <FiMail className="w-8 h-8 text-green-600" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">Check Your Email</h3>
                  <p className="text-muted-foreground mb-4">
                    We've sent a password reset link to <strong>{forgotEmail}</strong>
                  </p>
                  <p className="text-sm text-muted-foreground mb-6">
                    The link will expire in 1 hour. If you don't see the email, check your spam folder.
                  </p>
                  <Button 
                    variant="outline"
                    onClick={() => {
                      setShowForgotPassword(false);
                      setForgotSent(false);
                      setForgotEmail('');
                    }}
                    className="rounded-full"
                  >
                    Back to Sign In
                  </Button>
                </div>
              ) : (
                <form onSubmit={handleForgotPassword} className="space-y-5">
                  <div className="space-y-2">
                    <Label htmlFor="forgot-email" className="font-ui">Email Address</Label>
                    <div className="relative">
                      <FiMail className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                      <Input
                        id="forgot-email"
                        type="email"
                        placeholder="you@example.com"
                        value={forgotEmail}
                        onChange={(e) => setForgotEmail(e.target.value)}
                        className="pl-10 rounded-full border-2 h-12"
                        required
                        data-testid="forgot-email-input"
                      />
                    </div>
                  </div>
                  
                  <Button 
                    type="submit" 
                    className="w-full rounded-full h-12 font-ui text-lg"
                    disabled={loading}
                    data-testid="forgot-submit-btn"
                  >
                    {loading ? 'Sending...' : (
                      <>
                        <FiSend className="mr-2" />
                        Send Reset Link
                      </>
                    )}
                  </Button>
                  
                  <div className="text-center">
                    <button
                      type="button"
                      onClick={() => setShowForgotPassword(false)}
                      className="font-body text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                      Back to Sign In
                    </button>
                  </div>
                </form>
              )
            ) : (
              /* Regular Login/Register Form */
              <>
            <form onSubmit={handleSubmit} className="space-y-5">
              {!isLogin && (
                <div className="space-y-2">
                  <Label htmlFor="name" className="font-ui">Name</Label>
                  <div className="relative">
                    <FiUser className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      id="name"
                      type="text"
                      placeholder="Your name"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="pl-10 rounded-full border-2 h-12"
                      data-testid="auth-name-input"
                    />
                  </div>
                </div>
              )}
              
              <div className="space-y-2">
                <Label htmlFor="email" className="font-ui">Email</Label>
                <div className="relative">
                  <FiMail className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="you@example.com"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="pl-10 rounded-full border-2 h-12"
                    required
                    data-testid="auth-email-input"
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="password" className="font-ui">Password</Label>
                <div className="relative">
                  <FiLock className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="password"
                    type="password"
                    placeholder="••••••••"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="pl-10 rounded-full border-2 h-12"
                    required
                    minLength={6}
                    data-testid="auth-password-input"
                  />
                </div>
              </div>
              
              <Button 
                type="submit" 
                className="w-full rounded-full h-12 font-ui text-lg"
                disabled={loading}
                data-testid="auth-submit-btn"
              >
                {loading ? 'Please wait...' : (isLogin ? 'Sign In' : 'Create Account')}
              </Button>
              
              {isLogin && (
                <div className="text-center">
                  <button
                    type="button"
                    onClick={() => setShowForgotPassword(true)}
                    className="font-body text-sm text-primary hover:underline transition-colors"
                    data-testid="forgot-password-link"
                  >
                    Forgot your password?
                  </button>
                </div>
              )}
            </form>
            
            <div className="mt-6 text-center">
              <button
                type="button"
                onClick={() => setIsLogin(!isLogin)}
                className="font-body text-sm text-muted-foreground hover:text-foreground transition-colors"
                data-testid="auth-toggle-mode"
              >
                {isLogin 
                  ? "Don't have an account? Sign up" 
                  : 'Already have an account? Sign in'}
              </button>
            </div>
              </>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
