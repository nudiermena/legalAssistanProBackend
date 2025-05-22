from fastapi import APIRouter, Body, HTTPException, Depends, Request, BackgroundTasks
from fastapi.responses import FileResponse
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from models.request_models import LegalResearchRequest
from models.response_models import BaseResponse, format_response, handle_error
from agents.legal_research_agent import conduct_legal_research
from config.colombian_compliance import (
    ColombianLegalFramework,
    get_legal_areas,
    get_document_types,
    get_legal_term,
    validate_jurisdiction
)
from pathlib import Path
import tempfile
import os
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import markdown
import shutil
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
import json
import re

router = APIRouter(prefix="/dashboard/legal-research", tags=["research"])

@router.get("/", response_class=FileResponse)
async def get_legal_research_page():
    """Serves the legal research HTML page"""
    try:
        html_path = Path("static/legal-research.html")
        if not html_path.exists():
            raise HTTPException(status_code=404, detail="HTML file not found")
        return FileResponse(html_path)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error serving legal research page: {str(e)}"
        )

class LegalResearchRequest(BaseModel):
    research_topic: str = Field(
        ..., 
        description="Tema de investigación jurídica"
    )
    jurisdiction: str = Field(
        default="Colombia",
        description="Jurisdicción aplicable"
    )
    specific_areas: Optional[List[str]] = Field(
        None,
        description="Áreas específicas del derecho"
    )
    data_processing: Optional[Dict[str, str]] = Field(
        None,
        description="Tratamiento de datos de la investigación"
    )
    legal_terms: Optional[List[str]] = Field(
        None,
        description="Términos jurídicos relevantes"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "research_topic": "Responsabilidad civil en telemedicina",
                "jurisdiction": "Colombia",
                "specific_areas": [
                    "Derecho Médico",
                    "Derecho Digital",
                    "Responsabilidad Civil"
                ],
                "data_processing": {
                    "type": "investigacion_juridica",
                    "purpose": "analisis_academico"
                },
                "legal_terms": [
                    "consentimiento_informado",
                    "historia_clinica_electronica",
                    "responsabilidad_medica"
                ]
            }
        }

class Case(BaseModel):
    title: str
    court: str
    date: str
    jurisdiction: str
    summary: str
    tags: List[str]
    relevance: float
    url: Optional[str] = None

class Legislation(BaseModel):
    title: str
    type: str
    date: str
    jurisdiction: str
    summary: str
    tags: List[str]
    url: Optional[str] = None

class Article(BaseModel):
    title: str
    author: str
    date: str
    source: str
    summary: str
    tags: List[str]
    url: Optional[str] = None

class LegalResearchResponse(BaseModel):
    cases: List[Case]
    legislation: List[Legislation]
    articles: List[Article]
    summary: str
    statistics: Dict[str, Any]
    research_topic: str = Field(..., description="Tema investigado")
    jurisdiction: str = Field(..., description="Jurisdicción")
    colombian_compliance: Dict[str, Any] = Field(..., description="Cumplimiento normativo colombiano")
    legal_framework: Dict[str, List[str]] = Field(..., description="Marco jurídico aplicable")
    jurisprudence: Optional[List[Dict[str, str]]] = Field(None, description="Jurisprudencia relevante")
    specific_areas: Optional[List[str]] = Field(None, description="Áreas específicas analizadas")
    data_processing: Optional[Dict[str, str]] = Field(None, description="Detalles de tratamiento de datos")
    legal_terms: Optional[Dict[str, str]] = Field(None, description="Definiciones jurídicas")
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "cases": [
                    {
                        "title": "Corte Suprema de Justicia - Sala Laboral - Exp. SL-2023-4567",
                        "court": "Corte Suprema de Justicia",
                        "date": "2023-03-12",
                        "jurisdiction": "Colombia - Nacional",
                        "summary": "En este caso se estableció un precedente importante...",
                        "tags": ["Despido sin justa causa", "Indemnización", "Código Sustantivo del Trabajo"],
                        "relevance": 0.95,
                        "url": "https://ejemplo.com/caso1"
                    }
                ],
                "legislation": [
                    {
                        "title": "Ley 1581 de 2012",
                        "type": "Ley",
                        "date": "2012-10-17",
                "jurisdiction": "Colombia",
                        "summary": "Ley de protección de datos personales...",
                        "tags": ["Protección de datos", "Privacidad"],
                        "url": "https://ejemplo.com/ley1581"
                    }
                ],
                "articles": [
                    {
                        "title": "La evolución de la protección de datos en Colombia",
                        "author": "Juan Pérez",
                        "date": "2023-01-10",
                        "source": "Revista Jurídica",
                        "summary": "Este artículo analiza la evolución...",
                        "tags": ["Protección de datos", "Doctrina"],
                        "url": "https://ejemplo.com/articulo1"
                    }
                ],
                "summary": "Resumen ejecutivo de la investigación...",
                "statistics": {
                    "total_results": 25,
                    "national_jurisdiction": 21,
                    "international_jurisdiction": 4,
                    "cases": 12,
                    "legislation": 8,
                    "articles": 5,
                    "excluded": 7
                },
                # ...other example fields as before...
            }
        }

