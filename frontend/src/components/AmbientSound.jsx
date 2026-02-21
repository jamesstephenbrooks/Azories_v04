import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { 
  FiVolume2, FiVolumeX, FiCloud, FiSun, FiMoon, FiWind,
  FiDroplet, FiMusic, FiCoffee, FiFeather
} from 'react-icons/fi';

const API = process.env.REACT_APP_BACKEND_URL;

// Ambient sounds - served through backend proxy to avoid CORS
const AMBIENT_SOUNDS = {
  rain: {
    name: 'Rain',
    icon: FiDroplet,
    color: 'text-blue-400',
    key: 'rain',
    description: 'Gentle rainfall'
  },
  fireplace: {
    name: 'Fireplace',
    icon: FiSun,
    color: 'text-orange-400',
    key: 'fireplace',
    description: 'Crackling fire'
  },
  forest: {
    name: 'Forest',
    icon: FiFeather,
    color: 'text-green-400',
    key: 'forest',
    description: 'Birds & nature'
  },
  ocean: {
    name: 'Ocean',
    icon: FiWind,
    color: 'text-cyan-400',
    key: 'ocean',
    description: 'Ocean waves'
  },
  cafe: {
    name: 'Café',
    icon: FiCoffee,
    color: 'text-amber-400',
    key: 'cafe',
    description: 'Coffee shop'
  },
  night: {
    name: 'Night',
    icon: FiMoon,
    color: 'text-indigo-400',
    key: 'night',
    description: 'Crickets & night'
  },
  wind: {
    name: 'Wind',
    icon: FiCloud,
    color: 'text-gray-400',
    key: 'wind',
    description: 'Soft breeze'
  },
  library: {
    name: 'Library',
    icon: FiMusic,
    color: 'text-purple-400',
    key: 'library',
    description: 'Quiet ambience'
  }
};

// Genre to ambient sound mapping
const GENRE_AMBIENT_MAP = {
  'Fantasy': ['fireplace', 'forest', 'night'],
  'Adventure': ['forest', 'ocean', 'wind'],
  'Mystery': ['rain', 'night', 'library'],
  'Romance': ['rain', 'cafe', 'fireplace'],
  'Sci-Fi': ['wind', 'night', 'library'],
  'Horror': ['night', 'wind', 'rain'],
  'Comedy': ['cafe', 'forest', 'library'],
  'Drama': ['rain', 'fireplace', 'cafe'],
  'Educational': ['library', 'cafe', 'forest'],
  'General': ['library', 'rain', 'cafe']
};

