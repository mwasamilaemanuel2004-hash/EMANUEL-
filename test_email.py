"""
Email Test Script - Test SMTP connection and send test email
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.notification_service import NotificationService, Notification

async def test_email():
    print("\n" + "="*60)
    print("  ESMH.TRADE - EMAIL NOTIFICATION TEST")
    print("="*60)
    
    service = NotificationService()
    
    # Check status
    status = service.get_status()
    print(f"\n  Email Configured: {status['email_configured']}")
    print(f"  SMTP Server: {status['smtp_server']}")
    print(f"  SMTP User: {status['smtp_user']}")
    
    if not status['email_configured']:
        print("\n  ERROR: Email not configured. Check .env file.")
        return False
    
    # Send test email
    print("\n  Sending test email to emwasamila123@gmail.com...")
    
    notification = Notification(
        title="ESMH.TRADE Test Email",
        message="This is a test email from your ESMH.TRADE trading system.\n\nIf you received this, your email notifications are working correctly!\n\nSystem Status: ONLINE\nTrading Mode: PAPER\nActive Bots: 0\nOpen Positions: 0",
        channel="email",
        priority="high",
        data={'to_email': 'emwasamila123@gmail.com'}
    )
    
    result = await service.send(notification)
    
    print(f"\n  Result: {result.get('status', 'unknown')}")
    
    if result.get('status') == 'sent':
        print("  SUCCESS: Email sent successfully!")
        print("  Check emwasamila123@gmail.com for the test email.")
        return True
    else:
        print(f"  FAILED: {result.get('error', 'Unknown error')}")
        print("\n  Troubleshooting:")
        print("  1. Verify Gmail App Password is correct")
        print("  2. Check if 'Less secure app access' is enabled")
        print("  3. Ensure firewall allows outbound SMTP (port 587)")
        print("  4. Check Gmail account for security alerts")
        return False

if __name__ == "__main__":
    asyncio.run(test_email())
