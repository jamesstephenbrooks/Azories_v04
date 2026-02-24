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
  FiChevronLeft, FiChevronRight
} from 'react-icons/fi';

const API = process.env.REACT_APP_BACKEND_URL;

// Available genres and age ratings
const GENRES = ['All', 'Fantasy', 'Adventure', 'Mystery', 'Science Fiction', 'Fairy Tales', 'Educational', 'Animals', 'Humor', 'Action', 'Other'];
const AGE_RATINGS = ['All', 'All Ages', '5+', '8+', '12+', '16+'];

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
  
  // Check if admin token exists
  useEffect(() => {
    const token = localStorage.getItem('azories-admin-token');
    if (token) {
      verifyAdminToken(token);
    }
  }, []);

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
        axios.get(`${API}/api/admin/users`, headers).catch(() => ({ data: [] })),
        axios.get(`${API}/api/admin/analytics`, headers).catch(() => ({ data: null }))
      ]);
      
      setPendingBooks(pendingRes.books || []);
      setAllBooks(booksRes.data || []);
      setUsers(usersRes.data || []);
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
      const res = await axios.get(`${API}/api/books/${book.id}/full`, getAuthHeaders());
      const bookData = res.data;
      // Update previewBook with full data
      setPreviewBook(bookData);
      // Flatten all pages from all chapters
      const allPages = [];
      if (bookData.chapters) {
        for (const chapter of bookData.chapters) {
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
          <TabsList className="bg-white/5 border border-white/10 p-1 rounded-full">
            <TabsTrigger value="reviews" className="rounded-full data-[state=active]:bg-purple-600 text-white">
              <FiClock className="w-4 h-4 mr-2" /> Pending Reviews ({pendingBooks.length})
            </TabsTrigger>
            <TabsTrigger value="books" className="rounded-full data-[state=active]:bg-purple-600 text-white">
              <FiBook className="w-4 h-4 mr-2" /> All Books ({allBooks.length})
            </TabsTrigger>
            <TabsTrigger value="users" className="rounded-full data-[state=active]:bg-purple-600 text-white">
              <FiUsers className="w-4 h-4 mr-2" /> Users ({users.length})
            </TabsTrigger>
            <TabsTrigger value="analytics" className="rounded-full data-[state=active]:bg-purple-600 text-white">
              <FiBarChart2 className="w-4 h-4 mr-2" /> Analytics
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
            {/* User Search */}
            <div className="mb-4 p-4 bg-white/5 rounded-xl border border-white/10">
              <div className="relative max-w-md">
                <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40 w-4 h-4" />
                <Input
                  placeholder="Search users by name or email..."
                  value={userSearchQuery}
                  onChange={(e) => setUserSearchQuery(e.target.value)}
                  className="pl-10 bg-white/5 border-white/10 text-white placeholder:text-white/40"
                  data-testid="user-search-input"
                />
              </div>
            </div>
            
            <div className="bg-white/5 backdrop-blur rounded-2xl border border-white/10 overflow-hidden">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/10 text-left">
                    <th className="p-4 text-white/60 font-ui text-sm">Name</th>
                    <th className="p-4 text-white/60 font-ui text-sm">Email</th>
                    <th className="p-4 text-white/60 font-ui text-sm">Subscription</th>
                    <th className="p-4 text-white/60 font-ui text-sm">Credits</th>
                    <th className="p-4 text-white/60 font-ui text-sm">Joined</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredUsers.map((user) => (
                    <tr key={user.id} className="border-b border-white/5 hover:bg-white/5">
                      <td className="p-4 text-white font-medium">{user.name}</td>
                      <td className="p-4 text-white/70">{user.email}</td>
                      <td className="p-4">
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          user.subscription === 'pro' 
                            ? 'bg-purple-500/20 text-purple-400' 
                            : 'bg-white/10 text-white/60'
                        }`}>
                          {user.subscription || 'Free'}
                        </span>
                      </td>
                      <td className="p-4 text-white/70">{user.credits || 0}</td>
                      <td className="p-4 text-white/50 text-sm">
                        {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
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

          {/* Analytics Tab */}
          <TabsContent value="analytics">
            {analytics ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <Card className="bg-white/5 border-white/10">
                  <CardHeader>
                    <CardTitle className="text-white text-lg">Total Books</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-4xl font-bold text-blue-400">{analytics.total_books}</p>
                  </CardContent>
                </Card>
                <Card className="bg-white/5 border-white/10">
                  <CardHeader>
                    <CardTitle className="text-white text-lg">Published Books</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-4xl font-bold text-green-400">{analytics.published_books}</p>
                  </CardContent>
                </Card>
                <Card className="bg-white/5 border-white/10">
                  <CardHeader>
                    <CardTitle className="text-white text-lg">Total Users</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-4xl font-bold text-purple-400">{analytics.total_users}</p>
                  </CardContent>
                </Card>
                <Card className="bg-white/5 border-white/10">
                  <CardHeader>
                    <CardTitle className="text-white text-lg">Pro Users</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-4xl font-bold text-yellow-400">{analytics.pro_users}</p>
                  </CardContent>
                </Card>
                <Card className="bg-white/5 border-white/10">
                  <CardHeader>
                    <CardTitle className="text-white text-lg">Total Views</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-4xl font-bold text-cyan-400">{analytics.total_views || 0}</p>
                  </CardContent>
                </Card>
                <Card className="bg-white/5 border-white/10">
                  <CardHeader>
                    <CardTitle className="text-white text-lg">Total Reads</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-4xl font-bold text-pink-400">{analytics.total_reads || 0}</p>
                  </CardContent>
                </Card>
              </div>
            ) : (
              <div className="text-center py-12 text-white/60">
                <FiBarChart2 className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p>Loading analytics...</p>
              </div>
            )}
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
    </div>
  );
}
