# Quick Setup Guide

## 1. Get Your Supabase Credentials

1. Go to your Supabase project dashboard: https://supabase.com/dashboard
2. Navigate to your project: `luiiwyzjtkqnmnzqghoz`
3. Go to **Settings** → **API**
4. Copy these values:
   - **Project URL**: `https://luiiwyzjtkqnmnzqghoz.supabase.co`
   - **Anon Key**: (public key)
   - **Service Role Key**: (private key - keep secret!)

## 2. Set Up Database Tables

1. In your Supabase dashboard, go to **SQL Editor**
2. Copy and paste the contents of `supabase_setup.sql`
3. Click **Run** to execute the script

## 3. Configure Backend Environment

Create a `.env` file in your backend project root:

```env
# Supabase Configuration
SUPABASE_URL=https://luiiwyzjtkqnmnzqghoz.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

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

## 4. Install Dependencies

```bash
pip install supabase
```

## 5. Test the Backend

```bash
uvicorn main:app --reload
```

Visit: http://localhost:8000/docs

## 6. Test Authentication Endpoints

### Health Check

```bash
curl http://localhost:8000/auth/health
```

### Token Validation (without auth)

```bash
curl http://localhost:8000/auth/validate
```

## 7. Frontend Integration

Follow the `FRONTEND_INTEGRATION.md` guide to add Supabase authentication to your existing frontend.

## 8. Test Complete Flow

1. **Register a user** through your frontend
2. **Login** with the registered user
3. **Make API calls** with the JWT token
4. **Check user profile** at `/auth/me`

## Troubleshooting

### Common Issues:

1. **"Missing Supabase environment variables"**

   - Check your `.env` file has all required variables
   - Ensure no spaces around `=` signs

2. **"Database connection failed"**

   - Verify your database URL is correct
   - Check if Supabase project is active

3. **"Token validation failed"**

   - Ensure Supabase URL and keys are correct
   - Check if user exists in database

4. **CORS errors**
   - Add your frontend URL to `CORS_ORIGINS`
   - Ensure frontend is running on the correct port

### Debug Mode:

Add this to your main.py for detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Next Steps

1. ✅ Set up Supabase database tables
2. ✅ Configure backend environment
3. ✅ Test backend endpoints
4. 🔄 Add authentication to your frontend
5. 🔄 Test complete authentication flow
6. 🔄 Deploy to production

Your backend is now ready to work with Supabase authentication! 🚀
