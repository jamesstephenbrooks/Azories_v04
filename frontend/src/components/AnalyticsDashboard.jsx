import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  FiEye, FiBook, FiUsers, FiTrendingUp, FiBarChart2, FiCalendar,
  FiArrowUp, FiArrowDown, FiMinus
} from 'react-icons/fi';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AnalyticsDashboard({ books = [] }) {
  const [selectedBook, setSelectedBook] = useState(null);
  const [bookAnalytics, setBookAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [overallStats, setOverallStats] = useState({
    totalViews: 0,
    totalReads: 0,
    totalBooks: 0,
    publishedBooks: 0
  });

  useEffect(() => {
    // Calculate overall stats from books
    const stats = books.reduce((acc, book) => ({
      totalViews: acc.totalViews + (book.view_count || 0),
      totalReads: acc.totalReads + (book.read_count || 0),
      totalBooks: acc.totalBooks + 1,
      publishedBooks: acc.publishedBooks + (book.is_published ? 1 : 0)
    }), { totalViews: 0, totalReads: 0, totalBooks: 0, publishedBooks: 0 });
    setOverallStats(stats);
  }, [books]);

  const fetchBookAnalytics = async (bookId) => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/books/${bookId}/analytics`);
      setBookAnalytics(res.data);
    } catch (error) {
      console.error('Failed to fetch analytics');
    } finally {
      setLoading(false);
    }
  };

  const handleBookSelect = (book) => {
    setSelectedBook(book);
    fetchBookAnalytics(book.id);
  };

  const StatCard = ({ icon: Icon, title, value, change, color = "primary" }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="relative overflow-hidden"
    >
      <Card className="border-0 shadow-lg bg-gradient-to-br from-background to-muted/30">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground mb-1">{title}</p>
              <p className="text-3xl font-bold">{value.toLocaleString()}</p>
              {change !== undefined && (
                <div className={`flex items-center gap-1 mt-2 text-sm ${
                  change > 0 ? 'text-green-500' : change < 0 ? 'text-red-500' : 'text-muted-foreground'
                }`}>
                  {change > 0 ? <FiArrowUp /> : change < 0 ? <FiArrowDown /> : <FiMinus />}
                  <span>{Math.abs(change)}% vs last week</span>
                </div>
              )}
            </div>
            <div className={`p-4 rounded-2xl bg-${color}/10`}>
              <Icon className={`w-8 h-8 text-${color}`} />
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );

  const MiniBarChart = ({ data = [] }) => {
    const maxValue = Math.max(...data.map(d => d.count), 1);
    return (
      <div className="flex items-end gap-1 h-20">
        {data.map((item, idx) => (
          <div key={idx} className="flex-1 flex flex-col items-center gap-1">
            <motion.div
              initial={{ height: 0 }}
              animate={{ height: `${(item.count / maxValue) * 100}%` }}
              transition={{ delay: idx * 0.1, duration: 0.5 }}
              className="w-full bg-primary/80 rounded-t min-h-[4px]"
            />
            <span className="text-[10px] text-muted-foreground">
              {new Date(item.date).toLocaleDateString('en', { weekday: 'short' }).charAt(0)}
            </span>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="space-y-8" data-testid="analytics-dashboard">
      {/* Overall Stats */}
      <div>
        <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
          <FiBarChart2 className="text-primary" />
          Your Performance
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard 
            icon={FiEye} 
            title="Total Views" 
            value={overallStats.totalViews}
            color="blue-500"
          />
          <StatCard 
            icon={FiBook} 
            title="Total Reads" 
            value={overallStats.totalReads}
            color="green-500"
          />
          <StatCard 
            icon={FiUsers} 
            title="Published Books" 
            value={overallStats.publishedBooks}
            color="purple-500"
          />
          <StatCard 
            icon={FiTrendingUp} 
            title="Avg. Reads/Book" 
            value={overallStats.totalBooks > 0 ? Math.round(overallStats.totalReads / overallStats.totalBooks) : 0}
            color="orange-500"
          />
        </div>
      </div>

      {/* Book Performance Table */}
      <div>
        <h3 className="text-xl font-bold mb-4">Book Performance</h3>
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="text-left p-4 font-medium">Book</th>
                    <th className="text-center p-4 font-medium">Status</th>
                    <th className="text-center p-4 font-medium">Views</th>
                    <th className="text-center p-4 font-medium">Reads</th>
                    <th className="text-center p-4 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {books.map((book, idx) => (
                    <motion.tr 
                      key={book.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.05 }}
                      className="border-t hover:bg-muted/30 transition-colors"
                    >
                      <td className="p-4">
                        <div className="flex items-center gap-3">
                          {book.cover_image ? (
                            <img 
                              src={book.cover_image} 
                              alt={book.title}
                              className="w-10 h-14 object-cover rounded"
                            />
                          ) : (
                            <div className="w-10 h-14 bg-gradient-to-br from-primary/20 to-secondary/20 rounded flex items-center justify-center">
                              <FiBook className="text-primary/50" />
                            </div>
                          )}
                          <div>
                            <p className="font-medium line-clamp-1">{book.title}</p>
                            <p className="text-xs text-muted-foreground">{book.genre}</p>
                          </div>
                        </div>
                      </td>
                      <td className="p-4 text-center">
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          book.is_published 
                            ? 'bg-green-500/10 text-green-500' 
                            : 'bg-yellow-500/10 text-yellow-500'
                        }`}>
                          {book.is_published ? 'Published' : 'Draft'}
                        </span>
                      </td>
                      <td className="p-4 text-center font-mono">
                        {(book.view_count || 0).toLocaleString()}
                      </td>
                      <td className="p-4 text-center font-mono">
                        {(book.read_count || 0).toLocaleString()}
                      </td>
                      <td className="p-4 text-center">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleBookSelect(book)}
                          data-testid={`view-analytics-${book.id}`}
                        >
                          <FiBarChart2 className="w-4 h-4" />
                        </Button>
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Analytics Modal */}
      {selectedBook && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => setSelectedBook(null)}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-background rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-auto"
            onClick={e => e.stopPropagation()}
          >
            <div className="p-6 border-b">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-bold">{selectedBook.title}</h3>
                  <p className="text-sm text-muted-foreground">Detailed Analytics</p>
                </div>
                <Button variant="ghost" size="icon" onClick={() => setSelectedBook(null)}>
                  ×
                </Button>
              </div>
            </div>
            
            <div className="p-6 space-y-6">
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                </div>
              ) : bookAnalytics ? (
                <>
                  <div className="grid grid-cols-3 gap-4">
                    <Card>
                      <CardContent className="p-4 text-center">
                        <FiEye className="w-6 h-6 mx-auto text-blue-500 mb-2" />
                        <p className="text-2xl font-bold">{bookAnalytics.view_count}</p>
                        <p className="text-xs text-muted-foreground">Views</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="p-4 text-center">
                        <FiBook className="w-6 h-6 mx-auto text-green-500 mb-2" />
                        <p className="text-2xl font-bold">{bookAnalytics.read_count}</p>
                        <p className="text-xs text-muted-foreground">Reads</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="p-4 text-center">
                        <FiUsers className="w-6 h-6 mx-auto text-purple-500 mb-2" />
                        <p className="text-2xl font-bold">{bookAnalytics.unique_readers}</p>
                        <p className="text-xs text-muted-foreground">Unique Readers</p>
                      </CardContent>
                    </Card>
                  </div>

                  {bookAnalytics.daily_reads?.length > 0 && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-sm flex items-center gap-2">
                          <FiCalendar className="w-4 h-4" />
                          Reads This Week
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <MiniBarChart data={bookAnalytics.daily_reads} />
                      </CardContent>
                    </Card>
                  )}

                  <Card>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">Completion Rate</span>
                        <span className="font-bold">{Math.round(bookAnalytics.avg_completion_rate * 100)}%</span>
                      </div>
                      <div className="mt-2 h-2 bg-muted rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${bookAnalytics.avg_completion_rate * 100}%` }}
                          className="h-full bg-gradient-to-r from-primary to-green-500"
                        />
                      </div>
                    </CardContent>
                  </Card>
                </>
              ) : (
                <p className="text-center text-muted-foreground">No analytics data available</p>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </div>
  );
}
