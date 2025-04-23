from flask import Flask, request, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
import os
from app import create_app

app = create_app()
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

async def fetch(request):
    """Handle the incoming request."""
    # Convert Cloudflare request to WSGI environment
    environ = {
        'REQUEST_METHOD': request.method,
        'SCRIPT_NAME': '',
        'PATH_INFO': request.path,
        'QUERY_STRING': request.query_string.decode('utf-8'),
        'CONTENT_TYPE': request.headers.get('Content-Type', ''),
        'CONTENT_LENGTH': request.headers.get('Content-Length', ''),
        'SERVER_NAME': request.host,
        'SERVER_PORT': '443',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'https',
        'wsgi.input': request.body,
        'wsgi.errors': None,
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
    }

    # Add headers
    for key, value in request.headers.items():
        environ[f'HTTP_{key.upper().replace("-", "_")}'] = value

    # Call the Flask app
    response = app(environ, lambda status, headers, body: None)
    
    # Convert response to Cloudflare response
    return Response(
        response.body,
        status=response.status_code,
        headers=dict(response.headers)
    ) 