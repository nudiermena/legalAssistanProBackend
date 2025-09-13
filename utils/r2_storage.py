import boto3
from botocore.config import Config
# COMMENTED OUT - MIGRATING TO SUPABASE S3
# from config.cloudflare import (
#     R2_ACCESS_KEY_ID,
#     R2_SECRET_ACCESS_KEY,
#     R2_ENDPOINT,
#     R2_BUCKET_NAME,
#     R2_BUCKET_URL,
#     R2_LEGAL_RESEARCH_BUCKET_NAME,
#     R2_LEGAL_RESEARCH_BUCKET_URL,
#     R2_CONTRACT_ANALYSIS_BUCKET_NAME,
#     R2_CONTRACT_ANALYSIS_ENDPOINT
# )

# SUPABASE S3 Configuration
from config.cloudflare import (
    SUPABASE_S3_ACCESS_KEY_ID,
    SUPABASE_S3_SECRET_ACCESS_KEY,
    SUPABASE_S3_BUCKET_NAME,
    SUPABASE_S3_ENDPOINT,
    SUPABASE_S3_BUCKET_URL,
    SUPABASE_CONTRACT_ANALYSIS_BUCKET_NAME,
    SUPABASE_CONTRACT_ANALYSIS_ENDPOINT,
    SUPABASE_DOCUMENT_DRAFTING_BUCKET_NAME,
    SUPABASE_DOCUMENT_DRAFTING_ENDPOINT,
    SUPABASE_DOCUMENT_DRAFTING_BUCKET_URL
)
from typing import BinaryIO, Optional, Dict, Any
import uuid
import os
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
import json
import logging
from utils.pdf_generator import generate_contract_analysis_pdf

logger = logging.getLogger(__name__)

# COMMENTED OUT - MIGRATING TO SUPABASE S3
# def get_r2_client():
#     """Get configured R2 client with proper settings"""
#     return boto3.client(
#         's3',
#         endpoint_url=R2_ENDPOINT,
#         aws_access_key_id=R2_ACCESS_KEY_ID,
#         aws_secret_access_key=R2_SECRET_ACCESS_KEY,
#         config=Config(
#             signature_version='s3v4',
#             region_name='auto',  # Required for R2
#             max_pool_connections=50,  # Optimize connection pooling
#             retries={'max_attempts': 3}  # Add retry logic
#         )
#     )

# def get_contract_analysis_r2_client():
#     """Get R2 client specifically for contract analysis bucket"""
#     return boto3.client(
#         's3',
#         endpoint_url=R2_CONTRACT_ANALYSIS_ENDPOINT,
#         aws_access_key_id=R2_ACCESS_KEY_ID,
#         aws_secret_access_key=R2_SECRET_ACCESS_KEY,
#         config=Config(
#             signature_version='s3v4',
#             region_name='auto',  # Required for R2
#             max_pool_connections=50,  # Optimize connection pooling
#             retries={'max_attempts': 3}  # Add retry logic
#         )
#     )

def get_supabase_s3_client():
    """Get configured Supabase S3 client with proper settings"""
    return boto3.client(
        's3',
        endpoint_url=SUPABASE_S3_ENDPOINT,
        aws_access_key_id=SUPABASE_S3_ACCESS_KEY_ID,
        aws_secret_access_key=SUPABASE_S3_SECRET_ACCESS_KEY,
        config=Config(
            signature_version='s3v4',
            region_name='us-east-1',  # Supabase S3 region
            max_pool_connections=50,  # Optimize connection pooling
            retries={'max_attempts': 3}  # Add retry logic
        )
    )

def get_contract_analysis_supabase_s3_client():
    """Get Supabase S3 client specifically for contract analysis bucket"""
    return boto3.client(
        's3',
        endpoint_url=SUPABASE_CONTRACT_ANALYSIS_ENDPOINT,
        aws_access_key_id=SUPABASE_S3_ACCESS_KEY_ID,
        aws_secret_access_key=SUPABASE_S3_SECRET_ACCESS_KEY,
        config=Config(
            signature_version='s3v4',
            region_name='us-east-1',  # Supabase S3 region
            max_pool_connections=50,  # Optimize connection pooling
            retries={'max_attempts': 3}  # Add retry logic
        )
    )

