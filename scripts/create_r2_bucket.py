import requests
import json
from config.cloudflare import CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID, R2_BUCKET_NAME

def create_r2_bucket():
    """Create R2 bucket using Cloudflare API"""
    url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/r2/buckets"
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {CLOUDFLARE_API_TOKEN}'
    }
    
    data = {
        "name": R2_BUCKET_NAME,
        "locationHint": "enam"  # Using enam as specified in the curl command
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        print(f"Successfully created R2 bucket: {R2_BUCKET_NAME}")
        print("Response:", json.dumps(response.json(), indent=2))
        
    except requests.exceptions.RequestException as e:
        print(f"Error creating R2 bucket: {str(e)}")
        if hasattr(e.response, 'text'):
            print("Response:", e.response.text)

if __name__ == "__main__":
    create_r2_bucket() 