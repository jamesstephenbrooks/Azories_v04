import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { FiPackage, FiTruck, FiCheckCircle, FiClock, FiExternalLink, FiBookOpen, FiRefreshCw, FiAlertCircle, FiArrowLeft, FiXCircle } from 'react-icons/fi';
import Navbar from '../components/Navbar';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Status config: label, colour, icon
const STATUS_CONFIG = {
  preparing: {
    label: 'Preparing',
    icon: FiClock,
    bg: 'bg-amber-500/15',
    text: 'text-amber-400',
    border: 'border-amber-500/30',
    dot: 'bg-amber-400',
  },
  shipped: {
    label: 'Shipped',
    icon: FiTruck,
    bg: 'bg-blue-500/15',
    text: 'text-blue-400',
    border: 'border-blue-500/30',
    dot: 'bg-blue-400',
  },
  delivered: {
    label: 'Delivered',
    icon: FiCheckCircle,
    bg: 'bg-emerald-500/15',
    text: 'text-emerald-400',
    border: 'border-emerald-500/30',
    dot: 'bg-emerald-400',
  },
  cancelled: {
    label: 'Cancelled',
    icon: FiXCircle,
    bg: 'bg-red-500/15',
    text: 'text-red-400',
    border: 'border-red-500/30',
    dot: 'bg-red-400',
  },
};

// Carrier tracking URL templates
const CARRIER_URLS = {
  royalmail: 'https://www.royalmail.com/track-your-item#/tracking-results/',
  ups: 'https://www.ups.com/track?tracknum=',
  fedex: 'https://www.fedex.com/fedextrack/?trknbr=',
  dhl: 'https://www.dhl.com/en/express/tracking.html?AWB=',
  dpd: 'https://www.dpd.co.uk/service/parcel-tracking/?q=',
  usps: 'https://tools.usps.com/go/TrackConfirmAction?tLabels=',
  default: 'https://www.google.com/search?q=track+package+',
};

function getTrackingUrl(carrier, number) {
  if (!number) return null;
  const key = (carrier || '').toLowerCase().replace(/\s+/g, '');
  const base = CARRIER_URLS[key] || CARRIER_URLS.default;
  return base + encodeURIComponent(number);
}

function formatDate(dateStr) {
  if (!dateStr) return '—';
  try {
    return new Intl.DateTimeFormat('en-GB', {
      day: 'numeric', month: 'short', year: 'numeric',
    }).format(new Date(dateStr));
  } catch {
    return dateStr;
  }
}

// ─── Skeleton card ──────────────────────────────────────────────────────────
function SkeletonCard() {
  return (
    <div className="animate-pulse rounded-2xl border border-white/8 bg-white/4 p-5 flex gap-4">
      <div className="w-20 h-24 rounded-xl bg-white/10 flex-shrink-0" />
      <div className="flex-1 space-y-3 pt-1">
        <div className="h-4 bg-white/10 rounded-full w-3/4" />
        <div className="h-3 bg-white/10 rounded-full w-1/2" />
        <div className="h-3 bg-white/10 rounded-full w-2/5" />
        <div className="h-7 bg-white/10 rounded-full w-28 mt-2" />
      </div>
    </div>
  );
}

