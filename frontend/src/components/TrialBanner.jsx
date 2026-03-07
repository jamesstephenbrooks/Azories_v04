import { useAuth } from '../context/AuthContext';
import { FiClock, FiStar, FiArrowRight } from 'react-icons/fi';
import { Link } from 'react-router-dom';

export default function TrialBanner() {
  const { user } = useAuth();
  
  if (!user) return null;
  
  // Show trial banner only for trial users
  if (!user.pro_trial) return null;
  
  const daysRemaining = user.trial_days_remaining;
  const hoursRemaining = user.trial_hours_remaining;
  
  // Determine urgency colors based on time remaining
  let bgClass = 'from-purple-500/20 to-pink-500/20 border-purple-500/30';
  let textClass = 'text-purple-300';
  let iconClass = 'text-purple-400';
  
  // If showing hours (less than 1 day), use urgent colors
  if (hoursRemaining !== null && hoursRemaining !== undefined) {
    bgClass = 'from-red-500/20 to-pink-500/20 border-red-500/30';
    textClass = 'text-red-300';
    iconClass = 'text-red-400';
  } else if (daysRemaining !== null && daysRemaining <= 1) {
    bgClass = 'from-red-500/20 to-pink-500/20 border-red-500/30';
    textClass = 'text-red-300';
    iconClass = 'text-red-400';
  }
  
  // Format the time remaining display
  const getTimeDisplay = () => {
    if (hoursRemaining !== null && hoursRemaining !== undefined) {
      return <><span className="font-bold">{hoursRemaining} hour{hoursRemaining !== 1 ? 's' : ''}</span> remaining</>;
    }
    if (daysRemaining !== null) {
      return <><span className="font-bold">{daysRemaining} day{daysRemaining !== 1 ? 's' : ''}</span> remaining</>;
    }
    return null;
  };
  
  return (
    <div className={`bg-gradient-to-r ${bgClass} border rounded-xl p-3 mb-4`}>
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg bg-white/10 ${iconClass}`}>
            <FiClock className="w-4 h-4" />
          </div>
          <div>
            <p className={`text-sm font-medium ${textClass}`}>
              Pro Trial: {getTimeDisplay() || 'Active'}
            </p>
            <p className="text-xs text-white/50">
              {hoursRemaining !== null && hoursRemaining !== undefined 
                ? 'Your free Pro trial - enjoy all features!'
                : daysRemaining && daysRemaining > 2 
                  ? 'Enjoy all Pro features during your trial!'
                  : '48-hour access to all Pro features!'}
            </p>
          </div>
        </div>
        
        <Link 
          to="/pricing" 
          className="flex items-center gap-1 px-3 py-1.5 bg-white/10 hover:bg-white/20 rounded-lg text-xs text-white transition-colors"
        >
          <span>Upgrade Now</span>
          <FiArrowRight className="w-3 h-3" />
        </Link>
      </div>
    </div>
  );
}
