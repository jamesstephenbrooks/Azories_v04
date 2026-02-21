import { useTheme } from '@/context/ThemeContext';
import { motion } from 'framer-motion';
import { FiSun, FiMoon } from 'react-icons/fi';

export default function ThemeToggle({ className = '' }) {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <motion.button
      onClick={toggleTheme}
      className={`relative w-14 h-7 rounded-full p-1 transition-colors duration-300 ${
        isDark ? 'bg-indigo-600' : 'bg-amber-400'
      } ${className}`}
      whileTap={{ scale: 0.95 }}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {/* Background icons */}
      <div className="absolute inset-0 flex items-center justify-between px-1.5">
        <FiMoon className={`w-3.5 h-3.5 ${isDark ? 'text-indigo-200' : 'text-amber-600/30'}`} />
        <FiSun className={`w-3.5 h-3.5 ${isDark ? 'text-indigo-400/30' : 'text-amber-100'}`} />
      </div>
      
      {/* Toggle circle */}
      <motion.div
        className={`w-5 h-5 rounded-full shadow-md flex items-center justify-center ${
          isDark ? 'bg-indigo-100' : 'bg-white'
        }`}
        animate={{ x: isDark ? 26 : 0 }}
        transition={{ type: 'spring', stiffness: 500, damping: 30 }}
      >
        {isDark ? (
          <FiMoon className="w-3 h-3 text-indigo-600" />
        ) : (
          <FiSun className="w-3 h-3 text-amber-500" />
        )}
      </motion.div>
    </motion.button>
  );
}

// Compact version for navigation
export function ThemeToggleCompact({ className = '' }) {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <motion.button
      onClick={toggleTheme}
      className={`p-2 rounded-full transition-colors ${
        isDark 
          ? 'bg-indigo-500/20 text-indigo-400 hover:bg-indigo-500/30' 
          : 'bg-amber-500/20 text-amber-500 hover:bg-amber-500/30'
      } ${className}`}
      whileTap={{ scale: 0.9 }}
      whileHover={{ scale: 1.05 }}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      <motion.div
        initial={false}
        animate={{ rotate: isDark ? 180 : 0 }}
        transition={{ duration: 0.3 }}
      >
        {isDark ? <FiMoon className="w-5 h-5" /> : <FiSun className="w-5 h-5" />}
      </motion.div>
    </motion.button>
  );
}
