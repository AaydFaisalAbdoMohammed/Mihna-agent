import logging
from typing import Any, Dict

from ai.providers.base import BaseAIProvider
from ai.schemas import GuardAnalysisResult, BlueprintTypeEnum
from engineering.shared.errors import BlueprintSecurityError, AIProviderError

logger = logging.getLogger(__name__)


class StrictBlueprintGuard:
    """
    حارس المخططات الهندسي المتقدم (Strict Blueprint Guard).
    يستخدم الرؤية الحاسوبية للذكاء الاصطناعي للتأكد الجازم من أن المستند المرفوع
    هو مخطط هندسي معتمد (معماري، إنشائي، كهروميكانيكي، أو مخطط موقع) قبل السماح بمروره للتحليل.
    """

    SYSTEM_INSTRUCTION = """
    أنت خبير فحص جودة وتدقيق المخططات الهندسية (Engineering Blueprint Auditor).
    مهمتك هي تقييم المستند البصري المرفوع بدقة متناهية والتأكد مما إذا كان مخططاً هندسياً حقيقياً
    (معماري، إنشائي، MEP، أو مخطط موقع عام) يتضمن أبعاداً، محاور، رموزاً هندسية، أو جداول كميات/ملاحظات.
    
    إذا كان المستند صورة شخصية، منظر طبيعي، مستند نصي عادياً، أو غير واضح نهائياً، يجب رفضه بوضوح.
    """

    GUARD_PROMPT = """
    قم بفرز وتحليل هذا المستند المرفق بدقة هندسية:
    1. حدد ما إذا كان المستند يمثل مخططاً هندسياً/CAD/Drawings معتمداً.
    2. حدد درجة ثقتك في هذا القرار كنسبة بين 0.0 و 1.0.
    3. حدد نوع المخطط (architectural, structural, mep, site_plan, non_engineering).
    4. في حال الرفض أو عدم التأكد، اذكر السبب المباشر والدقيق في rejection_reason.
    """

    def __init__(self, provider: BaseAIProvider, min_confidence_threshold: float = 0.75):
        self.provider = provider
        self.min_confidence_threshold = min_confidence_threshold

    async def inspect(self, file_bytes: bytes, mime_type: str) -> Dict[str, Any]:
        """
        فحص المستند بصرياً وإرجاع النتيجة بشكل مفحص ومحمي بأسلوب Async.
        """
        try:
            # استدعاء الرؤية الحاسوبية مع تمرير الـ Pydantic Schema الصارم
            raw_result = await self.provider.analyze_vision(
                image_bytes=file_bytes,
                mime_type=mime_type,
                prompt=self.GUARD_PROMPT,
                system_instruction=self.SYSTEM_INSTRUCTION,
                response_schema=GuardAnalysisResult,
                temperature=0.0,  # الصفر لضمان أعلى درجات الدقة والصرامة
            )

            # تحويل النتيجة لـ GuardAnalysisResult إن كانت قاموساً للتأكد من السلامة Structure Safety
            if isinstance(raw_result, dict):
                guard_data = GuardAnalysisResult(**raw_result)
            elif isinstance(raw_result, GuardAnalysisResult):
                guard_data = raw_result
            else:
                guard_data = GuardAnalysisResult(
                    is_engineering_blueprint=False,
                    confidence_score=0.0,
                    detected_type=BlueprintTypeEnum.NON_ENGINEERING,
                    rejection_reason="تعذر فحص هيكلية استجابة حارس المخططات."
                )

            # تحويل نتيجة درجة الثقة إن وردت بنسبة مئوية (مثلاً 85 بدلاً من 0.85)
            confidence = guard_data.confidence_score
            if confidence > 1.0:
                confidence = confidence / 100.0

            # تطبيق معيار الأمان الصارم (Strict Decision Criteria)
            is_valid = (
                guard_data.is_engineering_blueprint
                and confidence >= self.min_confidence_threshold
                and guard_data.detected_type != BlueprintTypeEnum.NON_ENGINEERING
            )

            rejection_reason = guard_data.rejection_reason
            if not is_valid and not rejection_reason:
                rejection_reason = (
                    f"الملف المرفوع لا يستوفي معايير المخطط الهندسي "
                    f"(درجة الثقة: {round(confidence * 100, 1)}% - الحد الأدنى المطلوب: {int(self.min_confidence_threshold * 100)}%)."
                )

            return {
                "is_valid_blueprint": is_valid,
                "confidence_score": round(confidence, 2),
                "blueprint_type": guard_data.detected_type.value,
                "rejection_reason": rejection_reason if not is_valid else None
            }

        except AIProviderError as e:
            logger.error(f"فشل الاتصال بمزود الذكاء الاصطناعي أثناء فحص الحارس: {str(e)}")
            raise BlueprintSecurityError(
                message="تعذر التحقق من أمان المخطط بسبب تعثر في خدمة التحليل البصري.",
                details={"provider_error": str(e)}
            )
        except Exception as e:
            logger.exception("حدث خطأ غير متوقع داخل StrictBlueprintGuard")
            raise BlueprintSecurityError(
                message=f"حدث خطأ أثناء فحص أمان المخطط: {str(e)}"
            )
