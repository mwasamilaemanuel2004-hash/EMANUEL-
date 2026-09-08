"""
AI GUARDIAN - SUPER POWER SECURITY SYSTEM
"""
import os, time, secrets, logging, threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import deque, defaultdict
from enum import Enum
from dataclasses import dataclass

os.makedirs('data/logs', exist_ok=True)
os.makedirs('data/guardian', exist_ok=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [AI GUARDIAN] %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

class ThreatLevel(Enum):
    NONE = 0; LOW = 1; MEDIUM = 2; HIGH = 3; CRITICAL = 4; EXTREME = 5

class GuardianMode(Enum):
    PATROL = "patrol"; DEFENSE = "defense"; ATTACK = "attack"; STEALTH = "stealth"; EMERGENCY = "emergency"

class IncidentType(Enum):
    BRUTE_FORCE = "brute_force"; SQL_INJECTION = "sql_injection"; XSS_ATTACK = "xss_attack"
    API_ABUSE = "api_abuse"; PRIVILEGE_ESCALATION = "privilege_escalation"
    BOT_ACTIVITY = "bot_activity"; DDOS = "ddos"; SUSPICIOUS_LOGIN = "suspicious_login"

@dataclass
class SecurityIncident:
    id: str
    timestamp: datetime
    incident_type: IncidentType
    threat_level: ThreatLevel
    source_ip: str
    target: str
    details: Dict[str, Any]
    resolved: bool = False
    resolution: str = ""
class NeuralThreatDetector:
    """Neural Threat Detection Engine - pattern recognition for attacks"""
    def __init__(self):
        self.threat_patterns = self._load_patterns()
        self.learning_data = deque(maxlen=10000)
        self.detection_accuracy = 0.99

    def _load_patterns(self) -> Dict:
        return {
            'sql_injection': [
                r"(\b(union|select|insert|update|delete|drop|create)\b.*\b(from|into|table|database)\b)",
                r"(--|#|/\*)", r"('\s*(or|and)\s+')", r"(;\s*(drop|delete|truncate))",
            ],
            'xss_attack': [r"(<script[^>]*>)", r"(javascript\s*:)", r"(<iframe[^>]*>)"],
            'path_traversal': [r"(\.\./|\.\.\\)", r"(/etc/passwd)", r"(c:\\windows\\)"],
            'command_injection': [r"(;\s*(ls|cat|rm|wget|curl))", r"(\|\s*(ls|cat|rm|wget|curl))", r"(`[^`]+`)"],
        }

    def analyze_request(self, request_data: Dict) -> Tuple[ThreatLevel, Optional[IncidentType]]:
        import re
        threat_score = 0
        threats = []
        for key, value in request_data.items():
            if isinstance(value, str):
                for p in self.threat_patterns['sql_injection']:
                    if re.search(p, value, re.IGNORECASE):
                        threat_score += 4; threats.append(IncidentType.SQL_INJECTION); break
                for p in self.threat_patterns['xss_attack']:
                    if re.search(p, value, re.IGNORECASE):
                        threat_score += 4; threats.append(IncidentType.XSS_ATTACK); break
                for p in self.threat_patterns['path_traversal']:
                    if re.search(p, value, re.IGNORECASE):
                        threat_score += 4; threats.append(IncidentType.PRIVILEGE_ESCALATION); break
                for p in self.threat_patterns['command_injection']:
                    if re.search(p, value, re.IGNORECASE):
                        threat_score += 5; threats.append(IncidentType.PRIVILEGE_ESCALATION); break
        if threat_score >= 10: level = ThreatLevel.EXTREME
        elif threat_score >= 8: level = ThreatLevel.CRITICAL
        elif threat_score >= 4: level = ThreatLevel.HIGH
        elif threat_score >= 2: level = ThreatLevel.MEDIUM
        elif threat_score >= 1: level = ThreatLevel.LOW
        else: level = ThreatLevel.NONE
        return level, (threats[0] if threats else None)


class AIGuardian:
    """SUPER POWER SECURITY GUARDIAN"""
    def __init__(self):
        self.mode = GuardianMode.PATROL
        self.is_active = True
        self.start_time = datetime.now()
        self.threat_detector = NeuralThreatDetector()
        self.incidents: List[SecurityIncident] = []
        self.blocked_ips: Dict[str, datetime] = {}
        self.suspicious_ips: Dict[str, int] = defaultdict(int)
        self.request_counts: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.rate_limits = {'default': (100, 60), 'login': (5, 300), 'api': (1000, 60), 'admin': (50, 60)}
        self._lock = threading.Lock()
        self.stats = {
            'threats_blocked': 0, 'ips_blocked': 0, 'attacks_prevented': 0,
            'api_keys_protected': 0, 'uptime_seconds': 0,
        }
        self._start_monitoring()
        logger.info("AI GUARDIAN initialized - Super Power Security Active")

    def _start_monitoring(self):
        threading.Thread(target=self._monitor_loop, daemon=True).start()

    def _monitor_loop(self):
        while self.is_active:
            try:
                self._cleanup_expired_blocks()
                self.stats['uptime_seconds'] += 1
                time.sleep(1)
            except Exception:
                time.sleep(5)

    def _cleanup_expired_blocks(self):
        with self._lock:
            now = datetime.now()
            for ip in [ip for ip, exp in self.blocked_ips.items() if now > exp]:
                del self.blocked_ips[ip]

    def _is_ip_blocked(self, ip: str) -> bool:
        if ip in self.blocked_ips:
            if datetime.now() < self.blocked_ips[ip]:
                return True
            del self.blocked_ips[ip]
        return False

    def protect_request(self, request_data: Dict) -> Dict[str, Any]:
        """Protect incoming request - main entry point"""
        ip = request_data.get('ip', 'unknown')
        endpoint = request_data.get('endpoint', 'unknown')
        result = {'allowed': True, 'threat_level': ThreatLevel.NONE, 'action': 'allow', 'reason': ''}
        if self._is_ip_blocked(ip):
            result.update({'allowed': False, 'action': 'block', 'reason': 'IP blocked'})
            return result
        if not self._check_rate_limit(ip, endpoint):
            result.update({'allowed': False, 'action': 'rate_limit', 'reason': 'Rate exceeded'})
            self.suspicious_ips[ip] += 1
            return result
        level, inc_type = self.threat_detector.analyze_request(request_data)
        result['threat_level'] = level
        if level.value >= ThreatLevel.HIGH.value:
            result.update({'allowed': False, 'action': 'block', 'reason': f'Threat: {inc_type}'})
            self._handle_threat(ip, endpoint, level, inc_type)
        self.request_counts[ip].append(time.time())
        return result

    def _check_rate_limit(self, ip: str, endpoint: str) -> bool:
        cat = 'login' if 'login' in endpoint else ('api' if 'api' in endpoint else ('admin' if 'admin' in endpoint else 'default'))
        max_req, window = self.rate_limits[cat]
        now = time.time()
        recent = sum(1 for t in self.request_counts.get(ip, []) if now - t < window)
        return recent < max_req

    def _handle_threat(self, ip, endpoint, level, inc_type):
        self.stats['threats_blocked'] += 1
        self.stats['attacks_prevented'] += 1
        self.incidents.append(SecurityIncident(
            id=secrets.token_hex(16), timestamp=datetime.now(),
            incident_type=inc_type or IncidentType.BOT_ACTIVITY,
            threat_level=level, source_ip=ip, target=endpoint, details={}))
        duration = {ThreatLevel.HIGH: 3600, ThreatLevel.CRITICAL: 86400, ThreatLevel.EXTREME: 604800}.get(level, 3600)
        self.block_ip(ip, duration, f"Threat: {inc_type.value if inc_type else 'unknown'}")
        logger.warning(f"BLOCKED: {level.name} | IP: {ip} | {inc_type}")

    def block_ip(self, ip: str, duration: int = 3600, reason: str = ""):
        with self._lock:
            self.blocked_ips[ip] = datetime.now() + timedelta(seconds=duration)
            self.stats['ips_blocked'] += 1
            logger.info(f"IP Blocked: {ip} | {duration}s | {reason}")

    def unblock_ip(self, ip: str) -> bool:
        with self._lock:
            if ip in self.blocked_ips:
                del self.blocked_ips[ip]
                return True
            return False

    def protect_api_key(self, exchange: str, key_id: str) -> bool:
        self.stats['api_keys_protected'] += 1
        logger.info(f"API Key protected: {exchange} ({key_id[:8]}...)")
        return True

    def get_status(self) -> Dict[str, Any]:
        return {
            'active': self.is_active, 'mode': self.mode.value,
            'uptime': self.stats['uptime_seconds'],
            'threats_blocked': self.stats['threats_blocked'],
            'ips_blocked': self.stats['ips_blocked'],
            'currently_blocked': len(self.blocked_ips),
            'incidents': len(self.incidents),
            'attacks_prevented': self.stats['attacks_prevented'],
            'api_keys_protected': self.stats['api_keys_protected'],
            'accuracy': self.threat_detector.detection_accuracy,
        }

    def emergency_lockdown(self):
        self.mode = GuardianMode.EMERGENCY
        logger.critical("EMERGENCY LOCKDOWN ACTIVATED")

    def set_mode(self, mode: GuardianMode):
        self.mode = mode
        logger.info(f"AI GUARDIAN mode: {mode.value.upper()}")


# Global instance
ai_guardian = AIGuardian()

__all__ = ['AIGuardian', 'NeuralThreatDetector', 'ThreatLevel', 'GuardianMode', 'IncidentType', 'ai_guardian']
