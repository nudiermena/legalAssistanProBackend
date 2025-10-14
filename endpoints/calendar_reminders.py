from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import os
import logging

from config.supabase import get_supabase_config

try:
    import resend
    resend.api_key = os.getenv("RESEND_API_KEY")
except Exception:
    resend = None  # type: ignore


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calendar/reminders", tags=["calendar_reminders"]) 


class CalendarEvent(BaseModel):
    id: Any
    user_id: str = Field(..., description="ID of the profile/user owner of the event")
    title: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: datetime = Field(..., description="When the event expires (used for reminders)")
    location: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ReminderResult(BaseModel):
    event_id: Any
    user_id: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    event_title: Optional[str] = None
    event_date: datetime
    sent: bool
    error: Optional[str] = None


def _get_supabase_client():
    cfg = get_supabase_config()
    # Prefer admin client (service role) to bypass RLS for backend ops
    try:
        admin = cfg.get_admin_client()
        return admin
    except Exception:
        return cfg.get_client()


def _fetch_upcoming_events(days_ahead: int = 7, table_name: str = "calendar_events", date_column: str = "end_time") -> List[Dict[str, Any]]:
    client = _get_supabase_client()

    now_iso = datetime.utcnow().isoformat()
    future_iso = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat()

    # Supabase python client doesn't support joins directly; fetch events, then hydrate profiles
    try:
        events_resp = (
            client.table(table_name)
            .select("*")
            .gte(date_column, now_iso)
            .lte(date_column, future_iso)
            .execute()
        )
        return events_resp.data or []
    except Exception as e:
        logger.error(f"Failed querying {table_name}: {e}")
        raise


