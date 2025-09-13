import boto3
from botocore.config import Config
from config.cloudflare import (
    R2_ACCESS_KEY_ID,
    R2_SECRET_ACCESS_KEY,
    R2_ENDPOINT,
    R2_BUCKET_NAME
)

def configure_cors():
    """Configure CORS policy for the R2 bucket"""
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
            Bucket=R2_BUCKET_NAME,
            CORSConfiguration=cors_configuration
        )
        print(f"Successfully configured CORS for bucket: {R2_BUCKET_NAME}")
        print("CORS Configuration:", cors_configuration)
        
    except Exception as e:
        print(f"Error configuring CORS: {str(e)}")

if __name__ == "__main__":
    configure_cors() 