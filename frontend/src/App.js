import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "@/context/ThemeContext";
import { AuthProvider } from "@/context/AuthContext";
import { Toaster } from "@/components/ui/sonner";
import Landing from "@/pages/Landing";
import Library from "@/pages/Library";
import BookReader from "@/pages/BookReader";
import Dashboard from "@/pages/Dashboard";
import BookEditor from "@/pages/BookEditor";
import Auth from "@/pages/Auth";
import AdminCMS from "@/pages/AdminCMS";
import UserProfile from "@/pages/UserProfile";
import "@/App.css";

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/library" element={<Library />} />
            <Route path="/read/:bookId" element={<BookReader />} />
            <Route path="/auth" element={<Auth />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/editor/:bookId" element={<BookEditor />} />
            <Route path="/admin" element={<AdminCMS />} />
            <Route path="/profile" element={<UserProfile />} />
            <Route path="/profile/:userId" element={<UserProfile />} />
          </Routes>
        </BrowserRouter>
        <Toaster position="bottom-right" richColors />
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
