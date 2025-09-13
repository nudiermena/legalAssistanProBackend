# AI Model Fallback System

## Overview

The AI Model Fallback System automatically handles API errors, rate limiting, and service outages by seamlessly switching between multiple AI providers: **Mistral** and **Groq**. This ensures your legal assistant remains operational even when individual AI services experience issues.

## 🚀 Features

- **Automatic Fallback**: Seamlessly switches between AI models on errors
- **Smart Error Detection**: Identifies rate limits, timeouts, and service issues
- **Cost Optimization**: Automatically selects cost-effective models
- **Performance Monitoring**: Tracks response times and success rates
- **Health Checks**: Real-time monitoring of all AI model statuses
- **Configurable**: Easy to customize fallback behavior and priorities

## 🔧 Setup

### 1. Environment Variables

Add these API keys to your `.env` file:

```bash
# Primary AI Provider
MISTRAL_API_KEY=your_mistral_api_key_here

# Fallback AI Provider
GROQ_API_KEY=your_groq_api_key_here
```

### 2. API Keys Setup

#### Mistral AI

- Sign up at [Mistral AI](https://mistral.ai/)
- Get your API key from the dashboard
- Free tier: 20 requests/minute, 1000 requests/hour

#### Groq

- Sign up at [Groq](https://groq.com/)
- Get your API key from the dashboard
- Free tier: 100 requests/minute, 10,000 requests/hour

## 📊 How It Works

### Fallback Priority Order

1. **Mistral** (Primary - Best quality)
2. **Groq** (Fallback - Good quality, higher limits)

### Error Handling

- **Rate Limit Errors (429)**: Automatically switches to next available model
- **Temporary Errors**: Retries with exponential backoff
- **Permanent Errors**: Marks model as unavailable until manually reset
- **Service Capacity Exceeded**: Immediate fallback to next model

### Smart Model Selection

The system automatically selects the best available model based on:

- Current availability status
- Cost per request
- Performance history
- Error frequency

## 🎯 Usage

### Basic Usage

```python
from config.ai_models import legal_research_model

# The system automatically handles fallbacks
response = await legal_research_model.ainvoke(
    "What are the basic principles of Colombian constitutional law?"
)
```

### Check Model Status

```python
from config.ai_models import health_check, get_model_status

# Get overall health
health = health_check()
print(f"Status: {health['status']}")
print(f"Available Models: {health['available_models']}")

# Get detailed status
status = get_model_status()
print(f"Model Status: {status['fallback_manager']['model_status']}")
```

### Manual Model Selection

```python
from config.ai_models import fallback_manager

# Check available models
available = fallback_manager.get_available_models()
print(f"Available: {available}")

# Get best available model
best = fallback_manager.get_best_available_model()
print(f"Best: {best}")
```

## 🔍 Monitoring & Health Checks

### Health Check Endpoint

```bash
GET /dashboard/ai-health
```

Response:

```json
{
  "status": "success",
  "data": {
    "health": {
      "status": "healthy",
      "available_models": ["mistral", "groq"],
      "best_available_model": "mistral",
      "total_models": 2,
      "available_count": 2
    },
    "model_status": {
      "fallback_manager": {
        "available_models": ["mistral", "groq"],
        "best_available": "mistral",
        "model_status": {
          "mistral": "available",
          "groq": "available"
        }
      }
    }
  }
}
```

### Testing the System

Run the test script to verify everything works:

```bash
python test_ai_fallback_system.py
```

## ⚙️ Configuration

### Customize Fallback Behavior

Edit `config/ai_fallback_config.py`:

```python
# Adjust error thresholds
FALLBACK_CONFIG = {
    "error_threshold": 3,      # Switch after 3 errors
    "error_window": 300,       # Within 5 minutes
    "retry_delay": 60,         # Wait 1 minute before retry
    "max_retries": 3           # Maximum retries per request
}

# Enable cost optimization
COST_OPTIMIZATION = {
    "enable_cost_optimization": True,
    "prefer_cheaper_models": True,
    "max_cost_per_request": 0.10  # USD
}
```

### Model-Specific Settings

```python
MODEL_CONFIGS = {
    "mistral": {
        "model_id": "mistral-large-latest",
        "max_tokens": 4096,
        "temperature": 0.7,
        "timeout": 30,
        "priority": 1
    },
    "groq": {
        "model_id": "llama3-70b-8192",
        "max_tokens": 8192,
        "temperature": 0.7,
        "timeout": 30,
        "priority": 2
    }
}
```

## 🚨 Troubleshooting

### Common Issues

#### 1. "No AI models available"

- Check that at least one API key is set
- Verify API keys are valid
- Check internet connectivity

#### 2. "Model temporarily unavailable"

- This is normal after multiple errors
- Models automatically reactivate after 5 minutes
- Check the health endpoint for status

#### 3. Rate limiting persists

- The system should automatically switch models
- Check if all models are rate limited
- Consider upgrading API plans

### Debug Commands

```python
# Check environment variables
import os
print(f"MISTRAL_API_KEY: {'SET' if os.getenv('MISTRAL_API_KEY') else 'NOT SET'}")
print(f"GROQ_API_KEY: {'SET' if os.getenv('GROQ_API_KEY') else 'NOT SET'}")

# Check model status
from config.ai_models import fallback_manager
print(f"Model Status: {fallback_manager.model_status}")
print(f"Available Models: {fallback_manager.get_available_models()}")
```

## 💰 Cost Optimization

### Cost per 1K Tokens

- **Mistral**: $0.007 (highest quality, highest cost)
- **Groq**: $0.0008 (good quality, medium cost)

### Automatic Cost Optimization

The system automatically:

- Prefers cheaper models when quality requirements allow
- Switches to expensive models only when needed
- Tracks costs per request
- Provides cost estimates before execution

## 🔄 Migration from Old System

### Before (Single Mistral Model)

```python
# Old way - single model
from config.ai_models import legal_research_model
response = await legal_research_model.ainvoke(prompt)
```

### After (Fallback System)

```python
# New way - automatic fallback
from config.ai_models import legal_research_model
response = await legal_research_model.ainvoke(prompt)
# Automatically handles fallbacks - no code changes needed!
```

## 📈 Performance Metrics

The system tracks:

- Response times per model
- Success/failure rates
- Cost per request
- Error types and frequencies
- Model switching patterns

## 🛡️ Security

- API keys are stored securely in environment variables
- No sensitive data is logged
- Error messages are sanitized
- Rate limiting respects provider limits

## 🆘 Support

If you encounter issues:

1. **Check the health endpoint**: `/dashboard/ai-health`
2. **Run the test script**: `python test_ai_fallback_system.py`
3. **Check logs** for detailed error information
4. **Verify API keys** are set correctly
5. **Check provider status pages** for service outages

## 🔮 Future Enhancements

Planned features:

- **Load Balancing**: Distribute requests across multiple models
- **Quality Scoring**: Track response quality per model
- **Predictive Switching**: Anticipate and prevent failures
- **Custom Model Integration**: Add support for other AI providers
- **Advanced Analytics**: Detailed performance dashboards

---

**Note**: The fallback system is designed to be completely transparent to your existing code. All your current AI model calls will automatically benefit from the new fallback capabilities without any modifications needed.