def get_document_drafting_supabase_s3_client():
    """Get Supabase S3 client specifically for document drafting bucket"""
    return boto3.client(
        's3',
        endpoint_url=SUPABASE_DOCUMENT_DRAFTING_ENDPOINT,
        aws_access_key_id=SUPABASE_S3_ACCESS_KEY_ID,
        aws_secret_access_key=SUPABASE_S3_SECRET_ACCESS_KEY,
        config=Config(
            signature_version='s3v4',
            region_name='us-east-1',  # Supabase S3 region
            max_pool_connections=50,  # Optimize connection pooling
            retries={'max_attempts': 3}  # Add retry logic
        )
    )

async def upload_document_to_r2(
    file_content: BinaryIO, 
    document_type: str,
    content_type: str = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
) -> str:
    """
    Upload a document to R2 storage using multipart upload for larger files
    
    Args:
        file_content: Binary content of the file
        document_type: Type of document for naming
        content_type: MIME type of the document
        
    Returns:
        str: Public URL of the uploaded document
    """
    try:
        s3_client = get_document_drafting_supabase_s3_client()
        
        # Generate unique filename
        filename = f"{document_type}_{uuid.uuid4()}.docx"
        
        # Get file size
        file_content.seek(0, os.SEEK_END)
        file_size = file_content.tell()
        file_content.seek(0)
        
        # Common ExtraArgs for both upload methods
        extra_args = {
            'ContentType': content_type,
            'CacheControl': 'max-age=31536000',  # Cache for 1 year
            'ACL': 'public-read',  # Make object publicly readable
            'Metadata': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, PUT, POST, DELETE, HEAD',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Expose-Headers': 'ETag, Content-Length, Content-Type, Last-Modified'
            }
        }
        
        # Use multipart upload for files larger than 5MB
        if file_size > 5 * 1024 * 1024:  # 5MB
            mpu = s3_client.create_multipart_upload(
                Bucket=SUPABASE_DOCUMENT_DRAFTING_BUCKET_NAME,
                Key=filename,
                ContentType=content_type,
                Metadata=extra_args['Metadata']
            )
            
            parts = []
            chunk_size = 5 * 1024 * 1024  # 5MB chunks
            part_number = 1
            
            while True:
                chunk = file_content.read(chunk_size)
                if not chunk:
                    break
                    
                part = s3_client.upload_part(
                    Bucket=SUPABASE_DOCUMENT_DRAFTING_BUCKET_NAME,
                    Key=filename,
                    PartNumber=part_number,
                    UploadId=mpu['UploadId'],
                    Body=chunk
                )
                
                parts.append({
                    'PartNumber': part_number,
                    'ETag': part['ETag']
                })
                part_number += 1
            
            # Complete multipart upload
            s3_client.complete_multipart_upload(
                Bucket=SUPABASE_DOCUMENT_DRAFTING_BUCKET_NAME,
                Key=filename,
                UploadId=mpu['UploadId'],
                MultipartUpload={'Parts': parts}
            )
        else:
            # Simple upload for smaller files
            s3_client.upload_fileobj(
                file_content,
                SUPABASE_DOCUMENT_DRAFTING_BUCKET_NAME,
                filename,
                ExtraArgs=extra_args
            )
        
        # Generate public URL using the Supabase S3 bucket URL
        url = f"{SUPABASE_DOCUMENT_DRAFTING_BUCKET_URL}/{filename}"
        
        return url
        
    except Exception as e:
        raise Exception(f"Error uploading document to Supabase S3: {str(e)}")

