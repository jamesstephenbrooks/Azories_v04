/**
 * BonusPages - Pre-designed pages for Print on Demand books
 * 
 * These pages are added to printed books to enhance the experience:
 * - Welcome/Title page
 * - Dedication page (personalized)
 * - The End page
 * - Thank You page  
 * - About Azories page
 * - Certificate of Achievement
 * - Meet Azora page
 */

// Azora mascot images for bonus pages
export const BONUS_PAGE_IMAGES = {
  // Girl pointing with dragon and glowing magic book - welcoming, exciting
  welcome: 'https://customer-assets.emergentagent.com/job_5f7e2b9e-d2a4-4bf3-b6c6-aac66cbef904/artifacts/60k2xrwp_Azora%20Mascot%20Main.jpg',
  
  // Sitting girl reading with dragon on head - personal, cozy
  dedication: 'https://customer-assets.emergentagent.com/job_5f7e2b9e-d2a4-4bf3-b6c6-aac66cbef904/artifacts/ve63p3ok_Azora%20Mascot%202.jpg',
  
  // Running girl with dragon and book - adventure continues
  theEnd: 'https://customer-assets.emergentagent.com/job_5f7e2b9e-d2a4-4bf3-b6c6-aac66cbef904/artifacts/k0b04d29_Azora%20Mascot%201.jpg',
  
  // Waving Azora - friendly goodbye
  thankYou: 'https://res.cloudinary.com/dlbmjqmoy/image/upload/e_background_removal/v1772279875/azories/mascot/azora_waving_hello.png',
  
  // Girl with dragon and book - scholarly, informative
  aboutAzories: 'https://customer-assets.emergentagent.com/job_5f7e2b9e-d2a4-4bf3-b6c6-aac66cbef904/artifacts/dlulgnzy_Azora_Mascot.jpg',
  
  // Library Azora in traditional dress - achievement, formal
  certificate: 'https://customer-assets.emergentagent.com/job_5f7e2b9e-d2a4-4bf3-b6c6-aac66cbef904/artifacts/e45x5iez_azora%20library.png',
  
  // Library Azora shy pose - friendly intro
  meetAzora: 'https://customer-assets.emergentagent.com/job_5f7e2b9e-d2a4-4bf3-b6c6-aac66cbef904/artifacts/o1xvfgto_azora%20librbary%201.png',
};

// Page dimensions for 8x8 inch photobook (in pixels at 300 DPI)
export const PAGE_SIZE = {
  width: 2400,  // 8 inches * 300 DPI
  height: 2400, // 8 inches * 300 DPI
};

/**
 * Welcome Page - First bonus page
 * Shows Azora welcoming the reader to their special story
 */
