from pypdf import PdfReader
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

def extract_text_from_pdf_content(pdf_content: bytes) -> str:
    """
    Extract and clean text from PDF content using pypdf
    """
    try:
        # Create a BytesIO object from the PDF content
        pdf_file = BytesIO(pdf_content)
        
        # Extract text using pypdf
        reader = PdfReader(pdf_file)
        text_parts = []
        
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text:
                text_parts.append(page_text.strip())
        
        # Join all parts with newlines
        final_text = '\n'.join(text_parts)
        return final_text if final_text else None
            
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return None

def sanitize_text(text: str) -> str:
    """
    Sanitize text by removing control characters and normalizing Unicode characters
    """
    if not text:
        return ""
    
    # Normalize Unicode characters
    text = text.encode('utf-8', errors='ignore').decode('utf-8')
    
    # Remove control characters but keep newlines and tabs
    text = ''.join(char for char in text if char == '\n' or char == '\t' or (ord(char) >= 32 and ord(char) != 127))
    
    return text.strip() 