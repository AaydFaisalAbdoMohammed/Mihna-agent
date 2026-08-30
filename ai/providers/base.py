from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseAIProvider(ABC):
    """عقد مجرد لجميع المزودات لتسهيل استبدال Gemini بأي نموذج آخر مستقبلاً."""

    @abstractmethod
    def generate_json(self, prompt: str, system_instruction: Optional[str] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def analyze_vision(self, image_bytes: bytes, mime_type: str, prompt: str) -> Dict[str, Any]:
        pass
