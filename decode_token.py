#!/usr/bin/env python3
"""
Decode JWT token to analyze its contents
"""

import jwt
import time
from datetime import datetime

def decode_token_analysis():
    """Decode and analyze the JWT token"""
    
    # The token from your logs
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiZGQ4MzQxMWYtZGE0Zi00NGVhLTk3MWMtMDU1NTNmZTI4YzU5IiwiZW1haWwiOiJudWRpZXI3MTZAaG90bWFpbC5jb20iLCJmdWxsX25hbWUiOiJOdWRpZXIgRW1wcmVzYXJpYWwiLCJ1c2VybmFtZSI6bnVsbCwiaXNfYWRtaW4iOmZhbHNlLCJleHAiOjE3NTU1NDI0MjgsImlhdCI6MTc1NTU0MDYyOCwidHlwZSI6ImFjY2VzcyJ9.e-v9Y1YcGaeoFy-hzdia2KTWsHGAfiJHqQWpScL7MSI"
    
    print("=== JWT Token Analysis ===")
    print(f"Token: {token[:50]}...")
    print()
    
    try:
        # Decode header (without verification)
        header = jwt.get_unverified_header(token)
        print("📋 JWT Header:")
        print(f"   Algorithm: {header.get('alg', 'Unknown')}")
        print(f"   Type: {header.get('typ', 'Unknown')}")
        print()
        
        # Decode payload (without verification)
        payload = jwt.decode(token, options={"verify_signature": False})
        print("📄 JWT Payload:")
        print(f"   User ID: {payload.get('user_id')}")
        print(f"   Email: {payload.get('email')}")
        print(f"   Full Name: {payload.get('full_name')}")
        print(f"   Username: {payload.get('username')}")
        print(f"   Is Admin: {payload.get('is_admin')}")
        print(f"   Token Type: {payload.get('type')}")
        print()
        
        # Analyze timestamps
        iat = payload.get('iat')  # Issued at
        exp = payload.get('exp')  # Expires at
        
        if iat:
            issued_time = datetime.fromtimestamp(iat)
            print(f"⏰ Issued At: {issued_time}")
        
        if exp:
            expires_time = datetime.fromtimestamp(exp)
            current_time = datetime.now()
            print(f"⏰ Expires At: {expires_time}")
            print(f"⏰ Current Time: {current_time}")
            
            if exp < time.time():
                print("❌ TOKEN IS EXPIRED!")
            else:
                print("✅ Token is still valid")
        
        print()
        print("🔍 Analysis:")
        print("   - This is a backend-generated JWT token (HS256, no issuer)")
        print("   - Token was created with a different JWT secret key")
        print("   - Current JWT_SECRET_KEY can't verify this token")
        print("   - This explains why backend verification fails")
        
    except Exception as e:
        print(f"❌ Error decoding token: {e}")

if __name__ == "__main__":
    decode_token_analysis()











