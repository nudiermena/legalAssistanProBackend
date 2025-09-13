# Security Documentation

## Overview

The Legal AI Assistant API has been enhanced with comprehensive security features to protect against common threats and ensure secure operation in production environments. This document outlines all security measures, configuration options, and best practices.

## Security Features

### 1. Rate Limiting

**Purpose**: Prevents API abuse and DoS attacks by limiting request frequency.

**Implementation**:

- Redis-based rate limiting with sliding window algorithm
- Configurable limits per minute, hour, and day
- Per-user and per-IP tracking
- Automatic cleanup of old rate limit data

**Configuration**:

```bash
# Environment variables
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
RATE_LIMIT_PER_DAY=10000
RATE_LIMIT_BURST=10
```

**Default Limits**:

- 60 requests per minute
- 1,000 requests per hour
- 10,000 requests per day
- 10 requests burst limit

### 2. Authentication

**Purpose**: Ensures only authorized users can access protected endpoints.

**Implementation**:

- API key-based authentication
- Environment variable configuration
- Automatic user tracking and logging
- Protected endpoint enforcement

**Configuration**:

```bash
# API Keys (comma-separated)
API_KEYS=key1,key2,key3
```

**Usage**:

```bash
curl -H "X-API-Key: your_api_key" https://api.example.com/endpoint
```

### 3. Input Validation & Sanitization

**Purpose**: Prevents injection attacks and ensures data integrity.

**Features**:

- Automatic text sanitization
- SQL injection pattern detection
- XSS attack prevention
- File type validation
- Content length limits

**Validation Rules**:

- Maximum input length: 10,000 characters
- Maximum JSON payload: 1MB
- Allowed file types: PDF, DOC, DOCX, TXT, RTF, images
- Maximum file size: 10MB

### 4. Security Headers

**Purpose**: Protects against common web vulnerabilities.

**Headers Applied**:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: geolocation=(), microphone=(), camera=()`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Content-Security-Policy`: Comprehensive CSP policy

### 5. File Upload Security

**Purpose**: Prevents malicious file uploads and ensures file integrity.

**Features**:

- File type validation using magic numbers
- File size limits
- Malicious content detection
- Automatic file scanning
- Secure file handling

**Validation Process**:

1. File extension check
2. MIME type validation
3. Magic number verification
4. Content scanning for malicious patterns
5. Size validation

### 6. Request Logging & Monitoring

**Purpose**: Provides comprehensive audit trail and security monitoring.

**Features**:

- Request/response logging
- Security event tracking
- Anomaly detection
- Real-time alerting
- Performance monitoring

**Logged Information**:

- Request ID, user ID, client IP
- Request method, URL, headers
- Response status, processing time
- Security events and alerts
- Error details (sanitized)

### 7. Security Monitoring & Alerting

**Purpose**: Detects and responds to security threats in real-time.

**Features**:

- Real-time event monitoring
- Anomaly detection
- Automated alerting
- Security dashboard
- Activity analytics

**Alert Types**:

- Authentication failures
- Rate limit violations
- Malicious content detection
- High activity from single source
- API errors and exceptions

**Alert Levels**:

- **Critical**: Immediate action required
- **High**: High priority investigation
- **Medium**: Monitor and investigate
- **Low**: Informational

## Configuration

### Environment Variables

```bash
# Security Environment
SECURITY_ENVIRONMENT=production  # development, staging, production

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
RATE_LIMIT_PER_DAY=10000
RATE_LIMIT_BURST=10

# Authentication
API_KEYS=key1,key2,key3
SECRET_KEY=your-secret-key-here

# CORS Configuration
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# File Upload
MAX_FILE_SIZE=10485760  # 10MB in bytes
SCAN_UPLOADS=true

# Redis Configuration
REDIS_URL=redis://localhost:6379
```

### Security Levels

#### Development

- Relaxed rate limiting
- Detailed error messages
- CORS allows all origins
- Security headers enabled
- Full logging

#### Staging

- Moderate rate limiting
- Sanitized error messages
- Restricted CORS origins
- Security headers enabled
- Full logging

#### Production

- Strict rate limiting
- Generic error messages
- Restricted CORS origins
- Security headers enabled
- Minimal sensitive data logging
- API documentation disabled

## Security Dashboard

### Access

- URL: `/security/dashboard`
- Real-time monitoring interface
- Security status overview
- Alert management
- Activity analytics

