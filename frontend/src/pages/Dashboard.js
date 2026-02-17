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
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { FiPlus, FiEdit2, FiTrash2, FiBook, FiEye, FiEyeOff, FiLogIn } from 'react-icons/fi';
import Navbar from '@/components/Navbar';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function Dashboard() {
  const { user, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [genres, setGenres] = useState([]);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newBook, setNewBook] = useState({
    title: '',
    description: '',
    genre: 'General'
  });
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (!authLoading && !user) {
      navigate('/auth', { state: { from: '/dashboard' } });
    }
  }, [user, authLoading, navigate]);

  useEffect(() => {
    if (user) {
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
      setNewBook({ title: '', description: '', genre: 'General' });
      navigate(`/editor/${res.data.id}`);
    } catch (error) {
      toast.error('Failed to create book');
    } finally {
      setCreating(false);
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
              <h1 className="font-heading text-4xl md:text-5xl font-bold mb-2">
                My Books
              </h1>
              <p className="font-body text-lg text-muted-foreground">
                Welcome back, {user.name}! Create and manage your stories.
              </p>
            </div>
            
            <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
              <DialogTrigger asChild>
                <Button 
                  className="rounded-full px-6 py-6 font-ui text-lg"
                  data-testid="create-book-btn"
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
          </motion.div>
          
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
                    className="group hover:shadow-lg transition-shadow duration-300 cursor-pointer"
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
                        <span className={`px-3 py-1 rounded-full text-xs font-ui ${
                          book.is_published 
                            ? 'bg-accent/20 text-accent-foreground' 
                            : 'bg-muted text-muted-foreground'
                        }`}>
                          {book.is_published ? 'Published' : 'Draft'}
                        </span>
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
                      
                      <div className="flex items-center gap-2">
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
                  Start your storytelling journey by creating your first book!
                </p>
                <Button 
                  className="rounded-full mt-4"
                  onClick={() => setIsCreateOpen(true)}
                  data-testid="create-first-book"
                >
                  <FiPlus className="mr-2" />
                  Create Your First Book
                </Button>
              </motion.div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
