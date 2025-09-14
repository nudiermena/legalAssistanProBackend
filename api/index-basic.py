# Basic Python API without external dependencies
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.handle_request('GET')
    
    def do_POST(self):
        self.handle_request('POST')
    
    def do_OPTIONS(self):
        self.handle_request('OPTIONS')
    
    def handle_request(self, method):
        """Handle all HTTP requests"""
        # Parse the URL
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        # CORS headers
        cors_headers = {
            'Access-Control-Allow-Origin': 'https://miasistentelegalia.com',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Credentials': 'true',
            'Content-Type': 'application/json'
        }
        
        # Add CORS headers
        for header, value in cors_headers.items():
            self.send_header(header, value)
        
        # Handle OPTIONS preflight requests
        if method == 'OPTIONS':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({'message': 'CORS preflight successful'}).encode())
            return
        
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
                # Read request body
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    body = self.rfile.read(content_length).decode('utf-8')
                    request_data = json.loads(body)
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
        
        # Send response
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

# Vercel handler function
def handler(request):
    return Handler()
