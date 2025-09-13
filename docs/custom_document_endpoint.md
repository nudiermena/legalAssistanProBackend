# Custom Document Endpoint Implementation

## Overview

This document describes the implementation of a new custom document endpoint that allows users to create personalized legal documents with detailed specifications. The implementation includes both the new custom endpoint and enhancements to the existing document drafting system.

## New Endpoints

### 1. Custom Document Endpoint

**POST** `/api/v1/draft-custom-document`

Creates personalized legal documents based on detailed user specifications.

#### Request Model: `CustomDocumentRequest`

```json
{
  "document_type": "string",
  "description": "string",
  "parties": [
    {
      "name": "string",
      "identification": "string",
      "role": "string"
    }
  ],
  "key_points": "string",
  "industry": "string",
  "jurisdiction": "string",
  "complexity": "simple|standard|complex"
}
```

#### Response Model: `DocumentDraftingResponse`

```json
{
  "document": {
    "content": "string",
    "sections": ["string"],
    "markdown": true
  },
  "document_type": "string",
  "jurisdiction": "string",
  "key_requirements": ["string"],
  "parties": [{ "name": "string", "role": "string" }],
  "colombian_compliance": {
    "framework_version": "string",
    "status": "string",
    "constitutional_principles": ["string"],
    "validation_date": "string"
  },
  "document_url": "string",
  "timestamp": "datetime",
  "complexity": "string",
  "industry": "string"
}
```

### 2. Supporting Endpoints

#### Get Industries

**GET** `/document-drafting/industries`
Returns available industries for custom documents.

#### Get Jurisdictions

**GET** `/document-drafting/jurisdictions`
Returns available jurisdictions for custom documents.

#### Get Complexity Levels

**GET** `/document-drafting/complexity-levels`
Returns available complexity levels for custom documents.

## Enhanced Agent Functions

### 1. `draft_custom_document()`

New function in `agents/document_drafting_agent.py` that handles custom document generation with:

- Detailed prompt formatting based on industry and complexity
- Industry-specific considerations
- Complexity-based instructions
- Enhanced party information with identification

### 2. `format_custom_document_prompt()`

Creates detailed prompts for custom documents including:

- Industry-specific legal considerations
- Complexity-based detail levels
- Comprehensive legal requirements
- Colombian compliance requirements

## Security Features

### 1. Input Validation

- **`validate_document_request()`**: Validates and sanitizes custom document requests
- **`validate_legal_document_request()`**: Validates original document requests
- **`sanitize_text_input()`**: Sanitizes text inputs to prevent injection attacks

### 2. Security Monitoring

- Request logging with client IP tracking
- Security event monitoring via `SecurityMonitor`
- Error logging and alerting
- Rate limiting (inherited from existing middleware)

### 3. Validation Rules

- Document type: 3-200 characters
- Description: 10-2000 characters
- Parties: 1-10 parties with required fields
- Identification: Colombian document format validation
- Industry: Predefined list validation
- Jurisdiction: Predefined list validation
- Complexity: Predefined levels validation

## Industry Considerations

The system includes industry-specific legal considerations:

- **Technology**: IP, confidentiality, software development, licensing
- **Healthcare**: Medical privacy, health regulations, professional liability
- **Finance**: Financial regulations, compliance, risk clauses
- **Real Estate**: Property regulations, public records, ownership clauses
- **Retail**: Commercial considerations, consumer protection
- **Agriculture**: Agricultural regulations, certifications, environmental clauses
- **Oil & Gas**: Energy regulations, environmental, specific liability
- **Education**: Educational regulations, student data protection
- **Construction**: Construction regulations, licenses, insurance, civil liability
- **Other**: General clauses applicable to most industries

## Complexity Levels

### Simple

- Basic terms and standard clauses
- Concise and easy to understand
- Essential legal protections only

### Standard

- Normal level of detail with complete clauses
- Standard protections and mechanisms
- Balanced complexity for most use cases

### Complex

- Highly detailed with specific clauses
- Multiple scenarios and exhaustive protections
- Comprehensive legal coverage

## Usage Examples

### Frontend Integration

```javascript
// Example request to custom document endpoint
const customDocumentRequest = {
  document_type: "Contrato de colaboración tecnológica",
  description: "Contrato para colaboración entre empresas tecnológicas...",
  parties: [
    {
      name: "Empresa ABC S.A.S.",
      identification: "900123456-7",
      role: "Contratante",
    },
    {
      name: "Empresa XYZ Ltda.",
      identification: "800987654-3",
      role: "Contratista",
    },
  ],
  key_points: "Confidencialidad\nPropiedad intelectual\nTérminos de pago",
  industry: "technology",
  jurisdiction: "federal",
  complexity: "standard",
};

const response = await fetch("/api/v1/draft-custom-document", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  },
  body: JSON.stringify(customDocumentRequest),
});
```

### Backend Usage

```python
from endpoints.document_drafting import draft_custom_document_endpoint
from endpoints.document_drafting import CustomDocumentRequest

# Create request
request = CustomDocumentRequest(
    document_type="Contrato de colaboración",
    description="Detailed description...",
    parties=[...],
    key_points="Key points...",
    industry="technology",
    jurisdiction="federal",
    complexity="standard"
)

# Process request
response = await draft_custom_document_endpoint(request, current_user, http_request)
```

## Error Handling

The endpoint includes comprehensive error handling:

1. **Validation Errors**: Detailed error messages for invalid input
2. **Security Errors**: Logging and monitoring of security events
3. **Processing Errors**: Graceful handling of document generation failures
4. **Rate Limiting**: Automatic rate limiting via middleware

## Compliance Features

### Colombian Legal Framework

- Constitutional principles integration
- Regulatory compliance validation
- Data protection requirements
- Administrative procedure support

### Data Protection

- Personal data processing validation
- Consent requirements checking
- Retention period management
- Rights protection mechanisms

## Testing

The implementation includes comprehensive testing:

- Input validation testing
- Security sanitization testing
- Model validation testing
- Agent function testing
- Endpoint integration testing

## Migration Notes

### Backward Compatibility

- Original `/api/v1/draft-document` endpoint remains unchanged
- Existing functionality preserved
- Enhanced with additional security features

### New Features

- Custom document endpoint with detailed specifications
- Industry-specific considerations
- Complexity-based document generation
- Enhanced party information with identification
- Comprehensive validation and security

## Future Enhancements

Potential future improvements:

1. **Template System**: Pre-built templates for common document types
2. **Multi-language Support**: Support for multiple languages
3. **Advanced Validation**: More sophisticated legal validation rules
4. **Integration APIs**: Integration with external legal databases
5. **Version Control**: Document versioning and change tracking
6. **Collaboration**: Multi-user document editing capabilities

## Security Considerations

1. **Input Sanitization**: All inputs are sanitized to prevent injection attacks
2. **Rate Limiting**: Requests are rate-limited to prevent abuse
3. **Authentication**: All endpoints require valid authentication
4. **Logging**: Comprehensive security event logging
5. **Validation**: Strict input validation with predefined rules
6. **Monitoring**: Real-time security monitoring and alerting

## Performance Considerations

1. **Caching**: Document templates and validation rules are cached
2. **Async Processing**: Document generation is asynchronous
3. **Resource Management**: Efficient memory and CPU usage
4. **Scalability**: Designed to handle multiple concurrent requests
5. **Optimization**: Optimized prompts and agent configurations
