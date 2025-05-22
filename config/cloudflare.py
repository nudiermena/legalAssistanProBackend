import os

# Cloudflare API Configuration
CLOUDFLARE_API_TOKEN = "NNUMlK3eiStKJtWVOOw_lANamzaPRZGoXfqPM1LL"
CLOUDFLARE_ACCOUNT_ID = "825352db439a3e7007580aef68d8bcf0"
VECTORIZE_INDEX = os.getenv("VECTORIZE_INDEX")

# R2 Configuration
R2_ACCESS_KEY_ID = "4af6ece572b16a817b0cda9ff4a20f10"
R2_SECRET_ACCESS_KEY = "b3bc14045c918f5518e55140fdaea187104fb0a52684bbb2004038a5540ad770"
R2_BUCKET_NAME = "document-generator"
R2_ENDPOINT = "https://825352db439a3e7007580aef68d8bcf0.r2.cloudflarestorage.com"
# Public URL for testing
R2_PUBLIC_URL = "https://pub-fcdcd12ce9f5442b885f33f0e4cae158.r2.dev"
R2_BUCKET_URL = R2_PUBLIC_URL  # Using public URL for testing

# API URLs
VECTORIZE_API_URL = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/vectorize/indexes/{VECTORIZE_INDEX}/query"
UPLOAD_API_URL = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/vectorize/indexes/{VECTORIZE_INDEX}/documents"
EMBEDDING_MODEL_URL = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/@cf/baai/bge-small-en-v1.5" 