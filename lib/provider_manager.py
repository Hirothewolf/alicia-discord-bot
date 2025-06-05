from typing import Dict, Any, Optional, List
from lib.providers import BaseProvider, GeminiProvider, TogetherProvider

class ProviderManager:
    def __init__(self):
        self.providers: Dict[str, BaseProvider] = {
            "gemini": GeminiProvider(),
            "together": TogetherProvider()
        }
        self.default_provider = "gemini"

    def get_provider(self, provider_name: Optional[str] = None) -> BaseProvider:
        if provider_name is None:
            provider_name = self.default_provider
        return self.providers.get(provider_name, self.providers[self.default_provider])

    def get_available_providers(self) -> List[Dict[str, str]]:
        return [
            {"id": provider_id, "name": provider.name, "description": provider.description}
            for provider_id, provider in self.providers.items()
        ]

    async def validate_api_key(self, provider_name: str, api_key: str) -> bool:
        provider = self.get_provider(provider_name)
        return await provider.validate_api_key(api_key)

    def get_available_models(self, provider_name: str) -> Dict[str, Any]:
        provider = self.get_provider(provider_name)
        return provider.get_available_models()

    async def generate_response(self, provider_name: str, prompt: str, config: Dict[str, Any]) -> str:
        provider = self.get_provider(provider_name)
        return await provider.generate_response(prompt, config)