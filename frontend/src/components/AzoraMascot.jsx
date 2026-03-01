import { motion } from 'framer-motion';

// Azora mascot URLs - Official Azories character
export const AZORA_ASSETS = {
  // Main poses - with background removal for transparent effect
  pointing: 'https://res.cloudinary.com/dlbmjqmoy/image/upload/e_background_removal/v1772279592/azories/mascot/azora_pose4_pointing.png',
  pointingOriginal: 'https://res.cloudinary.com/dlbmjqmoy/image/upload/v1772279592/azories/mascot/azora_pose4_pointing.jpg',
  confident: 'https://res.cloudinary.com/dlbmjqmoy/image/upload/v1772279581/azories/mascot/azora_pose1_confident.jpg',
  running: 'https://res.cloudinary.com/dlbmjqmoy/image/upload/v1772279585/azories/mascot/azora_pose2_running.jpg',
  runningTransparent: 'https://res.cloudinary.com/dlbmjqmoy/image/upload/e_background_removal/v1772279585/azories/mascot/azora_pose2_running.png',
  reading: 'https://res.cloudinary.com/dlbmjqmoy/image/upload/e_background_removal/v1772279589/azories/mascot/azora_pose3_reading.png',
  
  // Additional variations
  readingCozy: 'https://res.cloudinary.com/dlbmjqmoy/image/upload/e_background_removal/v1772279866/azories/mascot/azora_reading_cozy.png',
  avatar: 'https://res.cloudinary.com/dlbmjqmoy/image/upload/v1772279871/azories/mascot/azora_avatar_face.jpg',
  waving: 'https://res.cloudinary.com/dlbmjqmoy/image/upload/e_background_removal/v1772279875/azories/mascot/azora_waving_hello.png',
  dragonIcon: 'https://res.cloudinary.com/dlbmjqmoy/image/upload/e_background_removal/v1772279877/azories/mascot/dragon_icon_solo.png',
  
  // Templates
  backCoverTemplate: 'https://res.cloudinary.com/dlbmjqmoy/image/upload/v1772279892/azories/templates/back_cover_template_v1.jpg'
};

// Dragon Loading Spinner Component
export function DragonSpinner({ size = 'md', className = '' }) {
  const sizeClasses = {
    sm: 'w-8 h-8',
    md: 'w-16 h-16',
    lg: 'w-24 h-24',
    xl: 'w-32 h-32'
  };

  return (
    <motion.div 
      className={`${sizeClasses[size]} ${className}`}
      animate={{ 
        rotate: [0, 10, -10, 0],
        scale: [1, 1.05, 1]
      }}
      transition={{ 
        duration: 1.5, 
        repeat: Infinity, 
        ease: "easeInOut" 
      }}
    >
      <img 
        src={AZORA_ASSETS.dragonIcon} 
        alt="Loading..." 
        className="w-full h-full object-contain rounded-full"
      />
    </motion.div>
  );
}

// Azora Welcome Component
export function AzoraWelcome({ title = "Welcome to Azories!", subtitle, className = '' }) {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex flex-col items-center text-center ${className}`}
    >
      <motion.img 
        src={AZORA_ASSETS.waving}
        alt="Azora waving hello"
        className="w-48 h-64 object-contain mb-6"
        animate={{ y: [0, -10, 0] }}
        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
      />
      <h2 className="text-2xl font-bold text-foreground mb-2">{title}</h2>
      {subtitle && <p className="text-muted-foreground">{subtitle}</p>}
    </motion.div>
  );
}

// Azora Empty State Component
export function AzoraEmptyState({ 
  title = "Nothing here yet", 
  message = "Start exploring to find amazing stories!",
  action,
  actionLabel = "Explore Library",
  className = '' 
}) {
  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`flex flex-col items-center text-center py-12 ${className}`}
    >
      <motion.img 
        src={AZORA_ASSETS.readingCozy}
        alt="Azora reading"
        className="w-40 h-52 object-contain mb-6 opacity-80"
        animate={{ y: [0, -5, 0] }}
        transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
      />
      <h3 className="text-xl font-semibold text-foreground mb-2">{title}</h3>
      <p className="text-muted-foreground mb-6 max-w-sm">{message}</p>
      {action && (
        <button 
          onClick={action}
          className="px-6 py-2 bg-primary text-primary-foreground rounded-full hover:bg-primary/90 transition-colors"
        >
          {actionLabel}
        </button>
      )}
    </motion.div>
  );
}

// Full Page Loading Screen with Azora
export function AzoraLoadingScreen({ message = "Loading magical adventures..." }) {
  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-gradient-to-b from-purple-900/95 to-slate-900/95 backdrop-blur-sm">
      <motion.img 
        src={AZORA_ASSETS.waving}
        alt="Azora"
        className="w-40 h-52 object-contain mb-8"
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ 
          opacity: 1, 
          scale: 1,
          y: [0, -15, 0]
        }}
        transition={{ 
          opacity: { duration: 0.5 },
          scale: { duration: 0.5 },
          y: { duration: 2, repeat: Infinity, ease: "easeInOut" }
        }}
      />
      <motion.h2 
        className="text-2xl font-bold text-white mb-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        Welcome to Azories
      </motion.h2>
      <motion.p 
        className="text-white/70 mb-6"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        {message}
      </motion.p>
      <DragonSpinner size="md" />
    </div>
  );
}

// Tagline constant
export const AZORIES_TAGLINE = "Where every child is the hero of their own story";

export default { 
  AZORA_ASSETS, 
  DragonSpinner, 
  AzoraWelcome, 
  AzoraEmptyState, 
  AzoraLoadingScreen,
  AZORIES_TAGLINE 
};
