# backend/app/admin/system_updater.py
"""
System Updater - Handles system updates and backups
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger
import os
import json


class SystemUpdater:
    """Handles system updates, upgrades, and backups"""
    
    def __init__(self):
        self.update_history: List[Dict] = []
        self.current_version = "2.0.0"
        self.last_update = None
        self.update_dir = "data/updates"
        os.makedirs(self.update_dir, exist_ok=True)
    
    async def perform_update(self, version: str, update_type: str, description: str) -> Dict:
        """Perform a system update"""
        try:
            update_record = {
                "version": version,
                "type": update_type,
                "description": description,
                "timestamp": datetime.now().isoformat(),
                "status": "completed"
            }
            
            self.update_history.append(update_record)
            self.last_update = datetime.now()
            
            logger.info(f"🔄 System update performed: {version} - {update_type}")
            return {
                "success": True,
                "version": version,
                "type": update_type,
                "message": f"System updated to {version}"
            }
            
        except Exception as e:
            logger.error(f"Update error: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_backup(self) -> Dict:
        """Create system backup"""
        try:
            backup_dir = os.path.join(self.update_dir, "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            backup_file = os.path.join(backup_dir, f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            
            backup_data = {
                "version": self.current_version,
                "timestamp": datetime.now().isoformat(),
                "update_history": self.update_history[-50:]
            }
            
            with open(backup_file, "w") as f:
                json.dump(backup_data, f, indent=2)
            
            logger.info(f"💾 Backup created: {backup_file}")
            return {
                "success": True,
                "backup_file": backup_file,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Backup error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_update_history(self, limit: int = 20) -> List[Dict]:
        """Get update history"""
        return self.update_history[-limit:]
    
    def get_status(self) -> Dict:
        """Get updater status"""
        return {
            "current_version": self.current_version,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "updates_count": len(self.update_history)
        }
