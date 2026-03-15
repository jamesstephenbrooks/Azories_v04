import { useAuth } from '../context/AuthContext';
import { FiClock } from 'react-icons/fi';

export default function TrialBanner() {
  const { user } = useAuth();
  
  if (!user) return null;
  
  // Show trial banner only for trial users
  if (!user.pro_trial) return null;
  
  // Get total hours remaining - prefer hours if available, otherwise convert days
  // Max is 48 hours for the trial
  let totalHours = 48;
  
  if (user.trial_hours_remaining) {
    totalHours = Math.min(user.trial_hours_remaining, 48);
  } else if (user.trial_days_remaining !== null && user.trial_days_remaining !== undefined) {
    // Convert days to hours, but cap at 48
    totalHours = Math.min(user.trial_days_remaining * 24, 48);
  }
  
  // Determine urgency colors based on time remaining
  let bgClass = 'from-purple-500/20 to-pink-500/20 border-purple-500/30';
  let textClass = 'text-purple-300';
  let iconClass = 'text-purple-400';
  
  // Use urgent colors when less than 12 hours remaining
  if (totalHours <= 12) {
    bgClass = 'from-red-500/20 to-pink-500/20 border-red-500/30';
    textClass = 'text-red-300';
    iconClass = 'text-red-400';
  } else if (totalHours <= 24) {
    bgClass = 'from-orange-500/20 to-pink-500/20 border-orange-500/30';
    textClass = 'text-orange-300';
    iconClass = 'text-orange-400';
  }
  
  // Format the time display
  const getTimeDisplay = () => {
    if (totalHours >= 48) {
      return <><span className="font-bold">48 hours</span> remaining</>;
    }
    if (totalHours >= 24) {
      const days = Math.floor(totalHours / 24);
      const hours = totalHours % 24;
      if (hours > 0) {
        return <><span className="font-bold">{days}d {hours}h</span> remaining</>;
      }
      return <><span className="font-bold">{days} day{days !== 1 ? 's' : ''}</span> remaining</>;
    }
    return <><span className="font-bold">{totalHours} hour{totalHours !== 1 ? 's' : ''}</span> remaining</>;
  };
  
  return (
    <div className={`bg-gradient-to-r ${bgClass} border rounded-xl p-3 mb-4`}>
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg bg-white/10 ${iconClass}`}>
          <FiClock className="w-4 h-4" />
        </div>
        <div>
          <p className={`text-sm font-medium ${textClass}`}>
            Pro Studio Trial: {getTimeDisplay()}
          </p>
          <p className="text-xs text-white/50">
            48-hour free access to all Pro Studio features - no credits needed!
          </p>
        </div>
      </div>
    </div>
  );
}
