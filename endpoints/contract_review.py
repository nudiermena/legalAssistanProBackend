from fastapi import APIRouter, Body, HTTPException, Depends, Request, File, UploadFile, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field, ValidationError, field_validator
from datetime import datetime
from models.request_models import ContractReviewRequest
from models.response_models import BaseResponse, format_response, handle_error
from agents.contract_agent import analyze_contract_file, create_contract_agent
from config.colombian_compliance import ColombianLegalFramework
from pathlib import Path
import tiktoken
from math import ceil
from pypdf import PdfReader
from io import BytesIO
import logging
import base64
import unicodedata
from utils.pdf_processor import extract_text_from_pdf_content, sanitize_text
import json
import io
import tempfile
import os
import fitz  # PyMuPDF
import shutil
import mimetypes
import httpx
import aiofiles
import tempfile
import os as os_module

# Security imports
from config.security import SECURITY_CONFIG, SecurityUtils
from utils.security_validators import (
    InputValidator,
    FileValidator,
    log_security_event,
    SecurityValidationError
)
from middleware.security import get_request_id, get_user_id, get_client_ip
from endpoints.auth import get_current_user

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["contracts"])

class ContractReviewRequest(BaseModel):
    contract_text: str = Field(
        ..., 
        description="Texto completo del contrato"
    )
    contract_type: str = Field(
        ...,
        description="Tipo de contrato"
    )
    jurisdiction: str = Field(
        default="Colombia",
        description="Jurisdicción aplicable"
    )
    parties: List[Dict[str, str]] = Field(
        ...,
        description="Partes del contrato"
    )
    specific_concerns: Optional[List[str]] = Field(
        None,
        description="Aspectos específicos a revisar"
    )
    relevant_regulations: Optional[List[str]] = Field(
        None,
        description="Normativa aplicable"
    )
    data_processing: Optional[Dict[str, str]] = Field(
        None,
        description="Tratamiento de datos personales"
    )
    legal_terms: Optional[List[str]] = Field(
        None,
        description="Términos jurídicos relevantes"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "contract_text": "Entre los suscritos a saber...",
                "contract_type": "contrato_prestacion_servicios",
                "jurisdiction": "Colombia",
                "parties": [
                    {
                        "type": "contratante",
                        "name": "Empresa ABC S.A.S.",
                        "id_type": "NIT",
                        "id_number": "900.123.456-7"
                    },
                    {
                        "type": "contratista",
                        "name": "Juan Pérez",
                        "id_type": "CC",
                        "id_number": "1234567890"
                    }
                ],
                "specific_concerns": [
                    "cláusula_permanencia",
                    "confidencialidad",
                    "propiedad_intelectual"
                ],
                "relevant_regulations": [
                    "Código Civil",
                    "Código de Comercio",
                    "Ley 1581 de 2012"
                ],
                "data_processing": {
                    "type": "datos_comerciales",
                    "purpose": "ejecucion_contractual",
                    "consent": "expreso"
                },
                "legal_terms": [
                    "clausula_penal",
                    "terminacion_unilateral",
                    "jurisdiccion_competente"
                ]
            }
        }

    @field_validator('contract_text')
    def validate_contract_text(cls, v):
        """Validate and sanitize contract text"""
        if not v:
            raise ValueError("Contract text cannot be empty")
        
        # Sanitize the text
        sanitized = InputValidator.sanitize_text(v)
        
        # Check for minimum length
        if len(sanitized) < 50:
            raise ValueError("Contract text must be at least 50 characters")
        
        return sanitized

    @field_validator('contract_type')
    def validate_contract_type(cls, v):
        """Validate contract type"""
        allowed_types = [
            "contrato_prestacion_servicios",
            "contrato_laboral",
            "contrato_comercial",
            "contrato_civil",
            "contrato_estatal"
        ]
        
        if v not in allowed_types:
            raise ValueError(f"Invalid contract type. Must be one of: {allowed_types}")
        
        return v

    @field_validator('parties')
    def validate_parties(cls, v):
        """Validate contract parties"""
        if not v or len(v) < 2:
            raise ValueError("Contract must have at least 2 parties")
        
        for party in v:
            if not isinstance(party, dict):
                raise ValueError("Each party must be a dictionary")
            
            required_fields = ["type", "name"]
            for field in required_fields:
                if field not in party:
                    raise ValueError(f"Party missing required field: {field}")
            
            # Sanitize party data
            party["name"] = InputValidator.sanitize_text(party.get("name", ""), 200)
            party["type"] = InputValidator.sanitize_text(party.get("type", ""), 50)
        
        return v

class ContractReviewResponse(BaseModel):
    analysis: Dict[str, str] = Field(
        ..., 
        description="Análisis detallado del contrato"
    )
    contract_type: str = Field(
        ..., 
        description="Tipo de contrato"
    )
    jurisdiction: str = Field(
        ..., 
        description="Jurisdicción"
    )
    parties: List[Dict[str, str]] = Field(
        ..., 
        description="Partes del contrato"
    )
    colombian_compliance: Dict[str, Any] = Field(
        ..., 
        description="Cumplimiento normativo"
    )
    risk_assessment: Dict[str, Any] = Field(
        ..., 
        description="Evaluación de riesgos"
    )
    recommendations: List[str] = Field(
        ..., 
        description="Recomendaciones"
    )
    specific_concerns: Optional[List[str]] = None
    relevant_regulations: Optional[List[str]] = None
    data_processing: Optional[Dict[str, str]] = None
    legal_terms: Optional[Dict[str, str]] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "analysis": {
                    "resumen_ejecutivo": "El contrato presenta...",
                    "clausulas_criticas": ["Cláusula 5: Confidencialidad..."],
                    "obligaciones_principales": ["1. El contratista se obliga..."],
                    "fechas_criticas": ["Vigencia: 12 meses..."],
                    "clausulas_inusuales": ["Cláusula 10: Limitación..."]
                },
                "contract_type": "prestacion_servicios",
                "jurisdiction": "Colombia",
                "parties": [
                    {
                        "type": "contratante",
                        "name": "Empresa ABC S.A.S.",
                        "id": "900123456-7"
                    }
                ],
                "colombian_compliance": {
                    "framework_version": "2024.1",
                    "status": "compliant"
                },
                "risk_assessment": {
                    "nivel_riesgo": "medio",
                    "riesgos_identificados": [
                        "Cláusula de permanencia excesiva",
                        "Ausencia de procedimiento de terminación"
                    ],
                    "impacto_potencial": "significativo"
                },
                "recommendations": [
                    "Modificar cláusula de permanencia",
                    "Incluir procedimiento de terminación",
                    "Especificar jurisdicción aplicable"
                ]
            }
        }

