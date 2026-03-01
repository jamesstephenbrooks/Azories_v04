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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import { 
  FiPlus, FiEdit2, FiTrash2, FiBook, FiEye, FiEyeOff, FiZap, FiStar, FiAward, 
  FiCheck, FiBarChart2, FiLoader, FiLayers, FiLink, FiX, FiSearch, FiChevronDown, FiChevronUp, FiGlobe,
  FiClock, FiSend
} from 'react-icons/fi';
import Navbar from '@/components/Navbar';
import AnalyticsDashboard from '@/components/AnalyticsDashboard';
import TrialBanner from '@/components/TrialBanner';
import { StreakDisplay, BadgeCollection, useStreaksAndBadges } from '@/components/ReadingStreaks';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function Dashboard() {
  const { user, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [genres, setGenres] = useState([]);
  const [ageRatings, setAgeRatings] = useState([]);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isUpgradeOpen, setIsUpgradeOpen] = useState(false);
  const [isAIStoryOpen, setIsAIStoryOpen] = useState(false);
  const [analyticsDialog, setAnalyticsDialog] = useState(null);
  const [analyticsData, setAnalyticsData] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');  // Search for books
  const [newBook, setNewBook] = useState({
    title: '',
    description: '',
    genre: 'General',
    layout_mode: 'standard',
    age_rating: 'All Ages'
  });
  const [aiStory, setAIStory] = useState({
    // Story Details
    title: '',
    age_range: '5-8',  // 3-5, 5-8, 8-12
    num_pages: 8,
    words_per_page: 'medium',  // short (50), medium (100), long (150)
    
    // Main Character
    character_name: '',
    character_description: '',
    
    // Story
    story_description: '',
    
    // Style
    art_style: '3d-pixar',  // 3d-pixar, watercolour, storybook
    
    // Legacy/backend compatibility
    idea: '',
    genre: 'Adventure',
    age_rating: 'All Ages',
    generate_images: true,
    media_type: 'images',
    image_style: '3d-pixar'
  });
  const [creating, setCreating] = useState(false);
  const [generatingStory, setGeneratingStory] = useState(false);
  const [subscription, setSubscription] = useState('free');
  const [credits, setCredits] = useState(0);
  const [trialStatus, setTrialStatus] = useState({ in_trial: false, display_text: '' });
  const AI_STORY_COST = 5; // Cost in credits for AI story creation
  
  // Series state
  const [series, setSeries] = useState([]);
  const [isSeriesOpen, setIsSeriesOpen] = useState(false);
  const [isAddToSeriesOpen, setIsAddToSeriesOpen] = useState(false);
  const [selectedBookForSeries, setSelectedBookForSeries] = useState(null);
  const [selectedSeriesForAdding, setSelectedSeriesForAdding] = useState(null);  // For adding book from series view
  const [expandedSeries, setExpandedSeries] = useState(null);  // To view books in a series
  const [newSeries, setNewSeries] = useState({ name: '', description: '' });
  const [creatingSeries, setCreatingSeries] = useState(false);
  const [activeTab, setActiveTab] = useState('books');  // 'books' or 'analytics'

  useEffect(() => {
    if (!authLoading && !user && !localStorage.getItem('azories-token')) {
      navigate('/auth', { state: { from: '/dashboard' } });
    }
  }, [user, authLoading, navigate]);

  useEffect(() => {
    if (user) {
      setSubscription(user.subscription || 'free');
      fetchMyBooks();
      fetchGenres();
      fetchAgeRatings();
      fetchSeries();
      fetchCredits();
      fetchTrialStatus();
    }
  }, [user]);

  const fetchCredits = async () => {
    try {
      const token = localStorage.getItem('azories-token');
      const res = await axios.get(`${API}/credits/balance`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCredits(res.data.credits || 0);
    } catch (error) {
      console.error('Failed to fetch credits:', error);
    }
  };

  const fetchTrialStatus = async () => {
    try {
      const token = localStorage.getItem('azories-token');
      const res = await axios.get(`${API}/auth/ai-story-trial`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTrialStatus(res.data);
    } catch (error) {
      console.error('Failed to fetch trial status:', error);
    }
  };

  const fetchMyBooks = async () => {
    try {
      const token = localStorage.getItem('azories-token');
      const res = await axios.get(`${API}/books/my`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setBooks(res.data);
    } catch (error) {
      toast.error('Failed to load books');
    } finally {
      setLoading(false);
    }
  };
  
  const fetchSeries = async () => {
    try {
      const token = localStorage.getItem('azories-token');
      const res = await axios.get(`${API}/series`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSeries(res.data);
    } catch (error) {
      console.error('Failed to load series');
    }
  };
  
  const createSeries = async () => {
    if (!newSeries.name.trim()) {
      toast.error('Please enter a series name');
      return;
    }
    setCreatingSeries(true);
    try {
      const token = localStorage.getItem('azories-token');
      await axios.post(`${API}/series`, newSeries, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Series created!');
      setNewSeries({ name: '', description: '' });
      fetchSeries();
    } catch (error) {
      toast.error('Failed to create series');
    } finally {
      setCreatingSeries(false);
    }
  };
  
  const deleteSeries = async (seriesId) => {
    if (!window.confirm('Delete this series? Books will be unlinked but not deleted.')) return;
    try {
      const token = localStorage.getItem('azories-token');
      await axios.delete(`${API}/series/${seriesId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Series deleted');
      fetchSeries();
    } catch (error) {
      toast.error('Failed to delete series');
    }
  };
  
  const addBookToSeries = async (seriesId, bookIdOverride = null) => {
    const bookId = bookIdOverride || selectedBookForSeries?.id;
    if (!bookId) return;
    try {
      const token = localStorage.getItem('azories-token');
      await axios.post(`${API}/series/${seriesId}/books/${bookId}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Book added to series!');
      setIsAddToSeriesOpen(false);
      setSelectedBookForSeries(null);
      fetchMyBooks();
      fetchSeries();
    } catch (error) {
      toast.error('Failed to add book to series');
    }
  };
  
  const removeBookFromSeries = async (book) => {
    try {
      const token = localStorage.getItem('azories-token');
      await axios.delete(`${API}/series/${book.series_id}/books/${book.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Book removed from series');
      fetchMyBooks();
      fetchSeries();
    } catch (error) {
      toast.error('Failed to remove book from series');
    }
  };
  
  const reorderBookInSeries = async (seriesId, bookId, currentIndex, newIndex) => {
    try {
      const token = localStorage.getItem('azories-token');
      await axios.put(`${API}/series/${seriesId}/books/${bookId}/order`, {
        new_order: newIndex + 1  // API expects 1-based order
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
    try {
      const token = localStorage.getItem('azories-token');
      const seriesData = series.find(s => s.id === seriesId);
      if (!seriesData?.books) return;
      
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
      fetchMyBooks();
      fetchSeries();
    } catch (error) {
      toast.error('Failed to submit some books for review');
    }
  };
  
  // Filter books based on search query
  const filteredBooks = books.filter(book => {
    if (!searchQuery.trim()) return true;
    const query = searchQuery.toLowerCase();
    return (
      book.title?.toLowerCase().includes(query) ||
      book.description?.toLowerCase().includes(query) ||
      book.genre?.toLowerCase().includes(query)
    );
  });
  
  // Get books not in the selected series (for adding)
  const booksNotInSeries = (seriesId) => {
    return books.filter(book => book.series_id !== seriesId);
  };

  const fetchGenres = async () => {
    try {
      const res = await axios.get(`${API}/genres`);
      setGenres(res.data.genres);
    } catch (error) {
      console.error('Error fetching genres');
    }
  };

  const fetchAgeRatings = async () => {
    try {
      const res = await axios.get(`${API}/age-ratings`);
      setAgeRatings(res.data.age_ratings);
    } catch (error) {
      setAgeRatings(['All Ages', '5+', '8+', '12+', '16+']);
    }
  };

  const fetchAnalytics = async (bookId) => {
    try {
      const token = localStorage.getItem('azories-token');
      const res = await axios.get(`${API}/books/${bookId}/analytics`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAnalyticsData(res.data);
      setAnalyticsDialog(bookId);
    } catch (error) {
      toast.error('Failed to load analytics');
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
      const token = localStorage.getItem('azories-token');
      const res = await axios.post(`${API}/books`, newBook, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Book created!');
      setIsCreateOpen(false);
      setNewBook({ title: '', description: '', genre: 'General', layout_mode: 'standard', age_rating: 'All Ages' });
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

  const generateAIStory = async () => {
    if (!aiStory.idea.trim()) {
      toast.error('Please enter a story idea');
      return;
    }
    
    if (credits < AI_STORY_COST) {
      toast.error(`Insufficient credits! You need ${AI_STORY_COST} credits.`);
      return;
    }
    
    setGeneratingStory(true);
    toast.info('Generating your story... This may take a minute.');
    
    try {
      const token = localStorage.getItem('azories-token');
      const res = await axios.post(`${API}/ai/generate-story`, aiStory, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Update local credits after successful generation
      setCredits(prev => prev - AI_STORY_COST);
      
      const imagesGenerated = res.data.images_generated || 0;
      toast.success(`Story "${res.data.title}" created with ${res.data.pages_created} pages and ${imagesGenerated} images!`);
      setIsAIStoryOpen(false);
      setAIStory({ idea: '', genre: 'Adventure', age_rating: 'All Ages', num_pages: 5, generate_images: true, media_type: 'images', image_style: '3d-pixar', words_per_page: 'medium' });
      navigate(`/editor/${res.data.book_id}`);
    } catch (error) {
      if (error.response?.status === 402) {
        toast.error('Insufficient credits! Please purchase more credits to continue.');
        setIsAIStoryOpen(false);
        navigate('/credits');
      } else {
        toast.error(error.response?.data?.detail || 'Failed to generate story');
      }
    } finally {
      setGeneratingStory(false);
    }
  };

  const handleUpgrade = async () => {
    try {
      const token = localStorage.getItem('azories-token');
      await axios.post(`${API}/auth/upgrade`, { subscription: 'pro' }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSubscription('pro');
      toast.success('Upgraded to Pro! You can now create books.');
      setIsUpgradeOpen(false);
      window.location.reload();
    } catch (error) {
      toast.error('Failed to upgrade');
    }
  };

  const togglePublish = async (book) => {
    try {
      const token = localStorage.getItem('azories-token');
      // If book is published, use unpublish endpoint
      if (book.is_published || book.publish_status === 'published') {
        await axios.post(`${API}/books/${book.id}/unpublish`, {}, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Book unpublished');
        fetchMyBooks();
        return;
      }
      
      // If book is in pending_review, show message
      if (book.publish_status === 'pending_review') {
        toast.info('This book is already coming soon!');
        return;
      }
      
      // Otherwise, request publish (sends to admin for review)
      const response = await axios.post(`${API}/books/${book.id}/request-publish`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(response.data.message || 'Book submitted for review!');
      fetchMyBooks();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update book');
    }
  };

  const getPublishStatusBadge = (book) => {
    if (book.is_published || book.publish_status === 'published') {
      return <span className="text-xs px-2 py-1 rounded-full bg-green-500/20 text-green-500">Published</span>;
    }
    if (book.publish_status === 'pending_review') {
      return <span className="text-xs px-2 py-1 rounded-full bg-amber-500/20 text-amber-500">Coming Soon ✨</span>;
    }
    if (book.publish_status === 'rejected') {
      return <span className="text-xs px-2 py-1 rounded-full bg-red-500/20 text-red-500">Rejected</span>;
    }
    return <span className="text-xs px-2 py-1 rounded-full bg-muted text-muted-foreground">Draft</span>;
  };

  const deleteBook = async (bookId) => {
    if (!window.confirm('Are you sure you want to delete this book?')) return;
    
    try {
      const token = localStorage.getItem('azories-token');
      await axios.delete(`${API}/books/${bookId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
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

  if (!user) return null;

  const isPro = subscription === 'pro';

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <div className="pt-28 pb-12 px-6 md:px-12">
        <div className="max-w-7xl mx-auto">
          {/* Trial Banner */}
          <TrialBanner />
          
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-10"
          >
            <div>
              <div className="flex items-center gap-3 mb-2">
                <h1 className="font-heading text-4xl md:text-5xl font-bold">My Books</h1>
                <span className={`px-3 py-1 rounded-full text-sm font-ui ${
                  isPro ? 'bg-secondary/20 text-secondary' : 'bg-muted text-muted-foreground'
                }`}>
                  {isPro ? (user.pro_trial ? 'Pro Trial' : 'Pro') : 'Free'}
                </span>
              </div>
              <p className="font-body text-lg text-muted-foreground">
                Welcome back, {user.name}! {isPro ? 'Create and manage your stories.' : 'Upgrade to Pro to start creating!'}
              </p>
            </div>
            
            <div className="flex gap-3 flex-wrap">
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
              
              {isPro && (
                <>
                  <Dialog open={isAIStoryOpen} onOpenChange={setIsAIStoryOpen}>
                    <DialogTrigger asChild>
                      <Button 
                        variant="outline"
                        className="rounded-full px-6 py-6 font-ui border-accent text-accent hover:bg-accent hover:text-accent-foreground"
                        data-testid="ai-story-btn"
                      >
                        <FiZap className="mr-2" />
                        AI Story Creator
                      </Button>
                    </DialogTrigger>
                  <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                      <DialogTitle className="font-heading text-2xl flex items-center gap-2">
                        <FiZap className="text-accent" />
                        AI Story Creator
                      </DialogTitle>
                      <DialogDescription>
                        Describe your story idea and AI will create the entire book with text and visuals!
                      </DialogDescription>
                    </DialogHeader>
                    
                    {/* Credit Cost Banner */}
                    <div className={`flex items-center justify-between p-3 rounded-xl ${credits >= AI_STORY_COST ? 'bg-gradient-to-r from-amber-500/10 to-orange-500/10 border border-amber-500/20' : 'bg-red-500/10 border border-red-500/30'}`}>
                      <div className="flex items-center gap-2">
                        <FiZap className={credits >= AI_STORY_COST ? 'text-amber-500' : 'text-red-500'} />
                        <span className="text-sm font-medium">
                          {credits >= AI_STORY_COST 
                            ? `Cost: ${AI_STORY_COST} credits (You have ${credits})`
                            : `Insufficient credits! Need ${AI_STORY_COST}, have ${credits}`
                          }
                        </span>
                      </div>
                      {credits < AI_STORY_COST && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="text-xs"
                          onClick={() => {
                            setIsAIStoryOpen(false);
                            navigate('/credits');
                          }}
                        >
                          Buy Credits
                        </Button>
                      )}
                    </div>
                    
                    <div className="space-y-5 pt-4">
                      <div className="space-y-2">
                        <Label className="font-ui">Your Story Idea</Label>
                        <Textarea
                          value={aiStory.idea}
                          onChange={(e) => setAIStory({ ...aiStory, idea: e.target.value })}
                          placeholder="A brave little robot who wants to learn how to dance..."
                          className="min-h-24 rounded-2xl border-2"
                        />
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label className="font-ui">Genre</Label>
                          <Select value={aiStory.genre} onValueChange={(v) => setAIStory({ ...aiStory, genre: v })}>
                            <SelectTrigger className="rounded-full border-2">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {genres.map((g) => <SelectItem key={g} value={g}>{g}</SelectItem>)}
                            </SelectContent>
                          </Select>
                        </div>
                        
                        <div className="space-y-2">
                          <Label className="font-ui">Age Rating</Label>
                          <Select value={aiStory.age_rating} onValueChange={(v) => setAIStory({ ...aiStory, age_rating: v })}>
                            <SelectTrigger className="rounded-full border-2">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {ageRatings.map((r) => <SelectItem key={r} value={r}>{r}</SelectItem>)}
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                      
                      <div className="space-y-2">
                        <Label className="font-ui">Number of Pages</Label>
                        <Select value={String(aiStory.num_pages)} onValueChange={(v) => setAIStory({ ...aiStory, num_pages: parseInt(v) })}>
                          <SelectTrigger className="rounded-full border-2">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {[3, 5, 8, 10, 15].map((n) => <SelectItem key={n} value={String(n)}>{n} pages</SelectItem>)}
                          </SelectContent>
                        </Select>
                      </div>
                      
                      {/* Words Per Page Selection */}
                      <div className="space-y-2">
                        <Label className="font-ui">Words Per Page</Label>
                        <Select value={aiStory.words_per_page} onValueChange={(v) => setAIStory({ ...aiStory, words_per_page: v })}>
                          <SelectTrigger className="rounded-full border-2">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="short">📝 Short (~50 words) - Quick reads</SelectItem>
                            <SelectItem value="medium">📖 Medium (~100 words) - Standard</SelectItem>
                            <SelectItem value="long">📚 Long (~150 words) - Detailed</SelectItem>
                          </SelectContent>
                        </Select>
                        <p className="text-xs text-muted-foreground">
                          {aiStory.words_per_page === 'short' && 'Perfect for younger readers (ages 3-5)'}
                          {aiStory.words_per_page === 'medium' && 'Great for most children\'s books (ages 5-8)'}
                          {aiStory.words_per_page === 'long' && 'Best for older readers (ages 8+)'}
                        </p>
                      </div>
                      
                      {/* Visual Media Options */}
                      <div className="space-y-3 pt-2 border-t border-border">
                        <Label className="font-ui font-semibold">Visual Media for Pages</Label>
                        <Select value={aiStory.media_type} onValueChange={(v) => setAIStory({ ...aiStory, media_type: v })}>
                          <SelectTrigger className="rounded-full border-2">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="images">🖼️ Generate Images</SelectItem>
                            <SelectItem value="videos">🎬 Generate Videos (Sora AI)</SelectItem>
                            <SelectItem value="cinemagraphs">✨ Cinemagraphs (Animated Images)</SelectItem>
                            <SelectItem value="none">📝 Text Only (No Visuals)</SelectItem>
                          </SelectContent>
                        </Select>
                        <p className="text-xs text-muted-foreground">
                          {aiStory.media_type === 'videos' && '⏱️ Video generation takes 2-5 minutes per page'}
                          {aiStory.media_type === 'cinemagraphs' && '⏱️ Cinemagraphs are animated images with subtle motion'}
                          {aiStory.media_type === 'images' && 'AI will generate an illustration for each page'}
                          {aiStory.media_type === 'none' && 'Story will be text-only, you can add visuals later in the editor'}
                        </p>
                      </div>
                      
                      {/* Image Style Selection (show only if generating images/cinemagraphs) */}
                      {(aiStory.media_type === 'images' || aiStory.media_type === 'cinemagraphs') && (
                        <div className="space-y-2">
                          <Label className="font-ui">Visual Style</Label>
                          <Select value={aiStory.image_style} onValueChange={(v) => setAIStory({ ...aiStory, image_style: v })}>
                            <SelectTrigger className="rounded-full border-2">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="3d-pixar">🎬 3D Pixar / Disney Style</SelectItem>
                              <SelectItem value="illustration">🎨 Children's Illustration</SelectItem>
                              <SelectItem value="comic">💥 Comic Book Style</SelectItem>
                              <SelectItem value="realistic">📷 Realistic/Photographic</SelectItem>
                              <SelectItem value="scifi">🚀 Sci-Fi / Futuristic</SelectItem>
                              <SelectItem value="sketch">✏️ Pencil Sketch</SelectItem>
                              <SelectItem value="watercolor">🎨 Watercolor Painting</SelectItem>
                              <SelectItem value="anime">🌸 Anime / Manga Style</SelectItem>
                              <SelectItem value="fantasy">🏰 Fantasy Art</SelectItem>
                              <SelectItem value="storybook">📖 Classic Storybook</SelectItem>
                            </SelectContent>
                          </Select>
                          <p className="text-xs text-muted-foreground">
                            💡 Tip: Mention a style in your idea (e.g., "Pixar-style" or "anime") to override this selection
                          </p>
                        </div>
                      )}
                      
                      {/* Video Style Selection (show only if generating videos) */}
                      {aiStory.media_type === 'videos' && (
                        <div className="space-y-2">
                          <Label className="font-ui">Video Style</Label>
                          <Select value={aiStory.image_style} onValueChange={(v) => setAIStory({ ...aiStory, image_style: v })}>
                            <SelectTrigger className="rounded-full border-2">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="animation">🎬 Children's Animation</SelectItem>
                              <SelectItem value="comic">💥 Comic Book Animation</SelectItem>
                              <SelectItem value="realistic">📷 Realistic/Cinematic</SelectItem>
                              <SelectItem value="scifi">🚀 Sci-Fi / Futuristic</SelectItem>
                              <SelectItem value="anime">🌸 Anime Style</SelectItem>
                              <SelectItem value="fantasy">🏰 Fantasy/Magical</SelectItem>
                              <SelectItem value="pixar">🎬 3D Pixar Style</SelectItem>
                              <SelectItem value="watercolor">🎨 Watercolor Animation</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      )}
                      
                      <Button 
                        onClick={generateAIStory}
                        disabled={generatingStory || credits < AI_STORY_COST}
                        className={`w-full rounded-full py-6 ${credits < AI_STORY_COST ? 'bg-muted text-muted-foreground' : 'bg-accent hover:bg-accent/90'}`}
                      >
                        {generatingStory ? (
                          <>
                            <FiLoader className="mr-2 animate-spin" />
                            Creating Your Story...
                          </>
                        ) : credits < AI_STORY_COST ? (
                          <>
                            <FiZap className="mr-2" />
                            Need {AI_STORY_COST - credits} More Credits
                          </>
                        ) : (
                          <>
                            <FiZap className="mr-2" />
                            Generate Story ({AI_STORY_COST} credits)
                            Generate Story
                          </>
                        )}
                      </Button>
                    </div>
                  </DialogContent>
                </Dialog>
              </>
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
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label className="font-ui">Description</Label>
                      <Textarea
                        value={newBook.description}
                        onChange={(e) => setNewBook({ ...newBook, description: e.target.value })}
                        placeholder="A brief description..."
                        className="rounded-2xl border-2 min-h-20"
                      />
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label className="font-ui">Genre</Label>
                        <Select value={newBook.genre} onValueChange={(v) => setNewBook({ ...newBook, genre: v })}>
                          <SelectTrigger className="rounded-full border-2"><SelectValue /></SelectTrigger>
                          <SelectContent>
                            {genres.map((g) => <SelectItem key={g} value={g}>{g}</SelectItem>)}
                          </SelectContent>
                        </Select>
                      </div>
                      
                      <div className="space-y-2">
                        <Label className="font-ui">Age Rating</Label>
                        <Select value={newBook.age_rating} onValueChange={(v) => setNewBook({ ...newBook, age_rating: v })}>
                          <SelectTrigger className="rounded-full border-2"><SelectValue /></SelectTrigger>
                          <SelectContent>
                            {ageRatings.map((r) => <SelectItem key={r} value={r}>{r}</SelectItem>)}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <Label className="font-ui">Layout</Label>
                      <Select value={newBook.layout_mode} onValueChange={(v) => setNewBook({ ...newBook, layout_mode: v })}>
                        <SelectTrigger className="rounded-full border-2"><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="standard">Standard Book</SelectItem>
                          <SelectItem value="comic">Comic Book</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <Button type="submit" className="w-full rounded-full" disabled={creating}>
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
              </DialogHeader>
              <div className="pt-4 space-y-6">
                <div className="space-y-4">
                  {[
                    'Create unlimited books',
                    'AI-powered image generation',
                    'AI video generation with Sora',
                    'AI Story Creator - full stories from ideas',
                    'Multiple narrator voices',
                    'Comic book layouts',
                    'Book analytics'
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
                  <p className="text-sm text-muted-foreground mb-2">Test Mode</p>
                  <p className="font-heading text-3xl font-bold">Free</p>
                </div>
                
                <Button onClick={handleUpgrade} className="w-full rounded-full py-6 text-lg font-ui bg-secondary hover:bg-secondary/90">
                  <FiZap className="mr-2" />
                  Upgrade Now
                </Button>
              </div>
            </DialogContent>
          </Dialog>
          
          {/* Analytics Dialog */}
          <Dialog open={!!analyticsDialog} onOpenChange={() => setAnalyticsDialog(null)}>
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle className="font-heading text-xl flex items-center gap-2">
                  <FiBarChart2 className="text-primary" />
                  Book Analytics
                </DialogTitle>
              </DialogHeader>
              {analyticsData && (
                <div className="pt-4 space-y-4">
                  <h3 className="font-semibold">{analyticsData.title}</h3>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 rounded-xl bg-muted/50 text-center">
                      <p className="text-3xl font-bold text-primary">{analyticsData.view_count}</p>
                      <p className="text-sm text-muted-foreground">Views</p>
                    </div>
                    <div className="p-4 rounded-xl bg-muted/50 text-center">
                      <p className="text-3xl font-bold text-secondary">{analyticsData.read_count}</p>
                      <p className="text-sm text-muted-foreground">Reads</p>
                    </div>
                    <div className="p-4 rounded-xl bg-muted/50 text-center">
                      <p className="text-3xl font-bold text-accent">{analyticsData.unique_readers}</p>
                      <p className="text-sm text-muted-foreground">Unique Readers</p>
                    </div>
                    <div className="p-4 rounded-xl bg-muted/50 text-center">
                      <p className="text-3xl font-bold">{Math.round(analyticsData.avg_completion_rate * 100)}%</p>
                      <p className="text-sm text-muted-foreground">Completion</p>
                    </div>
                  </div>
                  
                  {analyticsData.daily_reads?.length > 0 && (
                    <div className="pt-4">
                      <p className="font-ui text-sm mb-2">Last 7 Days</p>
                      <div className="flex items-end gap-1 h-20">
                        {analyticsData.daily_reads.map((day, idx) => (
                          <div key={idx} className="flex-1 flex flex-col items-center">
                            <div 
                              className="w-full bg-primary/20 rounded-t" 
                              style={{ height: `${Math.max(10, (day.count / Math.max(...analyticsData.daily_reads.map(d => d.count))) * 60)}px` }}
                            />
                            <span className="text-xs text-muted-foreground mt-1">{day.count}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </DialogContent>
          </Dialog>
          
          {/* Reading Streak & Badges Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="mb-8"
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="p-6 rounded-2xl bg-card border border-border">
                <h3 className="font-heading text-lg font-semibold mb-4 flex items-center gap-2">
                  <FiZap className="text-secondary" />
                  Reading Streak
                </h3>
                <StreakDisplay compact={false} />
              </div>
              <div className="p-6 rounded-2xl bg-card border border-border">
                <h3 className="font-heading text-lg font-semibold mb-4 flex items-center gap-2">
                  <FiAward className="text-primary" />
                  Your Badges
                </h3>
                <BadgeCollection showAll={false} />
              </div>
            </div>
          </motion.div>
          
          {/* Tabs for Books, Analytics, and Series */}
          <Tabs value={activeTab} onValueChange={(value) => {
            if (value === 'series') {
              navigate('/series');
            } else {
              setActiveTab(value);
            }
          }} className="w-full">
            <TabsList className="grid w-full max-w-lg grid-cols-3 mb-6 h-auto">
              <TabsTrigger value="books" className="rounded-full py-2.5 min-h-[44px]" data-testid="tab-my-books">
                <FiBook className="w-4 h-4 mr-1 sm:mr-2" />
                <span className="text-xs sm:text-sm">My Books</span>
              </TabsTrigger>
              <TabsTrigger value="analytics" className="rounded-full py-2.5 min-h-[44px]" data-testid="tab-analytics">
                <FiBarChart2 className="w-4 h-4 mr-1 sm:mr-2" />
                <span className="text-xs sm:text-sm">Analytics</span>
              </TabsTrigger>
              <TabsTrigger value="series" className="rounded-full py-2.5 min-h-[44px]" data-testid="tab-my-series">
                <FiLayers className="w-4 h-4 mr-1 sm:mr-2" />
                <span className="text-xs sm:text-sm">My Series</span>
              </TabsTrigger>
            </TabsList>
            
            <TabsContent value="books">
              {/* Search Bar */}
              <div className="relative mb-6">
                <FiSearch className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search your books..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-12 rounded-full border-2 h-12"
              data-testid="search-books-input"
            />
            {searchQuery && (
              <Button
                variant="ghost"
                size="icon"
                className="absolute right-2 top-1/2 transform -translate-y-1/2 rounded-full h-8 w-8"
                onClick={() => setSearchQuery('')}
              >
                <FiX className="w-4 h-4" />
              </Button>
            )}
          </div>
          
          {/* Books Grid */}
          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(3)].map((_, i) => <Card key={i} className="shimmer h-64" />)}
            </div>
          ) : filteredBooks.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredBooks.map((book, index) => (
                <motion.div
                  key={book.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                >
                  <Card className="group hover:shadow-lg transition-shadow">
                    <CardHeader className="pb-3">
                      <div className="flex items-start gap-4">
                        {/* Cover Thumbnail */}
                        <div 
                          className="w-16 h-20 rounded-lg bg-gradient-to-br from-primary/20 to-secondary/20 flex-shrink-0 overflow-hidden cursor-pointer hover:opacity-80 transition-opacity"
                          onClick={() => navigate(`/editor/${book.id}`)}
                        >
                          {book.cover_image ? (
                            <img 
                              src={book.cover_image} 
                              alt={book.title}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center">
                              <FiBook className="w-6 h-6 text-primary/40" />
                            </div>
                          )}
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between">
                            <div className="flex-1 min-w-0">
                              <CardTitle className="font-heading text-xl line-clamp-1">{book.title}</CardTitle>
                              <CardDescription className="font-body mt-1 line-clamp-2">
                                {book.description || 'No description'}
                              </CardDescription>
                              {/* Series Badge */}
                              {book.series_id && (
                                <div className="mt-2 flex items-center gap-2">
                                  <span className="px-2 py-1 rounded-full bg-primary/10 text-primary text-xs font-ui flex items-center gap-1">
                                    <FiLayers className="w-3 h-3" />
                                    {series.find(s => s.id === book.series_id)?.name || 'Series'}
                                    {book.series_order && ` #${book.series_order}`}
                                  </span>
                                  <Button 
                                    variant="ghost" 
                                    size="sm" 
                                    className="h-6 w-6 p-0 rounded-full"
                                    onClick={() => removeBookFromSeries(book)}
                                    title="Remove from series"
                                  >
                                    <FiX className="w-3 h-3" />
                                  </Button>
                                </div>
                              )}
                            </div>
                            <div className="flex flex-col gap-1 items-end ml-2">
                              {getPublishStatusBadge(book)}
                              {book.age_rating !== 'All Ages' && (
                                <span className="px-2 py-0.5 rounded text-xs bg-primary/10 text-primary">
                                  {book.age_rating}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground mb-4">
                        <span className="font-ui">{book.chapter_count} ch</span>
                        <span className="font-ui">{book.total_pages} pg</span>
                        <span className="font-ui">{book.view_count || 0} views</span>
                        <span className="font-ui">{book.read_count || 0} reads</span>
                      </div>
                      
                      <div className="flex items-center justify-between gap-3">
                        {/* Left side - Edit and utility buttons */}
                        <div className="flex items-center gap-2">
                          <Button variant="default" size="sm" className="rounded-full" onClick={() => navigate(`/editor/${book.id}`)}>
                            <FiEdit2 className="mr-2 w-4 h-4" />
                            Edit
                          </Button>
                          <Button variant="outline" size="icon" className="rounded-full" onClick={() => fetchAnalytics(book.id)}>
                            <FiBarChart2 className="w-4 h-4" />
                          </Button>
                          {!book.series_id && (
                            <Button 
                              variant="outline" 
                              size="icon" 
                              className="rounded-full"
                              onClick={() => {
                                setSelectedBookForSeries(book);
                                setIsAddToSeriesOpen(true);
                              }}
                              title="Add to Series"
                            >
                              <FiLink className="w-4 h-4" />
                            </Button>
                          )}
                          <Button 
                            variant="outline" 
                            size="icon" 
                            className="rounded-full text-destructive hover:bg-destructive hover:text-destructive-foreground"
                            onClick={() => deleteBook(book.id)}
                          >
                            <FiTrash2 className="w-4 h-4" />
                          </Button>
                        </div>
                        
                        {/* Right side - Publish button */}
                        <Button 
                          variant={book.is_published || book.publish_status === 'published' ? "outline" : "default"}
                          size="sm"
                          className={`rounded-full px-3 text-xs ${
                            book.is_published || book.publish_status === 'published'
                              ? 'border-green-500 text-green-600 hover:bg-green-50'
                              : book.publish_status === 'pending_review'
                                ? 'bg-amber-500 hover:bg-amber-600 text-white'
                                : 'bg-purple-600 hover:bg-purple-700 text-white'
                          }`}
                          onClick={() => togglePublish(book)}
                          data-testid={`publish-btn-${book.id}`}
                        >
                          {book.is_published || book.publish_status === 'published' ? (
                            <>
                              <FiEyeOff className="mr-1 w-3 h-3" />
                              Unpublish
                            </>
                          ) : book.publish_status === 'pending_review' ? (
                            <>
                              <FiClock className="mr-1 w-3 h-3" />
                              Coming Soon
                            </>
                          ) : (
                            <>
                              <FiSend className="mr-1 w-3 h-3" />
                              Publish
                            </>
                          )}
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          ) : searchQuery ? (
            // No results from search
            <div className="text-center py-20">
              <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="space-y-4">
                <div className="w-20 h-20 mx-auto rounded-full bg-muted/50 flex items-center justify-center">
                  <FiSearch className="w-10 h-10 text-muted-foreground" />
                </div>
                <h3 className="font-heading text-2xl">No books found</h3>
                <p className="font-body text-muted-foreground max-w-md mx-auto">
                  No books match "{searchQuery}". Try a different search term.
                </p>
                <Button variant="outline" className="rounded-full" onClick={() => setSearchQuery('')}>
                  Clear Search
                </Button>
              </motion.div>
            </div>
          ) : (
            <div className="text-center py-20">
              <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="space-y-4">
                <div className="w-20 h-20 mx-auto rounded-full bg-primary/10 flex items-center justify-center">
                  <FiBook className="w-10 h-10 text-primary" />
                </div>
                <h3 className="font-heading text-2xl">No books yet</h3>
                <p className="font-body text-muted-foreground max-w-md mx-auto">
                  {isPro ? 'Start your storytelling journey!' : 'Upgrade to Pro to start creating!'}
                </p>
                {isPro ? (
                  <div className="flex gap-3 justify-center">
                    <Button className="rounded-full" onClick={() => setIsCreateOpen(true)}>
                      <FiPlus className="mr-2" />
                      Create Book
                    </Button>
                    <Button variant="outline" className="rounded-full" onClick={() => setIsAIStoryOpen(true)}>
                      <FiZap className="mr-2" />
                      AI Story
                    </Button>
                  </div>
                ) : (
                  <Button className="rounded-full bg-secondary hover:bg-secondary/90" onClick={() => setIsUpgradeOpen(true)}>
                    <FiZap className="mr-2" />
                    Upgrade to Pro
                  </Button>
                )}
              </motion.div>
            </div>
          )}
            </TabsContent>
            
            <TabsContent value="analytics">
              <AnalyticsDashboard books={books} />
            </TabsContent>
          </Tabs>
        </div>
      </div>
      
      {/* Series Management Dialog */}
      <Dialog open={isSeriesOpen} onOpenChange={setIsSeriesOpen}>
        <DialogContent className="sm:max-w-lg max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-heading text-2xl flex items-center gap-2">
              <FiLayers className="text-primary" />
              Manage Book Series
            </DialogTitle>
            <DialogDescription>
              Create and organize your books into series
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-6 pt-4">
            {/* Create New Series */}
            <div className="space-y-3 p-4 rounded-xl bg-muted/30 border border-border">
              <Label className="font-ui font-semibold">Create New Series</Label>
              <Input
                value={newSeries.name}
                onChange={(e) => setNewSeries({ ...newSeries, name: e.target.value })}
                placeholder="Series name (e.g., The Dragon Chronicles)"
                className="rounded-full"
              />
              <Textarea
                value={newSeries.description}
                onChange={(e) => setNewSeries({ ...newSeries, description: e.target.value })}
                placeholder="Series description (optional)"
                className="rounded-xl min-h-16"
              />
              <Button 
                onClick={createSeries} 
                disabled={creatingSeries || !newSeries.name.trim()}
                className="rounded-full w-full"
              >
                {creatingSeries ? <FiLoader className="mr-2 animate-spin" /> : <FiPlus className="mr-2" />}
                Create Series
              </Button>
            </div>
            
            {/* Existing Series */}
            <div className="space-y-3">
              <Label className="font-ui font-semibold">Your Series ({series.length})</Label>
              {series.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-6">
                  No series yet. Create one above to start organizing your books!
                </p>
              ) : (
                <div className="space-y-3">
                  {series.map((s) => (
                    <div key={s.id} className="rounded-xl bg-card border border-border overflow-hidden">
                      {/* Series Header - Always visible */}
                      <div 
                        className="p-4 flex items-center justify-between cursor-pointer hover:bg-muted/30 transition-colors"
                        onClick={() => setExpandedSeries(expandedSeries === s.id ? null : s.id)}
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <h4 className="font-heading font-semibold">{s.name}</h4>
                            <span className="px-2 py-0.5 rounded-full bg-primary/10 text-primary text-xs">
                              {s.book_count || 0} book{s.book_count !== 1 ? 's' : ''}
                            </span>
                          </div>
                          {s.description && (
                            <p className="text-sm text-muted-foreground mt-1 line-clamp-1">{s.description}</p>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="rounded-full"
                            onClick={(e) => {
                              e.stopPropagation();
                              setExpandedSeries(expandedSeries === s.id ? null : s.id);
                            }}
                          >
                            {expandedSeries === s.id ? (
                              <FiChevronUp className="w-4 h-4" />
                            ) : (
                              <FiChevronDown className="w-4 h-4" />
                            )}
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="rounded-full text-destructive hover:bg-destructive hover:text-destructive-foreground"
                            onClick={(e) => {
                              e.stopPropagation();
                              deleteSeries(s.id);
                            }}
                          >
                            <FiTrash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                      
                      {/* Expanded Series Content - Books List */}
                      {expandedSeries === s.id && (
                        <div className="px-4 pb-4 border-t border-border pt-3 space-y-3">
                          {/* Books in this series */}
                          {s.books?.length > 0 ? (
                            <div className="space-y-2">
                              <Label className="text-xs text-muted-foreground">Books in this series (drag to reorder):</Label>
                              {s.books.map((book, idx) => (
                                <div 
                                  key={book.id} 
                                  className="flex items-center gap-3 p-2 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors group"
                                >
                                  {/* Reorder buttons */}
                                  <div className="flex flex-col gap-0.5">
                                    <Button
                                      variant="ghost"
                                      size="icon"
                                      className="h-5 w-5 rounded opacity-50 group-hover:opacity-100"
                                      disabled={idx === 0}
                                      onClick={() => reorderBookInSeries(s.id, book.id, idx, idx - 1)}
                                    >
                                      <FiChevronUp className="w-3 h-3" />
                                    </Button>
                                    <Button
                                      variant="ghost"
                                      size="icon"
                                      className="h-5 w-5 rounded opacity-50 group-hover:opacity-100"
                                      disabled={idx === s.books.length - 1}
                                      onClick={() => reorderBookInSeries(s.id, book.id, idx, idx + 1)}
                                    >
                                      <FiChevronDown className="w-3 h-3" />
                                    </Button>
                                  </div>
                                  <span className="w-6 h-6 rounded-full bg-primary/20 text-primary text-xs flex items-center justify-center font-semibold">
                                    {idx + 1}
                                  </span>
                                  {book.cover_image ? (
                                    <img src={book.cover_image} alt="" className="w-8 h-10 object-cover rounded" />
                                  ) : (
                                    <div className="w-8 h-10 bg-muted rounded flex items-center justify-center">
                                      <FiBook className="w-4 h-4 text-muted-foreground" />
                                    </div>
                                  )}
                                  <span className="flex-1 font-ui text-sm truncate">{book.title}</span>
                                  {getPublishStatusBadge(book)}
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-7 px-2 text-xs rounded-full"
                                    onClick={() => navigate(`/editor/${book.id}`)}
                                  >
                                    Edit
                                  </Button>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-7 w-7 rounded-full text-muted-foreground hover:text-destructive"
                                    onClick={() => removeBookFromSeries({ id: book.id, series_id: s.id })}
                                  >
                                    <FiX className="w-3 h-3" />
                                  </Button>
                                </div>
                              ))}
                              
                              {/* Publish All in Series Button */}
                              {s.books.some(b => !b.is_published) && (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  className="w-full mt-2 rounded-full"
                                  onClick={() => publishAllInSeries(s.id)}
                                >
                                  <FiGlobe className="w-3 h-3 mr-2" />
                                  Submit All for Review
                                </Button>
                              )}
                            </div>
                          ) : (
                            <p className="text-sm text-muted-foreground text-center py-2">
                              No books in this series yet
                            </p>
                          )}
                          
                          {/* Add Book to Series */}
                          <div className="pt-2 border-t border-border">
                            <Label className="text-xs text-muted-foreground mb-2 block">Add a book to this series:</Label>
                            {booksNotInSeries(s.id).length > 0 ? (
                              <Select 
                                onValueChange={(bookId) => addBookToSeries(s.id, bookId)}
                              >
                                <SelectTrigger className="rounded-full">
                                  <SelectValue placeholder="Select a book to add..." />
                                </SelectTrigger>
                                <SelectContent>
                                  {booksNotInSeries(s.id).map((book) => (
                                    <SelectItem key={book.id} value={book.id}>
                                      {book.title}
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            ) : (
                              <p className="text-xs text-muted-foreground text-center py-2">
                                All your books are already in a series
                              </p>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>
      
      {/* Add to Series Dialog */}
      <Dialog open={isAddToSeriesOpen} onOpenChange={setIsAddToSeriesOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="font-heading text-xl flex items-center gap-2">
              <FiLink className="text-primary" />
              Add to Series
            </DialogTitle>
            <DialogDescription>
              {selectedBookForSeries ? `Add "${selectedBookForSeries.title}" to a series` : 'Select a series'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 pt-4">
            {series.length === 0 ? (
              <div className="text-center py-6">
                <p className="text-sm text-muted-foreground mb-4">
                  No series yet. Create one first!
                </p>
                <Button 
                  variant="outline" 
                  className="rounded-full"
                  onClick={() => {
                    setIsAddToSeriesOpen(false);
                    setIsSeriesOpen(true);
                  }}
                >
                  <FiPlus className="mr-2" />
                  Create Series
                </Button>
              </div>
            ) : (
              <div className="space-y-2">
                {series.map((s) => (
                  <Button
                    key={s.id}
                    variant="outline"
                    className="w-full justify-start rounded-xl h-auto py-3"
                    onClick={() => addBookToSeries(s.id)}
                  >
                    <div className="text-left">
                      <div className="font-semibold">{s.name}</div>
                      <div className="text-xs text-muted-foreground">
                        {s.book_count || 0} book{s.book_count !== 1 ? 's' : ''} • Will be #{(s.book_count || 0) + 1}
                      </div>
                    </div>
                  </Button>
                ))}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
