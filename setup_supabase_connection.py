#!/usr/bin/env python3
"""
Setup script to configure Supabase connection properly
"""

import os
import sys
import requests
from urllib.parse import urlparse

def check_supabase_project():
    """Check if the Supabase project exists and is accessible"""
    print("🔍 Checking Supabase project status...")
    
    # Get project URL from env.example
    project_url = "https://luiiwyzjtkqnmnzqghoz.supabase.co"
    
    try:
        # Try to access the project
        response = requests.get(f"{project_url}/rest/v1/", timeout=10)
        if response.status_code == 200:
            print("✅ Supabase project is accessible")
            return True
        else:
            print(f"⚠️ Supabase project returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot access Supabase project: {e}")
        print("This could mean:")
        print("1. The project doesn't exist")
        print("2. The project URL is incorrect")
        print("3. Network connectivity issues")
        return False

def get_correct_database_url():
    """Get the correct database URL format for Supabase"""
    print("\n📋 Supabase Database URL Format:")
    print("The correct format should be:")
    print("postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres")
    print()
    print("Current URL in env.example:")
    print("postgresql://postgres:KDxtnciHVvlzrKxV@db.luiiwyzjtkqnmnzqghoz.supabase.co:5432/postgres")
    print()
    print("❌ Issues with current URL:")
    print("1. Wrong hostname format (should be aws-0-[REGION].pooler.supabase.com)")
    print("2. Wrong port (should be 6543, not 5432)")
    print("3. Wrong username format (should be postgres.[PROJECT-REF])")
    
    return None

def create_env_file():
    """Create a proper .env file with correct Supabase configuration"""
    print("\n📝 Creating .env file with correct configuration...")
    
    env_content = """# Supabase Configuration
SUPABASE_URL=https://luiiwyzjtkqnmnzqghoz.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here

# Database Configuration - YOU NEED TO UPDATE THIS
# Get the correct URL from your Supabase dashboard:
# Settings > Database > Connection string > URI
DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres

# Security Configuration
SECURITY_ENVIRONMENT=development
SECRET_KEY=your-secret-key-here-change-in-production
API_KEYS=test_key_12345

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
RATE_LIMIT_PER_DAY=10000
RATE_LIMIT_BURST=10

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# File Upload
MAX_FILE_SIZE=10485760
SCAN_UPLOADS=true

# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_DB=0

# Development Settings
USE_SQLITE_FALLBACK=false
ENABLE_VECTOR_DB=true
ENABLE_KNOWLEDGE_BASE=true
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Created .env file")
    print("⚠️ You need to update the following values:")
    print("1. SUPABASE_ANON_KEY - Get from Supabase dashboard > Settings > API")
    print("2. SUPABASE_SERVICE_ROLE_KEY - Get from Supabase dashboard > Settings > API")
    print("3. DATABASE_URL - Get from Supabase dashboard > Settings > Database > Connection string > URI")

def test_supabase_connection():
    """Test the Supabase connection with proper credentials"""
    print("\n🧪 Testing Supabase connection...")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found. Please create it first.")
        return False
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Get credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
    database_url = os.getenv('DATABASE_URL')
    
    if not supabase_url or supabase_url == 'your_supabase_url_here':
        print("❌ SUPABASE_URL not set in .env file")
        return False
    
    if not supabase_anon_key or supabase_anon_key == 'your_supabase_anon_key_here':
        print("❌ SUPABASE_ANON_KEY not set in .env file")
        return False
    
    if not database_url or 'PROJECT-REF' in database_url:
        print("❌ DATABASE_URL not properly configured in .env file")
        return False
    
    print("✅ Environment variables loaded")
    print(f"Supabase URL: {supabase_url}")
    print(f"Database URL: {database_url[:50]}...")
    
    # Test Supabase API
    try:
        headers = {
            'apikey': supabase_anon_key,
            'Authorization': f'Bearer {supabase_anon_key}'
        }
        response = requests.get(f"{supabase_url}/rest/v1/", headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ Supabase API connection successful")
        else:
            print(f"❌ Supabase API connection failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Supabase API connection error: {e}")
        return False
    
    # Test database connection
    try:
        from sqlalchemy import create_engine
        engine = create_engine(database_url)
        with engine.connect() as conn:
            result = conn.execute("SELECT version()")
            version = result.fetchone()[0]
            print(f"✅ Database connection successful: {version[:50]}...")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Supabase Connection Setup")
    print("=" * 50)
    
    # Check if project exists
    if not check_supabase_project():
        print("\n❌ Cannot access Supabase project.")
        print("Please check:")
        print("1. The project URL is correct")
        print("2. The project exists and is active")
        print("3. You have network connectivity")
        return
    
    # Show correct URL format
    get_correct_database_url()
    
    # Create .env file
    create_env_file()
    
    # Instructions
    print("\n📋 Next Steps:")
    print("1. Go to your Supabase dashboard: https://supabase.com/dashboard")
    print("2. Select your project: luiiwyzjtkqnmnzqghoz")
    print("3. Go to Settings > API")
    print("4. Copy the 'anon public' key to SUPABASE_ANON_KEY")
    print("5. Copy the 'service_role secret' key to SUPABASE_SERVICE_ROLE_KEY")
    print("6. Go to Settings > Database")
    print("7. Copy the 'Connection string' > 'URI' to DATABASE_URL")
    print("8. Update the .env file with these values")
    print("9. Run this script again to test the connection")
    
    # Test connection if credentials are set
    print("\n" + "=" * 50)
    test_supabase_connection()

if __name__ == "__main__":
    main() 