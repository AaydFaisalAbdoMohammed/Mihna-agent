from typing import Any, Dict
from ai.providers.base import BaseAIProvider

class StrictBlueprintGuard:
    def __init__(self, provider: BaseAIProvider):
        self.provider = provider

    def inspect(self, file_bytes: bytes, mime_type: str) -> Dict[str, Any]:
        prompt = """
Analyze if this file is a genuine engineering blueprint/CAD drawing.
Return JSON ONLY:
{
  "is_valid_blueprint": true/false,
  "confidence_score": 0.0 to 100.0,
  "blueprint_type": "Architectural/Structural/MEP/Invalid",
  "rejection_reason": "String if invalid"
}
"""
        result = self.provider.analyze_vision(file_bytes, mime_type, prompt)
        score = float(result.get("confidence_score", 0.0))
        if score < 80.0 or not result.get("is_valid_blueprint"):
            result["is_valid_blueprint"] = False
            result.setdefault("rejection_reason", "Low confidence score or non-engineering drawing.")
        return result
