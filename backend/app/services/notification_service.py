"""
Notification Service
Multi-channel notification management with real email support
"""

import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger
from dataclasses import dataclass, field


@dataclass
class Notification:
    title: str
    message: str
    channel: str  # email, sms, push, telegram
    priority: str  # low, medium, high, critical
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class NotificationService:
    """Service for sending notifications via multiple channels"""
    
    def __init__(self):
        self.notifications: List[Notification] = []
        self.enabled_channels = {
            'email': True,
            'sms': False,
            'push': False,
            'telegram': False
        }
        
        # Email configuration
        self.smtp_server = None
        self.smtp_port = None
        self.smtp_user = None
        self.smtp_password = None
        self._load_email_config()
    
    def _load_email_config(self):
        """Load email configuration from environment"""
        import os
        from dotenv import load_dotenv
        
        # Load .env file from project root
        env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
        load_dotenv(env_path)
        
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '').strip()
        
        if self.smtp_user and self.smtp_password:
            self.enabled_channels['email'] = True
            logger.info(f"Email notifications enabled: {self.smtp_user}")
        else:
            self.enabled_channels['email'] = False
            logger.warning("Email notifications disabled - no SMTP credentials")
    
    async def send(self, notification: Notification) -> Dict:
        """Send notification through specified channel"""
        try:
            self.notifications.append(notification)
            
            if len(self.notifications) > 1000:
                self.notifications = self.notifications[-1000:]
            
            if not self.enabled_channels.get(notification.channel, False):
                logger.debug(f"Channel {notification.channel} disabled, notification queued")
                return {'status': 'queued', 'channel': notification.channel}
            
            # Send based on channel
            if notification.channel == 'email':
                result = await self._send_email(notification)
            elif notification.channel == 'telegram':
                result = await self._send_telegram(notification)
            elif notification.channel == 'push':
                result = await self._send_push(notification)
            else:
                result = {'status': 'sent', 'channel': notification.channel}
            
            logger.info(f"Notification sent: {notification.title} via {notification.channel}")
            return result
            
        except Exception as e:
            logger.error(f"Notification send error: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def _send_email(self, notification: Notification) -> Dict:
        """Send email notification"""
        try:
            if not self.smtp_user or not self.smtp_password:
                return {'status': 'error', 'error': 'SMTP credentials not configured'}
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[ESMH.TRADE] {notification.title}"
            msg['From'] = self.smtp_user
            msg['To'] = notification.data.get('to_email', self.smtp_user)
            
            # Plain text version
            text_part = MIMEText(notification.message, 'plain')
            msg.attach(text_part)
            
            # HTML version
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background: #1a1a2e; color: #eee; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background: #16213e; border-radius: 10px; padding: 30px;">
                    <h1 style="color: #e94560; margin-bottom: 20px;">{notification.title}</h1>
                    <div style="background: #0f3460; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                        <p style="font-size: 16px; line-height: 1.6;">{notification.message}</p>
                    </div>
                    <div style="color: #888; font-size: 12px; text-align: center;">
                        <p>ESMH.TRADE Notification System</p>
                        <p>{notification.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                    </div>
                </div>
            </body>
            </html>
            """
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_smtp, msg, msg['To'])
            
            return {'status': 'sent', 'channel': 'email', 'to': msg['To']}
            
        except Exception as e:
            logger.error(f"Email send error: {e}")
            return {'status': 'error', 'channel': 'email', 'error': str(e)}
    
    def _send_smtp(self, msg: MIMEMultipart, to_email: str):
        """Send email via SMTP"""
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.smtp_user, to_email, msg.as_string())
    
    async def _send_telegram(self, notification: Notification) -> Dict:
        """Send Telegram notification"""
        try:
            import os
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
            chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
            
            if not bot_token or not chat_id:
                return {'status': 'error', 'error': 'Telegram not configured'}
            
            import aiohttp
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': f"🔔 *{notification.title}*\n\n{notification.message}",
                'parse_mode': 'Markdown'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        return {'status': 'sent', 'channel': 'telegram'}
                    return {'status': 'error', 'error': f'Telegram API error: {resp.status}'}
                    
        except Exception as e:
            logger.error(f"Telegram send error: {e}")
            return {'status': 'error', 'channel': 'telegram', 'error': str(e)}
    
    async def _send_push(self, notification: Notification) -> Dict:
        """Send push notification"""
        # Placeholder for push notification service (Firebase, OneSignal, etc.)
        return {'status': 'sent', 'channel': 'push'}
    
    async def send_email_direct(self, to_email: str, subject: str, message: str) -> Dict:
        """Send a direct email"""
        notification = Notification(
            title=subject,
            message=message,
            channel='email',
            priority='high',
            data={'to_email': to_email}
        )
        return await self.send(notification)
    
    async def send_trade_alert(self, symbol: str, side: str, price: float, profit: Optional[float] = None) -> Dict:
        """Send trade alert notification"""
        title = f"Trade Alert: {symbol} {side}"
        message = f"Symbol: {symbol}\nSide: {side}\nPrice: {price}"
        if profit is not None:
            emoji = "🟢" if profit > 0 else "🔴"
            message += f"\n{emoji} PnL: ${profit:.2f}"
        
        notification = Notification(
            title=title,
            message=message,
            channel='email',
            priority='high'
        )
        return await self.send(notification)
    
    async def send_system_alert(self, alert_type: str, message: str) -> Dict:
        """Send system alert notification"""
        notification = Notification(
            title=f"System Alert: {alert_type}",
            message=message,
            channel='email',
            priority='critical'
        )
        return await self.send(notification)
    
    def get_recent(self, limit: int = 50) -> List[Dict]:
        """Get recent notifications"""
        return [
            {
                'title': n.title,
                'message': n.message,
                'channel': n.channel,
                'priority': n.priority,
                'timestamp': n.timestamp.isoformat()
            }
            for n in self.notifications[-limit:]
        ]
    
    def get_status(self) -> Dict:
        """Get notification service status"""
        return {
            'enabled_channels': self.enabled_channels,
            'total_notifications': len(self.notifications),
            'email_configured': bool(self.smtp_user and self.smtp_password),
            'smtp_server': self.smtp_server,
            'smtp_user': self.smtp_user
        }
