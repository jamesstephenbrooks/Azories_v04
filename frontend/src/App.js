import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "@/context/ThemeContext";
import { AuthProvider } from "@/context/AuthContext";
import { Toaster } from "@/components/ui/sonner";
import OnboardingTutorial, { useOnboarding } from "@/components/OnboardingTutorial";
import { OfflineIndicator } from "@/components/OfflineReading";
import Landing from "@/pages/Landing";
import Library from "@/pages/Library";
import BookReader from "@/pages/BookReader";
import Dashboard from "@/pages/Dashboard";
import BookEditor from "@/pages/BookEditor";
import MySeries from "@/pages/MySeries";
import Auth from "@/pages/Auth";
import AdminCMS from "@/pages/AdminCMS";
import UserProfile from "@/pages/UserProfile";
import ArtStudio from "@/pages/ArtStudio";
import ArtStudioExpert from "@/pages/ArtStudioExpert";
import ProStudio from "@/pages/ProStudio";
import ComingSoon from "@/pages/ComingSoon";
import "@/App.css";

function AppContent() {
  const { shouldShow, setShouldShow } = useOnboarding();
  
  return (
    <>
      <OfflineIndicator />
      {shouldShow && <OnboardingTutorial onComplete={() => setShouldShow(false)} />}
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/coming-soon" element={<ComingSoon />} />
        <Route path="/library" element={<Library />} />
        <Route path="/read/:bookId" element={<BookReader />} />
        <Route path="/auth" element={<Auth />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/series" element={<MySeries />} />
        <Route path="/editor/:bookId" element={<BookEditor />} />
        <Route path="/admin" element={<AdminCMS />} />
        <Route path="/profile" element={<UserProfile />} />
        <Route path="/profile/:userId" element={<UserProfile />} />
        <Route path="/art-studio" element={<ArtStudio />} />
        <Route path="/art-studio/expert" element={<ArtStudioExpert />} />
        <Route path="/pro-studio" element={<ProStudio />} />
      </Routes>
      <Toaster position="bottom-right" richColors />
    </>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <AppContent />
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
