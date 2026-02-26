import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: `${process.env.REACT_APP_BACKEND_URL}/api`,
  timeout: 120000, // 2 minute timeout for long operations
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - adds auth token to every request
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('azories-token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handles errors globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Extract error message
    let errorMessage = 'An unexpected error occurred';
    
    if (error.response) {
      // Server responded with error status
      const { status, data } = error.response;
      
      if (status === 401) {
        // Unauthorized - clear token and redirect to login
        localStorage.removeItem('azories-token');
        errorMessage = 'Session expired. Please log in again.';
        // Don't redirect here - let the component handle it
      } else if (status === 402) {
        // Payment required (insufficient credits)
        errorMessage = data?.detail || 'Insufficient credits';
      } else if (status === 403) {
        errorMessage = data?.detail || 'Access denied';
      } else if (status === 404) {
        errorMessage = data?.detail || 'Resource not found';
      } else if (status === 422) {
        errorMessage = data?.detail || 'Invalid request data';
      } else if (status === 429) {
        errorMessage = data?.detail || 'Too many requests. Please wait.';
      } else if (status >= 500) {
        errorMessage = data?.detail || 'Server error. Please try again later.';
      } else {
        errorMessage = data?.detail || data?.message || errorMessage;
      }
    } else if (error.request) {
      // Request made but no response
      errorMessage = 'Network error. Please check your connection.';
    } else {
      // Error in request setup
      errorMessage = error.message || errorMessage;
    }
    
    // Attach parsed error message to error object
    error.errorMessage = errorMessage;
    
    return Promise.reject(error);
  }
);

// Helper to get error message from caught error
export const getErrorMessage = (error) => {
  return error.errorMessage || error.response?.data?.detail || error.message || 'An error occurred';
};

// Helper to check if error is due to insufficient credits
export const isInsufficientCredits = (error) => {
  return error.response?.status === 402;
};

// Helper to check if error is unauthorized
export const isUnauthorized = (error) => {
  return error.response?.status === 401;
};

// ============================================
// AUTH API
// ============================================
export const authAPI = {
  login: (email, password, rememberMe = true) => api.post('/auth/login', { email, password, remember_me: rememberMe }),
  register: (email, password, name) => api.post('/auth/register', { email, password, name }),
  me: () => api.get('/auth/me'),
  forgotPassword: (email) => api.post('/auth/forgot-password', { email }),
  resetPassword: (token, password) => api.post('/auth/reset-password', { token, password }),
  googleAuth: (credential) => api.post('/auth/google', { credential }),
};

// ============================================
// BOOKS API
// ============================================
export const booksAPI = {
  getAll: (params) => api.get('/books', { params }),
  getMy: () => api.get('/books/my'),
  getById: (bookId) => api.get(`/books/${bookId}`),
  create: (data) => api.post('/books', data),
  update: (bookId, data) => api.put(`/books/${bookId}`, data),
  delete: (bookId) => api.delete(`/books/${bookId}`),
  publish: (bookId) => api.post(`/books/${bookId}/publish`),
  unpublish: (bookId) => api.post(`/books/${bookId}/unpublish`),
  submitForReview: (bookId) => api.post(`/books/${bookId}/submit-review`),
  like: (bookId) => api.post(`/books/${bookId}/like`),
  getChapters: (bookId) => api.get(`/books/${bookId}/chapters`),
  createChapter: (bookId, data) => api.post(`/books/${bookId}/chapters`, data),
  updateChapter: (chapterId, data) => api.put(`/chapters/${chapterId}`, data),
  deleteChapter: (chapterId) => api.delete(`/chapters/${chapterId}`),
  reorderChapters: (bookId, order) => api.put(`/books/${bookId}/chapters/reorder`, { order }),
  getAnalytics: (bookId) => api.get(`/books/${bookId}/analytics`),
  getInviteLink: (bookId, role) => api.post(`/books/${bookId}/invite-link`, { role }),
  getCollaborators: (bookId) => api.get(`/books/${bookId}/collaborators`),
  inviteCollaborator: (bookId, data) => api.post(`/books/${bookId}/collaborators/invite`, data),
  updateCollaborator: (bookId, userId, data) => api.put(`/books/${bookId}/collaborators/${userId}`, data),
  removeCollaborator: (bookId, userId) => api.delete(`/books/${bookId}/collaborators/${userId}`),
};

