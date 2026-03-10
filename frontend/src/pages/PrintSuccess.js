import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { FiArrowLeft, FiCheckCircle, FiLoader, FiAlertCircle, FiPackage } from 'react-icons/fi';
import { Button } from '@/components/ui/button';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function PrintSuccess() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get('session_id');
  const [status, setStatus] = useState('loading');
  const [orderData, setOrderData] = useState(null);

  useEffect(() => {
    if (!sessionId) {
      setStatus('error');
      return;
    }

    const checkStatus = async () => {
      try {
        const token = localStorage.getItem('azories-token');
        const res = await fetch(`${API_URL}/api/print/checkout/status/${sessionId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setOrderData(data);
          setStatus(data.payment_status === 'paid' ? 'success' : 'pending');
        } else {
          setStatus('error');
        }
      } catch {
        setStatus('error');
      }
    };

    checkStatus();
  }, [sessionId]);

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center px-4 pt-24 pb-12">
      {/* Back button */}
      <button
        onClick={() => navigate('/library')}
        className="fixed top-[max(1.5rem,env(safe-area-inset-top,1rem))] left-4 z-50 w-11 h-11 rounded-full bg-purple-600/90 backdrop-blur-md shadow-lg flex items-center justify-center hover:bg-purple-500 transition-all text-white"
        data-testid="print-success-back-btn"
      >
        <FiArrowLeft className="w-5 h-5" />
      </button>

      <div className="max-w-md w-full text-center space-y-6">
        {status === 'loading' && (
          <>
            <FiLoader className="w-16 h-16 text-purple-500 animate-spin mx-auto" />
            <h1 className="text-2xl font-bold">Checking your order...</h1>
            <p className="text-muted-foreground">Please wait while we confirm your payment.</p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="w-20 h-20 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center mx-auto">
              <FiCheckCircle className="w-10 h-10 text-green-600 dark:text-green-400" />
            </div>
            <h1 className="text-2xl font-bold">Order Confirmed!</h1>
            <p className="text-muted-foreground">
              Your printed book is on its way! Order reference: <span className="font-mono font-bold text-foreground">{orderData?.order_reference || 'N/A'}</span>
            </p>
            <div className="bg-purple-50 dark:bg-purple-900/20 rounded-xl p-4 border border-purple-200 dark:border-purple-800">
              <FiPackage className="w-6 h-6 text-purple-600 mx-auto mb-2" />
              <p className="text-sm text-purple-700 dark:text-purple-300">
                We'll start printing your book shortly. You'll receive updates on its progress.
              </p>
            </div>
            <Button onClick={() => navigate('/library')} className="rounded-full px-8" data-testid="back-to-library-btn">
              Back to Library
            </Button>
          </>
        )}

        {status === 'pending' && (
          <>
            <FiLoader className="w-16 h-16 text-amber-500 animate-spin mx-auto" />
            <h1 className="text-2xl font-bold">Payment Processing</h1>
            <p className="text-muted-foreground">Your payment is still being processed. This usually takes a moment.</p>
            <Button variant="outline" onClick={() => window.location.reload()} className="rounded-full">
              Check Again
            </Button>
            <Button variant="ghost" onClick={() => navigate('/library')} className="rounded-full">
              Back to Library
            </Button>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="w-20 h-20 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mx-auto">
              <FiAlertCircle className="w-10 h-10 text-red-600 dark:text-red-400" />
            </div>
            <h1 className="text-2xl font-bold">Something went wrong</h1>
            <p className="text-muted-foreground">We couldn't verify your payment. Please contact support if you were charged.</p>
            <Button onClick={() => navigate('/library')} className="rounded-full px-8" data-testid="back-to-library-btn">
              Back to Library
            </Button>
          </>
        )}
      </div>
    </div>
  );
}
