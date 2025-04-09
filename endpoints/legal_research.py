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

class LegalResearchResponse(BaseModel):
    research_results: Dict[str, Any] = Field(
        ..., 
        description="Resultados de la investigación"
    )
    research_topic: str = Field(
        ..., 
        description="Tema investigado"
    )
    jurisdiction: str = Field(
        ..., 
        description="Jurisdicción"
    )
    colombian_compliance: Dict[str, Any] = Field(
        ..., 
        description="Cumplimiento normativo colombiano"
    )
    legal_framework: Dict[str, List[str]] = Field(
        ..., 
        description="Marco jurídico aplicable"
    )
    jurisprudence: Optional[List[Dict[str, str]]] = Field(
        None, 
        description="Jurisprudencia relevante"
    )
    specific_areas: Optional[List[str]] = Field(
        None,
        description="Áreas específicas analizadas"
    )
    data_processing: Optional[Dict[str, str]] = Field(
        None,
        description="Detalles de tratamiento de datos"
    )
    legal_terms: Optional[Dict[str, str]] = Field(
        None,
        description="Definiciones jurídicas"
    )
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "research_results": {
                    "analisis_normativo": "La telemedicina en Colombia...",
                    "jurisprudencia_relevante": [
                        "Sentencia T-123/2023: Establece...",
                        "Sentencia C-456/2022: Define..."
                    ],
                    "doctrina_aplicable": "Los autores coinciden...",
                    "recomendaciones": "Se sugiere considerar..."
                },
                "research_topic": "Responsabilidad civil en telemedicina",
                "jurisdiction": "Colombia",
                "colombian_compliance": {
                    "framework_version": "2024.1",
                    "constitutional_principles": [
                        "Debido proceso",
                        "Acceso a la justicia"
                    ],
                    "data_protection": "Cumple Ley 1581 de 2012"
                },
                "legal_framework": {
                    "leyes": [
                        "Ley 2213 de 2022",
                        "Ley 1581 de 2012"
                    ],
                    "decretos": [
                        "Decreto 538 de 2020"
                    ],
                    "resoluciones": [
                        "Resolución 2654 de 2019"
                    ]
                }
            }
        }

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
        
        return LegalResearchResponse(**result)
    
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