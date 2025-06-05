import google.generativeai as genai
from typing import Dict, Any, Optional
import aiohttp
from .base_provider import BaseProvider

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

    async def generate_response(self, prompt: str, config: Dict[str, Any]) -> str:
        genai.configure(api_key=config["api_key"])
        
        model = genai.GenerativeModel(
            model_name=config.get("model_name", "gemini-1.5-pro"),
            generation_config={
                "temperature": config.get("temperature", 0.9),
                "top_p": config.get("top_p", 0.95),
                "top_k": config.get("top_k", 40),
                "max_output_tokens": config.get("max_output_tokens", 2048),
            }
        )

        response = model.generate_content(prompt)
        return response.text

    async def validate_api_key(self, api_key: str) -> bool:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return response.status == 200

    def get_available_models(self) -> Dict[str, Any]:
        return {
            "gemini-1.5-pro": {
                "name": "Gemini 1.5 Pro",
                "description": "Latest version of Gemini Pro",
                "context_length": 128000,
            },
            "gemini-1.5-pro-latest": {
                "name": "Gemini 1.5 Pro Latest",
                "description": "Latest experimental version",
                "context_length": 128000,
            }
        }