import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { toast } from 'sonner';
import { 
  FiShield, FiBook, FiCheck, FiX, FiAlertTriangle, 
  FiEye, FiEyeOff, FiClock, FiUser, FiArrowLeft, FiLogIn, FiSearch, FiRefreshCw,
  FiUsers, FiBarChart2, FiStar, FiAward, FiTrash2, FiLock, FiLogOut, FiDatabase, FiFilter, FiImage,
  FiChevronLeft, FiChevronRight, FiSettings, FiKey, FiSave, FiCalendar, FiTrendingUp, FiPackage, FiDollarSign, FiTruck
} from 'react-icons/fi';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, AreaChart, Area
} from 'recharts';

const API = process.env.REACT_APP_BACKEND_URL;

// Available genres and age ratings
const GENRES = ['All', 'Fantasy', 'Adventure', 'Mystery', 'Science Fiction', 'Fairy Tales', 'Educational', 'Animals', 'Humor', 'Action', 'Other'];
const AGE_RATINGS = ['All', 'All Ages', '5+', '8+', '12+', '16+'];

// Settings Component for FAL Key Management
function SettingsFalKey() {
  const [falKey, setFalKey] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState(null);

  const handleSaveKey = async () => {
    if (!falKey.trim()) {
      toast.error('Please enter a FAL key');
      return;
    }
    
    setSaving(true);
    try {
      const res = await axios.post(`${API}/api/admin/update-fal-key`, 
        { fal_key: falKey },
        { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }}
      );
      
      if (res.data.success) {
        toast.success('FAL key updated successfully!');
        setStatus({ valid: true, preview: res.data.key_preview });
        setFalKey('');
      } else {
        toast.error(res.data.error || 'Failed to update key');
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update key');
    } finally {
      setSaving(false);
    }
  };

  const handleValidateKey = async () => {
    try {
      const res = await axios.post(`${API}/api/admin/validate-fal-key`, {}, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      
      if (res.data.status?.valid) {
        toast.success('FAL key is valid and working!');
        setStatus({ valid: true });
      } else {
        toast.error(res.data.status?.error_message || 'Key validation failed');
        setStatus({ valid: false, error: res.data.status?.error_message });
      }
    } catch (err) {
      toast.error('Failed to validate key');
    }
  };

  return (
    <div className="bg-white/5 rounded-xl p-6 border border-white/10">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-full bg-purple-600/20 flex items-center justify-center">
          <FiKey className="w-5 h-5 text-purple-400" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-white">FAL.AI API Key</h3>
          <p className="text-sm text-white/60">Used for image generation in Pro Studio</p>
        </div>
      </div>
      
      {status && (
        <div className={`mb-4 p-3 rounded-lg ${status.valid ? 'bg-green-500/10 border border-green-500/20' : 'bg-red-500/10 border border-red-500/20'}`}>
          <p className={`text-sm ${status.valid ? 'text-green-400' : 'text-red-400'}`}>
            {status.valid ? '✓ Current key is valid' : `✗ ${status.error || 'Key is invalid'}`}
            {status.preview && <span className="ml-2 text-white/40">({status.preview})</span>}
          </p>
        </div>
      )}
      
      <div className="space-y-4">
        <div className="relative">
          <Input
            type={showKey ? 'text' : 'password'}
            placeholder="Enter new FAL key (format: key_id:key_secret)"
            value={falKey}
            onChange={(e) => setFalKey(e.target.value)}
            className="bg-white/5 border-white/10 text-white pr-10"
          />
          <button
            type="button"
            onClick={() => setShowKey(!showKey)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/60"
          >
            {showKey ? <FiEyeOff className="w-4 h-4" /> : <FiEye className="w-4 h-4" />}
          </button>
        </div>
        
        <div className="flex gap-3">
          <Button
            onClick={handleSaveKey}
            disabled={saving || !falKey.trim()}
            className="bg-purple-600 hover:bg-purple-700"
          >
            {saving ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
            ) : (
              <FiSave className="w-4 h-4 mr-2" />
            )}
            Save New Key
          </Button>
          <Button
            variant="outline"
            onClick={handleValidateKey}
            className="border-white/20 text-white"
          >
            <FiRefreshCw className="w-4 h-4 mr-2" />
            Test Current Key
          </Button>
        </div>
        
        <p className="text-xs text-white/40">
          Get your key from <a href="https://fal.ai/dashboard/keys" target="_blank" rel="noopener noreferrer" className="text-purple-400 hover:underline">fal.ai/dashboard/keys</a>
        </p>
      </div>
    </div>
  );
}

export default function AdminDashboard() {
  const navigate = useNavigate();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);
  const [adminName, setAdminName] = useState('Admin');
  
  // Search & Filter State
  const [searchQuery, setSearchQuery] = useState('');
  const [genreFilter, setGenreFilter] = useState('All');
  const [ageFilter, setAgeFilter] = useState('All');
  const [userSearchQuery, setUserSearchQuery] = useState('');
  
  // Preview Modal State
  const [previewBook, setPreviewBook] = useState(null);
  const [previewPages, setPreviewPages] = useState([]);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [currentPreviewPage, setCurrentPreviewPage] = useState(-1); // -1 = cover page
  
  // Content Review State
  const [pendingBooks, setPendingBooks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [processing, setProcessing] = useState(null);
  const [moderating, setModerating] = useState(null);
  
  // CMS State
  const [allBooks, setAllBooks] = useState([]);
  const [users, setUsers] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  
  // Charts State
  const [timeseriesData, setTimeseriesData] = useState(null);
  const [timeseriesPeriod, setTimeseriesPeriod] = useState('daily');
  const [timeseriesDays, setTimeseriesDays] = useState(30);
  const [loadingTimeseries, setLoadingTimeseries] = useState(false);
  
  // Delete Test Accounts State
  const [deletingTestAccounts, setDeletingTestAccounts] = useState(false);
  
  // User Credits Modal State
  const [creditModalOpen, setCreditModalOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [newCredits, setNewCredits] = useState('');
  const [updatingCredits, setUpdatingCredits] = useState(false);
  
  // Open credit modal for a user
  const openCreditModal = (user) => {
    setSelectedUser(user);
    setNewCredits(user.credits?.toString() || '0');
    setCreditModalOpen(true);
  };
  
  // Update user credits
  const updateUserCredits = async () => {
    if (!selectedUser) return;
    
    const creditsValue = parseInt(newCredits, 10);
    if (isNaN(creditsValue) || creditsValue < 0) {
      toast.error('Please enter a valid number of credits (0 or more)');
      return;
    }
    
    setUpdatingCredits(true);
    try {
      const token = localStorage.getItem('azories-admin-token');
      const response = await axios.post(
        `${API}/api/admin/users/update-credits`,
        { email: selectedUser.email, credits: creditsValue },
        { headers: { Authorization: `Bearer ${token}` }}
      );
      
      if (response.data.success) {
        toast.success(`Credits updated: ${response.data.old_credits} → ${response.data.new_credits}`);
        
        // Update local state
        setUsers(users.map(u => 
          u.email === selectedUser.email 
            ? { ...u, credits: creditsValue }
            : u
        ));
        
        setCreditModalOpen(false);
        setSelectedUser(null);
      } else {
        toast.error('Failed to update credits');
      }
    } catch (error) {
      console.error('Error updating credits:', error);
      toast.error(error.response?.data?.detail || 'Failed to update credits');
    } finally {
      setUpdatingCredits(false);
    }
  };
  
  // Delete Test Accounts Function
  const deleteTestAccounts = async () => {
    if (!window.confirm('Are you sure you want to delete ALL test accounts? This cannot be undone.')) {
      return;
    }
    
    setDeletingTestAccounts(true);
    try {
      const token = localStorage.getItem('azories-admin-token');
      const response = await axios.delete(`${API}/api/admin/delete-test-accounts`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const data = response.data;
      toast.success(`Deleted ${data.deleted_count} test accounts!`);
      
      // Refresh users list
      fetchDashboardData();
      
    } catch (error) {
      console.error('Error deleting test accounts:', error);
      toast.error('Failed to delete test accounts');
    } finally {
      setDeletingTestAccounts(false);
    }
  };
  
  // Check if admin token exists
  useEffect(() => {
    const token = localStorage.getItem('azories-admin-token');
    if (token) {
      verifyAdminToken(token);
    }
  }, []);

  // Fetch timeseries when period or days change
  useEffect(() => {
    if (isLoggedIn) {
      fetchTimeseriesData();
    }
  }, [timeseriesPeriod, timeseriesDays, isLoggedIn]);

  const fetchTimeseriesData = async () => {
    const adminToken = localStorage.getItem('azories-admin-token');
    if (!adminToken) return;

    setLoadingTimeseries(true);
    try {
      const res = await fetch(
        `${API}/api/admin/analytics-timeseries?period=${timeseriesPeriod}&days=${timeseriesDays}`,
        { headers: { Authorization: `Bearer ${adminToken}` } }
      );
      if (res.ok) {
        const data = await res.json();
        setTimeseriesData(data);
      }
    } catch (error) {
      console.error('Error fetching timeseries:', error);
    } finally {
      setLoadingTimeseries(false);
    }
  };

  const verifyAdminToken = async (token) => {
    try {
      const res = await fetch(`${API}/api/admin/verify`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setIsLoggedIn(true);
        setAdminName(data.username || 'Admin');
        fetchAllData(token);
      } else {
        localStorage.removeItem('azories-admin-token');
      }
    } catch (error) {
      console.error('Admin verification failed:', error);
      localStorage.removeItem('azories-admin-token');
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginLoading(true);
    try {
      const res = await fetch(`${API}/api/admin/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      
      if (res.ok) {
        const data = await res.json();
        localStorage.setItem('azories-admin-token', data.access_token);
        setIsLoggedIn(true);
        setAdminName(data.admin_name || 'Admin');
        toast.success('Admin login successful');
        fetchAllData(data.access_token);
      } else {
        toast.error('Invalid admin credentials');
      }
    } catch (error) {
      toast.error('Login failed');
    } finally {
      setLoginLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('azories-admin-token');
    setIsLoggedIn(false);
    setPendingBooks([]);
    setAllBooks([]);
    setUsers([]);
    setAnalytics(null);
    toast.success('Logged out');
  };

  const getAuthHeaders = () => ({
    headers: { Authorization: `Bearer ${localStorage.getItem('azories-admin-token')}` }
  });

  const fetchAllData = async (token) => {
    const adminToken = token || localStorage.getItem('azories-admin-token');
    if (!adminToken) return;
    
    setLoading(true);
    const headers = { headers: { Authorization: `Bearer ${adminToken}` } };
    
    try {
      const [pendingRes, booksRes, usersRes, analyticsRes] = await Promise.all([
        fetch(`${API}/api/admin/pending-reviews`, headers).then(r => r.json()).catch(() => ({ books: [] })),
        axios.get(`${API}/api/admin/books`, headers).catch(() => ({ data: [] })),
        axios.get(`${API}/api/admin/users`, headers).catch(() => ({ data: { users: [] } })),
        axios.get(`${API}/api/admin/site-analytics?days=30`, headers).catch(() => ({ data: null }))
      ]);
      
      setPendingBooks(pendingRes.books || []);
      setAllBooks(booksRes.data || []);
      setUsers(usersRes.data?.users || usersRes.data || []);
      setAnalytics(analyticsRes.data);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Content Review Functions
  const handleRunModeration = async (bookId, bookTitle) => {
    setModerating(bookId);
    try {
      const adminToken = localStorage.getItem('azories-admin-token');
      const res = await fetch(`${API}/api/admin/books/${bookId}/run-moderation`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${adminToken}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        if (data.flagged) {
          toast.warning(`"${bookTitle}" flagged: ${data.categories.join(', ')}`);
        } else {
          toast.success(`"${bookTitle}" passed moderation check`);
        }
        fetchAllData();
      } else {
        toast.error('Failed to run moderation');
      }
    } catch (error) {
      toast.error('Error running moderation');
    } finally {
      setModerating(null);
    }
  };

  const handleApprove = async (bookId, bookTitle) => {
    setProcessing(bookId);
    try {
      const adminToken = localStorage.getItem('azories-admin-token');
      const res = await fetch(`${API}/api/admin/books/${bookId}/approve`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${adminToken}` }
      });
      if (res.ok) {
        toast.success(`"${bookTitle}" has been approved and published!`);
        fetchAllData();
      } else {
        toast.error('Failed to approve book');
      }
    } catch (error) {
      toast.error('Error approving book');
    } finally {
      setProcessing(null);
    }
  };

  const handleReject = async (bookId, bookTitle) => {
    const reason = window.prompt('Please provide a reason for rejection (optional):');
    setProcessing(bookId);
    try {
      const adminToken = localStorage.getItem('azories-admin-token');
      const res = await fetch(`${API}/api/admin/books/${bookId}/reject?reason=${encodeURIComponent(reason || '')}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${adminToken}` }
      });
      if (res.ok) {
        toast.success(`"${bookTitle}" has been rejected`);
        fetchAllData();
      } else {
        toast.error('Failed to reject book');
      }
    } catch (error) {
      toast.error('Error rejecting book');
    } finally {
      setProcessing(null);
    }
  };

  // CMS Functions
  const toggleFeatured = async (bookId) => {
    try {
      const res = await axios.post(`${API}/api/admin/books/${bookId}/feature`, {}, getAuthHeaders());
      setAllBooks(allBooks.map(b => b.id === bookId ? { ...b, is_featured: res.data.is_featured } : b));
      toast.success(res.data.is_featured ? 'Book featured' : 'Book unfeatured');
    } catch {
      toast.error('Failed to update');
    }
  };

  const toggleBestOfWeek = async (bookId) => {
    try {
      const res = await axios.post(`${API}/api/admin/books/${bookId}/best-of-week`, {}, getAuthHeaders());
      setAllBooks(allBooks.map(b => b.id === bookId ? { ...b, is_best_of_week: res.data.is_best_of_week } : b));
      toast.success(res.data.is_best_of_week ? 'Added to Best of Week' : 'Removed from Best of Week');
    } catch {
      toast.error('Failed to update');
    }
  };

  const togglePublish = async (bookId) => {
    try {
      const res = await axios.post(`${API}/api/admin/books/${bookId}/publish`, {}, getAuthHeaders());
      setAllBooks(allBooks.map(b => b.id === bookId ? { ...b, is_published: res.data.is_published } : b));
      toast.success(res.data.is_published ? 'Book published' : 'Book unpublished');
    } catch {
      toast.error('Failed to update');
    }
  };

  const deleteBook = async (bookId, title) => {
    if (!window.confirm(`Delete "${title}"? This cannot be undone.`)) return;
    try {
      await axios.delete(`${API}/api/admin/books/${bookId}`, getAuthHeaders());
      setAllBooks(allBooks.filter(b => b.id !== bookId));
      setPendingBooks(pendingBooks.filter(b => b.id !== bookId));
      toast.success('Book deleted');
    } catch {
      toast.error('Failed to delete');
    }
  };

  // Filter books based on search and filters
  const filteredBooks = useMemo(() => {
    return allBooks.filter(book => {
      const matchesSearch = !searchQuery.trim() || 
        book.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        book.author_name?.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesGenre = genreFilter === 'All' || book.genre === genreFilter;
      const matchesAge = ageFilter === 'All' || book.age_rating === ageFilter;
      return matchesSearch && matchesGenre && matchesAge;
    });
  }, [allBooks, searchQuery, genreFilter, ageFilter]);

  // Filter users based on search
  const filteredUsers = useMemo(() => {
    if (!userSearchQuery.trim()) return users;
    return users.filter(user => 
      user.name?.toLowerCase().includes(userSearchQuery.toLowerCase()) ||
      user.email?.toLowerCase().includes(userSearchQuery.toLowerCase())
    );
  }, [users, userSearchQuery]);

  const seedTestBooks = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/admin/seed-test-books`, {}, getAuthHeaders());
      toast.success(res.data.message);
      fetchAllData();
    } catch (error) {
      toast.error('Failed to seed test books');
    } finally {
      setLoading(false);
    }
  };

  const [generatingCovers, setGeneratingCovers] = useState(false);
  
  const generateMissingCovers = async () => {
    setGeneratingCovers(true);
    try {
      const res = await axios.post(`${API}/api/admin/generate-missing-covers`, {}, getAuthHeaders());
      if (res.data.updated > 0) {
        toast.success(`Generated ${res.data.updated} cover images!`);
        fetchAllData();
      } else {
        toast.info(res.data.message || 'All books already have covers');
      }
      if (res.data.errors?.length > 0) {
        console.error('Cover generation errors:', res.data.errors);
      }
    } catch (error) {
      toast.error('Failed to generate covers');
    } finally {
      setGeneratingCovers(false);
    }
  };

  // Preview book function
  const openPreview = async (book) => {
    setPreviewBook(book);
    setPreviewLoading(true);
    setCurrentPreviewPage(-1); // Start at cover page
    try {
      console.log('[AdminDashboard] Loading preview for book:', book.id);
      // Use admin endpoint which doesn't require user auth
      const res = await axios.get(`${API}/api/admin/books/${book.id}/full`, getAuthHeaders());
      const bookData = res.data;
      console.log('[AdminDashboard] Book data received:', bookData);
      // Update previewBook with full data
      setPreviewBook(bookData);
      // Flatten all pages from all chapters
      const allPages = [];
      if (bookData.chapters) {
        console.log('[AdminDashboard] Chapters found:', bookData.chapters.length);
        for (const chapter of bookData.chapters) {
          console.log(`[AdminDashboard] Chapter "${chapter.title}" has ${chapter.pages?.length || 0} pages`);
          if (chapter.pages) {
            for (const page of chapter.pages) {
              allPages.push({
                ...page,
                chapterTitle: chapter.title
              });
            }
          }
        }
      }
      console.log('[AdminDashboard] Total pages loaded:', allPages.length);
      setPreviewPages(allPages);
    } catch (error) {
      console.error('Failed to load book preview:', error);
      toast.error('Failed to load book preview');
    } finally {
      setPreviewLoading(false);
    }
  };

  const closePreview = () => {
    setPreviewBook(null);
    setPreviewPages([]);
    setCurrentPreviewPage(-1);
  };

  // Get publish status badge
  const getPublishStatusBadge = (book) => {
    if (book.is_published || book.publish_status === 'published') {
      return <span className="text-xs px-2 py-1 rounded-full bg-green-500/20 text-green-400">Published</span>;
    }
    if (book.publish_status === 'pending_review') {
      return <span className="text-xs px-2 py-1 rounded-full bg-amber-500/20 text-amber-400">Pending Review</span>;
    }
    if (book.publish_status === 'rejected') {
      return <span className="text-xs px-2 py-1 rounded-full bg-red-500/20 text-red-400">Rejected</span>;
    }
    return <span className="text-xs px-2 py-1 rounded-full bg-white/10 text-white/60">Draft</span>;
  };

  // Admin Login Screen
  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-md"
        >
          <div className="bg-card/90 backdrop-blur-xl rounded-3xl p-8 shadow-2xl border border-white/10">
            <div className="text-center mb-8">
              <div className="w-16 h-16 bg-purple-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <FiShield className="w-8 h-8 text-purple-400" />
              </div>
              <h1 className="font-heading text-2xl font-bold text-white">Admin Dashboard</h1>
              <p className="text-white/60 text-sm mt-2">
                Azories Content Management & Moderation
              </p>
            </div>
            
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <Label htmlFor="username" className="text-white/80">Username</Label>
                <Input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter admin username"
                  className="mt-1 bg-white/5 border-white/10 text-white"
                  data-testid="admin-username-input"
                  required
                />
              </div>
              <div>
                <Label htmlFor="password" className="text-white/80">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter admin password"
                  className="mt-1 bg-white/5 border-white/10 text-white"
                  data-testid="admin-password-input"
                  required
                />
              </div>
              <Button 
                type="submit" 
                className="w-full rounded-full bg-purple-600 hover:bg-purple-700" 
                disabled={loginLoading}
                data-testid="admin-login-btn"
              >
                {loginLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                    Authenticating...
                  </>
                ) : (
                  <>
                    <FiLogIn className="w-4 h-4 mr-2" />
                    Access Admin Panel
                  </>
                )}
              </Button>
            </form>
            
            <div className="mt-6 text-center">
              <button 
                onClick={() => navigate('/')}
                className="text-sm text-white/60 hover:text-purple-400 transition-colors"
              >
                ← Back to Azories
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <header className="border-b border-white/10 bg-black/20 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigate('/')} className="text-white/60 hover:text-white">
              <FiArrowLeft className="w-5 h-5" />
            </Button>
            <div className="w-10 h-10 bg-purple-500/20 rounded-xl flex items-center justify-center">
              <FiShield className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <h1 className="font-heading font-bold text-white">Admin Dashboard</h1>
              <p className="text-xs text-white/60">Welcome, {adminName}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => fetchAllData()}
              className="rounded-full border-white/20 text-white hover:bg-white/10"
            >
              <FiRefreshCw className="w-4 h-4 mr-2" /> Refresh
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLogout}
              className="rounded-full text-red-400 hover:text-red-300 hover:bg-red-500/10"
            >
              <FiLogOut className="w-4 h-4 mr-2" /> Logout
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          <div className="bg-white/5 backdrop-blur rounded-2xl p-4 border border-white/10">
            <FiClock className="w-8 h-8 text-amber-400 mb-2" />
            <p className="text-2xl font-bold text-white">{pendingBooks.length}</p>
            <p className="text-sm text-white/60">Pending Review</p>
          </div>
          <div className="bg-white/5 backdrop-blur rounded-2xl p-4 border border-white/10">
            <FiAlertTriangle className="w-8 h-8 text-red-400 mb-2" />
            <p className="text-2xl font-bold text-white">{pendingBooks.filter(b => b.moderation_flags?.length > 0).length}</p>
            <p className="text-sm text-white/60">Flagged</p>
          </div>
          <div className="bg-white/5 backdrop-blur rounded-2xl p-4 border border-white/10">
            <FiBook className="w-8 h-8 text-blue-400 mb-2" />
            <p className="text-2xl font-bold text-white">{analytics?.total_books || allBooks.length}</p>
            <p className="text-sm text-white/60">Total Books</p>
          </div>
          <div className="bg-white/5 backdrop-blur rounded-2xl p-4 border border-white/10">
            <FiEye className="w-8 h-8 text-green-400 mb-2" />
            <p className="text-2xl font-bold text-white">{analytics?.published_books || allBooks.filter(b => b.is_published).length}</p>
            <p className="text-sm text-white/60">Published</p>
          </div>
          <div className="bg-white/5 backdrop-blur rounded-2xl p-4 border border-white/10">
            <FiUsers className="w-8 h-8 text-purple-400 mb-2" />
            <p className="text-2xl font-bold text-white">{analytics?.total_users || users.length}</p>
            <p className="text-sm text-white/60">Total Users</p>
          </div>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="reviews" className="space-y-6">
          <TabsList className="bg-white/5 border border-white/10 p-1.5 rounded-2xl grid grid-cols-4 md:flex md:flex-wrap gap-1">
            <TabsTrigger value="reviews" className="rounded-xl data-[state=active]:bg-purple-600 text-white text-xs sm:text-sm px-2 sm:px-3">
              <FiClock className="w-3 h-3 sm:w-4 sm:h-4 sm:mr-2" /> 
              <span className="hidden sm:inline">Pending ({pendingBooks.length})</span>
              <span className="sm:hidden ml-1">{pendingBooks.length}</span>
            </TabsTrigger>
            <TabsTrigger value="books" className="rounded-xl data-[state=active]:bg-purple-600 text-white text-xs sm:text-sm px-2 sm:px-3">
              <FiBook className="w-3 h-3 sm:w-4 sm:h-4 sm:mr-2" />
              <span className="hidden sm:inline">Books ({allBooks.length})</span>
              <span className="sm:hidden ml-1">{allBooks.length}</span>
            </TabsTrigger>
            <TabsTrigger value="users" className="rounded-xl data-[state=active]:bg-purple-600 text-white text-xs sm:text-sm px-2 sm:px-3">
              <FiUsers className="w-3 h-3 sm:w-4 sm:h-4 sm:mr-2" />
              <span className="hidden sm:inline">Users ({users.length})</span>
              <span className="sm:hidden ml-1">{users.length}</span>
            </TabsTrigger>
            <TabsTrigger value="print-orders" className="rounded-xl data-[state=active]:bg-purple-600 text-white text-xs sm:text-sm px-2 sm:px-3">
              <FiPackage className="w-3 h-3 sm:w-4 sm:h-4 sm:mr-2" /> 
              <span className="hidden sm:inline">Orders</span>
            </TabsTrigger>
            <TabsTrigger value="analytics" className="rounded-xl data-[state=active]:bg-purple-600 text-white text-xs sm:text-sm px-2 sm:px-3">
              <FiBarChart2 className="w-3 h-3 sm:w-4 sm:h-4 sm:mr-2" /> 
              <span className="hidden sm:inline">Analytics</span>
            </TabsTrigger>
            <TabsTrigger value="charts" className="rounded-xl data-[state=active]:bg-purple-600 text-white text-xs sm:text-sm px-2 sm:px-3">
              <FiTrendingUp className="w-3 h-3 sm:w-4 sm:h-4 sm:mr-2" />
              <span className="hidden sm:inline">Charts</span>
            </TabsTrigger>
            <TabsTrigger value="settings" className="rounded-xl data-[state=active]:bg-purple-600 text-white text-xs sm:text-sm px-2 sm:px-3 col-span-2">
              <FiSettings className="w-3 h-3 sm:w-4 sm:h-4 sm:mr-2" />
              <span className="hidden sm:inline">Settings</span>
            </TabsTrigger>
          </TabsList>

          {/* Pending Reviews Tab */}
          <TabsContent value="reviews">
            <Card className="bg-white/5 border-white/10">
              <CardHeader>
                <CardTitle className="text-white">Books Pending Review</CardTitle>
                <CardDescription className="text-white/60">Review and approve or reject book submissions. Run AI moderation to scan content.</CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="text-center py-12">
                    <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                    <p className="text-white/60">Loading pending books...</p>
                  </div>
                ) : pendingBooks.length === 0 ? (
                  <div className="text-center py-12">
                    <FiCheck className="w-16 h-16 mx-auto text-green-500/50 mb-4" />
                    <h3 className="text-lg font-semibold mb-2 text-white">All Caught Up!</h3>
                    <p className="text-white/60">No books pending review at this time.</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {pendingBooks.map((book) => (
                      <div 
                        key={book.id}
                        className={`p-4 rounded-xl border ${
                          book.moderation_flags?.length > 0 
                            ? 'border-red-500/50 bg-red-500/5' 
                            : book.moderation_run_at 
                              ? 'border-green-500/50 bg-green-500/5'
                              : 'border-white/10 bg-white/5'
                        }`}
                        data-testid={`pending-book-${book.id}`}
                      >
                        <div className="flex items-start gap-4">
                          {/* Book Cover */}
                          <div className="w-16 h-22 rounded-lg overflow-hidden bg-white/10 flex-shrink-0">
                            {book.cover_image ? (
                              <img src={book.cover_image} alt={book.title} className="w-full h-full object-cover" />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center">
                                <FiBook className="w-6 h-6 text-white/30" />
                              </div>
                            )}
                          </div>
                          
                          {/* Book Info */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between gap-2">
                              <div>
                                <h3 className="font-semibold text-lg truncate text-white">{book.title}</h3>
                                <p className="text-sm text-white/60">by {book.author_name}</p>
                              </div>
                              <div className="flex flex-col gap-1 flex-shrink-0">
                                {book.moderation_flags?.length > 0 && (
                                  <span className="px-2 py-1 bg-red-500/20 text-red-400 text-xs rounded-full flex items-center gap-1">
                                    <FiAlertTriangle className="w-3 h-3" />
                                    Flagged
                                  </span>
                                )}
                                {book.moderation_run_at && !book.moderation_flags?.length && (
                                  <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded-full flex items-center gap-1">
                                    <FiCheck className="w-3 h-3" />
                                    Scanned
                                  </span>
                                )}
                                {!book.moderation_run_at && (
                                  <span className="px-2 py-1 bg-blue-500/20 text-blue-400 text-xs rounded-full flex items-center gap-1">
                                    <FiSearch className="w-3 h-3" />
                                    Not Scanned
                                  </span>
                                )}
                              </div>
                            </div>
                            
                            {/* AI Moderation Result */}
                            {book.moderation_run_at && (
                              <div className={`mt-2 p-3 rounded-lg ${book.moderation_flagged ? 'bg-red-500/10 border border-red-500/30' : 'bg-green-500/10 border border-green-500/30'}`}>
                                <p className={`text-xs font-semibold mb-1 ${book.moderation_flagged ? 'text-red-400' : 'text-green-400'}`}>
                                  {book.moderation_flagged ? '⚠️ AI Verdict: FLAGGED' : '✅ AI Verdict: PASSED'}
                                </p>
                                {book.moderation_flags?.length > 0 && (
                                  <div className="flex flex-wrap gap-1 mb-2">
                                    {book.moderation_flags.map((flag, i) => (
                                      <span key={i} className="px-2 py-0.5 bg-red-500/20 text-red-400 text-xs rounded">
                                        {flag}
                                      </span>
                                    ))}
                                  </div>
                                )}
                                {book.moderation_message && (
                                  <p className="text-xs text-white/60">{book.moderation_message}</p>
                                )}
                              </div>
                            )}
                            
                            <div className="flex items-center gap-2 mt-2 text-xs text-white/50">
                              <span>{book.genre}</span>
                              <span>•</span>
                              <span>{book.age_rating || 'All Ages'}</span>
                              {book.publish_requested_at && (
                                <>
                                  <span>•</span>
                                  <span>Submitted: {new Date(book.publish_requested_at).toLocaleDateString()}</span>
                                </>
                              )}
                            </div>
                          </div>
                          
                          {/* Actions */}
                          <div className="flex flex-col gap-2 flex-shrink-0">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => openPreview(book)}
                              className="text-xs border-white/20 text-white hover:bg-white/10"
                            >
                              <FiEye className="w-3 h-3 mr-1" />
                              Preview
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleRunModeration(book.id, book.title)}
                              disabled={moderating === book.id}
                              className="text-xs bg-blue-500/10 hover:bg-blue-500/20 border-blue-500/50 text-blue-400"
                            >
                              {moderating === book.id ? (
                                <div className="w-3 h-3 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mr-1" />
                              ) : (
                                <FiRefreshCw className="w-3 h-3 mr-1" />
                              )}
                              Re-scan
                            </Button>
                            <Button
                              size="sm"
                              onClick={() => handleApprove(book.id, book.title)}
                              disabled={processing === book.id}
                              className="bg-green-600 hover:bg-green-700 text-xs"
                            >
                              <FiCheck className="w-3 h-3 mr-1" />
                              Approve
                            </Button>
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => handleReject(book.id, book.title)}
                              disabled={processing === book.id}
                              className="text-xs"
                            >
                              <FiX className="w-3 h-3 mr-1" />
                              Reject
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* All Books Tab */}
          <TabsContent value="books" className="space-y-4">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <h2 className="text-xl font-heading font-bold text-white">All Books ({filteredBooks.length})</h2>
              <div className="flex gap-2">
                <Button
                  onClick={generateMissingCovers}
                  disabled={generatingCovers}
                  variant="outline"
                  className="rounded-full border-green-500/30 text-green-400 hover:bg-green-500/10"
                >
                  <FiImage className="w-4 h-4 mr-2" />
                  {generatingCovers ? 'Generating...' : 'Generate Missing Covers'}
                </Button>
                <Button
                  onClick={seedTestBooks}
                  disabled={loading}
                  variant="outline"
                  className="rounded-full border-white/20 text-white hover:bg-white/10"
                >
                  <FiDatabase className="w-4 h-4 mr-2" />
                  {loading ? 'Seeding...' : 'Seed Test Books'}
                </Button>
              </div>
            </div>
            
            {/* Search and Filter Bar */}
            <div className="flex flex-col md:flex-row gap-3 p-4 bg-white/5 rounded-xl border border-white/10">
              <div className="relative flex-1">
                <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40 w-4 h-4" />
                <Input
                  placeholder="Search by title or author..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 bg-white/5 border-white/10 text-white placeholder:text-white/40"
                  data-testid="book-search-input"
                />
              </div>
              <Select value={genreFilter} onValueChange={setGenreFilter}>
                <SelectTrigger className="w-full md:w-[180px] bg-white/5 border-white/10 text-white" data-testid="genre-filter">
                  <FiFilter className="w-4 h-4 mr-2 text-white/40" />
                  <SelectValue placeholder="Genre" />
                </SelectTrigger>
                <SelectContent>
                  {GENRES.map(genre => (
                    <SelectItem key={genre} value={genre}>{genre}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={ageFilter} onValueChange={setAgeFilter}>
                <SelectTrigger className="w-full md:w-[150px] bg-white/5 border-white/10 text-white" data-testid="age-filter">
                  <FiUser className="w-4 h-4 mr-2 text-white/40" />
                  <SelectValue placeholder="Age Rating" />
                </SelectTrigger>
                <SelectContent>
                  {AGE_RATINGS.map(age => (
                    <SelectItem key={age} value={age}>{age}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {(searchQuery || genreFilter !== 'All' || ageFilter !== 'All') && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => { setSearchQuery(''); setGenreFilter('All'); setAgeFilter('All'); }}
                  className="text-white/60 hover:text-white"
                >
                  Clear
                </Button>
              )}
            </div>
            
            <div className="bg-white/5 backdrop-blur rounded-2xl border border-white/10 overflow-hidden">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/10 text-left">
                    <th className="p-4 text-white/60 font-ui text-sm">Cover</th>
                    <th className="p-4 text-white/60 font-ui text-sm">Title</th>
                    <th className="p-4 text-white/60 font-ui text-sm">Author</th>
                    <th className="p-4 text-white/60 font-ui text-sm">Genre</th>
                    <th className="p-4 text-white/60 font-ui text-sm">Status</th>
                    <th className="p-4 text-white/60 font-ui text-sm">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredBooks.map((book) => (
                    <tr key={book.id} className="border-b border-white/5 hover:bg-white/5">
                      <td className="p-4">
                        <div className="w-12 h-16 rounded-lg overflow-hidden bg-white/10">
                          {book.cover_image ? (
                            <img src={book.cover_image} alt="" className="w-full h-full object-cover" />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center">
                              <FiBook className="text-white/30" />
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="p-4">
                        <p className="text-white font-medium">{book.title}</p>
                        <p className="text-xs text-white/40">{book.age_rating}</p>
                      </td>
                      <td className="p-4 text-white/70">{book.author_name}</td>
                      <td className="p-4">
                        <span className="text-xs px-2 py-1 rounded-full bg-white/10 text-white/70">
                          {book.genre}
                        </span>
                      </td>
                      <td className="p-4">
                        <div className="flex flex-col gap-1">
                          {getPublishStatusBadge(book)}
                          {book.is_featured && (
                            <span className="text-xs text-yellow-400">★ Featured</span>
                          )}
                          {book.is_best_of_week && (
                            <span className="text-xs text-purple-400">🏆 Best of Week</span>
                          )}
                        </div>
                      </td>
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => openPreview(book)}
                            className="rounded-full h-8 w-8 p-0"
                            title="Preview Book"
                          >
                            <FiBook className="w-3 h-3" />
                          </Button>
                          <Button
                            size="sm"
                            variant={book.is_published ? "default" : "outline"}
                            onClick={() => togglePublish(book.id)}
                            className="rounded-full h-8 w-8 p-0"
                            title={book.is_published ? "Unpublish" : "Publish"}
                          >
                            {book.is_published ? <FiEye className="w-3 h-3" /> : <FiEyeOff className="w-3 h-3" />}
                          </Button>
                          <Button
                            size="sm"
                            variant={book.is_featured ? "default" : "outline"}
                            onClick={() => toggleFeatured(book.id)}
                            className="rounded-full h-8 w-8 p-0"
                            title="Toggle Featured"
                          >
                            <FiStar className="w-3 h-3" />
                          </Button>
                          <Button
                            size="sm"
                            variant={book.is_best_of_week ? "default" : "outline"}
                            onClick={() => toggleBestOfWeek(book.id)}
                            className="rounded-full h-8 w-8 p-0"
                            title="Toggle Best of Week"
                          >
                            <FiAward className="w-3 h-3" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => deleteBook(book.id, book.title)}
                            className="rounded-full h-8 w-8 p-0 text-red-400 hover:text-red-300 hover:bg-red-500/10"
                            title="Delete Book"
                          >
                            <FiTrash2 className="w-3 h-3" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {filteredBooks.length === 0 && (
                <div className="text-center py-12 text-white/60">
                  {allBooks.length === 0 ? 'No books found' : 'No books match your filters'}
                </div>
              )}
            </div>
          </TabsContent>

          {/* Users Tab */}
          <TabsContent value="users">
            {/* User Search and Actions */}
            <div className="mb-4 space-y-3">
              {/* Search Row */}
              <div className="relative">
                <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40 w-4 h-4" />
                <Input
                  placeholder="Search users by name or email..."
                  value={userSearchQuery}
                  onChange={(e) => setUserSearchQuery(e.target.value)}
                  className="pl-10 bg-white/5 border-white/10 text-white placeholder:text-white/40"
                  data-testid="user-search-input"
                />
              </div>
              
              {/* Actions Row */}
              <div className="flex items-center justify-between gap-2">
                <p className="text-xs sm:text-sm text-white/50 flex items-center">
                  <FiDollarSign className="w-4 h-4 mr-1 text-purple-400" />
                  <span className="hidden sm:inline">Click "Edit" to modify user credits</span>
                  <span className="sm:hidden">Tap "Edit" for credits</span>
                </p>
                
                {/* Delete Test Accounts Button */}
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={deleteTestAccounts}
                  disabled={deletingTestAccounts}
                  className="bg-red-600 hover:bg-red-700 text-white text-xs px-2 sm:px-3 whitespace-nowrap"
                  data-testid="delete-test-accounts-btn"
                >
                  <FiTrash2 className={`w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2 ${deletingTestAccounts ? 'animate-spin' : ''}`} />
                  <span className="hidden sm:inline">{deletingTestAccounts ? 'Deleting...' : 'Delete Test Accounts'}</span>
                  <span className="sm:hidden">{deletingTestAccounts ? '...' : 'Delete Test'}</span>
                </Button>
              </div>
            </div>
            
            <div className="bg-white/5 backdrop-blur rounded-2xl border border-white/10 overflow-x-auto">
              <table className="w-full min-w-0">
                <thead>
                  <tr className="border-b border-white/10 text-left">
                    <th className="p-3 md:p-4 text-white/60 font-ui text-sm">Name</th>
                    <th className="p-3 md:p-4 text-white/60 font-ui text-sm hidden sm:table-cell">Email</th>
                    <th className="p-3 md:p-4 text-white/60 font-ui text-sm hidden lg:table-cell">Subscription</th>
                    <th className="p-3 md:p-4 text-white/60 font-ui text-sm">Credits</th>
                    <th className="p-3 md:p-4 text-white/60 font-ui text-sm hidden lg:table-cell">Joined</th>
                    <th className="p-3 md:p-4 text-white/60 font-ui text-sm text-right">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredUsers.map((user) => (
                    <tr 
                      key={user.id} 
                      className="border-b border-white/5 hover:bg-white/5 active:bg-white/10 transition-colors"
                      data-testid={`user-row-${user.email}`}
                    >
                      <td className="p-3 md:p-4">
                        <div className="text-white font-medium text-sm">{user.name}</div>
                        <div className="text-white/50 text-xs sm:hidden truncate max-w-[120px]">{user.email}</div>
                      </td>
                      <td className="p-3 md:p-4 text-white/70 text-sm hidden sm:table-cell">
                        <span className="truncate block max-w-[200px]">{user.email}</span>
                      </td>
                      <td className="p-3 md:p-4 hidden lg:table-cell">
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          user.subscription === 'pro' 
                            ? 'bg-purple-500/20 text-purple-400' 
                            : 'bg-white/10 text-white/60'
                        }`}>
                          {user.subscription || 'Free'}
                        </span>
                      </td>
                      <td className="p-3 md:p-4 text-white/70 text-sm">
                        {user.credits || 0}
                      </td>
                      <td className="p-3 md:p-4 text-white/50 text-sm hidden lg:table-cell">
                        {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                      </td>
                      <td className="p-3 md:p-4 text-right">
                        <Button
                          size="sm"
                          onClick={() => openCreditModal(user)}
                          className="bg-purple-600 hover:bg-purple-700 text-white text-xs px-2 py-1"
                          data-testid={`edit-credits-${user.email}`}
                        >
                          <FiDollarSign className="w-3 h-3 sm:mr-1" />
                          <span className="hidden sm:inline">Edit</span>
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {filteredUsers.length === 0 && (
                <div className="text-center py-12 text-white/60">
                  {users.length === 0 ? 'No users found' : 'No users match your search'}
                </div>
              )}
            </div>
          </TabsContent>

          {/* Print Orders Tab */}
          <TabsContent value="print-orders">
            <Card className="bg-white/5 border-white/10">
              <CardHeader>
                <div className="flex justify-between items-center">
                  <CardTitle className="text-white text-lg flex items-center gap-2">
                    <FiPackage className="w-5 h-5" />
                    Print Orders Management
                  </CardTitle>
                  <Button 
                    onClick={() => navigate('/admin/print-orders')}
                    className="bg-purple-600 hover:bg-purple-700"
                  >
                    Open Full Dashboard
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8">
                  <FiPackage className="w-16 h-16 mx-auto mb-4 text-purple-400" />
                  <h3 className="text-xl font-semibold text-white mb-2">Physical Book Order Tracking</h3>
                  <p className="text-gray-400 mb-6 max-w-md mx-auto">
                    Track all print orders, view order status, manage fulfillment, and see financial breakdowns including costs, revenue, and profit.
                  </p>
                  <div className="flex justify-center gap-4 flex-wrap">
                    <div className="bg-white/5 rounded-lg p-4 min-w-[140px]">
                      <FiDollarSign className="w-8 h-8 mx-auto mb-2 text-green-400" />
                      <p className="text-sm text-gray-400">Revenue & Profit</p>
                    </div>
                    <div className="bg-white/5 rounded-lg p-4 min-w-[140px]">
                      <FiTruck className="w-8 h-8 mx-auto mb-2 text-blue-400" />
                      <p className="text-sm text-gray-400">Order Tracking</p>
                    </div>
                    <div className="bg-white/5 rounded-lg p-4 min-w-[140px]">
                      <FiBarChart2 className="w-8 h-8 mx-auto mb-2 text-purple-400" />
                      <p className="text-sm text-gray-400">Financial Reports</p>
                    </div>
                  </div>
                  <Button 
                    onClick={() => navigate('/admin/print-orders')}
                    className="mt-6 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
                    size="lg"
                  >
                    <FiPackage className="w-5 h-5 mr-2" />
                    Go to Print Orders Dashboard
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>


          {/* Analytics Tab */}
          <TabsContent value="analytics">
            {analytics ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <Card className="bg-white/5 border-white/10">
                  <CardHeader>
                    <CardTitle className="text-white text-lg">Total Books</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-4xl font-bold text-blue-400">{analytics.summary?.total_books || allBooks.length || 0}</p>
                  </CardContent>
                </Card>
                <Card className="bg-white/5 border-white/10">
                  <CardHeader>
                    <CardTitle className="text-white text-lg">Published Books</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-4xl font-bold text-green-400">{analytics.summary?.published_books || 0}</p>
                  </CardContent>
                </Card>
                <Card className="bg-white/5 border-white/10">
                  <CardHeader>
                    <CardTitle className="text-white text-lg">Total Users</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-4xl font-bold text-purple-400">{analytics.summary?.total_users || users.length || 0}</p>
                  </CardContent>
                </Card>
                <Card className="bg-white/5 border-white/10">
                  <CardHeader>
                    <CardTitle className="text-white text-lg">New Users (30 days)</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-4xl font-bold text-yellow-400">{analytics.summary?.new_users || 0}</p>
                  </CardContent>
                </Card>
                <Card className="bg-white/5 border-white/10">
                  <CardHeader>
                    <CardTitle className="text-white text-lg">Page Views</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-4xl font-bold text-cyan-400">{analytics.summary?.total_page_views || 0}</p>
                    <p className="text-white/50 text-sm mt-1">Since tracking enabled</p>
                  </CardContent>
                </Card>
                <Card className="bg-white/5 border-white/10">
                  <CardHeader>
                    <CardTitle className="text-white text-lg">Unique Visitors</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-4xl font-bold text-pink-400">{analytics.summary?.unique_visitors || 0}</p>
                    <p className="text-white/50 text-sm mt-1">Last 30 days</p>
                  </CardContent>
                </Card>
                <Card className="bg-white/5 border-white/10">
                  <CardHeader>
                    <CardTitle className="text-white text-lg">AI Stories Created</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-4xl font-bold text-orange-400">{analytics.summary?.ai_stories_created || 0}</p>
                  </CardContent>
                </Card>
                <Card className="bg-white/5 border-white/10">
                  <CardHeader>
                    <CardTitle className="text-white text-lg">New Signups</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-4xl font-bold text-emerald-400">{analytics.summary?.signups || 0}</p>
                    <p className="text-white/50 text-sm mt-1">Last 30 days</p>
                  </CardContent>
                </Card>
                
                {/* Recent Users Section */}
                {analytics.recent_users && analytics.recent_users.length > 0 && (
                  <Card className="bg-white/5 border-white/10 col-span-full">
                    <CardHeader>
                      <CardTitle className="text-white text-lg">Recent Users</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2 max-h-64 overflow-y-auto">
                        {analytics.recent_users.slice(0, 10).map((user, idx) => (
                          <div key={idx} className="flex justify-between items-center py-2 border-b border-white/10">
                            <div>
                              <p className="text-white font-medium">{user.name || 'Unknown'}</p>
                              <p className="text-white/50 text-sm">{user.email}</p>
                            </div>
                            <div className="text-right">
                              <p className="text-white/70 text-sm">{user.credits || 0} credits</p>
                              <p className="text-white/40 text-xs">{user.created_at?.slice(0, 10)}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
                
                {/* Popular Books Section */}
                {analytics.popular_books && analytics.popular_books.length > 0 && (
                  <Card className="bg-white/5 border-white/10 col-span-full">
                    <CardHeader>
                      <CardTitle className="text-white text-lg">Popular Books (Most Read)</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {analytics.popular_books.map((book, idx) => (
                          <div key={idx} className="flex justify-between items-center py-2 border-b border-white/10">
                            <p className="text-white">{book.title}</p>
                            <p className="text-cyan-400 font-bold">{book.reads} reads</p>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            ) : (
              <div className="text-center py-12 text-white/60">
                <FiBarChart2 className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p>Loading analytics...</p>
              </div>
            )}
          </TabsContent>

          {/* Charts Tab */}
          <TabsContent value="charts">
            <div className="space-y-6">
              {/* Time Period Controls */}
              <Card className="bg-white/5 border-white/10">
                <CardContent className="pt-6">
                  <div className="flex flex-wrap items-center gap-4">
                    <div className="flex items-center gap-2">
                      <FiCalendar className="text-white/60" />
                      <span className="text-white font-medium">Period:</span>
                      <div className="flex gap-1">
                        {['daily', 'weekly', 'monthly'].map(p => (
                          <button
                            key={p}
                            onClick={() => setTimeseriesPeriod(p)}
                            className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                              timeseriesPeriod === p
                                ? 'bg-purple-600 text-white'
                                : 'bg-white/10 text-white/60 hover:bg-white/20'
                            }`}
                          >
                            {p.charAt(0).toUpperCase() + p.slice(1)}
                          </button>
                        ))}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-white font-medium">Days:</span>
                      <select
                        value={timeseriesDays}
                        onChange={(e) => setTimeseriesDays(Number(e.target.value))}
                        className="px-3 py-1.5 rounded border border-white/20 bg-white/10 text-white text-sm"
                      >
                        <option value={7}>Last 7 days</option>
                        <option value={14}>Last 14 days</option>
                        <option value={30}>Last 30 days</option>
                        <option value={60}>Last 60 days</option>
                        <option value={90}>Last 90 days</option>
                      </select>
                    </div>
                    {loadingTimeseries && (
                      <div className="w-5 h-5 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
                    )}
                  </div>
                </CardContent>
              </Card>

              {timeseriesData && timeseriesData.data?.length > 0 ? (
                <>
                  {/* Page Views & Visitors Chart */}
                  <Card className="bg-white/5 border-white/10">
                    <CardHeader>
                      <CardTitle className="text-white text-lg flex items-center gap-2">
                        <FiEye className="text-blue-400" />
                        Page Views & Visitors
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <AreaChart data={timeseriesData.data}>
                          <defs>
                            <linearGradient id="colorViews" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8}/>
                              <stop offset="95%" stopColor="#8884d8" stopOpacity={0}/>
                            </linearGradient>
                            <linearGradient id="colorVisitors" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#82ca9d" stopOpacity={0.8}/>
                              <stop offset="95%" stopColor="#82ca9d" stopOpacity={0}/>
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                          <XAxis 
                            dataKey={timeseriesPeriod === 'weekly' ? 'week_label' : timeseriesPeriod === 'monthly' ? 'month_label' : 'date'} 
                            tick={{ fontSize: 12, fill: '#999' }}
                            tickFormatter={(val) => timeseriesPeriod === 'daily' ? val?.slice(5) : val}
                          />
                          <YAxis tick={{ fontSize: 12, fill: '#999' }} />
                          <Tooltip 
                            contentStyle={{ backgroundColor: '#1e1e2e', borderRadius: '8px', border: '1px solid #333', color: '#fff' }}
                            labelStyle={{ color: '#fff' }}
                          />
                          <Legend />
                          <Area type="monotone" dataKey="page_views" name="Page Views" stroke="#8884d8" fillOpacity={1} fill="url(#colorViews)" />
                          <Area type="monotone" dataKey="unique_visitors" name="Unique Visitors" stroke="#82ca9d" fillOpacity={1} fill="url(#colorVisitors)" />
                        </AreaChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  {/* User Activity Chart */}
                  <Card className="bg-white/5 border-white/10">
                    <CardHeader>
                      <CardTitle className="text-white text-lg flex items-center gap-2">
                        <FiUsers className="text-green-400" />
                        User Activity
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={timeseriesData.data}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                          <XAxis 
                            dataKey={timeseriesPeriod === 'weekly' ? 'week_label' : timeseriesPeriod === 'monthly' ? 'month_label' : 'date'} 
                            tick={{ fontSize: 12, fill: '#999' }}
                            tickFormatter={(val) => timeseriesPeriod === 'daily' ? val?.slice(5) : val}
                          />
                          <YAxis tick={{ fontSize: 12, fill: '#999' }} />
                          <Tooltip 
                            contentStyle={{ backgroundColor: '#1e1e2e', borderRadius: '8px', border: '1px solid #333', color: '#fff' }}
                            labelStyle={{ color: '#fff' }}
                          />
                          <Legend />
                          <Line type="monotone" dataKey="signups" name="New Signups" stroke="#10b981" strokeWidth={2} dot={{ r: 4 }} />
                          <Line type="monotone" dataKey="book_reads" name="Book Reads" stroke="#f59e0b" strokeWidth={2} dot={{ r: 4 }} />
                        </LineChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  {/* Content Creation Chart */}
                  <Card className="bg-white/5 border-white/10">
                    <CardHeader>
                      <CardTitle className="text-white text-lg flex items-center gap-2">
                        <FiBook className="text-purple-400" />
                        Content Creation
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={timeseriesData.data}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                          <XAxis 
                            dataKey={timeseriesPeriod === 'weekly' ? 'week_label' : timeseriesPeriod === 'monthly' ? 'month_label' : 'date'} 
                            tick={{ fontSize: 12, fill: '#999' }}
                            tickFormatter={(val) => timeseriesPeriod === 'daily' ? val?.slice(5) : val}
                          />
                          <YAxis tick={{ fontSize: 12, fill: '#999' }} />
                          <Tooltip 
                            contentStyle={{ backgroundColor: '#1e1e2e', borderRadius: '8px', border: '1px solid #333', color: '#fff' }}
                            labelStyle={{ color: '#fff' }}
                          />
                          <Legend />
                          <Line type="monotone" dataKey="ai_stories" name="AI Stories Created" stroke="#8b5cf6" strokeWidth={2} dot={{ r: 4 }} />
                          <Line type="monotone" dataKey="books_created" name="Books Created" stroke="#ec4899" strokeWidth={2} dot={{ r: 4 }} />
                        </LineChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  {/* Summary Stats */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-gradient-to-r from-purple-600 to-purple-700 rounded-xl p-4 text-white">
                      <div className="text-2xl font-bold">
                        {timeseriesData.data.reduce((sum, d) => sum + (d.page_views || 0), 0).toLocaleString()}
                      </div>
                      <div className="text-purple-200 text-sm">Total Page Views</div>
                    </div>
                    <div className="bg-gradient-to-r from-green-600 to-green-700 rounded-xl p-4 text-white">
                      <div className="text-2xl font-bold">
                        {timeseriesData.data.reduce((sum, d) => sum + (d.signups || 0), 0).toLocaleString()}
                      </div>
                      <div className="text-green-200 text-sm">New Signups</div>
                    </div>
                    <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-xl p-4 text-white">
                      <div className="text-2xl font-bold">
                        {timeseriesData.data.reduce((sum, d) => sum + (d.book_reads || 0), 0).toLocaleString()}
                      </div>
                      <div className="text-blue-200 text-sm">Book Reads</div>
                    </div>
                    <div className="bg-gradient-to-r from-pink-600 to-pink-700 rounded-xl p-4 text-white">
                      <div className="text-2xl font-bold">
                        {timeseriesData.data.reduce((sum, d) => sum + (d.ai_stories || 0), 0).toLocaleString()}
                      </div>
                      <div className="text-pink-200 text-sm">AI Stories</div>
                    </div>
                  </div>
                </>
              ) : (
                <div className="text-center py-12 text-white/60">
                  <FiTrendingUp className="w-16 h-16 mx-auto mb-4 opacity-50" />
                  <p>{loadingTimeseries ? 'Loading charts...' : 'No chart data available'}</p>
                </div>
              )}
            </div>
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings">
            <Card className="bg-white/5 border-white/10">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <FiSettings className="w-5 h-5" /> System Settings
                </CardTitle>
                <CardDescription className="text-white/60">
                  Manage API keys and system configuration
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* FAL.AI Key Management */}
                <SettingsFalKey />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>

      {/* Preview Modal */}
      <Dialog open={!!previewBook} onOpenChange={(open) => !open && closePreview()}>
        <DialogContent className="max-w-4xl h-[85vh] bg-slate-900 border-white/10 p-0 overflow-hidden">
          <DialogHeader className="p-4 border-b border-white/10 bg-black/30">
            <div className="flex items-center justify-between">
              <div>
                <DialogTitle className="text-white text-xl">{previewBook?.title}</DialogTitle>
                <p className="text-white/60 text-sm">by {previewBook?.author_name} • {previewBook?.genre}</p>
              </div>
              <div className="flex items-center gap-2">
                {previewBook?.moderation_flagged ? (
                  <span className="px-3 py-1 bg-red-500/20 text-red-400 text-sm rounded-full flex items-center gap-1">
                    <FiAlertTriangle className="w-4 h-4" /> Flagged
                  </span>
                ) : previewBook?.moderation_run_at ? (
                  <span className="px-3 py-1 bg-green-500/20 text-green-400 text-sm rounded-full flex items-center gap-1">
                    <FiCheck className="w-4 h-4" /> Passed
                  </span>
                ) : null}
              </div>
            </div>
          </DialogHeader>
          
          <div className="flex-1 overflow-hidden flex flex-col">
            {previewLoading ? (
              <div className="flex-1 flex items-center justify-center">
                <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : (
              <>
                {/* Book Reader Style Preview */}
                <div className="flex-1 overflow-auto">
                  {/* Cover Page (currentPreviewPage === -1) or Content Pages */}
                  {currentPreviewPage === -1 ? (
                    /* Cover Page */
                    <div className="h-full flex items-center justify-center p-6 bg-gradient-to-b from-slate-800 to-slate-900">
                      <div className="text-center max-w-md">
                        {previewBook?.cover_image ? (
                          <img 
                            src={previewBook.cover_image} 
                            alt={previewBook.title}
                            className="w-64 h-auto mx-auto rounded-xl shadow-2xl mb-6 border border-white/10"
                          />
                        ) : (
                          <div className="w-64 h-80 mx-auto rounded-xl bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center mb-6 shadow-2xl">
                            <FiBook className="w-20 h-20 text-white/50" />
                          </div>
                        )}
                        <h1 className="text-3xl font-bold text-white mb-2">{previewBook?.title}</h1>
                        <p className="text-lg text-purple-400 mb-4">by {previewBook?.author_name}</p>
                        <div className="flex items-center justify-center gap-3 text-sm text-white/60 mb-4">
                          <span className="px-3 py-1 bg-white/10 rounded-full">{previewBook?.genre}</span>
                          <span className="px-3 py-1 bg-white/10 rounded-full">{previewBook?.age_rating || 'All Ages'}</span>
                        </div>
                        {previewBook?.description && (
                          <p className="text-white/70 text-sm leading-relaxed max-w-sm mx-auto">
                            {previewBook.description}
                          </p>
                        )}
                      </div>
                    </div>
                  ) : previewPages.length > 0 ? (
                    /* Content Page */
                    <div className="h-full flex items-center justify-center p-6 bg-gradient-to-b from-slate-800 to-slate-900">
                      <div className="max-w-2xl w-full">
                        {/* Chapter Title */}
                        {previewPages[currentPreviewPage]?.chapterTitle && (
                          <p className="text-purple-400 text-sm font-medium mb-2">
                            Chapter: {previewPages[currentPreviewPage].chapterTitle}
                          </p>
                        )}
                        
                        {/* Page Media - Full Width */}
                        {(previewPages[currentPreviewPage]?.image_url || previewPages[currentPreviewPage]?.video_url) && (
                          <div className="mb-6 rounded-xl overflow-hidden bg-black/50 flex items-center justify-center">
                            {previewPages[currentPreviewPage]?.video_url ? (
                              <video 
                                src={previewPages[currentPreviewPage].video_url} 
                                controls 
                                className="w-full max-h-[400px] object-contain"
                              />
                            ) : (
                              <img 
                                src={previewPages[currentPreviewPage].image_url} 
                                alt="Page illustration"
                                className="w-full max-h-[400px] object-contain"
                              />
                            )}
                          </div>
                        )}
                        
                        {/* Page Text */}
                        {previewPages[currentPreviewPage]?.text_content && (
                          <div className="bg-white/5 rounded-xl p-6 border border-white/10">
                            <p className="text-white/90 text-lg leading-relaxed whitespace-pre-wrap">
                              {previewPages[currentPreviewPage].text_content}
                            </p>
                          </div>
                        )}
                        
                        {/* Empty page indicator */}
                        {!previewPages[currentPreviewPage]?.image_url && 
                         !previewPages[currentPreviewPage]?.video_url && 
                         !previewPages[currentPreviewPage]?.text_content && (
                          <div className="text-center text-white/40 py-12">
                            <FiBook className="w-12 h-12 mx-auto mb-3 opacity-50" />
                            <p>This page has no content</p>
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    /* No Pages Message */
                    <div className="h-full flex items-center justify-center p-6 bg-gradient-to-b from-slate-800 to-slate-900">
                      <div className="text-center">
                        <FiBook className="w-16 h-16 mx-auto mb-4 text-white/30" />
                        <h3 className="text-xl font-semibold text-white mb-2">No Content Pages</h3>
                        <p className="text-white/60">This book has no content pages yet.</p>
                        <p className="text-white/40 text-sm mt-2">The author may still be working on it.</p>
                      </div>
                    </div>
                  )}
                </div>
                
                {/* Page Navigation */}
                <div className="p-4 border-t border-white/10 bg-black/30">
                  {/* Page Thumbnails */}
                  {previewPages.length > 0 && (
                    <div className="mb-4 flex items-center gap-2 overflow-x-auto pb-2">
                      {/* Cover thumbnail */}
                      <button
                        onClick={() => setCurrentPreviewPage(-1)}
                        className={`flex-shrink-0 w-12 h-16 rounded border-2 transition-all flex items-center justify-center text-xs ${
                          currentPreviewPage === -1 
                            ? 'border-purple-500 bg-purple-500/20' 
                            : 'border-white/20 hover:border-white/40'
                        }`}
                      >
                        <span className="text-white/80">Cover</span>
                      </button>
                      
                      {/* Page thumbnails */}
                      {previewPages.map((page, idx) => (
                        <button
                          key={idx}
                          onClick={() => setCurrentPreviewPage(idx)}
                          className={`flex-shrink-0 w-12 h-16 rounded border-2 overflow-hidden transition-all ${
                            currentPreviewPage === idx 
                              ? 'border-purple-500 bg-purple-500/20' 
                              : 'border-white/20 hover:border-white/40'
                          }`}
                        >
                          {page.image_url ? (
                            <img src={page.image_url} alt={`Page ${idx + 1}`} className="w-full h-full object-cover" />
                          ) : (
                            <span className="text-white/60 text-[10px]">{idx + 1}</span>
                          )}
                        </button>
                      ))}
                    </div>
                  )}
                  
                  {/* Navigation buttons */}
                  <div className="flex items-center justify-between">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPreviewPage(p => Math.max(-1, p - 1))}
                      disabled={currentPreviewPage === -1}
                      className="border-white/20 text-white hover:bg-white/10"
                    >
                      <FiChevronLeft className="w-4 h-4 mr-1" /> Previous
                    </Button>
                    
                    <span className="text-white/60 text-sm">
                      {currentPreviewPage === -1 ? 'Cover' : `Page ${currentPreviewPage + 1} of ${previewPages.length}`}
                    </span>
                    
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPreviewPage(p => p + 1)}
                      disabled={currentPreviewPage >= previewPages.length - 1}
                      className="border-white/20 text-white hover:bg-white/10"
                    >
                      Next <FiChevronRight className="w-4 h-4 ml-1" />
                    </Button>
                  </div>
                </div>
              </>
            )}
          </div>
          
          {/* Action Buttons */}
          {previewBook && (
            <div className="p-4 border-t border-white/10 bg-black/30 flex items-center justify-end gap-3">
              <Button
                variant="outline"
                onClick={closePreview}
                className="border-white/20 text-white"
              >
                Close
              </Button>
              <Button
                onClick={() => { handleApprove(previewBook.id, previewBook.title); closePreview(); }}
                disabled={processing === previewBook.id}
                className="bg-green-600 hover:bg-green-700"
              >
                <FiCheck className="w-4 h-4 mr-2" /> Approve
              </Button>
              <Button
                variant="destructive"
                onClick={() => { handleReject(previewBook.id, previewBook.title); closePreview(); }}
                disabled={processing === previewBook.id}
              >
                <FiX className="w-4 h-4 mr-2" /> Reject
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>
      
      {/* User Credits Modal */}
      <Dialog open={creditModalOpen} onOpenChange={setCreditModalOpen}>
        <DialogContent className="max-w-md bg-slate-900 border-white/10">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <FiDollarSign className="w-5 h-5 text-purple-400" />
              Manage User Credits
            </DialogTitle>
          </DialogHeader>
          
          {selectedUser && (
            <div className="space-y-6 pt-4">
              {/* User Info */}
              <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-full bg-purple-600/20 flex items-center justify-center">
                    <FiUser className="w-5 h-5 text-purple-400" />
                  </div>
                  <div>
                    <p className="text-white font-medium">{selectedUser.name}</p>
                    <p className="text-white/60 text-sm">{selectedUser.email}</p>
                  </div>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-white/60">Current Credits:</span>
                  <span className="text-purple-400 font-semibold">{selectedUser.credits || 0}</span>
                </div>
              </div>
              
              {/* Credit Input */}
              <div className="space-y-2">
                <Label className="text-white/80">New Credit Amount</Label>
                <div className="flex gap-2">
                  <Input
                    type="number"
                    min="0"
                    value={newCredits}
                    onChange={(e) => setNewCredits(e.target.value)}
                    className="bg-white/5 border-white/10 text-white"
                    placeholder="Enter credits"
                    data-testid="credit-input"
                  />
                </div>
                <p className="text-xs text-white/40">
                  Enter the total credits the user should have (not credits to add)
                </p>
              </div>
              
              {/* Quick Add Buttons */}
              <div className="space-y-2">
                <Label className="text-white/80 text-sm">Quick Add</Label>
                <div className="flex flex-wrap gap-2">
                  {[10, 25, 50, 100, 250].map((amount) => (
                    <Button
                      key={amount}
                      variant="outline"
                      size="sm"
                      onClick={() => setNewCredits(String((parseInt(newCredits) || 0) + amount))}
                      className="bg-white/5 border-white/10 text-white hover:bg-white/10"
                      data-testid={`quick-add-${amount}`}
                    >
                      +{amount}
                    </Button>
                  ))}
                </div>
              </div>
              
              {/* Actions */}
              <div className="flex gap-3 pt-2">
                <Button
                  variant="outline"
                  onClick={() => setCreditModalOpen(false)}
                  className="flex-1 bg-white/5 border-white/10 text-white hover:bg-white/10"
                >
                  Cancel
                </Button>
                <Button
                  onClick={updateUserCredits}
                  disabled={updatingCredits}
                  className="flex-1 bg-purple-600 hover:bg-purple-700 text-white"
                  data-testid="save-credits-btn"
                >
                  {updatingCredits ? (
                    <>
                      <FiRefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <FiSave className="w-4 h-4 mr-2" />
                      Save Credits
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
