# Legal AI Assistant API Setup Guide

## Current Status ✅

Your API is running successfully in development mode with the following configuration:

- **Security Level**: Development
- **Rate Limiting**: 60 requests/minute
- **Authentication**: Using default test API key
- **Supabase Integration**: Active
- **Security Monitoring**: Enabled

## Fixed Issues

✅ **Pydantic V2 Warning**: Fixed `schema_extra` → `json_schema_extra` in whistleblower_analysis.py

## Environment Configuration

### 1. Create Environment File

Create a `.env` file in your project root:

```bash
# Copy the example file
cp env.example .env
```

### 2. Configure API Keys

For **Development** (current setup):

```bash
API_KEYS=test_key_12345
```

For **Production**:

```bash
API_KEYS=your_secure_key_1,your_secure_key_2,your_secure_key_3
```

### 3. Security Configuration

**Development Mode** (current):

```bash
SECURITY_ENVIRONMENT=development
SECRET_KEY=your-secret-key-here-change-in-production
```

**Production Mode**:

```bash
SECURITY_ENVIRONMENT=production
SECRET_KEY=your-very-secure-production-key
```

## API Endpoints

### Available Endpoints:

1. **Health Check**: `GET /health`
2. **Security Status**: `GET /security/status`
3. **API Documentation**: `GET /docs` (development only)
4. **Legal Research**: `POST /legal-research`
5. **Contract Review**: `POST /contract-review`
6. **Document Drafting**: `POST /document-drafting`
7. **Legal Chat**: `POST /legal-chat`
8. **Case Prediction**: `POST /case-prediction`
9. **Regulatory Analysis**: `POST /regulatory-analysis`
10. **Patent Search**: `POST /patent-search`
11. **Whistleblower Analysis**: `POST /whistleblower-analysis`

## Authentication

### Development Mode

- Uses default test API key: `test_key_12345`
- No authentication required for public endpoints
- JWT tokens supported for Supabase integration

### Production Mode

- Requires valid API keys in `X-API-Key` header
- JWT authentication for user sessions
- Rate limiting enforced

## Testing the API

### 1. Health Check

```bash
curl http://localhost:8000/health
```

### 2. Security Status

```bash
curl http://localhost:8000/security/status
```

### 3. Test Legal Research

```bash
curl -X POST "http://localhost:8000/legal-research" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test_key_12345" \
  -d '{
    "query": "What are the requirements for contract formation in Colombia?",
    "jurisdiction": "Colombia",
    "legal_area": "Contract Law"
  }'
```

## Rate Limiting

Current limits:

- **Per Minute**: 60 requests
- **Per Hour**: 1,000 requests
- **Per Day**: 10,000 requests
- **Burst**: 10 requests

## Security Features

✅ **Active Security Features**:

- Rate limiting
- API key authentication
- Input validation
- Security headers
- Request logging
- Real-time monitoring

## Next Steps

1. **Configure Production Environment**:

   - Set `SECURITY_ENVIRONMENT=production`
   - Generate secure API keys
   - Configure proper CORS origins

2. **Set Up Supabase**:

   - Configure Supabase URL and keys
   - Set up user authentication

3. **Database Setup**:

   - Configure PostgreSQL connection
   - Run database migrations

4. **Redis Setup** (for rate limiting):
   - Install and configure Redis
   - Update Redis URL in environment

## Troubleshooting

### Common Issues:

1. **Pydantic Warnings**: ✅ Fixed
2. **Default API Key Warning**: Expected in development
3. **CORS Issues**: Configure `CORS_ORIGINS` for production
4. **Rate Limiting**: Adjust limits in environment variables

### Debug Endpoints:

- `GET /debug/env` - View environment variables
- `GET /security/status` - Security configuration status

## Production Checklist

- [ ] Set `SECURITY_ENVIRONMENT=production`
- [ ] Generate secure `SECRET_KEY`
- [ ] Configure production `API_KEYS`
- [ ] Set up proper `CORS_ORIGINS`
- [ ] Configure Supabase production keys
- [ ] Set up Redis for rate limiting
- [ ] Configure database connection
- [ ] Set up monitoring and logging

Your API is ready for development and testing! 🚀