export const WelcomePage = ({ bookTitle, childName }) => (
  <div className="bonus-page welcome-page w-full h-full bg-gradient-to-br from-purple-50 via-white to-pink-50 flex flex-col items-center justify-center p-4 sm:p-8 relative overflow-hidden">
    {/* Decorative corner flourishes - smaller for preview */}
    <div className="absolute top-2 left-2 sm:top-4 sm:left-4 w-10 h-10 sm:w-20 sm:h-20 border-t-2 sm:border-t-4 border-l-2 sm:border-l-4 border-purple-300 rounded-tl-lg sm:rounded-tl-xl opacity-60" />
    <div className="absolute top-2 right-2 sm:top-4 sm:right-4 w-10 h-10 sm:w-20 sm:h-20 border-t-2 sm:border-t-4 border-r-2 sm:border-r-4 border-purple-300 rounded-tr-lg sm:rounded-tr-xl opacity-60" />
    <div className="absolute bottom-2 left-2 sm:bottom-4 sm:left-4 w-10 h-10 sm:w-20 sm:h-20 border-b-2 sm:border-b-4 border-l-2 sm:border-l-4 border-purple-300 rounded-bl-lg sm:rounded-bl-xl opacity-60" />
    <div className="absolute bottom-2 right-2 sm:bottom-4 sm:right-4 w-10 h-10 sm:w-20 sm:h-20 border-b-2 sm:border-b-4 border-r-2 sm:border-r-4 border-purple-300 rounded-br-lg sm:rounded-br-xl opacity-60" />
    
    {/* Sparkle decorations - smaller */}
    <div className="absolute top-6 right-8 sm:top-12 sm:right-16 text-yellow-400 text-lg sm:text-2xl">✦</div>
    <div className="absolute top-10 left-10 sm:top-20 sm:left-20 text-purple-400 text-base sm:text-xl">✦</div>
    <div className="absolute bottom-12 right-12 sm:bottom-24 sm:right-24 text-pink-400 text-sm sm:text-lg">✦</div>
    
    {/* Main content - scaled for preview with proper text containment */}
    <div className="text-center mb-3 sm:mb-6 px-4 sm:px-8 w-full max-w-[90%]">
      <p className="text-purple-600 text-[10px] sm:text-lg font-medium tracking-widest uppercase mb-1 sm:mb-2">A Magical Story</p>
      <h1 className="text-base sm:text-3xl md:text-4xl font-bold text-gray-800 mb-1 sm:mb-2 font-serif leading-tight text-center break-words" style={{ wordBreak: 'break-word', overflowWrap: 'break-word' }}>{bookTitle || 'Your Story'}</h1>
      <p className="text-purple-500 text-xs sm:text-xl">Created especially for</p>
      <p className="text-sm sm:text-2xl font-bold text-purple-700 mt-0.5 sm:mt-1 break-words">{childName || 'You'}</p>
    </div>
    
    {/* Image in decorative frame - smaller for preview */}
    <div className="relative flex-shrink-0">
      <div className="w-24 h-24 sm:w-48 sm:h-48 rounded-full bg-gradient-to-br from-purple-200 to-pink-200 p-1 sm:p-2 shadow-xl">
        <div className="w-full h-full rounded-full overflow-hidden bg-white">
          <img 
            src={BONUS_PAGE_IMAGES.welcome}
            alt="Azora welcomes you"
            className="w-full h-full object-cover object-top"
          />
        </div>
      </div>
      {/* Sparkle accent */}
      <div className="absolute -top-1 -right-1 sm:-top-2 sm:-right-2 text-yellow-500 text-xl sm:text-3xl">✨</div>
    </div>
    
    {/* Footer text */}
    <p className="mt-3 sm:mt-6 text-gray-500 text-[10px] sm:text-sm">Made with love on Azories.com</p>
  </div>
);

/**
 * Dedication Page - Personal message page
 */
export const DedicationPage = ({ childName, dedicationMessage }) => (
  <div className="bonus-page dedication-page w-full h-full bg-gradient-to-b from-amber-50 via-white to-amber-50 flex flex-col items-center justify-center p-4 sm:p-8 relative overflow-hidden">
    {/* Decorative book border - smaller for preview */}
    <div className="absolute inset-3 sm:inset-6 border sm:border-2 border-amber-200 rounded-lg" />
    <div className="absolute inset-4 sm:inset-8 border border-amber-100 rounded-lg" />
    
    {/* Header ornament */}
    <div className="flex items-center gap-2 sm:gap-4 mb-4 sm:mb-8">
      <div className="h-px w-8 sm:w-16 bg-gradient-to-r from-transparent to-amber-400" />
      <span className="text-amber-500 text-lg sm:text-2xl">❦</span>
      <div className="h-px w-8 sm:w-16 bg-gradient-to-l from-transparent to-amber-400" />
    </div>
    
    <h2 className="text-base sm:text-2xl font-serif text-gray-600 mb-1 sm:mb-2">This book belongs to</h2>
    <h1 className="text-xl sm:text-4xl font-bold text-amber-700 mb-4 sm:mb-8 font-serif truncate max-w-[90%]">{childName || '________________'}</h1>
    
    {/* Image - smaller for preview */}
    <div className="w-24 h-24 sm:w-48 sm:h-48 rounded-xl sm:rounded-2xl overflow-hidden shadow-lg mb-4 sm:mb-8 border-2 sm:border-4 border-white flex-shrink-0">
      <img 
        src={BONUS_PAGE_IMAGES.dedication}
        alt="Azora reading"
        className="w-full h-full object-cover"
      />
    </div>
    
    {/* Dedication message */}
    <div className="max-w-[90%] sm:max-w-md text-center px-2">
      <p className="text-gray-600 text-xs sm:text-lg italic leading-snug sm:leading-relaxed line-clamp-3">
        {dedicationMessage || '"May every page bring you joy, and every story spark your imagination."'}
      </p>
    </div>
    
    {/* Footer ornament */}
    <div className="flex items-center gap-2 sm:gap-4 mt-4 sm:mt-8">
      <div className="h-px w-6 sm:w-12 bg-gradient-to-r from-transparent to-amber-400" />
      <span className="text-amber-400 text-sm sm:text-base">✦</span>
      <div className="h-px w-6 sm:w-12 bg-gradient-to-l from-transparent to-amber-400" />
    </div>
  </div>
);

