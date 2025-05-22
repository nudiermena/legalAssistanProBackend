import boto3
from botocore.config import Config
from config.cloudflare import (
    R2_ACCESS_KEY_ID,
    R2_SECRET_ACCESS_KEY,
    R2_ENDPOINT,
    R2_BUCKET_NAME,
    R2_BUCKET_URL
)
from typing import BinaryIO, Optional
import uuid
import os

def get_r2_client():
    """Get configured R2 client with proper settings"""
    return boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=Config(
            signature_version='s3v4',
            region_name='auto',  # Required for R2
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
        s3_client = get_r2_client()
        
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
                Bucket=R2_BUCKET_NAME,
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
                    Bucket=R2_BUCKET_NAME,
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
                Bucket=R2_BUCKET_NAME,
                Key=filename,
                UploadId=mpu['UploadId'],
                MultipartUpload={'Parts': parts}
            )
        else:
            # Simple upload for smaller files
            s3_client.upload_fileobj(
                file_content,
                R2_BUCKET_NAME,
                filename,
                ExtraArgs=extra_args
            )
        
        # Generate public URL using the public bucket URL
        url = f"{R2_BUCKET_URL}/{filename}"
        
        return url
        
    except Exception as e:
        raise Exception(f"Error uploading document to R2: {str(e)}")

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
                Bucket=R2_BUCKET_NAME,
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