def extract_json_from_markdown(summary: str):
    match = re.search(r"```json\s*([\s\S]+?)```", summary)
    if match:
        json_str = match.group(1)
        try:
            return json.loads(json_str)
        except Exception:
            return None
    return None

def normalize_relevance(val):
    if isinstance(val, (float, int)):
        return float(val)
    if isinstance(val, str):
        mapping = {"high": 1.0, "alta": 1.0, "media": 0.7, "medium": 0.7, "baja": 0.4, "low": 0.4}
        return mapping.get(val.strip().lower(), 0.0)
    return 0.0

def normalize_summary(val):
    if isinstance(val, str):
        return val
    if isinstance(val, dict):
        return val.get("executive_summary") or " ".join(str(v) for v in val.values())
    return str(val)

def sanitize_for_json(obj):
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    elif hasattr(obj, 'text'):
        return str(getattr(obj, 'text'))
    elif not isinstance(obj, (str, int, float, bool, type(None))):
        return str(obj)
    return obj

@router.post(
    "/investigate",
    response_model=LegalResearchResponse,
    summary="Investigación Jurídica Especializada",
    description="""
    Realiza investigación jurídica especializada según el ordenamiento jurídico
    colombiano, incluyendo análisis de jurisprudencia, doctrina y normativa aplicable.
    """
)
async def research_endpoint(
    request: LegalResearchRequest = Body(
        ...,
        description="Parámetros de investigación jurídica"
    )
):
    """Realiza investigación jurídica con cumplimiento normativo colombiano"""
    try:
        result = await conduct_legal_research(
            research_topic=request.research_topic,
            jurisdiction=request.jurisdiction,
            specific_areas=request.specific_areas,
            data_processing=request.data_processing,
            legal_terms=request.legal_terms
        )
        
        # Try to parse the agent's response as JSON and map to new fields
        try:
            if isinstance(result, dict) and 'cases' in result and 'legislation' in result and 'articles' in result:
                # Already structured
                structured = result
            else:
                # Try to parse from string (if agent returns JSON as string)
                structured = json.loads(result["research_results"]["analisis_normativo"])

            response_data = {
                "cases": structured.get("cases", []),
                "legislation": structured.get("legislation", []),
                "articles": structured.get("articles", []),
                "summary": structured.get("summary", ""),
                "statistics": structured.get("statistics", {}),
                "research_topic": result.get("research_topic", request.research_topic),
                "jurisdiction": result.get("jurisdiction", request.jurisdiction),
                "colombian_compliance": result.get("colombian_compliance", {}),
                "legal_framework": result.get("legal_framework", {}),
                "jurisprudence": result.get("jurisprudence"),
                "specific_areas": result.get("specific_areas"),
                "data_processing": result.get("data_processing"),
                "legal_terms": result.get("legal_terms"),
                "timestamp": datetime.now()
            }
        except Exception:
            # Fallback: fill new fields with defaults, use old structure for summary
            response_data = {
                "cases": [],
                "legislation": [],
                "articles": [],
                "summary": result["research_results"]["analisis_normativo"],
                "statistics": {},
                "research_topic": result.get("research_topic", request.research_topic),
                "jurisdiction": result.get("jurisdiction", request.jurisdiction),
                "colombian_compliance": result.get("colombian_compliance", {}),
                "legal_framework": result.get("legal_framework", {}),
                "jurisprudence": result.get("jurisprudence"),
                "specific_areas": result.get("specific_areas"),
                "data_processing": result.get("data_processing"),
                "legal_terms": result.get("legal_terms"),
                "timestamp": datetime.now()
            }

        # If cases, legislation, and articles are empty, try to extract from embedded JSON in summary
        if not response_data["cases"] and not response_data["legislation"] and not response_data["articles"]:
            embedded = extract_json_from_markdown(response_data["summary"])
            if embedded:
                embedded = sanitize_for_json(embedded)
                response_data["cases"] = embedded.get("cases", [])
                response_data["legislation"] = embedded.get("legislation", [])
                response_data["articles"] = embedded.get("articles", [])
                response_data["summary"] = embedded.get("summary", response_data["summary"])
                response_data["statistics"] = embedded.get("statistics", {})

        # Normalize relevance in cases
        for case in response_data["cases"]:
            if "relevance" in case:
                case["relevance"] = normalize_relevance(case["relevance"])

        # Normalize summary
        response_data["summary"] = normalize_summary(response_data["summary"])

        return LegalResearchResponse(**response_data)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "message": "Error en la investigación jurídica",
                "timestamp": datetime.now().isoformat()
            }
        )

