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

    async def get_available_models(self, provider_name: str, api_key: str) -> List[Dict[str, Any]]:
        provider = self.get_provider(provider_name)
        try:
            return await provider.get_available_models(api_key)
        except Exception:
            return provider.get_static_models()

    def get_static_models(self, provider_name: str) -> List[Dict[str, Any]]:
        provider = self.get_provider(provider_name)
        return provider.get_static_models()

    async def generate_response(self, provider_name: str, messages: List[Dict[str, Any]], config: Dict[str, Any]) -> str:
        provider = self.get_provider(provider_name)
        return await provider.generate_response(messages, config)

    def supports_safety_settings(self, provider_name: str) -> bool:
        provider = self.get_provider(provider_name)
        return provider.supports_safety_settings()

    def supports_rich_presence(self, provider_name: str) -> bool:
        provider = self.get_provider(provider_name)
        return provider.supports_rich_presence()