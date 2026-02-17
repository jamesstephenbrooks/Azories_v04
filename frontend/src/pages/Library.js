import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { FiSearch, FiBook, FiHeadphones, FiUser } from 'react-icons/fi';
import Navbar from '@/components/Navbar';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function Library() {
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [genre, setGenre] = useState('All');
  const [genres, setGenres] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    fetchBooks();
    fetchGenres();
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

  const fetchGenres = async () => {
    try {
      const res = await axios.get(`${API}/genres`);
      setGenres(['All', ...res.data.genres]);
    } catch (error) {
      console.error('Error fetching genres:', error);
    }
  };

  const BookCard = ({ book, index }) => (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
      className="book-card group cursor-pointer"
      onClick={() => navigate(`/read/${book.id}`)}
      data-testid={`book-card-${book.id}`}
    >
      <div className="book-perspective">
        <div className="relative bg-card rounded-3xl overflow-hidden border border-border book-3d">
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
                <FiBook className="w-16 h-16 text-primary/40" />
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

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      {/* Header */}
      <div className="pt-28 pb-12 px-6 md:px-12">
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
            
            {/* Search and Filters */}
            <div className="flex flex-col sm:flex-row gap-4">
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
            </div>
          </motion.div>
        </div>
      </div>
      
      {/* Books Grid */}
      <div className="px-6 md:px-12 pb-20">
        <div className="max-w-7xl mx-auto">
          {loading ? (
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
          )}
        </div>
      </div>
    </div>
  );
}