@router.get("/areas")
async def get_research_areas():
    """Get available legal research areas"""
    return get_legal_areas()

@router.get("/document-types")
async def get_available_document_types():
    """Get available document types"""
    return {
        "types": get_document_types(),
        "framework_version": ColombianLegalFramework.FRAMEWORK_VERSION
    }

def get_relevant_laws(areas: Optional[List[str]]) -> List[str]:
    """Obtiene leyes relevantes según el área de investigación"""
    # Implementation would connect to a database or knowledge base
    return ["Ley relevante 1", "Ley relevante 2"]

def get_relevant_jurisprudence(topic: str, timeframe: Optional[str]) -> List[Dict[str, str]]:
    """Obtiene jurisprudencia relevante según tema y período"""
    # Implementation would connect to a jurisprudence database
    return [{"sentencia": "T-123/23", "relevancia": "Alta"}]

def get_relevant_doctrine(topic: str) -> List[str]:
    """Obtiene doctrina relevante según el tema"""
    # Implementation would connect to a doctrine database
    return ["Doctrina relevante 1", "Doctrina relevante 2"]

# Add this new model
class DraftRequest(BaseModel):
    research_topic: str
    document_type: str
    research_results: Dict[str, Any]
    legal_framework: Dict[str, Any]
    jurisprudence: list

class DraftResponse(BaseModel):
    content: str
    document_type: str
    timestamp: datetime = Field(default_factory=datetime.now)

# Add this new endpoint
@router.post("/generate-draft", response_model=DraftResponse)
async def generate_draft(request: DraftRequest):
    """Generate a document draft based on research results"""
    try:
        # Get the template based on document type
        template = get_document_template(request.document_type)
        
        # Generate the markdown content
        content = await generate_markdown_content(
            template=template,
            topic=request.research_topic,
            results=request.research_results,
            framework=request.legal_framework,
            jurisprudence=request.jurisprudence
        )
        
        return DraftResponse(
            content=content,
            document_type=request.document_type,
            timestamp=datetime.now()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "message": "Error generando borrador",
                "timestamp": datetime.now().isoformat()
            }
        )

def get_document_template(doc_type: str) -> str:
    """Get the markdown template for the document type"""
    templates = {
        "Demanda": """
# Demanda

## 1. Datos de las Partes

### 1.1 Demandante
[Información del demandante]

### 1.2 Demandado
[Información del demandado]

## 2. Hechos
{facts}

## 3. Fundamentos de Derecho
{legal_basis}

## 4. Pretensiones
{claims}

## 5. Pruebas
{evidence}

## 6. Anexos
{attachments}
""",
        "Contestación": """
# Contestación de Demanda

## 1. Identificación del Proceso
{case_info}

## 2. Pronunciamiento sobre los Hechos
{facts_response}

## 3. Excepciones
{exceptions}

## 4. Pruebas
{evidence}

## 5. Peticiones
{requests}
""",
        "Recurso": """
# Recurso

## 1. Identificación de la Decisión Recurrida
{decision_info}

## 2. Fundamentos del Recurso
{grounds}

## 3. Argumentos Jurídicos
{legal_arguments}

## 4. Petición
{petition}
""",
        "Informe": """
# Informe Jurídico

## 1. Resumen Ejecutivo
{executive_summary}

## 2. Análisis Legal
{legal_analysis}

## 3. Conclusiones
{conclusions}

## 4. Recomendaciones
{recommendations}
"""
    }
    
    return templates.get(doc_type, "# Documento\n\n## Contenido\n")