// ============================================
// CHAPTERS & PAGES API
// ============================================
export const pagesAPI = {
  getByChapter: (chapterId) => api.get(`/chapters/${chapterId}/pages`),
  create: (chapterId, data) => api.post(`/chapters/${chapterId}/pages`, data),
  update: (pageId, data) => api.put(`/pages/${pageId}`, data),
  delete: (pageId) => api.delete(`/pages/${pageId}`),
  reorder: (chapterId, order) => api.put(`/chapters/${chapterId}/pages/reorder`, { order }),
  duplicate: (pageId) => api.post(`/pages/${pageId}/duplicate`),
};

// ============================================
// SERIES API  
// ============================================
export const seriesAPI = {
  getAll: () => api.get('/series'),
  getMy: () => api.get('/series/my'),
  getById: (seriesId) => api.get(`/series/${seriesId}`),
  create: (data) => api.post('/series', data),
  update: (seriesId, data) => api.put(`/series/${seriesId}`, data),
  delete: (seriesId) => api.delete(`/series/${seriesId}`),
  addBook: (seriesId, bookId) => api.post(`/series/${seriesId}/books/${bookId}`),
  removeBook: (seriesId, bookId) => api.delete(`/series/${seriesId}/books/${bookId}`),
  reorderBooks: (seriesId, order) => api.put(`/series/${seriesId}/reorder`, { order }),
};

