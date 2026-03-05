"""
Print Orders API Routes
Handles print-on-demand orders via Gelato
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import logging

from services.gelato_service import gelato_service
from services.print_pdf_generator import pdf_generator, generate_test_pdf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/print", tags=["Print Orders"])


# Request/Response Models
class ShippingAddress(BaseModel):
    firstName: str
    lastName: str
    addressLine1: str
    addressLine2: Optional[str] = ""
    city: str
    postCode: str
    state: Optional[str] = ""
    countryIsoCode: str = Field(..., min_length=2, max_length=2)
    email: str
    phone: Optional[str] = ""


class ShippingQuoteRequest(BaseModel):
    country_code: str = Field(..., min_length=2, max_length=2)
    page_count: int = Field(..., ge=1)
    quantity: int = Field(default=1, ge=1, le=100)


class CreateOrderRequest(BaseModel):
    book_id: str
    shipping_address: ShippingAddress
    shipping_method: str = "normal"  # normal, express, overnight
    payment_intent_id: Optional[str] = None  # Stripe payment intent


class OrderStatusResponse(BaseModel):
    order_id: str
    gelato_order_id: Optional[str]
    status: str
    created_at: datetime
    book_title: str
    shipping_address: Dict[str, Any]
    tracking: Optional[List[Dict[str, Any]]] = []
    total_price: float
    currency: str


# Database helper (uses the main db from server.py)
def get_db():
    from server import db
    return db


@router.get("/product-info")
async def get_product_info():
    """Get information about the print product"""
    return {
        "name": "8x8\" Softcover Photobook",
        "description": "Premium softcover photobook with matt lamination, perfect bound",
        "dimensions": "8 x 8 inches (200 x 200 mm)",
        "paper": "170gsm coated silk interior, 250gsm cover",
        "binding": "Perfect bound (glued)",
        "finish": "Matt lamination cover",
        "min_pages": 24,
        "max_pages": 200,
        "base_price": {
            "GBP": 14.99,
            "USD": 19.99
        },
        "production_time": "3-5 business days",
        "shipping_options": [
            {"method": "normal", "name": "Standard", "days": "5-10 business days"},
            {"method": "express", "name": "Express", "days": "2-4 business days"},
            {"method": "overnight", "name": "Next Day", "days": "1-2 business days"}
        ],
        "coming_soon": True  # Flag to show "Coming Soon" in UI
    }


@router.post("/shipping-quote")
async def get_shipping_quote(request: ShippingQuoteRequest):
    """Get shipping quote for a specific country"""
    quote = await gelato_service.get_shipping_quote(
        country_code=request.country_code,
        page_count=request.page_count,
        quantity=request.quantity
    )
    
    if not quote.get("success"):
        raise HTTPException(status_code=400, detail=quote.get("error", "Failed to get quote"))
    
    return quote


@router.get("/countries")
async def get_shipping_countries():
    """Get list of countries Gelato ships to"""
    result = await gelato_service.get_shipping_countries()
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/prepare/{book_id}")
async def prepare_print_order(
    book_id: str,
    current_user: dict = None  # Will add auth dependency
):
    """
    Prepare a book for printing - generates print-ready PDF
    Returns the page count and preview URL
    """
    db = get_db()
    
    # Get the book
    book = await db.books.find_one({"id": book_id})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Check if print PDF already exists and is recent
    existing_print = await db.print_orders.find_one({
        "book_id": book_id,
        "status": "prepared",
        "pdf_url": {"$exists": True}
    })
    
    if existing_print:
        return {
            "prepared": True,
            "page_count": existing_print.get("page_count"),
            "pdf_url": existing_print.get("pdf_url"),
            "cover_url": existing_print.get("cover_url"),
            "preview_url": existing_print.get("preview_url")
        }
    
    # Generate print-ready PDF
    try:
        # Get book pages
        pages = await db.pages.find({"book_id": book_id}, {"_id": 0}).sort("sequence", 1).to_list(100)
        
        result = await pdf_generator.generate_print_pdf(
            book=book,
            pages=pages
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to generate print PDF")
        
        # Store the prepared print info
        prep_id = str(uuid.uuid4())
        await db.print_preparations.insert_one({
            "id": prep_id,
            "book_id": book_id,
            "user_id": book.get("user_id"),
            "page_count": result.get("page_count"),
            "pdf_url": result.get("pdf_url"),
            "cover_url": result.get("cover_url"),
            "preview_url": result.get("preview_url"),
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow()  # Add expiry logic
        })
        
        return {
            "prepared": True,
            "preparation_id": prep_id,
            "page_count": result.get("page_count"),
            "pdf_url": result.get("pdf_url"),
            "cover_url": result.get("cover_url"),
            "preview_url": result.get("preview_url")
        }
        
    except Exception as e:
        logger.error(f"Error preparing print order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-order")
async def create_print_order(
    request: CreateOrderRequest,
    current_user: dict = None  # Will add auth dependency
):
    """
    Create a print order with Gelato
    Requires payment to be completed first
    """
    db = get_db()
    
    # Get the book
    book = await db.books.find_one({"id": request.book_id})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Get the prepared print data
    prep = await db.print_preparations.find_one({
        "book_id": request.book_id,
        "pdf_url": {"$exists": True}
    })
    
    if not prep:
        raise HTTPException(
            status_code=400, 
            detail="Book not prepared for printing. Call /prepare first."
        )
    
    # Generate order reference
    order_ref = f"AZ-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    
    # Create order with Gelato
    result = await gelato_service.create_order(
        pdf_url=prep["pdf_url"],
        cover_url=prep["cover_url"],
        recipient=request.shipping_address.dict(),
        page_count=prep["page_count"],
        order_reference=order_ref,
        shipping_method=request.shipping_method
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to create order"))
    
    # Store order in database
    order_id = str(uuid.uuid4())
    order_data = {
        "id": order_id,
        "order_reference": order_ref,
        "gelato_order_id": result.get("order_id"),
        "book_id": request.book_id,
        "book_title": book.get("title", "Untitled"),
        "user_id": book.get("user_id"),
        "status": "submitted",
        "gelato_status": result.get("status"),
        "shipping_address": request.shipping_address.dict(),
        "shipping_method": request.shipping_method,
        "payment_intent_id": request.payment_intent_id,
        "page_count": prep["page_count"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    await db.print_orders.insert_one(order_data)
    
    return {
        "success": True,
        "order_id": order_id,
        "order_reference": order_ref,
        "gelato_order_id": result.get("order_id"),
        "status": "submitted",
        "message": "Your print order has been submitted!"
    }


@router.get("/orders")
async def get_user_orders(
    current_user: dict = None  # Will add auth dependency
):
    """Get all print orders for the current user"""
    db = get_db()
    
    # For now, get all orders (will add user filtering with auth)
    orders = await db.print_orders.find().sort("created_at", -1).to_list(100)
    
    # Convert ObjectId to string
    for order in orders:
        order.pop("_id", None)
    
    return {"orders": orders}


@router.get("/orders/{order_id}")
async def get_order_details(order_id: str):
    """Get details of a specific order"""
    db = get_db()
    
    order = await db.print_orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get latest status from Gelato if we have a gelato_order_id
    if order.get("gelato_order_id"):
        gelato_status = await gelato_service.get_order_status(order["gelato_order_id"])
        if gelato_status.get("success"):
            order["gelato_status"] = gelato_status.get("status")
            order["fulfillment_status"] = gelato_status.get("fulfillment_status")
            order["tracking"] = gelato_status.get("tracking", [])
            
            # Update in database
            await db.print_orders.update_one(
                {"id": order_id},
                {"$set": {
                    "gelato_status": gelato_status.get("status"),
                    "fulfillment_status": gelato_status.get("fulfillment_status"),
                    "tracking": gelato_status.get("tracking", []),
                    "updated_at": datetime.utcnow()
                }}
            )
    
    order.pop("_id", None)
    return order


@router.post("/orders/{order_id}/cancel")
async def cancel_order(order_id: str):
    """Cancel an order (only possible before production starts)"""
    db = get_db()
    
    order = await db.print_orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if not order.get("gelato_order_id"):
        raise HTTPException(status_code=400, detail="No Gelato order to cancel")
    
    # Try to cancel with Gelato
    result = await gelato_service.cancel_order(order["gelato_order_id"])
    
    if result.get("success"):
        await db.print_orders.update_one(
            {"id": order_id},
            {"$set": {
                "status": "cancelled",
                "updated_at": datetime.utcnow()
            }}
        )
        return {"success": True, "message": "Order cancelled"}
    else:
        raise HTTPException(
            status_code=400, 
            detail=result.get("error", "Cannot cancel order - may already be in production")
        )


@router.get("/price-estimate")
async def get_price_estimate(
    page_count: int,
    country_code: str = "GB",
    shipping_method: str = "normal"
):
    """Get a price estimate for printing a book"""
    # Get shipping quote
    quote_result = await gelato_service.get_shipping_quote(
        country_code=country_code,
        page_count=page_count,
        quantity=1
    )
    
    shipping_cost = 0
    if quote_result.get("success") and quote_result.get("quotes"):
        # Find the matching shipping method
        for q in quote_result["quotes"]:
            if q.get("shipmentMethodUid") == shipping_method:
                shipping_cost = q.get("price", 0)
                break
        if shipping_cost == 0 and quote_result["quotes"]:
            shipping_cost = quote_result["quotes"][0].get("price", 0)
    
    currency = "GBP" if country_code == "GB" else "USD"
    price = gelato_service.calculate_price(page_count, shipping_cost, currency)
    
    return {
        "estimate": price,
        "shipping_options": quote_result.get("quotes", [])
    }
