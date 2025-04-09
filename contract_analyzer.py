import asyncio
import argparse
from pathlib import Path
import pdfplumber
from typing import Dict, Any

from agents.contract_agent import analyze_contract_file
from models.request_models import ContractReviewRequest

class ContractAnalyzer:
    def __init__(self):
        self.supported_file_types = ['.pdf', '.txt']

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from a PDF file."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if pdf.is_encrypted:
                    raise ValueError("PDF is encrypted. Please provide decrypted PDF.")
                
                text = ""
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
                
                return text.strip()
                
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")

    def read_file_content(self, file_path: str) -> str:
        """Read content from a file based on its extension."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        if path.suffix.lower() not in self.supported_file_types:
            raise ValueError(f"Unsupported file type. Supported types: {', '.join(self.supported_file_types)}")
            
        if path.suffix.lower() == '.pdf':
            return self.extract_text_from_pdf(file_path)
        else:
            return path.read_text(encoding='utf-8')

    async def analyze_contract(self, file_path: str, contract_type: str) -> Dict[str, Any]:
        """Analyze a contract file."""
        try:
            # Extract text from file
            print(f"Reading file: {file_path}")
            contract_text = self.read_file_content(file_path)
            
            # Define specific concerns based on contract type
            specific_concerns = [
                "clausula_permanencia",
                "confidencialidad",
                "propiedad_intelectual",
                "terminacion_contrato",
                "responsabilidad_partes"
            ]
            
            # Define data processing requirements
            data_processing = {
                "type": "datos_comerciales",
                "purpose": "ejecucion_contractual",
                "consent": "expreso"
            }
            
            # Analyze the contract using the existing agent
            print("Analyzing contract...")
            result = await analyze_contract_file(
                contract_text=contract_text,
                contract_type=contract_type,
                specific_concerns=specific_concerns,
                data_processing=data_processing
            )
            
            return result
            
        except Exception as e:
            print(f"Error analyzing contract: {str(e)}")
            raise

async def main():
    parser = argparse.ArgumentParser(description='Analyze contract documents')
    parser.add_argument('file_path', help='Path to the contract file (PDF or TXT)')
    parser.add_argument(
        '--type', 
        default='prestacion_servicios',
        choices=[
            'prestacion_servicios',
            'laboral',
            'compraventa',
            'arrendamiento',
            'suministro',
            'consultoria'
        ],
        help='Type of contract'
    )
    parser.add_argument('--output', help='Output file path (optional)')
    
    args = parser.parse_args()
    
    analyzer = ContractAnalyzer()
    
    try:
        # Analyze the contract
        result = await analyzer.analyze_contract(args.file_path, args.type)
        
        # Save or print the results
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            import json
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\nResults saved to: {output_path}")
        else:
            import json
            print("\nAnalysis Results:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code) 