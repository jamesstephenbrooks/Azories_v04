import { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import { proStudioAPI, getErrorMessage } from '../services/api';

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
      const response = await proStudioAPI.getScenes();
      setScenes(response.data.scenes || []);
    } catch (error) {
      console.error('Error fetching scenes:', error);
    }
  }, []);

  const fetchSceneOptions = useCallback(async () => {
    try {
      const response = await proStudioAPI.getSceneOptions();
      setSceneOptions(response.data);
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

    try {
      const response = await proStudioAPI.createScene({
        name: sceneName,
        description: sceneDescription,
        style: sceneStyle,
        genre: sceneGenre,
        location_type: sceneLocationType,
        lighting: sceneLighting,
        mood: sceneMood,
        time_of_day: sceneTimeOfDay,
        weather: sceneWeather
      });

      toast.success(`Scene "${response.data.scene.name}" created!`);
      await fetchScenes();
      resetForm();
      return response.data.scene;
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setIsCreatingScene(false);
    }
    return null;
  };

  const deleteScene = async (sceneId) => {
    try {
      await proStudioAPI.deleteScene(sceneId);
      toast.success('Scene deleted');
      await fetchScenes();
      if (viewingScene?.id === sceneId) {
        setViewingScene(null);
      }
      if (selectedScene?.id === sceneId) {
        setSelectedScene(null);
      }
    } catch (error) {
      toast.error(getErrorMessage(error));
    }
  };

  const openSceneView = async (scene) => {
    setViewingScene(scene);
    
    try {
      const response = await proStudioAPI.getSceneGallery(scene.id);
      setSceneGallery(response.data.images || []);
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
