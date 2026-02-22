import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { FiBook, FiRefreshCw, FiArrowRight } from 'react-icons/fi';
import { Button } from '@/components/ui/button';
import AnimatedBookCard from './AnimatedBookCard';

const API = process.env.REACT_APP_BACKEND_URL;

export default function BookRecommendations({ userId }) {
  const [recommendations, setRecommendations] = useState([]);
  const [basedOn, setBasedOn] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const fetchRecommendations = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/api/user/recommendations`);
      setRecommendations(res.data.recommendations || []);
      setBasedOn(res.data.based_on || []);
    } catch (error) {
      console.error('Failed to fetch recommendations:', error);
      // Fallback to popular books - API returns array directly
      try {
        const fallback = await axios.get(`${API}/api/books`, {
          params: { limit: 6, published_only: 'true' }
        });
        // API returns array directly, not {books: [...]}
        const books = Array.isArray(fallback.data) ? fallback.data : (fallback.data.books || []);
        setRecommendations(books.slice(0, 6));
        setBasedOn(['Popular in Azories']);
      } catch (e) {
        console.error('Failed to fetch fallback:', e);
        setRecommendations([]);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, [userId]);

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-6 w-48 bg-muted animate-pulse rounded" />
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="aspect-[3/4] bg-muted animate-pulse rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  if (recommendations.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2">
            <span className="text-2xl">✨</span>
            Recommended for You
          </h2>
          <p className="text-sm text-muted-foreground">
            Based on: {basedOn.join(', ')}
          </p>
        </div>
        <Button 
          variant="ghost" 
          size="sm" 
          onClick={fetchRecommendations}
          className="gap-2"
        >
          <FiRefreshCw className="w-4 h-4" />
          Refresh
        </Button>
      </div>

      {/* Book Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {recommendations.slice(0, 6).map((book, index) => (
          <div key={book.id}>
            <AnimatedBookCard 
              book={book}
              onClick={() => navigate(`/read/${book.id}`)}
            />
          </div>
        ))}
      </div>

      {/* View All Button */}
      <div className="flex justify-center pt-2">
        <Button 
          variant="outline" 
          onClick={() => navigate('/library')}
          className="rounded-full gap-2"
        >
          Explore Library
          <FiArrowRight className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
}
