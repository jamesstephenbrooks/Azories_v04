import { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export const useCharacters = () => {
  const [characters, setCharacters] = useState([]);
  const [selectedCharacter, setSelectedCharacter] = useState(null);
  const [viewingCharacter, setViewingCharacter] = useState(null);
  const [characterGallery, setCharacterGallery] = useState([]);
  const [characterStyles, setCharacterStyles] = useState([]);
  const [characterGenres, setCharacterGenres] = useState([]);
  const [isCreatingCharacter, setIsCreatingCharacter] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Form state
  const [characterName, setCharacterName] = useState('');
  const [characterDescription, setCharacterDescription] = useState('');
  const [characterStyle, setCharacterStyle] = useState('illustration');
  const [characterGenre, setCharacterGenre] = useState('fantasy');
  const [characterImages, setCharacterImages] = useState([]);

  const fetchCharacters = useCallback(async () => {
    const token = localStorage.getItem('azories-token');
    if (!token) return;

    try {
      const response = await fetch(`${API_URL}/api/pro-studio/characters`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setCharacters(data.characters || []);
      }
    } catch (error) {
      console.error('Error fetching characters:', error);
    }
  }, []);

  const fetchCharacterOptions = useCallback(async () => {
    try {
      const [stylesRes, genresRes] = await Promise.all([
        fetch(`${API_URL}/api/pro-studio/character-styles`),
        fetch(`${API_URL}/api/pro-studio/character-genres`)
      ]);
      
      if (stylesRes.ok) {
        const data = await stylesRes.json();
        setCharacterStyles(data.styles || []);
      }
      if (genresRes.ok) {
        const data = await genresRes.json();
        setCharacterGenres(data.genres || []);
      }
    } catch (error) {
      console.error('Error fetching character options:', error);
    }
  }, []);

  const createCharacter = async () => {
    if (!characterName.trim()) {
      toast.error('Please enter a character name');
      return null;
    }

    setIsCreatingCharacter(true);
    const token = localStorage.getItem('azories-token');

    try {
      const response = await fetch(`${API_URL}/api/pro-studio/characters`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          name: characterName,
          description_prompt: characterDescription,
          style: characterStyle,
          genre: characterGenre,
          reference_images: characterImages
        })
      });

      if (response.ok) {
        const data = await response.json();
        toast.success(`Character "${data.character.name}" created!`);
        await fetchCharacters();
        resetForm();
        return data.character;
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to create character');
      }
    } catch (error) {
      toast.error('Error creating character');
      console.error(error);
    } finally {
      setIsCreatingCharacter(false);
    }
    return null;
  };

  const deleteCharacter = async (characterId) => {
    const token = localStorage.getItem('azories-token');

    try {
      const response = await fetch(`${API_URL}/api/pro-studio/characters/${characterId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        toast.success('Character deleted');
        await fetchCharacters();
        if (viewingCharacter?.id === characterId) {
          setViewingCharacter(null);
        }
        if (selectedCharacter?.id === characterId) {
          setSelectedCharacter(null);
        }
      }
    } catch (error) {
      toast.error('Error deleting character');
      console.error(error);
    }
  };

  const openCharacterView = async (character) => {
    setViewingCharacter(character);
    
    // Fetch gallery for this character
    const token = localStorage.getItem('azories-token');
    try {
      const response = await fetch(
        `${API_URL}/api/pro-studio/characters/${character.id}/gallery`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (response.ok) {
        const data = await response.json();
        setCharacterGallery(data.images || []);
      }
    } catch (error) {
      console.error('Error fetching character gallery:', error);
    }
  };

  const resetForm = () => {
    setCharacterName('');
    setCharacterDescription('');
    setCharacterStyle('illustration');
    setCharacterGenre('fantasy');
    setCharacterImages([]);
  };

  useEffect(() => {
    fetchCharacters();
    fetchCharacterOptions();
  }, [fetchCharacters, fetchCharacterOptions]);

  return {
    // State
    characters,
    selectedCharacter,
    setSelectedCharacter,
    viewingCharacter,
    setViewingCharacter,
    characterGallery,
    setCharacterGallery,
    characterStyles,
    characterGenres,
    isCreatingCharacter,
    isLoading,
    
    // Form state
    characterName,
    setCharacterName,
    characterDescription,
    setCharacterDescription,
    characterStyle,
    setCharacterStyle,
    characterGenre,
    setCharacterGenre,
    characterImages,
    setCharacterImages,
    
    // Actions
    fetchCharacters,
    createCharacter,
    deleteCharacter,
    openCharacterView,
    resetForm
  };
};

export default useCharacters;
