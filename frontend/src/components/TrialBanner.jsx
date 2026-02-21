import { useAuth } from '../context/AuthContext';
import { FiClock, FiStar, FiArrowRight } from 'react-icons/fi';
import { Link } from 'react-router-dom';

export default function TrialBanner() {
  const { user } = useAuth();
  
  if (!user) return null;
  
  // Show trial banner only for trial users
  if (!user.pro_trial) return null;
  
  const daysRemaining = user.trial_days_remaining;
  
  // Determine urgency colors
  let bgClass = 'from-purple-500/20 to-pink-500/20 border-purple-500/30';
  let textClass = 'text-purple-300';
  let iconClass = 'text-purple-400';
  
  if (daysRemaining !== null && daysRemaining <= 7) {
    bgClass = 'from-orange-500/20 to-red-500/20 border-orange-500/30';
    textClass = 'text-orange-300';
    iconClass = 'text-orange-400';
  }
  if (daysRemaining !== null && daysRemaining <= 3) {
    bgClass = 'from-red-500/20 to-pink-500/20 border-red-500/30';
    textClass = 'text-red-300';
    iconClass = 'text-red-400';
  }
  
  return (
    <div className={`bg-gradient-to-r ${bgClass} border rounded-xl p-3 mb-4`}>
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg bg-white/10 ${iconClass}`}>
            <FiStar className="w-4 h-4" />
          </div>
          <div>
            <p className={`text-sm font-medium ${textClass}`}>
              {daysRemaining !== null ? (
                <>
                  Pro Trial: <span className="font-bold">{daysRemaining} days</span> remaining
                </>
              ) : (
                'Pro Trial Active'
              )}
            </p>
            <p className="text-xs text-white/50">
              Enjoy unlimited access to all Pro features!
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
