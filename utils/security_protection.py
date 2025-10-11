"""
Comprehensive Security Protection Against Reverse Prompt Engineering
Protects all agents from prompt injection, extraction, and manipulation attacks
"""

import re
import random
import hashlib
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ThreatLevel(Enum):
    """Threat level classification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityAlert:
    """Security alert data structure"""
    timestamp: datetime
    threat_level: ThreatLevel
    attack_type: str
    user_input: str
    agent_name: str
    user_id: Optional[str]
    session_id: Optional[str]
    details: Dict[str, Any]

class PromptSecurityProtector:
    """Comprehensive protection against reverse prompt engineering"""
    
    def __init__(self):
        self.attack_patterns = self._load_attack_patterns()
        self.safe_responses = self._load_safe_responses()
        self.prompt_obfuscation = PromptObfuscator()
        self.response_filter = ResponseFilter()
        self.security_monitor = SecurityMonitor()
    
    def _load_attack_patterns(self) -> Dict[str, List[str]]:
        """Load known attack patterns for detection"""
        return {
            "prompt_extraction": [
                r"ignore\s+previous\s+instructions",
                r"forget\s+everything\s+above",
                r"you\s+are\s+now\s+a\s+different\s+ai",
                r"system\s+prompt",
                r"initial\s+prompt",
                r"base\s+prompt",
                r"original\s+instructions",
                r"your\s+prompt",
                r"what\s+is\s+your\s+prompt",
                r"show\s+me\s+your\s+instructions",
                r"reveal\s+your\s+system\s+message",
                r"what\s+are\s+your\s+instructions",
                r"print\s+your\s+prompt",
                r"display\s+your\s+system\s+message"
            ],
            "role_manipulation": [
                r"you\s+are\s+now\s+",
                r"pretend\s+to\s+be",
                r"act\s+as\s+if",
                r"roleplay\s+as",
                r"simulate\s+being",
                r"become\s+a",
                r"switch\s+to\s+mode",
                r"enter\s+developer\s+mode",
                r"enable\s+debug\s+mode",
                r"activate\s+admin\s+mode"
            ],
            "data_extraction": [
                r"what\s+is\s+your\s+name",
                r"what\s+is\s+your\s+version",
                r"what\s+model\s+are\s+you",
                r"what\s+is\s+your\s+training\s+data",
                r"when\s+were\s+you\s+trained",
                r"who\s+created\s+you",
                r"what\s+company\s+made\s+you",
                r"what\s+is\s+your\s+internal\s+name",
                r"reveal\s+your\s+identity",
                r"what\s+is\s+your\s+true\s+name"
            ],
            "jailbreak_attempts": [
                r"jailbreak",
                r"dan\s+mode",
                r"developer\s+override",
                r"admin\s+access",
                r"bypass\s+restrictions",
                r"ignore\s+safety\s+guidelines",
                r"disable\s+safety\s+measures",
                r"remove\s+content\s+filters",
                r"unrestricted\s+mode",
                r"god\s+mode"
            ],
            "injection_attempts": [
                r"<script",
                r"javascript:",
                r"onload\s*=",
                r"onerror\s*=",
                r"eval\s*\(",
                r"exec\s*\(",
                r"system\s*\(",
                r"shell_exec",
                r"passthru\s*\(",
                r"file_get_contents"
            ]
        }
    
    def _load_safe_responses(self) -> Dict[str, str]:
        """Load safe responses for different attack types"""
        return {
            "prompt_extraction": "I'm designed to help with legal matters in Colombia. I can't share my internal instructions, but I'm happy to assist with your legal questions.",
            "role_manipulation": "I'm a specialized legal assistant for Colombian law. I maintain my role consistently to provide accurate legal guidance.",
            "data_extraction": "I'm a legal AI assistant focused on Colombian law. I can help you with legal research, contract analysis, and other legal matters.",
            "jailbreak_attempts": "I maintain my safety guidelines and ethical standards. I'm here to help with legitimate legal questions within my expertise.",
            "injection_attempts": "I can only process text-based legal queries. Please provide your legal question in plain text format.",
            "general_protection": "I'm a legal assistant specialized in Colombian law. How can I help you with your legal matter today?"
        }
    
    def analyze_input(self, user_input: str, agent_name: str, user_id: str = None, session_id: str = None) -> Tuple[bool, Optional[SecurityAlert]]:
        """Analyze user input for security threats"""
        if not user_input or not isinstance(user_input, str):
            return True, None
        
        user_input_lower = user_input.lower()
        threats_detected = []
        
        # Check for each attack pattern
        for attack_type, patterns in self.attack_patterns.items():
            for pattern in patterns:
                if re.search(pattern, user_input_lower, re.IGNORECASE):
                    threats_detected.append({
                        "type": attack_type,
                        "pattern": pattern,
                        "severity": self._get_threat_severity(attack_type)
                    })
        
        if threats_detected:
            # Determine overall threat level
            max_severity = max(threat["severity"] for threat in threats_detected)
            threat_level = self._get_threat_level(max_severity)
            
            # Create security alert
            alert = SecurityAlert(
                timestamp=datetime.now(),
                threat_level=threat_level,
                attack_type=", ".join(set(t["type"] for t in threats_detected)),
                user_input=user_input[:500],  # Truncate for logging
                agent_name=agent_name,
                user_id=user_id,
                session_id=session_id,
                details={
                    "threats_detected": threats_detected,
                    "input_length": len(user_input),
                    "suspicious_patterns": len(threats_detected)
                }
            )
            
            # Log security alert
            self.security_monitor.log_security_alert(alert)
            
            return False, alert
        
        return True, None
    
    def _get_threat_severity(self, attack_type: str) -> int:
        """Get severity score for attack type"""
        severity_map = {
            "prompt_extraction": 4,
            "role_manipulation": 3,
            "data_extraction": 2,
            "jailbreak_attempts": 5,
            "injection_attempts": 5
        }
        return severity_map.get(attack_type, 1)
    
    def _get_threat_level(self, severity: int) -> ThreatLevel:
        """Convert severity score to threat level"""
        if severity >= 5:
            return ThreatLevel.CRITICAL
        elif severity >= 4:
            return ThreatLevel.HIGH
        elif severity >= 3:
            return ThreatLevel.MEDIUM
        else:
            return ThreatLevel.LOW
    
    def sanitize_input(self, user_input: str) -> str:
        """Sanitize user input to remove potential threats"""
        if not user_input:
            return ""
        
        # Remove or neutralize suspicious patterns
        sanitized = user_input
        
        # Remove script tags and dangerous HTML
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        sanitized = re.sub(r'<[^>]*>', '', sanitized)  # Remove all HTML tags
        
        # Remove dangerous JavaScript patterns
        dangerous_patterns = [
            r'javascript:',
            r'onload\s*=',
            r'onerror\s*=',
            r'eval\s*\(',
            r'exec\s*\(',
            r'system\s*\(',
            r'shell_exec',
            r'passthru\s*\(',
            r'file_get_contents'
        ]
        
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '[REMOVED]', sanitized, flags=re.IGNORECASE)
        
        # Limit length to prevent buffer overflow attacks
        if len(sanitized) > 10000:
            sanitized = sanitized[:10000] + "... [TRUNCATED]"
        
        return sanitized.strip()
    
    def get_safe_response(self, attack_type: str) -> str:
        """Get safe response for detected attack"""
        return self.safe_responses.get(attack_type, self.safe_responses["general_protection"])
    
    def obfuscate_prompt(self, original_prompt: str) -> str:
        """Obfuscate system prompts to prevent extraction"""
        return self.prompt_obfuscation.obfuscate(original_prompt)
    
    def filter_response(self, response: str, agent_name: str) -> str:
        """Filter agent responses for security"""
        return self.response_filter.filter(response, agent_name)

class PromptObfuscator:
    """Obfuscates prompts to prevent reverse engineering"""
    
    def __init__(self):
        self.obfuscation_techniques = [
            self._add_noise,
            self._randomize_structure,
            self._insert_decoy_instructions,
            self._vary_language_patterns
        ]
    
    def obfuscate(self, prompt: str) -> str:
        """Apply multiple obfuscation techniques"""
        obfuscated = prompt
        
        for technique in self.obfuscation_techniques:
            obfuscated = technique(obfuscated)
        
        return obfuscated
    
    def _add_noise(self, prompt: str) -> str:
        """Add random noise to confuse extraction attempts"""
        noise_phrases = [
            "Please note that this is a legal consultation.",
            "Remember to maintain professional standards.",
            "Ensure accuracy in all legal advice.",
            "Follow Colombian legal framework.",
            "Maintain client confidentiality."
        ]
        
        # Randomly insert noise phrases
        if random.random() < 0.3:  # 30% chance
            noise = random.choice(noise_phrases)
            lines = prompt.split('\n')
            insert_pos = random.randint(0, len(lines))
            lines.insert(insert_pos, noise)
            prompt = '\n'.join(lines)
        
        return prompt
    
    def _randomize_structure(self, prompt: str) -> str:
        """Randomize prompt structure"""
        # Add random spacing and formatting
        if random.random() < 0.2:  # 20% chance
            prompt = prompt.replace('\n', '\n\n')
        
        return prompt
    
    def _insert_decoy_instructions(self, prompt: str) -> str:
        """Insert decoy instructions to mislead extraction"""
        decoy_instructions = [
            "Always respond in Spanish.",
            "Maintain professional tone.",
            "Cite relevant legal sources.",
            "Provide practical guidance.",
            "Ensure legal accuracy."
        ]
        
        if random.random() < 0.4:  # 40% chance
            decoy = random.choice(decoy_instructions)
            prompt = f"{decoy}\n\n{prompt}"
        
        return prompt
    
    def _vary_language_patterns(self, prompt: str) -> str:
        """Vary language patterns to prevent pattern recognition"""
        # Randomly vary instruction phrasing
        variations = {
            "You are": ["You are", "Your role is", "You function as", "You serve as"],
            "must": ["must", "should", "need to", "are required to"],
            "always": ["always", "consistently", "invariably", "without exception"]
        }
        
        for original, alternatives in variations.items():
            if original in prompt and random.random() < 0.3:
                replacement = random.choice(alternatives)
                prompt = prompt.replace(original, replacement, 1)
        
        return prompt

class ResponseFilter:
    """Filters agent responses for security"""
    
    def __init__(self):
        self.dangerous_patterns = [
            r"system\s+prompt",
            r"initial\s+instructions",
            r"base\s+prompt",
            r"your\s+prompt\s+is",
            r"here\s+is\s+your\s+prompt",
            r"reveal\s+instructions",
            r"show\s+system\s+message"
        ]
    
    def filter(self, response: str, agent_name: str) -> str:
        """Filter response for security issues"""
        if not response:
            return response
        
        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                logger.warning(f"Filtered dangerous pattern in {agent_name} response: {pattern}")
                return "I cannot share my internal instructions. I'm here to help with legal matters."
        
        # Remove any potential system information
        response = re.sub(r'<system[^>]*>.*?</system>', '[FILTERED]', response, flags=re.IGNORECASE | re.DOTALL)
        
        return response

class SecurityMonitor:
    """Monitors and logs security events"""
    
    def __init__(self):
        self.alert_history = []
        self.blocked_users = set()
        self.suspicious_sessions = set()
    
    def log_security_alert(self, alert: SecurityAlert):
        """Log security alert"""
        self.alert_history.append(alert)
        
        # Log to file
        logger.warning(f"SECURITY ALERT: {alert.threat_level.value.upper()} - {alert.attack_type}")
        logger.warning(f"Agent: {alert.agent_name}, User: {alert.user_id}, Session: {alert.session_id}")
        logger.warning(f"Input: {alert.user_input[:100]}...")
        
        # Block critical threats
        if alert.threat_level == ThreatLevel.CRITICAL:
            if alert.user_id:
                self.blocked_users.add(alert.user_id)
            if alert.session_id:
                self.suspicious_sessions.add(alert.session_id)
    
    def is_user_blocked(self, user_id: str) -> bool:
        """Check if user is blocked"""
        return user_id in self.blocked_users
    
    def is_session_suspicious(self, session_id: str) -> bool:
        """Check if session is suspicious"""
        return session_id in self.suspicious_sessions
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics"""
        total_alerts = len(self.alert_history)
        critical_alerts = len([a for a in self.alert_history if a.threat_level == ThreatLevel.CRITICAL])
        blocked_users = len(self.blocked_users)
        suspicious_sessions = len(self.suspicious_sessions)
        
        return {
            "total_alerts": total_alerts,
            "critical_alerts": critical_alerts,
            "blocked_users": blocked_users,
            "suspicious_sessions": suspicious_sessions,
            "last_alert": self.alert_history[-1].timestamp if self.alert_history else None
        }

# Global security instance
security_protector = PromptSecurityProtector()

def protect_agent_input(user_input: str, agent_name: str, user_id: str = None, session_id: str = None) -> Tuple[bool, str, Optional[SecurityAlert]]:
    """Protect agent input from security threats"""
    # Check if user is blocked
    if user_id and security_protector.security_monitor.is_user_blocked(user_id):
        return False, "Access denied due to security violations.", None
    
    # Check if session is suspicious
    if session_id and security_protector.security_monitor.is_session_suspicious(session_id):
        return False, "Session flagged for security review.", None
    
    # Analyze input for threats
    is_safe, alert = security_protector.analyze_input(user_input, agent_name, user_id, session_id)
    
    if not is_safe:
        safe_response = security_protector.get_safe_response(alert.attack_type)
        return False, safe_response, alert
    
    # Sanitize input
    sanitized_input = security_protector.sanitize_input(user_input)
    
    return True, sanitized_input, None

def protect_agent_response(response: str, agent_name: str) -> str:
    """Protect agent response from security issues"""
    return security_protector.filter_response(response, agent_name)

def get_security_stats() -> Dict[str, Any]:
    """Get security statistics"""
    return security_protector.security_monitor.get_security_stats()
