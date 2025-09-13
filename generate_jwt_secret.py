#!/usr/bin/env python3
"""
Generate a secure JWT secret key and add it to .env file
"""

import secrets
import os

def generate_jwt_secret():
    """Generate a secure JWT secret key"""
    return secrets.token_urlsafe(32)

def add_jwt_secret_to_env():
    """Add JWT_SECRET_KEY to .env file if it doesn't exist"""
    jwt_secret = generate_jwt_secret()
    
    # Check if JWT_SECRET_KEY already exists in .env
    env_file = ".env"
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            content = f.read()
            if "JWT_SECRET_KEY=" in content:
                print("JWT_SECRET_KEY already exists in .env file")
                return
    
    # Add JWT_SECRET_KEY to .env file
    with open(env_file, 'a') as f:
        f.write(f"\nJWT_SECRET_KEY={jwt_secret}\n")
    
    print(f"Added JWT_SECRET_KEY to .env file")
    print(f"Generated secret: {jwt_secret[:20]}...")

if __name__ == "__main__":
    add_jwt_secret_to_env()