/**
 * The End Page - Story conclusion
 */
export const TheEndPage = ({ bookTitle }) => (
  <div className="bonus-page the-end-page w-full h-full bg-gradient-to-br from-sky-50 via-white to-purple-50 flex flex-col items-center justify-center p-4 sm:p-8 relative overflow-hidden">
    {/* Background decorative circles - smaller */}
    <div className="absolute -top-10 -right-10 sm:-top-20 sm:-right-20 w-32 h-32 sm:w-64 sm:h-64 rounded-full bg-purple-100/30" />
    <div className="absolute -bottom-8 -left-8 sm:-bottom-16 sm:-left-16 w-24 h-24 sm:w-48 sm:h-48 rounded-full bg-sky-100/30" />
    
    {/* Main heading */}
    <div className="text-center mb-4 sm:mb-8">
      <h1 className="text-3xl sm:text-6xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-pink-600 font-serif">
        The End
      </h1>
      <div className="flex items-center justify-center gap-2 sm:gap-3 mt-2 sm:mt-4">
        <span className="text-purple-400 text-sm sm:text-base">✦</span>
        <span className="text-pink-400 text-sm sm:text-base">✦</span>
        <span className="text-purple-400 text-sm sm:text-base">✦</span>
      </div>
    </div>
    
    {/* Image - smaller for preview */}
    <div className="relative mb-4 sm:mb-8 flex-shrink-0">
      <div className="w-32 h-32 sm:w-64 sm:h-64 rounded-2xl sm:rounded-3xl overflow-hidden shadow-2xl border-2 sm:border-4 border-white">
        <img 
          src={BONUS_PAGE_IMAGES.theEnd}
          alt="Adventure continues"
          className="w-full h-full object-cover"
        />
      </div>
      {/* Trail sparkles */}
      <div className="absolute -left-2 top-1/2 sm:-left-4 text-yellow-400 text-base sm:text-xl">✨</div>
      <div className="absolute -left-4 top-1/3 sm:-left-8 text-purple-400 text-xs sm:text-sm">✦</div>
    </div>
    
    {/* Closing message */}
    <p className="text-sm sm:text-xl text-gray-600 text-center max-w-[90%] sm:max-w-sm leading-snug">
      But remember, every ending is just the beginning of a new adventure!
    </p>
    
    {/* Book title reminder */}
    <p className="mt-3 sm:mt-6 text-purple-500 text-xs sm:text-sm font-medium truncate max-w-[90%]">{bookTitle}</p>
  </div>
);

/**
 * Thank You Page - Goodbye message
 */
