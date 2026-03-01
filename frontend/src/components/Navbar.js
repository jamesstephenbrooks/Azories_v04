import { Link, useNavigate } from 'react-router-dom';
import { useTheme } from '@/context/ThemeContext';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { FiUser, FiLogOut, FiMenu, FiX, FiZap, FiDroplet } from 'react-icons/fi';
import { useState } from 'react';
import { ThemeToggleCompact } from './ThemeToggle';
import { StreakDisplay } from './ReadingStreaks';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

export const Navbar = () => {
  const { theme, toggleTheme } = useTheme();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

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
              to="/creators" 
              className="font-ui text-foreground/80 hover:text-foreground transition-colors flex items-center gap-1.5"
              data-testid="nav-creators"
            >
              <FiDroplet className="w-4 h-4 text-purple-500" />
              Creators
            </Link>
          )}
        </div>
        
        {/* Right side */}
        <div className="flex items-center gap-3">
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
                  onClick={() => navigate('/creators')}
                  data-testid="menu-creators"
                >
                  <FiDroplet className="mr-2 text-purple-500" />
                  Creators
                </DropdownMenuItem>
                <DropdownMenuItem 
                  onClick={logout}
                  className="text-destructive"
                  data-testid="menu-logout"
                >
                  <FiLogOut className="mr-2" />
                  Logout
                </DropdownMenuItem>
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
              to="/art-studio" 
              className="block px-4 py-3 font-ui rounded-xl hover:bg-muted min-h-[44px] flex items-center gap-2"
              onClick={() => setMobileOpen(false)}
              data-testid="mobile-nav-art-studio"
            >
              <FiDroplet className="w-4 h-4 text-purple-500" />
              Art Studio
            </Link>
          )}
          {user && (
            <Link 
              to="/pro-studio" 
              className="block px-4 py-3 font-ui rounded-xl hover:bg-muted min-h-[44px] flex items-center gap-2"
              onClick={() => setMobileOpen(false)}
              data-testid="mobile-nav-pro-studio"
            >
              <FiZap className="w-4 h-4 text-amber-500" />
              Pro Studio
            </Link>
          )}
        </div>
      )}
    </nav>
  );
};

export default Navbar;
