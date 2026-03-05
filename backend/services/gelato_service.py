"""
Gelato Print on Demand Service
Handles API integration with Gelato for ordering printed books

API Documentation: https://dashboard.gelato.com/docs/
"""

import os
import aiohttp
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

# Gelato API Configuration - Using v4 Orders API
GELATO_ORDER_API_URL = "https://order.gelatoapis.com"
GELATO_PRODUCT_API_URL = "https://product.gelatoapis.com"
GELATO_API_KEY = os.environ.get("GELATO_API_KEY")

# Product catalog for Azories books
PRODUCTS = {
    "softcover_8x10": {
        "uid": "photobooks-softcover_pf_210x297-mm-a4_pt_170-gsm-65lb-coated-silk_cl_4-4_ccl_4-4_bt_glued-left_ct_matt-lamination_prt_1-0_cpt_250-gsm-100-lb-cover-coated-silk_ver",
        "name": "Softcover Book (8x10\")",
        "base_price_gbp": 14.99,
        "base_price_usd": 19.99,
        "min_pages": 24,
        "max_pages": 200,
        "description": "Premium softcover photobook with matt lamination"
    },
    "hardcover_8x10": {
        "uid": "photobooks-hardcover_pf_210x297-mm-a4_pt_170-gsm-65lb-coated-silk_cl_4-4_ccl_4-4_bt_glued-left_ct_matt-lamination_prt_1-0_cpt_350-gsm-130-lb-cover-coated-silk_ver",
        "name": "Hardcover Book (8x10\")",
        "base_price_gbp": 19.99,
        "base_price_usd": 24.99,
        "min_pages": 24,
        "max_pages": 200,
        "description": "Premium hardcover photobook with matt lamination"
    }
}

# Default product
DEFAULT_PRODUCT = PRODUCTS["softcover_8x10"]