// ─── Order card ─────────────────────────────────────────────────────────────
function OrderCard({ order }) {
  const navigate = useNavigate();
  const status = order.display_status || 'preparing';
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.preparing;
  const Icon = cfg.icon;

  // Extract tracking info (Gelato returns an array)
  const trackingList = order.tracking || [];
  const firstTracking = trackingList[0] || {};
  const trackingNumber = firstTracking.tracking_number || firstTracking.trackingNumber;
  const carrier = firstTracking.carrier || firstTracking.courier;
  const trackingUrl = getTrackingUrl(carrier, trackingNumber);

  return (
    <div
      className="group rounded-2xl border border-white/10 bg-gradient-to-br from-white/5 to-white/2 hover:border-purple-500/30 hover:bg-white/6 transition-all duration-200 overflow-hidden"
      data-testid={`order-card-${order.id}`}
    >
      <div className="p-5 flex gap-4">
        {/* Cover thumbnail */}
        <button
          onClick={() => order.book_id && navigate(`/read/${order.book_id}`)}
          className="flex-shrink-0 w-[68px] h-[85px] rounded-lg overflow-hidden bg-white/8 border border-white/10 hover:opacity-90 transition-opacity"
          title="Open book"
          data-testid={`order-book-cover-${order.id}`}
        >
          {order.book_cover_url ? (
            <img
              src={order.book_cover_url}
              alt={order.book_title || 'Book cover'}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-white/20">
              <FiBookOpen className="w-6 h-6" />
            </div>
          )}
        </button>

        {/* Info */}
        <div className="flex-1 min-w-0 flex flex-col justify-between">
          <div>
            <h3 className="font-semibold text-white/90 text-sm leading-tight truncate" data-testid={`order-title-${order.id}`}>
              {order.book_title || 'Untitled Book'}
            </h3>
            <p className="text-white/40 text-xs mt-1" data-testid={`order-ref-${order.id}`}>
              {order.order_reference || order.id?.slice(0, 8).toUpperCase()}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 mt-2">
            {/* Date */}
            <span className="text-white/40 text-xs">
              {formatDate(order.created_at)}
            </span>

            {/* Separator */}
            <span className="text-white/20 text-xs">·</span>

            {/* Price */}
            <span className="text-white/70 text-xs font-medium" data-testid={`order-price-${order.id}`}>
              {order.price_display || '—'}
            </span>
          </div>

          {/* Status badge */}
          <div className="mt-3">
            <span
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${cfg.bg} ${cfg.text} ${cfg.border}`}
              data-testid={`order-status-${order.id}`}
            >
              <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot} animate-pulse`} />
              <Icon className="w-3 h-3" />
              {cfg.label}
            </span>
          </div>
        </div>
      </div>

      {/* Tracking row — shown only when shipped */}
      {(status === 'shipped' || status === 'delivered') && trackingNumber && (
        <div className="px-5 pb-4 pt-0">
          <div className="flex items-center gap-2 p-2.5 rounded-xl bg-white/5 border border-white/8">
            <FiTruck className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-white/40 text-[10px] uppercase tracking-wider leading-none mb-0.5">
                {carrier || 'Carrier'} · Tracking
              </p>
              <p className="text-white/80 text-xs font-mono truncate">{trackingNumber}</p>
            </div>
            {trackingUrl && (
              <a
                href={trackingUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-shrink-0 flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 transition-colors"
                data-testid={`tracking-link-${order.id}`}
              >
                Track <FiExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Empty state ─────────────────────────────────────────────────────────────
function EmptyState() {
  const navigate = useNavigate();
  return (
    <div className="flex flex-col items-center justify-center py-20 px-6 text-center" data-testid="orders-empty-state">
      <div className="w-20 h-20 rounded-3xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center mb-6">
        <FiPackage className="w-9 h-9 text-purple-400/60" />
      </div>
      <h2 className="text-xl font-semibold text-white/80 mb-2">No print orders yet</h2>
      <p className="text-white/40 text-sm max-w-xs mb-8 leading-relaxed">
        Once you order a printed copy of one of your books, it will appear here.
      </p>
      <button
        onClick={() => navigate('/dashboard')}
        className="inline-flex items-center gap-2 px-6 py-2.5 rounded-full bg-purple-600 hover:bg-purple-500 active:bg-purple-700 text-white text-sm font-medium transition-colors"
        data-testid="orders-cta-button"
      >
        <FiBookOpen className="w-4 h-4" />
        Browse My Books
      </button>
    </div>
  );
}

// ─── Error state ─────────────────────────────────────────────────────────────
function ErrorState({ onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 px-6 text-center" data-testid="orders-error-state">
      <div className="w-16 h-16 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mb-5">
        <FiAlertCircle className="w-7 h-7 text-red-400/70" />
      </div>
      <h2 className="text-lg font-semibold text-white/80 mb-2">Couldn't load orders</h2>
      <p className="text-white/40 text-sm max-w-xs mb-6">
        There was a problem fetching your orders. Please try again.
      </p>
      <button
        onClick={onRetry}
        className="inline-flex items-center gap-2 px-5 py-2 rounded-full border border-white/15 text-white/70 hover:text-white hover:border-white/30 text-sm transition-colors"
        data-testid="orders-retry-button"
      >
        <FiRefreshCw className="w-4 h-4" />
        Retry
      </button>
    </div>
  );
}

// ─── Main page ───────────────────────────────────────────────────────────────
export default function MyOrders() {
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchOrders = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('azories-token');
      const { data } = await axios.get(`${API}/print/my-orders`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setOrders(data.orders || []);
    } catch (err) {
      console.error('Failed to fetch orders:', err);
      setError(err.response?.data?.detail || 'Failed to load orders');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchOrders();
  }, [fetchOrders]);

  // Group orders by status for quick summary counts
  const statusCounts = orders.reduce((acc, o) => {
    const s = o.display_status || 'preparing';
    acc[s] = (acc[s] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="min-h-screen bg-[#0d0d1a]" data-testid="my-orders-page">
      <Navbar />

      {/* Subtle grid background */}
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          backgroundImage: 'radial-gradient(ellipse at 20% 20%, rgba(124,58,237,0.06) 0%, transparent 60%), radial-gradient(ellipse at 80% 80%, rgba(236,72,153,0.04) 0%, transparent 60%)',
        }}
      />

      <div className="relative max-w-2xl mx-auto px-4 pt-24 pb-16">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-1.5 text-white/40 hover:text-white/70 text-sm mb-5 transition-colors"
            data-testid="orders-back-btn"
          >
            <FiArrowLeft className="w-4 h-4" />
            Back
          </button>

          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight" data-testid="orders-heading">
                My Orders
              </h1>
              {!loading && !error && orders.length > 0 && (
                <p className="text-white/40 text-sm mt-1">
                  {orders.length} {orders.length === 1 ? 'order' : 'orders'} total
                </p>
              )}
            </div>

            {/* Summary chips — visible when there are orders */}
            {!loading && !error && orders.length > 0 && (
              <div className="flex flex-wrap gap-1.5" data-testid="orders-status-summary">
                {Object.entries(statusCounts).map(([status, count]) => {
                  const cfg = STATUS_CONFIG[status];
                  if (!cfg) return null;
                  return (
                    <span
                      key={status}
                      className={`px-2.5 py-1 rounded-full text-xs font-medium border ${cfg.bg} ${cfg.text} ${cfg.border}`}
                    >
                      {count} {cfg.label}
                    </span>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Content */}
        {loading ? (
          <div className="space-y-4" data-testid="orders-loading">
            {[1, 2, 3].map((i) => <SkeletonCard key={i} />)}
          </div>
        ) : error ? (
          <ErrorState onRetry={fetchOrders} />
        ) : orders.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="space-y-3" data-testid="orders-list">
            {orders.map((order) => (
              <OrderCard key={order.id || order.order_reference} order={order} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
