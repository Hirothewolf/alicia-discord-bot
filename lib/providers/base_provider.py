from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class BaseProvider(ABC):
    @abstractmethod
    async def generate_response(self, messages: List[Dict[str, Any]], config: Dict[str, Any]) -> str:
        """Generate a response using the provider's API"""
        pass

    @abstractmethod
    async def validate_api_key(self, api_key: str) -> bool:
        """Validate if the API key is valid for this provider"""
        pass

    @abstractmethod
    async def get_available_models(self, api_key: str) -> List[Dict[str, Any]]:
        """Get available models from the provider's API"""
        pass

    @abstractmethod
    def get_static_models(self) -> List[Dict[str, Any]]:
        """Get a static list of models as fallback"""
        pass

    @abstractmethod
    def supports_safety_settings(self) -> bool:
        """Check if provider supports safety settings"""
        pass

    @abstractmethod
    def supports_rich_presence(self) -> bool:
        """Check if provider supports rich presence features"""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Provider description"""
        pass