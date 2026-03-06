import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../components/ui/dialog';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { FiPrinter, FiTruck, FiCreditCard, FiCheck, FiPackage, FiAlertCircle, FiEye } from 'react-icons/fi';
import { toast } from 'sonner';
import BonusPagesPreview from './print/BonusPagesPreview';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Common countries for shipping
const COUNTRIES = [
  { code: 'GB', name: 'United Kingdom' },
  { code: 'US', name: 'United States' },
  { code: 'CA', name: 'Canada' },
  { code: 'AU', name: 'Australia' },
  { code: 'DE', name: 'Germany' },
  { code: 'FR', name: 'France' },
  { code: 'ES', name: 'Spain' },
  { code: 'IT', name: 'Italy' },
  { code: 'NL', name: 'Netherlands' },
  { code: 'IE', name: 'Ireland' },
  { code: 'NZ', name: 'New Zealand' },
  { code: 'SE', name: 'Sweden' },
  { code: 'NO', name: 'Norway' },
  { code: 'DK', name: 'Denmark' },
  { code: 'BE', name: 'Belgium' },
  { code: 'AT', name: 'Austria' },
  { code: 'CH', name: 'Switzerland' },
  { code: 'JP', name: 'Japan' },
  { code: 'SG', name: 'Singapore' },
];

const SHIPPING_METHODS = [
  { id: 'normal', name: 'Standard Shipping', days: '5-10 business days' },
  { id: 'express', name: 'Express Shipping', days: '2-4 business days' },
  { id: 'overnight', name: 'Next Day Delivery', days: '1-2 business days' },
];

