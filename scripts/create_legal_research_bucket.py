import requests
import json
import sys
import os

# Add the parent directory to the path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.cloudflare import CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID, R2_LEGAL_RESEARCH_BUCKET_NAME

def create_legal_research_bucket():
    """Create legal-research R2 bucket using Cloudflare API"""
    url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/r2/buckets"
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {CLOUDFLARE_API_TOKEN}'
    }
    
    data = {
        "name": R2_LEGAL_RESEARCH_BUCKET_NAME,
        "locationHint": "enam"  # Using enam as specified in the curl command
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        print(f"Successfully created legal-research R2 bucket: {R2_LEGAL_RESEARCH_BUCKET_NAME}")
        print("Response:", json.dumps(response.json(), indent=2))
        
    except requests.exceptions.RequestException as e:
        print(f"Error creating legal-research R2 bucket: {str(e)}")
        if hasattr(e.response, 'text'):
            print("Response:", e.response.text)

def configure_legal_research_bucket_cors():
    """Configure CORS policy for the legal-research R2 bucket"""
    import boto3
    from botocore.config import Config
    from config.cloudflare import (
        R2_ACCESS_KEY_ID,
        R2_SECRET_ACCESS_KEY,
        R2_ENDPOINT,
        R2_LEGAL_RESEARCH_BUCKET_NAME
    )
    
    s3_client = boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=Config(
            signature_version='s3v4',
            region_name='auto'
        )
    )
    
    # CORS configuration
    cors_configuration = {
        'CORSRules': [{
            'AllowedHeaders': [
                '*'
            ],
            'AllowedMethods': [
                'GET',
                'PUT',
                'POST',
                'DELETE',
                'HEAD'
            ],
            'AllowedOrigins': [
                'http://localhost:3000',  # Local development
                'http://localhost:8000',  # FastAPI default
                'https://*.yourdomain.com'  # Production domain
            ],
            'ExposeHeaders': [
                'ETag',
                'Content-Length',
                'Content-Type',
                'Last-Modified'
            ],
            'MaxAgeSeconds': 3600  # Cache preflight requests for 1 hour
        }]
    }
    
    try:
        # Put CORS configuration
        s3_client.put_bucket_cors(
            Bucket=R2_LEGAL_RESEARCH_BUCKET_NAME,
            CORSConfiguration=cors_configuration
        )
        print(f"Successfully configured CORS for legal-research bucket: {R2_LEGAL_RESEARCH_BUCKET_NAME}")
        print("CORS Configuration:", cors_configuration)
        
    except Exception as e:
        print(f"Error configuring CORS for legal-research bucket: {str(e)}")

if __name__ == "__main__":
    print("Creating legal-research R2 bucket...")
    create_legal_research_bucket()
    
    print("\nConfiguring CORS for legal-research bucket...")
    configure_legal_research_bucket_cors()
    
    print("\nLegal-research bucket setup complete!")
