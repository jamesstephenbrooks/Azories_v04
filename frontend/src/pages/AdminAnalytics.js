import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  FiUsers, FiBook, FiDollarSign, FiZap, FiTrendingUp, 
  FiActivity, FiArrowLeft, FiRefreshCw, FiBarChart2, FiPieChart
} from 'react-icons/fi';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const AdminAnalytics = () => {
  const navigate = useNavigate();
  const [analytics, setAnalytics] = useState(null);
  const [vipUsage, setVipUsage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    const token = localStorage.getItem('azories-token');
    if (!token) {
      navigate('/auth');
      return;
    }

    setLoading(true);
    try {
      const [analyticsRes, vipRes] = await Promise.all([
        fetch(`${API_URL}/api/admin/analytics`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch(`${API_URL}/api/admin/vip-usage`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      if (!analyticsRes.ok) {
        if (analyticsRes.status === 403) {
          toast.error('Admin access required');
          navigate('/');
          return;
        }
        throw new Error('Failed to fetch analytics');
      }

      const analyticsData = await analyticsRes.json();
      const vipData = await vipRes.json();
      
      setAnalytics(analyticsData);
      setVipUsage(vipData);
    } catch (error) {
      console.error('Error fetching analytics:', error);
      toast.error('Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({ icon: Icon, label, value, subtext, color = 'purple' }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-xl shadow-sm p-6 border border-gray-100"
    >
      <div className="flex items-center justify-between">
        <div className={`w-12 h-12 rounded-lg bg-${color}-100 flex items-center justify-center`}>
          <Icon className={`text-2xl text-${color}-600`} />
        </div>
        <span className="text-3xl font-bold text-gray-900">{value}</span>
      </div>
      <div className="mt-4">
        <h3 className="text-gray-600 font-medium">{label}</h3>
        {subtext && <p className="text-sm text-gray-400 mt-1">{subtext}</p>}
      </div>
    </motion.div>
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-purple-500 border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center">
            <button
              onClick={() => navigate(-1)}
              className="mr-4 p-2 hover:bg-gray-200 rounded-lg transition-colors"
            >
              <FiArrowLeft className="text-xl" />
            </button>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Admin Analytics</h1>
              <p className="text-gray-500">Monitor your platform performance</p>
            </div>
          </div>
          <button
            onClick={fetchAnalytics}
            className="flex items-center gap-2 bg-purple-600 hover:bg-purple-500 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <FiRefreshCw />
            Refresh
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-8">
          {['overview', 'revenue', 'vip-costs', 'users'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === tab 
                  ? 'bg-purple-600 text-white' 
                  : 'bg-white text-gray-600 hover:bg-gray-100'
              }`}
            >
              {tab.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </button>
          ))}
        </div>

        {activeTab === 'overview' && analytics && (
          <>
            {/* Overview Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <StatCard
                icon={FiUsers}
                label="Total Users"
                value={analytics.users.total}
                subtext={`+${analytics.users.this_week} this week`}
                color="blue"
              />
              <StatCard
                icon={FiBook}
                label="Published Books"
                value={analytics.books.published}
                subtext={`${analytics.books.total} total books`}
                color="green"
              />
              <StatCard
                icon={FiDollarSign}
                label="Total Revenue"
                value={`$${analytics.revenue.total.toFixed(2)}`}
                subtext={`$${analytics.revenue.this_month.toFixed(2)} this month`}
                color="yellow"
              />
              <StatCard
                icon={FiZap}
                label="Credits Sold"
                value={analytics.credits.total_purchased.toLocaleString()}
                subtext="Total credits purchased"
                color="purple"
              />
            </div>

            {/* Engagement Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <FiActivity className="mr-2 text-purple-600" />
                  Reading Engagement
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total Reads</span>
                    <span className="font-semibold">{analytics.engagement.total_reads}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Completed Books</span>
                    <span className="font-semibold">{analytics.engagement.completed_books}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Completion Rate</span>
                    <span className="font-semibold text-green-600">{analytics.engagement.completion_rate}%</span>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <FiBarChart2 className="mr-2 text-blue-600" />
                  Credit Usage
                </h3>
                <div className="space-y-2">
                  {analytics.credits.usage_by_operation?.map(op => (
                    <div key={op._id} className="flex justify-between text-sm">
                      <span className="text-gray-600">{op._id?.replace('_', ' ')}</span>
                      <span className="font-semibold">{op.count} uses ({op.total_credits} credits)</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <FiPieChart className="mr-2 text-pink-600" />
                  VIP Costs
                </h3>
                <div className="text-center py-4">
                  <div className="text-4xl font-bold text-pink-600">${analytics.vip_costs.total_cost_usd}</div>
                  <p className="text-gray-500 text-sm mt-2">{analytics.vip_costs.note}</p>
                </div>
              </div>
            </div>
          </>
        )}

        {activeTab === 'revenue' && analytics && (
          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">Recent Transactions</h3>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 text-gray-600">Date</th>
                    <th className="text-left py-3 px-4 text-gray-600">User</th>
                    <th className="text-left py-3 px-4 text-gray-600">Package</th>
                    <th className="text-right py-3 px-4 text-gray-600">Credits</th>
                    <th className="text-right py-3 px-4 text-gray-600">Amount</th>
                    <th className="text-center py-3 px-4 text-gray-600">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {analytics.recent_transactions?.map(tx => (
                    <tr key={tx.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4 text-sm">
                        {new Date(tx.completed_at).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-4 text-sm">{tx.user_email}</td>
                      <td className="py-3 px-4 text-sm capitalize">{tx.package_id}</td>
                      <td className="py-3 px-4 text-sm text-right">{tx.credits}</td>
                      <td className="py-3 px-4 text-sm text-right font-semibold">${tx.amount}</td>
                      <td className="py-3 px-4 text-center">
                        <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                          {tx.payment_status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {analytics.recent_transactions?.length === 0 && (
                <p className="text-center text-gray-500 py-8">No transactions yet</p>
              )}
            </div>
          </div>
        )}

        {activeTab === 'vip-costs' && vipUsage && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">VIP Users</h3>
              <div className="flex flex-wrap gap-2">
                {vipUsage.vip_users?.map(email => (
                  <span key={email} className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm">
                    {email}
                  </span>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Usage by VIP User</h3>
              <div className="space-y-4">
                {vipUsage.usage_by_user?.map(user => (
                  <div key={user._id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-medium">{user._id}</span>
                      <span className="text-red-600 font-bold">${user.total_cost_usd?.toFixed(2) || '0.00'}</span>
                    </div>
                    <div className="text-sm text-gray-500">
                      {user.total_operations} operations
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent VIP Operations</h3>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-4 text-gray-600">Time</th>
                      <th className="text-left py-3 px-4 text-gray-600">User</th>
                      <th className="text-left py-3 px-4 text-gray-600">Operation</th>
                      <th className="text-right py-3 px-4 text-gray-600">Cost</th>
                    </tr>
                  </thead>
                  <tbody>
                    {vipUsage.recent_operations?.slice(0, 20).map((op, idx) => (
                      <tr key={idx} className="border-b border-gray-100">
                        <td className="py-3 px-4 text-sm">
                          {new Date(op.timestamp).toLocaleString()}
                        </td>
                        <td className="py-3 px-4 text-sm">{op.user_email}</td>
                        <td className="py-3 px-4 text-sm">{op.operation?.replace('_', ' ')}</td>
                        <td className="py-3 px-4 text-sm text-right text-red-600">${op.actual_cost_usd?.toFixed(3)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'users' && analytics && (
          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">Most Active Users (by credits spent)</h3>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 text-gray-600">#</th>
                    <th className="text-left py-3 px-4 text-gray-600">User</th>
                    <th className="text-right py-3 px-4 text-gray-600">Credits Spent</th>
                  </tr>
                </thead>
                <tbody>
                  {analytics.active_users?.map((user, idx) => (
                    <tr key={user._id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4 text-sm font-semibold text-gray-400">{idx + 1}</td>
                      <td className="py-3 px-4">
                        <div className="font-medium">{user.name || 'Anonymous'}</div>
                        <div className="text-sm text-gray-500">{user.email}</div>
                      </td>
                      <td className="py-3 px-4 text-right font-semibold text-purple-600">
                        {user.total_spent} credits
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {analytics.active_users?.length === 0 && (
                <p className="text-center text-gray-500 py-8">No usage data yet</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminAnalytics;
