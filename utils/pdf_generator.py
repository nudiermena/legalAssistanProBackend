#!/usr/bin/env python3
"""
PDF Generator for Contract Analysis Results
"""

import io
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import json

logger = logging.getLogger(__name__)

class ContractAnalysisPDFGenerator:
    """Generate PDF reports for contract analysis results"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        # Subtitle style
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=12,
            textColor=colors.darkblue
        )
        
        # Body style
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_JUSTIFY
        )
        
        # Risk style
        self.risk_style = ParagraphStyle(
            'RiskStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=4,
            leftIndent=20
        )
    
    def generate_contract_analysis_pdf(
        self,
        analysis_data: Dict[str, Any],
        contract_type: str,
        user_id: str,
        session_id: str
    ) -> bytes:
        """Generate a comprehensive PDF report for contract analysis"""
        
        try:
            # Create PDF in memory
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build the story (content)
            story = []
            
            # Add title
            title = f"ANÁLISIS DE CONTRATO - {contract_type.upper()}"
            story.append(Paragraph(title, self.title_style))
            story.append(Spacer(1, 12))
            
            # Add metadata
            metadata_table = self._create_metadata_table(analysis_data, user_id, session_id)
            story.append(metadata_table)
            story.append(Spacer(1, 20))
            
            # Add executive summary
            if 'summary' in analysis_data:
                story.append(Paragraph("RESUMEN EJECUTIVO", self.subtitle_style))
                summary_text = analysis_data['summary']
                if isinstance(summary_text, dict):
                    summary_text = str(summary_text)
                story.append(Paragraph(summary_text[:1000] + "..." if len(summary_text) > 1000 else summary_text, self.body_style))
                story.append(Spacer(1, 12))
            
            # Add structured analysis if available
            if 'structured_analysis' in analysis_data and analysis_data['structured_analysis']:
                structured = analysis_data['structured_analysis']
                story = self._add_structured_analysis(story, structured)
            
            # Add risk assessment
            story = self._add_risk_assessment(story, analysis_data)
            
            # Add recommendations
            story = self._add_recommendations(story, analysis_data)
            
            # Add compliance information
            story = self._add_compliance_info(story, analysis_data)
            
            # Add knowledge base utilization
            story = self._add_knowledge_base_info(story, analysis_data)
            
            # Add memory utilization
            story = self._add_memory_info(story, analysis_data)
            
            # Add footer
            story.append(Spacer(1, 20))
            footer_text = f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - MiAsistenteLegalIA"
            story.append(Paragraph(footer_text, self.styles['Normal']))
            
            # Build PDF
            doc.build(story)
            
            # Get PDF content
            pdf_content = buffer.getvalue()
            buffer.close()
            
            logger.info(f"Generated contract analysis PDF: {len(pdf_content)} bytes")
            return pdf_content
            
        except Exception as e:
            logger.error(f"Error generating contract analysis PDF: {e}")
            raise
    
    def _create_metadata_table(self, analysis_data: Dict[str, Any], user_id: str, session_id: str) -> Table:
        """Create metadata table"""
        data = [
            ['Campo', 'Valor'],
            ['Tipo de Contrato', analysis_data.get('contract_type', 'No especificado')],
            ['Usuario', user_id[:8] + '...' if user_id else 'No especificado'],
            ['Sesión', session_id[:8] + '...' if session_id else 'No especificado'],
            ['Fecha de Análisis', analysis_data.get('analysis_timestamp', datetime.now().isoformat())],
            ['Partes Involucradas', str(len(analysis_data.get('parties', [])))],
        ]
        
        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        return table
    
    def _add_structured_analysis(self, story: list, structured: Dict[str, Any]) -> list:
        """Add structured analysis section"""
        story.append(Paragraph("ANÁLISIS ESTRUCTURADO", self.subtitle_style))
        
        # Risk level
        if 'risk_level' in structured:
            risk_level = structured['risk_level']
            risk_color = colors.red if risk_level == 'alto' else colors.orange if risk_level == 'medio' else colors.green
            story.append(Paragraph(f"<b>Nivel de Riesgo:</b> <font color='{risk_color}'>{risk_level.upper()}</font>", self.body_style))
        
        # Compliance status
        if 'compliance_status' in structured:
            compliance = structured['compliance_status']
            compliance_color = colors.green if compliance == 'cumple' else colors.red if compliance == 'no_cumple' else colors.orange
            story.append(Paragraph(f"<b>Estado de Cumplimiento:</b> <font color='{compliance_color}'>{compliance.upper()}</font>", self.body_style))
        
        # Critical clauses
        if 'critical_clauses' in structured and structured['critical_clauses']:
            story.append(Paragraph("Cláusulas Críticas:", self.body_style))
            for clause in structured['critical_clauses'][:5]:  # Limit to 5 clauses
                story.append(Paragraph(f"• {clause}", self.risk_style))
        
        story.append(Spacer(1, 12))
        return story
    
    def _add_risk_assessment(self, story: list, analysis_data: Dict[str, Any]) -> list:
        """Add risk assessment section"""
        story.append(Paragraph("EVALUACIÓN DE RIESGOS", self.subtitle_style))
        
        # Extract risks from structured analysis
        risks = []
        if 'structured_analysis' in analysis_data and analysis_data['structured_analysis']:
            structured = analysis_data['structured_analysis']
            if 'risks' in structured and structured['risks']:
                risks = structured['risks']
        
        if risks:
            for risk in risks[:10]:  # Limit to 10 risks
                story.append(Paragraph(f"• {risk}", self.risk_style))
        else:
            story.append(Paragraph("No se identificaron riesgos específicos en el análisis.", self.body_style))
        
        story.append(Spacer(1, 12))
        return story
    
    def _add_recommendations(self, story: list, analysis_data: Dict[str, Any]) -> list:
        """Add recommendations section"""
        story.append(Paragraph("RECOMENDACIONES", self.subtitle_style))
        
        # Extract recommendations from structured analysis
        recommendations = []
        if 'structured_analysis' in analysis_data and analysis_data['structured_analysis']:
            structured = analysis_data['structured_analysis']
            if 'recommendations' in structured and structured['recommendations']:
                recommendations = structured['recommendations']
        
        if recommendations:
            for i, rec in enumerate(recommendations[:8], 1):  # Limit to 8 recommendations
                story.append(Paragraph(f"{i}. {rec}", self.body_style))
        else:
            story.append(Paragraph("No se generaron recomendaciones específicas en este análisis.", self.body_style))
        
        story.append(Spacer(1, 12))
        return story
    
    def _add_compliance_info(self, story: list, analysis_data: Dict[str, Any]) -> list:
        """Add compliance information section"""
        story.append(Paragraph("INFORMACIÓN DE CUMPLIMIENTO", self.subtitle_style))
        
        # Add compliance details if available
        if 'knowledge_base_utilization' in analysis_data:
            kb_util = analysis_data['knowledge_base_utilization']
            story.append(Paragraph(f"Términos legales consultados: {kb_util.get('legal_terms_consulted', 0)}", self.body_style))
            story.append(Paragraph(f"Cláusulas de referencia: {kb_util.get('contract_clauses_referenced', 0)}", self.body_style))
            story.append(Paragraph(f"Jurisprudencia citada: {kb_util.get('jurisprudence_cited', 0)}", self.body_style))
        
        story.append(Spacer(1, 12))
        return story
    
    def _add_knowledge_base_info(self, story: list, analysis_data: Dict[str, Any]) -> list:
        """Add knowledge base utilization information"""
        story.append(Paragraph("UTILIZACIÓN DE BASE DE CONOCIMIENTO", self.subtitle_style))
        
        if 'knowledge_base_utilization' in analysis_data:
            kb_util = analysis_data['knowledge_base_utilization']
            story.append(Paragraph(f"Nivel de integración: {kb_util.get('knowledge_integration_level', 'básico')}", self.body_style))
            
            sources = kb_util.get('knowledge_sources_used', [])
            if sources:
                story.append(Paragraph("Fuentes utilizadas:", self.body_style))
                for source in sources:
                    story.append(Paragraph(f"• {source}", self.risk_style))
        
        story.append(Spacer(1, 12))
        return story
    
    def _add_memory_info(self, story: list, analysis_data: Dict[str, Any]) -> list:
        """Add memory utilization information"""
        story.append(Paragraph("UTILIZACIÓN DE MEMORIA", self.subtitle_style))
        
        if 'memory_utilization' in analysis_data:
            mem_util = analysis_data['memory_utilization']
            story.append(Paragraph(f"Análisis previos recuperados: {mem_util.get('previous_analyses_retrieved', 0)}", self.body_style))
            story.append(Paragraph(f"Patrones de riesgo identificados: {mem_util.get('risk_patterns_identified', 0)}", self.body_style))
            story.append(Paragraph(f"Problemas de cumplimiento identificados: {mem_util.get('compliance_issues_identified', 0)}", self.body_style))
            story.append(Paragraph(f"Personalización aplicada: {'Sí' if mem_util.get('personalization_applied', False) else 'No'}", self.body_style))
        
        story.append(Spacer(1, 12))
        return story

def generate_contract_analysis_pdf(
    analysis_data: Dict[str, Any],
    contract_type: str,
    user_id: str,
    session_id: str
) -> bytes:
    """Generate contract analysis PDF"""
    generator = ContractAnalysisPDFGenerator()
    return generator.generate_contract_analysis_pdf(analysis_data, contract_type, user_id, session_id)
