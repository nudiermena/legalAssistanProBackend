import os

# Cloudflare API Configuration

#CLOUDFLARE_API_TOKEN = "6U9WjMDx2sQ2mvmgFoLP0FHJ_4m9xHTWLe627QN5"
CLOUDFLARE_API_TOKEN = "XoSEspcS5Y-iH73kDSBAiVM_XvGCktecoozA7PI-"
CLOUDFLARE_ACCOUNT_ID = "825352db439a3e7007580aef68d8bcf0"
CLOUDFLARE_API_TOKEN_CHATBOT = "rU7QMkiar6vNIURIXig4GwagXI5fxMqaB6kK7OYX"
VECTORIZE_INDEX = os.getenv("VECTORIZE_INDEX")

# R2 Configuration (COMMENTED OUT - MIGRATING TO SUPABASE S3)
# R2_ACCESS_KEY_ID = "4af6ece572b16a817b0cda9ff4a20f10"
# R2_SECRET_ACCESS_KEY = "b3bc14045c918f5518e55140fdaea187104fb0a52684bbb2004038a5540ad770"
# R2_BUCKET_NAME = "document-generator"
# R2_ENDPOINT = "https://825352db439a3e7007580aef68d8bcf0.r2.cloudflarestorage.com"
# # Public URL for testing
# R2_PUBLIC_URL = "https://pub-fcdcd12ce9f5442b885f33f0e4cae158.r2.dev"
# R2_BUCKET_URL = R2_PUBLIC_URL  # Using public URL for testing

# # Contract Analysis R2 Configuration
# # Using the main document-generator bucket for contract analysis files
# R2_CONTRACT_ANALYSIS_BUCKET_NAME = "document-generator"  # Use main bucket instead of separate bucket
# R2_CONTRACT_ANALYSIS_ENDPOINT = "https://825352db439a3e7007580aef68d8bcf0.r2.cloudflarestorage.com"

# SUPABASE S3 Configuration
SUPABASE_S3_ACCESS_KEY_ID = "c19b1a09f64b8e5f5043d810aef2a2ee"
SUPABASE_S3_SECRET_ACCESS_KEY = "77aa5aa061949aa54752b3b34f21245bff4e4784c41495bc3fc3cfdcb2cd7617"
SUPABASE_S3_BUCKET_NAME = "contract-analisis"
SUPABASE_S3_ENDPOINT = "https://luiiwyzjtkqnmnzqghoz.supabase.co/storage/v1/s3"
SUPABASE_S3_BUCKET_URL = f"https://luiiwyzjtkqnmnzqghoz.supabase.co/storage/v1/object/public/{SUPABASE_S3_BUCKET_NAME}"

# Contract Analysis Supabase S3 Configuration
SUPABASE_CONTRACT_ANALYSIS_BUCKET_NAME = "contract-analisis"
SUPABASE_CONTRACT_ANALYSIS_ENDPOINT = "https://luiiwyzjtkqnmnzqghoz.supabase.co/storage/v1/s3"

# Document Drafting Supabase S3 Configuration
SUPABASE_DOCUMENT_DRAFTING_BUCKET_NAME = "document-drafting"
SUPABASE_DOCUMENT_DRAFTING_ENDPOINT = "https://luiiwyzjtkqnmnzqghoz.supabase.co/storage/v1/s3"
SUPABASE_DOCUMENT_DRAFTING_BUCKET_URL = f"https://luiiwyzjtkqnmnzqghoz.supabase.co/storage/v1/object/public/{SUPABASE_DOCUMENT_DRAFTING_BUCKET_NAME}"

# Legal Research R2 Configuration (COMMENTED OUT - MIGRATING TO SUPABASE S3)
# R2_LEGAL_RESEARCH_BUCKET_NAME = "legal-research"
# R2_LEGAL_RESEARCH_BUCKET_URL = R2_PUBLIC_URL  # Using same public URL for now

# API URLs
VECTORIZE_API_URL = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/vectorize/indexes/{VECTORIZE_INDEX}/query"
UPLOAD_API_URL = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/vectorize/indexes/{VECTORIZE_INDEX}/documents"
EMBEDDING_MODEL_URL = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/@cf/baai/bge-small-en-v1.5" 