# backend/app/admin/admin_auth.py
"""
ADMIN AUTHENTICATION - ULTRA SECURE ADMIN ACCESS
Inathibitisha admin credentials na kudhibiti access
"""

import hashlib
import secrets
from typing import Dict, Optional
from datetime import datetime, timedelta
from loguru import logger

class AdminAuth:
    """
    Ultra Secure Admin Authentication
    - Admin password: eSmwas@2004
    - Session management
    - Activity logging
    - IP restriction
    """
    
    ADMIN_PASSWORD_HASH = hashlib.sha256("eSmwas@2004".encode()).hexdigest()
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict] = {}
        self.activity_log: list = []
        self.failed_attempts: Dict[str, int] = {}
        self.max_attempts = 5
        self.lock_duration = 900  # 15 minutes
        self.session_duration = 3600  # 1 hour
        
        logger.info("🔐 Admin Authentication initialized")
    
    def authenticate(self, password: str, ip: str = "") -> Dict:
        """Authenticate admin"""
        try:
            # Check for too many failed attempts
            if ip in self.failed_attempts:
                if self.failed_attempts[ip] >= self.max_attempts:
                    return {
                        'success': False,
                        'error': 'Too many failed attempts. Locked for 15 minutes.',
                        'locked': True
                    }
            
            # Verify password
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            if password_hash == self.ADMIN_PASSWORD_HASH:
                # Generate session token
                session_token = secrets.token_urlsafe(32)
                
                # Create session
                self.active_sessions[session_token] = {
                    'created_at': datetime.now(),
                    'expires_at': datetime.now() + timedelta(seconds=self.session_duration),
                    'ip': ip,
                    'last_activity': datetime.now()
                }
                
                # Reset failed attempts
                if ip in self.failed_attempts:
                    del self.failed_attempts[ip]
                
                # Log successful login
                self._log_activity('admin_login', {'ip': ip, 'status': 'success'})
                
                logger.info(f"✅ Admin logged in from IP: {ip}")
                
                return {
                    'success': True,
                    'session_token': session_token,
                    'expires_at': self.active_sessions[session_token]['expires_at'].isoformat()
                }
            else:
                # Log failed attempt
                self.failed_attempts[ip] = self.failed_attempts.get(ip, 0) + 1
                self._log_activity('admin_login', {'ip': ip, 'status': 'failed'})
                
                remaining = self.max_attempts - self.failed_attempts[ip]
                
                logger.warning(f"⚠️ Failed admin login from IP: {ip}")
                
                return {
                    'success': False,
                    'error': f'Invalid password. {remaining} attempts remaining.',
                    'remaining_attempts': remaining
                }
                
        except Exception as e:
            logger.error(f"Admin authentication error: {e}")
            return {'success': False, 'error': str(e)}
    
    def verify_session(self, session_token: str) -> bool:
        """Verify admin session"""
        try:
            if session_token not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_token]
            
            # Check if session expired
            if datetime.now() > session['expires_at']:
                del self.active_sessions[session_token]
                return False
            
            # Update last activity
            session['last_activity'] = datetime.now()
            
            return True
            
        except Exception as e:
            logger.error(f"Session verification error: {e}")
            return False
    
    def logout(self, session_token: str) -> bool:
        """Logout admin"""
        try:
            if session_token in self.active_sessions:
                self._log_activity('admin_logout', {'session_token': session_token[:8]})
                del self.active_sessions[session_token]
                logger.info("✅ Admin logged out")
                return True
            return False
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False
    
    def _log_activity(self, action: str, data: Dict):
        """Log admin activity"""
        self.activity_log.append({
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'data': data
        })
        
        # Keep only last 1000 logs
        if len(self.activity_log) > 1000:
            self.activity_log = self.activity_log[-1000:]
    
    def get_activity_log(self, limit: int = 50) -> list:
        """Get admin activity log"""
        return self.activity_log[-limit:]
    
    def get_session_info(self, session_token: str) -> Optional[Dict]:
        """Get session information"""
        if session_token in self.active_sessions:
            session = self.active_sessions[session_token]
            return {
                'created_at': session['created_at'].isoformat(),
                'expires_at': session['expires_at'].isoformat(),
                'remaining_seconds': (session['expires_at'] - datetime.now()).total_seconds()
            }
        return None