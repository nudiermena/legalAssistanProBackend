#!/usr/bin/env python3
"""
Request a Demo Endpoint
Accepts demo requests from frontend, renders email using static/demo-confirmation.html,
and sends via Resend.
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
import resend


logger = logging.getLogger(__name__)

# Load environment variables (with error handling)
try:
    load_dotenv()
except Exception as e:
    logger.warning(f"Could not load .env file: {e}")

# Ensure Resend API configuration
if not os.getenv("RESEND_API_KEY"):
    os.environ["RESEND_API_KEY"] = "re_YdBnq9ZN_KEnQFxmq3xwaVDfdYhrzugxp"
if not os.getenv("RESEND_FROM_EMAIL"):
    os.environ["RESEND_FROM_EMAIL"] = "noreply@miasistentelegalia.com"
if not os.getenv("RESEND_REPLY_TO_EMAIL"):
    os.environ["RESEND_REPLY_TO_EMAIL"] = "support@miasistentelegalia.com"

resend.api_key = os.getenv("RESEND_API_KEY")

router = APIRouter(prefix="/api/request-demo", tags=["Request Demo"])


class DemoRequestItem(BaseModel):
    full_name: str
    email: EmailStr
    company: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    preferred_date: Optional[str] = None  # ISO date string
    preferred_time: Optional[str] = None
    interests: Optional[str] = None
    message: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = None


"""
In Pydantic v2, prefer typing directly as List[DemoRequestItem] instead of RootModel with __root__
"""


def _read_template() -> str:
    base_dir = Path(__file__).resolve().parent.parent
    template_path = base_dir / "static" / "demo-confirmation.html"
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found at {template_path}")
    return template_path.read_text(encoding="utf-8")


def _format_date(date_str: Optional[str]) -> str:
    if not date_str:
        return "Por confirmar"
    try:
        # Accept YYYY-MM-DD
        dt = datetime.fromisoformat(date_str)
    except ValueError:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            return date_str
    months = [
        "enero","febrero","marzo","abril","mayo","junio",
        "julio","agosto","septiembre","octubre","noviembre","diciembre"
    ]
    return f"{dt.day} de {months[dt.month-1]} de {dt.year}"


def _fill_template(html: str, item: DemoRequestItem) -> str:
    replacements = {
        "{{fullName}}": item.full_name,
        "{{preferredDateFormatted}}": _format_date(item.preferred_date),
        "{{preferredTime}}": item.preferred_time or "Por confirmar",
        "{{company}}": item.company or "-",
        "{{role}}": item.role or "-",
        "{{dashboardUrl}}": os.getenv("DASHBOARD_URL", "https://miasistentelegalia.com/dashboard"),
        "{{replyToEmail}}": os.getenv("RESEND_REPLY_TO_EMAIL", "support@miasistentelegalia.com"),
        "{{year}}": str(datetime.utcnow().year),
    }
    for key, value in replacements.items():
        html = html.replace(key, value)
    return html


def _sanitize_tag_value(value: str) -> str:
    try:
        import unicodedata
        import re
        normalized = unicodedata.normalize('NFKD', value or "")
        ascii_value = normalized.encode('ASCII', 'ignore').decode('ASCII')
        ascii_value = ascii_value.replace(' ', '_')
        sanitized = re.sub(r'[^a-zA-Z0-9_\-]', '', ascii_value)
        return sanitized[:50] if sanitized else "value"
    except Exception:
        return "value"

def _normalize_item_dict(data: dict) -> dict:
    # Unwrap common wrapper
    if isinstance(data, dict) and "demoData" in data and isinstance(data["demoData"], dict):
        data = data["demoData"]

    # Support both camelCase and snake_case keys
    def g(*keys, default=None):
        for k in keys:
            if k in data and data[k] is not None:
                return data[k]
        return default

    return {
        "full_name": g("full_name", "fullName"),
        "email": g("email", "Email"),
        "company": g("company", "companyName"),
        "phone": g("phone", "phoneNumber", "phone_number"),
        "role": g("role", "jobTitle", "title"),
        "preferred_date": g("preferred_date", "preferredDate"),
        "preferred_time": g("preferred_time", "preferredTime"),
        "interests": g("interests", "interest", "topics"),
        "message": g("message", "notes", "comment"),
        "status": g("status"),
        "created_at": g("created_at", "createdAt"),
    }


@router.post("/send")
async def request_demo(payload = Body(...)):
    try:
        if not resend.api_key:
            raise HTTPException(status_code=500, detail="Email service not configured")

        # Accept either a single object or an array and normalize
        items: List[DemoRequestItem]
        try:
            if isinstance(payload, list):
                normalized = [_normalize_item_dict(p if isinstance(p, dict) else {}) for p in payload]
                items = [DemoRequestItem(**n) for n in normalized]
            elif isinstance(payload, dict):
                normalized = _normalize_item_dict(payload)
                items = [DemoRequestItem(**normalized)]
            else:
                raise HTTPException(status_code=400, detail="Invalid payload format")
        except Exception as ve:
            logger.error(f"Validation/normalization error: {ve}")
            raise HTTPException(status_code=422, detail="Invalid payload fields. 'full_name' and 'email' are required.")

        if not items:
            raise HTTPException(status_code=400, detail="Empty payload list")

        item = items[0]
        html_template = _read_template()
        html_content = _fill_template(html_template, item)

        tags = [
            {"name": "request_type", "value": "demo"}
        ]
        if item.company:
            tags.append({"name": "company", "value": _sanitize_tag_value(item.company)})
        if item.role:
            tags.append({"name": "role", "value": _sanitize_tag_value(item.role)})

        params = {
            "from": os.getenv("RESEND_FROM_EMAIL", "noreply@miasistentelegalia.com"),
            "to": [item.email],
            "subject": "Confirmación de tu demo - Mi Asistente Legal IA",
            "html": html_content,
            "reply_to": os.getenv("RESEND_REPLY_TO_EMAIL", "support@miasistentelegalia.com"),
            "tags": tags,
        }

        result = resend.Emails.send(params)

        return {
            "success": True,
            "message": "Demo confirmation email sent",
            "email_id": getattr(result, "id", None),
        }
    except HTTPException:
        raise
    except FileNotFoundError as e:
        logger.error(str(e))
        raise HTTPException(status_code=500, detail="Email template not found")
    except Exception as e:
        logger.error(f"Error sending demo confirmation: {e}")
        raise HTTPException(status_code=500, detail="Failed to send email")


