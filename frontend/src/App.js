import React, { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route, useLocation, Navigate } from "react-router-dom";
import { ThemeProvider } from "@/context/ThemeContext";
import { AuthProvider } from "@/context/AuthContext";
import { Toaster } from "@/components/ui/sonner";
import OnboardingTutorial, { useOnboarding } from "@/components/OnboardingTutorial";
import { OfflineIndicator } from "@/components/OfflineReading";
import CookieConsent from "@/components/CookieConsent";
import ProtectedRoute from "@/components/ProtectedRoute";
import InstallPrompt from "@/components/InstallPrompt";
import { AZORA_ASSETS } from "@/components/AzoraMascot";
import { usePageTracking } from "@/hooks/useAnalytics";
import "@/App.css";

// Lazy load all pages — they only download when navigated to
const Landing = lazy(() => import("@/pages/Landing"));
const Library = lazy(() => import("@/pages/Library"));
const BookReader = lazy(() => import("@/pages/BookReader"));
const Dashboard = lazy(() => import("@/pages/Dashboard"));
const BookEditor = lazy(() => import("@/pages/BookEditor"));
const MySeries = lazy(() => import("@/pages/MySeries"));
const Auth = lazy(() => import("@/pages/Auth"));
const ResetPassword = lazy(() => import("@/pages/ResetPassword"));
const AdminDashboard = lazy(() => import("@/pages/AdminDashboard"));
const UserProfile = lazy(() => import("@/pages/UserProfile"));
const Creators = lazy(() => import("@/pages/ArtStudio"));
const CreatorsExpert = lazy(() => import("@/pages/ArtStudioExpert"));
const ProStudio = lazy(() => import("@/pages/ProStudio"));
const StoryCreator = lazy(() => import("@/pages/StoryCreator"));
const ComingSoon = lazy(() => import("@/pages/ComingSoon"));
const Credits = lazy(() => import("@/pages/Credits"));
const PaymentSuccess = lazy(() => import("@/pages/PaymentSuccess"));
const PrintSuccess = lazy(() => import("@/pages/PrintSuccess"));
const Contact = lazy(() => import("@/pages/Contact"));
const NotFound = lazy(() => import("@/pages/NotFound"));
const PrintOrdersCMS = lazy(() => import("@/pages/admin/PrintOrdersCMS"));

// Legal page with named exports
const TermsOfService = lazy(() => import("@/pages/Legal").then(m => ({ default: m.TermsOfService })));
const PrivacyPolicy = lazy(() => import("@/pages/Legal").then(m => ({ default: m.PrivacyPolicy })));

// Loading screen with Azora mascot and dragon spinner
function PageLoader() {
  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gradient-to-b from-purple-900/95 to-slate-900">
      <img
        src={AZORA_ASSETS.pointing}
        alt="Azora welcomes you"
        className="w-36 h-44 object-contain mb-6"
        style={{ animation: 'float 2s ease-in-out infinite' }}
      />
      <h2 className="text-xl font-bold text-white mb-3">Welcome to Azories</h2>
      <p className="text-white/60 text-sm mb-6">Loading magical adventures...</p>
      <img
        src={AZORA_ASSETS.dragonIcon}
        alt="Loading"
        className="w-12 h-12 object-contain rounded-full"
        style={{ animation: 'spin-slow 2s linear infinite, pulse 1s ease-in-out infinite' }}
      />
    </div>
  );
}

// Error boundary — catches crashes and shows a fallback instead of blank screen
class ErrorBoundary extends React.Component {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center h-screen gap-4 text-center p-8 bg-gray-900">
          <h2 className="text-2xl font-semibold text-white">Something went wrong</h2>
          <p className="text-gray-400">An unexpected error occurred.</p>
          <button
            className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
            onClick={() => window.location.reload()}
          >
            Reload Page
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

function AppContent() {
  const { shouldShow, completeOnboarding } = useOnboarding();
  const location = useLocation();
  const isAdminPage = location.pathname.startsWith("/admin");
  const isBookReaderPage = location.pathname.startsWith("/read/") || location.pathname.startsWith("/book/");
  // Only show onboarding on library/dashboard for logged-in users, not on landing or public pages
  const isOnboardingPage = location.pathname === "/library" || location.pathname === "/dashboard";

  // Track page views automatically
  usePageTracking();

  return (
    <ErrorBoundary>
      <OfflineIndicator />
      {shouldShow && isOnboardingPage && !isAdminPage && !isBookReaderPage && (
        <OnboardingTutorial onComplete={completeOnboarding} />
      )}
      <Suspense fallback={<PageLoader />}>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<Landing />} />
          <Route path="/coming-soon" element={<ComingSoon />} />
          <Route path="/library" element={<Library />} />
          <Route path="/read/:bookId" element={<BookReader />} />
          <Route path="/book/:bookId" element={<BookReader />} />
          <Route path="/auth" element={<Auth />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/terms" element={<TermsOfService />} />
          <Route path="/privacy" element={<PrivacyPolicy />} />
          <Route path="/contact" element={<Contact />} />
          <Route path="/profile/:userId" element={<UserProfile />} />

          {/* Protected — must be logged in */}
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/series" element={<ProtectedRoute><MySeries /></ProtectedRoute>} />
          <Route path="/editor/:bookId" element={<ProtectedRoute><BookEditor /></ProtectedRoute>} />
          <Route path="/profile" element={<ProtectedRoute><UserProfile /></ProtectedRoute>} />
          <Route path="/creators" element={<ProtectedRoute><Creators /></ProtectedRoute>} />
          <Route path="/creators/expert" element={<ProtectedRoute><CreatorsExpert /></ProtectedRoute>} />
          <Route path="/ai-stories" element={<ProtectedRoute><StoryCreator /></ProtectedRoute>} />
          {/* Legacy routes - redirect to new paths */}
          <Route path="/art-studio" element={<Navigate to="/creators" replace />} />
          <Route path="/art-studio/expert" element={<Navigate to="/creators/expert" replace />} />
          <Route path="/pro-studio" element={<ProtectedRoute><ProStudio /></ProtectedRoute>} />
          <Route path="/credits" element={<ProtectedRoute><Credits /></ProtectedRoute>} />
          <Route path="/payment-success" element={<ProtectedRoute><PaymentSuccess /></ProtectedRoute>} />
          <Route path="/print-success" element={<ProtectedRoute><PrintSuccess /></ProtectedRoute>} />

          {/* Admin routes — AdminDashboard handles its own authentication */}
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/admin/print-orders" element={<ProtectedRoute><PrintOrdersCMS /></ProtectedRoute>} />

          {/* 404 catch-all — must be last */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>
      <Toaster position="bottom-right" richColors />
      <CookieConsent />
      <InstallPrompt />
    </ErrorBoundary>
  );
}

function App() {
  return (
    <ThemeProvider>
      {/* BrowserRouter wraps AuthProvider so AuthContext can use useNavigate */}
      <BrowserRouter>
        <AuthProvider>
          <AppContent />
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