// ============================================
// PRO STUDIO API
// ============================================
export const proStudioAPI = {
  // Characters
  getCharacters: () => api.get('/pro-studio/characters'),
  getCharacter: (characterId) => api.get(`/pro-studio/characters/${characterId}`),
  createCharacter: (data) => api.post('/pro-studio/characters', data),
  updateCharacter: (characterId, data) => api.put(`/pro-studio/characters/${characterId}`, data),
  deleteCharacter: (characterId) => api.delete(`/pro-studio/characters/${characterId}`),
  getCharacterGallery: (characterId) => api.get(`/pro-studio/characters/${characterId}/gallery`),
  generateConsistent: (characterId, formData) => 
    api.post(`/pro-studio/characters/${characterId}/generate-consistent`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  generateThumbnail: (characterId) => api.post(`/pro-studio/characters/${characterId}/generate-thumbnail`),
  trainConsistency: (characterId) => api.post(`/pro-studio/characters/train-consistency?character_id=${characterId}`),
  getCharacterStyles: () => api.get('/pro-studio/character-styles'),
  getCharacterGenres: () => api.get('/pro-studio/character-genres'),
  
  // Scenes
  getScenes: () => api.get('/pro-studio/scenes'),
  getScene: (sceneId) => api.get(`/pro-studio/scenes/${sceneId}`),
  createScene: (data) => api.post('/pro-studio/scenes', data),
  updateScene: (sceneId, data) => api.put(`/pro-studio/scenes/${sceneId}`, data),
  deleteScene: (sceneId) => api.delete(`/pro-studio/scenes/${sceneId}`),
  getSceneGallery: (sceneId) => api.get(`/pro-studio/scenes/${sceneId}/gallery`),
  getSceneOptions: () => api.get('/pro-studio/scene-options'),
  generateWithScene: (sceneId, data) => api.post(`/pro-studio/scenes/${sceneId}/generate`, data),
  
  // Gallery
  getGallery: () => api.get('/pro-studio/gallery'),
  getGalleryUnified: (params) => api.get('/pro-studio/gallery/unified', { params }),
  saveToGallery: (data) => api.post('/pro-studio/gallery', data),
  saveToCharacterFolder: (characterId, data) => api.post(`/pro-studio/characters/${characterId}/gallery`, data),
  saveToSceneFolder: (sceneId, data) => api.post(`/pro-studio/scenes/${sceneId}/gallery`, data),
  deleteGalleryItem: (itemId) => api.delete(`/pro-studio/gallery/${itemId}`),
  
  // Videos
  getVideos: () => api.get('/pro-studio/videos'),
  
  // Generation
  generateImage: (data) => api.post('/pro-studio/generate-image', data),
  generateVariant: (data) => api.post('/pro-studio/generate-variant', data),
  generateShots: (data) => api.post('/pro-studio/generate-shots', data),
  generateExpression: (data) => api.post('/pro-studio/generate-expression', data),
  animateHero: (data) => api.post('/pro-studio/animate-hero', data),
};

// ============================================
// ART STUDIO API
// ============================================
export const artStudioAPI = {
  getGallery: (params) => api.get('/art-studio/gallery', { params }),
  getBookGallery: (bookId) => api.get(`/art-studio/gallery/book/${bookId}`),
  uploadImage: (data) => api.post('/art-studio/upload', data),
  deleteImage: (imageId) => api.delete(`/art-studio/gallery/${imageId}`),
  animationStatus: (jobId) => api.get(`/art-studio/animation-status/${jobId}`),
};

// ============================================
// FAL AI API
// ============================================
export const falAPI = {
  getModels: () => api.get('/fal/models'),
  generate: (data) => api.post('/fal/generate', data),
  trainingStatus: (jobId) => api.get(`/fal/training-status/${jobId}`),
};

// ============================================
// CREDITS API
// ============================================
export const creditsAPI = {
  getBalance: () => api.get('/credits/balance'),
  getHistory: () => api.get('/credits/history'),
  createCheckoutSession: (data) => api.post('/credits/checkout', data),
  verifyPayment: (sessionId) => api.get(`/credits/verify/${sessionId}`),
};

// ============================================
// TASKS API (for long-running operations)
// ============================================
export const tasksAPI = {
  getStatus: (taskId) => api.get(`/tasks/${taskId}`),
};

// ============================================
// USER API
// ============================================
export const userAPI = {
  getProfile: (userId) => api.get(`/users/${userId}`),
  updateProfile: (data) => api.put('/user/profile', data),
  getReadingStats: () => api.get('/user/reading-stats'),
  recordReading: (data) => api.post('/user/record-reading', data),
  getRecommendations: () => api.get('/user/recommendations'),
  getFollowers: (userId) => api.get(`/users/${userId}/followers`),
  getFollowing: (userId) => api.get(`/users/${userId}/following`),
  follow: (userId) => api.post(`/users/${userId}/follow`),
  unfollow: (userId) => api.delete(`/users/${userId}/follow`),
};

// ============================================
// AI API
// ============================================
export const aiAPI = {
  azora: (data) => api.post('/ai/azora', data),
  readingBuddy: (data) => api.post('/ai/reading-buddy', data),
  generateImage: (data) => api.post('/ai/generate-image', data),
  transcribe: (formData) => api.post('/ai/transcribe', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
};

// ============================================
// STARTER LIBRARY API
// ============================================
export const starterLibraryAPI = {
  get: () => api.get('/starter-library'),
};

// ============================================
// VOICES API
// ============================================
export const voicesAPI = {
  getAll: () => api.get('/voices'),
  uploadNarration: (bookId, formData) => api.post(`/books/${bookId}/narration`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
};

// ============================================
// CONTACT API
// ============================================
export const contactAPI = {
  send: (data) => api.post('/contact', data),
};

// ============================================
// ADMIN API (different base path - no /api prefix)
// ============================================
const adminApi = axios.create({
  baseURL: process.env.REACT_APP_BACKEND_URL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Admin request interceptor
adminApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('admin-token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Admin response interceptor
adminApi.interceptors.response.use(
  (response) => response,
  (error) => {
    let errorMessage = 'An error occurred';
    if (error.response?.data?.detail) {
      errorMessage = error.response.data.detail;
    } else if (error.response?.status === 401) {
      errorMessage = 'Admin session expired';
      localStorage.removeItem('admin-token');
    }
    error.errorMessage = errorMessage;
    return Promise.reject(error);
  }
);

export const adminAPI = {
  login: (username, password) => adminApi.post('/admin/login', { username, password }),
  verify: () => adminApi.get('/admin/verify'),
  getBooks: () => adminApi.get('/admin/books'),
  getUsers: () => adminApi.get('/admin/users'),
  getAnalytics: () => adminApi.get('/admin/analytics'),
  featureBook: (bookId) => adminApi.post(`/admin/books/${bookId}/feature`),
  bestOfWeek: (bookId) => adminApi.post(`/admin/books/${bookId}/best-of-week`),
  publishBook: (bookId) => adminApi.post(`/admin/books/${bookId}/publish`),
  deleteBook: (bookId) => adminApi.delete(`/admin/books/${bookId}`),
  seedTestBooks: () => adminApi.post('/admin/seed-test-books'),
  getPendingBooks: () => adminApi.get('/admin/pending-reviews'),
  approveBook: (bookId) => adminApi.post(`/admin/books/${bookId}/approve`),
  rejectBook: (bookId, data) => adminApi.post(`/admin/books/${bookId}/reject`, data),
  getDetailedAnalytics: () => adminApi.get('/admin/analytics/detailed'),
};

// Export the main api instance as default for direct use
export default api;
