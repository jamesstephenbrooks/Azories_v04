import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  FiBook, FiUsers, FiBarChart2, FiStar, FiAward, FiTrash2, 
  FiEye, FiEyeOff, FiLock, FiLogOut, FiRefreshCw, FiDatabase
} from 'react-icons/fi';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AdminCMS() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [books, setBooks] = useState([]);
  const [users, setUsers] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [adminName, setAdminName] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('admin_token');
    if (token) {
      verifyToken(token);
    }
  }, []);

  const verifyToken = async (token) => {
    try {
      await axios.get(`${API}/admin/verify`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setIsAuthenticated(true);
      setAdminName(localStorage.getItem('admin_name') || 'Admin');
      fetchAllData(token);
    } catch {
      localStorage.removeItem('admin_token');
      localStorage.removeItem('admin_name');
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await axios.post(`${API}/admin/login`, { username, password });
      localStorage.setItem('admin_token', res.data.access_token);
      localStorage.setItem('admin_name', res.data.admin_name);
      setIsAuthenticated(true);
      setAdminName(res.data.admin_name);
      toast.success('Welcome to Admin CMS');
      fetchAllData(res.data.access_token);
    } catch (error) {
      toast.error('Invalid admin credentials');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_name');
    setIsAuthenticated(false);
    setBooks([]);
    setUsers([]);
    setAnalytics(null);
  };

  const getAuthHeaders = () => ({
    headers: { Authorization: `Bearer ${localStorage.getItem('admin_token')}` }
  });

  const fetchAllData = async (token) => {
    const headers = { headers: { Authorization: `Bearer ${token}` } };
    try {
      const [booksRes, usersRes, analyticsRes] = await Promise.all([
        axios.get(`${API}/admin/books`, headers),
        axios.get(`${API}/admin/users`, headers),
        axios.get(`${API}/admin/analytics`, headers)
      ]);
      setBooks(booksRes.data);
      setUsers(usersRes.data);
      setAnalytics(analyticsRes.data);
    } catch (error) {
      toast.error('Failed to fetch data');
    }
  };

  const toggleFeatured = async (bookId) => {
    try {
      const res = await axios.post(`${API}/admin/books/${bookId}/feature`, {}, getAuthHeaders());
      setBooks(books.map(b => b.id === bookId ? { ...b, is_featured: res.data.is_featured } : b));
      toast.success(res.data.is_featured ? 'Book featured' : 'Book unfeatured');
    } catch {
      toast.error('Failed to update');
    }
  };

  const toggleBestOfWeek = async (bookId) => {
    try {
      const res = await axios.post(`${API}/admin/books/${bookId}/best-of-week`, {}, getAuthHeaders());
      setBooks(books.map(b => b.id === bookId ? { ...b, is_best_of_week: res.data.is_best_of_week } : b));
      toast.success(res.data.is_best_of_week ? 'Added to Best of Week' : 'Removed from Best of Week');
    } catch {
      toast.error('Failed to update');
    }
  };

  const togglePublish = async (bookId) => {
    try {
      const res = await axios.post(`${API}/admin/books/${bookId}/publish`, {}, getAuthHeaders());
      setBooks(books.map(b => b.id === bookId ? { ...b, is_published: res.data.is_published } : b));
      toast.success(res.data.is_published ? 'Book published' : 'Book unpublished');
    } catch {
      toast.error('Failed to update');
    }
  };

  const deleteBook = async (bookId, title) => {
    if (!window.confirm(`Delete "${title}"? This cannot be undone.`)) return;
    try {
      await axios.delete(`${API}/admin/books/${bookId}`, getAuthHeaders());
      setBooks(books.filter(b => b.id !== bookId));
      toast.success('Book deleted');
    } catch {
      toast.error('Failed to delete');
    }
  };

  const seedTestBooks = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/admin/seed-test-books`, {}, getAuthHeaders());
      toast.success(res.data.message);
      fetchAllData(localStorage.getItem('admin_token'));
    } catch (error) {
      toast.error('Failed to seed test books');
    } finally {
      setLoading(false);
    }
  };

  // Login Form
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-md"
        >
          <div className="bg-card/90 backdrop-blur-xl rounded-3xl p-8 shadow-2xl border border-white/10">
            <div className="text-center mb-8">
              <div className="w-16 h-16 bg-primary/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <FiLock className="w-8 h-8 text-primary" />
              </div>
              <h1 className="font-heading text-2xl font-bold">Admin Access</h1>
              <p className="text-muted-foreground font-body text-sm mt-2">
                Azories Content Management System
              </p>
            </div>
            
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter admin username"
                  className="mt-1"
                  data-testid="admin-username"
                  required
                />
              </div>
              <div>
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter admin password"
                  className="mt-1"
                  data-testid="admin-password"
                  required
                />
              </div>
              <Button 
                type="submit" 
                className="w-full rounded-full"
                disabled={loading}
                data-testid="admin-login-btn"
              >
                {loading ? 'Authenticating...' : 'Access Admin Panel'}
              </Button>
            </form>
            
            <div className="mt-6 text-center">
              <button 
                onClick={() => navigate('/')}
                className="text-sm text-muted-foreground hover:text-primary transition-colors"
              >
                ← Back to Azories
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    );
  }

  // Admin Dashboard
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <header className="border-b border-white/10 bg-black/20 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 bg-primary/20 rounded-xl flex items-center justify-center">
              <FiLock className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h1 className="font-heading font-bold text-white">Azories Admin</h1>
              <p className="text-xs text-white/60">Welcome, {adminName}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => fetchAllData(localStorage.getItem('admin_token'))}
              className="rounded-full"
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
        {analytics && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white/5 backdrop-blur rounded-2xl p-4 border border-white/10">
              <FiBook className="w-8 h-8 text-blue-400 mb-2" />
              <p className="text-2xl font-bold text-white">{analytics.total_books}</p>
              <p className="text-sm text-white/60">Total Books</p>
            </div>
            <div className="bg-white/5 backdrop-blur rounded-2xl p-4 border border-white/10">
              <FiEye className="w-8 h-8 text-green-400 mb-2" />
              <p className="text-2xl font-bold text-white">{analytics.published_books}</p>
              <p className="text-sm text-white/60">Published</p>
            </div>
            <div className="bg-white/5 backdrop-blur rounded-2xl p-4 border border-white/10">
              <FiUsers className="w-8 h-8 text-purple-400 mb-2" />
              <p className="text-2xl font-bold text-white">{analytics.total_users}</p>
              <p className="text-sm text-white/60">Total Users</p>
            </div>
            <div className="bg-white/5 backdrop-blur rounded-2xl p-4 border border-white/10">
              <FiStar className="w-8 h-8 text-yellow-400 mb-2" />
              <p className="text-2xl font-bold text-white">{analytics.pro_users}</p>
              <p className="text-sm text-white/60">Pro Users</p>
            </div>
          </div>
        )}

        {/* Tabs */}
        <Tabs defaultValue="books" className="space-y-6">
          <TabsList className="bg-white/5 border border-white/10 p-1 rounded-full">
            <TabsTrigger value="books" className="rounded-full data-[state=active]:bg-primary">
              <FiBook className="w-4 h-4 mr-2" /> Books ({books.length})
            </TabsTrigger>
            <TabsTrigger value="users" className="rounded-full data-[state=active]:bg-primary">
              <FiUsers className="w-4 h-4 mr-2" /> Users ({users.length})
            </TabsTrigger>
            <TabsTrigger value="analytics" className="rounded-full data-[state=active]:bg-primary">
              <FiBarChart2 className="w-4 h-4 mr-2" /> Analytics
            </TabsTrigger>
          </TabsList>

          {/* Books Tab */}
          <TabsContent value="books" className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-heading font-bold text-white">All Books</h2>
              <Button
                onClick={seedTestBooks}
                disabled={loading}
                variant="outline"
                className="rounded-full"
              >
                <FiDatabase className="w-4 h-4 mr-2" />
                {loading ? 'Seeding...' : 'Seed Test Books'}
              </Button>
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
                  {books.map((book) => (
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
                          {book.is_published && (
                            <span className="text-xs text-green-400">Published</span>
                          )}
                          {book.is_featured && (
                            <span className="text-xs text-yellow-400">Featured</span>
                          )}
                          {book.is_best_of_week && (
                            <span className="text-xs text-purple-400">Best of Week</span>
                          )}
                          {!book.is_published && (
                            <span className="text-xs text-white/40">Draft</span>
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
              {books.length === 0 && (
                <div className="p-8 text-center text-white/40">
                  No books found. Click "Seed Test Books" to add sample data.
                </div>
              )}
            </div>
          </TabsContent>

          {/* Users Tab */}
          <TabsContent value="users" className="space-y-4">
            <h2 className="text-xl font-heading font-bold text-white">All Users</h2>
            <div className="bg-white/5 backdrop-blur rounded-2xl border border-white/10 overflow-hidden">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/10 text-left">
                    <th className="p-4 text-white/60 font-ui text-sm">Name</th>
                    <th className="p-4 text-white/60 font-ui text-sm">Email</th>
                    <th className="p-4 text-white/60 font-ui text-sm">Role</th>
                    <th className="p-4 text-white/60 font-ui text-sm">Subscription</th>
                    <th className="p-4 text-white/60 font-ui text-sm">Joined</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => (
                    <tr key={user.id} className="border-b border-white/5 hover:bg-white/5">
                      <td className="p-4 text-white font-medium">{user.name}</td>
                      <td className="p-4 text-white/70">{user.email}</td>
                      <td className="p-4">
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          user.role === 'admin' ? 'bg-red-500/20 text-red-400' : 'bg-white/10 text-white/70'
                        }`}>
                          {user.role}
                        </span>
                      </td>
                      <td className="p-4">
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          user.subscription === 'pro' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-white/10 text-white/70'
                        }`}>
                          {user.subscription}
                        </span>
                      </td>
                      <td className="p-4 text-white/50 text-sm">
                        {new Date(user.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {users.length === 0 && (
                <div className="p-8 text-center text-white/40">No users found.</div>
              )}
            </div>
          </TabsContent>

          {/* Analytics Tab */}
          <TabsContent value="analytics" className="space-y-4">
            <h2 className="text-xl font-heading font-bold text-white">Platform Analytics</h2>
            
            {analytics && (
              <div className="space-y-6">
                <div className="bg-white/5 backdrop-blur rounded-2xl border border-white/10 p-6">
                  <h3 className="text-lg font-heading font-bold text-white mb-4">Top Books by Reads</h3>
                  {analytics.top_books.length > 0 ? (
                    <div className="space-y-3">
                      {analytics.top_books.map((book, index) => (
                        <div key={book.id} className="flex items-center gap-4 p-3 bg-white/5 rounded-xl">
                          <span className="w-8 h-8 rounded-full bg-primary/20 text-primary flex items-center justify-center font-bold">
                            {index + 1}
                          </span>
                          <span className="flex-1 text-white">{book.title}</span>
                          <span className="text-white/60">{book.reads} reads</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-white/40">No read data yet.</p>
                  )}
                </div>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
