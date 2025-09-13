#!/usr/bin/env python3
"""
Setup environment variables for development with vector database
"""

import os

def setup_environment():
    """Set up environment variables for development"""
    
    # Import settings to get Supabase credentials
    from config.settings import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY, POSTGRES_URL
    
    # Supabase Configuration from settings.py
    os.environ["SUPABASE_URL"] = SUPABASE_URL
    os.environ["SUPABASE_ANON_KEY"] = SUPABASE_ANON_KEY
    os.environ["SUPABASE_SERVICE_ROLE_KEY"] = SUPABASE_SERVICE_ROLE_KEY
    
    # Database Configuration from settings.py
    os.environ["DATABASE_URL"] = POSTGRES_URL
    
    # Vector Database Configuration - ENABLE FOR DEVELOPMENT
    os.environ["ENABLE_VECTOR_DB"] = "true"
    
    # Security Configuration
    os.environ["SECURITY_ENVIRONMENT"] = "development"
    os.environ["SECRET_KEY"] = "your-secret-key-here-change-in-production"
    os.environ["API_KEYS"] = "test_key_12345"
    
    # Rate Limiting
    os.environ["RATE_LIMIT_PER_MINUTE"] = "60"
    os.environ["RATE_LIMIT_PER_HOUR"] = "1000"
    os.environ["RATE_LIMIT_PER_DAY"] = "10000"
    os.environ["RATE_LIMIT_BURST"] = "10"
    
    # CORS Configuration
    os.environ["CORS_ORIGINS"] = "http://localhost:3000,http://localhost:8000"
    
    # File Upload
    os.environ["MAX_FILE_SIZE"] = "10485760"
    os.environ["SCAN_UPLOADS"] = "true"
    
    # Redis Configuration
    os.environ["REDIS_URL"] = "redis://localhost:6379"
    os.environ["REDIS_DB"] = "0"
    
    # Debug and Development Settings
    os.environ["DEBUG_MODE"] = "true"
    os.environ["USE_SQLITE_FALLBACK"] = "false"
    
    print("✅ Environment variables set for development")
    print("⚠️  Make sure to set MISTRAL_API_KEY for full functionality")

if __name__ == "__main__":
    setup_environment() 