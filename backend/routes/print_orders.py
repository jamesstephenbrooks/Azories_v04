"""
Print Orders API Routes
Handles print-on-demand orders via Gelato with Stripe payments
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import logging
import os
from dotenv import load_dotenv

from services.gelato_service import gelato_service
from services.print_pdf_generator import pdf_generator, generate_test_pdf

load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/print", tags=["Print Orders"])

# Stripe integration
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY")

# Fixed product pricing (server-side only - never trust frontend prices)
PRINT_PRODUCTS = {
    "softcover_8x10": {
        "name": "Softcover Book",
        "price_gbp": 14.99,
        "price_usd": 19.99,
        "description": "Premium softcover photobook"
    },
    "hardcover_8x10": {
        "name": "Hardcover Book", 
        "price_gbp": 19.99,
        "price_usd": 24.99,
        "description": "Premium hardcover photobook"
    }
}


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
    """Get information about print products"""
    return {
        "products": [
            {
                "id": "softcover_8x10",
                "name": "Softcover Book (8x10\")",
                "description": "Premium softcover photobook with matt lamination, perfect bound",
                "dimensions": "8 x 10 inches (203 x 254 mm)",
                "paper": "170gsm coated silk interior, 250gsm cover",
                "binding": "Perfect bound (glued)",
                "finish": "Matt lamination cover",
                "price": {"GBP": 14.99, "USD": 19.99}
            },
            {
                "id": "hardcover_8x10",
                "name": "Hardcover Book (8x10\")",
                "description": "Premium hardcover photobook with matt lamination",
                "dimensions": "8 x 10 inches (203 x 254 mm)",
                "paper": "170gsm coated silk interior, 350gsm cover",
                "binding": "Case bound",
                "finish": "Matt lamination cover",
                "price": {"GBP": 19.99, "USD": 24.99}
            }
        ],
        "min_pages": 24,
        "max_pages": 200,
        "production_time": "3-5 business days",
        "shipping_options": [
            {"method": "normal", "name": "Standard", "days": "5-10 business days"},
            {"method": "express", "name": "Express", "days": "2-4 business days"}
        ],
        "gelato_configured": gelato_service.is_configured(),
        "coming_soon": not gelato_service.is_configured()  # Show coming soon if not configured
    }


@router.get("/generate-test-pdf/{book_id}")
async def generate_test_pdf_endpoint(book_id: str):
    """
    Generate a test PDF for a specific book.
    Returns the PDF file for download and review.
    """
    from fastapi.responses import FileResponse
    import os
    
    db = get_db()
    
    try:
        result = await generate_test_pdf(book_id, db)
        
        if not os.path.exists(result["path"]):
            raise HTTPException(status_code=500, detail="PDF generation failed - file not created")
        
        return FileResponse(
            path=result["path"],
            filename=f"azories_print_test_{book_id[:8]}.pdf",
            media_type="application/pdf",
            headers={
                "X-PDF-Pages": str(result["total_pdf_pages"]),
                "X-PDF-Size-MB": str(result["size_mb"]),
                "X-Book-Title": result["book_title"] or "Unknown"
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")


@router.get("/test-pdf-info/{book_id}")
async def get_test_pdf_info(book_id: str):
    """
    Get info about what the test PDF will contain without generating it.
    """
    db = get_db()
    
    # Fetch book
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Get pages count - first check book document, then separate collection
    pages = book.get('pages', [])
    if not pages:
        pages_count = await db.pages.count_documents({"book_id": book_id})
    else:
        pages_count = len(pages)
    
    # Calculate total pages in PDF
    bonus_pages = 7  # Welcome, Dedication, The End, Thank You, Certificate, About, Meet Azora
    cover_pages = 2  # Front + Back
    total_pages = pages_count + bonus_pages + cover_pages
    
    return {
        "book_id": book_id,
        "book_title": book.get("title"),
        "story_pages": pages_count,
        "bonus_pages": bonus_pages,
        "cover_pages": cover_pages,
        "total_pdf_pages": total_pages,
        "page_size": "8 x 8 inches (2400 x 2400 pixels at 300 DPI)",
        "format": "PDF",
        "estimated_file_size_mb": round(total_pages * 0.8, 1),  # Rough estimate
        "download_url": f"/api/print/generate-test-pdf/{book_id}"
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
        # Get book pages - check both embedded and collection
        pages = book.get('pages', [])
        if not pages:
            pages = await db.pages.find({"book_id": book_id}, {"_id": 0}).sort("page_number", 1).to_list(100)
        
        # Generate PDF
        output_path = await pdf_generator.generate_print_pdf(
            book=book,
            pages=pages
        )
        
        if not output_path:
            raise HTTPException(status_code=500, detail="Failed to generate print PDF")
        
        # Upload PDF to Cloudinary for storage
        try:
            import cloudinary
            import cloudinary.uploader
            import os as os_module
            
            # Check file size - use chunked upload for large files
            file_size = os_module.path.getsize(output_path)
            
            if file_size > 10 * 1024 * 1024:  # > 10MB
                # Use upload_large for chunked upload
                upload_result = cloudinary.uploader.upload_large(
                    output_path,
                    resource_type="raw",
                    folder="azories/print_pdfs",
                    public_id=f"print_{book_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    chunk_size=6000000  # 6MB chunks
                )
            else:
                # Standard upload for smaller files
                upload_result = cloudinary.uploader.upload(
                    output_path,
                    resource_type="raw",
                    folder="azories/print_pdfs",
                    public_id=f"print_{book_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                )
            pdf_url = upload_result.get("secure_url")
        except Exception as upload_error:
            logger.warning(f"Could not upload PDF to Cloudinary: {upload_error}")
            # Use local path as fallback
            pdf_url = output_path
        
        # Count pages in the PDF
        page_count = 24  # Default minimum
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(output_path)
            page_count = len(reader.pages)
        except:
            pass
        
        # Store the prepared print info
        prep_id = str(uuid.uuid4())
        await db.print_preparations.insert_one({
            "id": prep_id,
            "book_id": book_id,
            "user_id": book.get("user_id") or book.get("author_id"),
            "page_count": page_count,
            "pdf_url": pdf_url,
            "cover_url": book.get("cover_image") or book.get("cover_image_url"),
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow()  # Add expiry logic
        })
        
        return {
            "prepared": True,
            "preparation_id": prep_id,
            "page_count": page_count,
            "pdf_url": pdf_url,
            "cover_url": book.get("cover_image") or book.get("cover_image_url")
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
    """Get a price estimate for printing a book (without needing a PDF)"""
    
    # Default shipping costs by region and method (approximate)
    shipping_costs = {
        "GB": {"normal": 4.99, "express": 8.99, "overnight": 14.99},
        "US": {"normal": 6.99, "express": 12.99, "overnight": 24.99},
        "CA": {"normal": 8.99, "express": 14.99, "overnight": 29.99},
        "AU": {"normal": 12.99, "express": 19.99, "overnight": 39.99},
        "EU": {"normal": 6.99, "express": 11.99, "overnight": 19.99},  # Default for EU countries
    }
    
    # EU countries list
    eu_countries = ["DE", "FR", "ES", "IT", "NL", "BE", "AT", "IE", "SE", "NO", "DK", "CH"]
    
    # Determine which region pricing to use
    if country_code in shipping_costs:
        region = country_code
    elif country_code in eu_countries:
        region = "EU"
    else:
        region = "US"  # Default to US pricing for other countries
    
    # Get shipping cost
    shipping_cost = shipping_costs[region].get(shipping_method, shipping_costs[region]["normal"])
    
    # Determine currency
    currency = "GBP" if country_code == "GB" else "USD"
    
    # Calculate price using the service
    price = gelato_service.calculate_price(
        product_type="softcover_8x10",
        shipping_cost=shipping_cost,
        currency=currency
    )
    
    # Extra pages are FREE - no additional cost
    extra_pages = max(0, page_count - 24)
    price["extra_pages"] = extra_pages
    price["extra_page_cost"] = 0  # Free
    # Total stays the same - no extra charge
    
    # Build shipping options
    shipping_options = [
        {
            "shipmentMethodUid": "normal",
            "name": "Standard Shipping",
            "price": shipping_costs[region]["normal"],
            "minTransitDays": 5,
            "maxTransitDays": 10
        },
        {
            "shipmentMethodUid": "express",
            "name": "Express Shipping",
            "price": shipping_costs[region]["express"],
            "minTransitDays": 2,
            "maxTransitDays": 4
        },
        {
            "shipmentMethodUid": "overnight",
            "name": "Next Day Delivery",
            "price": shipping_costs[region]["overnight"],
            "minTransitDays": 1,
            "maxTransitDays": 2
        }
    ]
    
    return {
        "estimate": price,
        "shipping_options": shipping_options
    }


# ==================== STRIPE PAYMENT ENDPOINTS ====================

class CheckoutRequest(BaseModel):
    book_id: str
    product_type: str = "softcover_8x10"  # softcover_8x10 or hardcover_8x10
    shipping_country: str = "GB"
    shipping_postal_code: str = ""
    origin_url: str  # Frontend origin for success/cancel URLs


class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str
    order_reference: str


@router.post("/checkout/create-session")
async def create_checkout_session(request: CheckoutRequest, http_request: Request):
    """
    Create a Stripe checkout session for a print order.
    Price is determined server-side based on product_type - never from frontend.
    """
    from emergentintegrations.payments.stripe.checkout import (
        StripeCheckout, 
        CheckoutSessionRequest, 
        CheckoutSessionResponse
    )
    
    db = get_db()
    
    # Validate product type
    if request.product_type not in PRINT_PRODUCTS:
        raise HTTPException(status_code=400, detail="Invalid product type")
    
    # Get book info
    book = await db.books.find_one({"id": request.book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Get price from server-side config (NEVER from frontend)
    product = PRINT_PRODUCTS[request.product_type]
    currency = "gbp" if request.shipping_country == "GB" else "usd"
    base_price = product["price_gbp"] if currency == "gbp" else product["price_usd"]
    
    # TODO: Add shipping cost from Gelato quote once fully integrated
    # For now, estimate shipping
    estimated_shipping = 5.99 if currency == "gbp" else 7.99
    total_amount = float(base_price) + float(estimated_shipping)
    
    # Generate order reference
    order_reference = f"AZ-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    
    # Build success/cancel URLs from frontend origin
    success_url = f"{request.origin_url}/print-success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{request.origin_url}/book/{request.book_id}"
    
    # Setup Stripe checkout
    webhook_url = f"{str(http_request.base_url)}api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    # Create checkout session
    checkout_request = CheckoutSessionRequest(
        amount=total_amount,
        currency=currency,
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "order_reference": order_reference,
            "book_id": request.book_id,
            "book_title": book.get("title", "Untitled"),
            "product_type": request.product_type,
            "shipping_country": request.shipping_country,
            "type": "print_order"
        }
    )
    
    try:
        session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(checkout_request)
        
        # Create payment transaction record (MANDATORY before redirect)
        transaction_id = str(uuid.uuid4())
        await db.payment_transactions.insert_one({
            "id": transaction_id,
            "session_id": session.session_id,
            "order_reference": order_reference,
            "book_id": request.book_id,
            "book_title": book.get("title"),
            "user_id": book.get("user_id"),
            "product_type": request.product_type,
            "amount": total_amount,
            "currency": currency.upper(),
            "payment_status": "initiated",
            "shipping_country": request.shipping_country,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        logger.info(f"Created checkout session {session.session_id} for order {order_reference}")
        
        return {
            "checkout_url": session.url,
            "session_id": session.session_id,
            "order_reference": order_reference
        }
        
    except Exception as e:
        logger.error(f"Stripe checkout error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create checkout session: {str(e)}")


@router.get("/checkout/status/{session_id}")
async def get_checkout_status(session_id: str):
    """
    Get the status of a checkout session.
    Called by frontend after returning from Stripe.
    """
    from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutStatusResponse
    
    db = get_db()
    
    # Get transaction record
    transaction = await db.payment_transactions.find_one(
        {"session_id": session_id},
        {"_id": 0}
    )
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Check if already processed to avoid double processing
    if transaction.get("payment_status") == "paid":
        return {
            "status": "complete",
            "payment_status": "paid",
            "order_reference": transaction.get("order_reference"),
            "already_processed": True
        }
    
    # Get status from Stripe
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url="")
    
    try:
        status: CheckoutStatusResponse = await stripe_checkout.get_checkout_status(session_id)
        
        # Update transaction record
        new_status = "paid" if status.payment_status == "paid" else status.status
        
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {
                "payment_status": new_status,
                "stripe_status": status.status,
                "updated_at": datetime.utcnow()
            }}
        )
        
        # If payment successful, create the print order record
        if status.payment_status == "paid" and transaction.get("payment_status") != "paid":
            order_id = str(uuid.uuid4())
            await db.print_orders.insert_one({
                "id": order_id,
                "order_reference": transaction.get("order_reference"),
                "book_id": transaction.get("book_id"),
                "book_title": transaction.get("book_title"),
                "user_id": transaction.get("user_id"),
                "product_type": transaction.get("product_type"),
                "status": "paid",  # Paid, awaiting shipping details
                "payment_session_id": session_id,
                "amount_paid": status.amount_total / 100,  # Convert from cents
                "currency": status.currency.upper(),
                "shipping_country": transaction.get("shipping_country"),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
            
            logger.info(f"Print order created: {order_id} for {transaction.get('order_reference')}")
        
        return {
            "status": status.status,
            "payment_status": status.payment_status,
            "amount_total": status.amount_total / 100,
            "currency": status.currency,
            "order_reference": transaction.get("order_reference"),
            "metadata": status.metadata
        }
        
    except Exception as e:
        logger.error(f"Error checking checkout status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check status: {str(e)}")


@router.post("/orders/{order_id}/add-shipping")
async def add_shipping_to_order(order_id: str, shipping_address: ShippingAddress):
    """
    Add shipping details to a paid order and submit to Gelato.
    """
    db = get_db()
    
    # Get the order
    order = await db.print_orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.get("status") != "paid":
        raise HTTPException(status_code=400, detail="Order is not in paid status")
    
    if order.get("gelato_order_id"):
        raise HTTPException(status_code=400, detail="Order already submitted to Gelato")
    
    # Generate PDF for printing
    book = await db.books.find_one({"id": order["book_id"]})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Get or generate the print PDF URL
    # For now, we'll use a placeholder - in production this would be a Cloudinary/S3 URL
    pdf_result = await generate_test_pdf(order["book_id"], db)
    
    # TODO: Upload PDF to cloud storage and get public URL
    # For now, return success without Gelato submission
    
    # Update order with shipping address
    await db.print_orders.update_one(
        {"id": order_id},
        {"$set": {
            "shipping_address": shipping_address.dict(),
            "status": "processing",
            "updated_at": datetime.utcnow()
        }}
    )
    
    return {
        "success": True,
        "order_id": order_id,
        "status": "processing",
        "message": "Shipping details added. Order is being prepared for production."
    }
