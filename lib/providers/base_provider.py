from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseProvider(ABC):
    @abstractmethod
    async def generate_response(self, prompt: str, config: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    async def validate_api_key(self, api_key: str) -> bool:
        pass

    @abstractmethod
    def get_available_models(self) -> Dict[str, Any]:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass