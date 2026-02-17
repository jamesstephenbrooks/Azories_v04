import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useTheme } from '@/context/ThemeContext';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { FiSun, FiMoon, FiBook, FiEdit3, FiHeadphones, FiArrowRight, FiStar, FiZap } from 'react-icons/fi';
import Navbar from '@/components/Navbar';

export default function Landing() {
  const { theme, toggleTheme } = useTheme();
  const { user } = useAuth();
  const navigate = useNavigate();

  const features = [
    {
      icon: <FiBook className="w-8 h-8" />,
      title: "3D Library",
      description: "Browse through a magical floating library of books"
    },
    {
      icon: <FiEdit3 className="w-8 h-8" />,
      title: "AI Creation",
      description: "Create stunning illustrations with AI-powered tools"
    },
    {
      icon: <FiHeadphones className="w-8 h-8" />,
      title: "Audio Books",
      description: "Listen to stories with multiple narrator voices"
    },
    {
      icon: <FiZap className="w-8 h-8" />,
      title: "Video Scenes",
      description: "Bring your stories to life with animated videos"
    }
  ];

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      {/* Hero Section */}
      <section className="hero-bg min-h-[90vh] relative overflow-hidden noise-overlay">
        <div className="max-w-7xl mx-auto px-6 md:px-12 pt-32 pb-20">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            {/* Left content */}
            <motion.div 
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8 }}
              className="space-y-8"
            >
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary font-ui text-sm">
                <FiStar className="w-4 h-4" />
                <span>Where Stories Come Alive</span>
              </div>
              
              <h1 className="font-heading text-5xl md:text-7xl font-bold tracking-tight leading-tight">
                <span className="logo-text">Azories</span>
                <br />
                <span className="text-foreground">Create Magic</span>
              </h1>
              
              <p className="font-body text-lg md:text-xl text-muted-foreground leading-relaxed max-w-lg">
                A digital storytelling platform where children become authors. 
                Create, illustrate, and share your own magical books with AI-powered tools.
              </p>
              
              <div className="flex flex-wrap gap-4 pt-4">
                <Button 
                  data-testid="explore-library-btn"
                  onClick={() => navigate('/library')}
                  className="rounded-full px-8 py-6 text-lg font-ui bg-primary hover:bg-primary/90 btn-magic"
                >
                  Explore Library
                  <FiArrowRight className="ml-2" />
                </Button>
                
                {user ? (
                  <Button 
                    data-testid="create-story-btn"
                    onClick={() => navigate('/dashboard')}
                    variant="outline"
                    className="rounded-full px-8 py-6 text-lg font-ui border-2"
                  >
                    Create Your Story
                  </Button>
                ) : (
                  <Button 
                    data-testid="get-started-btn"
                    onClick={() => navigate('/auth')}
                    variant="outline"
                    className="rounded-full px-8 py-6 text-lg font-ui border-2"
                  >
                    Get Started Free
                  </Button>
                )}
              </div>
            </motion.div>
            
            {/* Right - Floating Book Visual */}
            <motion.div 
              initial={{ opacity: 0, y: 50 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="relative hidden lg:block"
            >
              <div className="relative w-full h-[500px] book-perspective">
                {/* Main floating book */}
                <motion.div 
                  className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 animate-float"
                  whileHover={{ scale: 1.05 }}
                >
                  <div className="w-72 h-96 rounded-2xl overflow-hidden shadow-2xl magic-glow book-3d">
                    <img 
                      src="https://images.unsplash.com/photo-1690023835938-b078c130d58f?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2OTF8MHwxfHNlYXJjaHwyfHxtYWdpY2FsJTIwZmxvYXRpbmclMjBib29rcyUyMDNkJTIwYWVzdGhldGljfGVufDB8fHx8MTc3MTM1MTU0OHww&ixlib=rb-4.1.0&q=85"
                      alt="Magical Book"
                      className="w-full h-full object-cover"
                    />
                  </div>
                </motion.div>
                
                {/* Decorative floating elements */}
                <motion.div 
                  className="absolute top-10 right-20 w-16 h-20 rounded-lg bg-secondary/20 backdrop-blur animate-float-slow stagger-2"
                />
                <motion.div 
                  className="absolute bottom-20 left-10 w-12 h-16 rounded-lg bg-primary/20 backdrop-blur animate-float-slow stagger-4"
                />
                <motion.div 
                  className="absolute top-32 left-20 w-8 h-10 rounded bg-accent/30 backdrop-blur animate-float-slow stagger-3"
                />
              </div>
            </motion.div>
          </div>
        </div>
        
        {/* Gradient fade at bottom */}
        <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-background to-transparent" />
      </section>
      
      {/* Features Section */}
      <section className="py-20 md:py-32 px-6 md:px-12">
        <div className="max-w-7xl mx-auto">
          <motion.div 
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="font-heading text-4xl md:text-5xl font-bold text-foreground mb-4">
              Everything You Need to Create
            </h2>
            <p className="font-body text-lg text-muted-foreground max-w-2xl mx-auto">
              Powerful AI tools make it easy to write, illustrate, and share your stories
            </p>
          </motion.div>
          
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                className="group"
              >
                <div className="p-8 rounded-3xl bg-card border border-border hover:border-primary/30 transition-colors duration-300">
                  <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center text-primary mb-6 group-hover:scale-110 transition-transform duration-300">
                    {feature.icon}
                  </div>
                  <h3 className="font-heading text-xl font-semibold mb-3">{feature.title}</h3>
                  <p className="font-body text-muted-foreground">{feature.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
      
      {/* CTA Section */}
      <section className="py-20 px-6 md:px-12 bg-muted/50">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="space-y-8"
          >
            <h2 className="font-heading text-4xl md:text-5xl font-bold">
              Ready to Start Your Adventure?
            </h2>
            <p className="font-body text-lg text-muted-foreground">
              Join thousands of young authors creating magical stories every day.
            </p>
            <Button 
              data-testid="start-creating-btn"
              onClick={() => navigate(user ? '/dashboard' : '/auth')}
              className="rounded-full px-10 py-7 text-xl font-ui bg-primary hover:bg-primary/90"
            >
              Start Creating Now
              <FiArrowRight className="ml-2" />
            </Button>
          </motion.div>
        </div>
      </section>
      
      {/* Footer */}
      <footer className="py-12 px-6 md:px-12 border-t border-border">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-2">
            <span className="font-heading text-2xl font-bold logo-text">Azories</span>
            <span className="text-muted-foreground">© 2024</span>
          </div>
          <p className="font-body text-sm text-muted-foreground">
            Where children become the authors of their own universes.
          </p>
        </div>
      </footer>
    </div>
  );
}
