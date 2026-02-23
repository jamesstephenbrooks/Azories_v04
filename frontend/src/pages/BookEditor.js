import { useState, useEffect, useRef, useCallback } from 'react';
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
import { Progress } from '@/components/ui/progress';
import { toast } from 'sonner';
import { 
  FiArrowLeft, FiPlus, FiSave, FiTrash2, FiImage, FiVideo, FiUpload,
  FiBook, FiSettings, FiLoader, FiGrid, FiLayout, FiBookOpen, FiMic, FiZap, FiDownload,
  FiUsers
} from 'react-icons/fi';
import CollaborativeWriting from '@/components/CollaborativeWriting';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function BookEditor() {
  const { bookId } = useParams();
  const navigate = useNavigate();
  const { user, loading: authLoading } = useAuth();
  const fileInputRef = useRef(null);
  const videoInputRef = useRef(null);
  const coverInputRef = useRef(null);
  const backCoverInputRef = useRef(null);
  
  const [book, setBook] = useState(null);
  const [chapters, setChapters] = useState([]);
  const [selectedChapter, setSelectedChapter] = useState(null);
  const [pages, setPages] = useState([]);
  const [selectedPage, setSelectedPage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  // Unsaved changes tracking
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const lastSavedContent = useRef(null);
  
  // AI generation state
  const [imagePrompt, setImagePrompt] = useState('');
  const [videoPrompt, setVideoPrompt] = useState('');
  const [generatingImage, setGeneratingImage] = useState(false);
  const [generatingVideo, setGeneratingVideo] = useState(false);
  const [generatingSummary, setGeneratingSummary] = useState(false);
  const [imageStyle, setImageStyle] = useState('illustration');
  const [videoStyle, setVideoStyle] = useState('animation');
  
  // Voice narration state (speech-to-text)
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);
  const audioChunksRef = useRef([]);
  
  // Book gallery state (images assigned to this book from Art Studio)
  const [bookGallery, setBookGallery] = useState([]);
  const [showBookGallery, setShowBookGallery] = useState(false);
  
  // Voices
  const [voices, setVoices] = useState([]);
  
  // Which image slot to generate for (for comic mode)
  const [activeImageSlot, setActiveImageSlot] = useState(1);
  
  // Cover editing
  const [coverDialogOpen, setCoverDialogOpen] = useState(false);
  const [coverData, setCoverData] = useState({
    cover_image: '',
    back_cover_image: '',
    cover_title: '',
    cover_subtitle: '',
    back_cover_text: '',
    narrator_voice_id: '',
    age_rating: 'All Ages'
  });
  
  // Upload progress states
  const [imageUploadProgress, setImageUploadProgress] = useState(0);
  const [videoUploadProgress, setVideoUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  
  // Art Studio Gallery picker
  const [showGalleryPicker, setShowGalleryPicker] = useState(false);
  const [galleryImages, setGalleryImages] = useState([]);
  const [generalGalleryImages, setGeneralGalleryImages] = useState([]);
  const [proStudioCharacters, setProStudioCharacters] = useState([]);
  const [proStudioScenes, setProStudioScenes] = useState([]);
  const [starterLibraryImages, setStarterLibraryImages] = useState([]);
  const [galleryTab, setGalleryTab] = useState('book'); // 'book', 'all', 'characters', 'scenes', 'starter'
  
  // Cover Gallery picker
  const [showCoverGalleryPicker, setShowCoverGalleryPicker] = useState(false);
  const [coverGalleryTarget, setCoverGalleryTarget] = useState('front'); // 'front' or 'back'
  
  // New chapter/page dialogs
  const [newChapterOpen, setNewChapterOpen] = useState(false);
  const [newChapterTitle, setNewChapterTitle] = useState('');
  const [creatingChapter, setCreatingChapter] = useState(false);

  // Unsaved changes warning - beforeunload
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
        return e.returnValue;
      }
    };
    
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [hasUnsavedChanges]);
  
  // Track content changes
  useEffect(() => {
    if (selectedPage && lastSavedContent.current !== null) {
      const currentContent = JSON.stringify({
        text: selectedPage.text_content,
        image: selectedPage.image_url,
        video: selectedPage.video_url
      });
      setHasUnsavedChanges(currentContent !== lastSavedContent.current);
    }
  }, [selectedPage?.text_content, selectedPage?.image_url, selectedPage?.video_url]);

  useEffect(() => {
    if (!authLoading && !user) {
      navigate('/auth', { state: { from: `/editor/${bookId}` } });
    }
  }, [user, authLoading, navigate, bookId]);

  useEffect(() => {
    if (user && bookId) {
      fetchBook();
      fetchChapters();
      fetchVoices();
      fetchBookGallery();
      fetchGalleryImages();
      fetchStarterLibrary();
    }
  }, [user, bookId]);

  useEffect(() => {
    if (selectedChapter) {
      fetchPages(selectedChapter.id);
    }
  }, [selectedChapter]);

  const fetchBookGallery = async () => {
    const token = localStorage.getItem('azories-token');
    if (!token || !bookId) return;
    
    try {
      const res = await axios.get(`${API}/art-studio/gallery/book/${bookId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setBookGallery(res.data.images || []);
    } catch (error) {
      console.error('Failed to load book gallery');
      setBookGallery([]);
    }
  };
  
  const fetchStarterLibrary = async () => {
    try {
      const res = await axios.get(`${API}/starter-library`);
      setStarterLibraryImages(res.data.images || []);
    } catch (error) {
      console.error('Failed to load starter library');
      setStarterLibraryImages([]);
    }
  };

  const fetchVoices = async () => {
    try {
      const res = await axios.get(`${API}/voices`);
      setVoices(res.data);
    } catch (error) {
      console.error('Failed to load voices');
    }
  };
  
  // Fetch Art Studio gallery images for this book
  const fetchGalleryImages = async () => {
    const token = localStorage.getItem('azories-token');
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    
    try {
      // Fetch book-specific images
      const bookRes = await axios.get(`${API}/art-studio/gallery?book_id=${bookId}`, { headers });
      setGalleryImages(bookRes.data.images || []);
    } catch (error) {
      console.error('Failed to load book gallery images');
      setGalleryImages([]);
    }
    
    try {
      // Fetch all gallery images
      const allRes = await axios.get(`${API}/art-studio/gallery`, { headers });
      setGeneralGalleryImages(allRes.data.images || []);
    } catch (error) {
      console.error('Failed to load general gallery images');
      setGeneralGalleryImages([]);
    }
    
    try {
      // Fetch Pro Studio characters with their galleries
      const charRes = await axios.get(`${API}/pro-studio/characters`, { headers });
      const characters = charRes.data || [];
      // Get galleries for characters with images
      const charsWithGalleries = await Promise.all(
        characters.map(async (char) => {
          try {
            const galleryRes = await axios.get(`${API}/pro-studio/characters/${char.id}/gallery`, { headers });
            return { ...char, gallery: galleryRes.data || [] };
          } catch {
            return { ...char, gallery: [] };
          }
        })
      );
      setProStudioCharacters(charsWithGalleries.filter(c => c.gallery.length > 0));
    } catch (error) {
      console.error('Failed to load Pro Studio characters');
      setProStudioCharacters([]);
    }
    
    try {
      // Fetch Pro Studio scenes with their galleries
      const sceneRes = await axios.get(`${API}/pro-studio/scenes`, { headers });
      const scenes = sceneRes.data || [];
      // Get galleries for scenes with images
      const scenesWithGalleries = await Promise.all(
        scenes.map(async (scene) => {
          try {
            const galleryRes = await axios.get(`${API}/pro-studio/scenes/${scene.id}/gallery`, { headers });
            return { ...scene, gallery: galleryRes.data || [] };
          } catch {
            return { ...scene, gallery: [] };
          }
        })
      );
      setProStudioScenes(scenesWithGalleries.filter(s => s.gallery.length > 0));
    } catch (error) {
      console.error('Failed to load Pro Studio scenes');
      setProStudioScenes([]);
    }
  };
  
  // Use image from Art Studio gallery
  const addGalleryImageToPage = async (imageUrl, slot = 1) => {
    if (!selectedPage) {
      toast.error('Please select a page first');
      return;
    }
    
    const isComicMode = selectedPage.layout === 'comic_4panel' || selectedPage.layout === 'comic_2panel';
    const imageKey = isComicMode ? `image${slot}_url` : 'image_url';
    const token = localStorage.getItem('azories-token');
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    
    try {
      // Use the correct endpoint: /pages/{page_id}
      await axios.put(`${API}/pages/${selectedPage.id}`, {
        [imageKey]: imageUrl
      }, { headers });
      
      setPages(prevPages => 
        prevPages.map(p => 
          p.id === selectedPage.id ? { ...p, [imageKey]: imageUrl } : p
        )
      );
      setSelectedPage(prev => ({ ...prev, [imageKey]: imageUrl }));
      setShowGalleryPicker(false);
      toast.success('Image added from Art Studio');
    } catch (error) {
      console.error('Gallery add error:', error);
      toast.error('Failed to add image: ' + (error.response?.data?.detail || error.message));
    }
  };
  
  // Add cover image from Art Studio gallery
  const addCoverFromGallery = (imageUrl) => {
    if (coverGalleryTarget === 'front') {
      setCoverData({ ...coverData, cover_image: imageUrl });
    } else {
      setCoverData({ ...coverData, back_cover_image: imageUrl });
    }
    setShowCoverGalleryPicker(false);
    toast.success(`${coverGalleryTarget === 'front' ? 'Front' : 'Back'} cover image added from Art Studio`);
  };
  
  // Update image position/fit settings
  const updateImagePosition = async (key, value) => {
    if (!selectedPage) return;
    
    const token = localStorage.getItem('azories-token');
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    
    try {
      await axios.put(`${API}/pages/${selectedPage.id}`, {
        [key]: value
      }, { headers });
      
      setPages(prevPages => 
        prevPages.map(p => 
          p.id === selectedPage.id ? { ...p, [key]: value } : p
        )
      );
      setSelectedPage(prev => ({ ...prev, [key]: value }));
    } catch (error) {
      console.error('Position update error:', error);
      toast.error('Failed to update image position');
    }
  };

  const fetchBook = async () => {
    try {
      const res = await axios.get(`${API}/books/${bookId}`);
      setBook(res.data);
      setCoverData({
        cover_image: res.data.cover_image || '',
        back_cover_image: res.data.back_cover_image || '',
        cover_title: res.data.cover_title || res.data.title,
        cover_subtitle: res.data.cover_subtitle || '',
        back_cover_text: res.data.back_cover_text || '',
        narrator_voice_id: res.data.narrator_voice_id || '21m00Tcm4TlvDq8ikWAM',
        age_rating: res.data.age_rating || 'All Ages'
      });
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
        const firstPage = res.data[0];
        setSelectedPage(firstPage);
        // Initialize saved content tracking
        lastSavedContent.current = JSON.stringify({
          text: firstPage.text_content,
          image: firstPage.image_url,
          video: firstPage.video_url
        });
        setHasUnsavedChanges(false);
      } else {
        setSelectedPage(null);
        lastSavedContent.current = null;
        setHasUnsavedChanges(false);
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
    const token = localStorage.getItem('azories-token');
    try {
      const res = await axios.post(`${API}/books/${bookId}/chapters`, {
        title: newChapterTitle
      }, {
        headers: { Authorization: `Bearer ${token}` }
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
    
    const token = localStorage.getItem('azories-token');
    try {
      await axios.delete(`${API}/chapters/${chapterId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
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
    
    const token = localStorage.getItem('azories-token');
    try {
      const res = await axios.post(`${API}/chapters/${selectedChapter.id}/pages`, {
        text_content: '',
        layout_type: book?.layout_mode === 'comic' ? 'comic_2' : 'single'
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Page added!');
      await fetchPages(selectedChapter.id);
      setSelectedPage(res.data);
    } catch (error) {
      toast.error('Failed to create page');
    }
  };

  // Auto-save functionality
  const autoSaveTimeoutRef = useRef(null);
  
  const triggerAutoSave = useCallback(() => {
    if (autoSaveTimeoutRef.current) {
      clearTimeout(autoSaveTimeoutRef.current);
    }
    
    autoSaveTimeoutRef.current = setTimeout(async () => {
      if (selectedPage) {
        const token = localStorage.getItem('azories-token');
        if (!token) return;
        
        try {
          await axios.put(`${API}/pages/${selectedPage.id}`, {
            text_content: selectedPage.text_content,
            image_url: selectedPage.image_url,
            image_url_2: selectedPage.image_url_2,
            image_url_3: selectedPage.image_url_3,
            image_url_4: selectedPage.image_url_4,
            video_url: selectedPage.video_url,
            use_video: selectedPage.use_video,
            layout_type: selectedPage.layout_type
          }, {
            headers: { Authorization: `Bearer ${token}` }
          });
          // Silent save - no toast for auto-save
        } catch (error) {
          console.error('Auto-save failed:', error);
        }
      }
    }, 2000); // Auto-save after 2 seconds of no changes
  }, [selectedPage]);

  // Trigger auto-save when page content changes
  useEffect(() => {
    if (selectedPage) {
      triggerAutoSave();
    }
    return () => {
      if (autoSaveTimeoutRef.current) {
        clearTimeout(autoSaveTimeoutRef.current);
      }
    };
  }, [selectedPage?.text_content, selectedPage?.image_url, triggerAutoSave]);

  const savePage = async () => {
    if (!selectedPage) return;
    
    const token = localStorage.getItem('azories-token');
    if (!token) {
      toast.error('Please log in to save');
      return;
    }
    
    setSaving(true);
    try {
      await axios.put(`${API}/pages/${selectedPage.id}`, {
        text_content: selectedPage.text_content,
        image_url: selectedPage.image_url,
        image_url_2: selectedPage.image_url_2,
        image_url_3: selectedPage.image_url_3,
        image_url_4: selectedPage.image_url_4,
        video_url: selectedPage.video_url,
        use_video: selectedPage.use_video,
        layout_type: selectedPage.layout_type,
        image_position_x: selectedPage.image_position_x,
        image_position_y: selectedPage.image_position_y,
        image_fit: selectedPage.image_fit,
        font_family: selectedPage.font_family,
        font_size: selectedPage.font_size,
        text_align: selectedPage.text_align
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Reset unsaved changes tracking
      lastSavedContent.current = JSON.stringify({
        text: selectedPage.text_content,
        image: selectedPage.image_url,
        video: selectedPage.video_url
      });
      setHasUnsavedChanges(false);
      
      toast.success('Page saved!');
    } catch (error) {
      toast.error('Failed to save page');
      console.error('Save error:', error);
    } finally {
      setSaving(false);
    }
  };

  const saveCover = async () => {
    const token = localStorage.getItem('azories-token');
    if (!token) {
      toast.error('Please log in to save');
      return;
    }
    
    try {
      await axios.put(`${API}/books/${bookId}`, coverData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Cover saved!');
      setCoverDialogOpen(false);
      fetchBook();
    } catch (error) {
      toast.error('Failed to save cover');
    }
  };

  const [generatingAllImages, setGeneratingAllImages] = useState(false);
  
  const generateAllImages = async () => {
    if (!window.confirm('Generate AI images for all pages without images? This may take several minutes.')) return;
    
    const token = localStorage.getItem('azories-token');
    setGeneratingAllImages(true);
    toast.info('Generating images for all pages... This may take a few minutes.');
    
    try {
      const res = await axios.post(`${API}/ai/generate-all-images`, {
        book_id: bookId,
        style: imageStyle
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(res.data.message);
      // Refresh pages
      if (selectedChapter) {
        await fetchPages(selectedChapter.id);
      }
    } catch (error) {
      toast.error('Failed to generate images');
    } finally {
      setGeneratingAllImages(false);
    }
  };

  const generateImagesFromText = async () => {
    if (!window.confirm('Generate AI images for all pages based on their text content? This may take several minutes.')) return;
    
    const token = localStorage.getItem('azories-token');
    setGeneratingAllImages(true);
    toast.info('Analyzing text and generating images... This may take a few minutes.');
    
    try {
      const res = await axios.post(`${API}/ai/generate-images-from-text`, {
        book_id: bookId,
        style: imageStyle
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(res.data.message);
      // Refresh pages
      if (selectedChapter) {
        await fetchPages(selectedChapter.id);
      }
    } catch (error) {
      toast.error('Failed to generate images from text');
    } finally {
      setGeneratingAllImages(false);
    }
  };

  const deletePage = async (pageId) => {
    if (!window.confirm('Delete this page?')) return;
    
    const token = localStorage.getItem('azories-token');
    try {
      await axios.delete(`${API}/pages/${pageId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
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
        book_id: bookId,
        style: imageStyle
      });
      
      if (res.data.success) {
        const imageUrl = `data:image/png;base64,${res.data.image_base64}`;
        
        // Set the appropriate image slot based on activeImageSlot
        const updates = { ...selectedPage };
        if (activeImageSlot === 1) {
          updates.image_url = imageUrl;
        } else if (activeImageSlot === 2) {
          updates.image_url_2 = imageUrl;
        } else if (activeImageSlot === 3) {
          updates.image_url_3 = imageUrl;
        } else if (activeImageSlot === 4) {
          updates.image_url_4 = imageUrl;
        }
        
        setSelectedPage(updates);
        toast.success('Image generated!');
        setImagePrompt('');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to generate image');
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
    toast.info('Generating video... This may take 2-5 minutes.');
    
    try {
      const res = await axios.post(`${API}/ai/generate-video`, {
        prompt: videoPrompt,
        duration: 5,
        size: '1280x720',  // Valid: 1280x720, 1792x1024, 1024x1792, 1024x1024
        style: videoStyle
      });
      
      if (res.data.success) {
        const videoUrl = `data:video/mp4;base64,${res.data.video_base64}`;
        setSelectedPage({ ...selectedPage, video_url: videoUrl });
        toast.success('Video generated!');
        setVideoPrompt('');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to generate video');
    } finally {
      setGeneratingVideo(false);
    }
  };

  const handleImageUpload = async (e, slot = 1) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    setIsUploading(true);
    setImageUploadProgress(0);
    
    try {
      const res = await axios.post(`${API}/upload/image`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setImageUploadProgress(progress);
        }
      });
      
      if (res.data.success) {
        const updates = { ...selectedPage };
        if (slot === 1) {
          updates.image_url = res.data.image_url;
        } else if (slot === 2) {
          updates.image_url_2 = res.data.image_url;
        } else if (slot === 3) {
          updates.image_url_3 = res.data.image_url;
        } else if (slot === 4) {
          updates.image_url_4 = res.data.image_url;
        }
        setSelectedPage(updates);
        toast.success('Image uploaded!');
      }
    } catch (error) {
      toast.error('Failed to upload image');
    } finally {
      setIsUploading(false);
      setImageUploadProgress(0);
    }
  };

  const handleVideoUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    setIsUploading(true);
    setVideoUploadProgress(0);
    
    try {
      const res = await axios.post(`${API}/upload/video`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setVideoUploadProgress(progress);
        }
      });
      
      if (res.data.success) {
        setSelectedPage({ ...selectedPage, video_url: res.data.video_url });
        toast.success('Video uploaded!');
      }
    } catch (error) {
      toast.error('Failed to upload video');
    } finally {
      setIsUploading(false);
      setVideoUploadProgress(0);
    }
  };

  const handleCoverUpload = async (e, isBack = false) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const res = await axios.post(`${API}/upload/image`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      if (res.data.success) {
        if (isBack) {
          setCoverData({ ...coverData, back_cover_image: res.data.image_url });
        } else {
          setCoverData({ ...coverData, cover_image: res.data.image_url });
        }
        toast.success('Cover image uploaded!');
      }
    } catch (error) {
      toast.error('Failed to upload image');
    }
  };

  const isComicMode = book?.layout_mode === 'comic';

  // Voice narration functions
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      
      audioChunksRef.current = [];
      
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      recorder.onstop = async () => {
        stream.getTracks().forEach(track => track.stop());
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await transcribeAudio(audioBlob);
      };
      
      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
      toast.info('Recording... Speak your story!');
    } catch (error) {
      console.error('Microphone access error:', error);
      toast.error('Could not access microphone. Please allow microphone permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      setIsRecording(false);
      toast.info('Processing your narration...');
    }
  };

  const transcribeAudio = async (audioBlob) => {
    const token = localStorage.getItem('azories-token');
    if (!token) {
      toast.error('Please log in first');
      return;
    }

    setIsTranscribing(true);
    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'narration.webm');
      formData.append('language', 'en');

      const response = await axios.post(`${API}/speech-to-text`, formData, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });

      if (response.data.success && response.data.text) {
        // Append transcribed text to existing content
        const currentText = selectedPage?.text_content || '';
        const newText = currentText 
          ? `${currentText}\n\n${response.data.text}`
          : response.data.text;
        
        setSelectedPage({ ...selectedPage, text_content: newText });
        toast.success('Narration transcribed! Review and edit if needed.');
      } else {
        toast.error('Could not transcribe audio');
      }
    } catch (error) {
      console.error('Transcription error:', error);
      toast.error(error.response?.data?.detail || 'Failed to transcribe audio');
    } finally {
      setIsTranscribing(false);
    }
  };

  const goToNextPageAfterNarration = async () => {
    // First save current page
    await savePage();
    
    // Find current page index
    const currentIndex = pages.findIndex(p => p.id === selectedPage?.id);
    
    if (currentIndex >= 0 && currentIndex < pages.length - 1) {
      // Go to next page
      const nextPage = pages[currentIndex + 1];
      setSelectedPage(nextPage);
      toast.info(`Moved to page ${currentIndex + 2}`);
    } else {
      // Create new page if at the end
      await addPage();
      toast.success('New page created for your next narration!');
    }
  };

  const downloadBook = async () => {
    const token = localStorage.getItem('azories-token');
    if (!token) {
      toast.error('Please log in to download');
      return;
    }
    
    try {
      toast.info('Preparing PDF download...');
      const response = await axios.get(`${API}/books/${bookId}/download`, {
        responseType: 'blob',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Create download link for PDF
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${book?.title || 'book'}_azories.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success('PDF downloaded!');
    } catch (error) {
      console.error('PDF download error:', error);
      toast.error(error.response?.data?.detail || 'Failed to download PDF');
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
              <div className="flex items-center gap-2">
                <h1 className="font-heading text-lg font-semibold">
                  {book?.title || 'Book Editor'}
                </h1>
                {isComicMode && (
                  <span className="px-2 py-0.5 rounded text-xs bg-secondary/20 text-secondary font-ui">
                    Comic
                  </span>
                )}
              </div>
              <p className="font-body text-sm text-muted-foreground">
                {selectedChapter?.title || 'No chapter selected'}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {/* Collaborative Writing Button */}
            <CollaborativeWriting 
              bookId={bookId} 
              isOwner={book?.author_id === user?.id}
              currentCollaborators={book?.collaborators || []}
              onUpdate={() => fetchBook()}
            />
            
            <Button
              variant="outline"
              className="rounded-full"
              onClick={downloadBook}
              data-testid="download-book-btn"
            >
              <FiDownload className="mr-2 w-4 h-4" />
              PDF
            </Button>
            
            <Button
              variant="outline"
              onClick={() => navigate(`/read/${bookId}`)}
              className="rounded-full"
              data-testid="preview-book"
            >
              <FiBook className="mr-2 w-4 h-4" />
              Preview
            </Button>
            
            {/* Unsaved changes indicator */}
            {hasUnsavedChanges && (
              <span className="px-2 py-1 text-xs bg-amber-500/20 text-amber-500 rounded-full animate-pulse">
                Unsaved changes
              </span>
            )}
            
            <Button
              onClick={savePage}
              disabled={saving || !selectedPage}
              className={`rounded-full ${hasUnsavedChanges ? 'bg-amber-500 hover:bg-amber-600' : ''}`}
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
                <DialogContent className="sm:max-w-sm w-[90%] mx-auto my-auto max-h-[40vh] overflow-visible dialog-keyboard-safe">
                  <DialogHeader>
                    <DialogTitle className="font-heading">New Chapter</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4 pt-4 pb-safe">
                    <Input
                      placeholder="Chapter title"
                      value={newChapterTitle}
                      onChange={(e) => setNewChapterTitle(e.target.value)}
                      className="rounded-full border-2 text-base"
                      data-testid="new-chapter-title"
                      autoComplete="off"
                      inputMode="text"
                      onFocus={(e) => {
                        // Better mobile keyboard handling
                        const element = e.target;
                        setTimeout(() => {
                          element.scrollIntoView({ behavior: 'smooth', block: 'center' });
                          // Also scroll the dialog itself
                          const dialog = element.closest('[role="dialog"]');
                          if (dialog) {
                            dialog.style.transform = 'translateY(-20vh)';
                          }
                        }, 300);
                      }}
                      onBlur={(e) => {
                        // Reset transform when keyboard closes
                        const dialog = e.target.closest('[role="dialog"]');
                        if (dialog) {
                          dialog.style.transform = '';
                        }
                      }}
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
                  className={`flex items-center justify-between p-2 rounded-lg cursor-pointer mb-1 group ${
                    selectedChapter?.id === chapter.id 
                      ? 'bg-primary/10 text-primary' 
                      : 'hover:bg-muted'
                  }`}
                  onClick={() => setSelectedChapter(chapter)}
                  data-testid={`chapter-${chapter.id}`}
                >
                  <span className="font-ui text-sm truncate flex-1">{chapter.title}</span>
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
                  className={`flex items-center justify-between p-2 rounded-lg cursor-pointer mb-1 group ${
                    selectedPage?.id === page.id 
                      ? 'bg-primary/10 text-primary' 
                      : 'hover:bg-muted'
                  }`}
                  onClick={() => setSelectedPage(page)}
                  data-testid={`page-${page.id}`}
                >
                  <div className="flex items-center gap-2">
                    <span className="font-ui text-sm">Page {index + 1}</span>
                    {page.layout_type?.startsWith('comic') && (
                      <FiGrid className="w-3 h-3 text-secondary" />
                    )}
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="w-6 h-6 opacity-0 group-hover:opacity-100"
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
          
          {/* Cover Section in Sidebar */}
          <div className="p-4 border-t border-border">
            <Dialog open={coverDialogOpen} onOpenChange={setCoverDialogOpen}>
              <DialogTrigger asChild>
                <Button
                  variant="outline"
                  className="w-full rounded-lg justify-start gap-2"
                  data-testid="edit-cover-btn"
                >
                  <FiBookOpen className="w-4 h-4" />
                  Edit Covers
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle className="font-heading text-2xl">Book Cover Editor</DialogTitle>
                </DialogHeader>
                <div className="grid md:grid-cols-2 gap-6 pt-4">
                  {/* Front Cover */}
                  <div className="space-y-4">
                    <h3 className="font-ui font-semibold">Front Cover</h3>
                    <div 
                      className="aspect-[3/4] rounded-2xl border-2 border-dashed border-border bg-muted/30 overflow-hidden relative"
                    >
                      {coverData.cover_image ? (
                        <img src={coverData.cover_image} alt="Cover" className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <FiUpload className="w-8 h-8 text-muted-foreground" />
                        </div>
                      )}
                      <div className="absolute inset-0 bg-black/50 flex flex-col items-center justify-center text-white p-4">
                        <Input
                          value={coverData.cover_title}
                          onChange={(e) => setCoverData({ ...coverData, cover_title: e.target.value })}
                          placeholder="Book Title"
                          className="bg-transparent border-0 text-center text-2xl font-heading font-bold text-white placeholder:text-white/50"
                          onClick={(e) => e.stopPropagation()}
                        />
                        <Input
                          value={coverData.cover_subtitle}
                          onChange={(e) => setCoverData({ ...coverData, cover_subtitle: e.target.value })}
                          placeholder="Subtitle"
                          className="bg-transparent border-0 text-center text-lg font-body text-white placeholder:text-white/50 mt-2"
                          onClick={(e) => e.stopPropagation()}
                        />
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => coverInputRef.current?.click()}
                        className="flex-1"
                      >
                        <FiUpload className="w-3 h-3 mr-1" />
                        Upload
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setCoverGalleryTarget('front');
                          setShowCoverGalleryPicker(true);
                        }}
                        className="flex-1"
                        data-testid="add-cover-from-gallery"
                      >
                        <FiImage className="w-3 h-3 mr-1" />
                        Art Studio
                      </Button>
                    </div>
                    <input
                      type="file"
                      ref={coverInputRef}
                      onChange={(e) => handleCoverUpload(e, false)}
                      accept="image/*"
                      className="hidden"
                    />
                  </div>
                  
                  {/* Back Cover */}
                  <div className="space-y-4">
                    <h3 className="font-ui font-semibold">Back Cover</h3>
                    <div 
                      className="aspect-[3/4] rounded-2xl border-2 border-dashed border-border bg-muted/30 overflow-hidden relative"
                    >
                      {coverData.back_cover_image ? (
                        <img src={coverData.back_cover_image} alt="Back Cover" className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <FiUpload className="w-8 h-8 text-muted-foreground" />
                        </div>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => backCoverInputRef.current?.click()}
                        className="flex-1"
                      >
                        <FiUpload className="w-3 h-3 mr-1" />
                        Upload
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setCoverGalleryTarget('back');
                          setShowCoverGalleryPicker(true);
                        }}
                        className="flex-1"
                        data-testid="add-back-cover-from-gallery"
                      >
                        <FiImage className="w-3 h-3 mr-1" />
                        Art Studio
                      </Button>
                    </div>
                    <input
                      type="file"
                      ref={backCoverInputRef}
                      onChange={(e) => handleCoverUpload(e, true)}
                      accept="image/*"
                      className="hidden"
                    />
                    <Textarea
                      value={coverData.back_cover_text}
                      onChange={(e) => setCoverData({ ...coverData, back_cover_text: e.target.value })}
                      placeholder="Back cover description/synopsis..."
                      className="min-h-24 rounded-2xl"
                    />
                  </div>
                </div>
                
                <Button onClick={saveCover} className="w-full rounded-full mt-4">
                  <FiSave className="mr-2" />
                  Save Cover
                </Button>
              </DialogContent>
            </Dialog>
            
            {/* Cover Thumbnails Preview */}
            <div className="flex gap-2 mt-3">
              {coverData.cover_image && (
                <div className="flex-1">
                  <p className="text-xs text-muted-foreground mb-1">Front</p>
                  <div className="aspect-[3/4] rounded-lg overflow-hidden border border-border bg-muted/30">
                    <img src={coverData.cover_image} alt="Front" className="w-full h-full object-cover" />
                  </div>
                </div>
              )}
              {coverData.back_cover_image && (
                <div className="flex-1">
                  <p className="text-xs text-muted-foreground mb-1">Back</p>
                  <div className="aspect-[3/4] rounded-lg overflow-hidden border border-border bg-muted/30">
                    <img src={coverData.back_cover_image} alt="Back" className="w-full h-full object-cover" />
                  </div>
                </div>
              )}
              {!coverData.cover_image && !coverData.back_cover_image && (
                <p className="text-xs text-muted-foreground text-center w-full py-2">
                  No covers set
                </p>
              )}
            </div>
          </div>
          
          {/* Narrator Voice Section */}
          <div className="p-4 border-t border-border">
            <label className="text-xs text-muted-foreground mb-2 block">Narrator Voice</label>
            <Select 
              value={book?.narrator_voice_id || '21m00Tcm4TlvDq8ikWAM'} 
              onValueChange={async (v) => {
                const token = localStorage.getItem('azories-token');
                try {
                  await axios.put(`${API}/books/${bookId}`, { narrator_voice_id: v }, {
                    headers: { Authorization: `Bearer ${token}` }
                  });
                  setBook({ ...book, narrator_voice_id: v });
                  toast.success('Voice updated!');
                } catch (error) {
                  toast.error('Failed to update voice');
                }
              }}
            >
              <SelectTrigger className="w-full rounded-lg text-sm">
                <SelectValue placeholder="Select Voice" />
              </SelectTrigger>
              <SelectContent className="max-h-64">
                {voices.length > 0 ? (
                  voices.map((voice) => (
                    <SelectItem key={voice.voice_id} value={voice.voice_id} className="text-xs">
                      {voice.name}
                    </SelectItem>
                  ))
                ) : (
                  <div className="px-2 py-2 text-xs text-muted-foreground">Loading voices...</div>
                )}
              </SelectContent>
            </Select>
            
            <div className="flex items-center gap-2 mt-2">
              <input
                type="checkbox"
                id="lockVoice"
                checked={book?.narrator_voice_locked || false}
                onChange={async (e) => {
                  const token = localStorage.getItem('azories-token');
                  try {
                    await axios.put(`${API}/books/${bookId}`, { narrator_voice_locked: e.target.checked }, {
                      headers: { Authorization: `Bearer ${token}` }
                    });
                    setBook({ ...book, narrator_voice_locked: e.target.checked });
                    toast.success(e.target.checked ? 'Voice locked!' : 'Voice unlocked');
                  } catch (error) {
                    toast.error('Failed to update');
                  }
                }}
                className="rounded"
              />
              <label htmlFor="lockVoice" className="text-xs text-muted-foreground">
                Lock voice for readers
              </label>
            </div>
          </div>
        </div>
        
        {/* Main Editor Area */}
        <div className="flex-1 flex overflow-hidden">
          {selectedPage ? (
            <>
              {/* Left - Visual Content Panel with Scroll */}
              <div className="w-1/2 border-r border-border flex flex-col">
                <ScrollArea className="flex-1">
                  <div className="p-6 space-y-6">
                    <div className="flex items-center justify-between">
                      <h3 className="font-heading font-semibold">Visual Content</h3>
                      {isComicMode && (
                        <Select 
                          value={selectedPage.layout_type || 'single'} 
                          onValueChange={(v) => setSelectedPage({ ...selectedPage, layout_type: v })}
                        >
                          <SelectTrigger className="w-40 rounded-full">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="single">Single Image</SelectItem>
                            <SelectItem value="comic_2">2 Panels</SelectItem>
                            <SelectItem value="comic_3">3 Panels</SelectItem>
                            <SelectItem value="comic_4">4 Panels</SelectItem>
                          </SelectContent>
                        </Select>
                      )}
                    </div>
                    
                    <Tabs defaultValue="image">
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
                      
                      <TabsContent value="image" className="space-y-4">
                        {/* Image Preview(s) */}
                        {selectedPage.layout_type?.startsWith('comic') ? (
                          <div className={`grid gap-2 ${
                            selectedPage.layout_type === 'comic_2' ? 'grid-cols-2' :
                            selectedPage.layout_type === 'comic_3' ? 'grid-cols-3' :
                            selectedPage.layout_type === 'comic_4' ? 'grid-cols-2 grid-rows-2' : ''
                          }`}>
                            {[1, 2, 3, 4].slice(0, 
                              selectedPage.layout_type === 'comic_2' ? 2 :
                              selectedPage.layout_type === 'comic_3' ? 3 : 4
                            ).map((slot) => {
                              const imgUrl = slot === 1 ? selectedPage.image_url :
                                            slot === 2 ? selectedPage.image_url_2 :
                                            slot === 3 ? selectedPage.image_url_3 :
                                            selectedPage.image_url_4;
                              return (
                                <div 
                                  key={slot}
                                  className={`aspect-square rounded-xl border-2 ${
                                    activeImageSlot === slot ? 'border-primary' : 'border-dashed border-border'
                                  } bg-muted/30 overflow-hidden cursor-pointer`}
                                  onClick={() => setActiveImageSlot(slot)}
                                >
                                  {imgUrl ? (
                                    <img src={imgUrl} alt={`Panel ${slot}`} className="w-full h-full object-cover" />
                                  ) : (
                                    <div className="w-full h-full flex items-center justify-center">
                                      <span className="font-ui text-sm text-muted-foreground">Panel {slot}</span>
                                    </div>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        ) : (
                          /* Portrait aspect ratio - Book page preview (WYSIWYG) */
                          <div className="space-y-3">
                            <div 
                              className="rounded-2xl border-2 border-border bg-[#fdfbf7] dark:bg-[#2a2a30] overflow-hidden flex items-center justify-center relative aspect-[3/4] shadow-lg"
                              data-testid="page-image-preview"
                              style={{
                                boxShadow: 'inset -7px 0 30px -7px rgba(0,0,0,0.12), 0 4px 16px rgba(0,0,0,0.1)'
                              }}
                            >
                              {selectedPage.image_url ? (
                                <img 
                                  src={selectedPage.image_url} 
                                  alt="Page illustration"
                                  className="absolute inset-0 w-full h-full"
                                  style={{
                                    objectFit: selectedPage.image_fit || 'cover',
                                    objectPosition: `${selectedPage.image_position_x || 50}% ${selectedPage.image_position_y || 50}%`
                                  }}
                                />
                              ) : (
                                <div className="text-center p-4">
                                  <FiImage className="w-8 h-8 mx-auto text-muted-foreground/50 mb-1" />
                                  <p className="font-body text-xs text-muted-foreground">
                                    No image - use options below
                                  </p>
                                </div>
                              )}
                              {/* Page preview label */}
                              <div className="absolute bottom-2 left-2 bg-black/50 text-white text-[10px] px-2 py-0.5 rounded">
                                Preview: Left Page
                              </div>
                            </div>
                            
                            {/* Book Gallery Quick Access - Show assigned images for this book */}
                            {bookGallery.length > 0 && !selectedPage.image_url && (
                              <div className="bg-muted/30 rounded-xl p-3">
                                <div className="flex items-center justify-between mb-2">
                                  <h4 className="text-xs font-semibold text-foreground/70">
                                    Book Gallery ({bookGallery.length} images)
                                  </h4>
                                  <Button 
                                    variant="ghost" 
                                    size="sm" 
                                    className="h-6 text-xs"
                                    onClick={() => setShowBookGallery(!showBookGallery)}
                                  >
                                    {showBookGallery ? 'Hide' : 'Show All'}
                                  </Button>
                                </div>
                                <div className={`grid grid-cols-4 gap-2 ${showBookGallery ? '' : 'max-h-16 overflow-hidden'}`}>
                                  {bookGallery.slice(0, showBookGallery ? undefined : 4).map((img) => (
                                    <div 
                                      key={img.id}
                                      className="aspect-square rounded-lg overflow-hidden cursor-pointer border-2 border-transparent hover:border-primary transition-colors"
                                      onClick={() => addGalleryImageToPage(img.image_url, activeImageSlot)}
                                    >
                                      <img src={img.image_url} alt="" className="w-full h-full object-cover" />
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                            
                            {/* Image Position Controls */}
                            {selectedPage.image_url && (
                              <div className="bg-muted/30 rounded-xl p-3 space-y-3">
                                <h4 className="text-xs font-semibold text-foreground/70 flex items-center gap-2">
                                  <FiGrid className="w-3 h-3" />
                                  Image Position & Fit
                                </h4>
                                
                                {/* Fit Mode */}
                                <div className="flex items-center gap-2">
                                  <Label className="text-xs text-muted-foreground w-16">Fit:</Label>
                                  <Select 
                                    value={selectedPage.image_fit || 'cover'} 
                                    onValueChange={(value) => updateImagePosition('image_fit', value)}
                                  >
                                    <SelectTrigger className="h-8 text-xs flex-1">
                                      <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                      <SelectItem value="cover">Cover (fill & crop)</SelectItem>
                                      <SelectItem value="contain">Contain (show all)</SelectItem>
                                      <SelectItem value="fill">Stretch to fill</SelectItem>
                                    </SelectContent>
                                  </Select>
                                </div>
                                
                                {/* Position X */}
                                <div className="flex items-center gap-2">
                                  <Label className="text-xs text-muted-foreground w-16">Horizontal:</Label>
                                  <input
                                    type="range"
                                    min="0"
                                    max="100"
                                    value={selectedPage.image_position_x || 50}
                                    onChange={(e) => updateImagePosition('image_position_x', parseInt(e.target.value))}
                                    className="flex-1 h-2 accent-primary"
                                  />
                                  <span className="text-xs text-muted-foreground w-8 text-right">{selectedPage.image_position_x || 50}%</span>
                                </div>
                                
                                {/* Position Y */}
                                <div className="flex items-center gap-2">
                                  <Label className="text-xs text-muted-foreground w-16">Vertical:</Label>
                                  <input
                                    type="range"
                                    min="0"
                                    max="100"
                                    value={selectedPage.image_position_y || 50}
                                    onChange={(e) => updateImagePosition('image_position_y', parseInt(e.target.value))}
                                    className="flex-1 h-2 accent-primary"
                                  />
                                  <span className="text-xs text-muted-foreground w-8 text-right">{selectedPage.image_position_y || 50}%</span>
                                </div>
                                
                                {/* Quick position presets */}
                                <div className="flex gap-1 pt-1">
                                  <Button 
                                    variant="outline" 
                                    size="sm" 
                                    className="flex-1 h-7 text-[10px]"
                                    onClick={() => { updateImagePosition('image_position_x', 0); updateImagePosition('image_position_y', 0); }}
                                  >
                                    Top-Left
                                  </Button>
                                  <Button 
                                    variant="outline" 
                                    size="sm" 
                                    className="flex-1 h-7 text-[10px]"
                                    onClick={() => { updateImagePosition('image_position_x', 50); updateImagePosition('image_position_y', 0); }}
                                  >
                                    Top
                                  </Button>
                                  <Button 
                                    variant="outline" 
                                    size="sm" 
                                    className="flex-1 h-7 text-[10px]"
                                    onClick={() => { updateImagePosition('image_position_x', 50); updateImagePosition('image_position_y', 50); }}
                                  >
                                    Center
                                  </Button>
                                  <Button 
                                    variant="outline" 
                                    size="sm" 
                                    className="flex-1 h-7 text-[10px]"
                                    onClick={() => { updateImagePosition('image_position_x', 50); updateImagePosition('image_position_y', 100); }}
                                  >
                                    Bottom
                                  </Button>
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                        
                        {/* Upload */}
                        <div className="space-y-3">
                          <Label className="font-ui">Upload Image</Label>
                          <input
                            type="file"
                            ref={fileInputRef}
                            onChange={(e) => handleImageUpload(e, activeImageSlot)}
                            accept="image/*"
                            className="hidden"
                          />
                          <Button
                            variant="outline"
                            onClick={() => fileInputRef.current?.click()}
                            className="w-full rounded-full"
                            data-testid="upload-image-btn"
                            disabled={isUploading}
                          >
                            {isUploading && imageUploadProgress > 0 ? (
                              <FiLoader className="mr-2 w-4 h-4 animate-spin" />
                            ) : (
                              <FiUpload className="mr-2 w-4 h-4" />
                            )}
                            {isUploading && imageUploadProgress > 0 
                              ? `Uploading... ${imageUploadProgress}%` 
                              : `Upload Image ${isComicMode ? `(Panel ${activeImageSlot})` : ''}`
                            }
                          </Button>
                          {/* Image Upload Progress Bar */}
                          {isUploading && imageUploadProgress > 0 && (
                            <div className="space-y-1">
                              <Progress value={imageUploadProgress} className="h-2" />
                              <p className="text-xs text-muted-foreground text-center">
                                {imageUploadProgress}% uploaded
                              </p>
                            </div>
                          )}
                          
                          {/* Use from Art Studio Gallery */}
                          <div className="pt-2 border-t border-border">
                            <Button
                              variant="outline"
                              onClick={() => {
                                fetchGalleryImages();
                                setShowGalleryPicker(true);
                              }}
                              className="w-full rounded-full border-purple-500/50 text-purple-600 hover:bg-purple-50 dark:hover:bg-purple-500/10"
                              data-testid="use-from-gallery-btn"
                            >
                              <FiImage className="mr-2 w-4 h-4" />
                              Select from Art Studio / Pro Studio
                            </Button>
                            <p className="text-xs text-muted-foreground text-center mt-1">
                              Select images from your Art Studio or Pro Studio galleries
                            </p>
                          </div>
                        </div>
                      </TabsContent>
                      
                      <TabsContent value="video" className="space-y-4">
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
                        
                        {/* Use Video Instead of Image Toggle */}
                        {selectedPage.video_url && (
                          <div className="flex items-center justify-between p-3 rounded-xl bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-500/20">
                            <div>
                              <Label className="font-ui text-sm">Use video on page</Label>
                              <p className="text-xs text-muted-foreground">Show video instead of image when reading</p>
                            </div>
                            <input
                              type="checkbox"
                              checked={selectedPage.use_video || false}
                              onChange={(e) => setSelectedPage({ ...selectedPage, use_video: e.target.checked })}
                              className="w-5 h-5 accent-purple-500"
                              data-testid="use-video-toggle"
                            />
                          </div>
                        )}
                        
                        {/* Video Upload */}
                        <div className="space-y-3">
                          <Label className="font-ui">Upload Video</Label>
                          <input
                            type="file"
                            ref={videoInputRef}
                            onChange={handleVideoUpload}
                            accept="video/*"
                            className="hidden"
                          />
                          <Button
                            variant="outline"
                            onClick={() => videoInputRef.current?.click()}
                            className="w-full rounded-full"
                            data-testid="upload-video-btn"
                            disabled={isUploading}
                          >
                            {isUploading && videoUploadProgress > 0 ? (
                              <FiLoader className="mr-2 w-4 h-4 animate-spin" />
                            ) : (
                              <FiUpload className="mr-2 w-4 h-4" />
                            )}
                            {isUploading && videoUploadProgress > 0 
                              ? `Uploading... ${videoUploadProgress}%` 
                              : 'Upload Video'
                            }
                          </Button>
                          {/* Video Upload Progress Bar */}
                          {isUploading && videoUploadProgress > 0 && (
                            <div className="space-y-1">
                              <Progress value={videoUploadProgress} className="h-2" />
                              <p className="text-xs text-muted-foreground text-center">
                                {videoUploadProgress}% uploaded
                              </p>
                            </div>
                          )}
                        </div>
                        
                        {/* Use from Gallery */}
                        <div className="space-y-3 pt-2 border-t border-border">
                          <Label className="font-ui">Use from Gallery</Label>
                          <Button
                            variant="outline"
                            onClick={() => {
                              fetchGalleryImages();
                              setShowGalleryPicker(true);
                            }}
                            className="w-full rounded-full border-purple-500/50 text-purple-600 hover:bg-purple-50 dark:hover:bg-purple-500/10"
                            data-testid="video-from-gallery-btn"
                          >
                            <FiVideo className="mr-2 w-4 h-4" />
                            Select from Art Studio / Pro Studio
                          </Button>
                          <p className="text-xs text-muted-foreground text-center">
                            Select videos from your Art Studio or Pro Studio galleries
                          </p>
                        </div>
                      </TabsContent>
                    </Tabs>
                  </div>
                </ScrollArea>
              </div>
              
              {/* Right - Text Panel */}
              <div className="w-1/2 p-6 flex flex-col">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-heading font-semibold">Story Text</h3>
                  
                  {/* Text Formatting Controls */}
                  <div className="flex items-center gap-2">
                    <Select 
                      value={selectedPage.font_family || 'default'} 
                      onValueChange={(value) => setSelectedPage({ ...selectedPage, font_family: value })}
                    >
                      <SelectTrigger className="w-32 h-8 text-xs rounded-full">
                        <SelectValue placeholder="Font" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="default">Default</SelectItem>
                        <SelectItem value="serif">Serif</SelectItem>
                        <SelectItem value="sans">Sans Serif</SelectItem>
                        <SelectItem value="mono">Monospace</SelectItem>
                        <SelectItem value="cursive">Cursive</SelectItem>
                      </SelectContent>
                    </Select>
                    
                    <Select 
                      value={selectedPage.font_size || 'medium'} 
                      onValueChange={(value) => setSelectedPage({ ...selectedPage, font_size: value })}
                    >
                      <SelectTrigger className="w-24 h-8 text-xs rounded-full">
                        <SelectValue placeholder="Size" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="small">Small</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="large">Large</SelectItem>
                        <SelectItem value="xlarge">X-Large</SelectItem>
                      </SelectContent>
                    </Select>
                    
                    <Select 
                      value={selectedPage.text_align || 'left'} 
                      onValueChange={(value) => setSelectedPage({ ...selectedPage, text_align: value })}
                    >
                      <SelectTrigger className="w-24 h-8 text-xs rounded-full">
                        <SelectValue placeholder="Align" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="left">Left</SelectItem>
                        <SelectItem value="center">Center</SelectItem>
                        <SelectItem value="right">Right</SelectItem>
                        <SelectItem value="justify">Justify</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                
                <div className="flex-1 flex flex-col">
                  <Textarea
                    placeholder="Write your story here..."
                    value={selectedPage.text_content}
                    onChange={(e) => setSelectedPage({ ...selectedPage, text_content: e.target.value })}
                    className={`flex-1 min-h-[400px] rounded-2xl border-2 resize-none ${
                      selectedPage.font_family === 'serif' ? 'font-serif' :
                      selectedPage.font_family === 'sans' ? 'font-sans' :
                      selectedPage.font_family === 'mono' ? 'font-mono' :
                      selectedPage.font_family === 'cursive' ? 'font-cursive' : 'font-reader'
                    } ${
                      selectedPage.font_size === 'small' ? 'text-sm' :
                      selectedPage.font_size === 'large' ? 'text-xl' :
                      selectedPage.font_size === 'xlarge' ? 'text-2xl' : 'text-lg'
                    } ${
                      selectedPage.text_align === 'center' ? 'text-center' :
                      selectedPage.text_align === 'right' ? 'text-right' :
                      selectedPage.text_align === 'justify' ? 'text-justify' : 'text-left'
                    }`}
                    data-testid="page-text-content"
                  />
                  
                  {/* Voice Narration Controls */}
                  <div className="mt-4 p-4 bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-2xl border border-purple-500/20">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <FiMic className="w-5 h-5 text-purple-500" />
                        <span className="font-semibold text-sm">Voice Narration</span>
                      </div>
                      <span className="text-xs text-muted-foreground">Speak your story instead of typing</span>
                    </div>
                    
                    <div className="flex items-center gap-3">
                      {!isRecording ? (
                        <Button
                          onClick={startRecording}
                          disabled={isTranscribing}
                          className="rounded-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
                          data-testid="start-narration-btn"
                        >
                          <FiMic className="mr-2 w-4 h-4" />
                          {isTranscribing ? 'Transcribing...' : 'Start Narrating'}
                        </Button>
                      ) : (
                        <Button
                          onClick={stopRecording}
                          className="rounded-full bg-red-500 hover:bg-red-600 animate-pulse"
                          data-testid="stop-narration-btn"
                        >
                          <div className="w-3 h-3 bg-white rounded-full mr-2" />
                          Stop Recording
                        </Button>
                      )}
                      
                      <Button
                        variant="outline"
                        onClick={goToNextPageAfterNarration}
                        disabled={isRecording || isTranscribing || !selectedPage?.text_content}
                        className="rounded-full"
                        data-testid="next-page-after-narration"
                      >
                        Save & Next Page
                        <FiArrowLeft className="ml-2 w-4 h-4 rotate-180" />
                      </Button>
                    </div>
                    
                    {isRecording && (
                      <div className="mt-3 flex items-center gap-2 text-sm text-purple-500">
                        <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                        Recording in progress... Speak clearly!
                      </div>
                    )}
                    
                    {isTranscribing && (
                      <div className="mt-3 flex items-center gap-2 text-sm text-muted-foreground">
                        <FiLoader className="w-4 h-4 animate-spin" />
                        Transcribing your narration with AI...
                      </div>
                    )}
                  </div>
                  
                  <p className="text-sm text-muted-foreground mt-3">
                    {selectedPage.text_content?.length || 0} characters
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
      
      {/* Art Studio Gallery Picker Modal */}
      <Dialog open={showGalleryPicker} onOpenChange={setShowGalleryPicker}>
        <DialogContent className="max-w-4xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FiImage className="text-purple-500" />
              Select from Galleries
            </DialogTitle>
          </DialogHeader>
          
          {/* Gallery Tabs */}
          <div className="flex flex-wrap gap-2 mt-2 border-b border-border pb-2">
            <button
              onClick={() => setGalleryTab('starter')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                galleryTab === 'starter' 
                  ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white' 
                  : 'bg-amber-500/20 hover:bg-amber-500/30 text-amber-600'
              }`}
            >
              ⭐ Starter Library ({starterLibraryImages.length})
            </button>
            <button
              onClick={() => setGalleryTab('book')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                galleryTab === 'book' 
                  ? 'bg-purple-500 text-white' 
                  : 'bg-muted hover:bg-muted/80'
              }`}
            >
              This Book ({galleryImages.length})
            </button>
            <button
              onClick={() => setGalleryTab('all')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                galleryTab === 'all' 
                  ? 'bg-purple-500 text-white' 
                  : 'bg-muted hover:bg-muted/80'
              }`}
            >
              Art Studio ({generalGalleryImages.length})
            </button>
            <button
              onClick={() => setGalleryTab('characters')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                galleryTab === 'characters' 
                  ? 'bg-pink-500 text-white' 
                  : 'bg-muted hover:bg-muted/80'
              }`}
            >
              Pro Characters ({proStudioCharacters.reduce((sum, c) => sum + c.gallery.length, 0)})
            </button>
            <button
              onClick={() => setGalleryTab('scenes')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                galleryTab === 'scenes' 
                  ? 'bg-emerald-500 text-white' 
                  : 'bg-muted hover:bg-muted/80'
              }`}
            >
              Pro Scenes ({proStudioScenes.reduce((sum, s) => sum + s.gallery.length, 0)})
            </button>
          </div>
          
          <div className="mt-4">
            {/* Starter Library images */}
            {galleryTab === 'starter' && (
              <ScrollArea className="h-[50vh]">
                {starterLibraryImages.length === 0 ? (
                  <div className="text-center py-12">
                    <FiImage className="w-16 h-16 mx-auto text-muted-foreground/30 mb-4" />
                    <h3 className="font-medium text-lg mb-2">Loading starter images...</h3>
                  </div>
                ) : (
                  <>
                    <p className="text-sm text-muted-foreground mb-4">
                      Free images to get you started! Click any image to add it to your page.
                    </p>
                    <div className="grid grid-cols-4 md:grid-cols-5 gap-3">
                      {starterLibraryImages.map((img) => (
                        <div 
                          key={img.id}
                          className="relative group cursor-pointer rounded-lg overflow-hidden border-2 border-transparent hover:border-amber-500 transition-all"
                          onClick={() => addGalleryImageToPage(img.url, activeImageSlot)}
                        >
                          <img 
                            src={img.url} 
                            alt={img.name} 
                            className="w-full aspect-square object-cover"
                          />
                          <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-2">
                            <span className="text-white text-xs font-medium truncate">{img.name}</span>
                          </div>
                          <div className="absolute top-1 right-1 bg-amber-500 text-white text-[8px] px-1 rounded">
                            {img.category}
                          </div>
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </ScrollArea>
            )}
            
            {/* Art Studio images */}
            {(galleryTab === 'book' || galleryTab === 'all') && (() => {
              const currentImages = galleryTab === 'book' ? galleryImages : generalGalleryImages;
              
              if (currentImages.length === 0) {
                return (
                  <div className="text-center py-12">
                    <FiImage className="w-16 h-16 mx-auto text-muted-foreground/30 mb-4" />
                    <h3 className="font-medium text-lg mb-2">
                      {galleryTab === 'book' ? 'No images for this book' : 'No images in Art Studio'}
                    </h3>
                    <p className="text-sm text-muted-foreground mb-4">
                      Create images in the Art Studio first.
                    </p>
                    <Button
                      onClick={() => {
                        setShowGalleryPicker(false);
                        navigate('/art-studio');
                      }}
                      className="rounded-full"
                    >
                      <FiZap className="mr-2" />
                      Go to Art Studio
                    </Button>
                  </div>
                );
              }
              
              return (
                <ScrollArea className="h-[50vh]">
                  <div className="grid grid-cols-3 md:grid-cols-4 gap-3 p-1">
                    {currentImages.map((img, idx) => (
                      <button
                        key={img.id || idx}
                        onClick={() => addGalleryImageToPage(img.image_url, activeImageSlot)}
                        className="group relative aspect-square rounded-lg overflow-hidden border-2 border-transparent hover:border-purple-500 transition-all"
                      >
                        <img 
                          src={img.image_url} 
                          alt={img.name || 'Gallery image'}
                          className="w-full h-full object-cover"
                        />
                        <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                          <span className="text-white text-sm font-medium">Use Image</span>
                        </div>
                        {img.name && (
                          <div className="absolute bottom-0 left-0 right-0 bg-black/70 px-2 py-1">
                            <p className="text-white text-xs truncate">{img.name}</p>
                          </div>
                        )}
                      </button>
                    ))}
                  </div>
                </ScrollArea>
              );
            })()}
            
            {/* Pro Studio Characters */}
            {galleryTab === 'characters' && (
              proStudioCharacters.length === 0 ? (
                <div className="text-center py-12">
                  <FiUser className="w-16 h-16 mx-auto text-muted-foreground/30 mb-4" />
                  <h3 className="font-medium text-lg mb-2">No Pro Studio Characters</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Create characters in Pro Studio to see their generated images here.
                  </p>
                  <Button
                    onClick={() => {
                      setShowGalleryPicker(false);
                      navigate('/pro-studio');
                    }}
                    className="rounded-full bg-pink-500 hover:bg-pink-600"
                  >
                    <FiZap className="mr-2" />
                    Go to Pro Studio
                  </Button>
                </div>
              ) : (
                <ScrollArea className="h-[50vh]">
                  {proStudioCharacters.map((char) => (
                    <div key={char.id} className="mb-6">
                      <h4 className="font-medium mb-2 flex items-center gap-2">
                        <FiUser className="text-pink-500" />
                        {char.name}
                        <span className="text-xs text-muted-foreground">({char.gallery.length} images)</span>
                      </h4>
                      <div className="grid grid-cols-4 gap-2">
                        {char.gallery.map((img, idx) => (
                          <button
                            key={idx}
                            onClick={() => addGalleryImageToPage(img.image_url, activeImageSlot)}
                            className="group relative aspect-square rounded-lg overflow-hidden border-2 border-transparent hover:border-pink-500 transition-all"
                          >
                            <img 
                              src={img.image_url} 
                              alt={`${char.name} image`}
                              className="w-full h-full object-cover"
                            />
                            <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                              <span className="text-white text-xs font-medium">Use</span>
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                </ScrollArea>
              )
            )}
            
            {/* Pro Studio Scenes */}
            {galleryTab === 'scenes' && (
              proStudioScenes.length === 0 ? (
                <div className="text-center py-12">
                  <FiLayers className="w-16 h-16 mx-auto text-muted-foreground/30 mb-4" />
                  <h3 className="font-medium text-lg mb-2">No Pro Studio Scenes</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Create scenes in Pro Studio to see their generated images here.
                  </p>
                  <Button
                    onClick={() => {
                      setShowGalleryPicker(false);
                      navigate('/pro-studio');
                    }}
                    className="rounded-full bg-emerald-500 hover:bg-emerald-600"
                  >
                    <FiZap className="mr-2" />
                    Go to Pro Studio
                  </Button>
                </div>
              ) : (
                <ScrollArea className="h-[50vh]">
                  {proStudioScenes.map((scene) => (
                    <div key={scene.id} className="mb-6">
                      <h4 className="font-medium mb-2 flex items-center gap-2">
                        <FiLayers className="text-emerald-500" />
                        {scene.name}
                        <span className="text-xs text-muted-foreground">({scene.gallery.length} images)</span>
                      </h4>
                      <div className="grid grid-cols-4 gap-2">
                        {scene.gallery.map((img, idx) => (
                          <button
                            key={idx}
                            onClick={() => addGalleryImageToPage(img.image_url, activeImageSlot)}
                            className="group relative aspect-square rounded-lg overflow-hidden border-2 border-transparent hover:border-emerald-500 transition-all"
                          >
                            <img 
                              src={img.image_url} 
                              alt={`${scene.name} image`}
                              className="w-full h-full object-cover"
                            />
                            <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                              <span className="text-white text-xs font-medium">Use</span>
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                </ScrollArea>
              )
            )}
          </div>
        </DialogContent>
      </Dialog>
      
      {/* Cover Gallery Picker Modal */}
      <Dialog open={showCoverGalleryPicker} onOpenChange={setShowCoverGalleryPicker}>
        <DialogContent className="max-w-4xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FiImage className="text-purple-500" />
              Select {coverGalleryTarget === 'front' ? 'Front' : 'Back'} Cover from Art Studio
            </DialogTitle>
          </DialogHeader>
          
          <div className="mt-4">
            {(() => {
              const allImages = [...galleryImages, ...generalGalleryImages];
              
              if (allImages.length === 0) {
                return (
                  <div className="text-center py-8">
                    <FiImage className="w-12 h-12 mx-auto text-muted-foreground/50 mb-4" />
                    <p className="text-muted-foreground">No images in your Art Studio gallery</p>
                    <Button
                      onClick={() => {
                        setShowCoverGalleryPicker(false);
                        navigate('/art-studio');
                      }}
                      className="mt-4 rounded-full"
                    >
                      <FiZap className="mr-2" />
                      Go to Art Studio
                    </Button>
                  </div>
                );
              }
              
              return (
                <ScrollArea className="h-[50vh]">
                  <div className="grid grid-cols-3 md:grid-cols-4 gap-3 p-1">
                    {allImages.map((img, idx) => (
                      <button
                        key={img.id || idx}
                        onClick={() => addCoverFromGallery(img.image_url)}
                        className="group relative aspect-[3/4] rounded-lg overflow-hidden border-2 border-transparent hover:border-purple-500 transition-all"
                      >
                        <img 
                          src={img.image_url} 
                          alt={img.name || 'Gallery image'}
                          className="w-full h-full object-cover"
                        />
                        <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                          <span className="text-white text-sm font-medium">Use as Cover</span>
                        </div>
                      </button>
                    ))}
                  </div>
                </ScrollArea>
              );
            })()}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
