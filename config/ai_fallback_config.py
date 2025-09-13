"""
AI Model Fallback Configuration
This module contains configuration settings for the AI model fallback system
"""

import os
from typing import Dict, List, Optional

# Fallback configuration
FALLBACK_CONFIG = {
    "primary_model": "mistral",
    "fallback_order": ["mistral", "groq"],
    "error_threshold": 3,  # Number of errors before switching
    "error_window": 300,   # 5 minutes window for error counting
    "retry_delay": 60,     # 1 minute delay before retrying failed models
    "max_retries": 3,      # Maximum number of retries per request
}

# Model-specific configurations
MODEL_CONFIGS = {
    "mistral": {
        "model_id": "mistral-large-latest",
        "max_tokens": 4096,
        "temperature": 0.7,
        "timeout": 30,
        "priority": 1,
        "cost_per_1k_tokens": 0.007,  # USD per 1K tokens
    },
    "groq": {
        "model_id": "llama3-70b-8192",
        "max_tokens": 8192,
        "temperature": 0.7,
        "timeout": 30,
        "priority": 2,
        "cost_per_1k_tokens": 0.0008,  # USD per 1K tokens
    }
}

# Rate limiting configuration
RATE_LIMIT_CONFIG = {
    "mistral": {
        "requests_per_minute": 20,
        "requests_per_hour": 1000,
        "tokens_per_minute": 100000,
    },
    "groq": {
        "requests_per_minute": 100,
        "requests_per_hour": 10000,
        "tokens_per_minute": 1000000,
    }
}

# Error handling configuration
ERROR_HANDLING_CONFIG = {
    "rate_limit_errors": [
        "429",
        "rate limit",
        "capacity exceeded", 
        "quota exceeded",
        "too many requests",
        "service tier capacity exceeded"
    ],
    "temporary_errors": [
        "timeout",
        "connection error",
        "server error",
        "temporary failure"
    ],
    "permanent_errors": [
        "authentication failed",
        "invalid api key",
        "model not found"
    ]
}

# Cost optimization settings
COST_OPTIMIZATION = {
    "enable_cost_optimization": True,
    "prefer_cheaper_models": True,
    "max_cost_per_request": 0.10,  # USD
    "cost_threshold_for_switching": 0.05,  # USD
}

# Performance monitoring
PERFORMANCE_MONITORING = {
    "enable_monitoring": True,
    "log_response_times": True,
    "log_token_usage": True,
    "log_costs": True,
    "performance_threshold": 10.0,  # seconds
}

def get_model_config(model_name: str) -> Dict:
    """Get configuration for a specific model"""
    return MODEL_CONFIGS.get(model_name, {})

def get_fallback_config() -> Dict:
    """Get the fallback configuration"""
    return FALLBACK_CONFIG.copy()

def get_rate_limit_config(model_name: str) -> Dict:
    """Get rate limiting configuration for a specific model"""
    return RATE_LIMIT_CONFIG.get(model_name, {})

def get_error_handling_config() -> Dict:
    """Get error handling configuration"""
    return ERROR_HANDLING_CONFIG.copy()

def get_cost_optimization_config() -> Dict:
    """Get cost optimization configuration"""
    return COST_OPTIMIZATION.copy()

def get_performance_monitoring_config() -> Dict:
    """Get performance monitoring configuration"""
    return PERFORMANCE_MONITORING.copy()

def is_rate_limit_error(error_message: str) -> bool:
    """Check if an error message indicates a rate limit error"""
    error_lower = error_message.lower()
    rate_limit_indicators = ERROR_HANDLING_CONFIG["rate_limit_errors"]
    return any(indicator in error_lower for indicator in rate_limit_indicators)

def is_temporary_error(error_message: str) -> bool:
    """Check if an error message indicates a temporary error"""
    error_lower = error_message.lower()
    temporary_indicators = ERROR_HANDLING_CONFIG["temporary_errors"]
    return any(indicator in error_lower for indicator in temporary_indicators)

def is_permanent_error(error_message: str) -> bool:
    """Check if an error message indicates a permanent error"""
    error_lower = error_message.lower()
    permanent_indicators = ERROR_HANDLING_CONFIG["permanent_errors"]
    return any(indicator in error_lower for indicator in permanent_indicators)

def get_optimal_model_for_cost(max_cost: float = None) -> Optional[str]:
    """Get the most cost-effective model within budget"""
    if not COST_OPTIMIZATION["enable_cost_optimization"]:
        return FALLBACK_CONFIG["primary_model"]
    
    if max_cost is None:
        max_cost = COST_OPTIMIZATION["max_cost_per_request"]
    
    # Sort models by cost (cheapest first)
    sorted_models = sorted(
        MODEL_CONFIGS.items(),
        key=lambda x: x[1]["cost_per_1k_tokens"]
    )
    
    for model_name, config in sorted_models:
        if config["cost_per_1k_tokens"] <= max_cost / 1000:  # Convert to per-token cost
            return model_name
    
    return None

def get_model_priority_score(model_name: str) -> float:
    """Calculate a priority score for model selection"""
    if model_name not in MODEL_CONFIGS:
        return 0.0
    
    config = MODEL_CONFIGS[model_name]
    
    # Base priority (lower is better)
    base_priority = config["priority"]
    
    # Cost factor (cheaper is better)
    cost_factor = 1.0 / (config["cost_per_1k_tokens"] + 0.0001)
    
    # Performance factor (faster timeout is better)
    performance_factor = 1.0 / (config["timeout"] + 0.1)
    
    # Calculate final score (higher is better)
    score = (cost_factor * 0.4) + (performance_factor * 0.3) + (1.0 / base_priority * 0.3)
    
    return score

def get_optimal_model_order() -> List[str]:
    """Get models ordered by optimal selection priority"""
    models_with_scores = [
        (model_name, get_model_priority_score(model_name))
        for model_name in MODEL_CONFIGS.keys()
    ]
    
    # Sort by score (highest first)
    sorted_models = sorted(models_with_scores, key=lambda x: x[1], reverse=True)
    
    return [model_name for model_name, score in sorted_models]
