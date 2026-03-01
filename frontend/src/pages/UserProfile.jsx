import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import axios from 'axios';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { toast } from 'sonner';
import Navbar from '@/components/Navbar';
import { 
  FiUser, FiBook, FiEye, FiHeart, FiUsers, FiEdit2, FiStar,
  FiMapPin, FiLink, FiTwitter, FiCalendar, FiAward, FiTrendingUp
} from 'react-icons/fi';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function UserProfile() {
  const { userId } = useParams();
  const navigate = useNavigate();
  const { user: currentUser } = useAuth();
  
  const [profile, setProfile] = useState(null);
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isFollowing, setIsFollowing] = useState(false);
  const [editData, setEditData] = useState({
    display_name: '',
    bio: '',
    location: '',
    website: '',
    twitter: ''
  });

  const isOwnProfile = currentUser?.id === userId || (!userId && currentUser);

  useEffect(() => {
    fetchProfile();
    fetchUserBooks();
  }, [userId, currentUser]);

  const fetchProfile = async () => {
    try {
      const targetId = userId || currentUser?.id;
      if (!targetId) return;
      
      const res = await axios.get(`${API}/users/${targetId}/profile`);
      setProfile(res.data);
      setEditData({
        display_name: res.data.display_name || res.data.name || '',
        bio: res.data.bio || '',
        location: res.data.location || '',
        website: res.data.website || '',
        twitter: res.data.twitter || ''
      });
      setIsFollowing(res.data.is_following || false);
    } catch (error) {
      // If profile doesn't exist, create default from user data
      if (currentUser && isOwnProfile) {
        setProfile({
          id: currentUser.id,
          name: currentUser.name,
          display_name: currentUser.name,
          email: currentUser.email,
          bio: '',
          avatar: null,
          followers_count: 0,
          following_count: 0,
          books_count: 0,
          total_reads: 0
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchUserBooks = async () => {
    try {
      const targetId = userId || currentUser?.id;
      if (!targetId) return;
      
      const res = await axios.get(`${API}/users/${targetId}/books`);
      setBooks(res.data);
    } catch (error) {
      // Fallback to my books if viewing own profile
      if (isOwnProfile) {
        try {
          const res = await axios.get(`${API}/books/my`);
          setBooks(res.data.filter(b => b.is_published));
        } catch {}
      }
    }
  };

  const handleUpdateProfile = async () => {
    try {
      const token = localStorage.getItem('azories-token');
      await axios.put(`${API}/users/profile`, editData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProfile({ ...profile, ...editData });
      setIsEditOpen(false);
      toast.success('Profile updated!');
    } catch (error) {
      console.error('Profile update error:', error);
      toast.error(error.response?.data?.detail || 'Failed to update profile');
    }
  };

  const handleFollow = async () => {
    try {
      if (isFollowing) {
        await axios.delete(`${API}/users/${userId}/follow`);
        setIsFollowing(false);
        setProfile(p => ({ ...p, followers_count: (p.followers_count || 1) - 1 }));
      } else {
        await axios.post(`${API}/users/${userId}/follow`);
        setIsFollowing(true);
        setProfile(p => ({ ...p, followers_count: (p.followers_count || 0) + 1 }));
      }
    } catch (error) {
      toast.error('Failed to update follow status');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="flex items-center justify-center h-[60vh]">
          <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Profile Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="relative"
        >
          {/* Banner */}
          <div className="h-40 bg-gradient-to-r from-primary/30 via-purple-500/30 to-pink-500/30 rounded-t-2xl" />
          
          {/* Profile Info */}
          <div className="relative px-6 pb-6 bg-card rounded-b-2xl shadow-lg">
            {/* Avatar */}
            <div className="absolute -top-16 left-6">
              <div className="w-32 h-32 rounded-full bg-gradient-to-br from-primary to-purple-500 p-1">
                <div className="w-full h-full rounded-full bg-background flex items-center justify-center overflow-hidden">
                  {profile?.avatar ? (
                    <img src={profile.avatar} alt={profile.name} className="w-full h-full object-cover" />
                  ) : (
                    <span className="text-4xl font-bold text-primary">
                      {(profile?.display_name || profile?.name || 'U').charAt(0).toUpperCase()}
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex justify-end pt-4 gap-2">
              {isOwnProfile ? (
                <Button onClick={() => setIsEditOpen(true)} variant="outline" className="rounded-full">
                  <FiEdit2 className="w-4 h-4 mr-2" />
                  Edit Profile
                </Button>
              ) : (
                <Button 
                  onClick={handleFollow}
                  variant={isFollowing ? "outline" : "default"}
                  className="rounded-full"
                >
                  <FiUsers className="w-4 h-4 mr-2" />
                  {isFollowing ? 'Following' : 'Follow'}
                </Button>
              )}
            </div>

            {/* Name & Bio */}
            <div className="mt-8">
              <h1 className="text-2xl font-bold">{profile?.display_name || profile?.name}</h1>
              {profile?.bio && (
                <p className="text-muted-foreground mt-2">{profile.bio}</p>
              )}
              
              {/* Meta Info */}
              <div className="flex flex-wrap gap-4 mt-4 text-sm text-muted-foreground">
                {profile?.location && (
                  <span className="flex items-center gap-1">
                    <FiMapPin className="w-4 h-4" />
                    {profile.location}
                  </span>
                )}
                {profile?.website && (
                  <a href={profile.website} target="_blank" rel="noopener noreferrer" 
                     className="flex items-center gap-1 hover:text-primary transition-colors">
                    <FiLink className="w-4 h-4" />
                    Website
                  </a>
                )}
                {profile?.twitter && (
                  <a href={`https://twitter.com/${profile.twitter}`} target="_blank" rel="noopener noreferrer"
                     className="flex items-center gap-1 hover:text-primary transition-colors">
                    <FiTwitter className="w-4 h-4" />
                    @{profile.twitter}
                  </a>
                )}
                <span className="flex items-center gap-1">
                  <FiCalendar className="w-4 h-4" />
                  Joined {new Date(profile?.created_at || Date.now()).toLocaleDateString('en', { month: 'short', year: 'numeric' })}
                </span>
              </div>

              {/* Stats */}
              <div className="flex gap-6 mt-6 pt-6 border-t">
                <div className="text-center">
                  <p className="text-2xl font-bold">{profile?.followers_count || 0}</p>
                  <p className="text-sm text-muted-foreground">Followers</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold">{profile?.following_count || 0}</p>
                  <p className="text-sm text-muted-foreground">Following</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold">{books.length || profile?.books_count || 0}</p>
                  <p className="text-sm text-muted-foreground">Books</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold">{profile?.total_reads || 0}</p>
                  <p className="text-sm text-muted-foreground">Total Reads</p>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Achievement Badges */}
        {(profile?.badges?.length > 0 || isOwnProfile) && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="mt-6"
          >
            <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
              <FiAward className="text-yellow-500" />
              Achievements
            </h2>
            <div className="flex flex-wrap gap-3">
              {profile?.subscription === 'pro' && (
                <div className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-yellow-500/10 to-orange-500/10 rounded-full border border-yellow-500/20">
                  <FiStar className="text-yellow-500" />
                  <span className="text-sm font-medium">Pro Creator</span>
                </div>
              )}
              {(profile?.books_count >= 5 || books.length >= 5) && (
                <div className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-full border border-purple-500/20">
                  <FiBook className="text-purple-500" />
                  <span className="text-sm font-medium">Prolific Author</span>
                </div>
              )}
              {(profile?.total_reads >= 100) && (
                <div className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500/10 to-cyan-500/10 rounded-full border border-blue-500/20">
                  <FiTrendingUp className="text-blue-500" />
                  <span className="text-sm font-medium">Rising Star</span>
                </div>
              )}
            </div>
          </motion.div>
        )}

        {/* Published Books */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mt-8"
        >
          <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
            <FiBook />
            {isOwnProfile ? 'Your Published Books' : 'Published Books'}
          </h2>
          
          {books.length > 0 ? (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {books.map((book, idx) => (
                <motion.div
                  key={book.id}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: idx * 0.05 }}
                  className="cursor-pointer group"
                  onClick={() => navigate(`/read/${book.id}`)}
                >
                  <Card className="overflow-hidden border-0 shadow-lg hover:shadow-xl transition-all">
                    <div className="aspect-[3/4] relative">
                      {book.cover_image ? (
                        <img 
                          src={book.cover_image} 
                          alt={book.title}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        />
                      ) : (
                        <div className="w-full h-full bg-gradient-to-br from-primary/20 to-purple-500/20 flex items-center justify-center">
                          <FiBook className="w-12 h-12 text-primary/30" />
                        </div>
                      )}
                      <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                    <CardContent className="p-3">
                      <h3 className="font-medium text-sm line-clamp-1">{book.title}</h3>
                      <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <FiEye className="w-3 h-3" />
                          {book.view_count || 0}
                        </span>
                        <span className="flex items-center gap-1">
                          <FiHeart className="w-3 h-3" />
                          {book.read_count || 0}
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          ) : (
            <Card className="p-8 text-center">
              <FiBook className="w-12 h-12 mx-auto text-muted-foreground/30 mb-4" />
              <p className="text-muted-foreground">
                {isOwnProfile ? "You haven't published any books yet" : "No published books yet"}
              </p>
              {isOwnProfile && (
                <Button onClick={() => navigate('/dashboard')} className="mt-4 rounded-full">
                  Create Your First Book
                </Button>
              )}
            </Card>
          )}
        </motion.div>
      </div>

      {/* Edit Profile Dialog */}
      <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Edit Profile</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Display Name</label>
              <Input
                value={editData.display_name}
                onChange={e => setEditData({ ...editData, display_name: e.target.value })}
                placeholder="Your display name"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Bio</label>
              <Textarea
                value={editData.bio}
                onChange={e => setEditData({ ...editData, bio: e.target.value })}
                placeholder="Tell readers about yourself..."
                rows={3}
              />
            </div>
            <div>
              <label className="text-sm font-medium">Location</label>
              <Input
                value={editData.location}
                onChange={e => setEditData({ ...editData, location: e.target.value })}
                placeholder="City, Country"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Website</label>
              <Input
                value={editData.website}
                onChange={e => setEditData({ ...editData, website: e.target.value })}
                placeholder="https://yoursite.com"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Twitter Handle</label>
              <Input
                value={editData.twitter}
                onChange={e => setEditData({ ...editData, twitter: e.target.value })}
                placeholder="username (without @)"
              />
            </div>
            <Button onClick={handleUpdateProfile} className="w-full rounded-full">
              Save Changes
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
