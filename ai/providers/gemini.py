import logging
import os
import asyncio
from typing import Any, Dict, Optional, Type, TypeVar, Union
from pydantic import BaseModel

# -----------------------------------------------------------------------------
# الآلية الآمنة للاستيراد (Fall-back Safety Engine)
# -----------------------------------------------------------------------------
USE_NEW_SDK = False
GENAI_AVAILABLE = False

try:
    # محاولة استيراد المكتبة الحديثة google-genai
    from google import genai
    from google.genai import types
    USE_NEW_SDK = True
    GENAI_AVAILABLE = True
except ImportError:
    try:
        # محاولة استيراد المكتبة القديمة google-generativeai كخيار احتياطي
        import google.generativeai as legacy_genai
        genai = legacy_genai
        types = None
        USE_NEW_SDK = False
        GENAI_AVAILABLE = True
    except ImportError:
        genai = None
        types = None
        GENAI_AVAILABLE = False

# استيراد المكونات الداخلية مع معالجة الاستثناءات للتشغيل المستقل
try:
    from ai.providers.base import BaseAIProvider
except ImportError:
    class BaseAIProvider:
        pass

try:
    from engineering.shared.errors import AIProviderError
except ImportError:
    class AIProviderError(Exception):
        pass

try:
    from engineering.shared.json_parser import SafeJSONParser
except ImportError:
    import json
    class SafeJSONParser:
        @staticmethod
        def extract(text: str) -> Dict[str, Any]:
            try:
                # محاولة استخراج JSON من النص مباشرة أو البحث عن الكتل المكتوبة
                text = text.strip()
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                return json.loads(text)
            except Exception:
                return {}

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class GeminiProvider(BaseAIProvider):
    """
    تطبيق المزود الرئيسي لـ Google Gemini المعتمد على أحدث حزمة google-genai
    مع التوافق التلقائي للرجوع للمكتبة القديمة (Fallback mechanism).
    
    يدعم المعالجة غير المتزامنة (Async)، الـ Structured Outputs المعتمدة على Pydantic،
    والتحليل البصري الهندسي عالي الدقة.
    """

    def __init__(
        self, 
        api_key: Optional[str] = None, 
        model_name: str = "gemini-2.5-flash"
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name

        if not GENAI_AVAILABLE:
            logger.warning("لم يتم العثور على أي حزمة مثبتة لـ Google GenAI (google-genai أو google-generativeai).")
            self.client = None
            return

        if not self.api_key:
            logger.warning("GEMINI_API_KEY غير موجود في متغيرات البيئة.")
            self.client = None
            return

        try:
            if USE_NEW_SDK:
                # تهيئة العميل المتقدم من google-genai
                self.client = genai.Client(api_key=self.api_key)
            else:
                # تهيئة المكتبة القديمة google-generativeai
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel(model_name=self.model_name)
        except Exception as e:
            logger.error(f"فشل في تهيئة عميل Gemini: {str(e)}")
            self.client = None

    async def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        response_schema: Optional[Type[T]] = None,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """
        توليد استجابة JSON مهيكلة بشكل آمن وغير متزامن مع دعم الـ Fallback.
        """
        if not self.client:
            raise AIProviderError("مزود Gemini غير مهيأ (تحقق من تثبيت مكتبة google-genai ومفتاح API).")

        try:
            response_text = ""

            if USE_NEW_SDK:
                # إعداد التكوين المتقدم لـ SDK الحديثة
                config = types.GenerateContentConfig(
                    temperature=temperature,
                    response_mime_type="application/json",
                    system_instruction=system_instruction,
                    response_schema=response_schema if response_schema else None,
                )

                # الاستدعاء غير المتزامن (Async) عبر العميل الحديث
                response = await self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=config,
                )
                response_text = getattr(response, "text", "")
            else:
                # تنفيذ الاستدعاء عبر المكتبة القديمة باستخدام ThreadPool لعدم إعاقة الـ Async Event Loop
                def _legacy_call():
                    prompt_full = prompt
                    if system_instruction:
                        prompt_full = f"System: {system_instruction}\n\nUser: {prompt}"
                    res = self.client.generate_content(
                        prompt_full,
                        generation_config={"temperature": temperature, "response_mime_type": "application/json"}
                    )
                    return getattr(res, "text", "")

                response_text = await asyncio.to_thread(_legacy_call)

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
        if not self.client:
            raise AIProviderError("مزود Gemini غير مهيأ للتحليل البصري.")

        try:
            response_text = ""

            if USE_NEW_SDK:
                # تجهيز جزء الصورة للعميل الحديث
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

                response = await self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=[image_part, prompt],
                    config=config,
                )
                response_text = getattr(response, "text", "")
            else:
                # التعامل مع المكتبة القديمة للصور
                def _legacy_vision_call():
                    image_blob = {
                        "mime_type": mime_type,
                        "data": image_bytes
                    }
                    prompt_full = prompt
                    if system_instruction:
                        prompt_full = f"System: {system_instruction}\n\nUser: {prompt}"
                    
                    res = self.client.generate_content(
                        [image_blob, prompt_full],
                        generation_config={"temperature": temperature, "response_mime_type": "application/json"}
                    )
                    return getattr(res, "text", "")

                response_text = await asyncio.to_thread(_legacy_vision_call)

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
