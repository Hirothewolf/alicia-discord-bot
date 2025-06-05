import aiohttp
from typing import Dict, Any, Optional
from .base_provider import BaseProvider

class TogetherProvider(BaseProvider):
    def __init__(self):
        self._name = "Together AI"
        self._description = "Together AI's collection of open and closed source models"
        self._api_base = "https://api.together.xyz/v1"

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    async def generate_response(self, prompt: str, config: Dict[str, Any]) -> str:
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json"
        }

        data = {
            "model": config.get("model_name", "mistralai/Mixtral-8x7B-Instruct-v0.1"),
            "prompt": prompt,
            "max_tokens": config.get("max_tokens", 2048),
            "temperature": config.get("temperature", 0.7),
            "top_p": config.get("top_p", 0.95),
            "top_k": config.get("top_k", 40),
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self._api_base}/completions",
                headers=headers,
                json=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["text"]
                else:
                    error_data = await response.json()
                    raise Exception(f"Error from Together AI: {error_data.get('error', 'Unknown error')}")

    async def validate_api_key(self, api_key: str) -> bool:
        headers = {"Authorization": f"Bearer {api_key}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self._api_base}/models", headers=headers) as response:
                return response.status == 200

    def get_available_models(self) -> Dict[str, Any]:
        return {
            "mistralai/Mixtral-8x7B-Instruct-v0.1": {
                "name": "Mixtral 8x7B Instruct",
                "description": "Mixtral's 8x7B instruction-tuned model",
                "context_length": 32768,
            },
            "meta-llama/Llama-2-70b-chat": {
                "name": "Llama 2 70B Chat",
                "description": "Meta's Llama 2 70B chat model",
                "context_length": 4096,
            },
            "NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO": {
                "name": "Nous Hermes 2 Mixtral",
                "description": "Nous Research's Hermes 2 model based on Mixtral",
                "context_length": 32768,
            }
        }