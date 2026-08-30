import logging
import os
from typing import Any, Dict, Optional
import google.generativeai as genai
from ai.providers.base import BaseAIProvider
from engineering.shared.json_parser import SafeJSONParser
from engineering.shared.errors import AIProviderError

logger = logging.getLogger(__name__)

class GeminiProvider(BaseAIProvider):
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise AIProviderError("GEMINI_API_KEY is missing from configuration.")
        genai.configure(api_key=self.api_key)
        self.model_name = model_name

    def generate_json(self, prompt: str, system_instruction: Optional[str] = None) -> Dict[str, Any]:
        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_instruction,
                generation_config={"temperature": 0.1, "response_mime_type": "application/json"}
            )
            response = model.generate_content(prompt)
            parsed = SafeJSONParser.extract(getattr(response, "text", ""))
            if not parsed:
                raise AIProviderError("Failed to decode structured JSON from Gemini response.")
            return parsed
        except Exception as e:
            logger.exception("Gemini Provider execution failed")
            raise AIProviderError(f"Gemini service error: {str(e)}")

    def analyze_vision(self, image_bytes: bytes, mime_type: str, prompt: str) -> Dict[str, Any]:
        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={"temperature": 0.0, "response_mime_type": "application/json"}
            )
            response = model.generate_content([prompt, {"mime_type": mime_type, "data": image_bytes}])
            return SafeJSONParser.extract(getattr(response, "text", ""))
        except Exception as e:
            logger.exception("Gemini Vision execution failed")
            raise AIProviderError(f"Gemini Vision error: {str(e)}")
