import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiAward, FiZap, FiBook, FiStar, FiHeart, FiTrendingUp, FiClock, FiTarget } from 'react-icons/fi';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

// Badge definitions
export const BADGES = {
  first_book: {
    id: 'first_book',
    name: 'First Read',
    description: 'Completed your first book',
    icon: FiBook,
    color: 'from-blue-500 to-cyan-500',
    requirement: 'Complete 1 book'
  },
  bookworm: {
    id: 'bookworm',
    name: 'Bookworm',
    description: 'Read 5 books',
    icon: FiStar,
    color: 'from-yellow-500 to-orange-500',
    requirement: 'Complete 5 books'
  },
  streak_3: {
    id: 'streak_3',
    name: '3-Day Streak',
    description: 'Read for 3 days in a row',
    icon: FiZap,
    color: 'from-green-500 to-emerald-500',
    requirement: '3 day reading streak'
  },
  streak_7: {
    id: 'streak_7',
    name: 'Week Warrior',
    description: 'Read for 7 days in a row',
    icon: FiTrendingUp,
    color: 'from-purple-500 to-pink-500',
    requirement: '7 day reading streak'
  },
  streak_30: {
    id: 'streak_30',
    name: 'Dedicated Reader',
    description: 'Read for 30 days in a row',
    icon: FiAward,
    color: 'from-amber-500 to-red-500',
    requirement: '30 day reading streak'
  },
  night_owl: {
    id: 'night_owl',
    name: 'Night Owl',
    description: 'Read late at night',
    icon: FiClock,
    color: 'from-indigo-500 to-purple-500',
    requirement: 'Read after midnight'
  },
  early_bird: {
    id: 'early_bird',
    name: 'Early Bird',
    description: 'Read early in the morning',
    icon: FiStar,
    color: 'from-orange-400 to-yellow-400',
    requirement: 'Read before 7 AM'
  },
  genre_explorer: {
    id: 'genre_explorer',
    name: 'Genre Explorer',
    description: 'Read books from 5 different genres',
    icon: FiTarget,
    color: 'from-teal-500 to-blue-500',
    requirement: 'Read 5 different genres'
  },
  supporter: {
    id: 'supporter',
    name: 'Supporter',
    description: 'Follow 5 authors',
    icon: FiHeart,
    color: 'from-pink-500 to-rose-500',
    requirement: 'Follow 5 authors'
  },
  creator: {
    id: 'creator',
    name: 'Creator',
    description: 'Publish your first book',
    icon: FiBook,
    color: 'from-violet-500 to-purple-500',
    requirement: 'Publish 1 book'
  }
};

