import asyncio
import os
import sys

# Add backend path
sys.path.insert(0, '/app/backend')

# Load environment
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

async def test_email():
    from services.email_service import send_email, is_configured, get_provider
    
    print(f"Email configured: {is_configured()}")
    print(f"Provider: {get_provider()}")
    print(f"RESEND_API_KEY: {os.environ.get('RESEND_API_KEY', '')[:20]}...")
    print(f"ADMIN_NOTIFY_EMAIL: {os.environ.get('ADMIN_NOTIFY_EMAIL')}")
    
    # Test sending a simple email
    test_html = """
    <html>
    <body>
        <h1>Test Email from Azories</h1>
        <p>This is a test email to verify the email notification system is working.</p>
        <p>Time: """ + str(asyncio.get_event_loop().time()) + """</p>
    </body>
    </html>
    """
    
    admin_email = os.environ.get("ADMIN_NOTIFY_EMAIL", "books@azories.com")
    print(f"\nSending test email to: {admin_email}")
    
    result = await send_email(admin_email, "🧪 Test Email Notification", test_html)
    print(f"Result: {result}")
    
    return result

if __name__ == "__main__":
    result = asyncio.run(test_email())
    print(f"\nFinal result: {result}")