async def upload_legal_research_pdf_to_r2(
    research_data: Dict[str, Any],
    user_id: str,
    session_id: str
) -> str:
    """
    Generate and upload a detailed PDF summary of legal research to R2 storage
    
    Args:
        research_data: Complete research results from the legal research agent
        user_id: User ID for tracking
        session_id: Session ID for tracking
        
    Returns:
        str: Public URL of the uploaded PDF
    """
    try:
        # Generate PDF content
        pdf_content = generate_legal_research_pdf(research_data, user_id, session_id)
        
        # Convert to binary stream
        pdf_stream = io.BytesIO(pdf_content)
        pdf_stream.seek(0)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"legal_research_{user_id}_{session_id}_{timestamp}.pdf"
        
        # Upload to R2
        s3_client = get_r2_client()
        
        extra_args = {
            'ContentType': 'application/pdf',
            'CacheControl': 'max-age=31536000',  # Cache for 1 year
            'ACL': 'public-read',  # Make object publicly readable
            'Metadata': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, PUT, POST, DELETE, HEAD',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Expose-Headers': 'ETag, Content-Length, Content-Type, Last-Modified',
                'user_id': user_id,
                'session_id': session_id,
                'document_type': 'legal_research_summary',
                'generated_at': datetime.now().isoformat()
            }
        }
        
        # Upload PDF
        s3_client.upload_fileobj(
            pdf_stream,
            R2_LEGAL_RESEARCH_BUCKET_NAME,
            filename,
            ExtraArgs=extra_args
        )
        
        # Generate public URL
        url = f"{R2_LEGAL_RESEARCH_BUCKET_URL}/{filename}"
        
        return url
        
    except Exception as e:
        raise Exception(f"Error uploading legal research PDF to R2: {str(e)}")

