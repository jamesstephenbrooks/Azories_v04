import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import axios from 'axios';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription } from '@/components/ui/dialog';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { 
  FiPlus, FiEdit2, FiTrash2, FiBook, FiArrowLeft, FiLoader, 
  FiLayers, FiChevronUp, FiChevronDown, FiGlobe, FiImage, FiX
} from 'react-icons/fi';
import Navbar from '@/components/Navbar';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function MySeries() {
  const { user, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  
  const [series, setSeries] = useState([]);
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingSeries, setEditingSeries] = useState(null);
  const [newSeries, setNewSeries] = useState({ name: '', description: '' });
  const [creatingSeries, setCreatingSeries] = useState(false);

  useEffect(() => {
    if (!authLoading && !user && !localStorage.getItem('azories-token')) {
      navigate('/auth', { state: { from: '/series' } });
    }
  }, [user, authLoading, navigate]);

  useEffect(() => {
    if (user) {
      fetchSeries();
      fetchBooks();
    }
  }, [user]);

  const fetchSeries = async () => {
    const token = localStorage.getItem('azories-token');
    try {
      const res = await axios.get(`${API}/series`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSeries(res.data);
    } catch (error) {
      toast.error('Failed to load series');
    } finally {
      setLoading(false);
    }
  };

  const fetchBooks = async () => {
    const token = localStorage.getItem('azories-token');
    try {
      const res = await axios.get(`${API}/books/my`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setBooks(res.data);
    } catch (error) {
      console.error('Failed to load books');
    }
  };

  const createSeries = async () => {
    if (!newSeries.name.trim()) {
      toast.error('Please enter a series name');
      return;
    }
    
    setCreatingSeries(true);
    const token = localStorage.getItem('azories-token');
    try {
      await axios.post(`${API}/series`, newSeries, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Series created!');
      setNewSeries({ name: '', description: '' });
      setIsCreateOpen(false);
      fetchSeries();
    } catch (error) {
      toast.error('Failed to create series');
    } finally {
      setCreatingSeries(false);
    }
  };

  const updateSeries = async () => {
    if (!editingSeries?.name.trim()) {
      toast.error('Please enter a series name');
      return;
    }
    
    const token = localStorage.getItem('azories-token');
    try {
      await axios.put(`${API}/series/${editingSeries.id}`, {
        name: editingSeries.name,
        description: editingSeries.description
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Series updated!');
      setEditingSeries(null);
      fetchSeries();
    } catch (error) {
      toast.error('Failed to update series');
    }
  };

  const deleteSeries = async (seriesId) => {
    if (!window.confirm('Delete this series? Books will be unlinked but not deleted.')) return;
    
    const token = localStorage.getItem('azories-token');
    try {
      await axios.delete(`${API}/series/${seriesId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Series deleted');
      fetchSeries();
    } catch (error) {
      toast.error('Failed to delete series');
    }
  };

  const addBookToSeries = async (seriesId, bookId) => {
    const token = localStorage.getItem('azories-token');
    try {
      await axios.post(`${API}/series/${seriesId}/books/${bookId}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Book added to series!');
      fetchSeries();
      fetchBooks();
    } catch (error) {
      toast.error('Failed to add book to series');
    }
  };

  const removeBookFromSeries = async (seriesId, bookId) => {
    const token = localStorage.getItem('azories-token');
    try {
      await axios.delete(`${API}/series/${seriesId}/books/${bookId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Book removed from series');
      fetchSeries();
      fetchBooks();
    } catch (error) {
      toast.error('Failed to remove book');
    }
  };

  const reorderBook = async (seriesId, bookId, currentIndex, newIndex) => {
    const token = localStorage.getItem('azories-token');
    try {
      await axios.put(`${API}/series/${seriesId}/books/${bookId}/order`, {
        new_order: newIndex + 1
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchSeries();
    } catch (error) {
      toast.error('Failed to reorder book');
    }
  };

  const publishAllInSeries = async (seriesId) => {
    if (!window.confirm('Submit all books in this series for review?')) return;
    
    const token = localStorage.getItem('azories-token');
    const seriesData = series.find(s => s.id === seriesId);
    if (!seriesData?.books) return;
    
    try {
      let submitted = 0;
      for (const book of seriesData.books) {
        if (!book.is_published && book.publish_status !== 'pending_review') {
          await axios.post(`${API}/books/${book.id}/request-publish`, {}, {
            headers: { Authorization: `Bearer ${token}` }
          });
          submitted++;
        }
      }
      if (submitted > 0) {
        toast.success(`${submitted} book(s) submitted for admin review!`);
      } else {
        toast.info('All books are already published or coming soon');
      }
      fetchSeries();
      fetchBooks();
    } catch (error) {
      toast.error('Failed to submit some books for review');
    }
  };

  const getBooksNotInSeries = (seriesId) => {
    return books.filter(book => book.series_id !== seriesId);
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <div className="pt-32 pb-12 px-6 md:px-12">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-10"
          >
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => navigate('/dashboard')}
                className="rounded-full"
                data-testid="back-to-dashboard"
              >
                <FiArrowLeft className="w-5 h-5" />
              </Button>
              <div>
                <h1 className="font-heading text-4xl md:text-5xl font-bold flex items-center gap-3">
                  <FiLayers className="text-primary" />
                  My Series
                </h1>
                <p className="font-body text-lg text-muted-foreground mt-1">
                  Organize your books into series collections
                </p>
              </div>
            </div>
            
            <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
              <DialogTrigger asChild>
                <Button className="rounded-full px-6 py-6 font-ui text-lg" data-testid="create-series-btn">
                  <FiPlus className="mr-2" />
                  New Series
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-md">
                <DialogHeader>
                  <DialogTitle className="font-heading text-2xl">Create New Series</DialogTitle>
                  <DialogDescription>
                    Group your books into a series for readers to follow
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 pt-4">
                  <div className="space-y-2">
                    <Label className="font-ui">Series Name</Label>
                    <Input
                      value={newSeries.name}
                      onChange={(e) => setNewSeries({ ...newSeries, name: e.target.value })}
                      placeholder="The Dragon Chronicles"
                      className="rounded-full border-2"
                      data-testid="series-name-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="font-ui">Description (optional)</Label>
                    <Textarea
                      value={newSeries.description}
                      onChange={(e) => setNewSeries({ ...newSeries, description: e.target.value })}
                      placeholder="An epic adventure series about..."
                      className="rounded-2xl border-2 min-h-20"
                    />
                  </div>
                  <Button 
                    onClick={createSeries} 
                    disabled={creatingSeries}
                    className="w-full rounded-full"
                    data-testid="submit-series-btn"
                  >
                    {creatingSeries ? <FiLoader className="mr-2 animate-spin" /> : <FiPlus className="mr-2" />}
                    Create Series
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </motion.div>

          {/* Series Grid */}
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
            </div>
          ) : series.length > 0 ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {series.map((s, index) => (
                <motion.div
                  key={s.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Card className="overflow-hidden" data-testid={`series-card-${s.id}`}>
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <CardTitle className="font-heading text-2xl flex items-center gap-2">
                            <FiLayers className="text-primary" />
                            {s.name}
                          </CardTitle>
                          {s.description && (
                            <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                              {s.description}
                            </p>
                          )}
                        </div>
                        <div className="flex gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="rounded-full"
                            onClick={() => setEditingSeries(s)}
                            data-testid={`edit-series-${s.id}`}
                          >
                            <FiEdit2 className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="rounded-full text-destructive hover:bg-destructive hover:text-destructive-foreground"
                            onClick={() => deleteSeries(s.id)}
                            data-testid={`delete-series-${s.id}`}
                          >
                            <FiTrash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                      <div className="flex items-center gap-3 mt-3">
                        <span className="px-3 py-1 rounded-full bg-primary/10 text-primary text-sm font-ui">
                          {s.book_count || 0} book{s.book_count !== 1 ? 's' : ''}
                        </span>
                        {s.books?.some(b => !b.is_published) && (
                          <Button
                            variant="outline"
                            size="sm"
                            className="rounded-full text-xs"
                            onClick={() => publishAllInSeries(s.id)}
                          >
                            <FiGlobe className="w-3 h-3 mr-1" />
                            Submit for Review
                          </Button>
                        )}
                      </div>
                    </CardHeader>
                    
                    <CardContent>
                      {/* Books in Series */}
                      {s.books?.length > 0 ? (
                        <div className="space-y-2 mb-4">
                          {s.books.map((book, idx) => (
                            <div 
                              key={book.id}
                              className="flex items-center gap-3 p-3 rounded-xl bg-muted/30 hover:bg-muted/50 transition-colors group"
                            >
                              {/* Reorder buttons */}
                              <div className="flex flex-col gap-0.5">
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-5 w-5 rounded opacity-50 group-hover:opacity-100"
                                  disabled={idx === 0}
                                  onClick={() => reorderBook(s.id, book.id, idx, idx - 1)}
                                >
                                  <FiChevronUp className="w-3 h-3" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-5 w-5 rounded opacity-50 group-hover:opacity-100"
                                  disabled={idx === s.books.length - 1}
                                  onClick={() => reorderBook(s.id, book.id, idx, idx + 1)}
                                >
                                  <FiChevronDown className="w-3 h-3" />
                                </Button>
                              </div>
                              
                              {/* Book number */}
                              <span className="w-8 h-8 rounded-full bg-primary/20 text-primary text-sm flex items-center justify-center font-bold">
                                {idx + 1}
                              </span>
                              
                              {/* Cover thumbnail */}
                              {book.cover_image ? (
                                <img 
                                  src={book.cover_image} 
                                  alt="" 
                                  className="w-10 h-14 object-cover rounded-lg shadow-sm"
                                />
                              ) : (
                                <div className="w-10 h-14 bg-muted rounded-lg flex items-center justify-center">
                                  <FiBook className="w-4 h-4 text-muted-foreground" />
                                </div>
                              )}
                              
                              {/* Book info */}
                              <div className="flex-1 min-w-0">
                                <p className="font-ui text-sm font-medium truncate">{book.title}</p>
                                <span className={`text-xs ${book.is_published ? 'text-green-600 dark:text-green-400' : 'text-yellow-600 dark:text-yellow-400'}`}>
                                  {book.is_published ? 'Published' : 'Draft'}
                                </span>
                              </div>
                              
                              {/* Actions */}
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-8 rounded-full opacity-0 group-hover:opacity-100"
                                onClick={() => navigate(`/editor/${book.id}`)}
                              >
                                Edit
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 rounded-full opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive"
                                onClick={() => removeBookFromSeries(s.id, book.id)}
                              >
                                <FiX className="w-4 h-4" />
                              </Button>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="py-6 text-center text-muted-foreground">
                          <FiBook className="w-8 h-8 mx-auto mb-2 opacity-50" />
                          <p className="text-sm">No books in this series yet</p>
                        </div>
                      )}
                      
                      {/* Add Book to Series */}
                      {getBooksNotInSeries(s.id).length > 0 && (
                        <div className="pt-3 border-t border-border">
                          <Label className="text-xs text-muted-foreground mb-2 block">Add a book:</Label>
                          <Select onValueChange={(bookId) => addBookToSeries(s.id, bookId)}>
                            <SelectTrigger className="rounded-full">
                              <SelectValue placeholder="Select a book to add..." />
                            </SelectTrigger>
                            <SelectContent>
                              {getBooksNotInSeries(s.id).map((book) => (
                                <SelectItem key={book.id} value={book.id}>
                                  {book.title}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          ) : (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="text-center py-20"
            >
              <div className="w-24 h-24 mx-auto rounded-full bg-primary/10 flex items-center justify-center mb-6">
                <FiLayers className="w-12 h-12 text-primary" />
              </div>
              <h3 className="font-heading text-2xl mb-2">No series yet</h3>
              <p className="font-body text-muted-foreground max-w-md mx-auto mb-6">
                Create your first series to organize your books into collections that readers can follow.
              </p>
              <Button 
                className="rounded-full" 
                onClick={() => setIsCreateOpen(true)}
              >
                <FiPlus className="mr-2" />
                Create Your First Series
              </Button>
            </motion.div>
          )}
        </div>
      </div>

      {/* Edit Series Dialog */}
      <Dialog open={!!editingSeries} onOpenChange={() => setEditingSeries(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="font-heading text-2xl">Edit Series</DialogTitle>
          </DialogHeader>
          {editingSeries && (
            <div className="space-y-4 pt-4">
              <div className="space-y-2">
                <Label className="font-ui">Series Name</Label>
                <Input
                  value={editingSeries.name}
                  onChange={(e) => setEditingSeries({ ...editingSeries, name: e.target.value })}
                  className="rounded-full border-2"
                />
              </div>
              <div className="space-y-2">
                <Label className="font-ui">Description</Label>
                <Textarea
                  value={editingSeries.description || ''}
                  onChange={(e) => setEditingSeries({ ...editingSeries, description: e.target.value })}
                  className="rounded-2xl border-2 min-h-20"
                />
              </div>
              <Button onClick={updateSeries} className="w-full rounded-full">
                Save Changes
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
