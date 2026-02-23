import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import { 
  FiShield, FiBook, FiCheck, FiX, FiAlertTriangle, 
  FiEye, FiClock, FiUser, FiArrowLeft 
} from 'react-icons/fi';

const API = process.env.REACT_APP_BACKEND_URL;

export default function AdminDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [pendingBooks, setPendingBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(null);
  
  const VIP_EMAILS = ['arianamillb@icloud.com', 'jamesstephenbrooks@outlook.com'];
  const isAdmin = user && VIP_EMAILS.includes(user.email);

  useEffect(() => {
    if (user && isAdmin) {
      fetchPendingBooks();
    }
  }, [user, isAdmin]);

  const fetchPendingBooks = async () => {
    try {
      const token = localStorage.getItem('azories-token');
      const res = await fetch(`${API}/api/admin/pending-reviews`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setPendingBooks(data.books || []);
      }
    } catch (error) {
      console.error('Failed to fetch pending books:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (bookId, bookTitle) => {
    setProcessing(bookId);
    try {
      const token = localStorage.getItem('azories-token');
      const res = await fetch(`${API}/api/admin/books/${bookId}/approve`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        toast.success(`"${bookTitle}" has been approved and published!`);
        setPendingBooks(prev => prev.filter(b => b.id !== bookId));
      } else {
        toast.error('Failed to approve book');
      }
    } catch (error) {
      toast.error('Error approving book');
    } finally {
      setProcessing(null);
    }
  };

  const handleReject = async (bookId, bookTitle) => {
    const reason = window.prompt('Please provide a reason for rejection (optional):');
    setProcessing(bookId);
    try {
      const token = localStorage.getItem('azories-token');
      const res = await fetch(`${API}/api/admin/books/${bookId}/reject?reason=${encodeURIComponent(reason || '')}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        toast.success(`"${bookTitle}" has been rejected`);
        setPendingBooks(prev => prev.filter(b => b.id !== bookId));
      } else {
        toast.error('Failed to reject book');
      }
    } catch (error) {
      toast.error('Error rejecting book');
    } finally {
      setProcessing(null);
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-background to-background/95 flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="pt-6 text-center">
            <FiShield className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
            <h2 className="text-xl font-bold mb-2">Admin Access Required</h2>
            <p className="text-muted-foreground mb-4">Please log in to access the admin dashboard.</p>
            <Button onClick={() => navigate('/auth')}>Sign In</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-background to-background/95 flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="pt-6 text-center">
            <FiShield className="w-16 h-16 mx-auto text-red-500 mb-4" />
            <h2 className="text-xl font-bold mb-2">Access Denied</h2>
            <p className="text-muted-foreground mb-4">You don't have permission to access the admin dashboard.</p>
            <Button variant="outline" onClick={() => navigate('/')}>Go Home</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-background/95">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigate('/')}>
              <FiArrowLeft className="w-5 h-5" />
            </Button>
            <div>
              <h1 className="text-xl font-bold flex items-center gap-2">
                <FiShield className="text-purple-500" />
                Admin Dashboard
              </h1>
              <p className="text-sm text-muted-foreground">Content Moderation & Approvals</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <FiUser className="w-4 h-4" />
            {user.email}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Pending Reviews</p>
                  <p className="text-3xl font-bold text-amber-500">{pendingBooks.length}</p>
                </div>
                <FiClock className="w-8 h-8 text-amber-500/50" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Flagged Content</p>
                  <p className="text-3xl font-bold text-red-500">
                    {pendingBooks.filter(b => b.moderation_flags?.length > 0).length}
                  </p>
                </div>
                <FiAlertTriangle className="w-8 h-8 text-red-500/50" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Safe to Approve</p>
                  <p className="text-3xl font-bold text-green-500">
                    {pendingBooks.filter(b => !b.moderation_flags?.length).length}
                  </p>
                </div>
                <FiCheck className="w-8 h-8 text-green-500/50" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Pending Books */}
        <Card>
          <CardHeader>
            <CardTitle>Books Pending Review</CardTitle>
            <CardDescription>Review and approve or reject book submissions</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-12">
                <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                <p className="text-muted-foreground">Loading pending books...</p>
              </div>
            ) : pendingBooks.length === 0 ? (
              <div className="text-center py-12">
                <FiCheck className="w-16 h-16 mx-auto text-green-500/50 mb-4" />
                <h3 className="text-lg font-semibold mb-2">All Caught Up!</h3>
                <p className="text-muted-foreground">No books pending review at this time.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {pendingBooks.map((book) => (
                  <div 
                    key={book.id}
                    className={`p-4 rounded-xl border ${
                      book.moderation_flags?.length > 0 
                        ? 'border-red-500/50 bg-red-500/5' 
                        : 'border-border bg-muted/30'
                    }`}
                  >
                    <div className="flex items-start gap-4">
                      {/* Book Cover */}
                      <div className="w-20 h-28 rounded-lg overflow-hidden bg-muted flex-shrink-0">
                        {book.cover_image ? (
                          <img src={book.cover_image} alt={book.title} className="w-full h-full object-cover" />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center">
                            <FiBook className="w-8 h-8 text-muted-foreground" />
                          </div>
                        )}
                      </div>
                      
                      {/* Book Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <h3 className="font-semibold text-lg truncate">{book.title}</h3>
                            <p className="text-sm text-muted-foreground">by {book.author_name}</p>
                          </div>
                          {book.moderation_flags?.length > 0 && (
                            <span className="px-2 py-1 bg-red-500/20 text-red-500 text-xs rounded-full flex items-center gap-1 flex-shrink-0">
                              <FiAlertTriangle className="w-3 h-3" />
                              Flagged
                            </span>
                          )}
                        </div>
                        
                        {/* Moderation Info */}
                        {book.moderation_flags?.length > 0 && (
                          <div className="mt-2 p-2 bg-red-500/10 rounded-lg">
                            <p className="text-xs text-red-400 font-medium mb-1">Flagged Categories:</p>
                            <div className="flex flex-wrap gap-1">
                              {book.moderation_flags.map((flag, i) => (
                                <span key={i} className="px-2 py-0.5 bg-red-500/20 text-red-400 text-xs rounded">
                                  {flag}
                                </span>
                              ))}
                            </div>
                            {book.moderation_message && (
                              <p className="text-xs text-red-300 mt-2">{book.moderation_message}</p>
                            )}
                          </div>
                        )}
                        
                        <p className="text-sm text-muted-foreground mt-2 line-clamp-2">
                          {book.description || 'No description provided'}
                        </p>
                        
                        <div className="flex items-center gap-2 mt-3 text-xs text-muted-foreground">
                          <span>{book.genre}</span>
                          <span>•</span>
                          <span>{book.age_rating || 'All Ages'}</span>
                          {book.publish_requested_at && (
                            <>
                              <span>•</span>
                              <span>Submitted: {new Date(book.publish_requested_at).toLocaleDateString()}</span>
                            </>
                          )}
                        </div>
                      </div>
                      
                      {/* Actions */}
                      <div className="flex flex-col gap-2 flex-shrink-0">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => navigate(`/read/${book.id}`)}
                          className="text-xs"
                        >
                          <FiEye className="w-3 h-3 mr-1" />
                          Preview
                        </Button>
                        <Button
                          size="sm"
                          onClick={() => handleApprove(book.id, book.title)}
                          disabled={processing === book.id}
                          className="bg-green-600 hover:bg-green-700 text-xs"
                        >
                          <FiCheck className="w-3 h-3 mr-1" />
                          Approve
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => handleReject(book.id, book.title)}
                          disabled={processing === book.id}
                          className="text-xs"
                        >
                          <FiX className="w-3 h-3 mr-1" />
                          Reject
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