def _fetch_profiles_by_ids(user_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    if not user_ids:
        return {}
    client = _get_supabase_client()
    try:
        # Use 'in' filter in chunks if too many ids; here assume moderate size
        prof_resp = client.table("profiles").select("*").in_("id", user_ids).execute()
        profiles = prof_resp.data or []
        return {p.get("id"): p for p in profiles}
    except Exception as e:
        logger.error(f"Failed querying profiles: {e}")
        return {}


def _build_email_html(
    full_name: Optional[str],
    event_title: Optional[str],
    description: Optional[str],
    start_time: Optional[datetime],
    end_time: datetime,
    event_type: Optional[str],
) -> str:
    display_name = full_name or "Cliente"
    title = event_title or "Evento"
    desc = description or "Sin descripción"
    e_type = event_type or "General"
    start_str = start_time.strftime("%Y-%m-%d %H:%M UTC") if start_time else "N/A"
    end_str = end_time.strftime("%Y-%m-%d %H:%M UTC")
    try:
        days_remaining = max((end_time - datetime.utcnow()).days, 0)
    except Exception:
        days_remaining = 0
    return f"""
    <div style='font-family:system-ui,-apple-system,Segoe UI,Roboto,Inter,Arial,sans-serif;max-width:640px;margin:auto;padding:24px;border:1px solid #eee;border-radius:12px'>
      <h2 style='margin:0 0 12px'>Recordatorio de vencimiento</h2>
      <p style='margin:0 0 16px'>Hola {display_name},</p>
      <p style='margin:0 0 12px'>Tienes un evento próximo a vencer. Aquí tienes los detalles:</p>
      <div style='background:#f7f7f8;border:1px solid #e5e7eb;border-radius:10px;padding:12px 16px;margin:12px 0'>
        <div style='font-weight:600;margin-bottom:4px'>{title}</div>
        <div style='color:#374151;margin:2px 0'><strong>Tipo:</strong> {e_type}</div>
        <div style='color:#374151;margin:2px 0'><strong>Inicio:</strong> {start_str}</div>
        <div style='color:#374151;margin:2px 0'><strong>Vencimiento:</strong> {end_str} ({days_remaining} días restantes)</div>
        <div style='color:#374151;margin:6px 0'><strong>Descripción:</strong> {desc}</div>
      </div>
      <p style='margin:24px 0 0;color:#6b7280;font-size:13px'>Este es un correo automático de MiAsistenteLegalIA.</p>
    </div>
    """


@router.get("/upcoming", response_model=List[CalendarEvent])
async def list_upcoming_events(
    days: int = Query(7, ge=1, le=60, description="Days ahead to search for events"),
    table: str = Query("calendar_events", description="Supabase table for events"),
    date_column: str = Query("end_time", description="Date column used to filter upcoming events (use end_time)"),
):
    try:
        items = _fetch_upcoming_events(days_ahead=days, table_name=table, date_column=date_column)
        normalized: List[CalendarEvent] = []
        for ev in items:
            # Parse date field
            raw_end = ev.get("end_time") or ev.get(date_column)
            raw_start = ev.get("start_time")
            try:
                end_dt = datetime.fromisoformat(raw_end.replace("Z", "+00:00")) if isinstance(raw_end, str) else raw_end
            except Exception:
                end_dt = datetime.utcnow()
            try:
                start_dt = datetime.fromisoformat(raw_start.replace("Z", "+00:00")) if isinstance(raw_start, str) else raw_start
            except Exception:
                start_dt = None
            normalized.append(CalendarEvent(
                id=ev.get("id"),
                user_id=ev.get("user_id") or ev.get("profile_id") or ev.get("owner_id"),
                title=ev.get("title"),
                description=ev.get("description"),
                event_type=ev.get("event_type") or ev.get("type") or ev.get("category"),
                start_time=start_dt,
                end_time=end_dt,
                location=ev.get("location"),
                metadata={k: v for k, v in ev.items() if k not in {"id", "user_id", "profile_id", "owner_id", "start_time", "end_time", "title", "description", "event_type", "location"}}
            ))
        return normalized
    except Exception as e:
        logger.error(f"Error listing upcoming events: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch upcoming events")


@router.post("/send", response_model=List[ReminderResult])
async def send_upcoming_event_reminders(
    days: int = Query(1, ge=1, le=60),
    table: str = Query("calendar_events"),
    date_column: str = Query("end_time"),
):
    if resend is None or not getattr(resend, "api_key", None):
        raise HTTPException(status_code=500, detail="Email service not configured")

    events = _fetch_upcoming_events(days_ahead=days, table_name=table, date_column=date_column)
    user_ids = []
    for ev in events:
        uid = ev.get("user_id") or ev.get("profile_id") or ev.get("owner_id")
        if uid:
            user_ids.append(uid)

    profiles = _fetch_profiles_by_ids(list(dict.fromkeys(user_ids)))

    results: List[ReminderResult] = []
    for ev in events:
        uid = ev.get("user_id") or ev.get("profile_id") or ev.get("owner_id")
        prof = profiles.get(uid or "") if uid else None

        # Parse event date
        raw_end = ev.get("end_time") or ev.get(date_column)
        raw_start = ev.get("start_time")
        try:
            end_dt = datetime.fromisoformat(raw_end.replace("Z", "+00:00")) if isinstance(raw_end, str) else raw_end
        except Exception:
            end_dt = datetime.utcnow()
        try:
            start_dt = datetime.fromisoformat(raw_start.replace("Z", "+00:00")) if isinstance(raw_start, str) else raw_start
        except Exception:
            start_dt = None

        email = (prof or {}).get("email") if prof else None
        full_name = (prof or {}).get("full_name") if prof else None

        if not email:
            results.append(ReminderResult(
                event_id=ev.get("id"),
                user_id=uid or "",
                email=None,
                full_name=full_name,
                event_title=ev.get("title"),
                event_date=end_dt,
                sent=False,
                error="No email on profile"
            ))
            continue

        description = ev.get("description") or ev.get("details") or ev.get("notes")
        event_type = ev.get("event_type") or ev.get("type") or ev.get("category")
        html = _build_email_html(
            full_name=full_name,
            event_title=ev.get("title"),
            description=description,
            start_time=start_dt,
            end_time=end_dt,
            event_type=event_type,
        )
        try:
            from_email = os.getenv("RESEND_FROM_EMAIL", "noreply@miasistentelegalia.com")
            reply_to_email = os.getenv("RESEND_REPLY_TO_EMAIL", "support@miasistentelegalia.com")
            
            logger.info(f"Sending email to {email} from {from_email}")
            logger.debug(f"Email HTML content length: {len(html)} characters")
            
            params = {
                "from": from_email,
                "to": [email],
                "subject": "Recordatorio: evento próximo a vencer",
                "html": html,
                "reply_to": reply_to_email,
                "tags": [
                    {"name": "type", "value": "calendar_reminder"},
                    {"name": "event_id", "value": str(ev.get("id"))},
                ],
            }
            
            # Send email and capture response
            response = resend.Emails.send(params)
            logger.info(f"Resend API response for {email}: {response}")
            
            # Check if response contains error information
            if hasattr(response, 'data') and response.data:
                email_id = response.data.get('id')
                logger.info(f"Email sent successfully to {email}, ID: {email_id}")
            else:
                logger.warning(f"Unexpected response format from Resend for {email}: {response}")
            
            results.append(ReminderResult(
                event_id=ev.get("id"),
                user_id=uid or "",
                email=email,
                full_name=full_name,
                event_title=ev.get("title"),
                event_date=end_dt,
                sent=True,
                error=None,
            ))
        except Exception as e:
            logger.error(f"Failed sending email to {email}: {e}")
            logger.error(f"Email parameters: from={from_email}, to={email}, subject=Recordatorio: evento próximo a vencer")
            results.append(ReminderResult(
                event_id=ev.get("id"),
                user_id=uid or "",
                email=email,
                full_name=full_name,
                event_title=ev.get("title"),
                event_date=end_dt,
                sent=False,
                error=str(e),
            ))

    return results


@router.post("/test-email")
async def test_email_sending(
    test_email: str = Query(..., description="Email address to send test email to")
):
    """Test endpoint to verify Resend email configuration"""
    if resend is None or not getattr(resend, "api_key", None):
        raise HTTPException(status_code=500, detail="Email service not configured")
    
    try:
        from_email = os.getenv("RESEND_FROM_EMAIL", "noreply@miasistentelegalia.com")
        reply_to_email = os.getenv("RESEND_REPLY_TO_EMAIL", "support@miasistentelegalia.com")
        
        logger.info(f"Testing email configuration - From: {from_email}, To: {test_email}")
        
        # Simple test email
        test_html = """
        <div style='font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;'>
            <h2>Test Email from MiAsistenteLegalIA</h2>
            <p>This is a test email to verify the email configuration.</p>
            <p>If you receive this email, the Resend configuration is working correctly.</p>
            <p>Timestamp: {}</p>
        </div>
        """.format(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"))
        
        params = {
            "from": from_email,
            "to": [test_email],
            "subject": "Test Email - MiAsistenteLegalIA",
            "html": test_html,
            "reply_to": reply_to_email,
            "tags": [
                {"name": "type", "value": "test_email"},
                {"name": "timestamp", "value": datetime.utcnow().isoformat()},
            ],
        }
        
        response = resend.Emails.send(params)
        logger.info(f"Test email response: {response}")
        
        return {
            "success": True,
            "message": f"Test email sent to {test_email}",
            "response": str(response),
            "from_email": from_email,
            "to_email": test_email
        }
        
    except Exception as e:
        logger.error(f"Test email failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test email failed: {str(e)}")


