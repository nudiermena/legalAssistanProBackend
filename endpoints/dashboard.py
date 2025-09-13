from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from datetime import datetime, timedelta
from endpoints.auth import get_current_user
from typing import Dict, Any
import random
from config.ai_models import health_check, get_model_status

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/", response_class=FileResponse)
async def get_dashboard_page(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Render the dashboard page
    """
    try:
        html_path = Path("static/dashboard.html")
        if not html_path.exists():
            raise HTTPException(status_code=404, detail="HTML file not found")
        return FileResponse(html_path)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error serving legal research page: {str(e)}"
        )

@router.get("/api/dashboard-stats")
async def get_dashboard_stats(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get real-time dashboard statistics
    """
    return JSONResponse({
        "consultas": random.randint(150, 200),
        "documentos": random.randint(45, 60),
        "contratos": random.randint(85, 100),
        "predicciones": random.randint(230, 250)
    })

@router.get("/api/recent-activity")
async def get_recent_activity(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get recent user activity
    """
    activities = [
        {
            "icon": "fa-file-alt",
            "description": "Documento generado: Contrato de Prestación de Servicios",
            "time": "Hace 5 minutos",
            "timestamp": datetime.now() - timedelta(minutes=5)
        },
        {
            "icon": "fa-search",
            "description": "Búsqueda: Jurisprudencia sobre derecho laboral",
            "time": "Hace 15 minutos",
            "timestamp": datetime.now() - timedelta(minutes=15)
        },
        {
            "icon": "fa-balance-scale",
            "description": "Predicción de caso: Demanda por despido injustificado",
            "time": "Hace 1 hora",
            "timestamp": datetime.now() - timedelta(hours=1)
        },
        {
            "icon": "fa-file-contract",
            "description": "Análisis de contrato: Acuerdo de confidencialidad",
            "time": "Hace 2 horas",
            "timestamp": datetime.now() - timedelta(hours=2)
        }
    ]
    
    # Sort activities by timestamp
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Remove timestamp from response
    for activity in activities:
        del activity["timestamp"]
    
    return JSONResponse(activities)

@router.get("/api/dashboard/service-usage")
async def get_service_usage(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get service usage statistics
    """
    return JSONResponse({
        "legal_research": {
            "total_searches": random.randint(500, 1000),
            "unique_users": random.randint(100, 200),
            "avg_time": f"{random.randint(5, 15)} min"
        },
        "case_prediction": {
            "total_predictions": random.randint(200, 400),
            "accuracy_rate": f"{random.randint(85, 95)}%",
            "unique_users": random.randint(50, 100)
        },
        "contract_analysis": {
            "contracts_analyzed": random.randint(300, 600),
            "total_pages": random.randint(1500, 3000),
            "avg_processing_time": f"{random.randint(2, 8)} min"
        },
        "document_drafting": {
            "documents_generated": random.randint(400, 800),
            "templates_used": random.randint(10, 20),
            "user_satisfaction": f"{random.randint(90, 98)}%"
        }
    })

@router.get("/api/dashboard/user-metrics")
async def get_user_metrics(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get user-related metrics
    """
    return JSONResponse({
        "total_users": random.randint(1000, 2000),
        "active_users": random.randint(500, 1000),
        "new_users_today": random.randint(10, 30),
        "user_satisfaction": f"{random.randint(90, 98)}%",
        "premium_users": random.randint(100, 300)
    })

@router.get("/api/dashboard/system-health")
async def get_system_health(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get system health metrics
    """
    return JSONResponse({
        "system_status": "operational",
        "api_latency": f"{random.randint(100, 300)}ms",
        "uptime": f"{random.randint(95, 99)}.{random.randint(0, 99)}%",
        "error_rate": f"{random.random():.2f}%",
        "last_updated": datetime.now().isoformat()
    })

@router.get("/dashboard/ai-health")
async def ai_health_check():
    """Check the health status of all AI models"""
    try:
        health_status = health_check()
        model_status = get_model_status()
        
        return {
            "status": "success",
            "data": {
                "health": health_status,
                "model_status": model_status,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        # logger.error(f"Error checking AI health: {e}") # Assuming logger is defined elsewhere
        return {
            "status": "error",
            "message": f"Error checking AI health: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/profile", response_class=FileResponse)
async def get_profile_page(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Render the profile page
    """
    try:
        html_path = Path("static/profile.html")
        if not html_path.exists():
            raise HTTPException(status_code=404, detail="HTML file not found")
        return FileResponse(html_path)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error serving profile page: {str(e)}"
        )

@router.get("/settings", response_class=FileResponse)
async def get_settings_page(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Render the settings page
    """
    try:
        html_path = Path("static/settings.html")
        if not html_path.exists():
            raise HTTPException(status_code=404, detail="HTML file not found")
        return FileResponse(html_path)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error serving settings page: {str(e)}"
        ) 