export default function AmbientSound({ genre = 'General', isReading = false }) {
  const [isOpen, setIsOpen] = useState(false);
  const [activeSound, setActiveSound] = useState(null);
  const [volume, setVolume] = useState([30]);
  const [isMuted, setIsMuted] = useState(false);
  const audioRef = useRef(null);

  // Get recommended sounds for genre
  const recommendedSounds = GENRE_AMBIENT_MAP[genre] || GENRE_AMBIENT_MAP['General'];

  useEffect(() => {
    // Auto-suggest ambient sound when reading starts
    if (isReading && !activeSound) {
      // Don't auto-play, just open the selector
    }
  }, [isReading]);

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = isMuted ? 0 : volume[0] / 100;
    }
  }, [volume, isMuted]);

  const playSound = (soundKey) => {
    const sound = AMBIENT_SOUNDS[soundKey];
    if (!sound) return;

    if (audioRef.current) {
      audioRef.current.pause();
    }

    const audio = new Audio(sound.url);
    audio.crossOrigin = "anonymous"; // Help with CORS
    audio.loop = true;
    audio.volume = volume[0] / 100;
    
    audio.play()
      .then(() => {
        audioRef.current = audio;
        setActiveSound(soundKey);
      })
      .catch((error) => {
        console.error('Failed to play audio:', error);
        // Try alternate approach - some browsers need user interaction first
        alert('Click again to play sound. Your browser requires user interaction first.');
      });
  };

  const stopSound = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    setActiveSound(null);
  };

  const toggleMute = () => {
    setIsMuted(!isMuted);
    if (audioRef.current) {
      audioRef.current.volume = isMuted ? volume[0] / 100 : 0;
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
      }
    };
  }, []);

  const SoundButton = ({ soundKey, recommended = false }) => {
    const sound = AMBIENT_SOUNDS[soundKey];
    const Icon = sound.icon;
    const isActive = activeSound === soundKey;

    return (
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => isActive ? stopSound() : playSound(soundKey)}
        className={`relative flex flex-col items-center gap-2 p-4 rounded-xl transition-all ${
          isActive 
            ? 'bg-primary/20 border-2 border-primary shadow-lg' 
            : 'bg-muted/50 hover:bg-muted border-2 border-transparent'
        }`}
      >
        {recommended && !isActive && (
          <span className="absolute -top-1 -right-1 w-2 h-2 bg-yellow-400 rounded-full animate-pulse" />
        )}
        <div className={`p-3 rounded-full ${isActive ? 'bg-primary/20' : 'bg-background'}`}>
          <Icon className={`w-6 h-6 ${isActive ? 'text-primary' : sound.color}`} />
        </div>
        <span className="text-xs font-medium">{sound.name}</span>
        {isActive && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="absolute -bottom-1 left-1/2 -translate-x-1/2"
          >
            <div className="flex gap-0.5">
              {[...Array(3)].map((_, i) => (
                <motion.div
                  key={i}
                  animate={{ height: [4, 12, 4] }}
                  transition={{ duration: 0.5, repeat: Infinity, delay: i * 0.1 }}
                  className="w-1 bg-primary rounded-full"
                />
              ))}
            </div>
          </motion.div>
        )}
      </motion.button>
    );
  };

  return (
    <div className="relative" data-testid="ambient-sound-control">
      {/* Toggle Button */}
      <Button
        variant={activeSound ? "default" : "ghost"}
        size="sm"
        onClick={() => setIsOpen(!isOpen)}
        className="rounded-full gap-2"
      >
        {activeSound ? (
          <>
            {(() => {
              const Icon = AMBIENT_SOUNDS[activeSound].icon;
              return <Icon className="w-4 h-4" />;
            })()}
            <span className="hidden sm:inline">{AMBIENT_SOUNDS[activeSound].name}</span>
          </>
        ) : (
          <>
            <FiMusic className="w-4 h-4" />
            <span className="hidden sm:inline">Ambient</span>
          </>
        )}
      </Button>

      {/* Sound Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            className="absolute top-full right-0 mt-2 p-4 bg-background/95 backdrop-blur-xl rounded-2xl shadow-2xl border w-72 z-[100]"
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
              <div>
                <h4 className="font-semibold">Ambient Sounds</h4>
                <p className="text-xs text-muted-foreground">Enhance your reading</p>
              </div>
              {activeSound && (
                <Button variant="ghost" size="icon" onClick={toggleMute} className="rounded-full">
                  {isMuted ? <FiVolumeX className="w-4 h-4" /> : <FiVolume2 className="w-4 h-4" />}
                </Button>
              )}
            </div>

            {/* Recommended Section */}
            <div className="mb-4">
              <p className="text-xs text-muted-foreground mb-2 flex items-center gap-1">
                <span className="w-2 h-2 bg-yellow-400 rounded-full" />
                Recommended for {genre}
              </p>
              <div className="grid grid-cols-3 gap-2">
                {recommendedSounds.map(soundKey => (
                  <SoundButton key={soundKey} soundKey={soundKey} recommended />
                ))}
              </div>
            </div>

            {/* All Sounds */}
            <div>
              <p className="text-xs text-muted-foreground mb-2">All Sounds</p>
              <div className="grid grid-cols-4 gap-2">
                {Object.keys(AMBIENT_SOUNDS)
                  .filter(key => !recommendedSounds.includes(key))
                  .map(soundKey => (
                    <SoundButton key={soundKey} soundKey={soundKey} />
                  ))}
              </div>
            </div>

            {/* Volume Control */}
            {activeSound && (
              <div className="mt-4 pt-4 border-t">
                <div className="flex items-center gap-3">
                  <FiVolume2 className="w-4 h-4 text-muted-foreground" />
                  <Slider
                    value={volume}
                    onValueChange={setVolume}
                    max={100}
                    step={5}
                    className="flex-1"
                  />
                  <span className="text-xs text-muted-foreground w-8">{volume[0]}%</span>
                </div>
              </div>
            )}

            {/* Stop Button */}
            {activeSound && (
              <Button
                variant="outline"
                size="sm"
                onClick={stopSound}
                className="w-full mt-3 rounded-full"
              >
                Stop Sound
              </Button>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