async def generate_markdown_content(
    template: str,
    topic: str,
    results: Dict[str, Any],
    framework: Dict[str, Any],
    jurisprudence: list
) -> str:
    """Generate markdown content based on research results"""
    
    # Extract relevant information from results
    analysis = results.get("analisis_normativo", "")
    relevant_cases = results.get("jurisprudencia_relevante", [])
    doctrine = results.get("doctrina_aplicable", "")
    recommendations = results.get("recomendaciones", [])
    
    # Format legal framework
    legal_framework_text = "\n".join([
        f"- {law}" for laws in framework.values() for law in laws
    ])
    
    # Format jurisprudence
    jurisprudence_text = "\n".join([
        f"- {case}" for case in jurisprudence
    ])
    
    # Replace template placeholders
    content = template.format(
        case_info=f"Tema: {topic}",
        facts_response=analysis,
        legal_basis=legal_framework_text,
        evidence=jurisprudence_text,
        legal_arguments=doctrine,
        conclusions="\n".join(recommendations),
        # Add other placeholders as needed
        **{
            "facts": analysis,
            "claims": "",
            "attachments": "",
            "exceptions": "",
            "requests": "",
            "decision_info": "",
            "grounds": "",
            "petition": "",
            "executive_summary": f"Análisis jurídico sobre: {topic}",
            "legal_analysis": analysis,
            "recommendations": "\n".join(recommendations)
        }
    )
    
    return content

class DownloadDraftRequest(BaseModel):
    content: str
    format: Literal["docx", "pdf", "txt"]
    document_type: str
    filename: str

    class Config:
        json_schema_extra = {
            "example": {
                "content": "# Sample Document\n\nThis is a sample document.",
                "format": "pdf",
                "document_type": "Informe Legal",
                "filename": "documento_legal"
            }
        }

@router.post("/download-draft")
async def download_draft(request: DownloadDraftRequest, background_tasks: BackgroundTasks):
    """Generate and download document in specified format"""
    try:
        temp_dir = tempfile.mkdtemp()
        
        if request.format == "docx":
            temp_file = create_word_document(
                content=request.content,
                document_type=request.document_type,
                temp_dir=temp_dir
            )
            mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            
        elif request.format == "pdf":
            temp_file = create_pdf_document(
                content=request.content,
                document_type=request.document_type,
                temp_dir=temp_dir
            )
            mime_type = "application/pdf"
            
        else:  # txt
            temp_file = create_text_document(
                content=request.content,
                document_type=request.document_type,
                temp_dir=temp_dir
            )
            mime_type = "text/plain"

        filename = f"{request.filename}.{request.format}"
        
        # Add cleanup task to run after response is sent
        background_tasks.add_task(cleanup_temp_dir, temp_dir)
        
        return FileResponse(
            path=temp_file,
            media_type=mime_type,
            filename=filename
        )
            
    except Exception as e:
        # Clean up if there's an error
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "message": "Error generando documento",
                "timestamp": datetime.now().isoformat()
            }
        )

