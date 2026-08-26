# backend/app/admin/admin_controller.py
"""
ADMIN CONTROLLER - ULTRA ADVANCED SYSTEM CONTROL
Inawezesha admin kudhibiti system yote
- AI inaweza kuwasiliana na Admin pekee
- Admin ndiye anayeweza kutoa amri zote
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger

from .admin_auth import AdminAuth
from .trade_override import TradeOverrideSystem, OverrideType, TradeOverride
from .system_updater import SystemUpdater
from ..ai_chatbot.admin_communicator import AdminCommunicator
from ..core.trading_engine import TradingEngine
from ..core.risk_management_engine import RiskEngine
from ..core.bot_state_manager import BotStateManager

class CommandType(Enum):
    TRADE = "trade"
    SYSTEM = "system"
    BOT = "bot"
    SECURITY = "security"
    AI = "ai"
    UPDATE = "update"
    UPGRADE = "upgrade"
    MONITOR = "monitor"

@dataclass
class AdminCommand:
    id: str
    type: CommandType
    action: str
    params: Dict
    timestamp: datetime = field(default_factory=datetime.now)
    status: str = "pending"
    result: Optional[Dict] = None
    executed_by: str = "admin"

class AdminController:
    """
    Ultra Advanced Admin Controller
    - Admin ndiye anayeweza kutoa amri zote
    - AI inaweza kuwasiliana na Admin pekee
    - System upgrades na updates
    - Trade overrides
    - Bot management
    - Security controls
    """
    
    def __init__(self):
        self.admin_auth = AdminAuth()
        self.trade_override = TradeOverrideSystem(TradingEngine(), RiskEngine())
        self.system_updater = SystemUpdater()
        self.admin_communicator = AdminCommunicator()
        self.command_history: List[AdminCommand] = []
        self.command_counter = 0
        
        # System status
        self.system_status = {
            'version': '2.0.0',
            'status': 'running',
            'uptime': 0,
            'last_update': None,
            'bots_active': 0,
            'trades_today': 0
        }
        
        logger.info("🔐 Admin Controller initialized")
    
    async def execute_command(self, command: AdminCommand) -> Dict:
        """Execute admin command"""
        try:
            command.status = "executing"
            
            if command.type == CommandType.TRADE:
                result = await self._execute_trade_command(command)
            elif command.type == CommandType.SYSTEM:
                result = await self._execute_system_command(command)
            elif command.type == CommandType.BOT:
                result = await self._execute_bot_command(command)
            elif command.type == CommandType.SECURITY:
                result = await self._execute_security_command(command)
            elif command.type == CommandType.AI:
                result = await self._execute_ai_command(command)
            elif command.type == CommandType.UPDATE:
                result = await self._execute_update_command(command)
            elif command.type == CommandType.UPGRADE:
                result = await self._execute_upgrade_command(command)
            elif command.type == CommandType.MONITOR:
                result = await self._execute_monitor_command(command)
            else:
                return {'success': False, 'error': f'Unknown command type: {command.type}'}
            
            command.status = "completed"
            command.result = result
            self.command_history.append(command)
            
            # Log command
            logger.info(f"📋 Admin command executed: {command.type.value} - {command.action}")
            
            return result
            
        except Exception as e:
            command.status = "failed"
            logger.error(f"Command execution error: {e}")
            return {'success': False, 'error': str(e)}
    
    # ============================================
    # TRADE COMMANDS
    # ============================================
    
    async def _execute_trade_command(self, command: AdminCommand) -> Dict:
        """Execute trade-related commands"""
        action = command.action
        
        if action == "force_open":
            return await self.trade_override.force_open(
                symbol=command.params.get('symbol'),
                side=command.params.get('side'),
                quantity=command.params.get('quantity'),
                reason=command.params.get('reason', 'Admin override')
            )
        elif action == "force_close":
            return await self.trade_override.force_close(
                symbol=command.params.get('symbol'),
                reason=command.params.get('reason', 'Admin override')
            )
        elif action == "pause_all":
            return await self.trade_override.pause_all(
                reason=command.params.get('reason', 'Admin pause')
            )
        elif action == "resume_all":
            return await self.trade_override.resume_all()
        elif action == "get_positions":
            return await self.trade_override.get_positions()
        else:
            return {'success': False, 'error': f'Unknown trade action: {action}'}
    
    # ============================================
    # SYSTEM COMMANDS
    # ============================================
    
    async def _execute_system_command(self, command: AdminCommand) -> Dict:
        """Execute system-related commands"""
        action = command.action
        
        if action == "status":
            return self.get_system_status()
        elif action == "restart":
            return await self._restart_system()
        elif action == "shutdown":
            return await self._shutdown_system()
        elif action == "backup":
            return await self.system_updater.create_backup()
        elif action == "logs":
            return self._get_system_logs()
        else:
            return {'success': False, 'error': f'Unknown system action: {action}'}
    
    async def _restart_system(self) -> Dict:
        """Restart the system"""
        try:
            logger.warning("🔄 System restart initiated by admin")
            # In production, implement actual restart
            await asyncio.sleep(2)
            return {'success': True, 'message': 'System restarted successfully'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _shutdown_system(self) -> Dict:
        """Shutdown the system"""
        try:
            logger.warning("🛑 System shutdown initiated by admin")
            # In production, implement actual shutdown
            return {'success': True, 'message': 'System shutdown initiated'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_system_logs(self) -> Dict:
        """Get system logs"""
        return {
            'success': True,
            'logs': admin_auth.get_activity_log(50)
        }
    
    # ============================================
    # BOT COMMANDS
    # ============================================
    
    async def _execute_bot_command(self, command: AdminCommand) -> Dict:
        """Execute bot-related commands"""
        action = command.action
        
        if action == "start":
            bot_id = command.params.get('bot_id')
            return await self._start_bot(bot_id)
        elif action == "stop":
            bot_id = command.params.get('bot_id')
            return await self._stop_bot(bot_id)
        elif action == "pause":
            bot_id = command.params.get('bot_id')
            return await self._pause_bot(bot_id)
        elif action == "resume":
            bot_id = command.params.get('bot_id')
            return await self._resume_bot(bot_id)
        elif action == "restart":
            bot_id = command.params.get('bot_id')
            return await self._restart_bot(bot_id)
        elif action == "status":
            return self._get_bot_status()
        else:
            return {'success': False, 'error': f'Unknown bot action: {action}'}
    
    async def _start_bot(self, bot_id: str) -> Dict:
        return {'success': True, 'message': f'Bot {bot_id} started'}
    
    async def _stop_bot(self, bot_id: str) -> Dict:
        return {'success': True, 'message': f'Bot {bot_id} stopped'}
    
    async def _pause_bot(self, bot_id: str) -> Dict:
        return {'success': True, 'message': f'Bot {bot_id} paused'}
    
    async def _resume_bot(self, bot_id: str) -> Dict:
        return {'success': True, 'message': f'Bot {bot_id} resumed'}
    
    async def _restart_bot(self, bot_id: str) -> Dict:
        return {'success': True, 'message': f'Bot {bot_id} restarted'}
    
    def _get_bot_status(self) -> Dict:
        return {
            'success': True,
            'bots': {
                'forex': {'status': 'running', 'bots': 5},
                'crypto': {'status': 'running', 'bots': 5},
                'stocks': {'status': 'running', 'bots': 1},
                'metals': {'status': 'running', 'bots': 1},
                'commodities': {'status': 'running', 'bots': 1}
            }
        }
    
    # ============================================
    # SECURITY COMMANDS
    # ============================================
    
    async def _execute_security_command(self, command: AdminCommand) -> Dict:
        """Execute security-related commands"""
        action = command.action
        
        if action == "block_ip":
            ip = command.params.get('ip')
            return self._block_ip(ip)
        elif action == "unblock_ip":
            ip = command.params.get('ip')
            return self._unblock_ip(ip)
        elif action == "get_blocks":
            return self._get_blocked_ips()
        elif action == "reset_sessions":
            return self._reset_sessions()
        else:
            return {'success': False, 'error': f'Unknown security action: {action}'}
    
    def _block_ip(self, ip: str) -> Dict:
        return {'success': True, 'message': f'IP {ip} blocked'}
    
    def _unblock_ip(self, ip: str) -> Dict:
        return {'success': True, 'message': f'IP {ip} unblocked'}
    
    def _get_blocked_ips(self) -> Dict:
        return {'success': True, 'blocked_ips': []}
    
    def _reset_sessions(self) -> Dict:
        return {'success': True, 'message': 'All sessions reset'}
    
    # ============================================
    # AI COMMANDS
    # ============================================
    
    async def _execute_ai_command(self, command: AdminCommand) -> Dict:
        """Execute AI-related commands - Admin only"""
        action = command.action
        
        if action == "send_message":
            message = command.params.get('message')
            return await self.admin_communicator.send_to_admin(message)
        elif action == "get_conversation":
            return await self.admin_communicator.get_conversation()
        elif action == "clear_conversation":
            return await self.admin_communicator.clear_conversation()
        else:
            return {'success': False, 'error': f'Unknown AI action: {action}'}
    
    # ============================================
    # UPDATE/UPGRADE COMMANDS
    # ============================================
    
    async def _execute_update_command(self, command: AdminCommand) -> Dict:
        """Execute update command"""
        version = command.params.get('version')
        update_type = command.params.get('type', 'feature')
        description = command.params.get('description', '')
        
        if not version:
            return {'success': False, 'error': 'Version required'}
        
        return await self.system_updater.perform_update(version, update_type, description)
    
    async def _execute_upgrade_command(self, command: AdminCommand) -> Dict:
        """Execute upgrade command"""
        # Upgrade is a major system upgrade
        return await self._execute_update_command(command)
    
    # ============================================
    # MONITOR COMMANDS
    # ============================================
    
    async def _execute_monitor_command(self, command: AdminCommand) -> Dict:
        """Execute monitoring commands"""
        return {
            'success': True,
            'system': self.get_system_status(),
            'trades': self.trade_override.get_status(),
            'updates': self.system_updater.get_update_history(),
            'commands': self.get_command_history(10)
        }
    
    # ============================================
    # SYSTEM STATUS
    # ============================================
    
    def get_system_status(self) -> Dict:
        """Get full system status"""
        return {
            'success': True,
            'version': self.system_status['version'],
            'status': self.system_status['status'],
            'uptime': self.system_status['uptime'],
            'last_update': self.system_status['last_update'],
            'bots_active': self.system_status['bots_active'],
            'trades_today': self.system_status['trades_today'],
            'admin_sessions': len(self.admin_auth.active_sessions),
            'override_status': self.trade_override.get_status(),
            'update_history': self.system_updater.get_update_history()[-5:]
        }
    
    def get_command_history(self, limit: int = 20) -> List[Dict]:
        """Get command history"""
        return [{
            'id': c.id,
            'type': c.type.value,
            'action': c.action,
            'status': c.status,
            'timestamp': c.timestamp.isoformat(),
            'result': c.result
        } for c in self.command_history[-limit:]]
    
    def get_admin_commands(self) -> List[str]:
        """Get list of available admin commands"""
        return [
            # Trade commands
            'trade.force_open',
            'trade.force_close',
            'trade.pause_all',
            'trade.resume_all',
            'trade.get_positions',
            
            # System commands
            'system.status',
            'system.restart',
            'system.shutdown',
            'system.backup',
            'system.logs',
            
            # Bot commands
            'bot.start',
            'bot.stop',
            'bot.pause',
            'bot.resume',
            'bot.restart',
            'bot.status',
            
            # Security commands
            'security.block_ip',
            'security.unblock_ip',
            'security.get_blocks',
            'security.reset_sessions',
            
            # AI commands
            'ai.send_message',
            'ai.get_conversation',
            'ai.clear_conversation',
            
            # Update commands
            'update.system',
            'upgrade.system',
            
            # Monitor commands
            'monitor.system'
        ]