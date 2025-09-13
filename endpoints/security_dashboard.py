"""
Security dashboard endpoint for monitoring and managing security features.
Provides real-time security status, alerts, and statistics.
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from endpoints.auth import get_current_user
import json
import logging

from config.security import SECURITY_CONFIG, SecurityLevel
from utils.security_monitor import (
    security_monitor,
    SecurityEvent,
    SecurityAlert,
    AlertLevel,
    EventType
)
from middleware.security import get_request_id, get_user_id, get_client_ip
from utils.security_validators import log_security_event

# Security logger
security_logger = logging.getLogger("security")

router = APIRouter(prefix="/security", tags=["security"])

class SecurityStatusResponse(BaseModel):
    """Security status response model"""
    overall_status: str = Field(..., description="Overall security status")
    security_level: str = Field(..., description="Current security level")
    active_alerts: int = Field(..., description="Number of active alerts")
    recent_events: int = Field(..., description="Number of recent events")
    rate_limiting_enabled: bool = Field(..., description="Rate limiting status")
    authentication_enabled: bool = Field(..., description="Authentication status")
    last_updated: datetime = Field(..., description="Last update timestamp")

class SecurityAlertResponse(BaseModel):
    """Security alert response model"""
    alert_id: str = Field(..., description="Alert ID")
    alert_type: str = Field(..., description="Alert type")
    level: str = Field(..., description="Alert level")
    message: str = Field(..., description="Alert message")
    timestamp: datetime = Field(..., description="Alert timestamp")
    event_count: int = Field(..., description="Number of events in alert")
    metadata: Dict[str, Any] = Field(..., description="Alert metadata")

class SecurityEventResponse(BaseModel):
    """Security event response model"""
    event_type: str = Field(..., description="Event type")
    timestamp: datetime = Field(..., description="Event timestamp")
    request_id: str = Field(..., description="Request ID")
    user_id: str = Field(..., description="User ID")
    client_ip: str = Field(..., description="Client IP")
    severity: str = Field(..., description="Event severity")
    source: str = Field(..., description="Event source")

class UserActivityResponse(BaseModel):
    """User activity response model"""
    user_id: str = Field(..., description="User ID")
    total_events: int = Field(..., description="Total events")
    event_counts: Dict[str, int] = Field(..., description="Event type counts")
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")
    time_period_hours: int = Field(..., description="Time period in hours")

class IPActivityResponse(BaseModel):
    """IP activity response model"""
    ip: str = Field(..., description="IP address")
    total_events: int = Field(..., description="Total events")
    event_counts: Dict[str, int] = Field(..., description="Event type counts")
    unique_users: int = Field(..., description="Number of unique users")
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")
    time_period_hours: int = Field(..., description="Time period in hours")

@router.get("/dashboard", response_class=HTMLResponse)
async def get_security_dashboard(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Serve the security dashboard interface"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Dashboard - Legal AI Assistant</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .status-card { transition: all 0.3s ease; }
        .status-card:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        .alert-critical { border-left: 4px solid #dc3545; }
        .alert-high { border-left: 4px solid #fd7e14; }
        .alert-medium { border-left: 4px solid #ffc107; }
        .alert-low { border-left: 4px solid #28a745; }
        .event-log { max-height: 400px; overflow-y: auto; }
        .refresh-btn { cursor: pointer; }
    </style>
</head>
<body>
    <div class="container-fluid mt-4">
        <div class="row">
            <div class="col-12">
                <h2><i class="fas fa-shield-alt"></i> Security Dashboard</h2>
                <p class="text-muted">Real-time security monitoring and alerts</p>
            </div>
        </div>
        
        <!-- Status Cards -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card status-card">
                    <div class="card-body text-center">
                        <i class="fas fa-shield-alt fa-2x text-primary mb-2"></i>
                        <h5 class="card-title">Overall Status</h5>
                        <h3 id="overall-status" class="text-success">Healthy</h3>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card status-card">
                    <div class="card-body text-center">
                        <i class="fas fa-exclamation-triangle fa-2x text-warning mb-2"></i>
                        <h5 class="card-title">Active Alerts</h5>
                        <h3 id="active-alerts" class="text-warning">0</h3>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card status-card">
                    <div class="card-body text-center">
                        <i class="fas fa-chart-line fa-2x text-info mb-2"></i>
                        <h5 class="card-title">Recent Events</h5>
                        <h3 id="recent-events" class="text-info">0</h3>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card status-card">
                    <div class="card-body text-center">
                        <i class="fas fa-sync-alt fa-2x text-secondary mb-2 refresh-btn" onclick="refreshData()"></i>
                        <h5 class="card-title">Last Updated</h5>
                        <h6 id="last-updated" class="text-secondary">Just now</h6>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Alerts and Events -->
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-bell"></i> Recent Alerts</h5>
                    </div>
                    <div class="card-body">
                        <div id="alerts-container" class="event-log">
                            <p class="text-muted">Loading alerts...</p>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-list"></i> Recent Events</h5>
                    </div>
                    <div class="card-body">
                        <div id="events-container" class="event-log">
                            <p class="text-muted">Loading events...</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Activity Summary -->
        <div class="row mt-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-users"></i> User Activity</h5>
                    </div>
                    <div class="card-body">
                        <div id="user-activity-container">
                            <p class="text-muted">Loading user activity...</p>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-network-wired"></i> IP Activity</h5>
                    </div>
                    <div class="card-body">
                        <div id="ip-activity-container">
                            <p class="text-muted">Loading IP activity...</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function refreshData() {
            loadSecurityStatus();
            loadRecentAlerts();
            loadRecentEvents();
            loadUserActivity();
            loadIPActivity();
        }
        
        async function loadSecurityStatus() {
            try {
                const response = await fetch('/security/status');
                const data = await response.json();
                
                document.getElementById('overall-status').textContent = data.overall_status;
                document.getElementById('active-alerts').textContent = data.active_alerts;
                document.getElementById('recent-events').textContent = data.recent_events;
                document.getElementById('last-updated').textContent = new Date(data.last_updated).toLocaleTimeString();
                
                // Update status color
                const statusElement = document.getElementById('overall-status');
                statusElement.className = data.overall_status === 'Healthy' ? 'text-success' : 'text-danger';
            } catch (error) {
                console.error('Error loading security status:', error);
            }
        }
        
        async function loadRecentAlerts() {
            try {
                const response = await fetch('/security/alerts?minutes=60');
                const alerts = await response.json();
                
                const container = document.getElementById('alerts-container');
                if (alerts.length === 0) {
                    container.innerHTML = '<p class="text-success">No alerts in the last hour</p>';
                    return;
                }
                
                container.innerHTML = alerts.map(alert => `
                    <div class="alert alert-${getAlertClass(alert.level)} mb-2">
                        <strong>${alert.alert_type}</strong><br>
                        <small>${alert.message}</small><br>
                        <small class="text-muted">${new Date(alert.timestamp).toLocaleString()}</small>
                    </div>
                `).join('');
            } catch (error) {
                console.error('Error loading alerts:', error);
            }
        }
        
        async function loadRecentEvents() {
            try {
                const response = await fetch('/security/events?minutes=60');
                const events = await response.json();
                
                const container = document.getElementById('events-container');
                if (events.length === 0) {
                    container.innerHTML = '<p class="text-success">No events in the last hour</p>';
                    return;
                }
                
                container.innerHTML = events.map(event => `
                    <div class="border-bottom pb-2 mb-2">
                        <strong>${event.event_type}</strong><br>
                        <small>User: ${event.user_id || 'Anonymous'}</small><br>
                        <small>IP: ${event.client_ip}</small><br>
                        <small class="text-muted">${new Date(event.timestamp).toLocaleString()}</small>
                    </div>
                `).join('');
            } catch (error) {
                console.error('Error loading events:', error);
            }
        }
        
        async function loadUserActivity() {
            try {
                const response = await fetch('/security/user-activity');
                const activity = await response.json();
                
                const container = document.getElementById('user-activity-container');
                if (activity.length === 0) {
                    container.innerHTML = '<p class="text-muted">No user activity data</p>';
                    return;
                }
                
                container.innerHTML = activity.map(user => `
                    <div class="border-bottom pb-2 mb-2">
                        <strong>${user.user_id}</strong><br>
                        <small>Events: ${user.total_events}</small><br>
                        <small>Last activity: ${user.last_activity ? new Date(user.last_activity).toLocaleString() : 'Never'}</small>
                    </div>
                `).join('');
            } catch (error) {
                console.error('Error loading user activity:', error);
            }
        }
        
        async function loadIPActivity() {
            try {
                const response = await fetch('/security/ip-activity');
                const activity = await response.json();
                
                const container = document.getElementById('ip-activity-container');
                if (activity.length === 0) {
                    container.innerHTML = '<p class="text-muted">No IP activity data</p>';
                    return;
                }
                
                container.innerHTML = activity.map(ip => `
                    <div class="border-bottom pb-2 mb-2">
                        <strong>${ip.ip}</strong><br>
                        <small>Events: ${ip.total_events}</small><br>
                        <small>Users: ${ip.unique_users}</small><br>
                        <small>Last activity: ${ip.last_activity ? new Date(ip.last_activity).toLocaleString() : 'Never'}</small>
                    </div>
                `).join('');
            } catch (error) {
                console.error('Error loading IP activity:', error);
            }
        }
        
        function getAlertClass(level) {
            switch (level) {
                case 'critical': return 'danger';
                case 'high': return 'warning';
                case 'medium': return 'info';
                case 'low': return 'success';
                default: return 'secondary';
            }
        }
        
        // Load data on page load
        document.addEventListener('DOMContentLoaded', refreshData);
        
        // Auto-refresh every 30 seconds
        setInterval(refreshData, 30000);
    </script>
</body>
</html>
"""
    
    return HTMLResponse(content=html_content)

