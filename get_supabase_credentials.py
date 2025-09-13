#!/usr/bin/env python3
"""
Script to help you get the correct Supabase credentials
"""

def show_supabase_setup_guide():
    """Show step-by-step guide to get Supabase credentials"""
    print("🔧 Supabase Setup Guide")
    print("=" * 60)
    print()
    print("📋 Step 1: Access Your Supabase Dashboard")
    print("1. Go to: https://supabase.com/dashboard")
    print("2. Sign in to your account")
    print("3. Find your project: luiiwyzjtkqnmnzqghoz")
    print("4. Click on the project to open it")
    print()
    
    print("📋 Step 2: Get API Keys")
    print("1. In your project dashboard, go to 'Settings' (gear icon)")
    print("2. Click on 'API' in the left sidebar")
    print("3. You'll see two important keys:")
    print("   - 'anon public' key (for client-side access)")
    print("   - 'service_role secret' key (for server-side access)")
    print("4. Copy both keys - you'll need them for the .env file")
    print()
    
    print("📋 Step 3: Get Database Connection String")
    print("1. Still in Settings, click on 'Database' in the left sidebar")
    print("2. Scroll down to 'Connection string' section")
    print("3. Look for 'URI' - this is your DATABASE_URL")
    print("4. The format should be:")
    print("   postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres")
    print()
    
    print("📋 Step 4: Create .env File")
    print("1. In your project root, create a file called '.env'")
    print("2. Add the following content (replace with your actual values):")
    print()
    
    env_template = """# Supabase Configuration
SUPABASE_URL=https://luiiwyzjtkqnmnzqghoz.supabase.co
SUPABASE_ANON_KEY=your_actual_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_actual_service_role_key_here

# Database Configuration
DATABASE_URL=your_actual_database_uri_here

# Development Settings
USE_SQLITE_FALLBACK=false
ENABLE_VECTOR_DB=true
ENABLE_KNOWLEDGE_BASE=true

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
REDIS_DB=0"""
    
    print(env_template)
    print()
    
    print("📋 Step 5: Test Connection")
    print("1. After creating the .env file, run:")
    print("   python test_supabase_connection.py")
    print("2. This will test if your credentials work")
    print()
    
    print("⚠️ Important Notes:")
    print("- Keep your service_role key secret - never commit it to version control")
    print("- The anon key is safe to use in client-side code")
    print("- Make sure your Supabase project has the required tables (run memory_schema.sql)")
    print("- The database URL format is different from the old format in env.example")
    print()

def show_current_issues():
    """Show current issues with the setup"""
    print("🚨 Current Issues Found:")
    print("=" * 40)
    print()
    print("❌ Problem 1: Wrong Database URL Format")
    print("Current (incorrect):")
    print("postgresql://postgres:KDxtnciHVvlzrKxV@db.luiiwyzjtkqnmnzqghoz.supabase.co:5432/postgres")
    print()
    print("Should be (correct):")
    print("postgresql://postgres.luiiwyzjtkqnmnzqghoz:KDxtnciHVvlzrKxV@aws-0-us-east-1.pooler.supabase.com:6543/postgres")
    print()
    print("❌ Problem 2: Missing .env File")
    print("The system is trying to use default values instead of your Supabase credentials")
    print()
    print("❌ Problem 3: No Authentication Keys")
    print("The system needs your Supabase API keys to authenticate")
    print()

def create_env_template():
    """Create a template .env file"""
    print("📝 Creating .env template file...")
    
    template_content = """# Supabase Configuration
# Replace these with your actual values from Supabase dashboard
SUPABASE_URL=https://luiiwyzjtkqnmnzqghoz.supabase.co
SUPABASE_ANON_KEY=your_actual_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_actual_service_role_key_here

# Database Configuration
# Get this from Supabase dashboard > Settings > Database > Connection string > URI
DATABASE_URL=postgresql://postgres.luiiwyzjtkqnmnzqghoz:your_password@aws-0-us-east-1.pooler.supabase.com:6543/postgres

# Development Settings
USE_SQLITE_FALLBACK=false
ENABLE_VECTOR_DB=true
ENABLE_KNOWLEDGE_BASE=true

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
"""
    
    with open('.env.template', 'w') as f:
        f.write(template_content)
    
    print("✅ Created .env.template file")
    print("📋 Next steps:")
    print("1. Copy .env.template to .env")
    print("2. Replace the placeholder values with your actual Supabase credentials")
    print("3. Run: python test_supabase_connection.py")

def main():
    """Main function"""
    print("🔧 Supabase Credentials Setup Helper")
    print("=" * 50)
    print()
    
    show_current_issues()
    print()
    show_supabase_setup_guide()
    print()
    create_env_template()
    print()
    print("🎯 Summary:")
    print("To use Supabase instead of SQLite, you need to:")
    print("1. Get your Supabase API keys from the dashboard")
    print("2. Get the correct database connection string")
    print("3. Create a .env file with these credentials")
    print("4. Test the connection")
    print()
    print("Once you have your credentials, run:")
    print("python test_supabase_connection.py")

if __name__ == "__main__":
    main() 