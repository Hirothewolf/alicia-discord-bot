import aiohttp
import json
from typing import Dict, Any, Optional, List
from .base_provider import BaseProvider

class TogetherProvider(BaseProvider):
    def __init__(self):
        self._name = "Together AI"
        self._description = "Together AI's collection of open and closed source models via OpenAI-compatible API"
        self._api_base = "https://api.together.xyz/v1"

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    async def generate_response(self, messages: List[Dict[str, Any]], config: Dict[str, Any]) -> str:
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json"
        }

        # Convert messages to OpenAI format
        openai_messages = []
        for msg in messages:
            if msg["role"] == "model":
                openai_messages.append({"role": "assistant", "content": msg["parts"][0]})
            else:
                openai_messages.append({"role": msg["role"], "content": msg["parts"][0]})

        data = {
            "model": config.get("model_name", "mistralai/Mixtral-8x7B-Instruct-v0.1"),
            "messages": openai_messages,
            "max_tokens": config.get("max_output_tokens", 2048),
            "temperature": config.get("temperature", 0.7),
            "top_p": config.get("top_p", 0.95),
            "stream": False
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self._api_base}/chat/completions",
                headers=headers,
                json=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    error_data = await response.json()
                    raise Exception(f"Error from Together AI: {error_data.get('error', {}).get('message', 'Unknown error')}")

    async def validate_api_key(self, api_key: str) -> bool:
        headers = {"Authorization": f"Bearer {api_key}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self._api_base}/models", headers=headers) as response:
                return response.status == 200

    async def get_available_models(self, api_key: str) -> List[Dict[str, Any]]:
        headers = {"Authorization": f"Bearer {api_key}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self._api_base}/models", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    models = []
                    for model in data.get("data", []):
                        models.append({
                            'name': model['id'],
                            'display_name': model['id'].replace('/', ' / '),
                            'description': f"Together AI model: {model['id']}",
                            'context_length': model.get('context_length', 'Unknown'),
                            'pricing': model.get('pricing', {}),
                            'type': model.get('type', 'chat')
                        })
                    return models
                else:
                    return []

    def get_static_models(self) -> List[Dict[str, Any]]:
        return [
            {
                'name': 'mistralai/Mixtral-8x7B-Instruct-v0.1',
                'display_name': 'Mixtral 8x7B Instruct',
                'description': 'Mixtral\'s 8x7B instruction-tuned model',
                'context_length': 32768,
                'type': 'chat'
            },
            {
                'name': 'meta-llama/Llama-2-70b-chat-hf',
                'display_name': 'Llama 2 70B Chat',
                'description': 'Meta\'s Llama 2 70B chat model',
                'context_length': 4096,
                'type': 'chat'
            },
            {
                'name': 'NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO',
                'display_name': 'Nous Hermes 2 Mixtral',
                'description': 'Nous Research\'s Hermes 2 model based on Mixtral',
                'context_length': 32768,
                'type': 'chat'
            },
            {
                'name': 'teknium/OpenHermes-2.5-Mistral-7B',
                'display_name': 'OpenHermes 2.5 Mistral 7B',
                'description': 'OpenHermes 2.5 based on Mistral 7B',
                'context_length': 8192,
                'type': 'chat'
            },
            {
                'name': 'togethercomputer/RedPajama-INCITE-Chat-3B-v1',
                'display_name': 'RedPajama INCITE Chat 3B',
                'description': 'RedPajama INCITE Chat model',
                'context_length': 2048,
                'type': 'chat'
            }
        ]

    def supports_safety_settings(self) -> bool:
        return False

    def supports_rich_presence(self) -> bool:
        return False