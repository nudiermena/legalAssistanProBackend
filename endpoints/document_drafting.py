from fastapi import APIRouter, HTTPException, Body, Depends, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict, validator
from datetime import datetime
from agents.document_drafting_agent import draft_legal_document
from config.colombian_compliance import ColombianLegalFramework
from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO
import markdown
import os
import shutil
import tempfile
from utils.r2_storage import upload_document_to_r2

# Create a single router without prefix - we'll specify full paths
router = APIRouter(tags=["documents"])

class Party(BaseModel):
    name: str
    role: str = Field(default="Parte")
    details: Optional[str] = None

class DocumentDraftingRequest(BaseModel):
    document_type: str = Field(..., description="Tipo de documento")
    jurisdiction: str = Field(default="Colombia", description="Jurisdicción")
    key_requirements: List[str] = Field(default_factory=list, description="Requisitos clave")
    parties: List[Dict[str, str]] = Field(..., description="Partes")
    legal_terms: Optional[List[str]] = Field(default_factory=list, description="Términos jurídicos")
    data_processing: Optional[Dict[str, str]] = Field(default_factory=dict, description="Tratamiento de datos")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "document_type": "contrato_laboral",
                "key_requirements": ["Término indefinido", "Período de prueba"],
                "parties": [
                    {"name": "Empresa ABC", "role": "Empleador"},
                    {"name": "Juan Pérez", "role": "Trabajador"}
                ]
            }
        }
    )

class DocumentDraftingResponse(BaseModel):
    document: Dict[str, Union[str, List[str], bool]] = Field(..., description="Documento generado")
    document_type: str = Field(..., description="Tipo de documento")
    jurisdiction: str = Field(..., description="Jurisdicción")
    key_requirements: List[str] = Field(..., description="Requisitos")
    parties: List[Dict[str, str]] = Field(..., description="Partes")
    colombian_compliance: Dict[str, Any] = Field(..., description="Cumplimiento")
    legal_terms: Optional[Dict[str, str]] = None
    data_processing: Optional[Dict[str, str]] = Field(
        None,
        description="Configuración de tratamiento de datos",
        example={
            "category": "personal",
            "retention_period": "365 días",
            "consent_valid": "true",
            "requirements": "Requisitos estándar de protección de datos"
        }
    )
    document_url: Optional[str] = Field(None, description="URL del documento en R2")
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "document": {
                    "content": "Entre los suscritos...",
                    "sections": ["Partes", "Objeto", "Obligaciones"],
                    "markdown": True
                },
                "document_url": "https://document-generator.r2.dev/contrato_laboral_123.docx"
            }
        }
    )

def create_word_document(content: str, document_type: str) -> BytesIO:
    """Create a Word document from markdown content."""
    # Convert markdown to HTML
    html_content = markdown.markdown(content)
    
    # Create a new Word document
    doc = Document()
    
    # Set up the document style
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(11)
    
    # Add title
    title = doc.add_heading(document_type.replace('_', ' ').title(), 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Add content
    paragraphs = html_content.split('\n')
    for para in paragraphs:
        if para.strip():
            p = doc.add_paragraph()
            p.add_run(para.strip())
    
    # Save to BytesIO
    doc_io = BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    return doc_io

@router.get(
    "/dashboard/document-drafting/",
    response_class=HTMLResponse,
    summary="Interface de Redacción de Documentos",
    description="Sirve la interfaz web para redacción de documentos"
)
async def get_document_drafting_interface(request: Request):
    """Serve the document drafting interface"""
    static_dir = Path("static")
    html_file = static_dir / "document-drafting.html"
    
    if not html_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Document drafting interface not found"
        )
    
    try:
        return HTMLResponse(content=html_file.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading document drafting interface: {str(e)}"
        )

@router.post(
    "/api/v1/draft-document",
    response_model=DocumentDraftingResponse,
    summary="Generación de Documentos Jurídicos",
    description="Genera documentos jurídicos según el ordenamiento jurídico colombiano"
)
async def draft_document_endpoint(
    request: DocumentDraftingRequest = Body(
        ...,
        description="Parámetros para la generación del documento"
    )
):
    """Genera documentos jurídicos con cumplimiento normativo colombiano"""
    try:
        party_names = [party.get("name", "") for party in request.parties]
        
        result = await draft_legal_document(
            document_type=request.document_type,
            jurisdiction=request.jurisdiction,
            key_requirements=request.key_requirements,
            parties=party_names,
            legal_terms=request.legal_terms,
            data_processing=request.data_processing
        )
        
        # Create Word document
        doc_io = create_word_document(result["document"]["content"], request.document_type)
        
        # Upload to R2
        document_url = await upload_document_to_r2(doc_io, request.document_type)
        
        response_data = {
            "document": result["document"],
            "document_type": result["document_type"],
            "jurisdiction": result["jurisdiction"],
            "key_requirements": result["key_requirements"],
            "parties": result["parties"],
            "colombian_compliance": result["colombian_compliance"],
            "legal_terms": result.get("legal_terms"),
            "data_processing": result.get("data_processing"),
            "document_url": document_url,
            "timestamp": datetime.now()
        }
        
        return DocumentDraftingResponse(**response_data)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "message": "Error en la generación del documento",
                "timestamp": datetime.now().isoformat()
            }
        )

@router.get(
    "/document-drafting/templates",
    response_model=Dict[str, List[str]],
    summary="Plantillas Disponibles",
    description="Obtiene las plantillas de documentos jurídicos disponibles"
)
async def get_document_templates():
    """Retorna las plantillas de documentos disponibles"""
    return {
        "contratos_laborales": [
            "Término indefinido",
            "Término fijo",
            "Obra o labor",
            "Aprendizaje"
        ],
        "contratos_comerciales": [
            "Compraventa",
            "Arrendamiento",
            "Prestación de servicios",
            "Distribución"
        ],
        "documentos_societarios": [
            "Acta de constitución",
            "Reforma estatutaria",
            "Acta de asamblea",
            "Poder especial"
        ],
        "documentos_procesales": [
            "Demanda",
            "Contestación",
            "Recurso de apelación",
            "Tutela"
        ]
    }

def get_legal_framework(doc_type: str, requirements: List[str]) -> Dict[str, List[str]]:
    """Obtiene marco jurídico según tipo de documento y requisitos"""
    return {
        "normativa": ["Norma 1", "Norma 2"],
        "jurisprudencia": ["Sentencia 1", "Sentencia 2"],
        "doctrina": ["Doctrina 1", "Doctrina 2"]
    }

def cleanup_temp_file(file_path: str):
    """Remove temporary file after download"""
    try:
        os.unlink(file_path)
    except Exception as e:
        print(f"Error cleaning up temporary file: {e}")

@router.post("/download-document")
async def download_document(
    background_tasks: BackgroundTasks,
    document_content: dict = Body(..., description="Contenido del documento")
):
    """Endpoint para descargar el documento en formato Word."""
    try:
        content = document_content.get("content", "")
        document_type = document_content.get("document_type", "documento")
        
        if not content:
            raise HTTPException(status_code=400, detail="No se proporcionó contenido para el documento")
        
        # Create Word document
        doc_io = create_word_document(content, document_type)
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_file:
            temp_file.write(doc_io.getvalue())
            temp_file_path = temp_file.name
        
        # Add cleanup task
        background_tasks.add_task(os.unlink, temp_file_path)
        
        # Return the file
        return FileResponse(
            temp_file_path,
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            filename=f"{document_type}_{datetime.now().strftime('%Y%m%d')}.docx"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el documento Word: {str(e)}") 