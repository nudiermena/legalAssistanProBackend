# Friend Invitation Endpoint Guide

## Overview

The Friend Invitation Endpoint allows users to send personalized invitation emails to friends using the [Resend](https://github.com/resend/resend-python) email service. The endpoint generates beautiful HTML emails with all the invitation details and sends them to the specified friend's email address.

## Endpoints

### POST `/invitation/send`

Sends an invitation email to a friend.

#### Request Body

```json
{
  "friendName": "string",
  "inviterName": "string",
  "inviteCode": "string",
  "shareUrl": "string",
  "dailyLimit": "number",
  "trialDays": "number",
  "expiresAt": "string",
  "friendEmail": "string"
}
```

#### Parameters

- **friendName** (string, required): Name of the friend being invited
- **inviterName** (string, required): Name of the person sending the invitation
- **inviteCode** (string, required): Unique invitation code for the friend
- **shareUrl** (string, required): URL for the friend to access the platform
- **dailyLimit** (number, required): Number of daily requests allowed
- **trialDays** (number, required): Number of trial days
- **expiresAt** (string, required): Expiration date of the invitation
- **friendEmail** (string, required): Email address of the friend to send the invitation to

#### Response

```json
{
  "success": true,
  "message": "Invitation sent successfully to friend@example.com",
  "email_id": "resend_email_id_123"
}
```

### GET `/invitation/health`

Health check endpoint for the invitation service.

#### Response

```json
{
  "status": "healthy",
  "message": "Invitation service is operational",
  "service": "invitation",
  "timestamp": "2025-08-15T01:35:34.025219+00:00"
}
```

## Email Template

The endpoint uses a beautiful HTML email template that includes:

- **Header**: MiAsistenteLegalIA branding with gradient background
- **Personalized greeting**: Uses the friend's name
- **Invitation details**: Shows who sent the invitation
- **Trial information**: Displays trial days and daily limits
- **Invitation code**: Prominently displayed in a code box
- **Expiration date**: Clear expiration information
- **Call-to-action button**: Direct link to start using the platform
- **Feature list**: Overview of what the platform offers
- **Security notice**: Important information about invitation privacy
- **Footer**: Contact information and copyright

## Configuration

### Environment Variables

Set the following environment variables:

```bash
# Required
RESEND_API_KEY=re_your_resend_api_key_here

# Optional (with defaults)
RESEND_FROM_EMAIL=noreply@miasistentelegalia.com
RESEND_REPLY_TO_EMAIL=support@miasistentelegalia.com
```

### Getting Resend API Key

1. Sign up at [Resend](https://resend.com)
2. Go to your dashboard
3. Navigate to API Keys section
4. Create a new API key
5. Add the key to your environment variables

## Installation

1. Install the required dependency:

```bash
pip install resend==2.13.0
```

2. Add the dependency to your `requirements.txt`:

```
# Email dependencies
resend==2.13.0
```

## Usage Examples

### Python Example

```python
import requests

# Send invitation
invitation_data = {
    "friendName": "Juan Pérez",
    "inviterName": "María García",
    "inviteCode": "ABC123456",
    "shareUrl": "https://app.miasistentelegalia.com/friend-invite/ABC123456",
    "dailyLimit": 5,
    "trialDays": 3,
    "expiresAt": "22 de agosto de 2025",
    "friendEmail": "juan.perez@example.com"
}

response = requests.post(
    "http://localhost:8000/invitation/send",
    json=invitation_data
)

if response.status_code == 200:
    result = response.json()
    print(f"Invitation sent! Email ID: {result['email_id']}")
else:
    print(f"Error: {response.text}")
```

### JavaScript/Frontend Example

```javascript
const sendInvitation = async (invitationData) => {
  try {
    const response = await fetch("/invitation/send", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(invitationData),
    });

    const result = await response.json();

    if (response.ok) {
      console.log("Invitation sent successfully:", result.message);
      return result;
    } else {
      throw new Error(result.detail || "Failed to send invitation");
    }
  } catch (error) {
    console.error("Error sending invitation:", error);
    throw error;
  }
};

// Usage
const invitationData = {
  friendName: "Juan Pérez",
  inviterName: "María García",
  inviteCode: "ABC123456",
  shareUrl: "https://app.miasistentelegalia.com/friend-invite/ABC123456",
  dailyLimit: 5,
  trialDays: 3,
  expiresAt: "22 de agosto de 2025",
  friendEmail: "juan.perez@example.com",
};

sendInvitation(invitationData)
  .then((result) => {
    // Handle success
    showSuccessMessage("Invitation sent successfully!");
  })
  .catch((error) => {
    // Handle error
    showErrorMessage("Failed to send invitation: " + error.message);
  });
```

## Error Handling

The endpoint includes comprehensive error handling:

- **Missing API Key**: Returns 500 error if Resend API key is not configured
- **Invalid Email**: Returns 422 error for invalid email addresses
- **Resend API Errors**: Returns 500 error with specific error message
- **Unexpected Errors**: Returns 500 error with generic message

## Security Features

- **Email Validation**: Uses Pydantic EmailStr for email validation
- **Input Sanitization**: All inputs are validated and sanitized
- **Error Logging**: Comprehensive logging for debugging and monitoring
- **Rate Limiting**: Inherits from the main application's rate limiting
- **CORS Protection**: Inherits from the main application's CORS configuration

## Testing

Run the test script to verify the endpoint functionality:

```bash
python test_invitation_endpoint.py
```

The test script will:

1. Check the health endpoint
2. Send a test invitation
3. Test error handling with invalid data

## Monitoring

The endpoint includes:

- **Request Logging**: All requests are logged with details
- **Email Tracking**: Email IDs are returned for tracking
- **Health Monitoring**: Health check endpoint for service monitoring
- **Error Tracking**: Comprehensive error logging

## Integration with Frontend

The endpoint is designed to work seamlessly with the frontend invitation modal shown in the image. The parameters match exactly what the frontend sends:

- `friendName` → Friend's name from the modal
- `inviterName` → Current user's name
- `inviteCode` → Generated invitation code
- `shareUrl` → Frontend URL with invitation code
- `dailyLimit` → Selected daily limit from dropdown
- `trialDays` → Selected trial days from dropdown
- `expiresAt` → Calculated expiration date
- `friendEmail` → Friend's email from the modal

## Troubleshooting

### Common Issues

1. **"Email service not configured"**

   - Solution: Set the `RESEND_API_KEY` environment variable

2. **"Failed to send invitation email"**

   - Check your Resend API key is valid
   - Verify the sender email domain is verified in Resend
   - Check Resend dashboard for any account issues

3. **"Invalid email address"**
   - Ensure the email format is valid
   - Check for typos in the email address

### Debug Mode

Enable debug logging by setting the log level:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Support

For issues with the invitation endpoint:

1. Check the application logs for detailed error messages
2. Verify your Resend configuration
3. Test with the provided test script
4. Check the health endpoint for service status
