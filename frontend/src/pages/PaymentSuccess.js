import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FiCheck, FiX, FiLoader } from 'react-icons/fi';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const PaymentSuccess = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState('checking');
  const [result, setResult] = useState(null);
  const [attempts, setAttempts] = useState(0);

  const sessionId = searchParams.get('session_id');

  useEffect(() => {
    if (sessionId) {
      pollPaymentStatus();
    } else {
      setStatus('error');
    }
  }, [sessionId]);

  const pollPaymentStatus = async () => {
    const token = localStorage.getItem('azories-token');
    if (!token) {
      navigate('/auth');
      return;
    }

    if (attempts >= 10) {
      setStatus('timeout');
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/payments/status/${sessionId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (!response.ok) {
        throw new Error('Failed to check payment status');
      }

      const data = await response.json();
      setResult(data);

      if (data.payment_status === 'paid') {
        setStatus('success');
        toast.success(`${data.credits_added} credits added to your account!`);
      } else if (data.status === 'expired') {
        setStatus('expired');
      } else {
        // Continue polling
        setAttempts(prev => prev + 1);
        setTimeout(pollPaymentStatus, 2000);
      }
    } catch (error) {
      console.error('Error checking payment:', error);
      setAttempts(prev => prev + 1);
      setTimeout(pollPaymentStatus, 2000);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-purple-900 flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-gray-800 rounded-2xl p-8 max-w-md w-full text-center"
      >
        {status === 'checking' && (
          <>
            <div className="w-20 h-20 bg-purple-600/30 rounded-full flex items-center justify-center mx-auto mb-6">
              <FiLoader className="text-4xl text-purple-400 animate-spin" />
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">Processing Payment</h1>
            <p className="text-gray-400">Please wait while we confirm your payment...</p>
          </>
        )}

        {status === 'success' && (
          <>
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', bounce: 0.5 }}
              className="w-20 h-20 bg-green-500/30 rounded-full flex items-center justify-center mx-auto mb-6"
            >
              <FiCheck className="text-4xl text-green-400" />
            </motion.div>
            <h1 className="text-2xl font-bold text-white mb-2">Payment Successful!</h1>
            <p className="text-gray-400 mb-4">{result?.message}</p>
            {result?.credits_added && (
              <div className="bg-green-500/20 rounded-lg p-4 mb-6">
                <div className="text-3xl font-bold text-green-400">+{result.credits_added}</div>
                <div className="text-gray-400">credits added</div>
                {result.new_balance && (
                  <div className="text-sm text-gray-400 mt-2">
                    New balance: <span className="text-white font-semibold">{result.new_balance} credits</span>
                  </div>
                )}
              </div>
            )}
            <button
              onClick={() => navigate('/pro-studio')}
              className="w-full bg-purple-600 hover:bg-purple-500 text-white font-semibold py-3 rounded-lg transition-colors"
            >
              Go to Pro Studio
            </button>
          </>
        )}

        {status === 'expired' && (
          <>
            <div className="w-20 h-20 bg-yellow-500/30 rounded-full flex items-center justify-center mx-auto mb-6">
              <FiX className="text-4xl text-yellow-400" />
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">Session Expired</h1>
            <p className="text-gray-400 mb-6">Your payment session has expired. Please try again.</p>
            <button
              onClick={() => navigate('/credits')}
              className="w-full bg-purple-600 hover:bg-purple-500 text-white font-semibold py-3 rounded-lg transition-colors"
            >
              Try Again
            </button>
          </>
        )}

        {status === 'timeout' && (
          <>
            <div className="w-20 h-20 bg-yellow-500/30 rounded-full flex items-center justify-center mx-auto mb-6">
              <FiLoader className="text-4xl text-yellow-400" />
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">Verification Timeout</h1>
            <p className="text-gray-400 mb-6">
              We couldn't verify your payment immediately. If you completed the payment, your credits will be added shortly.
            </p>
            <button
              onClick={() => navigate('/pro-studio')}
              className="w-full bg-purple-600 hover:bg-purple-500 text-white font-semibold py-3 rounded-lg transition-colors"
            >
              Go to Pro Studio
            </button>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="w-20 h-20 bg-red-500/30 rounded-full flex items-center justify-center mx-auto mb-6">
              <FiX className="text-4xl text-red-400" />
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">Something Went Wrong</h1>
            <p className="text-gray-400 mb-6">No payment session found. Please try purchasing credits again.</p>
            <button
              onClick={() => navigate('/credits')}
              className="w-full bg-purple-600 hover:bg-purple-500 text-white font-semibold py-3 rounded-lg transition-colors"
            >
              Go to Credits
            </button>
          </>
        )}
      </motion.div>
    </div>
  );
};

export default PaymentSuccess;
