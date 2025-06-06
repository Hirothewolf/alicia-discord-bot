import google.generativeai as genai
from typing import Dict, Any, Optional, List
import aiohttp
import json
from datetime import datetime, timedelta
import aiofiles
import os
from .base_provider import BaseProvider

CACHE_FILE = 'gemini_models_cache.json'

class GeminiProvider(BaseProvider):
    def __init__(self):
        self._name = "Google Gemini"
        self._description = "Google's Gemini AI models for natural language processing"

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    async def generate_response(self, messages: List[Dict[str, Any]], config: Dict[str, Any]) -> str:
        genai.configure(api_key=config["api_key"])
        
        generation_config = {
            "temperature": config.get("temperature", 1.0),
            "top_p": config.get("top_p", 0.95),
            "top_k": config.get("top_k", 40),
            "max_output_tokens": config.get("max_output_tokens", 2048),
        }
        
        safety_settings = []
        if config.get("safety_settings"):
            safety_settings = [
                {"category": category, "threshold": level}
                for category, level in config["safety_settings"].items()
            ]

        model = genai.GenerativeModel(
            model_name=config.get("model_name", "gemini-1.5-pro-latest"),
            generation_config=generation_config,
            safety_settings=safety_settings if safety_settings else None
        )

        # Convert messages to Gemini format
        gemini_messages = []
        for msg in messages:
            if msg["role"] == "assistant":
                gemini_messages.append({"role": "model", "parts": msg["parts"]})
            else:
                gemini_messages.append(msg)

        chat = model.start_chat(history=gemini_messages[:-1] if len(gemini_messages) > 1 else [])
        
        # Get the last message content
        last_message = gemini_messages[-1]["parts"][0] if gemini_messages else ""
        
        response = chat.send_message(last_message)
        return response.text

    async def validate_api_key(self, api_key: str) -> bool:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return response.status == 200

    async def load_cache(self) -> Optional[List[Dict[str, Any]]]:
        if os.path.exists(CACHE_FILE):
            async with aiofiles.open(CACHE_FILE, 'r') as f:
                cache = json.loads(await f.read())
            if datetime.now() - datetime.fromisoformat(cache['timestamp']) < timedelta(weeks=1):
                return cache['models']
        return None

    async def save_cache(self, models: List[Dict[str, Any]]) -> None:
        cache = {
            'timestamp': datetime.now().isoformat(),
            'models': models
        }
        async with aiofiles.open(CACHE_FILE, 'w') as f:
            await f.write(json.dumps(cache, indent=4))

    async def get_available_models(self, api_key: str) -> List[Dict[str, Any]]:
        cached_models = await self.load_cache()
        if cached_models:
            return cached_models
        
        genai.configure(api_key=api_key)
        
        models = []
        try:
            for model in genai.list_models():
                if model.name.startswith(("models/gemini-", "models/gemma")):
                    model_data = {
                        'name': model.name.split('models/')[1],
                        'base_model_id': getattr(model, 'base_model_id', 'N/A'),
                        'version': getattr(model, 'version', 'N/A'),
                        'display_name': model.display_name,
                        'description': model.description,
                        'input_token_limit': getattr(model, 'input_token_limit', 'N/A'),
                        'output_token_limit': getattr(model, 'output_token_limit', 'N/A'),
                        'supported_generation_methods': model.supported_generation_methods,
                        'temperature': getattr(model, 'temperature', 'N/A'),
                        'max_temperature': getattr(model, 'max_temperature', 'N/A'),
                        'top_p': getattr(model, 'top_p', 'N/A'),
                        'top_k': getattr(model, 'top_k', 'N/A')
                    }
                    models.append(model_data)
            
            await self.save_cache(models)
            return models
        except Exception as e:
            print(f"Error fetching Gemini models: {e}")
            return self.get_static_models()

    def get_static_models(self) -> List[Dict[str, Any]]:
        return [
            {
                'name': 'gemini-1.5-pro-latest',
                'display_name': 'Gemini 1.5 Pro Latest',
                'description': 'Latest version of Gemini 1.5 Pro',
                'input_token_limit': 2097152,
                'output_token_limit': 8192,
                'supported_generation_methods': ['generateContent', 'countTokens']
            },
            {
                'name': 'gemini-1.5-flash-latest',
                'display_name': 'Gemini 1.5 Flash Latest',
                'description': 'Latest version of Gemini 1.5 Flash',
                'input_token_limit': 1048576,
                'output_token_limit': 8192,
                'supported_generation_methods': ['generateContent', 'countTokens']
            },
            {
                'name': 'gemini-1.0-pro',
                'display_name': 'Gemini 1.0 Pro',
                'description': 'Gemini 1.0 Pro model',
                'input_token_limit': 30720,
                'output_token_limit': 2048,
                'supported_generation_methods': ['generateContent', 'countTokens']
            }
        ]

    def supports_safety_settings(self) -> bool:
        return True

    def supports_rich_presence(self) -> bool:
        return True