@router.get("/status", response_model=SecurityStatusResponse)
async def get_security_status(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get overall security status"""
    try:
        # Get recent alerts and events
        recent_alerts = security_monitor.get_recent_alerts(minutes=60)
        recent_events = security_monitor.get_recent_events(minutes=60)
        
        # Determine overall status
        critical_alerts = [alert for alert in recent_alerts if alert.level == AlertLevel.CRITICAL]
        high_alerts = [alert for alert in recent_alerts if alert.level == AlertLevel.HIGH]
        
        if critical_alerts:
            overall_status = "Critical"
        elif high_alerts:
            overall_status = "Warning"
        else:
            overall_status = "Healthy"
        
        return SecurityStatusResponse(
            overall_status=overall_status,
            security_level=SECURITY_CONFIG.environment.value,
            active_alerts=len(recent_alerts),
            recent_events=len(recent_events),
            rate_limiting_enabled=True,
            authentication_enabled=True,
            last_updated=datetime.utcnow()
        )
    except Exception as e:
        log_security_event("security_status_error", {"error": str(e)}, severity="ERROR")
        raise HTTPException(status_code=500, detail="Error retrieving security status")

@router.get("/alerts", response_model=List[SecurityAlertResponse])
async def get_recent_alerts(
    minutes: int = Query(60, description="Minutes to look back"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get recent security alerts"""
    try:
        alerts = security_monitor.get_recent_alerts(minutes=minutes)
        
        return [
            SecurityAlertResponse(
                alert_id=alert.alert_id,
                alert_type=alert.alert_type,
                level=alert.level.value,
                message=alert.message,
                timestamp=alert.timestamp,
                event_count=len(alert.events),
                metadata=alert.metadata
            )
            for alert in alerts
        ]
    except Exception as e:
        log_security_event("security_alerts_error", {"error": str(e)}, severity="ERROR")
        raise HTTPException(status_code=500, detail="Error retrieving security alerts")

@router.get("/events", response_model=List[SecurityEventResponse])
async def get_recent_events(
    minutes: int = Query(60, description="Minutes to look back"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get recent security events"""
    try:
        events = security_monitor.get_recent_events(minutes=minutes)
        
        return [
            SecurityEventResponse(
                event_type=event.event_type,
                timestamp=event.timestamp,
                request_id=event.request_id,
                user_id=event.user_id,
                client_ip=event.client_ip,
                severity=event.severity,
                source=event.source
            )
            for event in events
        ]
    except Exception as e:
        log_security_event("security_events_error", {"error": str(e)}, severity="ERROR")
        raise HTTPException(status_code=500, detail="Error retrieving security events")

@router.get("/user-activity", response_model=List[UserActivityResponse])
async def get_user_activity(
    hours: int = Query(24, description="Hours to look back"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get user activity summary"""
    try:
        # Get unique users from recent events
        recent_events = security_monitor.get_recent_events(minutes=hours * 60)
        user_ids = set(event.user_id for event in recent_events if event.user_id)
        
        activity_summaries = []
        for user_id in user_ids:
            summary = security_monitor.get_user_activity_summary(user_id, hours=hours)
            activity_summaries.append(UserActivityResponse(**summary))
        
        return activity_summaries
    except Exception as e:
        log_security_event("user_activity_error", {"error": str(e)}, severity="ERROR")
        raise HTTPException(status_code=500, detail="Error retrieving user activity")

@router.get("/ip-activity", response_model=List[IPActivityResponse])
async def get_ip_activity(
    hours: int = Query(24, description="Hours to look back"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get IP activity summary"""
    try:
        # Get unique IPs from recent events
        recent_events = security_monitor.get_recent_events(minutes=hours * 60)
        ips = set(event.client_ip for event in recent_events if event.client_ip)
        
        activity_summaries = []
        for ip in ips:
            summary = security_monitor.get_ip_activity_summary(ip, hours=hours)
            activity_summaries.append(IPActivityResponse(**summary))
        
        return activity_summaries
    except Exception as e:
        log_security_event("ip_activity_error", {"error": str(e)}, severity="ERROR")
        raise HTTPException(status_code=500, detail="Error retrieving IP activity")

@router.get("/config")
async def get_security_config(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current security configuration (admin only)"""
    try:
        # In production, this should check for admin privileges
        return {
            "security_level": SECURITY_CONFIG.environment.value,
            "rate_limits": {
                "per_minute": SECURITY_CONFIG.rate_limit.requests_per_minute,
                "per_hour": SECURITY_CONFIG.rate_limit.requests_per_hour,
                "per_day": SECURITY_CONFIG.rate_limit.requests_per_day
            },
            "file_upload": {
                "max_size": SECURITY_CONFIG.max_file_size,
                "allowed_types": SECURITY_CONFIG.allowed_file_types,
                "scan_uploads": SECURITY_CONFIG.scan_uploads
            },
            "authentication": {
                "enabled": True,
                "api_key_header": SECURITY_CONFIG.api_key_header
            },
            "monitoring": {
                "thresholds": security_monitor.thresholds
            }
        }
    except Exception as e:
        log_security_event("security_config_error", {"error": str(e)}, severity="ERROR")
        raise HTTPException(status_code=500, detail="Error retrieving security configuration") 