class AnalysisOptions(BaseModel):
    risk_analysis: Dict[str, bool]
    clause_extraction: Dict[str, bool]
    compliance_check: Dict[str, bool]

class Metadata(BaseModel):
    file_name: str
    file_type: str
    file_size: int

class AnalysisRequest(BaseModel):
    file: UploadFile
    metadata: Dict[str, Any]
    analysis_options: Dict[str, Any]
    language: str = "es"
    jurisdiction: str = "Colombia"

class AnalysisResponse(BaseModel):
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None

class ContractAnalysisRequest(BaseModel):
    content: str = Field(..., description="Contract text content")
    metadata: Dict[str, Any]
    analysis_options: AnalysisOptions
    language: str = Field(default="es", description="Language of the contract")
    jurisdiction: str = Field(default="Colombia", description="Jurisdiction of the contract")

    class Config:
        json_schema_extra = {
            "example": {
                "content": "Contract text content...",
                "metadata": {
                    "file_name": "contract.pdf",
                    "file_type": "application/pdf",
                    "file_size": 1024000
                },
                "analysis_options": {
                    "risk_analysis": {"financial": True, "legal": True},
                    "clause_extraction": {"important": True, "obligations": True},
                    "compliance_check": {"regulatory": True, "internal": True}
                },
                "language": "es",
                "jurisdiction": "Colombia"
            }
        }

    @field_validator('content')
    def validate_content(cls, v):
        """Validate and sanitize content"""
        if not v:
            raise ValueError("Content cannot be empty")
        
        sanitized = InputValidator.sanitize_text(v)
        
        if len(sanitized) < 50:
            raise ValueError("Content must be at least 50 characters")
        
        return sanitized

    @field_validator('metadata')
    def validate_metadata(cls, v):
        """Validate metadata"""
        if not isinstance(v, dict):
            raise ValueError("Metadata must be a dictionary")
        
        required_fields = ["file_name", "file_type", "file_size"]
        for field in required_fields:
            if field not in v:
                raise ValueError(f"Metadata missing required field: {field}")
        
        # Validate file size
        if v["file_size"] > SECURITY_CONFIG.max_file_size:
            raise ValueError(f"File size exceeds maximum allowed size of {SECURITY_CONFIG.max_file_size}")
        
        return v

def split_text_into_chunks(text: str, max_tokens: int = 100000) -> List[str]:
    """Split text into chunks that fit within token limit"""
    # Initialize tokenizer
    enc = tiktoken.encoding_for_model("gpt-4")  # or another appropriate encoding
    
    # Get tokens
    tokens = enc.encode(text)
    total_tokens = len(tokens)
    
    # If text fits in one chunk, return it
    if total_tokens <= max_tokens:
        return [text]
    
    # Calculate number of chunks needed
    num_chunks = ceil(total_tokens / max_tokens)
    chunk_size = ceil(total_tokens / num_chunks)
    
    chunks = []
    for i in range(0, total_tokens, chunk_size):
        chunk_tokens = tokens[i:i + chunk_size]
        chunk_text = enc.decode(chunk_tokens)
        chunks.append(chunk_text)
    
    return chunks

async def analyze_large_contract(
    contract_text: str,
    contract_type: str,
    jurisdiction: str = "Colombia",
    specific_concerns: List[str] = None,
    relevant_regulations: List[str] = None
) -> dict:
    """Analyze large contracts by splitting into manageable chunks"""
    try:
        # Split contract into chunks
        chunks = split_text_into_chunks(contract_text)
        
        # Analyze each chunk
        chunk_analyses = []
        for i, chunk in enumerate(chunks):
            chunk_prompt = f"""Analyze part {i+1} of {len(chunks)} of this {contract_type} contract:

Contract Text:
{chunk}

Focus on:
1. Key clauses and terms
2. Potential risks or issues
3. Compliance with {jurisdiction} law
4. Specific concerns: {', '.join(specific_concerns) if specific_concerns else 'None specified'}
5. Relevant regulations: {', '.join(relevant_regulations) if relevant_regulations else 'Standard regulations'}

Provide a concise analysis focusing on the most important findings.
"""
            # Create a new agent for each chunk to avoid context overflow
            agent = create_contract_agent()
            chunk_result = await agent.arun(chunk_prompt)
            chunk_analyses.append(chunk_result)
        
        # Combine and summarize the analyses
        summary_prompt = f"""Synthesize the following analyses of a {contract_type} contract into a cohesive summary:

{'\n\n'.join([f'Part {i+1}:\n{analysis}' for i, analysis in enumerate(chunk_analyses)])}

Provide:
1. Executive summary
2. Key findings across all sections
3. Overall risk assessment
4. Main recommendations
5. Compliance status
"""
        
        agent = create_contract_agent()
        final_analysis = await agent.arun(summary_prompt)
        
        return {
            "status": "success",
            "analysis": final_analysis,
            "metadata": {
                "contract_type": contract_type,
                "jurisdiction": jurisdiction,
                "total_chunks": len(chunks),
                "specific_concerns": specific_concerns,
                "relevant_regulations": relevant_regulations
            }
        }
    
    except Exception as e:
        print(f"Error analyzing contract: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "message": "Error analyzing contract",
                "timestamp": datetime.now().isoformat()
            }
        )

def is_valid_base64(content: str) -> bool:
    """Check if string is valid base64"""
    try:
        # Remove any whitespace and newlines
        content = ''.join(content.split())
        # Add padding if necessary
        padding = len(content) % 4
        if padding:
            content += '=' * (4 - padding)
        # Try to decode
        base64.b64decode(content.encode('ascii'))
        return True
    except Exception:
        return False