def create_pdf_document(content: str, document_type: str, temp_dir: str) -> str:
    """Create a PDF document using ReportLab"""
    pdf_path = os.path.join(temp_dir, "document.pdf")
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Create styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        alignment=1,  # Center alignment
        spaceAfter=30,
        textColor=colors.HexColor('#2c3e50')
    )
    
    heading1_style = ParagraphStyle(
        'CustomH1',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#34495e'),
        spaceBefore=20,
        spaceAfter=10
    )
    
    heading2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceBefore=15,
        spaceAfter=8
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=12,
        leading=16,
        spaceBefore=6,
        spaceAfter=6
    )
    
    # Create the document content
    story = []
    
    # Add title
    story.append(Paragraph(document_type, title_style))
    story.append(Spacer(1, 20))
    
    # Process markdown content
    current_text = []
    in_list = False
    list_items = []
    
    for line in content.split('\n'):
        if line.strip():
            if line.startswith('# '):
                if current_text:
                    story.append(Paragraph('\n'.join(current_text), normal_style))
                    current_text = []
                story.append(Paragraph(line[2:], heading1_style))
            elif line.startswith('## '):
                if current_text:
                    story.append(Paragraph('\n'.join(current_text), normal_style))
                    current_text = []
                story.append(Paragraph(line[3:], heading2_style))
            elif line.startswith('* ') or line.startswith('- '):
                if not in_list:
                    if current_text:
                        story.append(Paragraph('\n'.join(current_text), normal_style))
                        current_text = []
                    in_list = True
                list_items.append(line[2:])
            else:
                if in_list:
                    # Create bullet list
                    for item in list_items:
                        story.append(Paragraph(f"• {item}", normal_style))
                    list_items = []
                    in_list = False
                current_text.append(line)
        else:
            if current_text:
                story.append(Paragraph('\n'.join(current_text), normal_style))
                current_text = []
            if in_list:
                for item in list_items:
                    story.append(Paragraph(f"• {item}", normal_style))
                list_items = []
                in_list = False
            story.append(Spacer(1, 12))
    
    # Add any remaining text
    if current_text:
        story.append(Paragraph('\n'.join(current_text), normal_style))
    if list_items:
        for item in list_items:
            story.append(Paragraph(f"• {item}", normal_style))
    
    # Add footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.gray,
        alignment=1
    )
    story.append(Spacer(1, 30))
    story.append(Paragraph(
        f"Generado por LegalTechAI - {datetime.now().strftime('%Y-%m-%d')}",
        footer_style
    ))
    
    # Build the PDF
    doc.build(story)
    return pdf_path

def create_word_document(content: str, document_type: str, temp_dir: str) -> str:
    """Create a Word document from markdown content"""
    doc = Document()
    
    # Add title
    title = doc.add_heading(document_type, 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Process markdown content
    current_text = []
    in_list = False
    list_items = []
    
    for line in content.split('\n'):
        if line.strip():
            if line.startswith('# '):
                if current_text:
                    p = doc.add_paragraph()
                    p.add_run('\n'.join(current_text))
                    current_text = []
                doc.add_heading(line[2:], 1)
            elif line.startswith('## '):
                if current_text:
                    p = doc.add_paragraph()
                    p.add_run('\n'.join(current_text))
                    current_text = []
                doc.add_heading(line[3:], 2)
            elif line.startswith('* ') or line.startswith('- '):
                if not in_list:
                    if current_text:
                        p = doc.add_paragraph()
                        p.add_run('\n'.join(current_text))
                        current_text = []
                    in_list = True
                list_items.append(line[2:])
            else:
                if in_list:
                    # Create bullet list
                    for item in list_items:
                        p = doc.add_paragraph(style='List Bullet')
                        p.add_run(item)
                    list_items = []
                    in_list = False
                current_text.append(line)
        else:
            if current_text:
                p = doc.add_paragraph()
                p.add_run('\n'.join(current_text))
                current_text = []
            if in_list:
                for item in list_items:
                    p = doc.add_paragraph(style='List Bullet')
                    p.add_run(item)
                list_items = []
                in_list = False
            doc.add_paragraph()
    
    # Add any remaining text
    if current_text:
        p = doc.add_paragraph()
        p.add_run('\n'.join(current_text))
    if list_items:
        for item in list_items:
            p = doc.add_paragraph(style='List Bullet')
            p.add_run(item)
    
    # Save document
    file_path = os.path.join(temp_dir, "document.docx")
    doc.save(file_path)
    return file_path

def create_text_document(content: str, document_type: str, temp_dir: str) -> str:
    """Create a text document from markdown content"""
    file_path = os.path.join(temp_dir, "document.txt")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f"{document_type}\n")
        f.write("=" * len(document_type) + "\n\n")
        f.write(content)
    
    return file_path

def cleanup_temp_dir(temp_dir: str):
    """Clean up temporary directory"""
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"Error cleaning up temporary directory: {e}") 