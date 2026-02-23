import { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export const useCredits = () => {
  const [credits, setCredits] = useState(0);
  const [creditCosts, setCreditCosts] = useState({});

  const fetchCredits = useCallback(async () => {
    const token = localStorage.getItem('azories-token');
    if (!token) return;

    try {
      const response = await fetch(`${API_URL}/api/credits/balance`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setCredits(data.credits || 0);
        setCreditCosts(data.costs || {});
      }
    } catch (error) {
      console.error('Error fetching credits:', error);
    }
  }, []);

  const addCredits = async (amount) => {
    // Direct credit addition is restricted - redirect to purchase page
    toast.error('Please purchase credits through the store');
    window.location.href = '/credits';
  };

  const checkCredits = (operation) => {
    const cost = creditCosts[operation] || 0;
    return credits >= cost;
  };

  useEffect(() => {
    fetchCredits();
  }, [fetchCredits]);

  return {
    credits,
    creditCosts,
    fetchCredits,
    addCredits,
    checkCredits
  };
};

export default useCredits;