def clean_base64_content(content: str) -> str:
    """Clean and prepare base64 content for decoding"""
    try:
        # Remove any whitespace, newlines, and other invalid characters
        content = ''.join(c for c in content if c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')
        
        # Add padding if necessary
        padding = len(content) % 4
        if padding:
            content += '=' * (4 - padding)
            
        return content
    except Exception as e:
        logging.error(f"Error cleaning base64 content: {str(e)}")
        return ""

def get_file_type(filename: str) -> str:
    """Get file type using mimetypes module"""
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type:
        return mime_type
    return 'application/octet-stream'

def validate_pdf_content(content: bytes) -> Tuple[bool, str]:
    """
    Validate if content is actually a PDF file
    Returns: (is_valid, error_message)
    """
    try:
        # Check PDF header
        if not content.startswith(b'%PDF-'):
            return False, "El archivo no tiene la estructura correcta de un PDF."
            
        # Additional PDF validation
        if b'.PDF' not in content[:1024]:
            return False, "El archivo no tiene la estructura correcta de un PDF."
            
        return True, ""
        
    except Exception as e:
        logging.error(f"Error validating PDF: {str(e)}")
        return False, f"Error al validar el PDF: {str(e)}"

def debug_pdf_content(content: bytes, filename: str) -> None:
    """Debug helper to check PDF content"""
    try:
        # Log first 50 bytes for debugging
        logger.debug(f"First 50 bytes of {filename}: {content[:50]}")
        # Check for PDF signature
        has_pdf_header = content.startswith(b'%PDF-')
        logger.debug(f"Has PDF header: {has_pdf_header}")
        # Log file size
        logger.debug(f"File size: {len(content)} bytes")
    except Exception as e:
        logger.error(f"Error in debug_pdf_content: {str(e)}")

def decode_base64_safely(content: str, filename: str) -> Tuple[Optional[bytes], str]:
    """
    Safely decode base64 content with detailed logging
    """
    try:
        logger.debug(f"Starting base64 decode for {filename}")
        logger.debug(f"Content length before cleaning: {len(content)}")
        
        # Remove any whitespace
        content = content.strip()
        
        # Check if content looks like base64
        if not content:
            return None, "Contenido vacío"
            
        # Log sample of content for debugging
        logger.debug(f"First 50 chars of content: {content[:50]}")
        
        try:
            # Try direct decode first
            decoded = base64.b64decode(content)
            logger.debug(f"Successfully decoded {len(decoded)} bytes")
            return decoded, ""
        except Exception as first_error:
            logger.warning(f"First decode attempt failed: {str(first_error)}")
            
            # Try cleaning the content
            cleaned_content = ''.join(c for c in content if c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')
            
            # Add padding if necessary
            padding = len(cleaned_content) % 4
            if padding:
                cleaned_content += '=' * (4 - padding)
            
            try:
                decoded = base64.b64decode(cleaned_content)
                logger.debug(f"Successfully decoded after cleaning: {len(decoded)} bytes")
                return decoded, ""
            except Exception as second_error:
                logger.error(f"Second decode attempt failed: {str(second_error)}")
                return None, f"Error decodificando el contenido: {str(second_error)}"
                
    except Exception as e:
        logger.error(f"Base64 decode error: {str(e)}")
        return None, f"Error en el proceso de decodificación: {str(e)}"

async def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes using pypdf with enhanced fallback methods"""
    try:
        # Create a BytesIO object from the PDF content
        pdf_file = BytesIO(pdf_bytes)
        
        # Extract text using pypdf
        reader = PdfReader(pdf_file)
        text_parts = []
        total_pages = len(reader.pages)
        
        logger.info(f"PDF has {total_pages} pages")
        
        for i, page in enumerate(reader.pages):
            try:
                # Try standard text extraction
                page_text = page.extract_text() or ""
                
                # If no text found, try alternative extraction methods
                if not page_text.strip():
                    # Try extracting text with different parameters
                    page_text = page.extract_text(visitor_text=lambda text, cm, tm, fontDict, fontSize: text)
                
                # If still no text, try extracting from form fields
                if not page_text.strip():
                    try:
                        if "/AcroForm" in page.get_object():
                            form_text = []
                            for field in page.get_object()["/AcroForm"]["/Fields"]:
                                field_obj = field.get_object()
                                if "/V" in field_obj:
                                    form_text.append(str(field_obj["/V"]))
                            page_text = " ".join(form_text)
                    except:
                        pass
                
                logger.debug(f"Page {i+1}: {len(page_text)} characters extracted")
                
                if page_text.strip():
                    text_parts.append(page_text.strip())
                    
            except Exception as page_error:
                logger.warning(f"Error extracting text from page {i+1}: {page_error}")
                continue
                
        # Join all parts with newlines
        final_text = '\n'.join(text_parts)
        
        # If no text was extracted, provide a helpful message
        if not final_text.strip():
            logger.warning("No text could be extracted from PDF. This might be an image-based PDF or password-protected.")
            return f"[PDF with {total_pages} pages - No extractable text found. This appears to be an image-based or scanned document that requires OCR processing.]"
        
        logger.info(f"Successfully extracted {len(final_text)} characters from PDF")
        return final_text
            
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return None

async def extract_text_from_docx(docx_bytes: bytes) -> str:
    """Extract text from DOCX bytes using python-docx"""
    try:
        from docx import Document
        from io import BytesIO
        
        # Create a BytesIO object from the DOCX bytes
        docx_io = BytesIO(docx_bytes)
        
        # Use python-docx to extract text
        doc = Document(docx_io)
        text_parts = []
        
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text.strip())
        
        # Join all parts with newlines
        final_text = '\n'.join(text_parts)
        return final_text if final_text else None
            
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {str(e)}")
        return None

async def extract_text_from_file(file_bytes: bytes, file_type: str) -> str:
    """Extract text from file bytes based on file type"""
    try:
        if file_type.lower() == 'application/pdf':
            return await extract_text_from_pdf(file_bytes)
        elif file_type.lower() in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']:
            return await extract_text_from_docx(file_bytes)
        else:
            # Try to detect file type from content
            if file_bytes.startswith(b'%PDF-'):
                return await extract_text_from_pdf(file_bytes)
            elif file_bytes.startswith(b'PK'):
                return await extract_text_from_docx(file_bytes)
            else:
                logger.error(f"Unsupported file type: {file_type}")
                return None
    
    except Exception as e:
        logger.error(f"Error extracting text from file: {str(e)}")
        return None

def decode_pdf_field(field_value: str) -> str:
    """Decode PDF form field values that might be hex-encoded."""
    if isinstance(field_value, str) and field_value.startswith('<') and field_value.endswith('>'):
        try:
            hex_string = field_value[1:-1]
            return bytes.fromhex(hex_string).decode('utf-8', errors='replace')
        except Exception as e:
            logger.warning(f"Error decoding field value: {e}")
            return field_value
    return field_value

# Create a base temporary directory for uploads
TEMP_UPLOAD_DIR = Path(tempfile.gettempdir()) / "contract_uploads"
TEMP_UPLOAD_DIR.mkdir(exist_ok=True)

def create_temp_subfolder() -> Path:
    """Create a timestamped subfolder for uploads."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    subfolder = TEMP_UPLOAD_DIR / f"upload_{timestamp}_{os.urandom(4).hex()}"
    subfolder.mkdir(exist_ok=True)
    return subfolder

async def save_upload_file(upload_file: UploadFile, folder: Path) -> Path:
    """Save uploaded file and return the file path."""
    try:
        # Create a unique filename
        original_filename = Path(upload_file.filename).stem
        safe_filename = f"{original_filename}_{os.urandom(4).hex()}.pdf"
        file_path = folder / safe_filename
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        
        logger.info(f"Saved uploaded file to: {file_path}")
        return file_path
    
    except Exception as e:
        logger.error(f"Error saving uploaded file: {e}")
        raise

async def extract_pdf_data(file_path: Path) -> Dict[str, Any]:
    """Extract both form fields and text content from PDF using PyMuPDF."""
    form_data = {}
    text_content = []
    
    try:
        # Open PDF from file
        doc = fitz.open(file_path)
        
        # Extract form fields
        for page in doc:
            # Get form fields from page
            fields = page.widgets()
            for field in fields:
                if field.field_type == fitz.PDF_WIDGET_TYPE_TEXT:
                    field_name = field.field_name
                    field_value = field.field_value
                    if field_value:
                        form_data[field_name] = field_value
            
            # Extract text content
            text = page.get_text()
            if text.strip():
                text_content.append(text.strip())
        
        logger.info(f"Extracted {len(form_data)} form fields from {file_path.name}")
        
        return {
            "form_data": form_data,
            "text_content": "\n".join(text_content)
        }
        
    except Exception as e:
        logger.error(f"Error extracting PDF data from {file_path}: {str(e)}")
        raise
    finally:
        if 'doc' in locals():
            doc.close()

def cleanup_old_files(max_age_hours: int = 24):
    """Clean up files older than specified hours."""
    try:
        current_time = datetime.now()
        for subfolder in TEMP_UPLOAD_DIR.iterdir():
            if subfolder.is_dir():
                folder_time = datetime.fromtimestamp(subfolder.stat().st_mtime)
                age = current_time - folder_time
                if age.total_seconds() > (max_age_hours * 3600):
                    shutil.rmtree(subfolder)
                    logger.info(f"Cleaned up old folder: {subfolder}")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

async def download_file_from_url(url: str, folder: Path) -> Path:
    """Download file from URL and save to folder using R2 client with authentication"""
    try:
        # Validate URL
        if not url.startswith(('http://', 'https://')):
            raise ValueError("Invalid URL format")
        
        logger.info(f"Downloading from URL: {url}")
        
        # Extract filename from URL, handling contract-analisys bucket format
        filename = url.split('/')[-1]
        if not filename or '.' not in filename:
            # Try to detect file type from URL path
            if 'docx' in url.lower() or 'document' in url.lower():
                filename = f"downloaded_file_{os.urandom(4).hex()}.docx"
            else:
                filename = f"downloaded_file_{os.urandom(4).hex()}.pdf"
        
        # For contract-analisys bucket, preserve original filename structure
        if 'contract-analisys' in url:
            # Extract timestamp and original filename from contract-analisys format
            # Format: https://bucket.r2.cloudflarestorage.com/contract-analisys/timestamp-filename.pdf
            path_parts = url.split('/')
            if len(path_parts) >= 2:
                bucket_file = path_parts[-1]  # timestamp-filename.pdf
                if '-' in bucket_file:
                    # Split timestamp and filename
                    parts = bucket_file.split('-', 1)
                    if len(parts) == 2 and parts[0].isdigit():
                        original_filename = parts[1]
                        filename = original_filename if original_filename else filename
        
        # Create safe filename preserving original extension
        file_extension = Path(filename).suffix.lower()
        if not file_extension:
            file_extension = '.pdf'  # Default fallback
        
        safe_filename = f"{Path(filename).stem}_{os.urandom(4).hex()}{file_extension}"
        file_path = folder / safe_filename
        
        # Use Supabase S3 client for contract analysis bucket
        if 'supabase.co' in url or 'contract-analisis' in url:
            try:
                from utils.r2_storage import get_contract_analysis_supabase_s3_client
                from botocore.exceptions import ClientError
                from config.cloudflare import SUPABASE_CONTRACT_ANALYSIS_ENDPOINT, SUPABASE_CONTRACT_ANALYSIS_BUCKET_NAME
                
                # Get Supabase S3 client for contract analysis bucket
                s3_client = get_contract_analysis_supabase_s3_client()
                
                # Extract the object key from the URL
                # URL format: https://luiiwyzjtkqnmnzqghoz.supabase.co/storage/v1/object/public/contract-analisis/contract-analysis/filename
                # or: https://luiiwyzjtkqnmnzqghoz.supabase.co/storage/v1/object/public/contract-analisis/contract-files/filename
                # or: https://luiiwyzjtkqnmnzqghoz.supabase.co/storage/v1/object/public/contract-analisis/filename (root level)
                
                from urllib.parse import unquote
                
                if '/contract-analysis/' in url:
                    url_parts = url.split('/contract-analysis/')
                    if len(url_parts) == 2:
                        # Decode URL encoding and reconstruct the object key
                        filename = unquote(url_parts[1])
                        object_key = f"contract-analysis/{filename}"
                    else:
                        object_key = unquote(url.split('/')[-1])
                elif '/contract-files/' in url:
                    url_parts = url.split('/contract-files/')
                    if len(url_parts) == 2:
                        # Decode URL encoding and reconstruct the object key
                        filename = unquote(url_parts[1])
                        object_key = f"contract-files/{filename}"
                    else:
                        object_key = unquote(url.split('/')[-1])
                else:
                    # For files in the root of the bucket, extract and decode the filename
                    # URL format: https://luiiwyzjtkqnmnzqghoz.supabase.co/storage/v1/object/public/contract-analisis/filename
                    if '/contract-analisis/' in url:
                        url_parts = url.split('/contract-analisis/')
                        if len(url_parts) == 2:
                            object_key = unquote(url_parts[1])
                        else:
                            object_key = unquote(url.split('/')[-1])
                    else:
                        # Fallback: extract just the filename from the URL
                        object_key = unquote(url.split('/')[-1])
                
                logger.info(f"Downloading from Supabase S3 with object key: {object_key}")
                logger.info(f"Supabase S3 Bucket: {SUPABASE_CONTRACT_ANALYSIS_BUCKET_NAME}")
                logger.info(f"Full Supabase S3 URL: {SUPABASE_CONTRACT_ANALYSIS_ENDPOINT}/{object_key}")
                
                # Download file from Supabase S3
                response = s3_client.get_object(
                    Bucket=SUPABASE_CONTRACT_ANALYSIS_BUCKET_NAME,
                    Key=object_key
                )
                
                # Get file content
                file_content = response['Body'].read()
                total_size = len(file_content)
                
                # Check file size
                if total_size > SECURITY_CONFIG.max_file_size:
                    raise ValueError(f"File too large: {total_size} bytes")
                
                # Save file
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(file_content)
                
                logger.info(f"Downloaded contract analysis file from Supabase S3: {object_key} -> {file_path} ({total_size} bytes)")
                return file_path
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_message = e.response['Error']['Message']
                logger.error(f"Supabase S3 Client error: {error_code} - {error_message}")
                logger.error(f"Failed to download object: {object_key} from bucket: {SUPABASE_CONTRACT_ANALYSIS_BUCKET_NAME}")
                
                if error_code == 'AccessDenied':
                    raise ValueError(f"Access denied to Supabase S3 object '{object_key}'. Please check if the file exists and you have permission to access it.")
                elif error_code == 'NoSuchKey':
                    # Try to download directly from the original URL as fallback
                    logger.info(f"File not found in Supabase S3 bucket, trying direct download from original URL: {url}")
                    try:
                        # Fall back to direct HTTP download
                        async with httpx.AsyncClient(timeout=30.0) as client:
                            response = await client.get(url, headers={
                                'User-Agent': 'MiAsistenteLegalIA/1.0',
                                'Accept': 'application/pdf,application/octet-stream,*/*',
                                'Accept-Encoding': 'gzip, deflate'
                            })
                            response.raise_for_status()
                            
                            file_content = response.content
                            total_size = len(file_content)
                            
                            if total_size > SECURITY_CONFIG.max_file_size:
                                raise ValueError(f"File too large: {total_size} bytes")
                            
                            async with aiofiles.open(file_path, 'wb') as f:
                                await f.write(file_content)
                            
                            logger.info(f"Successfully downloaded file via direct HTTP: {url} -> {file_path} ({total_size} bytes)")
                            return file_path
                            
                    except Exception as fallback_error:
                        logger.error(f"Direct download fallback also failed: {fallback_error}")
                        # Provide helpful error message for missing files
                        if 'contract-files/' in object_key:
                            raise ValueError(f"Contract file not found in Supabase S3 storage. Please re-upload the contract file and try again.")
                        else:
                            raise ValueError(f"File '{object_key}' not found in Supabase S3 storage.")
                else:
                    raise ValueError(f"Supabase S3 error: {error_code} - {error_message}")
            except Exception as e:
                logger.error(f"Error downloading from Supabase S3: {e}")
                raise ValueError(f"Supabase S3 download error: {e}")
        
        else:
            # For non-R2 URLs, use direct HTTP download
            async with httpx.AsyncClient(
                timeout=30.0,
                headers={
                    'User-Agent': 'MiAsistenteLegalIA/1.0',
                    'Accept': 'application/pdf, */*',
                    'Accept-Encoding': 'gzip, deflate'
                }
            ) as client:
                async with client.stream('GET', url) as response:
                    logger.info(f"Response status: {response.status_code}")
                    
                    if response.status_code == 400:
                        error_content = await response.aread()
                        logger.error(f"400 Bad Request - Response content: {error_content}")
                        raise ValueError(f"Bad Request: {error_content.decode('utf-8', errors='ignore')}")
                    
                    response.raise_for_status()
                    
                    # Check content type
                    content_type = response.headers.get('content-type', '')
                    if 'pdf' not in content_type.lower() and not url.lower().endswith('.pdf'):
                        logger.warning(f"Unexpected content type: {content_type}")
                    
                    # Check file size
                    content_length = response.headers.get('content-length')
                    if content_length and int(content_length) > SECURITY_CONFIG.max_file_size:
                        raise ValueError(f"File too large: {content_length} bytes")
                    
                    # Download and save file
                    total_size = 0
                    async with aiofiles.open(file_path, 'wb') as f:
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            total_size += len(chunk)
                            if total_size > SECURITY_CONFIG.max_file_size:
                                raise ValueError(f"File too large: {total_size} bytes")
                            await f.write(chunk)
                
                logger.info(f"Downloaded file from {url} to {file_path} ({total_size} bytes)")
                return file_path
        
    except Exception as e:
        logger.error(f"Error downloading file from {url}: {e}")
        raise ValueError(f"Error downloading file: {e}")

def validate_file_url(url: str) -> bool:
    """Validate file URL for security with specific bucket validation"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        
        # Check protocol
        if parsed.scheme not in ['http', 'https']:
            return False
        
        # Check for suspicious patterns
        suspicious_patterns = [
            '..',  # Directory traversal
            '<script',  # XSS
            'javascript:',  # XSS
            'data:',  # Data URLs
        ]
        
        for pattern in suspicious_patterns:
            if pattern in url.lower():
                logger.warning(f"Suspicious pattern in URL: {pattern}")
                return False
        
        # Specific validation for contract-analisys bucket
        if 'r2.cloudflarestorage.com' in parsed.netloc:
            # Check if URL contains the contract-analisys bucket
            if 'contract-analisys' in parsed.path:
                logger.info(f"Valid contract analysis file URL from contract-analisys bucket: {url[:100]}...")
                return True
            else:
                logger.warning(f"R2 URL does not contain contract-analisys bucket: {parsed.path}")
                return False
        
        # Allow other trusted domains
        allowed_domains = [
            'cloudflare.com',
            'supabase.co'
        ]
        
        # Check domain
        if any(domain in parsed.netloc for domain in allowed_domains):
            return True
        
        logger.warning(f"File URL from unauthorized domain: {parsed.netloc}")
        return False
        
    except Exception as e:
        logger.error(f"Error validating URL: {e}")
        return False

class ContractAnalysisRequest(BaseModel):
    file_url: Optional[str] = None
    content: Optional[str] = None
    language: str = "es"
    jurisdiction: str = "Colombia"
    contract_type: Optional[str] = None
    analysis_options: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

@router.post("/contract-review/analyze")
async def analyze_contract(
    request: Request,
    file: Optional[UploadFile] = File(None),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Analyze contract with security validation and logging
    """
    request_id = get_request_id()
    user_id = get_user_id()
    client_ip = get_client_ip()
    
    # Parse JSON body directly
    try:
        body = await request.json()
        logger.info(f"Received JSON body: {body}")
        
        # Extract values from JSON body
        file_url = body.get("file_url")
        content = body.get("content")
        language = body.get("language", "es")
        jurisdiction = body.get("jurisdiction", "Colombia")
        contract_type = body.get("contract_type")
        analysis_options = body.get("analysis_options")
        metadata = body.get("metadata")
        
    except Exception as e:
        logger.error(f"Error parsing JSON body: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    try:
        # Debug logging to see what we're receiving
        logger.info(f"Received parameters - file_url: {file_url}, content: {content is not None}, file: {file is not None}")
        logger.info(f"Analysis options: {analysis_options}")
        logger.info(f"Metadata: {metadata}")
        
        # Log the request
        log_security_event(
            "contract_analysis_request",
            {
                "request_id": request_id,
                "user_id": user_id,
                "client_ip": client_ip,
                "has_file": file is not None,
                "has_content": content is not None,
                "has_file_url": file_url is not None,
                "contract_type": contract_type,
                "language": language,
                "jurisdiction": jurisdiction,
                "file_url_value": file_url[:100] if file_url else None
            },
            severity="INFO"
        )
        
        # Validate and sanitize inputs
        if language:
            language = InputValidator.sanitize_text(language, 10)
        if jurisdiction:
            jurisdiction = InputValidator.sanitize_text(jurisdiction, 50)
        if contract_type:
            contract_type = InputValidator.sanitize_text(contract_type, 100)
        if file_url:
            file_url = InputValidator.sanitize_text(file_url, 500)
        
        # Validate file if provided
        if file:
            # Validate file type
            if not FileValidator.validate_file_type(file):
                log_security_event(
                    "invalid_file_type",
                    {
                        "request_id": request_id,
                        "filename": file.filename,
                        "content_type": file.content_type
                    },
                    severity="WARNING"
                )
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid file type. Allowed types: {SECURITY_CONFIG.allowed_file_types}"
                )
            
            # Validate file size
            file_size = 0
            try:
                content_bytes = await file.read()
                file_size = len(content_bytes)
                await file.seek(0)  # Reset file pointer
            except Exception as e:
                log_security_event(
                    "file_read_error",
                    {
                        "request_id": request_id,
                        "filename": file.filename,
                        "error": str(e)
                    },
                    severity="ERROR"
                )
                raise HTTPException(status_code=400, detail="Error reading file")
            
            if not FileValidator.validate_file_size(file_size):
                log_security_event(
                    "file_too_large",
                    {
                        "request_id": request_id,
                        "filename": file.filename,
                        "file_size": file_size,
                        "max_size": SECURITY_CONFIG.max_file_size
                    },
                    severity="WARNING"
                )
                raise HTTPException(
                    status_code=413, 
                    detail=f"File too large. Maximum size: {SECURITY_CONFIG.max_file_size} bytes"
                )
            
            # Validate file content
            is_valid, validation_message = await FileValidator.validate_file_content(file)
            if not is_valid:
                log_security_event(
                    "malicious_file_content",
                    {
                        "request_id": request_id,
                        "filename": file.filename,
                        "validation_message": validation_message
                    },
                    severity="WARNING"
                )
                raise HTTPException(
                    status_code=400, 
                    detail=f"File validation failed: {validation_message}"
                )
        
        # Validate file_url if provided
        if file_url:
            if not validate_file_url(file_url):
                log_security_event(
                    "invalid_file_url",
                    {
                        "request_id": request_id,
                        "file_url": file_url[:100]  # Log first 100 chars only
                    },
                    severity="WARNING"
                )
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid or unauthorized file URL"
                )
        
        # Validate content if provided
        if content:
            content = InputValidator.sanitize_text(content)
            if len(content) < 50:
                raise HTTPException(
                    status_code=400, 
                    detail="Content must be at least 50 characters"
                )
        
        # Ensure we have either file, content, or file_url
        if not file and not content and not file_url:
            log_security_event(
                "missing_content",
                {
                    "request_id": request_id,
                    "user_id": user_id
                },
                severity="WARNING"
            )
            raise HTTPException(status_code=400, detail="No contract content, file, or file URL provided.")

        # 1. Use content if provided, else extract from file or file_url
        if content:
            contract_text = content
        elif file:
            try:
                file_bytes = await file.read()
                file_extension = Path(file.filename).suffix.lower()
                
                # Determine file type based on extension
                if file_extension == '.pdf':
                    file_type = 'application/pdf'
                elif file_extension in ['.docx', '.doc']:
                    file_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                else:
                    file_type = 'application/octet-stream'
                
                # Extract text using the unified function
                contract_text = await extract_text_from_file(file_bytes, file_type)
                
                # If extraction failed, try fallback
                if not contract_text:
                    contract_text = file_bytes.decode('utf-8')
                
                # Sanitize extracted text
                contract_text = InputValidator.sanitize_text(contract_text)
                
            except Exception as e:
                log_security_event(
                    "file_processing_error",
                    {
                        "request_id": request_id,
                        "filename": file.filename,
                        "error": str(e)
                    },
                    severity="ERROR"
                )
                raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
        elif file_url:
            try:
                # Create temporary folder for downloaded file
                temp_folder = create_temp_subfolder()
                
                # Download file from URL
                downloaded_file_path = await download_file_from_url(file_url, temp_folder)
                
                # Extract text from downloaded file
                file_bytes = downloaded_file_path.read_bytes()
                file_extension = downloaded_file_path.suffix.lower()
                
                # Determine file type based on extension
                if file_extension == '.pdf':
                    file_type = 'application/pdf'
                elif file_extension in ['.docx', '.doc']:
                    file_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                else:
                    file_type = 'application/octet-stream'
                
                # Extract text using the unified function
                contract_text = await extract_text_from_file(file_bytes, file_type)
                logger.info(f"Extracted text from {file_extension} file, length: {len(contract_text) if contract_text else 0}")
                
                # Check if text extraction was successful
                if not contract_text or len(contract_text.strip()) == 0:
                    logger.error(f"Failed to extract text from downloaded file: {downloaded_file_path}")
                    raise ValueError("Could not extract text from the downloaded file. The file might be corrupted or password-protected.")
                
                # Check if we got a helpful message about image-based PDFs
                if contract_text and contract_text.startswith("[PDF with") and "No extractable text found" in contract_text:
                    logger.warning(f"Image-based PDF detected: {downloaded_file_path}")
                    # For image-based PDFs, we can still proceed with analysis using the message
                    # The contract analysis agent can handle this case
                
                # Sanitize extracted text
                contract_text = InputValidator.sanitize_text(contract_text)
                logger.info(f"Sanitized text length: {len(contract_text) if contract_text else 0}")
                
                # Clean up downloaded file
                try:
                    shutil.rmtree(temp_folder)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup temp folder {temp_folder}: {cleanup_error}")
                
            except Exception as e:
                log_security_event(
                    "file_url_processing_error",
                    {
                        "request_id": request_id,
                        "file_url": file_url[:100],  # Log first 100 chars only
                        "error": str(e)
                    },
                    severity="ERROR"
                )
                raise HTTPException(status_code=500, detail=f"Error processing file from URL: {str(e)}")

        # 2. Process analysis_options if provided
        options = {}
        if analysis_options:
            try:
                # Validate options structure
                if not isinstance(analysis_options, dict):
                    raise ValueError("Analysis options must be a dictionary")
                
                # Sanitize analysis options values
                options = {}
                for key, value in analysis_options.items():
                    if isinstance(value, str):
                        options[key] = InputValidator.sanitize_text(value, 100)
                    else:
                        options[key] = value
                
            except Exception as e:
                log_security_event(
                    "invalid_analysis_options",
                    {
                        "request_id": request_id,
                        "analysis_options": str(analysis_options)[:100]  # Log first 100 chars
                    },
                    severity="WARNING"
                )
                raise HTTPException(status_code=400, detail=f"Invalid analysis_options: {e}")

        # 3. Validate contract text before analysis
        if not contract_text or len(contract_text.strip()) == 0:
            logger.error(f"No valid contract text to analyze. Text length: {len(contract_text) if contract_text else 0}")
            raise HTTPException(status_code=400, detail="No valid contract text could be extracted from the provided file or content.")

        # 4. Call your analysis logic (real, not dummy)
        try:
            logger.info(f"Starting contract analysis with text length: {len(contract_text)}")
            result = await analyze_contract_file(
                text=contract_text,
                contract_type=contract_type,
                language=language,
                jurisdiction=jurisdiction,
                analysis_options=options,
                user_id=current_user.get("user_id"),  # Use authenticated user's UUID
                session_id=f"contract_{current_user.get('user_id')}_{datetime.now().timestamp()}"
            )
            
            # Log successful analysis
            log_security_event(
                "contract_analysis_success",
                {
                    "request_id": request_id,
                    "user_id": user_id,
                    "contract_type": contract_type,
                    "text_length": len(contract_text),
                    "has_file": file is not None,
                    "has_file_url": file_url is not None
                },
                severity="INFO"
            )
            
            # Check if result contains PDF URL and log it
            if isinstance(result, dict) and 'summary_pdf_url' in result:
                logger.info(f"Contract analysis completed with PDF URL: {result['summary_pdf_url']}")
            
            # Return the result directly (it should already be in the correct format)
                return result
            
        except Exception as e:
            log_security_event(
                "analysis_error",
                {
                    "request_id": request_id,
                    "user_id": user_id,
                    "error": str(e),
                    "contract_type": contract_type
                },
                severity="ERROR"
            )
            raise HTTPException(status_code=500, detail=str(e))

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log unexpected errors
        log_security_event(
            "unexpected_error",
            {
                "request_id": request_id,
                "user_id": user_id,
                "error": str(e),
                "error_type": type(e).__name__
            },
            severity="ERROR"
        )
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get(
    "/contract-types",
    response_model=Dict[str, List[str]],
    summary="Tipos de Contratos",
    description="Obtiene los tipos de contratos disponibles para análisis"
)
async def get_contract_types(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Retorna los tipos de contratos disponibles"""
    return {
        "civiles": [
            "Compraventa",
            "Arrendamiento",
            "Mandato",
            "Mutuo"
        ],
        "comerciales": [
            "Suministro",
            "Agencia comercial",
            "Distribución",
            "Franquicia"
        ],
        "laborales": [
            "Término indefinido",
            "Término fijo",
            "Obra o labor",
            "Prestación de servicios"
        ],
        "estatales": [
            "Prestación de servicios",
            "Consultoría",
            "Obra pública",
            "Concesión"
        ]
    }

def assess_contract_risks(
    contract_type: str,
    specific_concerns: Optional[List[str]]
) -> Dict[str, any]:
    """Evalúa riesgos específicos del contrato"""
    # Implementation would connect to a risk assessment system
    return {
        "nivel_riesgo": "por_determinar",
        "riesgos_identificados": [],
        "impacto_potencial": "por_evaluar"
    } 

@router.get("/dashboard/contract-review", response_class=HTMLResponse)
async def get_contract_analysis_interface(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Serve the contract analysis interface"""
    static_dir = Path("static")
    html_file = static_dir / "contract-analysis.html"
    
    # Create the HTML file if it doesn't exist
    if not html_file.exists():
        html_content = """
<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Análisis de Contratos - MiAsistenteLegalIA</title>
    <!-- Your existing HTML content -->
  </head>
  <body>
    <div class="container mt-4">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Análisis de Contrato</h5>
                <form id="uploadForm" enctype="multipart/form-data">
                    <div class="form-group">
                        <input type="file" 
                               id="fileInput" 
                               name="file"
                               accept="application/pdf" 
                               style="display: none;"
                               onchange="handleFileSelect(this)">
                        <button type="button" 
                                class="btn btn-primary" 
                                onclick="document.getElementById('fileInput').click()">
                            Seleccionar PDF
                        </button>
                    </div>
                </form>
                <div class="loading-container mt-3" style="display: none;"></div>
                <div class="error-container mt-3" style="display: none;"></div>
                <div class="results-container mt-3" style="display: none;"></div>
            </div>
        </div>
    </div>
  </body>
</html>
"""
        # Create static directory if it doesn't exist
        static_dir.mkdir(parents=True, exist_ok=True)
        html_file.write_text(html_content, encoding="utf-8")
    
    return HTMLResponse(content=html_file.read_text(encoding="utf-8"))

@router.post("/contract-review/upload-analyze")
async def upload_and_analyze_contract(
    file: UploadFile = File(...),
    contract_type: str = Form("prestacion_servicios"),
    language: str = Form("es"),
    jurisdiction: str = Form("Colombia"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Upload and analyze a contract document
    """
    try:
        # Read file content
        content = await file.read()
        
        # Extract text using the unified function
        text_content = await extract_text_from_file_content(content, file.filename)
            
        # Prepare analysis request
        analysis_request = ContractAnalysisRequest(
            content=text_content,
            metadata={
                "file_name": file.filename,
                "file_type": file.content_type,
                "file_size": len(content)
            },
            analysis_options=AnalysisOptions(
                risk_analysis={
                    "financial": True,
                    "legal": True,
                    "compliance": True
                },
                clause_extraction={
                    "important": True,
                    "obligations": True,
                    "termination": True
                },
                compliance_check={
                    "regulatory": True,
                    "internal": True,
                    "industry": True
                }
            ),
            language=language,
            jurisdiction=jurisdiction
        )
        
        # Analyze the contract
        result = await analyze_contract_file(
            contract_text=text_content,
            contract_type=contract_type,
            specific_concerns=[
                "confidencialidad",
                "propiedad_intelectual",
                "terminacion_contrato"
            ],
            data_processing={
                "type": "datos_comerciales",
                "purpose": "ejecucion_contractual"
            },
            user_id=current_user.get("user_id"),  # Use authenticated user's UUID
            session_id=f"contract_{current_user.get('user_id')}_{datetime.now().timestamp()}"
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail={
                "message": f"Error processing file: {str(e)}",
                "type": "processing_error"
            }
        )

async def extract_text_from_file_content(content: bytes, filename: str) -> str:
    """Extract text from file content using appropriate method based on file type"""
    try:
        logger.info(f"Extracting text from file {filename} with {len(content)} bytes")
        
        # Determine file type based on filename extension
        file_extension = Path(filename).suffix.lower()
        if file_extension == '.pdf':
            file_type = 'application/pdf'
        elif file_extension in ['.docx', '.doc']:
            file_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        else:
            file_type = 'application/octet-stream'
        
        # Extract text using the unified function
        extracted_text = await extract_text_from_file(content, file_type)
        
        if extracted_text:
            logger.info(f"Total extracted text length: {len(extracted_text)}")
            return extracted_text
        else:
            logger.error(f"Failed to extract text from {filename}")
            raise HTTPException(
                status_code=422,
                detail=f"Could not extract text from {filename}. The file might be corrupted or in an unsupported format."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting text from {filename}: {str(e)}")
        raise HTTPException(
            status_code=422,
            detail=f"Error extracting text from {filename}: {str(e)}"
        )

# Download and Upload Models
class DownloadContractAnalysisRequest(BaseModel):
    analysis_data: Dict[str, Any] = Field(..., description="Contract analysis data to download")
    contract_type: str = Field(default="contract_analysis", description="Type of contract analysis")
    format: str = Field(default="pdf", description="Download format (pdf, docx)")

class UploadContractFileRequest(BaseModel):
    file_url: Optional[str] = Field(None, description="URL of the file to upload")
    contract_type: str = Field(default="contract_analysis", description="Type of contract")

class ContractFileUploadResponse(BaseModel):
    success: bool
    message: str
    file_url: Optional[str] = None
    file_metadata: Optional[Dict[str, Any]] = None

@router.post("/contract-review/download-analysis")
async def download_contract_analysis(
    request: DownloadContractAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Download contract analysis results as PDF
    """
    try:
        user_id = current_user.get("user_id")
        session_id = f"download_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Generate PDF content
        from utils.r2_storage import generate_contract_analysis_pdf
        pdf_content = generate_contract_analysis_pdf(
            request.analysis_data,
            user_id,
            session_id,
            request.contract_type
        )
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(pdf_content)
            temp_file_path = temp_file.name
        
        # Add cleanup task
        background_tasks.add_task(os_module.unlink, temp_file_path)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"contract_analysis_{request.contract_type}_{timestamp}.pdf"
        
        # Return the file
        return FileResponse(
            temp_file_path,
            media_type='application/pdf',
            filename=filename
        )
        
    except Exception as e:
        logger.error(f"Error generating contract analysis PDF: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating contract analysis PDF: {str(e)}"
        )

@router.post("/contract-review/upload-to-r2")
async def upload_contract_file_to_r2(
    file: UploadFile = File(...),
    contract_type: str = Form("contract_analysis"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Upload a contract file to R2 storage
    """
    try:
        user_id = current_user.get("user_id")
        session_id = f"upload_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Validate file
        if not FileValidator.validate_file_type(file):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {SECURITY_CONFIG.allowed_file_types}"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Validate file size
        if not FileValidator.validate_file_size(len(file_content)):
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {SECURITY_CONFIG.max_file_size} bytes"
            )
        
        # Upload to R2
        from utils.r2_storage import upload_contract_file_to_r2
        file_url = await upload_contract_file_to_r2(
            file_content=file_content,
            filename=file.filename,
            user_id=user_id,
            session_id=session_id,
            contract_type=contract_type
        )
        
        # Get file metadata
        file_metadata = {
            "original_filename": file.filename,
            "file_size": len(file_content),
            "content_type": file.content_type,
            "uploaded_at": datetime.now().isoformat(),
            "user_id": user_id,
            "session_id": session_id,
            "contract_type": contract_type
        }
        
        return ContractFileUploadResponse(
            success=True,
            message="File uploaded successfully to R2 storage",
            file_url=file_url,
            file_metadata=file_metadata
        )
        
    except Exception as e:
        logger.error(f"Error uploading contract file to R2: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading contract file to R2: {str(e)}"
        )

@router.post("/contract-review/upload-analysis-to-r2")
async def upload_contract_analysis_to_r2(
    analysis_data: Dict[str, Any] = Body(...),
    contract_type: str = Body(default="contract_analysis"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Upload contract analysis results to R2 storage as PDF
    """
    try:
        user_id = current_user.get("user_id")
        session_id = f"analysis_upload_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Upload analysis PDF to R2
        from utils.r2_storage import upload_contract_analysis_pdf_to_r2
        pdf_url = await upload_contract_analysis_pdf_to_r2(
            analysis_data=analysis_data,
            user_id=user_id,
            session_id=session_id,
            contract_type=contract_type
        )
        
        return {
            "success": True,
            "message": "Contract analysis uploaded successfully to R2 storage",
            "pdf_url": pdf_url,
            "metadata": {
                "user_id": user_id,
                "session_id": session_id,
                "contract_type": contract_type,
                "uploaded_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error uploading contract analysis to R2: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading contract analysis to R2: {str(e)}"
        )

@router.get("/contract-review/list-documents")
async def list_contract_documents(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    List contract analysis documents for the current user
    """
    try:
        user_id = current_user.get("user_id")
        
        # List documents from R2
        from utils.r2_storage import list_contract_analysis_documents
        documents = await list_contract_analysis_documents(user_id=user_id)
        
        return {
            "success": True,
            "documents": documents,
            "count": len(documents),
            "user_id": user_id
        }
        
    except Exception as e:
        logger.error(f"Error listing contract documents: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing contract documents: {str(e)}"
        )

@router.get("/contract-review/download-document/{document_key}")
async def download_contract_document(
    document_key: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Download a specific contract document from R2 storage
    """
    try:
        user_id = current_user.get("user_id")
        
        # Get Supabase S3 client
        from utils.r2_storage import get_contract_analysis_supabase_s3_client
        s3_client = get_contract_analysis_supabase_s3_client()
        
        # Download file from Supabase S3
        # The document_key should already be the correct object key
        response = s3_client.get_object(
            Bucket='contract-analisis',  # Use the Supabase S3 bucket
            Key=document_key
        )
        
        # Get file content
        file_content = response['Body'].read()
        
        # Get metadata
        metadata = response.get('Metadata', {})
        
        # Determine content type
        content_type = response.get('ContentType', 'application/pdf')
        
        # Generate filename
        filename = document_key.split('/')[-1] if '/' in document_key else document_key
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        # Return file response
        return FileResponse(
            temp_file_path,
            media_type=content_type,
            filename=filename
        )
        
    except Exception as e:
        logger.error(f"Error downloading contract document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error downloading contract document: {str(e)}"
        ) 