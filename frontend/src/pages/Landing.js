import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useTheme } from '@/context/ThemeContext';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { FiBook, FiEdit3, FiHeadphones, FiArrowRight, FiStar, FiZap, FiPlay } from 'react-icons/fi';
import Navbar from '@/components/Navbar';
import { AZORA_ASSETS, AZORIES_TAGLINE } from '@/components/AzoraMascot';

// Sample book covers from our library
const FEATURED_BOOK_COVERS = [
  'https://res.cloudinary.com/dlbmjqmoy/image/upload/w_200,q_70/v1772261904/azories/books/the_wizards_apprentice/cover_clean.jpg',
  'https://res.cloudinary.com/dlbmjqmoy/image/upload/w_200,q_70/v1772217091/azories/books/colors_of_the_world/cover.png',
  'https://res.cloudinary.com/dlbmjqmoy/image/upload/w_200,q_70/v1772271593/azories/books/super_silly_superhero/cover.png',
];

export default function Landing() {
  const { theme } = useTheme();
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
      title: "Comic Mode",
      description: "Create comic strips with multiple panels per page"
    }
  ];

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      {/* Hero Section */}
      <section className="min-h-[90vh] relative overflow-hidden">
        {/* Magical gradient background */}
        <div 
          className="absolute inset-0 z-0"
          style={{
            background: theme === 'dark' 
              ? 'linear-gradient(135deg, #1a0a2e 0%, #16213e 50%, #0f0f23 100%)' 
              : 'linear-gradient(135deg, #f8f4ff 0%, #e8f4f8 50%, #fff8f0 100%)'
          }}
        />
        
        {/* Subtle sparkle effect overlay */}
        <div className="absolute inset-0 z-0 opacity-30">
          <div className="absolute top-20 left-[10%] w-2 h-2 rounded-full bg-yellow-400 animate-pulse" />
          <div className="absolute top-40 left-[25%] w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse" style={{ animationDelay: '0.5s' }} />
          <div className="absolute top-32 right-[30%] w-2 h-2 rounded-full bg-cyan-400 animate-pulse" style={{ animationDelay: '1s' }} />
          <div className="absolute top-60 right-[15%] w-1.5 h-1.5 rounded-full bg-pink-400 animate-pulse" style={{ animationDelay: '1.5s' }} />
          <div className="absolute bottom-40 left-[20%] w-2 h-2 rounded-full bg-emerald-400 animate-pulse" style={{ animationDelay: '0.7s' }} />
          <div className="absolute bottom-32 right-[25%] w-1.5 h-1.5 rounded-full bg-orange-400 animate-pulse" style={{ animationDelay: '1.2s' }} />
        </div>
        
        <div className="max-w-7xl mx-auto px-6 md:px-12 pt-32 pb-20 relative z-10">
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
                <span>{AZORIES_TAGLINE}</span>
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
                  user.subscription === 'pro' ? (
                    <Button 
                      data-testid="create-story-btn"
                      onClick={() => navigate('/dashboard')}
                      variant="outline"
                      className="rounded-full px-8 py-6 text-lg font-ui border-2"
                    >
                      <FiEdit3 className="mr-2" />
                      Create Your Story
                    </Button>
                  ) : (
                    <Button 
                      data-testid="upgrade-btn"
                      onClick={() => navigate('/dashboard')}
                      variant="outline"
                      className="rounded-full px-8 py-6 text-lg font-ui border-2 border-secondary text-secondary"
                    >
                      <FiZap className="mr-2" />
                      Upgrade to Pro
                    </Button>
                  )
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
              
              {/* Subscription info */}
              <div className="flex items-center gap-6 pt-4 text-sm text-muted-foreground">
                <div className="flex items-center gap-2">
                  <FiBook className="w-4 h-4 text-primary" />
                  <span>Free: Read unlimited books</span>
                </div>
                <div className="flex items-center gap-2">
                  <FiEdit3 className="w-4 h-4 text-secondary" />
                  <span>Pro: Create your own books</span>
                </div>
              </div>
            </motion.div>
            
            {/* Right - Azora Mascot and Book Covers */}
            <motion.div 
              initial={{ opacity: 0, y: 50 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="relative hidden lg:block"
            >
              <div className="relative w-full h-[500px]">
                {/* Azora pointing - main mascot with transparent background */}
                <motion.div 
                  className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-20"
                  animate={{ y: [0, -15, 0] }}
                  transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                >
                  <img 
                    src={AZORA_ASSETS.pointing}
                    alt="Azora - Your magical adventure guide"
                    className="w-80 h-[420px] object-contain"
                    style={{ 
                      filter: 'drop-shadow(0 25px 50px rgba(0,0,0,0.2))',
                    }}
                  />
                </motion.div>
                
                {/* Floating book covers - larger with animation */}
                <motion.div 
                  className="absolute top-4 right-4 w-28 h-36 rounded-xl overflow-hidden shadow-2xl z-10"
                  animate={{ 
                    y: [0, -12, 0], 
                    rotate: [2, 5, 2],
                    scale: [1, 1.02, 1]
                  }}
                  transition={{ duration: 4, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
                >
                  <img 
                    src={FEATURED_BOOK_COVERS[0]}
                    alt="Featured book"
                    className="w-full h-full object-cover"
                  />
                </motion.div>
                
                <motion.div 
                  className="absolute bottom-16 left-4 w-24 h-32 rounded-xl overflow-hidden shadow-2xl z-10"
                  animate={{ 
                    y: [0, 12, 0], 
                    rotate: [-2, -5, -2],
                    scale: [1, 1.03, 1]
                  }}
                  transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut", delay: 1 }}
                >
                  <img 
                    src={FEATURED_BOOK_COVERS[1]}
                    alt="Featured book"
                    className="w-full h-full object-cover"
                  />
                </motion.div>
                
                <motion.div 
                  className="absolute top-20 left-12 w-22 h-28 rounded-xl overflow-hidden shadow-2xl z-10"
                  animate={{ 
                    y: [0, -10, 0], 
                    rotate: [0, 3, 0],
                    scale: [1, 1.02, 1]
                  }}
                  transition={{ duration: 4.5, repeat: Infinity, ease: "easeInOut", delay: 0.3 }}
                >
                  <img 
                    src={FEATURED_BOOK_COVERS[2]}
                    alt="Featured book"
                    className="w-full h-full object-cover"
                  />
                </motion.div>
                
                {/* Magical glow behind Azora */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-gradient-radial from-purple-500/20 via-cyan-500/10 to-transparent rounded-full blur-3xl z-0" />
              </div>
            </motion.div>
          </div>
        </div>
        
        {/* Gradient fade at bottom */}
        <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-background to-transparent z-10" />
      </section>
      
      {/* Start Your Adventure - Book Showcase */}
      <section className="py-16 px-6 md:px-12 bg-background">
        <div className="max-w-7xl mx-auto">
          <motion.div 
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-12"
          >
            <h2 className="font-heading text-3xl md:text-4xl font-bold text-foreground mb-3">
              Start Your Adventure
            </h2>
            <p className="font-body text-muted-foreground">
              Discover magical stories waiting to be explored
            </p>
          </motion.div>
          
          <div className="flex justify-center gap-6 flex-wrap">
            {[
              { url: 'https://res.cloudinary.com/dlbmjqmoy/image/upload/w_300,q_80/v1772261904/azories/books/the_wizards_apprentice/cover_clean.jpg', title: "The Wizard's Apprentice" },
              { url: 'https://res.cloudinary.com/dlbmjqmoy/image/upload/w_300,q_80/v1772217091/azories/books/colors_of_the_world/cover.png', title: 'Colors of the World' },
              { url: 'https://res.cloudinary.com/dlbmjqmoy/image/upload/w_300,q_80/v1772271593/azories/books/super_silly_superhero/cover.png', title: 'Super Silly Superhero' },
              { url: 'https://res.cloudinary.com/dlbmjqmoy/image/upload/w_300,q_80/v1772217089/azories/books/the_case_of_the_missing_cookie/cover.jpg', title: 'Missing Cookies' },
              { url: 'https://res.cloudinary.com/dlbmjqmoy/image/upload/w_300,q_80/v1772271593/azories/books/the_dragons_secret_garden/cover.png', title: "Dragon's Secret Garden" },
            ].map((book, index) => (
              <motion.div
                key={book.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                whileHover={{ scale: 1.05, y: -10 }}
                className="cursor-pointer"
                onClick={() => navigate('/library')}
              >
                <div className="w-36 h-48 md:w-44 md:h-60 rounded-2xl overflow-hidden shadow-xl hover:shadow-2xl transition-shadow duration-300">
                  <img 
                    src={book.url}
                    alt={book.title}
                    className="w-full h-full object-cover"
                  />
                </div>
              </motion.div>
            ))}
          </div>
          
          <motion.div 
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.5 }}
            className="text-center mt-10"
          >
            <Button 
              onClick={() => navigate('/library')}
              variant="outline"
              className="rounded-full px-8 py-5 font-ui"
            >
              View All Books
              <FiArrowRight className="ml-2" />
            </Button>
          </motion.div>
        </div>
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
      
      {/* How it Works */}
      <section className="py-20 px-6 md:px-12 bg-muted/30">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="font-heading text-4xl md:text-5xl font-bold mb-4">
              How Azories Works
            </h2>
          </motion.div>
          
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { num: "01", title: "Write Your Story", desc: "Type or dictate your story, chapter by chapter" },
              { num: "02", title: "Generate Visuals", desc: "Use AI to create illustrations, videos, or upload your own" },
              { num: "03", title: "Share & Listen", desc: "Publish to the library and enjoy audiobook narration" }
            ].map((step, index) => (
              <motion.div
                key={step.num}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.2 }}
                className="relative"
              >
                <span className="font-heading text-8xl font-bold text-primary/10 absolute -top-6 -left-4">
                  {step.num}
                </span>
                <div className="relative pt-8 pl-4">
                  <h3 className="font-heading text-2xl font-semibold mb-3">{step.title}</h3>
                  <p className="font-body text-muted-foreground">{step.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
      
      {/* CTA Section */}
      <section className="py-20 px-6 md:px-12">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="space-y-8 p-12 rounded-3xl bg-gradient-to-br from-primary/5 to-secondary/5 border border-primary/10"
          >
            <h2 className="font-heading text-4xl md:text-5xl font-bold">
              Ready to Start Your Adventure?
            </h2>
            <p className="font-body text-lg text-muted-foreground">
              Join thousands of young authors creating magical stories every day.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Button 
                data-testid="start-creating-btn"
                onClick={() => navigate(user ? '/dashboard' : '/auth')}
                className="rounded-full px-10 py-7 text-xl font-ui bg-primary hover:bg-primary/90"
              >
                Start Creating Now
                <FiArrowRight className="ml-2" />
              </Button>
              <Button 
                variant="outline"
                onClick={() => navigate('/library')}
                className="rounded-full px-10 py-7 text-xl font-ui"
              >
                <FiPlay className="mr-2" />
                Browse Library
              </Button>
            </div>
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
