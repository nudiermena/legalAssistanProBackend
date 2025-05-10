from fastapi import APIRouter, Body, HTTPException, Depends, Request, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse
from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field, ValidationError
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
from utils.pdf_processor import extract_text_from_pdf_content
import magic  # pip install python-magic
import json
import io
import tempfile
import os
import PyPDF2
import fitz  # PyMuPDF
import shutil
import mimetypes

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
        schema_extra = {
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
    metadata: Metadata
    analysis_options: AnalysisOptions
    language: str = Field(default="es", description="Language of the contract")
    jurisdiction: str = Field(default="Colombia", description="Jurisdiction of the contract")

    class Config:
        schema_extra = {
            "example": {
                "content": "Entre los suscritos a saber...",
                "metadata": {
                    "file_name": "contrato.pdf",
                    "file_type": "application/pdf",
                    "file_size": 1024
                },
                "analysis_options": {
                    "risk_analysis": {
                        "financial": True,
                        "legal": True,
                        "compliance": True
                    },
                    "clause_extraction": {
                        "important": True,
                        "obligations": True,
                        "termination": True
                    },
                    "compliance_check": {
                        "regulatory": True,
                        "internal": True,
                        "industry": True
                    }
                },
                "language": "es",
                "jurisdiction": "Colombia"
            }
        }

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

def sanitize_text(text: str) -> str:
    """
    Sanitize text by removing control characters and normalizing Unicode characters
    """
    if not text:
        return ""
    
    # Normalize Unicode characters
    text = unicodedata.normalize('NFKD', text)
    
    # Remove control characters but keep newlines and tabs
    text = ''.join(char for char in text if char == '\n' or char == '\t' or (ord(char) >= 32 and ord(char) != 127))
    
    return text.strip()

def extract_text_from_pdf_content(pdf_content: bytes) -> Optional[str]:
    """
    Extract and clean text from PDF content
    """
    try:
        # Create a temporary file-like object in memory
        from io import BytesIO
        pdf_file = BytesIO(pdf_content)
        
        # Extract text using pdfplumber
        with pdfplumber.open(pdf_file) as pdf:
            text_parts = []
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                if page_text:
                    # Clean and sanitize the text
                    cleaned_text = sanitize_text(page_text)
                    if cleaned_text:
                        text_parts.append(cleaned_text)
            
            # Join all parts with newlines
            final_text = '\n'.join(text_parts)
            return final_text if final_text else None
            
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {str(e)}")
        return None

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
    """Extract text from PDF bytes using a temporary file."""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        try:
            # Write PDF bytes to temporary file
            tmp_file.write(pdf_bytes)
            tmp_file.flush()
            
            # Extract text using pdfplumber
            with pdfplumber.open(tmp_file.name) as pdf:
                text = []
                for page in pdf.pages:
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text.append(page_text.strip())
                    except Exception as e:
                        logger.warning(f"Error extracting text from page: {str(e)}")
                        continue
                
                return '\n'.join(text)
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            raise
        finally:
            # Clean up temporary file
            try:
                os.unlink(tmp_file.name)
            except Exception as e:
                logger.warning(f"Error removing temporary file: {str(e)}")

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

@router.post("/analyze")
async def analyze_contract(
    file: Optional[UploadFile] = File(None),
    request: Optional[ContractReviewRequest] = None
):
    """Analyze a contract file and provide legal insights"""
    try:
        if not file and not request:
            raise HTTPException(status_code=400, detail="No file or request provided")
        
        if file:
            # Get file type using mimetypes
            file_type = get_file_type(file.filename)
            
            # Read file content
            content = await file.read()
            
            # Validate PDF if it's supposed to be one
            if file_type == 'application/pdf':
                is_valid, error_msg = validate_pdf_content(content)
                if not is_valid:
                    raise HTTPException(status_code=422, detail=error_msg)
                
                # Extract text from PDF
                text_content = extract_text_from_pdf(content)
            else:
                text_content = content.decode('utf-8')
            
            # Create a temporary file
            temp_file_path = f"temp_{file.filename}"
            try:
                with open(temp_file_path, "wb") as temp_file:
                    temp_file.write(content)
                
                # Analyze the contract
                result = await analyze_contract_file(
                    file_path=temp_file_path,
                    file_type=file_type,
                    instructions=request.instructions if request else None
                )
                
                return format_response(result)
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
        else:
            # Handle text-based analysis
            result = await analyze_contract_file(
                text=request.text,
                instructions=request.instructions
            )
            return format_response(result)
            
    except Exception as e:
        return handle_error(e)

@router.get(
    "/contract-types",
    response_model=Dict[str, List[str]],
    summary="Tipos de Contratos",
    description="Obtiene los tipos de contratos disponibles para análisis"
)
async def get_contract_types():
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
async def get_contract_analysis_interface(request: Request):
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
    <title>Análisis de Contratos - LegalTechAI</title>
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
    jurisdiction: str = Form("Colombia")
):
    """
    Upload and analyze a contract document
    """
    try:
        # Read file content
        content = await file.read()
        
        # Extract text based on file type
        if file.filename.lower().endswith('.pdf'):
            text_content = extract_text_from_pdf(content)
        else:
            text_content = content.decode('utf-8')
            
        # Prepare analysis request
        analysis_request = ContractAnalysisRequest(
            content=text_content,
            metadata=Metadata(
                file_name=file.filename,
                file_type=file.content_type,
                file_size=len(content)
            ),
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
            }
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

def extract_text_from_pdf(content: bytes) -> str:
    """Extract text from PDF content using pypdf"""
    try:
        with BytesIO(content) as pdf_file:
            reader = PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise HTTPException(
            status_code=422,
            detail=f"Error extracting text from PDF: {str(e)}"
        ) 