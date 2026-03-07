import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FiZap, FiCheck, FiImage, FiVideo, FiStar, FiCreditCard, FiArrowLeft } from 'react-icons/fi';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const Credits = () => {
  const navigate = useNavigate();
  const [packages, setPackages] = useState({});
  const [creditCosts, setCreditCosts] = useState({});
  const [userCredits, setUserCredits] = useState(0);
  const [loading, setLoading] = useState(true);
  const [purchasing, setPurchasing] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    const token = localStorage.getItem('azories-token');
    if (!token) {
      navigate('/auth');
      return;
    }

    try {
      // Fetch packages
      const packagesRes = await fetch(`${API_URL}/api/payments/packages`);
      const packagesData = await packagesRes.json();
      setPackages(packagesData.packages || {});
      setCreditCosts(packagesData.credit_costs || {});

      // Fetch user credits
      const creditsRes = await fetch(`${API_URL}/api/credits/balance`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const creditsData = await creditsRes.json();
      setUserCredits(creditsData.credits || 0);
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Failed to load credit packages');
    } finally {
      setLoading(false);
    }
  };

  const handlePurchase = async (packageId) => {
    const token = localStorage.getItem('azories-token');
    if (!token) {
      navigate('/auth');
      return;
    }

    setPurchasing(packageId);

    try {
      // Save the current page URL to return to after payment
      // Use referrer if available, otherwise current page
      const returnUrl = document.referrer && document.referrer.includes(window.location.origin) 
        ? document.referrer.replace(window.location.origin, '')
        : '/dashboard';
      sessionStorage.setItem('payment_return_url', returnUrl);
      
      const response = await fetch(`${API_URL}/api/payments/create-checkout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          package_id: packageId,
          origin_url: window.location.origin
        })
      });

      if (!response.ok) {
        throw new Error('Failed to create checkout session');
      }

      const data = await response.json();
      
      // Redirect to Stripe checkout
      window.location.href = data.checkout_url;
    } catch (error) {
      console.error('Purchase error:', error);
      toast.error('Failed to start checkout. Please try again.');
      setPurchasing(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 to-purple-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-purple-500 border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-purple-900 py-12 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Back Button */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="mb-6"
        >
          <Button
            variant="ghost"
            onClick={() => navigate(-1)}
            className="text-white/70 hover:text-white hover:bg-white/10"
            data-testid="credits-back-btn"
          >
            <FiArrowLeft className="mr-2" />
            Back
          </Button>
        </motion.div>
        
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <h1 className="text-4xl font-bold text-white mb-4">
            <FiZap className="inline-block mr-3 text-yellow-400" />
            Pro Studio Credits
          </h1>
          <p className="text-gray-300 text-lg max-w-2xl mx-auto">
            Power your creativity with AI-generated images, videos, and character consistency features
          </p>
          <div className="mt-4 inline-block bg-purple-600/30 rounded-full px-6 py-2">
            <span className="text-white">Your Balance: </span>
            <span className="text-yellow-400 font-bold text-xl">{userCredits} credits</span>
          </div>
        </motion.div>

        {/* Credit Packages */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {Object.entries(packages).map(([id, pkg], index) => (
            <motion.div
              key={id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className={`relative rounded-2xl overflow-hidden ${
                pkg.popular 
                  ? 'bg-gradient-to-b from-purple-600 to-purple-800 ring-2 ring-yellow-400' 
                  : 'bg-gray-800/80'
              }`}
            >
              {pkg.popular && (
                <div className="absolute top-0 right-0 bg-yellow-400 text-gray-900 text-xs font-bold px-3 py-1 rounded-bl-lg">
                  MOST POPULAR
                </div>
              )}
              
              <div className="p-6">
                <h3 className="text-xl font-bold text-white capitalize mb-2">{id}</h3>
                <div className="mb-4">
                  <span className="text-4xl font-bold text-white">£{pkg.price}</span>
                  <span className="text-gray-400 ml-2">GBP</span>
                </div>
                
                <div className="bg-black/20 rounded-lg p-3 mb-4">
                  <div className="text-2xl font-bold text-yellow-400">{pkg.credits.toLocaleString()}</div>
                  <div className="text-sm text-gray-300">credits</div>
                </div>
                
                <p className="text-gray-300 text-sm mb-4">{pkg.description}</p>
                
                <button
                  onClick={() => handlePurchase(id)}
                  disabled={purchasing === id}
                  className={`w-full py-3 rounded-lg font-semibold transition-all ${
                    pkg.popular
                      ? 'bg-yellow-400 text-gray-900 hover:bg-yellow-300'
                      : 'bg-purple-600 text-white hover:bg-purple-500'
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  {purchasing === id ? (
                    <span className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-5 w-5 border-2 border-current border-t-transparent mr-2"></div>
                      Processing...
                    </span>
                  ) : (
                    <span className="flex items-center justify-center">
                      <FiCreditCard className="mr-2" />
                      Buy Now
                    </span>
                  )}
                </button>
              </div>
            </motion.div>
          ))}
        </div>

        {/* What Credits Get You */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="bg-gray-800/60 rounded-2xl p-8"
        >
          <h2 className="text-2xl font-bold text-white mb-6 text-center">What Can You Create?</h2>
          
          <div className="grid md:grid-cols-4 gap-6">
            <div className="text-center p-4">
              <div className="w-16 h-16 bg-gradient-to-r from-amber-600/30 to-orange-600/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <FiZap className="text-3xl text-amber-400" />
              </div>
              <h3 className="text-white font-semibold mb-2">AI Story Creator</h3>
              <p className="text-gray-400 text-sm">
                5 credits = 1 complete story<br />
                AI writes text + generates all page images
              </p>
            </div>
            
            <div className="text-center p-4">
              <div className="w-16 h-16 bg-purple-600/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <FiImage className="text-3xl text-purple-400" />
              </div>
              <h3 className="text-white font-semibold mb-2">AI Images</h3>
              <p className="text-gray-400 text-sm">
                1 credit = 1 image<br />
                High-quality illustrations, characters, and scenes
              </p>
            </div>
            
            <div className="text-center p-4">
              <div className="w-16 h-16 bg-pink-600/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <FiVideo className="text-3xl text-pink-400" />
              </div>
              <h3 className="text-white font-semibold mb-2">AI Videos</h3>
              <p className="text-gray-400 text-sm">
                10 credits = 1 video<br />
                Bring your images to life with animation
              </p>
            </div>
            
            <div className="text-center p-4">
              <div className="w-16 h-16 bg-yellow-600/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <FiStar className="text-3xl text-yellow-400" />
              </div>
              <h3 className="text-white font-semibold mb-2">Character Training</h3>
              <p className="text-gray-400 text-sm">
                50 credits = 1 LoRA training<br />
                Create consistent characters across all your books
              </p>
            </div>
          </div>

          <div className="mt-8 pt-6 border-t border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4 text-center">Credit Costs</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-3xl mx-auto">
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">AI Story:</span>
                <span className="text-white font-semibold">{creditCosts.ai_story_create || 5} credits</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">FLUX Image:</span>
                <span className="text-white font-semibold">{creditCosts.flux_generate || 1} credit</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">FLUX Pro:</span>
                <span className="text-white font-semibold">{creditCosts.flux_pro_generate || 2} credits</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Face Consistency:</span>
                <span className="text-white font-semibold">{creditCosts.pulid_generate || 3} credits</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">LoRA Training:</span>
                <span className="text-white font-semibold">{creditCosts.lora_training || 50} credits</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">LoRA Generate:</span>
                <span className="text-white font-semibold">{creditCosts.lora_generate || 2} credits</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Video:</span>
                <span className="text-white font-semibold">{creditCosts.video_generate || 10} credits</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">9-Angle Shots:</span>
                <span className="text-white font-semibold">{creditCosts.shots_generate || 5} credits</span>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Back Button */}
        <div className="text-center mt-8">
          <button
            onClick={() => navigate(-1)}
            className="text-gray-400 hover:text-white transition-colors"
          >
            ← Go Back
          </button>
        </div>
      </div>
    </div>
  );
};

export default Credits;