class GelatoService:
    """Service for interacting with Gelato Print on Demand API"""
    
    def __init__(self):
        self.api_key = GELATO_API_KEY
        self.order_api_url = GELATO_ORDER_API_URL
        self.product_api_url = GELATO_PRODUCT_API_URL
        self.products = PRODUCTS
        self.default_product = DEFAULT_PRODUCT
        
    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers for Gelato API"""
        return {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "AzoriesStoryCreator/1.0"
        }
    
    def is_configured(self) -> bool:
        """Check if Gelato API is properly configured"""
        return bool(self.api_key)
    
    async def get_product_catalog(self) -> Dict[str, Any]:
        """Get available products from Gelato catalog"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.product_api_url}/v3/catalogs",
                    headers=self._get_headers()
                ) as response:
                    if response.status == 200:
                        return {"success": True, "catalogs": await response.json()}
                    else:
                        error = await response.text()
                        logger.error(f"Gelato catalog API error: {error}")
                        return {"success": False, "error": error}
        except Exception as e:
            logger.error(f"Gelato catalog exception: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_shipping_quote(
        self,
        country_code: str,
        postal_code: str,
        pdf_url: str,
        product_type: str = "softcover_8x10",
        quantity: int = 1,
        currency: str = "GBP"
    ) -> Dict[str, Any]:
        """
        Get shipping quote for an order using v3 quote API
        
        Args:
            country_code: ISO 2-letter country code (e.g., 'US', 'GB')
            postal_code: Recipient postal/zip code
            pdf_url: URL to the print-ready PDF
            product_type: Product key from PRODUCTS dict
            quantity: Number of copies
            currency: Currency code (GBP, USD, EUR)
        """
        try:
            product = self.products.get(product_type, self.default_product)
            order_ref = f"quote_{uuid.uuid4().hex[:8]}"
            
            async with aiohttp.ClientSession() as session:
                payload = {
                    "orderReferenceId": order_ref,
                    "customerReferenceId": f"customer_{order_ref}",
                    "currency": currency,
                    "allowMultipleQuotes": False,
                    "recipient": {
                        "country": country_code,
                        "postCode": postal_code
                    },
                    "products": [
                        {
                            "itemReferenceId": f"{order_ref}_item",
                            "productUid": product["uid"],
                            "fileUrl": pdf_url,
                            "quantity": quantity
                        }
                    ]
                }
                
                logger.info(f"Requesting shipping quote to {country_code} for {product_type}")
                
                async with session.post(
                    f"{self.order_api_url}/v3/orders:quote",
                    headers=self._get_headers(),
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        quotes = data.get("quotes", [])
                        
                        # Extract shipping methods from first quote
                        shipping_methods = []
                        if quotes:
                            shipping_methods = quotes[0].get("shipmentMethods", [])
                            
                        return {
                            "success": True,
                            "quotes": shipping_methods,
                            "product_price": product["base_price_gbp"] if currency == "GBP" else product["base_price_usd"],
                            "product_name": product["name"],
                            "fulfillment_country": quotes[0].get("fulfillmentCountry") if quotes else None,
                            "raw_response": data
                        }
                    else:
                        error = await response.text()
                        logger.error(f"Gelato shipping quote error: {error}")
                        return {"success": False, "error": error, "status": response.status}
        except Exception as e:
            logger.error(f"Gelato shipping quote exception: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_order(
        self,
        pdf_url: str,
        recipient: Dict[str, Any],
        order_reference: str,
        product_type: str = "softcover_8x10",
        shipment_method_uid: Optional[str] = None,
        currency: str = "GBP"
    ) -> Dict[str, Any]:
        """
        Create a print order with Gelato v4 API
        
        Args:
            pdf_url: URL to the print-ready PDF (complete book with cover)
            recipient: Shipping address details
            order_reference: Our internal order reference
            product_type: Product key from PRODUCTS dict
            shipment_method_uid: Optional specific shipping method
            currency: Currency code (GBP, USD, EUR)
        """
        try:
            product = self.products.get(product_type, self.default_product)
            
            async with aiohttp.ClientSession() as session:
                payload = {
                    "orderType": "order",
                    "orderReferenceId": order_reference,
                    "customerReferenceId": recipient.get("email", f"customer_{order_reference}"),
                    "currency": currency,
                    "items": [
                        {
                            "itemReferenceId": f"{order_reference}_book",
                            "productUid": product["uid"],
                            "quantity": 1,
                            "files": [
                                {
                                    "type": "default",
                                    "url": pdf_url
                                }
                            ]
                        }
                    ],
                    "shippingAddress": {
                        "firstName": recipient.get("firstName", ""),
                        "lastName": recipient.get("lastName", ""),
                        "addressLine1": recipient.get("addressLine1", ""),
                        "addressLine2": recipient.get("addressLine2", ""),
                        "city": recipient.get("city", ""),
                        "postCode": recipient.get("postCode", ""),
                        "state": recipient.get("state", ""),
                        "country": recipient.get("country", ""),
                        "email": recipient.get("email", ""),
                        "phone": recipient.get("phone", "")
                    }
                }
                
                if shipment_method_uid:
                    payload["shipmentMethodUid"] = shipment_method_uid
                
                logger.info(f"Creating Gelato order: {order_reference}")
                
                async with session.post(
                    f"{self.order_api_url}/v4/orders",
                    headers=self._get_headers(),
                    json=payload
                ) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        logger.info(f"Gelato order created successfully: {data.get('id')}")
                        return {
                            "success": True,
                            "order_id": data.get("id"),
                            "status": data.get("fulfillmentStatus"),
                            "financial_status": data.get("financialStatus"),
                            "data": data
                        }
                    else:
                        error = await response.text()
                        logger.error(f"Gelato order creation error: {error}")
                        return {"success": False, "error": error, "status": response.status}
        except Exception as e:
            logger.error(f"Gelato order creation exception: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get the current status of an order using v4 API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.order_api_url}/v4/orders/{order_id}",
                    headers=self._get_headers()
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "order_id": data.get("id"),
                            "status": data.get("fulfillmentStatus"),
                            "financial_status": data.get("financialStatus"),
                            "shipments": data.get("shipments", []),
                            "created_at": data.get("createdAt"),
                            "updated_at": data.get("updatedAt"),
                            "data": data
                        }
                    elif response.status == 404:
                        return {"success": False, "error": "Order not found", "status": 404}
                    else:
                        error = await response.text()
                        return {"success": False, "error": error, "status": response.status}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel an order using v4 API
        Only possible before order reaches 'printed' or 'shipped' status
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.order_api_url}/v4/orders/{order_id}:cancel",
                    headers=self._get_headers(),
                    json={}
                ) as response:
                    if response.status in [200, 204]:
                        return {"success": True, "message": "Order cancelled successfully"}
                    elif response.status == 409:
                        return {"success": False, "error": "Order cannot be cancelled in current status", "status": 409}
                    elif response.status == 404:
                        return {"success": False, "error": "Order not found", "status": 404}
                    else:
                        error = await response.text()
                        return {"success": False, "error": error, "status": response.status}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def search_orders(
        self,
        order_reference_ids: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Search for orders by reference IDs or other criteria"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "limit": limit,
                    "offset": offset
                }
                if order_reference_ids:
                    payload["orderReferenceIds"] = order_reference_ids
                
                async with session.post(
                    f"{self.order_api_url}/v4/orders:search",
                    headers=self._get_headers(),
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "orders": data.get("orders", []),
                            "total": len(data.get("orders", []))
                        }
                    else:
                        error = await response.text()
                        return {"success": False, "error": error}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def calculate_price(
        self,
        product_type: str = "softcover_8x10",
        shipping_cost: float = 0,
        currency: str = "GBP"
    ) -> Dict[str, Any]:
        """
        Calculate total price for an order
        
        Returns breakdown of costs
        """
        product = self.products.get(product_type, self.default_product)
        base_price = product["base_price_gbp"] if currency == "GBP" else product["base_price_usd"]
        
        subtotal = base_price
        total = subtotal + shipping_cost
        
        return {
            "product_name": product["name"],
            "base_price": base_price,
            "subtotal": subtotal,
            "shipping": shipping_cost,
            "total": round(total, 2),
            "currency": currency
        }
    
    def get_available_products(self) -> List[Dict[str, Any]]:
        """Get list of available products for ordering"""
        return [
            {
                "key": key,
                "name": product["name"],
                "description": product["description"],
                "price_gbp": product["base_price_gbp"],
                "price_usd": product["base_price_usd"]
            }
            for key, product in self.products.items()
        ]


# Singleton instance
gelato_service = GelatoService()