export const ThankYouPage = ({ childName }) => (
  <div className="bonus-page thank-you-page w-full h-full bg-gradient-to-b from-pink-50 via-white to-purple-50 flex flex-col items-center justify-center p-4 sm:p-8 relative overflow-hidden">
    {/* Heart decorations - smaller */}
    <div className="absolute top-6 left-6 sm:top-12 sm:left-12 text-pink-300 text-lg sm:text-2xl">♥</div>
    <div className="absolute top-10 right-8 sm:top-20 sm:right-16 text-purple-300 text-base sm:text-xl">♥</div>
    <div className="absolute bottom-8 left-10 sm:bottom-16 sm:left-20 text-pink-200 text-sm sm:text-lg">♥</div>
    
    <h1 className="text-2xl sm:text-4xl font-bold text-purple-700 mb-1 sm:mb-2 font-serif">Thank You</h1>
    <h2 className="text-lg sm:text-2xl text-pink-600 mb-4 sm:mb-8">for reading!</h2>
    
    {/* Waving Azora - smaller for preview */}
    <div className="relative mb-4 sm:mb-8 flex-shrink-0">
      <div className="w-28 h-28 sm:w-52 sm:h-52 rounded-full bg-gradient-to-br from-pink-200 to-purple-200 p-1 sm:p-1.5 shadow-xl">
        <div className="w-full h-full rounded-full overflow-hidden bg-white flex items-center justify-center">
          <img 
            src={BONUS_PAGE_IMAGES.thankYou}
            alt="Azora waving goodbye"
            className="w-4/5 h-4/5 object-contain"
          />
        </div>
      </div>
      {/* Wave effect */}
      <div className="absolute -right-1 top-4 sm:-right-2 sm:top-8 text-lg sm:text-2xl">👋</div>
    </div>
    
    <p className="text-sm sm:text-xl text-gray-600 text-center max-w-[90%] sm:max-w-md mb-2 sm:mb-4">
      {childName ? `${childName}, you're` : "You're"} an amazing reader!
    </p>
    <p className="text-xs sm:text-lg text-purple-500 text-center">
      Come back soon for more adventures!
    </p>
    
    {/* Azories branding */}
    <div className="mt-4 sm:mt-8 flex items-center gap-1 sm:gap-2 text-gray-400 text-[10px] sm:text-sm">
      <span>Made with</span>
      <span className="text-pink-500">♥</span>
      <span>on Azories.com</span>
    </div>
  </div>
);

/**
 * About Azories Page - Platform information
 */
export const AboutAzoriesPage = () => (
  <div className="bonus-page about-page w-full h-full bg-gradient-to-br from-purple-600 via-purple-700 to-indigo-800 flex flex-col items-center justify-start pt-6 sm:pt-10 p-4 sm:p-8 text-white relative overflow-hidden">
    {/* Background pattern - smaller */}
    <div className="absolute inset-0 opacity-10">
      <div className="absolute top-5 left-5 sm:top-10 sm:left-10 text-3xl sm:text-6xl">✦</div>
      <div className="absolute top-16 right-10 sm:top-32 sm:right-20 text-2xl sm:text-4xl">✦</div>
      <div className="absolute bottom-10 left-12 sm:bottom-20 sm:left-24 text-2xl sm:text-5xl">✦</div>
      <div className="absolute bottom-20 right-8 sm:bottom-40 sm:right-16 text-xl sm:text-3xl">✦</div>
    </div>
    
    <h1 className="text-lg sm:text-2xl font-bold mb-0.5 sm:mb-1">About</h1>
    <h2 className="text-2xl sm:text-4xl font-bold mb-3 sm:mb-6 font-serif tracking-wide">Azories</h2>
    
    {/* Image in frame - smaller */}
    <div className="w-24 h-24 sm:w-40 sm:h-40 rounded-xl sm:rounded-2xl overflow-hidden shadow-2xl border-2 sm:border-4 border-white/20 mb-3 sm:mb-6 flex-shrink-0">
      <img 
        src={BONUS_PAGE_IMAGES.aboutAzories}
        alt="Azora and her dragon"
        className="w-full h-full object-cover"
      />
    </div>
    
    <p className="text-center text-[10px] sm:text-base leading-snug sm:leading-relaxed max-w-[90%] sm:max-w-sm mb-2 sm:mb-4 text-purple-100">
      Azories creates personalized AI-powered stories that bring imagination to life. 
      Every story is unique, just like you!
    </p>
    
    <div className="flex items-center gap-2 sm:gap-4 text-purple-200 text-[8px] sm:text-xs">
      <span>✦ AI-Powered</span>
      <span>✦ Personalized</span>
      <span>✦ Magical</span>
    </div>
    
    <p className="mt-2 sm:mt-4 text-purple-300 text-[8px] sm:text-xs">www.azories.com</p>
  </div>
);

