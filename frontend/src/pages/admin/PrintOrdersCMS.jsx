import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import Navbar from '../../components/Navbar';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { 
  FiPackage, FiDollarSign, FiTrendingUp, FiTruck, 
  FiRefreshCw, FiEye, FiFilter, FiDownload,
  FiCheckCircle, FiClock, FiAlertCircle, FiXCircle
} from 'react-icons/fi';
import api from '../../services/api';

const API_URL = process.env.REACT_APP_BACKEND_URL;

function PrintOrdersCMS() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [summary, setSummary] = useState(null);
  const [financialSummary, setFinancialSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [periodFilter, setPeriodFilter] = useState('all');

  useEffect(() => {
    fetchOrders();
    fetchFinancialSummary();
  }, [statusFilter]);

  useEffect(() => {
    fetchFinancialSummary();
  }, [periodFilter]);

  async function fetchOrders() {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (statusFilter) params.append('status', statusFilter);
      
      const response = await api.get(`${API_URL}/api/print/admin/orders?${params}`);
      setOrders(response.data.orders || []);
      setSummary(response.data.summary || null);
    } catch (error) {
      console.error('Failed to fetch orders:', error);
    } finally {
      setLoading(false);
    }
  }

  async function fetchFinancialSummary() {
    try {
      const response = await api.get(`${API_URL}/api/print/admin/financial-summary?period=${periodFilter}`);
      setFinancialSummary(response.data);
    } catch (error) {
      console.error('Failed to fetch financial summary:', error);
    }
  }

  async function updateOrderStatus(orderId, newStatus) {
    try {
      await api.put(`${API_URL}/api/print/admin/orders/${orderId}/status?status=${newStatus}`);
      fetchOrders();
    } catch (error) {
      console.error('Failed to update order status:', error);
    }
  }

  function getStatusIcon(status) {
    switch (status) {
      case 'paid':
      case 'completed':
      case 'delivered':
        return <FiCheckCircle className="w-4 h-4 text-green-500" />;
      case 'processing':
      case 'in_production':
      case 'shipped':
        return <FiClock className="w-4 h-4 text-blue-500" />;
      case 'pending':
        return <FiAlertCircle className="w-4 h-4 text-yellow-500" />;
      case 'cancelled':
      case 'refunded':
        return <FiXCircle className="w-4 h-4 text-red-500" />;
      default:
        return <FiPackage className="w-4 h-4 text-gray-500" />;
    }
  }

  function getStatusBadgeClass(status) {
    switch (status) {
      case 'paid':
      case 'completed':
      case 'delivered':
        return 'bg-green-100 text-green-800';
      case 'processing':
      case 'in_production':
        return 'bg-blue-100 text-blue-800';
      case 'shipped':
        return 'bg-purple-100 text-purple-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'cancelled':
      case 'refunded':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  }

  function formatCurrency(amount, currency = 'GBP') {
    const symbol = currency === 'GBP' ? '£' : '$';
    return `${symbol}${parseFloat(amount || 0).toFixed(2)}`;
  }

  function formatDate(dateString) {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-GB', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <div className="pt-20 pb-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Print Orders CMS</h1>
            <p className="text-gray-500 mt-1">Track orders, manage fulfillment, and view financials</p>
          </div>
          <Button onClick={fetchOrders} variant="outline" className="flex items-center gap-2">
            <FiRefreshCw className="w-4 h-4" />
            Refresh
          </Button>
        </div>

        {/* Financial Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Total Revenue</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {summary ? formatCurrency(summary.total_revenue) : '£0.00'}
                  </p>
                </div>
                <div className="p-3 bg-green-100 rounded-full">
                  <FiDollarSign className="w-6 h-6 text-green-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Total Cost</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {summary ? formatCurrency(summary.total_cost) : '£0.00'}
                  </p>
                </div>
                <div className="p-3 bg-red-100 rounded-full">
                  <FiTruck className="w-6 h-6 text-red-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Total Profit</p>
                  <p className="text-2xl font-bold text-green-600">
                    {summary ? formatCurrency(summary.total_profit) : '£0.00'}
                  </p>
                </div>
                <div className="p-3 bg-emerald-100 rounded-full">
                  <FiTrendingUp className="w-6 h-6 text-emerald-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Total Orders</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {summary?.total_orders || 0}
                  </p>
                  <p className="text-xs text-gray-400">
                    {summary?.average_profit_margin || 0}% avg margin
                  </p>
                </div>
                <div className="p-3 bg-blue-100 rounded-full">
                  <FiPackage className="w-6 h-6 text-blue-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Detailed Financial Breakdown */}
        {financialSummary && (
          <Card className="mb-8">
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle className="text-lg">Financial Breakdown</CardTitle>
                <select
                  value={periodFilter}
                  onChange={(e) => setPeriodFilter(e.target.value)}
                  className="px-3 py-1.5 text-sm border rounded-lg bg-white"
                >
                  <option value="all">All Time</option>
                  <option value="today">Today</option>
                  <option value="week">Last 7 Days</option>
                  <option value="month">Last 30 Days</option>
                  <option value="year">Last Year</option>
                </select>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* GBP */}
                <div className="p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-medium text-gray-700 mb-3">GBP (£)</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Revenue</span>
                      <span className="font-medium">£{financialSummary.financials?.gbp?.revenue?.toFixed(2) || '0.00'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Cost (Gelato)</span>
                      <span className="font-medium text-red-600">-£{financialSummary.financials?.gbp?.cost?.toFixed(2) || '0.00'}</span>
                    </div>
                    <div className="border-t pt-2 flex justify-between">
                      <span className="font-medium">Profit</span>
                      <span className="font-bold text-green-600">£{financialSummary.financials?.gbp?.profit?.toFixed(2) || '0.00'}</span>
                    </div>
                  </div>
                </div>

                {/* USD */}
                <div className="p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-medium text-gray-700 mb-3">USD ($)</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Revenue</span>
                      <span className="font-medium">${financialSummary.financials?.usd?.revenue?.toFixed(2) || '0.00'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Cost (Gelato)</span>
                      <span className="font-medium text-red-600">-${financialSummary.financials?.usd?.cost?.toFixed(2) || '0.00'}</span>
                    </div>
                    <div className="border-t pt-2 flex justify-between">
                      <span className="font-medium">Profit</span>
                      <span className="font-bold text-green-600">${financialSummary.financials?.usd?.profit?.toFixed(2) || '0.00'}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Combined Profit */}
              <div className="mt-4 p-4 bg-emerald-50 rounded-lg border border-emerald-200">
                <div className="flex justify-between items-center">
                  <span className="text-emerald-700 font-medium">Combined Profit (GBP equivalent)</span>
                  <span className="text-2xl font-bold text-emerald-700">
                    £{financialSummary.financials?.combined_profit_gbp?.toFixed(2) || '0.00'}
                  </span>
                </div>
              </div>

              {/* Orders by Status */}
              {financialSummary.orders_by_status && Object.keys(financialSummary.orders_by_status).length > 0 && (
                <div className="mt-6">
                  <h4 className="font-medium text-gray-700 mb-3">Orders by Status</h4>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(financialSummary.orders_by_status).map(([status, count]) => (
                      <span key={status} className={`px-3 py-1 rounded-full text-sm ${getStatusBadgeClass(status)}`}>
                        {status}: {count}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Filters */}
        <Card className="mb-6">
          <CardContent className="py-4">
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2">
                <FiFilter className="w-4 h-4 text-gray-500" />
                <span className="text-sm text-gray-600">Filter by status:</span>
              </div>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-1.5 text-sm border rounded-lg bg-white"
              >
                <option value="">All Statuses</option>
                <option value="pending">Pending</option>
                <option value="paid">Paid</option>
                <option value="processing">Processing</option>
                <option value="shipped">Shipped</option>
                <option value="delivered">Delivered</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
                <option value="refunded">Refunded</option>
              </select>
            </div>
          </CardContent>
        </Card>

        {/* Orders Table */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Orders ({orders.length})</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <FiRefreshCw className="w-6 h-6 animate-spin text-gray-400" />
              </div>
            ) : orders.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <FiPackage className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>No orders found</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-gray-50">
                      <th className="px-4 py-3 text-left font-medium text-gray-600">Order</th>
                      <th className="px-4 py-3 text-left font-medium text-gray-600">Book</th>
                      <th className="px-4 py-3 text-left font-medium text-gray-600">Status</th>
                      <th className="px-4 py-3 text-left font-medium text-gray-600">Date</th>
                      <th className="px-4 py-3 text-right font-medium text-gray-600">Revenue</th>
                      <th className="px-4 py-3 text-right font-medium text-gray-600">Cost</th>
                      <th className="px-4 py-3 text-right font-medium text-gray-600">Profit</th>
                      <th className="px-4 py-3 text-center font-medium text-gray-600">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {orders.map((order) => (
                      <tr key={order.id} className="border-b hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <div>
                            <span className="font-mono text-xs text-gray-500">{order.order_reference}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="max-w-[200px]">
                            <p className="font-medium text-gray-900 truncate">{order.book_title || 'Untitled'}</p>
                            <p className="text-xs text-gray-500">{order.product_type?.replace('_', ' ')}</p>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs ${getStatusBadgeClass(order.status)}`}>
                            {getStatusIcon(order.status)}
                            {order.status}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-gray-600">
                          {formatDate(order.created_at)}
                        </td>
                        <td className="px-4 py-3 text-right font-medium">
                          {formatCurrency(order.financial?.amount_charged, order.financial?.currency)}
                        </td>
                        <td className="px-4 py-3 text-right text-red-600">
                          {formatCurrency(order.financial?.total_cost, order.financial?.currency)}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <span className={order.financial?.profit >= 0 ? 'text-green-600 font-medium' : 'text-red-600'}>
                            {formatCurrency(order.financial?.profit, order.financial?.currency)}
                          </span>
                          <span className="text-xs text-gray-400 ml-1">
                            ({order.financial?.profit_margin}%)
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center justify-center gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setSelectedOrder(order)}
                              className="p-1"
                            >
                              <FiEye className="w-4 h-4" />
                            </Button>
                            <select
                              value={order.status}
                              onChange={(e) => updateOrderStatus(order.id, e.target.value)}
                              className="text-xs border rounded px-1 py-0.5"
                            >
                              <option value="pending">Pending</option>
                              <option value="paid">Paid</option>
                              <option value="processing">Processing</option>
                              <option value="shipped">Shipped</option>
                              <option value="delivered">Delivered</option>
                              <option value="completed">Completed</option>
                              <option value="cancelled">Cancelled</option>
                              <option value="refunded">Refunded</option>
                            </select>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Order Detail Modal */}
        {selectedOrder && (
          <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={() => setSelectedOrder(null)}>
            <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
              <div className="p-6">
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h3 className="text-lg font-bold">Order Details</h3>
                    <p className="text-sm text-gray-500 font-mono">{selectedOrder.order_reference}</p>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => setSelectedOrder(null)}>×</Button>
                </div>

                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div>
                    <p className="text-sm text-gray-500">Book</p>
                    <p className="font-medium">{selectedOrder.book_title}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Product</p>
                    <p className="font-medium">{selectedOrder.product_type}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Status</p>
                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs ${getStatusBadgeClass(selectedOrder.status)}`}>
                      {selectedOrder.status}
                    </span>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Created</p>
                    <p className="font-medium">{formatDate(selectedOrder.created_at)}</p>
                  </div>
                </div>

                {/* Financial Breakdown */}
                <div className="bg-gray-50 rounded-lg p-4 mb-6">
                  <h4 className="font-medium mb-3">Financial Breakdown</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Retail Price</span>
                      <span>{formatCurrency(selectedOrder.financial?.retail_price, selectedOrder.financial?.currency)}</span>
                    </div>
                    {selectedOrder.financial?.discount_applied > 0 && (
                      <div className="flex justify-between text-orange-600">
                        <span>Discount Applied</span>
                        <span>-{formatCurrency(selectedOrder.financial?.discount_applied, selectedOrder.financial?.currency)}</span>
                      </div>
                    )}
                    <div className="flex justify-between font-medium">
                      <span>Amount Charged</span>
                      <span>{formatCurrency(selectedOrder.financial?.amount_charged, selectedOrder.financial?.currency)}</span>
                    </div>
                    <div className="border-t my-2"></div>
                    <div className="flex justify-between text-red-600">
                      <span>Gelato Product Cost</span>
                      <span>-{formatCurrency(selectedOrder.financial?.gelato_product_cost, selectedOrder.financial?.currency)}</span>
                    </div>
                    <div className="flex justify-between text-red-600">
                      <span>Gelato Shipping</span>
                      <span>-{formatCurrency(selectedOrder.financial?.gelato_shipping_cost, selectedOrder.financial?.currency)}</span>
                    </div>
                    <div className="border-t my-2"></div>
                    <div className="flex justify-between font-bold text-lg">
                      <span>Net Profit</span>
                      <span className={selectedOrder.financial?.profit >= 0 ? 'text-green-600' : 'text-red-600'}>
                        {formatCurrency(selectedOrder.financial?.profit, selectedOrder.financial?.currency)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Shipping Address */}
                {selectedOrder.shipping_address && (
                  <div className="mb-6">
                    <h4 className="font-medium mb-3">Shipping Address</h4>
                    <div className="text-sm text-gray-600">
                      <p>{selectedOrder.shipping_address.firstName} {selectedOrder.shipping_address.lastName}</p>
                      <p>{selectedOrder.shipping_address.addressLine1}</p>
                      {selectedOrder.shipping_address.addressLine2 && <p>{selectedOrder.shipping_address.addressLine2}</p>}
                      <p>{selectedOrder.shipping_address.city}, {selectedOrder.shipping_address.postCode}</p>
                      <p>{selectedOrder.shipping_address.countryIsoCode}</p>
                    </div>
                  </div>
                )}

                {/* Gelato Info */}
                {selectedOrder.gelato_order_id && (
                  <div>
                    <h4 className="font-medium mb-3">Gelato Order</h4>
                    <p className="text-sm font-mono text-gray-500">{selectedOrder.gelato_order_id}</p>
                    {selectedOrder.gelato_status && (
                      <p className="text-sm mt-1">Status: {selectedOrder.gelato_status}</p>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default PrintOrdersCMS;
