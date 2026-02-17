import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import axios from 'axios';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { toast } from 'sonner';
import { 
  FiArrowLeft, FiPlus, FiSave, FiTrash2, FiImage, FiVideo, FiUpload,
  FiChevronLeft, FiChevronRight, FiBook, FiSettings, FiPlay, FiLoader
} from 'react-icons/fi';
import Navbar from '@/components/Navbar';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function BookEditor() {
  const { bookId } = useParams();
  const navigate = useNavigate();
  const { user, loading: authLoading } = useAuth();
  const fileInputRef = useRef(null);
  
  const [book, setBook] = useState(null);
  const [chapters, setChapters] = useState([]);
  const [selectedChapter, setSelectedChapter] = useState(null);
  const [pages, setPages] = useState([]);
  const [selectedPage, setSelectedPage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  // AI generation state
  const [imagePrompt, setImagePrompt] = useState('');
  const [videoPrompt, setVideoPrompt] = useState('');
  const [generatingImage, setGeneratingImage] = useState(false);
  const [generatingVideo, setGeneratingVideo] = useState(false);
  
  // New chapter/page dialogs
  const [newChapterOpen, setNewChapterOpen] = useState(false);
  const [newChapterTitle, setNewChapterTitle] = useState('');
  const [creatingChapter, setCreatingChapter] = useState(false);

  useEffect(() => {
    if (!authLoading && !user) {
      navigate('/auth', { state: { from: `/editor/${bookId}` } });
    }
  }, [user, authLoading, navigate, bookId]);

  useEffect(() => {
    if (user && bookId) {
      fetchBook();
      fetchChapters();
    }
  }, [user, bookId]);

  useEffect(() => {
    if (selectedChapter) {
      fetchPages(selectedChapter.id);
    }
  }, [selectedChapter]);

  const fetchBook = async () => {
    try {
      const res = await axios.get(`${API}/books/${bookId}`);
      setBook(res.data);
    } catch (error) {
      toast.error('Failed to load book');
      navigate('/dashboard');
    } finally {
      setLoading(false);
    }
  };

  const fetchChapters = async () => {
    try {
      const res = await axios.get(`${API}/books/${bookId}/chapters`);
      setChapters(res.data);
      if (res.data.length > 0 && !selectedChapter) {
        setSelectedChapter(res.data[0]);
      }
    } catch (error) {
      console.error('Error fetching chapters:', error);
    }
  };

  const fetchPages = async (chapterId) => {
    try {
      const res = await axios.get(`${API}/chapters/${chapterId}/pages`);
      setPages(res.data);
      if (res.data.length > 0) {
        setSelectedPage(res.data[0]);
      } else {
        setSelectedPage(null);
      }
    } catch (error) {
      console.error('Error fetching pages:', error);
    }
  };

  const createChapter = async () => {
    if (!newChapterTitle.trim()) {
      toast.error('Please enter a chapter title');
      return;
    }
    
    setCreatingChapter(true);
    try {
      const res = await axios.post(`${API}/books/${bookId}/chapters`, {
        title: newChapterTitle
      });
      toast.success('Chapter created!');
      setNewChapterOpen(false);
      setNewChapterTitle('');
      await fetchChapters();
      setSelectedChapter(res.data);
    } catch (error) {
      toast.error('Failed to create chapter');
    } finally {
      setCreatingChapter(false);
    }
  };

  const deleteChapter = async (chapterId) => {
    if (!window.confirm('Delete this chapter and all its pages?')) return;
    
    try {
      await axios.delete(`${API}/chapters/${chapterId}`);
      toast.success('Chapter deleted');
      await fetchChapters();
      if (selectedChapter?.id === chapterId) {
        setSelectedChapter(chapters[0] || null);
      }
    } catch (error) {
      toast.error('Failed to delete chapter');
    }
  };

  const createPage = async () => {
    if (!selectedChapter) {
      toast.error('Please select or create a chapter first');
      return;
    }
    
    try {
      const res = await axios.post(`${API}/chapters/${selectedChapter.id}/pages`, {
        text_content: ''
      });
      toast.success('Page added!');
      await fetchPages(selectedChapter.id);
      setSelectedPage(res.data);
    } catch (error) {
      toast.error('Failed to create page');
    }
  };

  const savePage = async () => {
    if (!selectedPage) return;
    
    setSaving(true);
    try {
      await axios.put(`${API}/pages/${selectedPage.id}`, {
        text_content: selectedPage.text_content,
        image_url: selectedPage.image_url,
        video_url: selectedPage.video_url
      });
      toast.success('Page saved!');
    } catch (error) {
      toast.error('Failed to save page');
    } finally {
      setSaving(false);
    }
  };

  const deletePage = async (pageId) => {
    if (!window.confirm('Delete this page?')) return;
    
    try {
      await axios.delete(`${API}/pages/${pageId}`);
      toast.success('Page deleted');
      await fetchPages(selectedChapter.id);
    } catch (error) {
      toast.error('Failed to delete page');
    }
  };

  const generateImage = async () => {
    if (!imagePrompt.trim()) {
      toast.error('Please enter a prompt for the image');
      return;
    }
    
    setGeneratingImage(true);
    try {
      const res = await axios.post(`${API}/ai/generate-image`, {
        prompt: imagePrompt,
        book_id: bookId
      });
      
      if (res.data.success) {
        const imageUrl = `data:image/png;base64,${res.data.image_base64}`;
        setSelectedPage({ ...selectedPage, image_url: imageUrl });
        toast.success('Image generated!');
        setImagePrompt('');
      }
    } catch (error) {
      toast.error('Failed to generate image');
    } finally {
      setGeneratingImage(false);
    }
  };

  const generateVideo = async () => {
    if (!videoPrompt.trim()) {
      toast.error('Please enter a prompt for the video');
      return;
    }
    
    setGeneratingVideo(true);
    toast.info('Generating video... This may take a few minutes.');
    
    try {
      const res = await axios.post(`${API}/ai/generate-video`, {
        prompt: videoPrompt,
        duration: 4,
        size: '1280x720'
      });
      
      if (res.data.success) {
        const videoUrl = `data:video/mp4;base64,${res.data.video_base64}`;
        setSelectedPage({ ...selectedPage, video_url: videoUrl });
        toast.success('Video generated!');
        setVideoPrompt('');
      }
    } catch (error) {
      toast.error('Failed to generate video');
    } finally {
      setGeneratingVideo(false);
    }
  };

  const handleImageUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const res = await axios.post(`${API}/upload/image`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      if (res.data.success) {
        setSelectedPage({ ...selectedPage, image_url: res.data.image_url });
        toast.success('Image uploaded!');
      }
    } catch (error) {
      toast.error('Failed to upload image');
    }
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="min-h-screen bg-background">
      {/* Top Bar */}
      <div className="glass fixed top-0 left-0 right-0 z-40 px-4 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
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
              <h1 className="font-heading text-lg font-semibold">
                {book?.title || 'Book Editor'}
              </h1>
              <p className="font-body text-sm text-muted-foreground">
                {selectedChapter?.title || 'No chapter selected'}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={() => navigate(`/read/${bookId}`)}
              className="rounded-full"
              data-testid="preview-book"
            >
              <FiBook className="mr-2 w-4 h-4" />
              Preview
            </Button>
            <Button
              onClick={savePage}
              disabled={saving || !selectedPage}
              className="rounded-full"
              data-testid="save-page"
            >
              <FiSave className="mr-2 w-4 h-4" />
              {saving ? 'Saving...' : 'Save'}
            </Button>
          </div>
        </div>
      </div>
      
      <div className="pt-20 flex h-[calc(100vh-5rem)]">
        {/* Left Sidebar - Chapters & Pages */}
        <div className="w-64 border-r border-border bg-card flex flex-col">
          <div className="p-4 border-b border-border">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-heading font-semibold">Chapters</h3>
              <Dialog open={newChapterOpen} onOpenChange={setNewChapterOpen}>
                <DialogTrigger asChild>
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    className="rounded-full w-8 h-8"
                    data-testid="add-chapter-btn"
                  >
                    <FiPlus className="w-4 h-4" />
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-sm">
                  <DialogHeader>
                    <DialogTitle className="font-heading">New Chapter</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4 pt-4">
                    <Input
                      placeholder="Chapter title"
                      value={newChapterTitle}
                      onChange={(e) => setNewChapterTitle(e.target.value)}
                      className="rounded-full border-2"
                      data-testid="new-chapter-title"
                    />
                    <Button 
                      onClick={createChapter}
                      disabled={creatingChapter}
                      className="w-full rounded-full"
                      data-testid="submit-new-chapter"
                    >
                      {creatingChapter ? 'Creating...' : 'Create Chapter'}
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
            </div>
            
            <ScrollArea className="h-32">
              {chapters.map((chapter) => (
                <div
                  key={chapter.id}
                  className={`flex items-center justify-between p-2 rounded-lg cursor-pointer mb-1 ${
                    selectedChapter?.id === chapter.id 
                      ? 'bg-primary/10 text-primary' 
                      : 'hover:bg-muted'
                  }`}
                  onClick={() => setSelectedChapter(chapter)}
                  data-testid={`chapter-${chapter.id}`}
                >
                  <span className="font-ui text-sm truncate">{chapter.title}</span>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="w-6 h-6 opacity-0 group-hover:opacity-100"
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteChapter(chapter.id);
                    }}
                  >
                    <FiTrash2 className="w-3 h-3" />
                  </Button>
                </div>
              ))}
              {chapters.length === 0 && (
                <p className="text-sm text-muted-foreground text-center py-4">
                  No chapters yet
                </p>
              )}
            </ScrollArea>
          </div>
          
          <div className="p-4 flex-1 flex flex-col">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-heading font-semibold">Pages</h3>
              <Button 
                variant="ghost" 
                size="icon" 
                className="rounded-full w-8 h-8"
                onClick={createPage}
                disabled={!selectedChapter}
                data-testid="add-page-btn"
              >
                <FiPlus className="w-4 h-4" />
              </Button>
            </div>
            
            <ScrollArea className="flex-1">
              {pages.map((page, index) => (
                <div
                  key={page.id}
                  className={`flex items-center justify-between p-2 rounded-lg cursor-pointer mb-1 ${
                    selectedPage?.id === page.id 
                      ? 'bg-primary/10 text-primary' 
                      : 'hover:bg-muted'
                  }`}
                  onClick={() => setSelectedPage(page)}
                  data-testid={`page-${page.id}`}
                >
                  <span className="font-ui text-sm">Page {index + 1}</span>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="w-6 h-6"
                    onClick={(e) => {
                      e.stopPropagation();
                      deletePage(page.id);
                    }}
                  >
                    <FiTrash2 className="w-3 h-3" />
                  </Button>
                </div>
              ))}
              {pages.length === 0 && selectedChapter && (
                <p className="text-sm text-muted-foreground text-center py-4">
                  No pages yet
                </p>
              )}
            </ScrollArea>
          </div>
        </div>
        
        {/* Main Editor Area */}
        <div className="flex-1 flex overflow-hidden">
          {selectedPage ? (
            <>
              {/* Left - Image/Video Panel */}
              <div className="w-1/2 border-r border-border p-6 flex flex-col">
                <h3 className="font-heading font-semibold mb-4">Visual Content</h3>
                
                <Tabs defaultValue="image" className="flex-1 flex flex-col">
                  <TabsList className="mb-4">
                    <TabsTrigger value="image" data-testid="tab-image">
                      <FiImage className="mr-2 w-4 h-4" />
                      Image
                    </TabsTrigger>
                    <TabsTrigger value="video" data-testid="tab-video">
                      <FiVideo className="mr-2 w-4 h-4" />
                      Video
                    </TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="image" className="flex-1 flex flex-col space-y-4">
                    {/* Image Preview */}
                    <div className="aspect-[4/3] rounded-2xl border-2 border-dashed border-border bg-muted/30 overflow-hidden flex items-center justify-center">
                      {selectedPage.image_url ? (
                        <img 
                          src={selectedPage.image_url} 
                          alt="Page illustration"
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="text-center p-4">
                          <FiImage className="w-12 h-12 mx-auto text-muted-foreground/50 mb-2" />
                          <p className="font-body text-sm text-muted-foreground">
                            No image yet
                          </p>
                        </div>
                      )}
                    </div>
                    
                    {/* AI Image Generation */}
                    <div className="space-y-3">
                      <Label className="font-ui">Generate with AI</Label>
                      <div className="flex gap-2">
                        <Input
                          placeholder="Describe the image you want..."
                          value={imagePrompt}
                          onChange={(e) => setImagePrompt(e.target.value)}
                          className="rounded-full border-2"
                          data-testid="image-prompt"
                        />
                        <Button
                          onClick={generateImage}
                          disabled={generatingImage}
                          className="rounded-full"
                          data-testid="generate-image-btn"
                        >
                          {generatingImage ? (
                            <FiLoader className="w-4 h-4 animate-spin" />
                          ) : (
                            'Generate'
                          )}
                        </Button>
                      </div>
                    </div>
                    
                    {/* Upload */}
                    <div className="space-y-3">
                      <Label className="font-ui">Or upload your own</Label>
                      <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleImageUpload}
                        accept="image/*"
                        className="hidden"
                      />
                      <Button
                        variant="outline"
                        onClick={() => fileInputRef.current?.click()}
                        className="w-full rounded-full"
                        data-testid="upload-image-btn"
                      >
                        <FiUpload className="mr-2 w-4 h-4" />
                        Upload Image
                      </Button>
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="video" className="flex-1 flex flex-col space-y-4">
                    {/* Video Preview */}
                    <div className="aspect-video rounded-2xl border-2 border-dashed border-border bg-muted/30 overflow-hidden flex items-center justify-center">
                      {selectedPage.video_url ? (
                        <video 
                          src={selectedPage.video_url}
                          controls
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="text-center p-4">
                          <FiVideo className="w-12 h-12 mx-auto text-muted-foreground/50 mb-2" />
                          <p className="font-body text-sm text-muted-foreground">
                            No video yet
                          </p>
                        </div>
                      )}
                    </div>
                    
                    {/* AI Video Generation */}
                    <div className="space-y-3">
                      <Label className="font-ui">Generate with Sora AI</Label>
                      <div className="flex gap-2">
                        <Input
                          placeholder="Describe the animated scene..."
                          value={videoPrompt}
                          onChange={(e) => setVideoPrompt(e.target.value)}
                          className="rounded-full border-2"
                          data-testid="video-prompt"
                        />
                        <Button
                          onClick={generateVideo}
                          disabled={generatingVideo}
                          className="rounded-full"
                          data-testid="generate-video-btn"
                        >
                          {generatingVideo ? (
                            <FiLoader className="w-4 h-4 animate-spin" />
                          ) : (
                            'Generate'
                          )}
                        </Button>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Video generation takes 2-5 minutes
                      </p>
                    </div>
                  </TabsContent>
                </Tabs>
              </div>
              
              {/* Right - Text Panel */}
              <div className="w-1/2 p-6 flex flex-col">
                <h3 className="font-heading font-semibold mb-4">Story Text</h3>
                
                <div className="flex-1 flex flex-col">
                  <Textarea
                    placeholder="Write your story here..."
                    value={selectedPage.text_content}
                    onChange={(e) => setSelectedPage({ ...selectedPage, text_content: e.target.value })}
                    className="flex-1 min-h-[400px] font-reader text-lg rounded-2xl border-2 resize-none"
                    data-testid="page-text-content"
                  />
                  
                  <p className="text-sm text-muted-foreground mt-3">
                    {selectedPage.text_content.length} characters
                  </p>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center space-y-4">
                <FiBook className="w-16 h-16 mx-auto text-muted-foreground/50" />
                <h3 className="font-heading text-xl">No page selected</h3>
                <p className="font-body text-muted-foreground">
                  {chapters.length === 0 
                    ? 'Create a chapter to get started'
                    : 'Select a page or create a new one'}
                </p>
                {chapters.length === 0 && (
                  <Button
                    onClick={() => setNewChapterOpen(true)}
                    className="rounded-full"
                  >
                    <FiPlus className="mr-2" />
                    Create Chapter
                  </Button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
