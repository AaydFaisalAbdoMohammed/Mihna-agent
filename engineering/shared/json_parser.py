import json
import re
from typing import Any, Dict

class SafeJSONParser:
    @staticmethod
    def extract(text: str) -> Dict[str, Any]:
        if not text:
            return {}
        text = text.strip()

        try:
            return json.loads(text)
        except Exception:
            pass

        fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
        if fenced:
            try:
                return json.loads(fenced.group(1))
            except Exception:
                pass

        decoder = json.JSONDecoder()
        for idx, char in enumerate(text):
            if char == '{':
                try:
                    obj, _ = decoder.raw_decode(text[idx:])
                    if isinstance(obj, dict):
                        return obj
                except Exception:
                    continue
        return {}
