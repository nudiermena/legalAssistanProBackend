# Supabase Setup Guide - Fix Authentication Issues

## 🔧 **Issue Identified**

The authentication is failing because the Supabase environment variables are not properly configured. The error shows:

```
ERROR:config.supabase:Failed to initialize Supabase clients: Invalid URL
```

## 🚀 **Quick Fix Steps**

### 1. **Create `.env` File**

Create a `.env` file in your project root with the following content:

```env
# Supabase Configuration
SUPABASE_URL=https://luiiwyzjtkqnmnzqghoz.supabase.co
SUPABASE_ANON_KEY=your_actual_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_actual_service_role_key_here

# Database Configuration
DATABASE_URL=postgresql://postgres:KDxtnciHVvlzrKxV@db.luiiwyzjtkqnmnzqghoz.supabase.co:5432/postgres

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
```

### 2. **Get Your Supabase Credentials**

1. Go to your Supabase project dashboard: https://supabase.com/dashboard
2. Navigate to your project: `luiiwyzjtkqnmnzqghoz`
3. Go to **Settings** → **API**
4. Copy these values:

   **Project URL**: `https://luiiwyzjtkqnmnzqghoz.supabase.co`

   **Anon Key** (public key): Copy the "anon public" key

   **Service Role Key** (private key): Copy the "service_role secret" key

### 3. **Update Your `.env` File**

Replace the placeholder values in your `.env` file:

```env
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # Your actual anon key
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # Your actual service role key
```

### 4. **Restart Your Application**

```bash
# Stop the current server (Ctrl+C)
# Then restart
uvicorn main:app --reload
```

## 🔍 **Verify Configuration**

### **Test Environment Variables**

Add this debug endpoint to test your configuration:

```python
# Add to main.py temporarily
@app.get("/debug/env")
async def debug_env():
    """Debug environment variables (remove in production)"""
    return {
        "SUPABASE_URL": os.getenv("SUPABASE_URL", "NOT_SET"),
        "SUPABASE_ANON_KEY": os.getenv("SUPABASE_ANON_KEY", "NOT_SET")[:20] + "..." if os.getenv("SUPABASE_ANON_KEY") else "NOT_SET",
        "SUPABASE_SERVICE_ROLE_KEY": os.getenv("SUPABASE_SERVICE_ROLE_KEY", "NOT_SET")[:20] + "..." if os.getenv("SUPABASE_SERVICE_ROLE_KEY") else "NOT_SET",
    }
```

### **Test Authentication**

```bash
# Test with your JWT token
curl -H "Authorization: Bearer your_jwt_token" http://localhost:8000/auth/me

# Test token validation
curl -H "Authorization: Bearer your_jwt_token" http://localhost:8000/auth/validate
```

## 🐛 **Common Issues and Solutions**

### **Issue 1: "Invalid URL" Error**

- **Cause**: `SUPABASE_URL` is not set or incorrect
- **Solution**: Make sure `SUPABASE_URL` is set to `https://luiiwyzjtkqnmnzqghoz.supabase.co`

### **Issue 2: "SUPABASE_ANON_KEY must be set"**

- **Cause**: Anon key is missing or empty
- **Solution**: Copy the correct anon key from Supabase dashboard

### **Issue 3: "SUPABASE_SERVICE_ROLE_KEY must be set"**

- **Cause**: Service role key is missing
- **Solution**: Copy the service role key from Supabase dashboard

### **Issue 4: Environment variables not loading**

- **Cause**: `.env` file not in correct location or not being loaded
- **Solution**:
  - Make sure `.env` file is in the project root
  - Install python-dotenv: `pip install python-dotenv`
  - Add to main.py: `from dotenv import load_dotenv; load_dotenv()`

## 📋 **Complete Setup Checklist**

- [ ] Created `.env` file in project root
- [ ] Added correct `SUPABASE_URL`
- [ ] Added correct `SUPABASE_ANON_KEY`
- [ ] Added correct `SUPABASE_SERVICE_ROLE_KEY`
- [ ] Restarted the application
- [ ] Tested authentication endpoint
- [ ] Verified JWT token validation works

## 🔒 **Security Notes**

1. **Never commit `.env` file to git** - it contains sensitive credentials
2. **Use different keys for development and production**
3. **Rotate keys regularly** for security
4. **Service role key has admin privileges** - keep it secure

## 🚀 **After Setup**

Once configured correctly, you should see:

```
INFO:config.supabase:Supabase clients initialized successfully
DEBUG:config.supabase:JWT format appears valid, proceeding with Supabase verification
DEBUG:config.supabase:Token validation successful for user: nudier716@hotmail.com
```

## 📞 **Need Help?**

If you're still having issues:

1. Check the debug logs for specific error messages
2. Verify your Supabase project is active
3. Ensure your JWT token is valid and not expired
4. Test with the debug endpoint: `GET /debug/env`

The authentication should work perfectly once the environment variables are properly configured!
