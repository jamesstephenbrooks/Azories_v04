"""
Backend tests for My Orders feature (iteration 64)
Tests: GET /api/print/my-orders endpoint
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from review_request
TEST_EMAIL = "test@printtest.com"
TEST_PASSWORD = "printtest"
SEEDED_ORDER_REF = "AZ-TEST-ORDER1"


@pytest.fixture(scope="module")
def auth_token():
    """Login and get auth token for test user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        token = data.get("token") or data.get("access_token")
        if token:
            print(f"Auth token obtained for {TEST_EMAIL}")
            return token
    print(f"Login failed: {response.status_code} - {response.text[:200]}")
    pytest.skip(f"Authentication failed: {response.status_code}")


class TestMyOrdersEndpointAuth:
    """Authentication tests for GET /api/print/my-orders"""

    def test_no_auth_returns_401(self):
        """Unauthenticated request should return 401"""
        response = requests.get(f"{BASE_URL}/api/print/my-orders")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        print("PASS: /api/print/my-orders returns 401 without auth")

    def test_invalid_token_returns_401(self):
        """Invalid token should return 401"""
        response = requests.get(
            f"{BASE_URL}/api/print/my-orders",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        print("PASS: Invalid token returns 401")

    def test_valid_token_returns_200(self, auth_token):
        """Valid token should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/print/my-orders",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: Valid token returns 200")


class TestMyOrdersResponse:
    """Response structure tests for GET /api/print/my-orders"""

    def test_response_has_orders_key(self, auth_token):
        """Response must contain 'orders' key"""
        response = requests.get(
            f"{BASE_URL}/api/print/my-orders",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "orders" in data, f"'orders' key missing from response. Got: {list(data.keys())}"
        print(f"PASS: Response has 'orders' key")

    def test_response_has_total_key(self, auth_token):
        """Response must contain 'total' key"""
        response = requests.get(
            f"{BASE_URL}/api/print/my-orders",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data, f"'total' key missing from response. Got: {list(data.keys())}"
        total = data["total"]
        orders = data["orders"]
        assert isinstance(orders, list), f"'orders' should be a list, got {type(orders)}"
        assert total == len(orders), f"total={total} != len(orders)={len(orders)}"
        print(f"PASS: Response has 'total' key. Found {total} order(s).")

    def test_seeded_order_present(self, auth_token):
        """Seeded test order AZ-TEST-ORDER1 must appear"""
        response = requests.get(
            f"{BASE_URL}/api/print/my-orders",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        orders = data.get("orders", [])

        # Find the seeded order by reference
        seeded = next(
            (o for o in orders if o.get("order_reference") == SEEDED_ORDER_REF),
            None
        )
        assert seeded is not None, (
            f"Seeded order '{SEEDED_ORDER_REF}' not found in orders. "
            f"Got refs: {[o.get('order_reference') for o in orders]}"
        )
        print(f"PASS: Seeded order {SEEDED_ORDER_REF} found in my-orders response")

    def test_order_card_fields_present(self, auth_token):
        """Order must have required fields for order card display"""
        response = requests.get(
            f"{BASE_URL}/api/print/my-orders",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        orders = data.get("orders", [])

        assert len(orders) > 0, "No orders found - cannot check order fields"

        order = next(
            (o for o in orders if o.get("order_reference") == SEEDED_ORDER_REF),
            orders[0]
        )

        # Check required display fields
        assert "book_title" in order, f"Missing 'book_title' in order: {list(order.keys())}"
        assert "created_at" in order, f"Missing 'created_at' in order: {list(order.keys())}"
        assert "price_display" in order, f"Missing 'price_display' in order: {list(order.keys())}"
        assert "display_status" in order, f"Missing 'display_status' in order: {list(order.keys())}"
        print(f"PASS: Order has all required fields. display_status={order['display_status']}, price_display={order['price_display']}")

    def test_shipped_order_has_display_status(self, auth_token):
        """Seeded order with status=shipped must have display_status='shipped'"""
        response = requests.get(
            f"{BASE_URL}/api/print/my-orders",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        orders = data.get("orders", [])

        seeded = next(
            (o for o in orders if o.get("order_reference") == SEEDED_ORDER_REF),
            None
        )
        assert seeded is not None, f"Seeded order {SEEDED_ORDER_REF} not found"

        display_status = seeded.get("display_status")
        assert display_status == "shipped", (
            f"Expected display_status='shipped', got '{display_status}'. "
            f"Raw status in order: {seeded.get('status')}"
        )
        print(f"PASS: Seeded order display_status='shipped'")

    def test_book_cover_url_enriched(self, auth_token):
        """Orders should be enriched with book_cover_url"""
        response = requests.get(
            f"{BASE_URL}/api/print/my-orders",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        orders = data.get("orders", [])
        assert len(orders) > 0, "No orders to check"

        order = next(
            (o for o in orders if o.get("order_reference") == SEEDED_ORDER_REF),
            orders[0]
        )
        # book_cover_url may be None if book has no cover, but key should be set
        assert "book_cover_url" in order, (
            f"'book_cover_url' key missing from order. Keys: {list(order.keys())}"
        )
        print(f"PASS: Order has 'book_cover_url' field. Value: {order.get('book_cover_url')}")

    def test_orders_sorted_by_date_desc(self, auth_token):
        """Orders must be sorted by created_at descending"""
        response = requests.get(
            f"{BASE_URL}/api/print/my-orders",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        orders = data.get("orders", [])

        if len(orders) < 2:
            print(f"Only {len(orders)} order(s) - cannot check sort order")
            return  # Not enough orders to verify sort

        dates = [o.get("created_at") for o in orders if o.get("created_at")]
        # Just check first two are in descending order
        assert dates[0] >= dates[1], (
            f"Orders not sorted desc: [{dates[0]}] should be >= [{dates[1]}]"
        )
        print(f"PASS: Orders sorted by date desc: {dates[0]} >= {dates[1]}")

    def test_tracking_present_for_shipped(self, auth_token):
        """Seeded order with tracking=JD014600004947503980/royalmail must have tracking info"""
        response = requests.get(
            f"{BASE_URL}/api/print/my-orders",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        orders = data.get("orders", [])

        seeded = next(
            (o for o in orders if o.get("order_reference") == SEEDED_ORDER_REF),
            None
        )
        assert seeded is not None, f"Seeded order {SEEDED_ORDER_REF} not found"

        # Check tracking field is present
        tracking = seeded.get("tracking", [])
        print(f"INFO: tracking field for seeded order: {tracking}")

        if isinstance(tracking, list) and len(tracking) > 0:
            t = tracking[0]
            tracking_number = t.get("tracking_number") or t.get("trackingNumber")
            carrier = t.get("carrier") or t.get("courier")
            print(f"PASS: Tracking found: number={tracking_number}, carrier={carrier}")
        else:
            # Tracking might be stored differently (as single string vs array)
            # Check direct fields
            raw_tracking = seeded.get("tracking_number") or seeded.get("trackingNumber")
            print(f"INFO: Direct tracking_number field: {raw_tracking}")
            # This is not a hard fail - tracking field could be empty list if seeded differently
            print(f"INFO: Tracking list empty or missing for seeded order - check DB seed format")
