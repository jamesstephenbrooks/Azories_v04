import React, { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { ThemeProvider } from "@/context/ThemeContext";
import { AuthProvider } from "@/context/AuthContext";
import { Toaster } from "@/components/ui/sonner";
import OnboardingTutorial, { useOnboarding } from "@/components/OnboardingTutorial";
import { OfflineIndicator } from "@/components/OfflineReading";
import CookieConsent from "@/components/CookieConsent";
import ProtectedRoute from "@/components/ProtectedRoute";
import { AZORA_ASSETS } from "@/components/AzoraMascot";
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
const AdminCMS = lazy(() => import("@/pages/AdminCMS"));
const AdminAnalytics = lazy(() => import("@/pages/AdminAnalytics"));
const AdminDashboard = lazy(() => import("@/pages/AdminDashboard"));
const UserProfile = lazy(() => import("@/pages/UserProfile"));
const ArtStudio = lazy(() => import("@/pages/ArtStudio"));
const ArtStudioExpert = lazy(() => import("@/pages/ArtStudioExpert"));
const ProStudio = lazy(() => import("@/pages/ProStudio"));
const ComingSoon = lazy(() => import("@/pages/ComingSoon"));
const Credits = lazy(() => import("@/pages/Credits"));
const PaymentSuccess = lazy(() => import("@/pages/PaymentSuccess"));
const Contact = lazy(() => import("@/pages/Contact"));
const NotFound = lazy(() => import("@/pages/NotFound"));

// Legal page with named exports
const TermsOfService = lazy(() => import("@/pages/Legal").then(m => ({ default: m.TermsOfService })));
const PrivacyPolicy = lazy(() => import("@/pages/Legal").then(m => ({ default: m.PrivacyPolicy })));

// Loading screen with Azora mascot and dragon spinner
function PageLoader() {
  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gradient-to-b from-purple-900/95 to-slate-900">
      <img 
        src={AZORA_ASSETS.waving}
        alt="Azora welcomes you"
        className="w-32 h-40 object-contain mb-6 animate-bounce-slow"
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
  const isBookReaderPage = location.pathname.startsWith("/read/");

  return (
    <ErrorBoundary>
      <OfflineIndicator />
      {shouldShow && !isAdminPage && !isBookReaderPage && (
        <OnboardingTutorial onComplete={completeOnboarding} />
      )}
      <Suspense fallback={<PageLoader />}>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<Landing />} />
          <Route path="/coming-soon" element={<ComingSoon />} />
          <Route path="/library" element={<Library />} />
          <Route path="/read/:bookId" element={<BookReader />} />
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
          <Route path="/art-studio" element={<ProtectedRoute><ArtStudio /></ProtectedRoute>} />
          <Route path="/art-studio/expert" element={<ProtectedRoute><ArtStudioExpert /></ProtectedRoute>} />
          <Route path="/pro-studio" element={<ProtectedRoute><ProStudio /></ProtectedRoute>} />
          <Route path="/credits" element={<ProtectedRoute><Credits /></ProtectedRoute>} />
          <Route path="/payment-success" element={<ProtectedRoute><PaymentSuccess /></ProtectedRoute>} />

          {/* Admin only — must be logged in AND is_admin = true */}
          <Route path="/admin" element={<ProtectedRoute requireAdmin><AdminDashboard /></ProtectedRoute>} />
          <Route path="/admin/cms" element={<ProtectedRoute requireAdmin><AdminCMS /></ProtectedRoute>} />
          <Route path="/admin/analytics" element={<ProtectedRoute requireAdmin><AdminAnalytics /></ProtectedRoute>} />

          {/* 404 catch-all — must be last */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>
      <Toaster position="bottom-right" richColors />
      <CookieConsent />
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
