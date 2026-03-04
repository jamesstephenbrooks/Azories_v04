"""
Gelato Print on Demand Service
Handles API integration with Gelato for ordering printed books
"""

import os
import aiohttp
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Gelato API Configuration
GELATO_API_URL = "https://api.gelato.com/v3"
GELATO_API_KEY = os.environ.get("GELATO_API_KEY")
GELATO_PRODUCT_UID = os.environ.get("GELATO_PRODUCT_UID")

# Default product: 8x8" Softcover Photobook
DEFAULT_PRODUCT = {
    "uid": GELATO_PRODUCT_UID or "photobooks-softcover_pf_200x200-mm-8x8-inch_pt_170-gsm-65lb-coated-silk_cl_4-4_ccl_4-4_bt_glued-left_ct_matt-lamination_prt_1-0_cpt_250-gsm-100-lb-cover-coated-silk_ver",
    "name": "8x8\" Softcover Photobook",
    "base_price_gbp": 14.99,
    "base_price_usd": 19.99,
    "min_pages": 24,
    "max_pages": 200,
    "description": "Premium softcover photobook with matt lamination"
}


class GelatoService:
    """Service for interacting with Gelato Print on Demand API"""
    
    def __init__(self):
        self.api_key = GELATO_API_KEY
        self.base_url = GELATO_API_URL
        self.product = DEFAULT_PRODUCT
        
    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers for Gelato API"""
        return {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def get_shipping_countries(self) -> Dict[str, Any]:
        """Get list of countries Gelato ships to"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/countries",
                headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.text()
                    logger.error(f"Gelato countries API error: {error}")
                    return {"error": error, "status": response.status}
    
    async def get_shipping_quote(
        self,
        country_code: str,
        page_count: int,
        quantity: int = 1
    ) -> Dict[str, Any]:
        """
        Get shipping quote for an order
        
        Args:
            country_code: ISO 2-letter country code (e.g., 'US', 'GB')
            page_count: Number of pages in the book
            quantity: Number of copies
        """
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "productUid": self.product["uid"],
                    "quantity": quantity,
                    "pageCount": max(page_count, self.product["min_pages"]),
                    "recipient": {
                        "countryIsoCode": country_code
                    }
                }
                
                async with session.post(
                    f"{self.base_url}/shipment/quotes",
                    headers=self._get_headers(),
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "quotes": data.get("quotes", []),
                            "product_price": self.product["base_price_gbp"] if country_code == "GB" else self.product["base_price_usd"]
                        }
                    else:
                        error = await response.text()
                        logger.error(f"Gelato shipping quote error: {error}")
                        return {"success": False, "error": error}
        except Exception as e:
            logger.error(f"Gelato shipping quote exception: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_order(
        self,
        pdf_url: str,
        cover_url: str,
        recipient: Dict[str, Any],
        page_count: int,
        order_reference: str,
        shipping_method: str = "normal"
    ) -> Dict[str, Any]:
        """
        Create a print order with Gelato
        
        Args:
            pdf_url: URL to the print-ready PDF (interior pages)
            cover_url: URL to the cover PDF
            recipient: Shipping address details
            page_count: Number of interior pages
            order_reference: Our internal order reference
            shipping_method: 'normal', 'express', or 'overnight'
        """
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "orderType": "order",
                    "orderReferenceId": order_reference,
                    "customerReferenceId": recipient.get("email", ""),
                    "currency": "GBP" if recipient.get("countryIsoCode") == "GB" else "USD",
                    "items": [
                        {
                            "itemReferenceId": f"{order_reference}-book",
                            "productUid": self.product["uid"],
                            "pageCount": max(page_count, self.product["min_pages"]),
                            "quantity": 1,
                            "files": [
                                {
                                    "type": "inside",
                                    "url": pdf_url
                                },
                                {
                                    "type": "cover",
                                    "url": cover_url
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
                        "country": recipient.get("countryIsoCode", ""),
                        "email": recipient.get("email", ""),
                        "phone": recipient.get("phone", "")
                    },
                    "shipmentMethodUid": self._get_shipment_method_uid(shipping_method)
                }
                
                async with session.post(
                    f"{self.base_url}/orders",
                    headers=self._get_headers(),
                    json=payload
                ) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        return {
                            "success": True,
                            "order_id": data.get("id"),
                            "status": data.get("status"),
                            "data": data
                        }
                    else:
                        error = await response.text()
                        logger.error(f"Gelato order creation error: {error}")
                        return {"success": False, "error": error}
        except Exception as e:
            logger.error(f"Gelato order creation exception: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get the current status of an order"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/orders/{order_id}",
                    headers=self._get_headers()
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "status": data.get("status"),
                            "fulfillment_status": data.get("fulfillmentStatus"),
                            "tracking": data.get("shipments", []),
                            "data": data
                        }
                    else:
                        error = await response.text()
                        return {"success": False, "error": error}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order (only possible before production starts)"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(
                    f"{self.base_url}/orders/{order_id}",
                    headers=self._get_headers()
                ) as response:
                    if response.status in [200, 204]:
                        return {"success": True, "message": "Order cancelled"}
                    else:
                        error = await response.text()
                        return {"success": False, "error": error}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_shipment_method_uid(self, method: str) -> str:
        """Map shipping method name to Gelato UID"""
        methods = {
            "normal": "normal",
            "express": "express",
            "overnight": "overnight"
        }
        return methods.get(method, "normal")
    
    def calculate_price(
        self,
        page_count: int,
        shipping_cost: float,
        currency: str = "GBP"
    ) -> Dict[str, float]:
        """
        Calculate total price for an order
        
        Returns breakdown of costs
        """
        base_price = self.product["base_price_gbp"] if currency == "GBP" else self.product["base_price_usd"]
        
        # Additional pages cost (if over minimum)
        extra_pages = max(0, page_count - self.product["min_pages"])
        extra_page_cost = extra_pages * 0.10  # £0.10 per extra page
        
        subtotal = base_price + extra_page_cost
        total = subtotal + shipping_cost
        
        return {
            "base_price": base_price,
            "extra_pages": extra_pages,
            "extra_page_cost": extra_page_cost,
            "subtotal": subtotal,
            "shipping": shipping_cost,
            "total": total,
            "currency": currency
        }


# Singleton instance
gelato_service = GelatoService()
