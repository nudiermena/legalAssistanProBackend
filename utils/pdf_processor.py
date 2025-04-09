import pdfplumber
import base64
from typing import Optional

def extract_text_from_pdf_content(pdf_content: bytes) -> Optional[str]:
    """
    Extract text from PDF content while handling encoding issues
    """
    try:
        # Create a temporary file-like object in memory
        from io import BytesIO
        pdf_file = BytesIO(pdf_content)
        
        # Extract text using pdfplumber
        with pdfplumber.open(pdf_file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
            
            # Clean and normalize the text
            text = text.strip()
            # Replace any null bytes or invalid characters
            text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
            
            return text if text else None
            
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {str(e)}")
        return None 