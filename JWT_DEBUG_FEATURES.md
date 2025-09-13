# JWT Debug Features for Supabase Authentication

## Overview

Comprehensive debug logging has been added to the JWT token validation process with Supabase to help troubleshoot authentication issues and monitor the validation flow.

## Debug Features Added

### 1. **Enhanced JWT Token Verification** (`config/supabase.py`)

#### **`verify_user_token()` Method**

- **Token Analysis**: Analyzes JWT structure before validation
- **Performance Timing**: Measures Supabase verification time
- **Detailed Logging**: Logs each step of the validation process
- **Error Classification**: Categorizes different types of validation errors

```python
# Debug logs include:
- Token length and format validation
- JWT structure analysis
- Supabase verification timing
- User data retrieval details
- Error type classification
```

#### **`_analyze_jwt_token()` Method**

- **JWT Structure Analysis**: Decodes header and payload without verification
- **Claim Extraction**: Extracts common JWT claims (exp, iss, sub, aud, iat, nbf)
- **Format Validation**: Checks token format and structure
- **Error Handling**: Provides detailed error information

### 2. **Enhanced Authentication Endpoint** (`endpoints/auth.py`)

#### **`get_current_user()` Function**

- **Request Context**: Logs request ID and client IP
- **Validation Timing**: Measures total validation time
- **User Status Tracking**: Logs user active status and permissions
- **Security Events**: Logs authentication events for monitoring

#### **`validate_token()` Endpoint**

- **Comprehensive Logging**: Tracks token validation requests
- **User Status Checks**: Logs active/inactive user attempts
- **Scope Assignment**: Logs user permission scopes
- **Error Tracking**: Detailed error logging with context

### 3. **Enhanced Authentication Middleware** (`middleware/security.py`)

#### **`AuthenticationMiddleware.dispatch()`**

- **Request Processing**: Logs authentication attempts for each request
- **Token Extraction**: Logs JWT token detection and format
- **Validation Timing**: Measures middleware validation time
- **User Context**: Logs successful authentication and user details

### 4. **Profile Data Retrieval** (`config/supabase.py`)

#### **`get_user_by_id()` Method**

- **Database Queries**: Logs profile data retrieval attempts
- **User Status**: Logs user active and admin status
- **Error Handling**: Detailed error logging for database issues

#### **`update_last_login()` Method**

- **Login Tracking**: Logs last login timestamp updates
- **Performance Monitoring**: Tracks database update operations

### 5. **Debug Endpoint** (`endpoints/auth.py`)

#### **`/auth/debug/token-analysis`**

- **Token Analysis**: Analyzes JWT structure without authentication
- **Supabase Verification**: Tests token verification separately
- **Development Tool**: Useful for troubleshooting token issues

## Debug Log Levels

### **DEBUG Level**

- Detailed step-by-step validation process
- Token structure analysis
- Performance timing information
- User data retrieval details

### **WARNING Level**

- Invalid token formats
- Inactive user attempts
- Missing profile data
- Validation failures

### **ERROR Level**

- Supabase verification errors
- Database connection issues
- Unexpected exceptions
- Security violations

## Debug Information Captured

### **Token Information**

- Token length and format
- JWT structure analysis
- Header and payload contents
- Common JWT claims
- Signature length

### **Validation Process**

- Request context (ID, IP, timestamp)
- Supabase verification timing
- User data retrieval timing
- Error classification and details

### **User Information**

- User ID and email
- Active/inactive status
- Admin privileges
- Organization details
- Last login updates

### **Security Events**

- Authentication successes/failures
- Token validation attempts
- Inactive user access attempts
- Error conditions and types

## Usage Examples

### **1. Monitor Authentication Flow**

```bash
# Set log level to DEBUG
export LOG_LEVEL=DEBUG

# Watch authentication logs
tail -f logs/app.log | grep -E "(JWT|auth|token)"
```

### **2. Analyze Token Structure**

```bash
# Use debug endpoint
curl -X POST "http://localhost:8000/auth/debug/token-analysis" \
  -H "Content-Type: application/json" \
  -d '{"token": "your_jwt_token_here"}'
```

### **3. Track Specific User**

```bash
# Filter logs for specific user
tail -f logs/app.log | grep "user@example.com"
```

### **4. Monitor Performance**

```bash
# Track validation timing
tail -f logs/app.log | grep "verification completed in"
```

## Security Considerations

### **Production Usage**

- Debug endpoints should be disabled in production
- Sensitive token information is logged at DEBUG level only
- Security events are logged at appropriate levels
- Token analysis is performed without verification

### **Log Management**

- Debug logs contain sensitive information
- Implement proper log rotation and retention
- Consider log encryption for sensitive environments
- Monitor log file sizes and performance impact

## Troubleshooting Common Issues

### **1. Token Expired**

```
ERROR: Token appears to be expired
```

- Check token expiration time in JWT payload
- Verify system clock synchronization
- Review token refresh logic

### **2. Invalid Token Format**

```
WARNING: Invalid JWT format detected
```

- Verify token is properly formatted (3 parts separated by dots)
- Check for missing or malformed token parts
- Validate token encoding

### **3. User Not Found**

```
WARNING: No profile data found for user ID
```

- Verify user exists in profiles table
- Check user creation process
- Validate user ID consistency

### **4. Inactive User**

```
WARNING: User account is inactive
```

- Check user active status in database
- Review user activation process
- Verify account status management

## Configuration

### **Environment Variables**

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Disable debug endpoint in production
export DISABLE_DEBUG_ENDPOINTS=true
```

### **Logging Configuration**

```python
# In your logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Benefits

1. **Comprehensive Monitoring**: Full visibility into authentication process
2. **Performance Tracking**: Monitor validation timing and bottlenecks
3. **Error Diagnosis**: Detailed error information for troubleshooting
4. **Security Auditing**: Track authentication events and security violations
5. **Development Support**: Debug tools for token analysis and testing

This debug system provides complete visibility into the JWT validation process while maintaining security and performance standards.
