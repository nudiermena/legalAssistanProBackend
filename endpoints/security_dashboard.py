"""
Security Dashboard Endpoint
Provides security monitoring and statistics for the legal AI system
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from endpoints.auth import get_current_user
from utils.security_protection import get_security_stats
from middleware.security_middleware import get_security_dashboard_data
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/security", tags=["security"])

class SecurityStatsResponse(BaseModel):
    """Security statistics response model"""
    total_alerts: int
    critical_alerts: int
    blocked_users: int
    suspicious_sessions: int
    last_alert: Optional[str]
    blocked_ips: int
    suspicious_patterns: int
    rate_limits: Dict[str, Any]
    timestamp: str

class SecurityAlertResponse(BaseModel):
    """Security alert response model"""
    timestamp: str
    threat_level: str
    attack_type: str
    agent_name: str
    user_id: Optional[str]
    session_id: Optional[str]
    input_preview: str
    details: Dict[str, Any]

@router.get("/dashboard", response_model=SecurityStatsResponse)
async def get_security_dashboard(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get security dashboard statistics"""
    try:
        # Check if user has admin privileges
        if not current_user.get("is_admin", False):
            raise HTTPException(
                status_code=403,
                detail="Access denied. Admin privileges required."
            )
        
        # Get security statistics
        stats = get_security_stats()
        dashboard_data = get_security_dashboard_data()
        
        response = SecurityStatsResponse(
            total_alerts=stats["total_alerts"],
            critical_alerts=stats["critical_alerts"],
            blocked_users=stats["blocked_users"],
            suspicious_sessions=stats["suspicious_sessions"],
            last_alert=stats["last_alert"].isoformat() if stats["last_alert"] else None,
            blocked_ips=dashboard_data["blocked_ips"],
            suspicious_patterns=dashboard_data["suspicious_patterns"],
            rate_limits=dashboard_data["rate_limits"],
            timestamp=datetime.now().isoformat()
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting security dashboard: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving security statistics"
        )

@router.get("/alerts", response_model=List[SecurityAlertResponse])
async def get_security_alerts(
    limit: int = 50,
    threat_level: Optional[str] = None,
    agent_name: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get security alerts with filtering"""
    try:
        # Check if user has admin privileges
        if not current_user.get("is_admin", False):
            raise HTTPException(
                status_code=403,
                detail="Access denied. Admin privileges required."
            )
        
        # Get alerts from security monitor
        from utils.security_protection import security_protector
        alerts = security_protector.security_monitor.alert_history
        
        # Apply filters
        filtered_alerts = []
        for alert in alerts[-limit:]:  # Get latest alerts
            if threat_level and alert.threat_level.value != threat_level:
                continue
            if agent_name and alert.agent_name != agent_name:
                continue
            
            filtered_alerts.append(SecurityAlertResponse(
                timestamp=alert.timestamp.isoformat(),
                threat_level=alert.threat_level.value,
                attack_type=alert.attack_type,
                agent_name=alert.agent_name,
                user_id=alert.user_id,
                session_id=alert.session_id,
                input_preview=alert.user_input[:100] + "..." if len(alert.user_input) > 100 else alert.user_input,
                details=alert.details
            ))
        
        return filtered_alerts
        
    except Exception as e:
        logger.error(f"Error getting security alerts: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving security alerts"
        )

@router.post("/block-user")
async def block_user(
    user_id: str,
    reason: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Block a user for security violations"""
    try:
        # Check if user has admin privileges
        if not current_user.get("is_admin", False):
            raise HTTPException(
                status_code=403,
                detail="Access denied. Admin privileges required."
            )
        
        # Block user
        from utils.security_protection import security_protector
        security_protector.security_monitor.blocked_users.add(user_id)
        
        logger.warning(f"User {user_id} blocked by admin {current_user.get('user_id')} for: {reason}")
        
        return {
            "status": "success",
            "message": f"User {user_id} has been blocked",
            "reason": reason,
            "blocked_by": current_user.get("user_id"),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error blocking user: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error blocking user"
        )

@router.post("/unblock-user")
async def unblock_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Unblock a user"""
    try:
        # Check if user has admin privileges
        if not current_user.get("is_admin", False):
            raise HTTPException(
                status_code=403,
                detail="Access denied. Admin privileges required."
            )
        
        # Unblock user
        from utils.security_protection import security_protector
        security_protector.security_monitor.blocked_users.discard(user_id)
        
        logger.info(f"User {user_id} unblocked by admin {current_user.get('user_id')}")
        
        return {
            "status": "success",
            "message": f"User {user_id} has been unblocked",
            "unblocked_by": current_user.get("user_id"),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error unblocking user: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error unblocking user"
        )

@router.get("/threat-patterns")
async def get_threat_patterns(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get detected threat patterns"""
    try:
        # Check if user has admin privileges
        if not current_user.get("is_admin", False):
            raise HTTPException(
                status_code=403,
                detail="Access denied. Admin privileges required."
            )
        
        # Get threat patterns from security protector
        from utils.security_protection import security_protector
        patterns = security_protector.attack_patterns
        
        return {
            "attack_patterns": patterns,
            "total_patterns": sum(len(patterns[category]) for category in patterns),
            "categories": list(patterns.keys()),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting threat patterns: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving threat patterns"
        )

@router.get("/system-health")
async def get_system_health(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get system security health status"""
    try:
        # Check if user has admin privileges
        if not current_user.get("is_admin", False):
            raise HTTPException(
                status_code=403,
                detail="Access denied. Admin privileges required."
            )
        
        # Get security statistics
        stats = get_security_stats()
        dashboard_data = get_security_dashboard_data()
        
        # Calculate health score
        total_alerts = stats["total_alerts"]
        critical_alerts = stats["critical_alerts"]
        blocked_users = stats["blocked_users"]
        
        # Health score calculation (0-100)
        health_score = 100
        if total_alerts > 0:
            health_score -= min(30, (total_alerts / 10) * 5)  # Reduce for total alerts
        if critical_alerts > 0:
            health_score -= min(50, critical_alerts * 10)  # Reduce for critical alerts
        if blocked_users > 0:
            health_score -= min(20, blocked_users * 5)  # Reduce for blocked users
        
        health_score = max(0, health_score)
        
        # Determine health status
        if health_score >= 80:
            status = "healthy"
        elif health_score >= 60:
            status = "warning"
        else:
            status = "critical"
        
        return {
            "health_score": round(health_score, 1),
            "status": status,
            "total_alerts": total_alerts,
            "critical_alerts": critical_alerts,
            "blocked_users": blocked_users,
            "blocked_ips": dashboard_data["blocked_ips"],
            "suspicious_sessions": dashboard_data["suspicious_sessions"],
            "recommendations": [
                "Monitor critical alerts closely" if critical_alerts > 0 else None,
                "Review blocked users for false positives" if blocked_users > 0 else None,
                "Investigate suspicious patterns" if dashboard_data["suspicious_patterns"] > 0 else None
            ],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting system health: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving system health"
        )