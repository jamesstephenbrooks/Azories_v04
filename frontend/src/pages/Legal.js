import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FiArrowLeft, FiFileText, FiShield, FiMail } from 'react-icons/fi';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const Legal = ({ type = 'terms' }) => {
  const navigate = useNavigate();
  const [content, setContent] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchContent();
  }, [type]);

  const fetchContent = async () => {
    try {
      const endpoint = type === 'privacy' ? '/api/legal/privacy' : '/api/legal/terms';
      const response = await fetch(`${API_URL}${endpoint}`);
      const data = await response.json();
      setContent(data);
    } catch (error) {
      console.error('Error fetching content:', error);
      toast.error('Failed to load content');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-purple-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-purple-500 border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-purple-50 py-12 px-4">
      <div className="max-w-3xl mx-auto">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center text-gray-600 hover:text-gray-900 mb-8 transition-colors"
        >
          <FiArrowLeft className="mr-2" />
          Back
        </button>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-lg p-8"
        >
          <div className="flex items-center mb-6">
            {type === 'privacy' ? (
              <FiShield className="text-3xl text-purple-600 mr-4" />
            ) : (
              <FiFileText className="text-3xl text-purple-600 mr-4" />
            )}
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{content?.title}</h1>
              <p className="text-gray-500 text-sm">Last updated: {content?.last_updated}</p>
            </div>
          </div>

          <div className="prose prose-purple max-w-none">
            {content?.content?.split('\n').map((line, index) => {
              if (line.startsWith('# ')) {
                return <h1 key={index} className="text-2xl font-bold text-gray-900 mt-8 mb-4">{line.replace('# ', '')}</h1>;
              } else if (line.startsWith('## ')) {
                return <h2 key={index} className="text-xl font-semibold text-gray-800 mt-6 mb-3">{line.replace('## ', '')}</h2>;
              } else if (line.startsWith('- ')) {
                return <li key={index} className="text-gray-700 ml-4">{line.replace('- ', '')}</li>;
              } else if (line.trim()) {
                return <p key={index} className="text-gray-700 mb-3">{line}</p>;
              }
              return null;
            })}
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export const TermsOfService = () => <Legal type="terms" />;
export const PrivacyPolicy = () => <Legal type="privacy" />;

export default Legal;
