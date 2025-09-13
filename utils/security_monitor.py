"""
Security monitoring and alerting system for the Legal AI Assistant API.
Tracks security events, detects anomalies, and generates alerts.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta, timezone
from collections import defaultdict, deque
import logging
from dataclasses import dataclass, asdict
from enum import Enum

from config.security import SECURITY_CONFIG, SecurityLevel
from middleware.security import get_request_id, get_user_id, get_client_ip

# Security logger
security_logger = logging.getLogger("security")

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class AlertLevel(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class EventType(Enum):
    """Security event types"""
    AUTHENTICATION_FAILURE = "authentication_failure"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_FILE_UPLOAD = "invalid_file_upload"
    MALICIOUS_CONTENT = "malicious_content"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    API_ERROR = "api_error"
    UNEXPECTED_ERROR = "unexpected_error"
    BRUTE_FORCE_ATTEMPT = "brute_force_attempt"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"

@dataclass
class SecurityEvent:
    """Security event data structure"""
    event_type: str
    timestamp: datetime
    request_id: str
    user_id: str
    client_ip: str
    details: Dict[str, Any] = None
    severity: str = "INFO"
    source: str = "api"
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with datetime serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

@dataclass
class SecurityAlert:
    """Security alert data structure"""
    alert_id: str
    alert_type: str
    level: AlertLevel
    message: str
    timestamp: datetime
    events: List[SecurityEvent] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.events is None:
            self.events = []
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with datetime serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['level'] = self.level.value
        data['events'] = [event.to_dict() for event in self.events]
        return data

# Alert handlers
def log_alert_handler(alert: SecurityAlert):
    """Default alert handler that logs alerts"""
    security_logger.warning(f"SECURITY ALERT [{alert.level.value.upper()}]: {alert.message}")
    security_logger.warning(f"Alert ID: {alert.alert_id}, Type: {alert.alert_type}")
    security_logger.warning(f"Events: {len(alert.events)}, Metadata: {alert.metadata}")

def email_alert_handler(alert: SecurityAlert):
    """Email alert handler (placeholder for production implementation)"""
    if alert.level in [AlertLevel.HIGH, AlertLevel.CRITICAL]:
        # In production, this would send an email
        security_logger.critical(f"CRITICAL ALERT - Email notification would be sent: {alert.message}")

class SecurityMonitor:
    """Main security monitoring class"""
    
    def __init__(self):
        """Initialize the security monitor"""
        self.events = deque(maxlen=10000)
        self.alerts = deque(maxlen=1000)
        self.user_activity = defaultdict(lambda: deque(maxlen=1000))
        self.ip_activity = defaultdict(lambda: deque(maxlen=1000))
        self.alert_handlers = [log_alert_handler]
        
        # Security thresholds
        self.thresholds = {
            "auth_failures_per_minute": 5,
            "rate_limit_violations_per_minute": 10,
            "malicious_content_per_minute": 3,
            "api_errors_per_minute": 20,
            "requests_per_minute_per_ip": 100,
            "requests_per_minute_per_user": 50
        }
        
        # Start monitoring tasks
        self.monitoring_task = None
        self._monitoring_started = False
    
    # Static methods for easy access
    @staticmethod
    def log_security_event(
        event_type: str,
        user_id: str = None,
        details: Dict[str, Any] = None,
        severity: str = "INFO",
        source: str = "api"
    ):
        """Static method to log a security event"""
        event = SecurityEvent(
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            request_id=get_request_id(),
            user_id=user_id or get_user_id(),
            client_ip=get_client_ip(),
            details=details or {},
            severity=severity,
            source=source
        )
        
        security_monitor.add_event(event)
        
        # Also log to regular security logger using the to_dict method
        try:
            event_dict = event.to_dict()
            if severity == "ERROR":
                security_logger.error(f"Security event: {json.dumps(event_dict, cls=DateTimeEncoder)}")
            elif severity == "WARNING":
                security_logger.warning(f"Security event: {json.dumps(event_dict, cls=DateTimeEncoder)}")
            else:
                security_logger.info(f"Security event: {json.dumps(event_dict, cls=DateTimeEncoder)}")
        except Exception as e:
            # Fallback logging if JSON serialization fails
            security_logger.error(f"Error serializing security event: {e}")
            security_logger.info(f"Security event: {event_type} - {severity} - User: {user_id}")
    
    @staticmethod
    def log_document_generation(
        user_id: str,
        document_type: str,
        complexity: str = "standard",
        industry: str = "general",
        client_ip: str = None
    ):
        """Static method to log document generation events"""
        SecurityMonitor.log_security_event(
            event_type="document_generation",
            user_id=user_id,
            details={
                "document_type": document_type,
                "complexity": complexity,
                "industry": industry,
                "client_ip": client_ip or get_client_ip()
            },
            severity="INFO",
            source="document_drafting"
        )
    
    @staticmethod
    def log_authentication_success(
        user_id: str,
        email: str = None,
        username: str = None,
        client_ip: str = None,
        is_admin: bool = False
    ):
        """Static method to log successful authentication"""
        SecurityMonitor.log_security_event(
            event_type="user_authentication_success",
            user_id=user_id,
            details={
                "email": email,
                "username": username,
                "client_ip": client_ip or get_client_ip(),
                "is_admin": is_admin
            },
            severity="INFO",
            source="authentication"
        )
    
    @staticmethod
    def log_authentication_failure(
        user_id: str = None,
        email: str = None,
        reason: str = None,
        client_ip: str = None
    ):
        """Static method to log failed authentication"""
        SecurityMonitor.log_security_event(
            event_type="user_authentication_failure",
            user_id=user_id or "unknown",
            details={
                "email": email,
                "reason": reason,
                "client_ip": client_ip or get_client_ip()
            },
            severity="WARNING",
            source="authentication"
        )
    
    @staticmethod
    def log_rate_limit_exceeded(
        user_id: str = None,
        client_ip: str = None,
        endpoint: str = None,
        limit: int = None
    ):
        """Static method to log rate limit violations"""
        SecurityMonitor.log_security_event(
            event_type="rate_limit_exceeded",
            user_id=user_id or get_user_id(),
            details={
                "client_ip": client_ip or get_client_ip(),
                "endpoint": endpoint,
                "limit": limit
            },
            severity="WARNING",
            source="rate_limiting"
        )
    
    @staticmethod
    def log_api_error(
        error_type: str,
        error_message: str,
        endpoint: str = None,
        user_id: str = None,
        client_ip: str = None
    ):
        """Static method to log API errors"""
        SecurityMonitor.log_security_event(
            event_type="api_error",
            user_id=user_id or get_user_id(),
            details={
                "error_type": error_type,
                "error_message": error_message,
                "endpoint": endpoint,
                "client_ip": client_ip or get_client_ip()
            },
            severity="ERROR",
            source="api"
        )
    
    @staticmethod
    def log_suspicious_activity(
        activity_type: str,
        details: Dict[str, Any],
        user_id: str = None,
        client_ip: str = None
    ):
        """Static method to log suspicious activity"""
        SecurityMonitor.log_security_event(
            event_type="suspicious_activity",
            user_id=user_id or get_user_id(),
            details={
                "activity_type": activity_type,
                "client_ip": client_ip or get_client_ip(),
                **details
            },
            severity="WARNING",
            source="security_monitoring"
        )
    
    @staticmethod
    def get_recent_events(minutes: int = 60) -> List[SecurityEvent]:
        """Static method to get recent events"""
        return security_monitor.get_recent_events(minutes)
    
    @staticmethod
    def get_recent_alerts(minutes: int = 60) -> List[SecurityAlert]:
        """Static method to get recent alerts"""
        return security_monitor.get_recent_alerts(minutes)
    
    @staticmethod
    def get_user_activity_summary(user_id: str, hours: int = 24) -> Dict[str, Any]:
        """Static method to get user activity summary"""
        return security_monitor.get_user_activity_summary(user_id, hours)
    
    @staticmethod
    def get_ip_activity_summary(ip: str, hours: int = 24) -> Dict[str, Any]:
        """Static method to get IP activity summary"""
        return security_monitor.get_ip_activity_summary(ip, hours)
    
    def start_monitoring(self):
        """Start the monitoring background task"""
        if self.monitoring_task is None and not self._monitoring_started:
            try:
                # Only start if there's a running event loop
                loop = asyncio.get_running_loop()
                self.monitoring_task = loop.create_task(self._monitor_loop())
                self._monitoring_started = True
                security_logger.info("Security monitoring started")
            except RuntimeError:
                # No running event loop, will start when app starts
                security_logger.info("Security monitoring will start when event loop is available")
    
    async def ensure_monitoring_started(self):
        """Ensure monitoring is started (called from FastAPI startup)"""
        if not self._monitoring_started:
            self.start_monitoring()
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while True:
            try:
                await self._check_anomalies()
                await self._cleanup_old_data()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                security_logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)
    
    def add_event(self, event: SecurityEvent):
        """Add a security event to monitoring"""
        self.events.append(event)
        
        # Track user activity
        if event.user_id:
            self.user_activity[event.user_id].append(event)
        
        # Track IP activity
        if event.client_ip:
            self.ip_activity[event.client_ip].append(event)
        
        # Check for immediate alerts
        self._check_immediate_alerts(event)
    
    def _check_immediate_alerts(self, event: SecurityEvent):
        """Check for events that should trigger immediate alerts"""
        immediate_alerts = {
            EventType.AUTHENTICATION_FAILURE: AlertLevel.HIGH,
            EventType.MALICIOUS_CONTENT: AlertLevel.HIGH,
            EventType.SQL_INJECTION_ATTEMPT: AlertLevel.CRITICAL,
            EventType.XSS_ATTEMPT: AlertLevel.HIGH,
            EventType.BRUTE_FORCE_ATTEMPT: AlertLevel.CRITICAL
        }
        
        if event.event_type in immediate_alerts:
            self._create_alert(
                alert_type=f"immediate_{event.event_type}",
                level=immediate_alerts[event.event_type],
                message=f"Immediate alert: {event.event_type} detected",
                events=[event],
                metadata={"triggered_by": event.event_type}
            )
    
    async def _check_anomalies(self):
        """Check for anomalies in recent activity"""
        current_time = datetime.now(timezone.utc)
        one_minute_ago = current_time - timedelta(minutes=1)
        
        # Get recent events
        recent_events = [
            event for event in self.events
            if event.timestamp >= one_minute_ago
        ]
        
        # Check authentication failures
        auth_failures = [
            event for event in recent_events
            if event.event_type == EventType.AUTHENTICATION_FAILURE.value
        ]
        
        if len(auth_failures) >= self.thresholds["auth_failures_per_minute"]:
            self._create_alert(
                alert_type="high_auth_failures",
                level=AlertLevel.MEDIUM,
                message=f"High number of authentication failures: {len(auth_failures)} in the last minute",
                events=auth_failures,
                metadata={"count": len(auth_failures), "threshold": self.thresholds["auth_failures_per_minute"]}
            )
        
        # Check rate limit violations
        rate_limit_violations = [
            event for event in recent_events
            if event.event_type == EventType.RATE_LIMIT_EXCEEDED.value
        ]
        
        if len(rate_limit_violations) >= self.thresholds["rate_limit_violations_per_minute"]:
            self._create_alert(
                alert_type="high_rate_limit_violations",
                level=AlertLevel.MEDIUM,
                message=f"High number of rate limit violations: {len(rate_limit_violations)} in the last minute",
                events=rate_limit_violations,
                metadata={"count": len(rate_limit_violations), "threshold": self.thresholds["rate_limit_violations_per_minute"]}
            )
        
        # Check malicious content
        malicious_content = [
            event for event in recent_events
            if event.event_type == EventType.MALICIOUS_CONTENT.value
        ]
        
        if len(malicious_content) >= self.thresholds["malicious_content_per_minute"]:
            self._create_alert(
                alert_type="high_malicious_content",
                level=AlertLevel.HIGH,
                message=f"High number of malicious content attempts: {len(malicious_content)} in the last minute",
                events=malicious_content,
                metadata={"count": len(malicious_content), "threshold": self.thresholds["malicious_content_per_minute"]}
            )
        
        # Check API errors
        api_errors = [
            event for event in recent_events
            if event.event_type == EventType.API_ERROR.value
        ]
        
        if len(api_errors) >= self.thresholds["api_errors_per_minute"]:
            self._create_alert(
                alert_type="high_api_errors",
                level=AlertLevel.MEDIUM,
                message=f"High number of API errors: {len(api_errors)} in the last minute",
                events=api_errors,
                metadata={"count": len(api_errors), "threshold": self.thresholds["api_errors_per_minute"]}
            )
        
        # Check per-IP activity
        ip_counts = defaultdict(int)
        for event in recent_events:
            ip_counts[event.client_ip] += 1
        
        for ip, count in ip_counts.items():
            if count >= self.thresholds["requests_per_minute_per_ip"]:
                self._create_alert(
                    alert_type="high_ip_activity",
                    level=AlertLevel.MEDIUM,
                    message=f"High activity from IP {ip}: {count} requests in the last minute",
                    events=[event for event in recent_events if event.client_ip == ip],
                    metadata={"ip": ip, "count": count, "threshold": self.thresholds["requests_per_minute_per_ip"]}
                )
        
        # Check per-user activity
        user_counts = defaultdict(int)
        for event in recent_events:
            if event.user_id:
                user_counts[event.user_id] += 1
        
        for user_id, count in user_counts.items():
            if count >= self.thresholds["requests_per_minute_per_user"]:
                self._create_alert(
                    alert_type="high_user_activity",
                    level=AlertLevel.MEDIUM,
                    message=f"High activity from user {user_id}: {count} requests in the last minute",
                    events=[event for event in recent_events if event.user_id == user_id],
                    metadata={"user_id": user_id, "count": count, "threshold": self.thresholds["requests_per_minute_per_user"]}
                )
    
    def _create_alert(self, alert_type: str, level: AlertLevel, message: str, events: List[SecurityEvent], metadata: Dict[str, Any]):
        """Create and store a security alert"""
        alert = SecurityAlert(
            alert_id=f"alert_{int(time.time())}_{len(self.alerts)}",
            alert_type=alert_type,
            level=level,
            message=message,
            timestamp=datetime.now(timezone.utc),
            events=events,
            metadata=metadata
        )
        
        self.alerts.append(alert)
        
        # Log the alert
        security_logger.warning(f"Security alert: {alert.alert_type} - {alert.message}")
        
        # Call alert handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                security_logger.error(f"Error in alert handler: {e}")
    
    def add_alert_handler(self, handler: Callable[[SecurityAlert], None]):
        """Add an alert handler function"""
        self.alert_handlers.append(handler)
    
    async def _cleanup_old_data(self):
        """Clean up old events and alerts"""
        current_time = datetime.now(timezone.utc)
        cutoff_time = current_time - timedelta(hours=24)  # Keep 24 hours of data
        
        # Clean up old events
        self.events = deque(
            [event for event in self.events if event.timestamp >= cutoff_time],
            maxlen=10000
        )
        
        # Clean up old alerts
        self.alerts = deque(
            [alert for alert in self.alerts if alert.timestamp >= cutoff_time],
            maxlen=1000
        )
        
        # Clean up old user activity
        for user_id in list(self.user_activity.keys()):
            self.user_activity[user_id] = deque(
                [event for event in self.user_activity[user_id] if event.timestamp >= cutoff_time],
                maxlen=1000
            )
        
        # Clean up old IP activity
        for ip in list(self.ip_activity.keys()):
            self.ip_activity[ip] = deque(
                [event for event in self.ip_activity[ip] if event.timestamp >= cutoff_time],
                maxlen=1000
            )
    
    def get_recent_events(self, minutes: int = 60) -> List[SecurityEvent]:
        """Get events from the last N minutes"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        return [event for event in self.events if event.timestamp >= cutoff_time]
    
    def get_recent_alerts(self, minutes: int = 60) -> List[SecurityAlert]:
        """Get alerts from the last N minutes"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        return [alert for alert in self.alerts if alert.timestamp >= cutoff_time]
    
    def get_user_activity_summary(self, user_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get activity summary for a specific user"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        user_events = [
            event for event in self.user_activity.get(user_id, [])
            if event.timestamp >= cutoff_time
        ]
        
        event_counts = defaultdict(int)
        for event in user_events:
            event_counts[event.event_type] += 1
        
        return {
            "user_id": user_id,
            "total_events": len(user_events),
            "event_counts": dict(event_counts),
            "last_activity": user_events[-1].timestamp.isoformat() if user_events else None,
            "time_period_hours": hours
        }
    
    def get_ip_activity_summary(self, ip: str, hours: int = 24) -> Dict[str, Any]:
        """Get activity summary for a specific IP"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        ip_events = [
            event for event in self.ip_activity.get(ip, [])
            if event.timestamp >= cutoff_time
        ]
        
        event_counts = defaultdict(int)
        user_counts = defaultdict(int)
        for event in ip_events:
            event_counts[event.event_type] += 1
            if event.user_id:
                user_counts[event.user_id] += 1
        
        return {
            "ip": ip,
            "total_events": len(ip_events),
            "event_counts": dict(event_counts),
            "unique_users": len(user_counts),
            "last_activity": ip_events[-1].timestamp.isoformat() if ip_events else None,
            "time_period_hours": hours
        }