### Features

- **Status Overview**: Overall security health
- **Recent Alerts**: Latest security alerts
- **Event Log**: Recent security events
- **User Activity**: User behavior analytics
- **IP Activity**: IP-based activity monitoring
- **Auto-refresh**: Updates every 30 seconds

### API Endpoints

#### Security Status

```bash
GET /security/status
```

#### Recent Alerts

```bash
GET /security/alerts?minutes=60
```

#### Recent Events

```bash
GET /security/events?minutes=60
```

#### User Activity

```bash
GET /security/user-activity?hours=24
```

#### IP Activity

```bash
GET /security/ip-activity?hours=24
```

#### Security Configuration

```bash
GET /security/config
```

## Security Best Practices

### 1. API Key Management

- Use strong, randomly generated API keys
- Rotate keys regularly
- Store keys securely
- Monitor key usage

### 2. Rate Limiting

- Set appropriate limits for your use case
- Monitor rate limit violations
- Adjust limits based on legitimate usage patterns

### 3. File Uploads

- Validate all file uploads
- Scan for malicious content
- Limit file types and sizes
- Store files securely

### 4. Monitoring

- Monitor security dashboard regularly
- Set up alert notifications
- Review security logs
- Investigate anomalies

### 5. Environment Configuration

- Use production security level in production
- Configure CORS properly
- Set up Redis for rate limiting
- Use HTTPS in production

## Threat Protection

### SQL Injection

- Input sanitization
- Pattern detection
- Parameterized queries
- Error message sanitization

### XSS Attacks

- Input sanitization
- Content Security Policy
- XSS protection headers
- Output encoding

### File Upload Attacks

- File type validation
- Content scanning
- Size limits
- Secure storage

### Rate Limiting Bypass

- Multiple rate limit windows
- IP and user tracking
- Burst protection
- Redis-based storage

### Authentication Bypass

- API key validation
- Protected endpoint enforcement
- User activity tracking
- Failed attempt monitoring

## Monitoring & Alerting

### Security Events

All security events are logged with the following information:

- Event type and severity
- Timestamp and request ID
- User ID and client IP
- Event details and metadata

### Alert Thresholds

- Authentication failures: 5 per minute
- Rate limit violations: 10 per minute
- File upload errors: 5 per minute
- Malicious content: 3 per minute
- API errors: 20 per minute
- Requests per IP: 100 per minute
- Requests per user: 50 per minute

### Alert Actions

- **Logging**: All alerts are logged
- **Email**: Critical and high alerts trigger email notifications
- **Dashboard**: All alerts appear in security dashboard
- **Monitoring**: Alerts are tracked for trend analysis

## Incident Response

### 1. Detection

- Automated monitoring detects threats
- Alerts are generated for suspicious activity
- Security dashboard provides real-time visibility

### 2. Investigation

- Review security logs and events
- Analyze user and IP activity
- Check for patterns and trends
- Identify root cause

### 3. Response

- Block malicious IPs if necessary
- Revoke compromised API keys
- Adjust rate limits if needed
- Update security configuration

### 4. Recovery

- Restore normal operations
- Monitor for continued threats
- Update security measures
- Document incident details

## Compliance

### Data Protection

- Personal data masking in logs
- Secure data handling
- Access control and authentication
- Audit trail maintenance

### Legal Requirements

- Colombian legal framework compliance
- Data processing regulations
- Privacy protection measures
- Legal disclaimer inclusion

## Troubleshooting

### Common Issues

#### Rate Limiting Too Strict

- Check current rate limits
- Adjust limits in configuration
- Monitor legitimate usage patterns

#### Authentication Failures

- Verify API key format
- Check API key in environment
- Review authentication logs

#### File Upload Issues

- Check file type restrictions
- Verify file size limits
- Review file validation logs

#### Security Dashboard Not Loading

- Check Redis connection
- Verify security middleware
- Review application logs

### Debug Mode

In development mode, additional debugging information is available:

- Detailed error messages
- Security event details
- Configuration information
- Performance metrics

## Support

For security-related issues or questions:

1. Check the security dashboard
2. Review security logs
3. Consult this documentation
4. Contact security team

## Updates

This security documentation is updated regularly to reflect:

- New security features
- Configuration changes
- Best practice updates
- Threat landscape changes

---

**Last Updated**: December 2024
**Version**: 1.0.0
**Security Level**: Production Ready
