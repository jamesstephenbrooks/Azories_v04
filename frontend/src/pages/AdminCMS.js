import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import axios from 'axios';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { toast } from 'sonner';
import { 
  FiArrowLeft, FiStar, FiAward, FiTrash2, FiUsers, FiBook, 
  FiTrendingUp, FiEye, FiShield, FiBarChart2
} from 'react-icons/fi';
import Navbar from '@/components/Navbar';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const AGE_RATINGS = ["All Ages", "5+", "8+", "12+", "16+"];

export default function AdminCMS() {
  const { user, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  
  const [books, setBooks] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedBook, setSelectedBook] = useState(null);

  useEffect(() => {
    if (!authLoading) {
      if (!user) {
        navigate('/auth');
      } else if (user.role !== 'admin') {
        toast.error('Admin access required');
        navigate('/dashboard');
      }
    }
  }, [user, authLoading, navigate]);

  useEffect(() => {
    if (user?.role === 'admin') {
      fetchBooks();
      fetchAnalytics();
    }
  }, [user]);

  const fetchBooks = async () => {
    try {
      const res = await axios.get(`${API}/admin/books`);
      setBooks(res.data);
    } catch (error) {
      toast.error('Failed to load books');
    } finally {
      setLoading(false);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const res = await axios.get(`${API}/admin/analytics`);
      setAnalytics(res.data);
    } catch (error) {
      console.error('Failed to load analytics');
    }
  };

  const toggleFeatured = async (bookId) => {
    try {
      const res = await axios.post(`${API}/admin/books/${bookId}/feature`);
      toast.success(res.data.is_featured ? 'Added to Featured' : 'Removed from Featured');
      fetchBooks();
    } catch (error) {
      toast.error('Failed to update');
    }
  };

  const toggleBestOfWeek = async (bookId) => {
    try {
      const res = await axios.post(`${API}/admin/books/${bookId}/best-of-week`);
      toast.success(res.data.is_best_of_week ? 'Added to Best of Week' : 'Removed from Best of Week');
      fetchBooks();
    } catch (error) {
      toast.error('Failed to update');
    }
  };

  const setAgeRating = async (bookId, rating) => {
    try {
      await axios.post(`${API}/admin/books/${bookId}/age-rating?age_rating=${rating}`);
      toast.success(`Age rating set to ${rating}`);
      fetchBooks();
    } catch (error) {
      toast.error('Failed to update age rating');
    }
  };

  const deleteBook = async (bookId) => {
    if (!window.confirm('Are you sure you want to delete this book?')) return;
    
    try {
      await axios.delete(`${API}/admin/books/${bookId}`);
      toast.success('Book deleted');
      fetchBooks();
    } catch (error) {
      toast.error('Failed to delete book');
    }
  };

  const filteredBooks = books.filter(book => 
    book.title.toLowerCase().includes(search.toLowerCase()) ||
    book.author_name.toLowerCase().includes(search.toLowerCase())
  );

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (user?.role !== 'admin') {
    return null;
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <div className="pt-28 pb-12 px-6 md:px-12">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="flex items-center gap-4 mb-8">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate('/dashboard')}
              className="rounded-full"
            >
              <FiArrowLeft className="w-5 h-5" />
            </Button>
            <div>
              <h1 className="font-heading text-4xl font-bold flex items-center gap-3">
                <FiShield className="text-primary" />
                Admin CMS
              </h1>
              <p className="font-body text-muted-foreground">
                Manage books, featured content, and platform settings
              </p>
            </div>
          </div>
          
          {/* Analytics Cards */}
          {analytics && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                      <FiBook className="w-6 h-6 text-primary" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold">{analytics.total_books}</p>
                      <p className="text-sm text-muted-foreground">Total Books</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-full bg-accent/10 flex items-center justify-center">
                      <FiEye className="w-6 h-6 text-accent" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold">{analytics.published_books}</p>
                      <p className="text-sm text-muted-foreground">Published</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-full bg-secondary/10 flex items-center justify-center">
                      <FiUsers className="w-6 h-6 text-secondary" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold">{analytics.total_users}</p>
                      <p className="text-sm text-muted-foreground">Users</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                      <FiTrendingUp className="w-6 h-6 text-primary" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold">{analytics.pro_users}</p>
                      <p className="text-sm text-muted-foreground">Pro Users</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
          
          {/* Top Books */}
          {analytics?.top_books?.length > 0 && (
            <Card className="mb-8">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FiBarChart2 className="text-primary" />
                  Top Books by Reads
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {analytics.top_books.map((book, idx) => (
                    <div key={book.id} className="flex items-center justify-between p-2 rounded-lg hover:bg-muted">
                      <div className="flex items-center gap-3">
                        <span className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center text-sm font-bold text-primary">
                          {idx + 1}
                        </span>
                        <span className="font-ui">{book.title}</span>
                      </div>
                      <span className="text-muted-foreground">{book.reads} reads</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
          
          {/* Search */}
          <div className="mb-6">
            <Input
              placeholder="Search books by title or author..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="max-w-md rounded-full border-2"
            />
          </div>
          
          {/* Books Table */}
          <Card>
            <CardHeader>
              <CardTitle>All Books ({filteredBooks.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-3 font-ui">Title</th>
                      <th className="text-left p-3 font-ui">Author</th>
                      <th className="text-left p-3 font-ui">Status</th>
                      <th className="text-left p-3 font-ui">Age Rating</th>
                      <th className="text-left p-3 font-ui">Views</th>
                      <th className="text-left p-3 font-ui">Reads</th>
                      <th className="text-left p-3 font-ui">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredBooks.map((book) => (
                      <tr key={book.id} className="border-b hover:bg-muted/50">
                        <td className="p-3">
                          <span className="font-semibold">{book.title}</span>
                          <div className="flex gap-1 mt-1">
                            {book.is_featured && (
                              <span className="text-xs px-2 py-0.5 rounded bg-primary/10 text-primary">Featured</span>
                            )}
                            {book.is_best_of_week && (
                              <span className="text-xs px-2 py-0.5 rounded bg-secondary/10 text-secondary">Best of Week</span>
                            )}
                          </div>
                        </td>
                        <td className="p-3 text-muted-foreground">{book.author_name}</td>
                        <td className="p-3">
                          <span className={`px-2 py-1 rounded text-xs ${
                            book.is_published ? 'bg-accent/20 text-accent-foreground' : 'bg-muted text-muted-foreground'
                          }`}>
                            {book.is_published ? 'Published' : 'Draft'}
                          </span>
                        </td>
                        <td className="p-3">
                          <Select 
                            value={book.age_rating || 'All Ages'} 
                            onValueChange={(v) => setAgeRating(book.id, v)}
                          >
                            <SelectTrigger className="w-28 h-8 text-xs">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {AGE_RATINGS.map(rating => (
                                <SelectItem key={rating} value={rating}>{rating}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </td>
                        <td className="p-3 text-muted-foreground">{book.view_count || 0}</td>
                        <td className="p-3 text-muted-foreground">{book.read_count || 0}</td>
                        <td className="p-3">
                          <div className="flex gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              className={`w-8 h-8 rounded-full ${book.is_featured ? 'bg-primary/10' : ''}`}
                              onClick={() => toggleFeatured(book.id)}
                              title="Toggle Featured"
                            >
                              <FiStar className={`w-4 h-4 ${book.is_featured ? 'text-primary fill-primary' : ''}`} />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className={`w-8 h-8 rounded-full ${book.is_best_of_week ? 'bg-secondary/10' : ''}`}
                              onClick={() => toggleBestOfWeek(book.id)}
                              title="Toggle Best of Week"
                            >
                              <FiAward className={`w-4 h-4 ${book.is_best_of_week ? 'text-secondary fill-secondary' : ''}`} />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="w-8 h-8 rounded-full text-destructive hover:bg-destructive hover:text-destructive-foreground"
                              onClick={() => deleteBook(book.id)}
                              title="Delete Book"
                            >
                              <FiTrash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              {filteredBooks.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  No books found
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
