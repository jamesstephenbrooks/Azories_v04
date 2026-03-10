import { Link, useNavigate } from 'react-router-dom';
import { useTheme } from '@/context/ThemeContext';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { FiUser, FiLogOut, FiMenu, FiX, FiZap, FiDroplet, FiDollarSign } from 'react-icons/fi';
import { useState, useEffect } from 'react';
import { ThemeToggleCompact } from './ThemeToggle';
import { StreakDisplay } from './ReadingStreaks';
import { creditsAPI } from '@/services/api';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

// App version - increment this with each deployment
const APP_VERSION = 'v1.0.13';

export const Navbar = () => {
  const { theme, toggleTheme } = useTheme();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [credits, setCredits] = useState(null);

  // Fetch credits when user is logged in
  useEffect(() => {
    if (user) {
      creditsAPI.getBalance()
        .then(res => setCredits(res.data.credits || 0))
        .catch(() => setCredits(null));
    }
  }, [user]);

  return (
    <nav className="fixed top-4 left-1/2 -translate-x-1/2 z-50 w-[95%] max-w-6xl">
      <div className="glass rounded-full px-6 py-3 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2" data-testid="navbar-logo">
          <span className="font-heading text-2xl font-bold logo-text">Azories</span>
        </Link>
        
        {/* Desktop Nav */}
        <div className="hidden md:flex items-center gap-6">
          <Link 
            to="/library" 
            className="font-ui text-foreground/80 hover:text-foreground transition-colors"
            data-testid="nav-library"
          >
            Library
          </Link>
          
          {user && (
            <Link 
              to="/dashboard" 
              className="font-ui text-foreground/80 hover:text-foreground transition-colors"
              data-testid="nav-dashboard"
            >
              My Books
            </Link>
          )}
          
          {user && (
            <Link 
              to="/ai-stories" 
              className="font-ui text-foreground/80 hover:text-foreground transition-colors flex items-center gap-1.5"
              data-testid="nav-ai-stories"
            >
              <img src="https://static.prod-images.emergentagent.com/jobs/145964ea-a5d4-4590-8e1b-a21ed8ca2cd2/images/8515ab60b7ad93f5867e025fe18e43b3916962f27b5c15dc8d66d45d6c530105.png" alt="" className="w-5 h-5 object-contain" />
              AI Stories
            </Link>
          )}
          
          {user && (
            <Link 
              to="/creators" 
              className="font-ui text-foreground/80 hover:text-foreground transition-colors flex items-center gap-1.5"
              data-testid="nav-creators"
            >
              <img src="https://static.prod-images.emergentagent.com/jobs/145964ea-a5d4-4590-8e1b-a21ed8ca2cd2/images/6abddb8323c8f308894f61fd3e7e9e87169635a50bed38649e770085b66c0a5b.png" alt="" className="w-5 h-5 object-contain" />
              Image Creator
            </Link>
          )}
          
          {user && (
            <Link 
              to="/pro-studio" 
              className="font-ui text-foreground/80 hover:text-foreground transition-colors flex items-center gap-1.5"
              data-testid="nav-pro-studio"
            >
              <img src="https://static.prod-images.emergentagent.com/jobs/145964ea-a5d4-4590-8e1b-a21ed8ca2cd2/images/9de85d575bb699661553a31cef27fb34df03f2a5edf7d04dd8f27eda40e2df80.png" alt="" className="w-5 h-5 object-contain" />
              Pro Studio
            </Link>
          )}
        </div>
        
        {/* Right side */}
        <div className="flex items-center gap-3">
          {/* Credit Balance Display */}
          {user && credits !== null && (
            <button
              onClick={() => navigate('/credits')}
              className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-gradient-to-r from-amber-500/20 to-orange-500/20 hover:from-amber-500/30 hover:to-orange-500/30 transition-all cursor-pointer"
              data-testid="credit-balance"
            >
              <FiZap className="w-4 h-4 text-amber-500" />
              <span className="text-sm font-semibold text-amber-600 dark:text-amber-400">
                {credits.toLocaleString()}
              </span>
            </button>
          )}
          
          <ThemeToggleCompact />
          
          {user ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button 
                  variant="ghost" 
                  className="rounded-full gap-2"
                  data-testid="user-menu-trigger"
                >
                  <FiUser className="w-5 h-5" />
                  <span className="hidden md:inline font-ui">{user.name}</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                {/* Credit Balance in dropdown */}
                <div className="px-2 py-2 border-b border-border/50 mb-1">
                  <button 
                    onClick={() => navigate('/credits')}
                    className="w-full flex items-center justify-between px-2 py-1 rounded-md hover:bg-muted transition-colors"
                  >
                    <span className="text-sm text-muted-foreground">Credits</span>
                    <span className="flex items-center gap-1 text-sm font-semibold text-amber-600 dark:text-amber-400">
                      <FiZap className="w-3 h-3" />
                      {credits !== null ? credits.toLocaleString() : '...'}
                    </span>
                  </button>
                </div>
                <DropdownMenuItem 
                  onClick={() => navigate('/profile')}
                  data-testid="menu-profile"
                >
                  <FiUser className="mr-2" />
                  My Profile
                </DropdownMenuItem>
                <DropdownMenuItem 
                  onClick={() => navigate('/dashboard')}
                  data-testid="menu-dashboard"
                >
                  My Books
                </DropdownMenuItem>
                <DropdownMenuItem 
                  onClick={() => navigate('/ai-stories')}
                  data-testid="menu-ai-stories"
                >
                  <img src="https://static.prod-images.emergentagent.com/jobs/145964ea-a5d4-4590-8e1b-a21ed8ca2cd2/images/8515ab60b7ad93f5867e025fe18e43b3916962f27b5c15dc8d66d45d6c530105.png" alt="" className="w-5 h-5 mr-2 object-contain" />
                  AI Stories
                </DropdownMenuItem>
                <DropdownMenuItem 
                  onClick={() => navigate('/creators')}
                  data-testid="menu-creators"
                >
                  <img src="https://static.prod-images.emergentagent.com/jobs/145964ea-a5d4-4590-8e1b-a21ed8ca2cd2/images/6abddb8323c8f308894f61fd3e7e9e87169635a50bed38649e770085b66c0a5b.png" alt="" className="w-5 h-5 mr-2 object-contain" />
                  Image Creator
                </DropdownMenuItem>
                <DropdownMenuItem 
                  onClick={() => navigate('/pro-studio')}
                  data-testid="menu-pro-studio"
                >
                  <img src="https://static.prod-images.emergentagent.com/jobs/145964ea-a5d4-4590-8e1b-a21ed8ca2cd2/images/9de85d575bb699661553a31cef27fb34df03f2a5edf7d04dd8f27eda40e2df80.png" alt="" className="w-5 h-5 mr-2 object-contain" />
                  Pro Studio
                </DropdownMenuItem>
                <DropdownMenuItem 
                  onClick={() => navigate('/credits')}
                  data-testid="menu-buy-credits"
                >
                  <img src="https://static.prod-images.emergentagent.com/jobs/145964ea-a5d4-4590-8e1b-a21ed8ca2cd2/images/1501b83d52263b743e57ba5b1060fd241424e47c1a4e7cb89ffdcb01e3177e1b.png" alt="" className="w-5 h-5 mr-2 object-contain" />
                  Buy Credits
                </DropdownMenuItem>
                <DropdownMenuItem 
                  onClick={logout}
                  className="text-destructive"
                  data-testid="menu-logout"
                >
                  <img src="https://static.prod-images.emergentagent.com/jobs/145964ea-a5d4-4590-8e1b-a21ed8ca2cd2/images/8fd79389761db4e4b8898ec4e7cdcdc944784be1c379c7516f96ab3dfcbd2819.png" alt="" className="w-5 h-5 mr-2 object-contain" />
                  Logout
                </DropdownMenuItem>
                
                {/* Version number */}
                <div className="px-2 py-2 mt-2 border-t border-border">
                  <span className="text-xs text-muted-foreground">{APP_VERSION}</span>
                </div>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <Button 
              onClick={() => navigate('/auth')}
              className="rounded-full font-ui"
              data-testid="nav-login-btn"
            >
              Sign In
            </Button>
          )}
          
          {/* Mobile menu toggle */}
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden rounded-full min-w-[44px] min-h-[44px]"
            onClick={() => setMobileOpen(!mobileOpen)}
            data-testid="mobile-menu-toggle"
          >
            {mobileOpen ? <FiX className="w-6 h-6" /> : <FiMenu className="w-6 h-6" />}
          </Button>
        </div>
      </div>
      
      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden glass mt-2 rounded-2xl p-4 space-y-1">
          <Link 
            to="/library" 
            className="block px-4 py-3 font-ui rounded-xl hover:bg-muted min-h-[44px] flex items-center"
            onClick={() => setMobileOpen(false)}
            data-testid="mobile-nav-library"
          >
            Library
          </Link>
          {user && (
            <Link 
              to="/dashboard" 
              className="block px-4 py-3 font-ui rounded-xl hover:bg-muted min-h-[44px] flex items-center"
              onClick={() => setMobileOpen(false)}
              data-testid="mobile-nav-dashboard"
            >
              My Books
            </Link>
          )}
          {user && (
            <Link 
              to="/ai-stories" 
              className="block px-4 py-3 font-ui rounded-xl hover:bg-muted min-h-[44px] flex items-center gap-2"
              onClick={() => setMobileOpen(false)}
              data-testid="mobile-nav-ai-stories"
            >
              <img src="https://static.prod-images.emergentagent.com/jobs/145964ea-a5d4-4590-8e1b-a21ed8ca2cd2/images/8515ab60b7ad93f5867e025fe18e43b3916962f27b5c15dc8d66d45d6c530105.png" alt="" className="w-5 h-5 object-contain" />
              AI Stories
            </Link>
          )}
          {user && (
            <Link 
              to="/creators" 
              className="block px-4 py-3 font-ui rounded-xl hover:bg-muted min-h-[44px] flex items-center gap-2"
              onClick={() => setMobileOpen(false)}
              data-testid="mobile-nav-creators"
            >
              <img src="https://static.prod-images.emergentagent.com/jobs/145964ea-a5d4-4590-8e1b-a21ed8ca2cd2/images/6abddb8323c8f308894f61fd3e7e9e87169635a50bed38649e770085b66c0a5b.png" alt="" className="w-5 h-5 object-contain" />
              Image Creator
            </Link>
          )}
          {user && (
            <Link 
              to="/pro-studio" 
              className="block px-4 py-3 font-ui rounded-xl hover:bg-muted min-h-[44px] flex items-center gap-2"
              onClick={() => setMobileOpen(false)}
              data-testid="mobile-nav-pro-studio"
            >
              <img src="https://static.prod-images.emergentagent.com/jobs/145964ea-a5d4-4590-8e1b-a21ed8ca2cd2/images/9de85d575bb699661553a31cef27fb34df03f2a5edf7d04dd8f27eda40e2df80.png" alt="" className="w-5 h-5 object-contain" />
              Pro Studio
            </Link>
          )}
        </div>
      )}
    </nav>
  );
};

export default Navbar;
