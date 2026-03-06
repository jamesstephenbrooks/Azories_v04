"""
Test Print Order APIs with Stripe Checkout Integration
Tests for iteration 51 - Print on Demand ordering flow

Covers:
- Price estimate API with different countries and shipping methods
- Product info API
- Stripe checkout session creation
- Order preparation flow
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://gelato-order-flow.preview.emergentagent.com')

# Test book ID for testing
TEST_BOOK_ID = "fb341971-71be-4c8a-b764-a7cac7fb9a71"


class TestPrintProductInfo:
    """Product information endpoint tests"""
    
    def test_get_product_info_returns_products(self):
        """Test that product-info returns available products"""
        response = requests.get(f"{BASE_URL}/api/print/product-info")
        assert response.status_code == 200
        
        data = response.json()
        assert "products" in data
        assert len(data["products"]) >= 2  # At least softcover and hardcover
        
        # Verify product structure
        for product in data["products"]:
            assert "id" in product
            assert "name" in product
            assert "description" in product
            assert "price" in product
            assert "GBP" in product["price"]
            assert "USD" in product["price"]
    
    def test_product_info_pricing_correct(self):
        """Test that product pricing is correct"""
        response = requests.get(f"{BASE_URL}/api/print/product-info")
        assert response.status_code == 200
        
        data = response.json()
        products = {p["id"]: p for p in data["products"]}
        
        # Verify softcover pricing
        assert products["softcover_8x10"]["price"]["GBP"] == 14.99
        assert products["softcover_8x10"]["price"]["USD"] == 19.99
        
        # Verify hardcover pricing
        assert products["hardcover_8x10"]["price"]["GBP"] == 19.99
        assert products["hardcover_8x10"]["price"]["USD"] == 24.99
    
    def test_product_info_includes_shipping_options(self):
        """Test that shipping options are included"""
        response = requests.get(f"{BASE_URL}/api/print/product-info")
        assert response.status_code == 200
        
        data = response.json()
        assert "shipping_options" in data
        assert len(data["shipping_options"]) >= 2  # At least normal and express
        
        methods = [opt["method"] for opt in data["shipping_options"]]
        assert "normal" in methods
        assert "express" in methods


class TestPriceEstimate:
    """Price estimate endpoint tests with different regions and shipping methods"""
    
    def test_price_estimate_gb_normal(self):
        """Test price estimate for GB with standard shipping"""
        response = requests.get(
            f"{BASE_URL}/api/print/price-estimate",
            params={"page_count": 24, "country_code": "GB", "shipping_method": "normal"}
        )
        assert response.status_code == 200
        
        data = response.json()
        estimate = data["estimate"]
        
        # Verify GBP pricing for UK
        assert estimate["currency"] == "GBP"
        assert estimate["base_price"] == 14.99
        assert estimate["shipping"] == 4.99  # UK standard shipping
        assert estimate["total"] == 14.99 + 4.99  # 19.98
        assert estimate["extra_pages"] == 0
        assert estimate["extra_page_cost"] == 0.0
    
    def test_price_estimate_us_express(self):
        """Test price estimate for US with express shipping"""
        response = requests.get(
            f"{BASE_URL}/api/print/price-estimate",
            params={"page_count": 24, "country_code": "US", "shipping_method": "express"}
        )
        assert response.status_code == 200
        
        data = response.json()
        estimate = data["estimate"]
        
        # Verify USD pricing for US
        assert estimate["currency"] == "USD"
        assert estimate["base_price"] == 19.99
        assert estimate["shipping"] == 12.99  # US express shipping
    
    def test_price_estimate_eu_country(self):
        """Test price estimate for EU country (Germany)"""
        response = requests.get(
            f"{BASE_URL}/api/print/price-estimate",
            params={"page_count": 24, "country_code": "DE", "shipping_method": "normal"}
        )
        assert response.status_code == 200
        
        data = response.json()
        estimate = data["estimate"]
        
        # EU countries use USD and EU shipping rates
        assert estimate["currency"] == "USD"
        assert estimate["shipping"] == 6.99  # EU standard shipping
    
    def test_price_estimate_extra_pages(self):
        """Test price estimate with extra pages (over 24)"""
        response = requests.get(
            f"{BASE_URL}/api/print/price-estimate",
            params={"page_count": 40, "country_code": "GB", "shipping_method": "normal"}
        )
        assert response.status_code == 200
        
        data = response.json()
        estimate = data["estimate"]
        
        # 40 pages = 24 base + 16 extra pages
        assert estimate["extra_pages"] == 16
        assert estimate["extra_page_cost"] == 1.60  # £0.10 per extra page
        # Use round() for floating point comparison
        assert round(estimate["total"], 2) == round(14.99 + 4.99 + 1.60, 2)  # 21.58
    
    def test_price_estimate_shipping_options_included(self):
        """Test that shipping options are included in response"""
        response = requests.get(
            f"{BASE_URL}/api/print/price-estimate",
            params={"page_count": 24, "country_code": "GB", "shipping_method": "normal"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "shipping_options" in data
        
        options = data["shipping_options"]
        assert len(options) >= 3  # normal, express, overnight
        
        # Verify option structure
        for opt in options:
            assert "shipmentMethodUid" in opt
            assert "name" in opt
            assert "price" in opt
            assert "minTransitDays" in opt
            assert "maxTransitDays" in opt


class TestStripeCheckout:
    """Stripe checkout session creation tests"""
    
    def test_create_checkout_session_success(self):
        """Test successful checkout session creation"""
        response = requests.post(
            f"{BASE_URL}/api/print/checkout/create-session",
            json={
                "book_id": TEST_BOOK_ID,
                "product_type": "softcover_8x10",
                "shipping_country": "GB",
                "origin_url": "https://gelato-order-flow.preview.emergentagent.com"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify checkout URL and session ID returned
        assert "checkout_url" in data
        assert "session_id" in data
        assert "order_reference" in data
        
        # Verify checkout URL is a valid Stripe URL
        assert data["checkout_url"].startswith("https://checkout.stripe.com")
        
        # Verify session ID format
        assert data["session_id"].startswith("cs_")
        
        # Verify order reference format (AZ-YYYYMMDD-XXXXXXXX)
        assert data["order_reference"].startswith("AZ-")
    
    def test_create_checkout_session_us_country(self):
        """Test checkout session creation for US (USD currency)"""
        response = requests.post(
            f"{BASE_URL}/api/print/checkout/create-session",
            json={
                "book_id": TEST_BOOK_ID,
                "product_type": "softcover_8x10",
                "shipping_country": "US",
                "origin_url": "https://gelato-order-flow.preview.emergentagent.com"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "checkout_url" in data
        assert data["checkout_url"].startswith("https://checkout.stripe.com")
    
    def test_create_checkout_session_hardcover(self):
        """Test checkout session creation for hardcover product"""
        response = requests.post(
            f"{BASE_URL}/api/print/checkout/create-session",
            json={
                "book_id": TEST_BOOK_ID,
                "product_type": "hardcover_8x10",
                "shipping_country": "GB",
                "origin_url": "https://gelato-order-flow.preview.emergentagent.com"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "checkout_url" in data
    
    def test_create_checkout_session_invalid_product(self):
        """Test checkout session with invalid product type"""
        response = requests.post(
            f"{BASE_URL}/api/print/checkout/create-session",
            json={
                "book_id": TEST_BOOK_ID,
                "product_type": "invalid_product",
                "shipping_country": "GB",
                "origin_url": "https://gelato-order-flow.preview.emergentagent.com"
            }
        )
        assert response.status_code == 400
        
        data = response.json()
        assert "Invalid product type" in data.get("detail", "")
    
    def test_create_checkout_session_invalid_book(self):
        """Test checkout session with non-existent book"""
        response = requests.post(
            f"{BASE_URL}/api/print/checkout/create-session",
            json={
                "book_id": "non-existent-book-id-12345",
                "product_type": "softcover_8x10",
                "shipping_country": "GB",
                "origin_url": "https://gelato-order-flow.preview.emergentagent.com"
            }
        )
        assert response.status_code == 404


class TestPrintOrderPrepare:
    """Test book preparation for printing"""
    
    def test_prepare_book_requires_auth(self):
        """Test that prepare endpoint works (may require auth)"""
        # Note: This endpoint may require authentication
        response = requests.post(f"{BASE_URL}/api/print/prepare/{TEST_BOOK_ID}")
        # Should not return 500 - either 200 (success) or 401/403 (auth required)
        assert response.status_code in [200, 401, 403, 404]


class TestCheckoutStatus:
    """Test checkout status endpoint"""
    
    def test_checkout_status_invalid_session(self):
        """Test checkout status with invalid session ID"""
        response = requests.get(f"{BASE_URL}/api/print/checkout/status/invalid_session_id")
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
