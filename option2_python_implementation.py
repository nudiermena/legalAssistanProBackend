#!/usr/bin/env python3
"""
Option 2: Enhanced CustomDocumentRequest Format - Python Implementation
For use with FastAPI project
"""

import json
import requests
from typing import Dict, Any, Optional

class CustomDocumentRequest:
    """Python class for Option 2: Enhanced CustomDocumentRequest Format"""
    
    def __init__(self):
        # Option 2: Enhanced CustomDocumentRequest Format
        self.enhanced_request = {
            "document_type": "Contrato de trabajo por prestacion de servicios",
            "description": "Requiero un contrato de servicios donde se evalue todos los requisitos de ley para el sector de salud en Medellín, Colombia",
            "parties": [
                {
                    "name": "Nudier Mena",
                    "identification": "12345678",  # Replace with actual CC/NIT
                    "role": "Contratante"
                },
                {
                    "name": "Karen Mena",
                    "identification": "87654321",  # Replace with actual CC/NIT
                    "role": "Contratista"
                }
            ],
            "key_points": "Contrato de servicios en sector salud\nEvaluación de requisitos legales\nJurisdicción: Medellín\nComplejidad: Compleja\nFormato: PDF\nIdioma: Español",
            "industry": "healthcare",
            "jurisdiction": "medellin",
            "complexity": "complex"
        }
    
    def update_identification_numbers(self, cc_nudier: str, cc_karen: str) -> Dict[str, Any]:
        """Update identification numbers with real CC/NIT"""
        self.enhanced_request["parties"][0]["identification"] = cc_nudier
        self.enhanced_request["parties"][1]["identification"] = cc_karen
        return self.enhanced_request
    
    def get_request_data(self) -> Dict[str, Any]:
        """Get the enhanced request data"""
        return self.enhanced_request
    
    def validate_request(self) -> bool:
        """Validate the request format"""
        required_fields = ["document_type", "description", "parties", "key_points", "industry", "jurisdiction", "complexity"]
        
        # Check required fields
        for field in required_fields:
            if field not in self.enhanced_request or not self.enhanced_request[field]:
                print(f"❌ Missing required field: {field}")
                return False
        
        # Check parties have identification
        for i, party in enumerate(self.enhanced_request["parties"]):
            if "identification" not in party or not party["identification"]:
                print(f"❌ Party {i+1} missing identification")
                return False
        
        # Check valid industry
        valid_industries = ["technology", "healthcare", "finance", "real-estate", "retail", "agriculture", "oil-gas", "education", "construction", "other"]
        if self.enhanced_request["industry"] not in valid_industries:
            print(f"❌ Invalid industry: {self.enhanced_request['industry']}")
            return False
        
        # Check valid complexity
        valid_complexities = ["simple", "standard", "complex"]
        if self.enhanced_request["complexity"] not in valid_complexities:
            print(f"❌ Invalid complexity: {self.enhanced_request['complexity']}")
            return False
        
        # Check valid jurisdiction
        valid_jurisdictions = ["federal", "bogota", "medellin", "cali", "barranquilla", "bucaramanga", "cartagena", "pereira", "other"]
        if self.enhanced_request["jurisdiction"] not in valid_jurisdictions:
            print(f"❌ Invalid jurisdiction: {self.enhanced_request['jurisdiction']}")
            return False
        
        return True

def create_custom_document_api_call(base_url: str = "http://localhost:8000", token: Optional[str] = None) -> Dict[str, Any]:
    """Create a custom document using the API"""
    
    # Create the request object
    custom_request = CustomDocumentRequest()
    
    # Validate the request
    if not custom_request.validate_request():
        raise ValueError("Invalid request format")
    
    # Get the request data
    request_data = custom_request.get_request_data()
    
    # Prepare headers
    headers = {
        "Content-Type": "application/json"
    }
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    # Make the API call
    try:
        response = requests.post(
            f"{base_url}/api/v1/draft-custom-document",
            headers=headers,
            json=request_data
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ API call failed: {response.status_code}")
            print(f"Response: {response.text}")
            return {"error": f"HTTP {response.status_code}", "details": response.text}
            
    except Exception as e:
        print(f"❌ Error making API call: {e}")
        return {"error": str(e)}

def main():
    """Main function to demonstrate Option 2 usage"""
    print("🔧 Option 2: Enhanced CustomDocumentRequest Format - Python Implementation")
    print("=" * 70)
    
    # Create the request object
    custom_request = CustomDocumentRequest()
    
    # Show the request data
    print("=== Enhanced Request Data ===")
    print(json.dumps(custom_request.get_request_data(), indent=2, ensure_ascii=False))
    
    # Validate the request
    print("\n=== Validation ===")
    if custom_request.validate_request():
        print("✅ Request format is valid!")
    else:
        print("❌ Request format is invalid!")
        return
    
    # Show how to update identification numbers
    print("\n=== Update Identification Numbers ===")
    updated_request = custom_request.update_identification_numbers("1234567890", "0987654321")
    print("Updated request with real CC/NIT numbers:")
    print(json.dumps(updated_request, indent=2, ensure_ascii=False))
    
    # Show API call example
    print("\n=== API Call Example ===")
    print("To make the API call, use:")
    print("result = create_custom_document_api_call(base_url='http://localhost:8000', token='your_jwt_token')")
    
    print("\n" + "=" * 70)
    print("✅ Option 2 Python implementation is ready!")
    print("\n📋 Usage:")
    print("1. Create CustomDocumentRequest() instance")
    print("2. Update identification numbers with real CC/NIT")
    print("3. Use create_custom_document_api_call() to make the API request")
    print("4. The 422 error should be resolved")

if __name__ == "__main__":
    main() 