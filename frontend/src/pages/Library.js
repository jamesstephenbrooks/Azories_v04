import { useState, useEffect, lazy, Suspense } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { FiSearch, FiBook, FiHeadphones, FiUser, FiStar, FiAward, FiTrendingUp, FiGrid, FiBox } from 'react-icons/fi';
import Navbar from '@/components/Navbar';

// Lazy load the 3D bookshelf component
const Bookshelf3D = lazy(() => import('@/components/Bookshelf3D'));

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function Library() {
  const [books, setBooks] = useState([]);
  const [featuredBooks, setFeaturedBooks] = useState([]);
  const [bestOfWeek, setBestOfWeek] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [genre, setGenre] = useState('All');
  const [genres, setGenres] = useState([]);
  const [activeTab, setActiveTab] = useState('all');
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or '3d'
  const [selectedBook, setSelectedBook] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchBooks();
    fetchFeaturedBooks();
    fetchGenres();
  }, []);

  useEffect(() => {
    if (activeTab === 'all') {
      fetchBooks();
    }
  }, [search, genre]);

  const fetchBooks = async () => {
    try {
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (genre && genre !== 'All') params.append('genre', genre);
      params.append('published_only', 'true');
      
      const res = await axios.get(`${API}/books?${params.toString()}`);
      setBooks(res.data);
    } catch (error) {
      console.error('Error fetching books:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchFeaturedBooks = async () => {
    try {
      const res = await axios.get(`${API}/books/featured`);
      const featured = res.data.filter(b => b.is_featured);
      const bestWeek = res.data.filter(b => b.is_best_of_week);
      setFeaturedBooks(featured);
      setBestOfWeek(bestWeek);
    } catch (error) {
      console.error('Error fetching featured books:', error);
    }
  };

  const fetchGenres = async () => {
    try {
      const res = await axios.get(`${API}/genres`);
      setGenres(['All', ...res.data.genres]);
    } catch (error) {
      console.error('Error fetching genres:', error);
    }
  };

  const BookCard = ({ book, index, isFeatured = false }) => (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
      className="book-card group cursor-pointer"
      onClick={() => navigate(`/read/${book.id}`)}
      data-testid={`book-card-${book.id}`}
    >
      <div className="book-perspective">
        <div className={`relative bg-card rounded-3xl overflow-hidden border border-border book-3d ${isFeatured ? 'ring-2 ring-primary/50' : ''}`}>
          {/* Featured/Best badges */}
          {(book.is_featured || book.is_best_of_week) && (
            <div className="absolute top-3 left-3 z-10 flex gap-2">
              {book.is_featured && (
                <span className="px-3 py-1 rounded-full bg-primary text-primary-foreground text-xs font-ui flex items-center gap-1">
                  <FiStar className="w-3 h-3" /> Featured
                </span>
              )}
              {book.is_best_of_week && (
                <span className="px-3 py-1 rounded-full bg-secondary text-secondary-foreground text-xs font-ui flex items-center gap-1">
                  <FiAward className="w-3 h-3" /> Best of Week
                </span>
              )}
            </div>
          )}
          
          {/* Book Cover */}
          <div className="aspect-[3/4] relative overflow-hidden">
            {book.cover_image ? (
              <img 
                src={book.cover_image} 
                alt={book.title}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center">
                <div className="text-center p-4">
                  <FiBook className="w-12 h-12 mx-auto text-primary/40 mb-2" />
                  <span className="font-heading text-lg text-primary/60">{book.cover_title || book.title}</span>
                </div>
              </div>
            )}
            
            {/* Hover overlay */}
            <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center gap-4">
              <Button 
                className="rounded-full"
                onClick={(e) => {
                  e.stopPropagation();
                  navigate(`/read/${book.id}`);
                }}
                data-testid={`read-btn-${book.id}`}
              >
                <FiBook className="mr-2" />
                Read
              </Button>
              <Button 
                variant="secondary" 
                className="rounded-full"
                onClick={(e) => {
                  e.stopPropagation();
                  navigate(`/read/${book.id}?audio=true`);
                }}
                data-testid={`listen-btn-${book.id}`}
              >
                <FiHeadphones className="mr-2" />
                Listen
              </Button>
            </div>
          </div>
          
          {/* Book Info */}
          <div className="p-5 space-y-2">
            <h3 className="font-heading text-lg font-semibold line-clamp-1">
              {book.title}
            </h3>
            <p className="font-body text-sm text-muted-foreground line-clamp-2">
              {book.description || 'A magical story awaits...'}
            </p>
            <div className="flex items-center justify-between pt-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <FiUser className="w-4 h-4" />
                <span className="font-ui">{book.author_name}</span>
              </div>
              <span className="text-xs px-3 py-1 rounded-full bg-primary/10 text-primary font-ui">
                {book.genre}
              </span>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );

  const FeaturedSection = ({ title, icon, books: sectionBooks, emptyMessage }) => (
    <div className="mb-16">
      <div className="flex items-center gap-3 mb-6">
        {icon}
        <h2 className="font-heading text-2xl font-bold">{title}</h2>
      </div>
      {sectionBooks.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {sectionBooks.map((book, index) => (
            <BookCard key={book.id} book={book} index={index} isFeatured />
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-muted/30 rounded-3xl">
          <p className="text-muted-foreground font-body">{emptyMessage}</p>
        </div>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      {/* Header */}
      <div className="pt-28 pb-8 px-6 md:px-12">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <h1 className="font-heading text-4xl md:text-5xl font-bold mb-4">
              Explore the Library
            </h1>
            <p className="font-body text-lg text-muted-foreground mb-8">
              Discover magical stories created by young authors
            </p>
          </motion.div>
        </div>
      </div>
      
      {/* Tabs and Content */}
      <div className="px-6 md:px-12 pb-20">
        <div className="max-w-7xl mx-auto">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="mb-8 bg-muted/50 p-1 rounded-full inline-flex">
              <TabsTrigger 
                value="all" 
                className="rounded-full px-6 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
                data-testid="tab-all-books"
              >
                All Books
              </TabsTrigger>
              <TabsTrigger 
                value="featured" 
                className="rounded-full px-6 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
                data-testid="tab-featured"
              >
                <FiStar className="mr-2 w-4 h-4" />
                Featured
              </TabsTrigger>
              <TabsTrigger 
                value="best" 
                className="rounded-full px-6 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
                data-testid="tab-best-week"
              >
                <FiAward className="mr-2 w-4 h-4" />
                Best of Week
              </TabsTrigger>
            </TabsList>
            
            <TabsContent value="all">
              {/* Search, Filters, and View Toggle */}
              <div className="flex flex-col sm:flex-row gap-4 mb-8">
                <div className="relative flex-1 max-w-md">
                  <FiSearch className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    type="text"
                    placeholder="Search by title or author..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="pl-12 rounded-full border-2 h-12"
                    data-testid="library-search-input"
                  />
                </div>
                
                <Select value={genre} onValueChange={setGenre}>
                  <SelectTrigger 
                    className="w-full sm:w-48 rounded-full border-2 h-12"
                    data-testid="genre-select"
                  >
                    <SelectValue placeholder="Genre" />
                  </SelectTrigger>
                  <SelectContent>
                    {genres.map((g) => (
                      <SelectItem key={g} value={g} data-testid={`genre-option-${g}`}>
                        {g}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                
                {/* View Mode Toggle */}
                <div className="flex gap-2 bg-muted/50 p-1 rounded-full">
                  <Button
                    variant={viewMode === 'grid' ? 'default' : 'ghost'}
                    size="icon"
                    onClick={() => setViewMode('grid')}
                    className="rounded-full w-10 h-10"
                    data-testid="view-grid-btn"
                  >
                    <FiGrid className="w-4 h-4" />
                  </Button>
                  <Button
                    variant={viewMode === '3d' ? 'default' : 'ghost'}
                    size="icon"
                    onClick={() => setViewMode('3d')}
                    className="rounded-full w-10 h-10"
                    data-testid="view-3d-btn"
                  >
                    <FiBox className="w-4 h-4" />
                  </Button>
                </div>
              </div>
              
              {/* 3D Bookshelf View */}
              {viewMode === '3d' ? (
                <div className="space-y-6">
                  <Suspense fallback={
                    <div className="w-full h-[600px] rounded-3xl bg-muted/30 flex items-center justify-center">
                      <div className="text-center space-y-4">
                        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
                        <p className="font-body text-muted-foreground">Loading 3D Library...</p>
                      </div>
                    </div>
                  }>
                    <Bookshelf3D 
                      books={books}
                      onSelectBook={(book) => setSelectedBook(book)}
                      selectedBook={selectedBook}
                    />
                  </Suspense>
                </div>
              ) : (
              /* Books Grid */
              loading ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
                  {[...Array(8)].map((_, i) => (
                    <div key={i} className="rounded-3xl overflow-hidden">
                      <div className="aspect-[3/4] shimmer" />
                      <div className="p-5 space-y-3">
                        <div className="h-6 w-3/4 shimmer rounded" />
                        <div className="h-4 w-full shimmer rounded" />
                        <div className="h-4 w-1/2 shimmer rounded" />
                      </div>
                    </div>
                  ))}
                </div>
              ) : books.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
                  {books.map((book, index) => (
                    <BookCard key={book.id} book={book} index={index} />
                  ))}
                </div>
              ) : (
                <div className="text-center py-20">
                  <FiBook className="w-16 h-16 mx-auto text-muted-foreground/50 mb-4" />
                  <h3 className="font-heading text-xl text-muted-foreground">
                    No books found
                  </h3>
                  <p className="font-body text-muted-foreground mt-2">
                    Try adjusting your search or filters
                  </p>
                </div>
              )
              )}
            </TabsContent>
            
            <TabsContent value="featured">
              <FeaturedSection 
                title="Featured Books" 
                icon={<FiStar className="w-6 h-6 text-primary" />}
                books={featuredBooks}
                emptyMessage="No featured books at the moment. Check back soon!"
              />
            </TabsContent>
            
            <TabsContent value="best">
              <FeaturedSection 
                title="Best of the Week" 
                icon={<FiAward className="w-6 h-6 text-secondary" />}
                books={bestOfWeek}
                emptyMessage="Best of the week books will appear here!"
              />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