export default function PrintOrderModal({ 
  isOpen, 
  onClose, 
  book,
  comingSoon = false // Print on Demand is now active!
}) {
  const [step, setStep] = useState(1); // 1: Info, 2: Address, 3: Shipping, 4: Payment, 5: Confirmation
  const [loading, setLoading] = useState(false);
  const [productInfo, setProductInfo] = useState(null);
  const [preparing, setPreparing] = useState(false);
  const [prepData, setPrepData] = useState(null);
  
  // Address form
  const [address, setAddress] = useState({
    firstName: '',
    lastName: '',
    addressLine1: '',
    addressLine2: '',
    city: '',
    postCode: '',
    state: '',
    countryIsoCode: 'GB',
    email: '',
    phone: ''
  });
  
  // Shipping
  const [shippingMethod, setShippingMethod] = useState('normal');
  const [shippingQuote, setShippingQuote] = useState(null);
  const [priceEstimate, setPriceEstimate] = useState(null);
  
  // Order result
  const [orderResult, setOrderResult] = useState(null);

  // Fetch product info on mount
  useEffect(() => {
    if (isOpen) {
      fetchProductInfo();
    }
  }, [isOpen]);

  // Fetch shipping quote when country changes
  useEffect(() => {
    if (prepData?.page_count && address.countryIsoCode) {
      fetchPriceEstimate();
    }
  }, [address.countryIsoCode, shippingMethod, prepData]);

  const fetchProductInfo = async () => {
    try {
      const response = await fetch(`${API_URL}/api/print/product-info`);
      if (response.ok) {
        const data = await response.json();
        setProductInfo(data);
      }
    } catch (error) {
      console.error('Error fetching product info:', error);
    }
  };

  const prepareBook = async () => {
    setPreparing(true);
    try {
      const token = localStorage.getItem('azories-token');
      const response = await fetch(`${API_URL}/api/print/prepare/${book.id}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setPrepData(data);
        setStep(2);
      } else {
        toast.error('Failed to prepare book for printing');
      }
    } catch (error) {
      toast.error('Error preparing book');
    } finally {
      setPreparing(false);
    }
  };

  const fetchPriceEstimate = async () => {
    if (!prepData?.page_count) return;
    
    try {
      const response = await fetch(
        `${API_URL}/api/print/price-estimate?page_count=${prepData.page_count}&country_code=${address.countryIsoCode}&shipping_method=${shippingMethod}`
      );
      if (response.ok) {
        const data = await response.json();
        setPriceEstimate(data.estimate);
        setShippingQuote(data.shipping_options);
      }
    } catch (error) {
      console.error('Error fetching price:', error);
    }
  };

  const submitOrder = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('azories-token');
      const response = await fetch(`${API_URL}/api/print/create-order`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          book_id: book.id,
          shipping_address: address,
          shipping_method: shippingMethod
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setOrderResult(data);
        setStep(5);
        toast.success('Order placed successfully!');
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to place order');
      }
    } catch (error) {
      toast.error('Error placing order');
    } finally {
      setLoading(false);
    }
  };

  const handleAddressChange = (field, value) => {
    setAddress(prev => ({ ...prev, [field]: value }));
  };

  const validateAddress = () => {
    const required = ['firstName', 'lastName', 'addressLine1', 'city', 'postCode', 'countryIsoCode', 'email'];
    return required.every(field => address[field]?.trim());
  };

  const formatPrice = (amount, currency = 'GBP') => {
    const symbol = currency === 'GBP' ? '£' : '$';
    return `${symbol}${amount?.toFixed(2) || '0.00'}`;
  };

  // Coming Soon State
  const [showBonusPreview, setShowBonusPreview] = useState(false);
  
  if (comingSoon) {
    return (
      <>
        <Dialog open={isOpen} onOpenChange={onClose}>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <FiPrinter className="text-purple-500" />
                Print Your Book
              </DialogTitle>
            </DialogHeader>
            
            <div className="text-center py-6">
              <div className="w-20 h-20 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <FiPackage className="w-10 h-10 text-purple-500" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Coming Soon!</h3>
              <p className="text-gray-600 mb-4">
                We're putting the finishing touches on our print-on-demand service. 
                Soon you'll be able to order beautiful printed copies of your stories!
              </p>
              
              {/* Product info */}
              <div className="bg-purple-50 rounded-lg p-4 text-sm text-purple-700 mb-4">
                <p className="font-medium mb-1">Premium 8x8" Photobook</p>
                <p>Softcover with matt lamination • High-quality printing</p>
                <p className="mt-2 font-semibold">Starting from £14.99 / $19.99</p>
              </div>
              
              {/* Bonus pages preview button */}
              <div className="bg-gradient-to-r from-amber-50 to-purple-50 rounded-lg p-4 mb-4">
                <p className="text-sm text-gray-600 mb-2">
                  Each printed book includes <span className="font-semibold text-purple-600">7 bonus pages</span>:
                </p>
                <p className="text-xs text-gray-500 mb-3">
                  Welcome • Dedication • The End • Thank You • Certificate • About Azories • Meet Azora
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowBonusPreview(true)}
                  className="gap-2"
                >
                  <FiEye className="w-4 h-4" />
                  Preview Bonus Pages
                </Button>
              </div>
            </div>
            
            <Button onClick={onClose} className="w-full">
              Got it!
            </Button>
          </DialogContent>
        </Dialog>
        
        {/* Bonus pages preview modal */}
        <BonusPagesPreview
          isOpen={showBonusPreview}
          onClose={() => setShowBonusPreview(false)}
          bookTitle={book?.title}
          childName={book?.main_character_name || book?.child_name}
        />
      </>
    );
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FiPrinter className="text-purple-500" />
            Order Printed Book
          </DialogTitle>
          <DialogDescription>
            Get a beautiful printed copy of "{book?.title}"
          </DialogDescription>
        </DialogHeader>

        {/* Progress Steps */}
        <div className="flex justify-between mb-6">
          {[
            { num: 1, label: 'Product' },
            { num: 2, label: 'Address' },
            { num: 3, label: 'Shipping' },
            { num: 4, label: 'Review' },
            { num: 5, label: 'Done' }
          ].map(({ num, label }) => (
            <div key={num} className="flex flex-col items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
                ${step >= num ? 'bg-purple-500 text-white' : 'bg-gray-200 text-gray-500'}`}>
                {step > num ? <FiCheck size={16} /> : num}
              </div>
              <span className="text-xs mt-1 text-gray-500">{label}</span>
            </div>
          ))}
        </div>

        {/* Step 1: Product Info */}
        {step === 1 && (
          <div className="space-y-4">
            <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg p-4">
              <h4 className="font-semibold mb-2">8x8" Premium Photobook</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Softcover with matt lamination</li>
                <li>• 170gsm coated silk pages</li>
                <li>• Perfect bound (glued binding)</li>
                <li>• Includes bonus activity pages</li>
              </ul>
              <p className="mt-3 text-lg font-bold text-purple-600">
                From £14.99 / $19.99
              </p>
            </div>
            
            <div className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
              <FiTruck className="text-blue-500 mt-1 flex-shrink-0" />
              <div className="text-sm">
                <p className="font-medium text-blue-700">Worldwide Shipping</p>
                <p className="text-blue-600">Ships to over 200 countries</p>
              </div>
            </div>

            <Button 
              className="w-full" 
              onClick={prepareBook}
              disabled={preparing}
            >
              {preparing ? 'Preparing...' : 'Continue to Shipping Address'}
            </Button>
          </div>
        )}

        {/* Step 2: Shipping Address */}
        {step === 2 && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>First Name *</Label>
                <Input 
                  value={address.firstName}
                  onChange={(e) => handleAddressChange('firstName', e.target.value)}
                  placeholder="John"
                />
              </div>
              <div>
                <Label>Last Name *</Label>
                <Input 
                  value={address.lastName}
                  onChange={(e) => handleAddressChange('lastName', e.target.value)}
                  placeholder="Smith"
                />
              </div>
            </div>
            
            <div>
              <Label>Email *</Label>
              <Input 
                type="email"
                value={address.email}
                onChange={(e) => handleAddressChange('email', e.target.value)}
                placeholder="john@example.com"
              />
            </div>
            
            <div>
              <Label>Address Line 1 *</Label>
              <Input 
                value={address.addressLine1}
                onChange={(e) => handleAddressChange('addressLine1', e.target.value)}
                placeholder="123 Main Street"
              />
            </div>
            
            <div>
              <Label>Address Line 2</Label>
              <Input 
                value={address.addressLine2}
                onChange={(e) => handleAddressChange('addressLine2', e.target.value)}
                placeholder="Apt 4B (optional)"
              />
            </div>
            
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>City *</Label>
                <Input 
                  value={address.city}
                  onChange={(e) => handleAddressChange('city', e.target.value)}
                  placeholder="London"
                />
              </div>
              <div>
                <Label>Postal Code *</Label>
                <Input 
                  value={address.postCode}
                  onChange={(e) => handleAddressChange('postCode', e.target.value)}
                  placeholder="SW1A 1AA"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>State/Province</Label>
                <Input 
                  value={address.state}
                  onChange={(e) => handleAddressChange('state', e.target.value)}
                  placeholder="Optional"
                />
              </div>
              <div>
                <Label>Country *</Label>
                <Select 
                  value={address.countryIsoCode}
                  onValueChange={(v) => handleAddressChange('countryIsoCode', v)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {COUNTRIES.map(c => (
                      <SelectItem key={c.code} value={c.code}>{c.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div>
              <Label>Phone (for delivery)</Label>
              <Input 
                value={address.phone}
                onChange={(e) => handleAddressChange('phone', e.target.value)}
                placeholder="+44 7700 900000"
              />
            </div>

            <div className="flex gap-3">
              <Button variant="outline" onClick={() => setStep(1)} className="flex-1">
                Back
              </Button>
              <Button 
                onClick={() => setStep(3)} 
                className="flex-1"
                disabled={!validateAddress()}
              >
                Continue
              </Button>
            </div>
          </div>
        )}

        {/* Step 3: Shipping Method */}
        {step === 3 && (
          <div className="space-y-4">
            <h4 className="font-medium">Select Shipping Method</h4>
            
            <div className="space-y-2">
              {SHIPPING_METHODS.map(method => (
                <div 
                  key={method.id}
                  className={`p-4 border rounded-lg cursor-pointer transition-colors
                    ${shippingMethod === method.id ? 'border-purple-500 bg-purple-50' : 'hover:bg-gray-50'}`}
                  onClick={() => setShippingMethod(method.id)}
                >
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="font-medium">{method.name}</p>
                      <p className="text-sm text-gray-500">{method.days}</p>
                    </div>
                    <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center
                      ${shippingMethod === method.id ? 'border-purple-500' : 'border-gray-300'}`}>
                      {shippingMethod === method.id && (
                        <div className="w-3 h-3 rounded-full bg-purple-500" />
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {priceEstimate && (
              <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Book Price</span>
                  <span>{formatPrice(priceEstimate.base_price, priceEstimate.currency)}</span>
                </div>
                {priceEstimate.extra_pages > 0 && (
                  <div className="flex justify-between text-sm text-gray-500">
                    <span>Extra pages ({priceEstimate.extra_pages})</span>
                    <span>{formatPrice(priceEstimate.extra_page_cost, priceEstimate.currency)}</span>
                  </div>
                )}
                <div className="flex justify-between text-sm">
                  <span>Shipping</span>
                  <span>{formatPrice(priceEstimate.shipping, priceEstimate.currency)}</span>
                </div>
                <div className="border-t pt-2 flex justify-between font-semibold">
                  <span>Total</span>
                  <span className="text-purple-600">
                    {formatPrice(priceEstimate.total, priceEstimate.currency)}
                  </span>
                </div>
              </div>
            )}

            <div className="flex gap-3">
              <Button variant="outline" onClick={() => setStep(2)} className="flex-1">
                Back
              </Button>
              <Button onClick={() => setStep(4)} className="flex-1">
                Review Order
              </Button>
            </div>
          </div>
        )}

        {/* Step 4: Review & Pay */}
        {step === 4 && (
          <div className="space-y-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="font-medium mb-2">Order Summary</h4>
              <p className="text-sm text-gray-600">{book?.title}</p>
              <p className="text-sm text-gray-500">{prepData?.page_count} pages</p>
            </div>
            
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="font-medium mb-2">Shipping To</h4>
              <p className="text-sm text-gray-600">
                {address.firstName} {address.lastName}<br />
                {address.addressLine1}<br />
                {address.addressLine2 && <>{address.addressLine2}<br /></>}
                {address.city}, {address.postCode}<br />
                {COUNTRIES.find(c => c.code === address.countryIsoCode)?.name}
              </p>
            </div>

            {priceEstimate && (
              <div className="bg-purple-50 rounded-lg p-4">
                <div className="flex justify-between font-semibold text-lg">
                  <span>Total</span>
                  <span className="text-purple-600">
                    {formatPrice(priceEstimate.total, priceEstimate.currency)}
                  </span>
                </div>
              </div>
            )}

            <div className="flex items-start gap-2 p-3 bg-yellow-50 rounded-lg text-sm">
              <FiAlertCircle className="text-yellow-600 mt-0.5 flex-shrink-0" />
              <p className="text-yellow-700">
                Payment integration coming soon. This is a preview of the ordering process.
              </p>
            </div>

            <div className="flex gap-3">
              <Button variant="outline" onClick={() => setStep(3)} className="flex-1">
                Back
              </Button>
              <Button 
                onClick={submitOrder} 
                className="flex-1 bg-gradient-to-r from-purple-500 to-pink-500"
                disabled={loading}
              >
                <FiCreditCard className="mr-2" />
                {loading ? 'Processing...' : 'Place Order'}
              </Button>
            </div>
          </div>
        )}

        {/* Step 5: Confirmation */}
        {step === 5 && orderResult && (
          <div className="text-center py-6">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <FiCheck className="w-8 h-8 text-green-500" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Order Placed!</h3>
            <p className="text-gray-600 mb-4">
              Your order #{orderResult.order_reference} has been submitted.
            </p>
            <p className="text-sm text-gray-500">
              You'll receive an email confirmation with tracking details once your book ships.
            </p>
            <Button onClick={onClose} className="mt-6">
              Done
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
