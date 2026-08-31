import logging
import os
from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel

# استخدام الحزمة الرسمية الجديدة من Google GenAI
from google import genai
from google.genai import types

from ai.providers.base import BaseAIProvider
from engineering.shared.errors import AIProviderError
from engineering.shared.json_parser import SafeJSONParser

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class GeminiProvider(BaseAIProvider):
    """
    تطبيق المزود الرئيسي لـ Google Gemini المعتمد على أحدث حزمة google-genai.
    يدعم المعالجة غير المتزامنة (Async)، الـ Structured Outputs المعتمدة على Pydantic،
    والتحليل البصري الهندسية عالي الدقة.
    """

    def __init__(
        self, 
        api_key: Optional[str] = None, 
        model_name: str = "gemini-2.5-flash"
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise AIProviderError("GEMINI_API_KEY غير موجود في إعدادات البيئة.")
        
        # تهيئة العميل المتزامن وغير المتزامن من العميل الرئيسي
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = model_name

    async def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        response_schema: Optional[Type[T]] = None,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """
        توليد استجابة JSON مهيكلة بشكل آمن وغير متزامن.
        """
        try:
            # إعداد التكوين المتقدم للنموذج
            config = types.GenerateContentConfig(
                temperature=temperature,
                response_mime_type="application/json",
                system_instruction=system_instruction,
                response_schema=response_schema if response_schema else None,
            )

            # استدعاء Async عبر العميل الجديد
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config,
            )

            response_text = getattr(response, "text", "")
            if not response_text:
                raise AIProviderError("تم استلام استجابة فارغة من نموذج Gemini.")

            # تحليل الـ JSON بشكل آمن
            parsed = SafeJSONParser.extract(response_text)
            if not parsed:
                raise AIProviderError("فشل في استخراج صيغة JSON صحيحة من استجابة Gemini.")

            return parsed

        except AIProviderError:
            raise
        except Exception as e:
            logger.exception("فشل في تنفيذ طلب Gemini generate_json")
            raise AIProviderError(f"خطأ في خدمة Gemini: {str(e)}")

    async def analyze_vision(
        self,
        image_bytes: bytes,
        mime_type: str,
        prompt: str,
        system_instruction: Optional[str] = None,
        response_schema: Optional[Type[T]] = None,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """
        تحليل المخططات الهندسية والصور المعمارية عبر Gemini Vision بشكل آمن وغير متزامن.
        """
        try:
            # تجهيز جزء الصورة لتمريره للعميل
            image_part = types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type,
            )

            config = types.GenerateContentConfig(
                temperature=temperature,
                response_mime_type="application/json",
                system_instruction=system_instruction,
                response_schema=response_schema if response_schema else None,
            )

            # استدعاء Vision بأسلوب Async مع الصورة والـ Prompt
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=[image_part, prompt],
                config=config,
            )

            response_text = getattr(response, "text", "")
            if not response_text:
                raise AIProviderError("تم استلام استجابة فارغة عند تحليل المخطط الهندسي.")

            parsed = SafeJSONParser.extract(response_text)
            if not parsed:
                raise AIProviderError("فشل في تفكيك بيانات المخطط إلى JSON صحيح.")

            return parsed

        except AIProviderError:
            raise
        except Exception as e:
            logger.exception("فشل في تنفيذ تحليل المخطط عبر Gemini Vision")
            raise AIProviderError(f"خطأ أثناء تحليل المخطط الهندسي: {str(e)}")