// Streak display component
export function StreakDisplay({ streak = 0, compact = false }) {
  const isActive = streak > 0;
  
  if (compact) {
    return (
      <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
        isActive ? 'bg-orange-500/10 text-orange-500' : 'bg-muted text-muted-foreground'
      }`}>
        <FiZap className={`w-3 h-3 ${isActive ? 'text-orange-500' : ''}`} />
        <span>{streak}</span>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className={`relative p-4 rounded-2xl ${
        isActive 
          ? 'bg-gradient-to-r from-orange-500/10 to-red-500/10 border border-orange-500/20' 
          : 'bg-muted/50'
      }`}
    >
      <div className="flex items-center gap-4">
        <div className={`w-14 h-14 rounded-xl flex items-center justify-center ${
          isActive ? 'bg-gradient-to-r from-orange-500 to-red-500' : 'bg-muted'
        }`}>
          <FiZap className={`w-7 h-7 ${isActive ? 'text-white' : 'text-muted-foreground'}`} />
        </div>
        <div>
          <div className="flex items-baseline gap-2">
            <span className={`text-3xl font-bold ${isActive ? 'text-orange-500' : 'text-muted-foreground'}`}>
              {streak}
            </span>
            <span className="text-sm text-muted-foreground">day streak</span>
          </div>
          <p className="text-sm text-muted-foreground">
            {isActive 
              ? streak >= 7 
                ? "You're on fire! Keep it up!" 
                : "Great progress! Keep reading!"
              : "Start reading to build your streak!"
            }
          </p>
        </div>
      </div>
      
      {/* Streak flames animation */}
      {isActive && streak >= 3 && (
        <div className="absolute -top-2 right-4 flex gap-1">
          {[...Array(Math.min(streak, 5))].map((_, i) => (
            <motion.div
              key={i}
              initial={{ y: 10, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: i * 0.1 }}
              className="text-orange-500"
            >
              🔥
            </motion.div>
          ))}
        </div>
      )}
    </motion.div>
  );
}

// Badge component
export function Badge({ badge, earned = false, size = 'md', showDetails = true }) {
  const badgeInfo = typeof badge === 'string' ? BADGES[badge] : badge;
  if (!badgeInfo) return null;

  const Icon = badgeInfo.icon;
  const sizeClasses = {
    sm: 'w-10 h-10',
    md: 'w-14 h-14',
    lg: 'w-20 h-20'
  };

  return (
    <motion.div
      whileHover={{ scale: 1.05 }}
      className={`relative group ${!earned ? 'opacity-40 grayscale' : ''}`}
    >
      <div className={`${sizeClasses[size]} rounded-xl bg-gradient-to-r ${badgeInfo.color} flex items-center justify-center shadow-lg`}>
        <Icon className={`${size === 'sm' ? 'w-5 h-5' : size === 'lg' ? 'w-10 h-10' : 'w-7 h-7'} text-white`} />
      </div>
      
      {showDetails && (
        <div className="mt-2 text-center">
          <p className="text-xs font-medium truncate">{badgeInfo.name}</p>
        </div>
      )}
      
      {/* Tooltip */}
      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-popover border rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 whitespace-nowrap">
        <p className="font-medium text-sm">{badgeInfo.name}</p>
        <p className="text-xs text-muted-foreground">{badgeInfo.description}</p>
        {!earned && (
          <p className="text-xs text-primary mt-1">{badgeInfo.requirement}</p>
        )}
      </div>
      
      {/* Lock icon for unearned */}
      {!earned && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-6 h-6 bg-background rounded-full flex items-center justify-center shadow">
            <span className="text-xs">🔒</span>
          </div>
        </div>
      )}
    </motion.div>
  );
}

// Badge collection grid
export function BadgeCollection({ earnedBadges = [], showAll = true }) {
  const allBadges = Object.keys(BADGES);
  const badgesToShow = showAll ? allBadges : earnedBadges;

  return (
    <div className="grid grid-cols-5 gap-4">
      {badgesToShow.map(badgeId => (
        <Badge 
          key={badgeId} 
          badge={badgeId} 
          earned={earnedBadges.includes(badgeId)} 
        />
      ))}
    </div>
  );
}

// New badge earned popup
export function NewBadgePopup({ badge, onClose }) {
  const badgeInfo = BADGES[badge];
  if (!badgeInfo) return null;

  const Icon = badgeInfo.icon;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0, rotate: -180 }}
          animate={{ scale: 1, rotate: 0 }}
          exit={{ scale: 0, rotate: 180 }}
          transition={{ type: 'spring', damping: 15 }}
          className="bg-background rounded-3xl p-8 text-center max-w-sm mx-4"
          onClick={e => e.stopPropagation()}
        >
          {/* Confetti effect */}
          <div className="absolute inset-0 pointer-events-none overflow-hidden rounded-3xl">
            {[...Array(20)].map((_, i) => (
              <motion.div
                key={i}
                initial={{ y: -20, x: Math.random() * 300, opacity: 1 }}
                animate={{ y: 400, opacity: 0 }}
                transition={{ duration: 2, delay: Math.random() * 0.5 }}
                className="absolute w-2 h-2 rounded-full"
                style={{ backgroundColor: ['#f59e0b', '#10b981', '#8b5cf6', '#ec4899'][i % 4] }}
              />
            ))}
          </div>

          <div className="relative">
            <motion.div
              animate={{ rotate: [0, 10, -10, 0] }}
              transition={{ duration: 0.5, repeat: 3 }}
              className={`w-24 h-24 mx-auto rounded-2xl bg-gradient-to-r ${badgeInfo.color} flex items-center justify-center shadow-2xl mb-4`}
            >
              <Icon className="w-12 h-12 text-white" />
            </motion.div>
            
            <h2 className="text-2xl font-bold mb-2">New Badge!</h2>
            <h3 className={`text-xl font-bold bg-gradient-to-r ${badgeInfo.color} bg-clip-text text-transparent mb-2`}>
              {badgeInfo.name}
            </h3>
            <p className="text-muted-foreground mb-6">{badgeInfo.description}</p>
            
            <Button onClick={onClose} className="rounded-full px-8">
              Awesome!
            </Button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

// Hook to manage streaks and badges
export function useStreaksAndBadges() {
  const [streak, setStreak] = useState(0);
  const [badges, setBadges] = useState([]);
  const [newBadge, setNewBadge] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchStats = async () => {
    try {
      const res = await axios.get(`${API}/api/user/reading-stats`);
      setStreak(res.data.streak || 0);
      setBadges(res.data.badges || []);
    } catch (error) {
      console.error('Failed to fetch reading stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const recordReading = async (bookId, timeSpent = 0) => {
    try {
      const res = await axios.post(`${API}/api/user/record-reading`, {
        book_id: bookId,
        time_spent: timeSpent
      });
      
      if (res.data.new_badge) {
        setNewBadge(res.data.new_badge);
        setBadges(prev => [...prev, res.data.new_badge]);
      }
      
      if (res.data.streak !== undefined) {
        setStreak(res.data.streak);
      }
      
      return res.data;
    } catch (error) {
      console.error('Failed to record reading:', error);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  return {
    streak,
    badges,
    newBadge,
    setNewBadge,
    loading,
    recordReading,
    refreshStats: fetchStats
  };
}

// Import Button for the NewBadgePopup
import { Button } from '@/components/ui/button';
