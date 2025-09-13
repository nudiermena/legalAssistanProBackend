# Supabase Authentication Integration Guide

This guide explains how to set up Supabase authentication for the Legal AI Assistant, where the frontend handles user registration/login and the backend validates JWT tokens.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Supabase      │
│   (Vite/React)  │    │   (FastAPI)     │    │   (Database)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │ 1. User registers/    │                       │
         │    logs in            │                       │
         │──────────────────────▶│                       │
         │                       │                       │
         │ 2. Gets JWT token     │                       │
         │◀──────────────────────│                       │
         │                       │                       │
         │ 3. Makes API calls    │                       │
         │    with JWT token     │                       │
         │──────────────────────▶│                       │
         │                       │ 4. Validates token    │
         │                       │──────────────────────▶│
         │                       │                       │
         │                       │ 5. Returns user data  │
         │                       │◀──────────────────────│
         │                       │                       │
         │ 6. Returns protected  │                       │
         │    data               │                       │
         │◀──────────────────────│                       │
```

## Setup Instructions

### 1. Supabase Project Setup

1. **Create a Supabase project**:

   - Go to [supabase.com](https://supabase.com)
   - Create a new project
   - Note down your project URL and anon key

2. **Create the profiles table**:

   ```sql
   -- Create profiles table
   CREATE TABLE profiles (
     id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
     email TEXT UNIQUE NOT NULL,
     username TEXT UNIQUE,
     full_name TEXT,
     organization TEXT,
     is_admin BOOLEAN DEFAULT FALSE,
     is_active BOOLEAN DEFAULT TRUE,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
     last_login TIMESTAMP WITH TIME ZONE,
     avatar_url TEXT
   );

   -- Enable RLS (Row Level Security)
   ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

   -- Create policies
   CREATE POLICY "Users can view own profile" ON profiles
     FOR SELECT USING (auth.uid() = id);

   CREATE POLICY "Users can update own profile" ON profiles
     FOR UPDATE USING (auth.uid() = id);

   CREATE POLICY "Admins can view all profiles" ON profiles
     FOR SELECT USING (
       EXISTS (
         SELECT 1 FROM profiles WHERE id = auth.uid() AND is_admin = true
       )
     );

   -- Create function to handle new user registration
   CREATE OR REPLACE FUNCTION handle_new_user()
   RETURNS TRIGGER AS $$
   BEGIN
     INSERT INTO profiles (id, email, username, full_name, organization, is_admin, is_active)
     VALUES (
       NEW.id,
       NEW.email,
       NEW.raw_user_meta_data->>'username',
       NEW.raw_user_meta_data->>'full_name',
       NEW.raw_user_meta_data->>'organization',
       COALESCE((NEW.raw_user_meta_data->>'is_admin')::boolean, false),
       true
     );
     RETURN NEW;
   END;
   $$ LANGUAGE plpgsql SECURITY DEFINER;

   -- Create trigger for new user registration
   CREATE TRIGGER on_auth_user_created
     AFTER INSERT ON auth.users
     FOR EACH ROW EXECUTE FUNCTION handle_new_user();
   ```

### 2. Backend Configuration

1. **Install dependencies**:

   ```bash
   pip install supabase
   ```

2. **Update environment variables** (`.env`):

   ```env
   # Supabase Configuration
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_ANON_KEY=your_supabase_anon_key
   SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

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

   # Database Configuration
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/legal_assistant
   ```

3. **Start the backend**:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### 3. Frontend Configuration

1. **Install dependencies**:

   ```bash
   cd frontend
   npm install
   ```

2. **Create environment file** (`.env`):

   ```env
   # Supabase Configuration
   VITE_SUPABASE_URL=your_supabase_project_url
   VITE_SUPABASE_ANON_KEY=your_supabase_anon_key

   # API Configuration
   VITE_API_URL=http://localhost:8000

   # Environment
   VITE_ENV=development
   ```

3. **Start the frontend**:
   ```bash
   npm run dev
   ```

## Authentication Flow

### User Registration

1. User fills out registration form on frontend
2. Frontend calls `supabase.auth.signUp()` with user data
3. Supabase creates user and sends confirmation email
4. User confirms email and can now log in

### User Login

1. User enters credentials on frontend
2. Frontend calls `supabase.auth.signInWithPassword()`
3. Supabase returns JWT token
4. Frontend stores token in session

### API Authentication

1. Frontend makes API calls with JWT token in Authorization header
2. Backend middleware validates token with Supabase
3. If valid, backend processes request and returns data
4. If invalid, backend returns 401 error

## API Endpoints

### Authentication Endpoints

- `POST /auth/validate` - Validate JWT token
- `GET /auth/me` - Get current user profile
- `PUT /auth/profile` - Update user profile
- `GET /auth/users` - List users (admin only)
- `GET /auth/user/{user_id}` - Get user by ID
- `GET /auth/health` - Health check

### Protected Endpoints

All other endpoints require authentication via JWT token in Authorization header:

```
Authorization: Bearer <jwt_token>
```

## Security Features

### Rate Limiting

- Per-user rate limiting based on JWT token
- Fallback to IP-based rate limiting
- Configurable limits per minute, hour, and day

### Token Validation

- JWT tokens validated with Supabase
- Automatic token refresh handling
- Secure token storage in frontend

### CORS Configuration

- Configured for frontend-backend communication
- Secure origins in production

### Input Validation

- All user inputs validated and sanitized
- SQL injection protection
- XSS protection

## Testing the Integration

### 1. Test User Registration

```bash
# Frontend: http://localhost:3000
# Register a new user through the UI
```

### 2. Test User Login

```bash
# Frontend: http://localhost:3000
# Login with registered user
```

### 3. Test API Authentication

```bash
# Get JWT token from frontend session
# Make API call with token
curl -H "Authorization: Bearer <jwt_token>" \
     http://localhost:8000/auth/me
```

### 4. Test Protected Endpoints

```bash
# Test protected endpoint
curl -H "Authorization: Bearer <jwt_token>" \
     http://localhost:8000/protected/example
```

## Troubleshooting

### Common Issues

1. **CORS Errors**:

   - Check CORS_ORIGINS in backend .env
   - Ensure frontend URL is included

2. **Token Validation Errors**:

   - Verify Supabase URL and keys
   - Check token expiration
   - Ensure user is active in database

3. **Database Connection Errors**:

   - Verify Supabase project is active
   - Check database policies
   - Ensure profiles table exists

4. **Rate Limiting Issues**:
   - Check Redis connection
   - Verify rate limit configuration
   - Check user identification logic

### Debug Mode

Enable debug logging in backend:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Production Deployment

### Environment Variables

- Use strong, unique secret keys
- Configure production Supabase project
- Set appropriate CORS origins
- Configure production Redis instance

### Security Considerations

- Enable HTTPS in production
- Use secure session storage
- Implement proper error handling
- Monitor authentication logs
- Regular security audits

### Performance Optimization

- Implement token caching
- Optimize database queries
- Use connection pooling
- Monitor rate limiting metrics

## Support

For issues or questions:

1. Check Supabase documentation
2. Review FastAPI authentication docs
3. Check application logs
4. Verify environment configuration