# Global security monitor instance
security_monitor = SecurityMonitor()

# Utility functions for easy event logging
def log_security_event_monitored(
    event_type: str,
    details: Dict[str, Any],
    severity: str = "INFO",
    source: str = "api"
):
    """Log a security event with monitoring"""
    event = SecurityEvent(
        event_type=event_type,
        timestamp=datetime.now(timezone.utc),
        request_id=get_request_id(),
        user_id=get_user_id(),
        client_ip=get_client_ip(),
        details=details,
        severity=severity,
        source=source
    )
    
    security_monitor.add_event(event)
    
    # Also log to regular security logger using the to_dict method
    try:
        event_dict = event.to_dict()
        if severity == "ERROR":
            security_logger.error(f"Security event: {json.dumps(event_dict, cls=DateTimeEncoder)}")
        elif severity == "WARNING":
            security_logger.warning(f"Security event: {json.dumps(event_dict, cls=DateTimeEncoder)}")
        else:
            security_logger.info(f"Security event: {json.dumps(event_dict, cls=DateTimeEncoder)}")
    except Exception as e:
        # Fallback logging if JSON serialization fails
        security_logger.error(f"Error serializing security event: {e}")
        security_logger.info(f"Security event: {event_type} - {severity}")

# Export functions and classes
__all__ = [
    "SecurityMonitor",
    "SecurityEvent",
    "SecurityAlert",
    "AlertLevel",
    "EventType",
    "security_monitor",
    "log_security_event_monitored",
    "DateTimeEncoder"
] 