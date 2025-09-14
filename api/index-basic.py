# Basic Python API without external dependencies
import json
from datetime import datetime

def handler(request):
    """Basic request handler for Vercel"""
    
    # Get request method and path
    method = request.get('method', 'GET')
    path = request.get('path', '/')
    headers = request.get('headers', {})
    body = request.get('body', '')
    
    # CORS headers
    cors_headers = {
        'Access-Control-Allow-Origin': 'https://miasistentelegalia.com',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': '*',
        'Access-Control-Allow-Credentials': 'true',
        'Content-Type': 'application/json'
    }
    
    # Handle OPTIONS preflight requests
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({'message': 'CORS preflight successful'})
        }
    
    # Handle different endpoints
    if path == '/':
        response = {
            'message': 'Welcome to Legal AI Assistant API - Basic Version',
            'cors_enabled': True,
            'frontend_domain': 'https://miasistentelegalia.com',
            'status': 'working',
            'timestamp': datetime.now().isoformat()
        }
    
    elif path == '/health':
        response = {
            'status': 'healthy',
            'version': 'basic',
            'cors_enabled': True,
            'timestamp': datetime.now().isoformat()
        }
    
    elif path == '/test':
        response = {
            'message': 'API is working',
            'timestamp': datetime.now().isoformat(),
            'cors': 'enabled',
            'status': 'success'
        }
    
    elif path == '/legal-chat/consulta' and method == 'POST':
        try:
            # Parse request body
            if body:
                request_data = json.loads(body) if isinstance(body, str) else body
                user_message = request_data.get('message', 'No message provided')
                user_id = request_data.get('user_id', 'unknown')
            else:
                user_message = 'No message provided'
                user_id = 'unknown'
            
            response = {
                'success': True,
                'response': f'Received your message: {user_message}',
                'message': 'Legal chat consultation completed successfully',
                'timestamp': datetime.now().isoformat(),
                'cors_status': 'working',
                'user_id': user_id
            }
        except Exception as e:
            response = {
                'success': False,
                'error': f'Error processing request: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    else:
        response = {
            'error': 'Endpoint not found',
            'path': path,
            'method': method,
            'timestamp': datetime.now().isoformat()
        }
    
    return {
        'statusCode': 200,
        'headers': cors_headers,
        'body': json.dumps(response)
    }

# For Vercel Python runtime
def main(request):
    return handler(request)
