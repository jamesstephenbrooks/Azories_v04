import { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export const useScenes = () => {
  const [scenes, setScenes] = useState([]);
  const [selectedScene, setSelectedScene] = useState(null);
  const [viewingScene, setViewingScene] = useState(null);
  const [sceneGallery, setSceneGallery] = useState([]);
  const [sceneOptions, setSceneOptions] = useState({ 
    location_types: [], 
    lighting: [], 
    moods: [] 
  });
  const [isCreatingScene, setIsCreatingScene] = useState(false);

  // Form state
  const [sceneName, setSceneName] = useState('');
  const [sceneDescription, setSceneDescription] = useState('');
  const [sceneStyle, setSceneStyle] = useState('illustration');
  const [sceneGenre, setSceneGenre] = useState('fantasy');
  const [sceneLocationType, setSceneLocationType] = useState('outdoor');
  const [sceneLighting, setSceneLighting] = useState('natural');
  const [sceneMood, setSceneMood] = useState('peaceful');
  const [sceneTimeOfDay, setSceneTimeOfDay] = useState('');
  const [sceneWeather, setSceneWeather] = useState('');

  const fetchScenes = useCallback(async () => {
    const token = localStorage.getItem('azories-token');
    if (!token) return;

    try {
      const response = await fetch(`${API_URL}/api/pro-studio/scenes`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setScenes(data.scenes || []);
      }
    } catch (error) {
      console.error('Error fetching scenes:', error);
    }
  }, []);

  const fetchSceneOptions = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/pro-studio/scene-options`);
      if (response.ok) {
        const data = await response.json();
        setSceneOptions(data);
      }
    } catch (error) {
      console.error('Error fetching scene options:', error);
    }
  }, []);

  const createScene = async () => {
    if (!sceneName.trim()) {
      toast.error('Please enter a scene name');
      return null;
    }

    setIsCreatingScene(true);
    const token = localStorage.getItem('azories-token');

    try {
      const response = await fetch(`${API_URL}/api/pro-studio/scenes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          name: sceneName,
          description: sceneDescription,
          style: sceneStyle,
          genre: sceneGenre,
          location_type: sceneLocationType,
          lighting: sceneLighting,
          mood: sceneMood,
          time_of_day: sceneTimeOfDay,
          weather: sceneWeather
        })
      });

      if (response.ok) {
        const data = await response.json();
        toast.success(`Scene "${data.scene.name}" created!`);
        await fetchScenes();
        resetForm();
        return data.scene;
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to create scene');
      }
    } catch (error) {
      toast.error('Error creating scene');
      console.error(error);
    } finally {
      setIsCreatingScene(false);
    }
    return null;
  };

  const deleteScene = async (sceneId) => {
    const token = localStorage.getItem('azories-token');

    try {
      const response = await fetch(`${API_URL}/api/pro-studio/scenes/${sceneId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        toast.success('Scene deleted');
        await fetchScenes();
        if (viewingScene?.id === sceneId) {
          setViewingScene(null);
        }
        if (selectedScene?.id === sceneId) {
          setSelectedScene(null);
        }
      }
    } catch (error) {
      toast.error('Error deleting scene');
      console.error(error);
    }
  };

  const openSceneView = async (scene) => {
    setViewingScene(scene);
    
    // Fetch gallery for this scene
    const token = localStorage.getItem('azories-token');
    try {
      const response = await fetch(
        `${API_URL}/api/pro-studio/scenes/${scene.id}/gallery`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (response.ok) {
        const data = await response.json();
        setSceneGallery(data.images || []);
      }
    } catch (error) {
      console.error('Error fetching scene gallery:', error);
    }
  };

  const resetForm = () => {
    setSceneName('');
    setSceneDescription('');
    setSceneStyle('illustration');
    setSceneGenre('fantasy');
    setSceneLocationType('outdoor');
    setSceneLighting('natural');
    setSceneMood('peaceful');
    setSceneTimeOfDay('');
    setSceneWeather('');
  };

  useEffect(() => {
    fetchScenes();
    fetchSceneOptions();
  }, [fetchScenes, fetchSceneOptions]);

  return {
    // State
    scenes,
    selectedScene,
    setSelectedScene,
    viewingScene,
    setViewingScene,
    sceneGallery,
    setSceneGallery,
    sceneOptions,
    isCreatingScene,
    
    // Form state
    sceneName,
    setSceneName,
    sceneDescription,
    setSceneDescription,
    sceneStyle,
    setSceneStyle,
    sceneGenre,
    setSceneGenre,
    sceneLocationType,
    setSceneLocationType,
    sceneLighting,
    setSceneLighting,
    sceneMood,
    setSceneMood,
    sceneTimeOfDay,
    setSceneTimeOfDay,
    sceneWeather,
    setSceneWeather,
    
    // Actions
    fetchScenes,
    createScene,
    deleteScene,
    openSceneView,
    resetForm
  };
};

export default useScenes;
