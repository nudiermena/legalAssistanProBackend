# Legal AI Assistant API

A comprehensive API for legal assistance, providing various tools for contract review, legal research, regulatory analysis, and more. Each endpoint is specialized for specific legal tasks and includes appropriate disclaimers and compliance checks.

## Features

- Contract Review: Analyze contracts for key terms, risks, and compliance
- Legal Research: Conduct comprehensive legal research on specific issues
- Regulatory Analysis: Analyze regulatory changes and their impact
- Legal Chat: AI-powered legal assistance for general queries
- Patent Search: Conduct prior art searches for patent applications
- Document Drafting: Generate customized legal documents
- Whistleblower Analysis: Analyze whistleblower reports
- Demand Letter Generation: Create legally compliant demand letters
- Legal Diagnosis: Provide personalized legal guidance

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/legal-ai-assistant.git
cd legal-ai-assistant
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your configuration
```

## Usage

1. Start the server:

```bash
uvicorn main:app --reload
```

2. Access the API documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

- `GET /`: Root endpoint with API information
- `POST /api/contract-review`: Contract analysis
- `POST /api/legal-research`: Legal research
- `POST /api/regulatory-analysis`: Regulatory analysis
- `POST /api/legal-chat`: Legal assistance chat
- `POST /api/patent-search`: Patent prior art search
- `POST /api/document-drafting`: Legal document generation
- `POST /api/whistleblower-analysis`: Whistleblower report analysis
- `POST /api/demand-letter`: Demand letter generation
- `POST /api/legal-diagnosis`: Legal issue diagnosis

## Development

### Project Structure

```
legal-ai-assistant/
├── agents/                 # AI agents for different tasks
├── endpoints/             # API endpoints
├── models/               # Data models and schemas
├── utils/               # Utility functions
├── main.py              # FastAPI application
├── requirements.txt     # Project dependencies
└── README.md           # Project documentation
```

### Adding New Features

1. Create a new agent in the `agents/` directory
2. Define request/response models in `models/`
3. Create an endpoint in `endpoints/`
4. Update the main application in `main.py`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This API is for informational purposes only and does not constitute legal advice. Users should consult with qualified legal professionals for specific legal advice.