/**
 * Certificate Page - Achievement certificate
 */
export const CertificatePage = ({ childName, bookTitle, completionDate }) => (
  <div className="bonus-page certificate-page w-full h-full bg-gradient-to-b from-amber-50 to-yellow-50 flex flex-col items-center justify-center p-3 sm:p-6 relative overflow-hidden">
    {/* Ornate border - smaller for preview */}
    <div className="absolute inset-2 sm:inset-4 border-2 sm:border-4 border-amber-400 rounded-lg" />
    <div className="absolute inset-3 sm:inset-6 border sm:border-2 border-amber-300 rounded-lg" />
    <div className="absolute inset-4 sm:inset-8 border border-amber-200 rounded-lg" />
    
    {/* Corner decorations - smaller */}
    <div className="absolute top-4 left-4 sm:top-8 sm:left-8 text-amber-500 text-xl sm:text-3xl">❧</div>
    <div className="absolute top-4 right-4 sm:top-8 sm:right-8 text-amber-500 text-xl sm:text-3xl transform scale-x-[-1]">❧</div>
    <div className="absolute bottom-4 left-4 sm:bottom-8 sm:left-8 text-amber-500 text-xl sm:text-3xl transform scale-y-[-1]">❧</div>
    <div className="absolute bottom-4 right-4 sm:bottom-8 sm:right-8 text-amber-500 text-xl sm:text-3xl transform scale-[-1]">❧</div>
    
    {/* Certificate content */}
    <div className="text-center z-10">
      <p className="text-amber-600 text-[8px] sm:text-sm tracking-[0.2em] sm:tracking-[0.3em] uppercase mb-1 sm:mb-2">Certificate of</p>
      <h1 className="text-2xl sm:text-4xl font-bold text-amber-800 font-serif mb-3 sm:mb-6">Achievement</h1>
      
      <p className="text-gray-600 text-xs sm:text-lg mb-1 sm:mb-2">This certifies that</p>
      <h2 className="text-lg sm:text-3xl font-bold text-amber-700 font-serif mb-2 sm:mb-4 border-b sm:border-b-2 border-amber-300 pb-1 sm:pb-2 px-4 sm:px-8 truncate max-w-[90%] mx-auto">
        {childName || '________________'}
      </h2>
      
      <p className="text-gray-600 text-[10px] sm:text-base mb-0.5 sm:mb-1">has successfully completed reading</p>
      <p className="text-sm sm:text-xl font-semibold text-purple-700 mb-3 sm:mb-6 truncate max-w-[85%] mx-auto">"{bookTitle || 'This Wonderful Story'}"</p>
      
      {/* Small image - smaller for preview */}
      <div className="w-16 h-16 sm:w-24 sm:h-24 mx-auto rounded-full overflow-hidden border-2 sm:border-4 border-amber-300 shadow-lg mb-2 sm:mb-4 flex-shrink-0">
        <img 
          src={BONUS_PAGE_IMAGES.certificate}
          alt="Azora"
          className="w-full h-full object-cover object-top"
        />
      </div>
      
      {/* Date and seal */}
      <p className="text-gray-500 text-[10px] sm:text-sm mb-2 sm:mb-4">
        {completionDate || new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
      </p>
      
      {/* Star rating */}
      <div className="flex justify-center gap-0.5 sm:gap-1 text-amber-500 text-lg sm:text-2xl">
        <span>★</span>
        <span>★</span>
        <span>★</span>
        <span>★</span>
        <span>★</span>
      </div>
    </div>
  </div>
);

/**
 * Meet Azora Page - Character introduction
 */
export const MeetAzoraPage = () => (
  <div className="bonus-page meet-azora-page w-full h-full bg-gradient-to-br from-rose-50 via-white to-purple-50 flex flex-col items-center justify-center p-4 sm:p-8 relative overflow-hidden">
    {/* Decorative elements - smaller */}
    <div className="absolute top-4 sm:top-8 left-1/2 transform -translate-x-1/2 flex items-center gap-2 sm:gap-3">
      <div className="h-px w-10 sm:w-20 bg-gradient-to-r from-transparent to-rose-300" />
      <span className="text-rose-400 text-base sm:text-xl">✦</span>
      <div className="h-px w-10 sm:w-20 bg-gradient-to-l from-transparent to-rose-300" />
    </div>
    
    <h1 className="text-xl sm:text-3xl font-bold text-purple-700 mb-1 sm:mb-2 font-serif">Meet</h1>
    <h2 className="text-3xl sm:text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-rose-600 mb-3 sm:mb-6 font-serif">
      Azora
    </h2>
    
    {/* Image in fancy frame - smaller */}
    <div className="relative mb-3 sm:mb-6 flex-shrink-0">
      <div className="w-32 h-32 sm:w-56 sm:h-56 rounded-xl sm:rounded-2xl bg-gradient-to-br from-rose-200 to-purple-200 p-0.5 sm:p-1 shadow-xl">
        <div className="w-full h-full rounded-lg sm:rounded-xl overflow-hidden bg-white">
          <img 
            src={BONUS_PAGE_IMAGES.meetAzora}
            alt="Meet Azora"
            className="w-full h-full object-cover object-top"
          />
        </div>
      </div>
      {/* Sparkle accents */}
      <div className="absolute -top-1 -right-1 sm:-top-3 sm:-right-3 text-yellow-500 text-lg sm:text-2xl">✨</div>
      <div className="absolute -bottom-1 -left-1 sm:-bottom-2 sm:-left-2 text-purple-400 text-base sm:text-xl">✦</div>
    </div>
    
    {/* Character description */}
    <p className="text-center text-gray-600 leading-snug sm:leading-relaxed max-w-[90%] sm:max-w-sm mb-2 sm:mb-4 text-xs sm:text-base">
      Hi! I'm Azora, your magical story guide. I love helping kids discover amazing adventures 
      through the power of imagination and reading!
    </p>
    
    <p className="text-purple-500 text-[10px] sm:text-sm font-medium">
      Ready for your next adventure?
    </p>
    
    {/* Footer */}
    <div className="absolute bottom-4 sm:bottom-8 left-1/2 transform -translate-x-1/2 flex items-center gap-2 sm:gap-3">
      <div className="h-px w-10 sm:w-20 bg-gradient-to-r from-transparent to-purple-300" />
      <span className="text-purple-400 text-base sm:text-xl">♥</span>
      <div className="h-px w-10 sm:w-20 bg-gradient-to-l from-transparent to-purple-300" />
    </div>
  </div>
);

/**
 * Get all bonus pages in order for a printed book
 */
export const getBonusPages = ({ bookTitle, childName, dedicationMessage, completionDate }) => [
  {
    id: 'welcome',
    component: WelcomePage,
    props: { bookTitle, childName },
    position: 'start', // Before story content
  },
  {
    id: 'dedication',
    component: DedicationPage,
    props: { childName, dedicationMessage },
    position: 'start',
  },
  {
    id: 'theEnd',
    component: TheEndPage,
    props: { bookTitle },
    position: 'end', // After story content
  },
  {
    id: 'thankYou',
    component: ThankYouPage,
    props: { childName },
    position: 'end',
  },
  {
    id: 'certificate',
    component: CertificatePage,
    props: { childName, bookTitle, completionDate },
    position: 'end',
  },
  {
    id: 'aboutAzories',
    component: AboutAzoriesPage,
    props: {},
    position: 'end',
  },
  {
    id: 'meetAzora',
    component: MeetAzoraPage,
    props: {},
    position: 'end',
  },
];

export default {
  BONUS_PAGE_IMAGES,
  WelcomePage,
  DedicationPage,
  TheEndPage,
  ThankYouPage,
  AboutAzoriesPage,
  CertificatePage,
  MeetAzoraPage,
  getBonusPages,
};
