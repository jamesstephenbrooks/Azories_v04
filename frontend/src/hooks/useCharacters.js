import { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import { proStudioAPI, getErrorMessage } from '../services/api';

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
      const response = await proStudioAPI.getCharacters();
      setCharacters(response.data.characters || []);
    } catch (error) {
      console.error('Error fetching characters:', error);
    }
  }, []);

  const fetchCharacterOptions = useCallback(async () => {
    try {
      const [stylesRes, genresRes] = await Promise.all([
        proStudioAPI.getCharacterStyles(),
        proStudioAPI.getCharacterGenres()
      ]);
      
      setCharacterStyles(stylesRes.data.styles || []);
      setCharacterGenres(genresRes.data.genres || []);
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

    try {
      const response = await proStudioAPI.createCharacter({
        name: characterName,
        description_prompt: characterDescription,
        style: characterStyle,
        genre: characterGenre,
        reference_images: characterImages
      });

      toast.success(`Character "${response.data.character.name}" created!`);
      await fetchCharacters();
      resetForm();
      return response.data.character;
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setIsCreatingCharacter(false);
    }
    return null;
  };

  const deleteCharacter = async (characterId) => {
    try {
      await proStudioAPI.deleteCharacter(characterId);
      toast.success('Character deleted');
      await fetchCharacters();
      if (viewingCharacter?.id === characterId) {
        setViewingCharacter(null);
      }
      if (selectedCharacter?.id === characterId) {
        setSelectedCharacter(null);
      }
    } catch (error) {
      toast.error(getErrorMessage(error));
    }
  };

  const openCharacterView = async (character) => {
    setViewingCharacter(character);
    
    try {
      const response = await proStudioAPI.getCharacterGallery(character.id);
      setCharacterGallery(response.data.images || []);
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