def generate_legal_research_pdf(research_data: Dict[str, Any], user_id: str, session_id: str) -> bytes:
    """
    Generate a detailed PDF summary of legal research
    
    Args:
        research_data: Complete research results
        user_id: User ID for tracking
        session_id: Session ID for tracking
        
    Returns:
        bytes: PDF content as bytes
    """
    # Create PDF buffer
    buffer = io.BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Create styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        alignment=1,  # Center alignment
        spaceAfter=30,
        textColor=colors.HexColor('#2c3e50'),
        fontName='Helvetica-Bold'
    )
    
    heading1_style = ParagraphStyle(
        'CustomH1',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#34495e'),
        spaceBefore=20,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    )
    
    heading2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceBefore=15,
        spaceAfter=8,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=12,
        leading=16,
        spaceBefore=6,
        spaceAfter=6,
        fontName='Helvetica'
    )
    
    small_style = ParagraphStyle(
        'Small',
        parent=styles['Normal'],
        fontSize=10,
        leading=12,
        spaceBefore=3,
        spaceAfter=3,
        fontName='Helvetica'
    )
    
    # Create document content
    story = []
    
    # Add title
    story.append(Paragraph("INFORME DE INVESTIGACIÓN JURÍDICA", title_style))
    story.append(Spacer(1, 20))
    
    # Add metadata
    metadata_style = ParagraphStyle(
        'Metadata',
        parent=styles['Normal'],
        fontSize=10,
        leading=12,
        spaceBefore=3,
        spaceAfter=3,
        fontName='Helvetica',
        textColor=colors.gray
    )
    
    story.append(Paragraph(f"<b>Fecha de generación:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", metadata_style))
    story.append(Paragraph(f"<b>Usuario:</b> {user_id}", metadata_style))
    story.append(Paragraph(f"<b>Sesión:</b> {session_id}", metadata_style))
    story.append(Spacer(1, 20))
    
    # Add research topic
    research_topic = research_data.get("research_topic", "N/A")
    story.append(Paragraph("TEMA DE INVESTIGACIÓN", heading1_style))
    story.append(Paragraph(research_topic, normal_style))
    story.append(Spacer(1, 15))
    
    # Add jurisdiction
    jurisdiction = research_data.get("jurisdiction", "Colombia")
    story.append(Paragraph("JURISDICCIÓN", heading1_style))
    story.append(Paragraph(jurisdiction, normal_style))
    story.append(Spacer(1, 15))
    
    # Add executive summary
    if research_data.get("executive_summary"):
        story.append(Paragraph("RESUMEN EJECUTIVO", heading1_style))
        summary = research_data["executive_summary"]
        # Truncate if too long
        if len(summary) > 2000:
            summary = summary[:2000] + "..."
        story.append(Paragraph(summary, normal_style))
        story.append(Spacer(1, 15))
    
    # Add cases section
    cases = research_data.get("cases", [])
    if cases:
        story.append(Paragraph("JURISPRUDENCIA RELEVANTE", heading1_style))
        for i, case in enumerate(cases[:5], 1):  # Limit to top 5 cases
            story.append(Paragraph(f"{i}. {case.get('title', 'N/A')}", heading2_style))
            story.append(Paragraph(f"<b>Corte:</b> {case.get('court', 'N/A')}", small_style))
            story.append(Paragraph(f"<b>Fecha:</b> {case.get('date', 'N/A')}", small_style))
            story.append(Paragraph(f"<b>Resumen:</b> {case.get('summary', 'N/A')[:300]}...", normal_style))
            story.append(Paragraph(f"<b>Relevancia:</b> {case.get('relevance', 0.5):.2f}", small_style))
            story.append(Spacer(1, 10))
        story.append(Spacer(1, 15))
    
    # Add legislation section
    legislation = research_data.get("legislation", [])
    if legislation:
        story.append(Paragraph("LEGISLACIÓN APLICABLE", heading1_style))
        for i, leg in enumerate(legislation[:5], 1):  # Limit to top 5
            story.append(Paragraph(f"{i}. {leg.get('title', 'N/A')}", heading2_style))
            story.append(Paragraph(f"<b>Tipo:</b> {leg.get('type', 'N/A')}", small_style))
            story.append(Paragraph(f"<b>Fecha:</b> {leg.get('date', 'N/A')}", small_style))
            story.append(Paragraph(f"<b>Resumen:</b> {leg.get('summary', 'N/A')[:300]}...", normal_style))
            story.append(Spacer(1, 10))
        story.append(Spacer(1, 15))
    
    # Add doctrine section
    doctrine = research_data.get("doctrine", [])
    if doctrine:
        story.append(Paragraph("DOCTRINA APLICABLE", heading1_style))
        for i, doc in enumerate(doctrine[:5], 1):  # Limit to top 5
            story.append(Paragraph(f"{i}. {doc.get('title', 'N/A')}", heading2_style))
            story.append(Paragraph(f"<b>Autor:</b> {doc.get('author', 'N/A')}", small_style))
            story.append(Paragraph(f"<b>Fuente:</b> {doc.get('source', 'N/A')}", small_style))
            story.append(Paragraph(f"<b>Resumen:</b> {doc.get('summary', 'N/A')[:300]}...", normal_style))
            story.append(Spacer(1, 10))
        story.append(Spacer(1, 15))
    
    # Add recommendations
    recommendations = research_data.get("recommendations", [])
    if recommendations:
        story.append(Paragraph("RECOMENDACIONES", heading1_style))
        for i, rec in enumerate(recommendations, 1):
            story.append(Paragraph(f"{i}. {rec.get('description', 'N/A')}", normal_style))
            if rec.get('priority'):
                story.append(Paragraph(f"   <b>Prioridad:</b> {rec['priority']}", small_style))
        story.append(Spacer(1, 15))
    
    # Add statistics
    statistics = research_data.get("statistics", {})
    if statistics:
        story.append(Paragraph("ESTADÍSTICAS DE INVESTIGACIÓN", heading1_style))
        stats_text = f"""
        <b>Fuentes encontradas:</b> {statistics.get('sources_found', 0)}<br/>
        <b>Tiempo de búsqueda:</b> {statistics.get('search_time', 'N/A')}<br/>
        <b>Metodología utilizada:</b> {statistics.get('methodology_used', 'N/A')}<br/>
        """
        story.append(Paragraph(stats_text, normal_style))
        story.append(Spacer(1, 15))
    
    # Add limitations
    limitations = research_data.get("limitations", [])
    if limitations:
        story.append(Paragraph("LIMITACIONES Y CONSIDERACIONES", heading1_style))
        for limitation in limitations:
            story.append(Paragraph(f"• {limitation}", normal_style))
        story.append(Spacer(1, 15))
    
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
        f"Generado por LegalTechAI - Sistema de Investigación Jurídica<br/>"
        f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        footer_style
    ))
    
    # Build the PDF
    try:
        doc.build(story)
    except Exception as e:
        print(f"Error building PDF: {e}")
        # Fallback: create a simple PDF
        from reportlab.pdfgen import canvas
        c = canvas.Canvas(buffer)
        c.drawString(100, 750, "INFORME DE INVESTIGACIÓN JURÍDICA")
        c.drawString(100, 700, f"Tema: {research_data.get('research_topic', 'N/A')}")
        c.drawString(100, 650, f"Usuario: {user_id}")
        c.drawString(100, 600, f"Sesión: {session_id}")
        c.drawString(100, 550, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        c.save()
    
    # Get PDF content
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return pdf_content

async def list_documents(prefix: Optional[str] = None) -> list:
    """
    List documents in the R2 bucket using ListObjectsV2
    
    Args:
        prefix: Optional prefix to filter documents
        
    Returns:
        list: List of document metadata
    """
    try:
        s3_client = get_r2_client()
        
        # Use ListObjectsV2 as recommended by Cloudflare
        response = s3_client.list_objects_v2(
            Bucket=R2_BUCKET_NAME,
            Prefix=prefix
        )
        
        documents = []
        for obj in response.get('Contents', []):
            # Get object metadata including CORS headers
            metadata = s3_client.head_object(
                Bucket=SUPABASE_DOCUMENT_DRAFTING_BUCKET_NAME,
                Key=obj['Key']
            )
            
            documents.append({
                'key': obj['Key'],
                'size': obj['Size'],
                'last_modified': obj['LastModified'],
                'url': f"{R2_BUCKET_URL}/{obj['Key']}",  # Using public URL
                'content_type': metadata.get('ContentType'),
                'cache_control': metadata.get('CacheControl'),
                'metadata': metadata.get('Metadata', {})
            })
            
        return documents
        
    except Exception as e:
        raise Exception(f"Error listing documents from R2: {str(e)}")

async def upload_contract_analysis_pdf_to_supabase_s3(
    analysis_data: Dict[str, Any],
    user_id: str,
    session_id: str,
    contract_type: str = "contract_analysis"
) -> str:
    """
    Generate and upload a detailed PDF summary of contract analysis to Supabase S3 storage
    
    Args:
        analysis_data: Complete analysis results from the contract agent
        user_id: User ID for tracking
        session_id: Session ID for tracking
        contract_type: Type of contract analysis
        
    Returns:
        str: Public URL of the uploaded PDF
    """
    try:
        # Generate PDF content
        pdf_content = generate_contract_analysis_pdf(analysis_data, user_id, session_id, contract_type)
        
        # Convert to binary stream
        pdf_stream = io.BytesIO(pdf_content)
        pdf_stream.seek(0)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"contract_analysis_{user_id}_{session_id}_{timestamp}.pdf"
        
        # Upload to Supabase S3 contract analysis bucket
        s3_client = get_contract_analysis_supabase_s3_client()
        
        extra_args = {
            'ContentType': 'application/pdf',
            'CacheControl': 'max-age=31536000',  # Cache for 1 year
            'Metadata': {
                'user_id': user_id,
                'session_id': session_id,
                'document_type': 'contract_analysis_summary',
                'contract_type': contract_type,
                'generated_at': datetime.now().isoformat()
            }
        }
        
        # Use prefix to organize contract analysis files in the bucket
        object_key = f"contract-analysis/{filename}"
        
        # Upload PDF
        s3_client.upload_fileobj(
            pdf_stream,
            SUPABASE_CONTRACT_ANALYSIS_BUCKET_NAME,
            object_key,
            ExtraArgs=extra_args
        )
        
        # Generate public URL
        url = f"{SUPABASE_S3_BUCKET_URL}/{object_key}"
        
        return url
        
    except Exception as e:
        raise Exception(f"Error uploading contract analysis PDF to Supabase S3: {str(e)}")

# Keep the old function name for backward compatibility
async def upload_contract_analysis_pdf_to_r2(
    analysis_data: Dict[str, Any],
    user_id: str,
    session_id: str,
    contract_type: str = "contract_analysis"
) -> str:
    """Backward compatibility wrapper for Supabase S3"""
    return await upload_contract_analysis_pdf_to_supabase_s3(analysis_data, user_id, session_id, contract_type)

def generate_contract_analysis_pdf(analysis_data: Dict[str, Any], user_id: str, session_id: str, contract_type: str) -> bytes:
    """
    Generate a comprehensive PDF report for contract analysis results
    
    Args:
        analysis_data: Complete analysis results from the contract agent
        user_id: User ID for tracking
        session_id: Session ID for tracking
        contract_type: Type of contract analysis
        
    Returns:
        bytes: PDF content as bytes
    """
    try:
        # Create buffer for PDF
        buffer = io.BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Create custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1,  # Center alignment
            textColor=colors.darkblue
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        subheading_style = ParagraphStyle(
            'CustomSubHeading',
            parent=styles['Heading3'],
            fontSize=12,
            spaceAfter=8,
            textColor=colors.darkgreen
        )
        
        # Build content
        content = []
        
        # Title
        content.append(Paragraph("ANÁLISIS DE CONTRATO", title_style))
        content.append(Spacer(1, 12))
        
        # Document info
        info_data = [
            ['Usuario:', user_id],
            ['Sesión:', session_id],
            ['Tipo de Contrato:', contract_type],
            ['Fecha de Análisis:', datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
        ]))
        
        content.append(info_table)
        content.append(Spacer(1, 20))
        
        # Executive Summary
        if 'summary' in analysis_data:
            content.append(Paragraph("RESUMEN EJECUTIVO", heading_style))
            summary_text = analysis_data['summary'][:1000] + "..." if len(analysis_data['summary']) > 1000 else analysis_data['summary']
            content.append(Paragraph(summary_text, styles['Normal']))
            content.append(Spacer(1, 12))
        
        # Risk Assessment
        if 'structured_analysis' in analysis_data and analysis_data['structured_analysis']:
            structured = analysis_data['structured_analysis']
            
            content.append(Paragraph("EVALUACIÓN DE RIESGOS", heading_style))
            
            # Risk level
            risk_level = structured.get('risk_level', 'No determinado')
            risk_score = structured.get('risk_score', 0)
            
            risk_data = [
                ['Nivel de Riesgo:', risk_level],
                ['Puntuación de Riesgo:', str(risk_score)],
                ['Estado de Cumplimiento:', structured.get('compliance_status', 'No determinado')]
            ]
            
            risk_table = Table(risk_data, colWidths=[2*inch, 4*inch])
            risk_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ]))
            
            content.append(risk_table)
            content.append(Spacer(1, 12))
            
            # Critical clauses
            if structured.get('critical_clauses'):
                content.append(Paragraph("CLÁUSULAS CRÍTICAS", subheading_style))
                for i, clause in enumerate(structured['critical_clauses'][:5], 1):
                    content.append(Paragraph(f"{i}. {clause}", styles['Normal']))
                content.append(Spacer(1, 8))
            
            # Risks identified
            if structured.get('risks'):
                content.append(Paragraph("RIESGOS IDENTIFICADOS", subheading_style))
                for i, risk in enumerate(structured['risks'][:5], 1):
                    content.append(Paragraph(f"{i}. {risk}", styles['Normal']))
                content.append(Spacer(1, 8))
            
            # Recommendations
            if structured.get('recommendations'):
                content.append(Paragraph("RECOMENDACIONES", subheading_style))
                for i, rec in enumerate(structured['recommendations'][:5], 1):
                    content.append(Paragraph(f"{i}. {rec}", styles['Normal']))
                content.append(Spacer(1, 8))
        
        # Knowledge Base Usage
        if 'knowledge_base_utilization' in analysis_data:
            kb_usage = analysis_data['knowledge_base_utilization']
            content.append(Paragraph("UTILIZACIÓN DE BASE DE CONOCIMIENTO", heading_style))
            
            kb_data = [
                ['Términos Legales Consultados:', str(kb_usage.get('legal_terms_consulted', 0))],
                ['Cláusulas de Contrato Referenciadas:', str(kb_usage.get('contract_clauses_referenced', 0))],
                ['Jurisprudencia Citada:', str(kb_usage.get('jurisprudence_cited', 0))]
            ]
            
            kb_table = Table(kb_data, colWidths=[2.5*inch, 3.5*inch])
            kb_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgreen),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ]))
            
            content.append(kb_table)
            content.append(Spacer(1, 12))
        
        # Memory Integration
        if 'memory_utilization' in analysis_data:
            memory_usage = analysis_data['memory_utilization']
            content.append(Paragraph("INTEGRACIÓN DE MEMORIA", heading_style))
            
            memory_data = [
                ['Análisis Previos Recuperados:', str(memory_usage.get('previous_analyses_retrieved', 0))],
                ['Patrones de Riesgo Identificados:', str(memory_usage.get('risk_patterns_identified', 0))],
                ['Problemas de Cumplimiento Identificados:', str(memory_usage.get('compliance_issues_identified', 0))],
                ['Personalización Aplicada:', 'Sí' if memory_usage.get('personalization_applied', False) else 'No']
            ]
            
            memory_table = Table(memory_data, colWidths=[2.5*inch, 3.5*inch])
            memory_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightyellow),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ]))
            
            content.append(memory_table)
            content.append(Spacer(1, 12))
        
        # Footer
        content.append(Spacer(1, 20))
        content.append(Paragraph("---", styles['Normal']))
        content.append(Paragraph("Generado por LegalTechAI - Sistema de Análisis de Contratos", styles['Normal']))
        content.append(Paragraph(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        
        # Build PDF
        doc.build(content)
        
        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
        
    except Exception as e:
        raise Exception(f"Error generating contract analysis PDF: {str(e)}")

async def upload_contract_file_to_supabase_s3(
    file_content: bytes,
    filename: str,
    user_id: str,
    session_id: str,
    contract_type: str = "contract_analysis"
) -> str:
    """
    Upload a contract file to Supabase S3 storage
    
    Args:
        file_content: Binary content of the file
        filename: Original filename
        user_id: User ID for tracking
        session_id: Session ID for tracking
        contract_type: Type of contract
        
    Returns:
        str: Public URL of the uploaded file
    """
    try:
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = filename.split('.')[-1] if '.' in filename else 'pdf'
        unique_filename = f"{timestamp}-{filename}"
        
        # Upload to Supabase S3 contract analysis bucket
        s3_client = get_contract_analysis_supabase_s3_client()
        
        extra_args = {
            'ContentType': f'application/{file_extension}',
            'CacheControl': 'max-age=31536000',  # Cache for 1 year
            'Metadata': {
                'user_id': user_id,
                'session_id': session_id,
                'contract_type': contract_type,
                'original_filename': filename,
                'uploaded_at': datetime.now().isoformat()
            }
        }
        
        # Use prefix to organize contract files in the bucket
        object_key = f"contract-files/{unique_filename}"
        
        # Upload file
        s3_client.put_object(
            Bucket=SUPABASE_CONTRACT_ANALYSIS_BUCKET_NAME,
            Key=object_key,
            Body=file_content,
            **extra_args
        )
        
        # Generate public URL
        url = f"{SUPABASE_S3_BUCKET_URL}/{object_key}"
        
        return url
        
    except Exception as e:
        raise Exception(f"Error uploading contract file to Supabase S3: {str(e)}")

# Keep the old function name for backward compatibility
async def upload_contract_file_to_r2(
    file_content: bytes,
    filename: str,
    user_id: str,
    session_id: str,
    contract_type: str = "contract_analysis"
) -> str:
    """Backward compatibility wrapper for Supabase S3"""
    return await upload_contract_file_to_supabase_s3(file_content, filename, user_id, session_id, contract_type)

async def list_contract_analysis_documents_supabase_s3(user_id: Optional[str] = None) -> list:
    """
    List contract analysis documents in the Supabase S3 bucket
    
    Args:
        user_id: Optional user ID to filter documents
        
    Returns:
        list: List of document metadata
    """
    try:
        s3_client = get_contract_analysis_supabase_s3_client()
        
        # Use ListObjectsV2 to list both contract analysis PDFs and contract files
        response = s3_client.list_objects_v2(
            Bucket=SUPABASE_CONTRACT_ANALYSIS_BUCKET_NAME,
            Prefix='contract-'  # This will match both 'contract-analysis/' and 'contract-files/'
        )
        
        documents = []
        for obj in response.get('Contents', []):
            # Get object metadata
            metadata = s3_client.head_object(
                Bucket=SUPABASE_CONTRACT_ANALYSIS_BUCKET_NAME,
                Key=obj['Key']
            )
            
            # Filter by user_id if provided
            if user_id and user_id not in obj['Key']:
                continue
            
            documents.append({
                'key': obj['Key'],
                'size': obj['Size'],
                'last_modified': obj['LastModified'],
                'url': f"{SUPABASE_S3_BUCKET_URL}/{obj['Key']}",
                'content_type': metadata.get('ContentType'),
                'cache_control': metadata.get('CacheControl'),
                'metadata': metadata.get('Metadata', {})
            })
            
        return documents
        
    except Exception as e:
        raise Exception(f"Error listing contract analysis documents from Supabase S3: {str(e)}")

# Keep the old function name for backward compatibility
async def list_contract_analysis_documents(user_id: Optional[str] = None) -> list:
    """Backward compatibility wrapper for Supabase S3"""
    return await list_contract_analysis_documents_supabase_s3(user_id)

async def list_legal_research_documents(user_id: Optional[str] = None) -> list:
    """
    List legal research documents in the R2 bucket
    
    Args:
        user_id: Optional user ID to filter documents
        
    Returns:
        list: List of legal research document metadata
    """
    try:
        s3_client = get_r2_client()
        
        # Use ListObjectsV2 as recommended by Cloudflare
        prefix = f"legal_research_{user_id}_" if user_id else "legal_research_"
        response = s3_client.list_objects_v2(
            Bucket=R2_LEGAL_RESEARCH_BUCKET_NAME,
            Prefix=prefix
        )
        
        documents = []
        for obj in response.get('Contents', []):
            # Get object metadata including CORS headers
            metadata = s3_client.head_object(
                Bucket=R2_LEGAL_RESEARCH_BUCKET_NAME,
                Key=obj['Key']
            )
            
            documents.append({
                'key': obj['Key'],
                'size': obj['Size'],
                'last_modified': obj['LastModified'],
                'url': f"{R2_LEGAL_RESEARCH_BUCKET_URL}/{obj['Key']}",  # Using public URL
                'content_type': metadata.get('ContentType'),
                'cache_control': metadata.get('CacheControl'),
                'metadata': metadata.get('Metadata', {}),
                'user_id': metadata.get('Metadata', {}).get('user_id'),
                'session_id': metadata.get('Metadata', {}).get('session_id'),
                'document_type': metadata.get('Metadata', {}).get('document_type')
            })
            
        return documents
        
    except Exception as e:
        raise Exception(f"Error listing legal research documents from R2: {str(e)}")

async def upload_contract_analysis_summary_pdf(
    analysis_data: Dict[str, Any],
    user_id: str,
    session_id: str,
    contract_type: str = "contract_analysis"
) -> str:
    """
    Generate and upload contract analysis summary PDF to Supabase S3
    
    Args:
        analysis_data: Contract analysis results
        user_id: User ID for tracking
        session_id: Session ID for tracking
        contract_type: Type of contract analysis
        
    Returns:
        str: Public URL of the uploaded PDF
    """
    try:
        # Generate PDF content
        pdf_content = generate_contract_analysis_pdf(
            analysis_data=analysis_data,
            contract_type=contract_type,
            user_id=user_id,
            session_id=session_id
        )
        
        # Create filename with contract-analisi-result prefix
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"contract-analisi-result_{contract_type}_{user_id}_{timestamp}.pdf"
        
        # Upload to Supabase S3
        s3_client = get_contract_analysis_supabase_s3_client()
        
        # Upload to contract-analisis bucket with contract-analisi-result prefix
        object_key = f"contract-analisi-result/{filename}"
        
        s3_client.put_object(
            Bucket=SUPABASE_CONTRACT_ANALYSIS_BUCKET_NAME,
            Key=object_key,
            Body=pdf_content,
            ContentType='application/pdf',
            Metadata={
                'user_id': user_id,
                'session_id': session_id,
                'contract_type': contract_type,
                'analysis_timestamp': datetime.now().isoformat(),
                'document_type': 'contract_analysis_summary'
            }
        )
        
        # Generate public URL
        pdf_url = f"{SUPABASE_S3_BUCKET_URL}/{object_key}"
        
        logger.info(f"Contract analysis summary PDF uploaded: {pdf_url}")
        return pdf_url
        
    except Exception as e:
        logger.error(f"Error uploading contract analysis summary PDF: {e}")
        raise Exception(f"Error uploading contract analysis summary PDF: {str(e)}") 