import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import axios from 'axios';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription } from '@/components/ui/dialog';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { FiPlus, FiEdit2, FiTrash2, FiBook, FiEye, FiEyeOff, FiZap, FiStar, FiAward, FiCheck } from 'react-icons/fi';
import Navbar from '@/components/Navbar';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function Dashboard() {
  const { user, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [genres, setGenres] = useState([]);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isUpgradeOpen, setIsUpgradeOpen] = useState(false);
  const [newBook, setNewBook] = useState({
    title: '',
    description: '',
    genre: 'General',
    layout_mode: 'standard'
  });
  const [creating, setCreating] = useState(false);
  const [subscription, setSubscription] = useState('free');

  useEffect(() => {
    if (!authLoading && !user) {
      navigate('/auth', { state: { from: '/dashboard' } });
    }
  }, [user, authLoading, navigate]);

  useEffect(() => {
    if (user) {
      setSubscription(user.subscription || 'free');
      fetchMyBooks();
      fetchGenres();
    }
  }, [user]);

  const fetchMyBooks = async () => {
    try {
      const res = await axios.get(`${API}/books/my`);
      setBooks(res.data);
    } catch (error) {
      toast.error('Failed to load books');
    } finally {
      setLoading(false);
    }
  };

  const fetchGenres = async () => {
    try {
      const res = await axios.get(`${API}/genres`);
      setGenres(res.data.genres);
    } catch (error) {
      console.error('Error fetching genres:', error);
    }
  };

  const createBook = async (e) => {
    e.preventDefault();
    if (!newBook.title.trim()) {
      toast.error('Please enter a title');
      return;
    }
    
    setCreating(true);
    try {
      const res = await axios.post(`${API}/books`, newBook);
      toast.success('Book created!');
      setIsCreateOpen(false);
      setNewBook({ title: '', description: '', genre: 'General', layout_mode: 'standard' });
      navigate(`/editor/${res.data.id}`);
    } catch (error) {
      if (error.response?.status === 403) {
        toast.error('Pro subscription required to create books');
        setIsUpgradeOpen(true);
      } else {
        toast.error('Failed to create book');
      }
    } finally {
      setCreating(false);
    }
  };

  const handleUpgrade = async () => {
    try {
      await axios.post(`${API}/auth/upgrade`, { subscription: 'pro' });
      setSubscription('pro');
      toast.success('Upgraded to Pro! You can now create books.');
      setIsUpgradeOpen(false);
      // Refresh user data
      window.location.reload();
    } catch (error) {
      toast.error('Failed to upgrade');
    }
  };

  const togglePublish = async (book) => {
    try {
      await axios.put(`${API}/books/${book.id}`, {
        is_published: !book.is_published
      });
      toast.success(book.is_published ? 'Book unpublished' : 'Book published!');
      fetchMyBooks();
    } catch (error) {
      toast.error('Failed to update book');
    }
  };

  const toggleFeatured = async (book) => {
    try {
      await axios.post(`${API}/admin/books/${book.id}/feature`);
      toast.success(book.is_featured ? 'Removed from featured' : 'Added to featured!');
      fetchMyBooks();
    } catch (error) {
      toast.error('Failed to update');
    }
  };

  const toggleBestOfWeek = async (book) => {
    try {
      await axios.post(`${API}/admin/books/${book.id}/best-of-week`);
      toast.success(book.is_best_of_week ? 'Removed from best of week' : 'Added to best of week!');
      fetchMyBooks();
    } catch (error) {
      toast.error('Failed to update');
    }
  };

  const deleteBook = async (bookId) => {
    if (!window.confirm('Are you sure you want to delete this book?')) return;
    
    try {
      await axios.delete(`${API}/books/${bookId}`);
      toast.success('Book deleted');
      fetchMyBooks();
    } catch (error) {
      toast.error('Failed to delete book');
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!user) {
    return null;
  }

  const isPro = subscription === 'pro';

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <div className="pt-28 pb-12 px-6 md:px-12">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-10"
          >
            <div>
              <div className="flex items-center gap-3 mb-2">
                <h1 className="font-heading text-4xl md:text-5xl font-bold">
                  My Books
                </h1>
                <span className={`px-3 py-1 rounded-full text-sm font-ui ${
                  isPro 
                    ? 'bg-secondary/20 text-secondary' 
                    : 'bg-muted text-muted-foreground'
                }`}>
                  {isPro ? 'Pro' : 'Free'}
                </span>
              </div>
              <p className="font-body text-lg text-muted-foreground">
                Welcome back, {user.name}! {isPro ? 'Create and manage your stories.' : 'Upgrade to Pro to start creating!'}
              </p>
            </div>
            
            <div className="flex gap-3">
              {!isPro && (
                <Button 
                  variant="outline"
                  className="rounded-full px-6 py-6 font-ui border-secondary text-secondary hover:bg-secondary hover:text-secondary-foreground"
                  onClick={() => setIsUpgradeOpen(true)}
                  data-testid="upgrade-to-pro-btn"
                >
                  <FiZap className="mr-2" />
                  Upgrade to Pro
                </Button>
              )}
              
              <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
                <DialogTrigger asChild>
                  <Button 
                    className="rounded-full px-6 py-6 font-ui text-lg"
                    data-testid="create-book-btn"
                    disabled={!isPro}
                  >
                    <FiPlus className="mr-2" />
                    New Book
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-md">
                  <DialogHeader>
                    <DialogTitle className="font-heading text-2xl">Create New Book</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={createBook} className="space-y-5 pt-4">
                    <div className="space-y-2">
                      <Label htmlFor="title" className="font-ui">Title</Label>
                      <Input
                        id="title"
                        value={newBook.title}
                        onChange={(e) => setNewBook({ ...newBook, title: e.target.value })}
                        placeholder="My Amazing Story"
                        className="rounded-full border-2"
                        data-testid="new-book-title"
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="description" className="font-ui">Description</Label>
                      <Textarea
                        id="description"
                        value={newBook.description}
                        onChange={(e) => setNewBook({ ...newBook, description: e.target.value })}
                        placeholder="A brief description of your story..."
                        className="rounded-2xl border-2 min-h-24"
                        data-testid="new-book-description"
                      />
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="genre" className="font-ui">Genre</Label>
                        <Select 
                          value={newBook.genre} 
                          onValueChange={(v) => setNewBook({ ...newBook, genre: v })}
                        >
                          <SelectTrigger 
                            className="rounded-full border-2"
                            data-testid="new-book-genre"
                          >
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {genres.map((g) => (
                              <SelectItem key={g} value={g}>{g}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      
                      <div className="space-y-2">
                        <Label htmlFor="layout" className="font-ui">Layout</Label>
                        <Select 
                          value={newBook.layout_mode} 
                          onValueChange={(v) => setNewBook({ ...newBook, layout_mode: v })}
                        >
                          <SelectTrigger 
                            className="rounded-full border-2"
                            data-testid="new-book-layout"
                          >
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="standard">Standard Book</SelectItem>
                            <SelectItem value="comic">Comic Book</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    
                    <Button 
                      type="submit" 
                      className="w-full rounded-full"
                      disabled={creating}
                      data-testid="submit-new-book"
                    >
                      {creating ? 'Creating...' : 'Create Book'}
                    </Button>
                  </form>
                </DialogContent>
              </Dialog>
            </div>
          </motion.div>
          
          {/* Upgrade Dialog */}
          <Dialog open={isUpgradeOpen} onOpenChange={setIsUpgradeOpen}>
            <DialogContent className="sm:max-w-lg">
              <DialogHeader>
                <DialogTitle className="font-heading text-2xl flex items-center gap-2">
                  <FiZap className="text-secondary" />
                  Upgrade to Pro
                </DialogTitle>
                <DialogDescription className="font-body">
                  Unlock the full power of Azories and start creating your own magical stories!
                </DialogDescription>
              </DialogHeader>
              <div className="pt-4 space-y-6">
                <div className="space-y-4">
                  {[
                    'Create unlimited books',
                    'AI-powered image generation',
                    'AI video generation with Sora',
                    'Multiple narrator voices',
                    'Comic book layouts',
                    'Feature your books in the library'
                  ].map((feature) => (
                    <div key={feature} className="flex items-center gap-3">
                      <div className="w-6 h-6 rounded-full bg-accent/20 flex items-center justify-center">
                        <FiCheck className="w-4 h-4 text-accent" />
                      </div>
                      <span className="font-body">{feature}</span>
                    </div>
                  ))}
                </div>
                
                <div className="p-4 rounded-2xl bg-muted/50 text-center">
                  <p className="text-sm text-muted-foreground mb-2">Test Mode Pricing</p>
                  <p className="font-heading text-3xl font-bold">Free</p>
                  <p className="text-sm text-muted-foreground">(For testing only)</p>
                </div>
                
                <Button 
                  onClick={handleUpgrade}
                  className="w-full rounded-full py-6 text-lg font-ui bg-secondary hover:bg-secondary/90"
                  data-testid="confirm-upgrade-btn"
                >
                  <FiZap className="mr-2" />
                  Upgrade Now
                </Button>
              </div>
            </DialogContent>
          </Dialog>
          
          {/* Books Grid */}
          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(3)].map((_, i) => (
                <Card key={i} className="shimmer h-64" />
              ))}
            </div>
          ) : books.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {books.map((book, index) => (
                <motion.div
                  key={book.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                >
                  <Card 
                    className="group hover:shadow-lg transition-shadow duration-300"
                    data-testid={`dashboard-book-${book.id}`}
                  >
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <CardTitle className="font-heading text-xl line-clamp-1">
                            {book.title}
                          </CardTitle>
                          <CardDescription className="font-body mt-1 line-clamp-2">
                            {book.description || 'No description'}
                          </CardDescription>
                        </div>
                        <div className="flex flex-col gap-1">
                          <span className={`px-3 py-1 rounded-full text-xs font-ui ${
                            book.is_published 
                              ? 'bg-accent/20 text-accent-foreground' 
                              : 'bg-muted text-muted-foreground'
                          }`}>
                            {book.is_published ? 'Published' : 'Draft'}
                          </span>
                          {book.layout_mode === 'comic' && (
                            <span className="px-3 py-1 rounded-full text-xs font-ui bg-secondary/20 text-secondary">
                              Comic
                            </span>
                          )}
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground mb-4">
                        <span className="font-ui">{book.chapter_count} chapters</span>
                        <span className="font-ui">{book.total_pages} pages</span>
                        <span className="px-2 py-1 rounded bg-primary/10 text-primary text-xs font-ui">
                          {book.genre}
                        </span>
                      </div>
                      
                      <div className="flex items-center gap-2 flex-wrap">
                        <Button
                          variant="default"
                          size="sm"
                          className="rounded-full flex-1"
                          onClick={() => navigate(`/editor/${book.id}`)}
                          data-testid={`edit-book-${book.id}`}
                        >
                          <FiEdit2 className="mr-2 w-4 h-4" />
                          Edit
                        </Button>
                        <Button
                          variant="outline"
                          size="icon"
                          className="rounded-full"
                          onClick={() => togglePublish(book)}
                          data-testid={`publish-book-${book.id}`}
                        >
                          {book.is_published ? <FiEyeOff className="w-4 h-4" /> : <FiEye className="w-4 h-4" />}
                        </Button>
                        <Button
                          variant="outline"
                          size="icon"
                          className={`rounded-full ${book.is_featured ? 'bg-primary/10 border-primary' : ''}`}
                          onClick={() => toggleFeatured(book)}
                          data-testid={`feature-book-${book.id}`}
                        >
                          <FiStar className={`w-4 h-4 ${book.is_featured ? 'text-primary fill-primary' : ''}`} />
                        </Button>
                        <Button
                          variant="outline"
                          size="icon"
                          className={`rounded-full ${book.is_best_of_week ? 'bg-secondary/10 border-secondary' : ''}`}
                          onClick={() => toggleBestOfWeek(book)}
                          data-testid={`best-week-book-${book.id}`}
                        >
                          <FiAward className={`w-4 h-4 ${book.is_best_of_week ? 'text-secondary fill-secondary' : ''}`} />
                        </Button>
                        <Button
                          variant="outline"
                          size="icon"
                          className="rounded-full text-destructive hover:bg-destructive hover:text-destructive-foreground"
                          onClick={() => deleteBook(book.id)}
                          data-testid={`delete-book-${book.id}`}
                        >
                          <FiTrash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          ) : (
            <div className="text-center py-20">
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="space-y-4"
              >
                <div className="w-20 h-20 mx-auto rounded-full bg-primary/10 flex items-center justify-center">
                  <FiBook className="w-10 h-10 text-primary" />
                </div>
                <h3 className="font-heading text-2xl">No books yet</h3>
                <p className="font-body text-muted-foreground max-w-md mx-auto">
                  {isPro 
                    ? 'Start your storytelling journey by creating your first book!'
                    : 'Upgrade to Pro to start creating your own magical stories!'}
                </p>
                {isPro ? (
                  <Button 
                    className="rounded-full mt-4"
                    onClick={() => setIsCreateOpen(true)}
                    data-testid="create-first-book"
                  >
                    <FiPlus className="mr-2" />
                    Create Your First Book
                  </Button>
                ) : (
                  <Button 
                    className="rounded-full mt-4 bg-secondary hover:bg-secondary/90"
                    onClick={() => setIsUpgradeOpen(true)}
                    data-testid="upgrade-first"
                  >
                    <FiZap className="mr-2" />
                    Upgrade to Pro
                  </Button>
                )}
              </motion.div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
