import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone, timedelta

sys.path.insert(0, '/app/backend')

from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

async def test_all_notifications():
    from services.email_service import send_email, is_configured, get_provider
    
    print("="*60)
    print("ADMIN EMAIL NOTIFICATIONS TEST")
    print("="*60)
    print(f"Email Provider: {get_provider()}")
    print(f"Admin Email: {os.environ.get('ADMIN_NOTIFY_EMAIL')}")
    print()
    
    results = []
    admin_email = os.environ.get("ADMIN_NOTIFY_EMAIL", "books@azories.com")
    now_iso = datetime.now(timezone.utc).isoformat()
    
    # Test 1: New User Signup Notification
    print("TEST 1: New User Signup Notification")
    test_user = {
        "name": "Test User",
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com"
    }
    admin_subject = f"🆕 New User Signup: {test_user['name']}"
    admin_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #10b981, #059669); padding: 20px; border-radius: 12px 12px 0 0;">
            <h1 style="color: white; margin: 0; font-size: 24px;">🎉 New User Registered!</h1>
        </div>
        <div style="background: #ffffff; padding: 20px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 12px 12px;">
            <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;"><strong>Name:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">{test_user['name']}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;"><strong>Email:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">{test_user['email']}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;"><strong>Registered:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">{now_iso}</td>
                </tr>
            </table>
            <p style="color: #6b7280; margin-top: 20px;">User has a 30-day Pro trial active.</p>
        </div>
    </body>
    </html>
    """
    result1 = await send_email(admin_email, admin_subject, admin_html)
    print(f"  Result: {'✅ SUCCESS' if result1.get('success') else '❌ FAILED'}")
    print(f"  Email ID: {result1.get('email_id')}")
    print(f"  Provider: {result1.get('provider')}")
    results.append(("User Signup", result1))
    print()
    
    # Test 2: Credit Purchase Notification
    print("TEST 2: Credit Purchase Notification")
    credits = 500
    amount = 18.00
    admin_subject = f"💰 Credit Purchase: {credits} credits by Test User"
    admin_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #f59e0b, #d97706); padding: 20px; border-radius: 12px 12px 0 0;">
            <h1 style="color: white; margin: 0; font-size: 24px;">💰 New Credit Purchase!</h1>
        </div>
        <div style="background: #ffffff; padding: 20px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 12px 12px;">
            <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;"><strong>User:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">Test User</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;"><strong>Email:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">test@example.com</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;"><strong>Credits:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">{credits} credits</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;"><strong>Amount:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">£{amount}</td>
                </tr>
            </table>
            <p style="color: #16a34a; font-weight: bold; margin-top: 20px;">✅ Payment processed successfully via Stripe</p>
        </div>
    </body>
    </html>
    """
    result2 = await send_email(admin_email, admin_subject, admin_html)
    print(f"  Result: {'✅ SUCCESS' if result2.get('success') else '❌ FAILED'}")
    print(f"  Email ID: {result2.get('email_id')}")
    print(f"  Provider: {result2.get('provider')}")
    results.append(("Credit Purchase", result2))
    print()
    
    # Test 3: Book Submission Notification
    print("TEST 3: Book Submission Notification")
    book_title = "Test Book Submission"
    subject = f"✅ New book ready for review: '{book_title}'"
    app_url = os.environ.get("APP_URL", "https://azories.com")
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #7c3aed, #a855f7); padding: 20px; border-radius: 12px 12px 0 0;">
            <h1 style="color: white; margin: 0; font-size: 24px;">📚 Azories Book Review</h1>
        </div>
        <div style="background: #ffffff; padding: 20px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 12px 12px;">
            <h2 style="color: #1f2937; margin-top: 0;">✅ New Book Submission</h2>
            <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;"><strong>Book Title:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">{book_title}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;"><strong>Author:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">Test Author (test@example.com)</td>
                </tr>
            </table>
            <div style="background: #f0fdf4; border: 1px solid #16a34a; padding: 15px; border-radius: 8px; margin: 15px 0;">
                <h3 style="color: #16a34a; margin: 0 0 10px 0;">✅ AI Moderation: PASSED</h3>
                <p style="margin: 5px 0;">Content is appropriate for children</p>
            </div>
            <p style="color: #6b7280; margin-top: 20px;">Please log in to the Admin Dashboard to review this book.</p>
            <div style="text-align: center; margin: 25px 0;">
                <a href="{app_url}/admin" style="background: #7c3aed; color: white; padding: 12px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; display: inline-block;">Review Book</a>
            </div>
        </div>
    </body>
    </html>
    """
    result3 = await send_email(admin_email, subject, html_content)
    print(f"  Result: {'✅ SUCCESS' if result3.get('success') else '❌ FAILED'}")
    print(f"  Email ID: {result3.get('email_id')}")
    print(f"  Provider: {result3.get('provider')}")
    results.append(("Book Submission", result3))
    print()
    
    # Summary
    print("="*60)
    print("SUMMARY")
    print("="*60)
    passed = sum(1 for _, r in results if r.get('success'))
    print(f"Passed: {passed}/3")
    for name, r in results:
        status = "✅" if r.get('success') else "❌"
        print(f"  {status} {name}: {r.get('email_id', r.get('error', 'N/A'))}")
    print()
    
    return all(r.get('success') for _, r in results)

if __name__ == "__main__":
    success = asyncio.run(test_all_notifications())
    exit(0 if success else 1)
