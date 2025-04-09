from fastapi import APIRouter
from datetime import datetime, timedelta
import random

router = APIRouter()

@router.get("/api/dashboard-stats")
async def get_dashboard_stats():
    """
    Get real-time dashboard statistics
    """
    return {
        "consultas": random.randint(150, 200),
        "documentos": random.randint(45, 60),
        "contratos": random.randint(85, 100),
        "predicciones": random.randint(230, 250)
    }

@router.get("/api/recent-activity")
async def get_recent_activity():
    """
    Get recent user activity
    """
    activities = [
        {
            "icon": "fa-file-alt",
            "description": "Documento generado: Contrato de Prestación de Servicios",
            "time": "Hace 5 minutos"
        },
        {
            "icon": "fa-search",
            "description": "Búsqueda: Jurisprudencia sobre derecho laboral",
            "time": "Hace 15 minutos"
        },
        {
            "icon": "fa-balance-scale",
            "description": "Predicción de caso: Demanda por despido injustificado",
            "time": "Hace 1 hora"
        },
        {
            "icon": "fa-file-contract",
            "description": "Análisis de contrato: Acuerdo de confidencialidad",
            "time": "Hace 2 horas"
        }
    ]
    return activities 