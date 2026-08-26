# backend/app/ai_chatbot/admin_communicator.py
"""
Admin Communicator - Bridge between AI and Admin
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger


class AdminCommunicator:
    """Handles communication between AI system and admin"""
    
    def __init__(self):
        self.conversation_history: List[Dict] = []
        self.admin_messages: List[Dict] = []
        self.max_history = 1000
    
    async def send_to_admin(self, message: str) -> Dict:
        """Send message from AI to admin"""
        try:
            msg_record = {
                "id": len(self.conversation_history) + 1,
                "sender": "AI",
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "read": False
            }
            
            self.conversation_history.append(msg_record)
            if len(self.conversation_history) > self.max_history:
                self.conversation_history = self.conversation_history[-self.max_history:]
            
            logger.info(f"🤖 AI -> Admin: {message[:100]}")
            return {
                "success": True,
                "message_id": msg_record["id"],
                "timestamp": msg_record["timestamp"]
            }
            
        except Exception as e:
            logger.error(f"Send to admin error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_conversation(self, limit: int = 50) -> Dict:
        """Get conversation history"""
        return {
            "success": True,
            "messages": self.conversation_history[-limit:],
            "total": len(self.conversation_history)
        }
    
    async def clear_conversation(self) -> Dict:
        """Clear conversation history"""
        self.conversation_history = []
        self.admin_messages = []
        logger.info("🗑️ Conversation cleared")
        return {"success": True, "message": "Conversation cleared"}
    
    def add_admin_message(self, message: str) -> Dict:
        """Add message from admin to AI"""
        msg_record = {
            "id": len(self.conversation_history) + 1,
            "sender": "ADMIN",
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        self.conversation_history.append(msg_record)
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]
        
        return msg_record
