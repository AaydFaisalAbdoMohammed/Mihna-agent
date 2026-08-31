#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
© 2026 PHOENIX & MIHNA AGENT PRO - BLUEPRINT ANALYZER ENGINE
المحلل الهندسي البصري المستخرج للتفاصيل المعمارية، المساحات، والغرف من المخططات
===============================================================================
"""

import logging
from typing import Any, Dict, List, Optional

from ai.providers.base import BaseAIProvider
from ai.schemas import AnalyzerResult, BlueprintTypeEnum, RoomDetails
from engineering.shared.errors import CalculationError, AIProviderError
from engineering.shared.validation import CommonValidator

logger = logging.getLogger(__name__)


class BlueprintAnalyzer:
    """
    المحلل الهندسي للمخططات (Blueprint Analyzer).
    يقوم بتحليل الصور والمخططات الهندسية المعمارية والإنشائية لاستخراج المساحات،
    توزيع الغرف، عدد الأدوار، والتلميحات الإنشائية باستخدام الرؤية الحاسوبية المتقدمة.
    """

    SYSTEM_INSTRUCTION = """
    أنت مهندس معماري خبير ومحلل كميات ومخططات هندسية (Senior Architectural & Quantity Surveyor).
    مهمتك هي قراءة المخطط الهندسي المرفق بدقة متناهية واستخراج البيانات التقنية والمكانية التالية:
    1. تحديد نوع المخطط الهندسي (معماري، إنشائي، كهروميكانيكي، أو مخطط موقع).
    2. تقدير إجمالي المساحة المبنية (Total Built-up Area) بالمتر المربع.
    3. تحديد عدد الأدوار الظاهرة أو المشار إليها في المخطط.
    4. استخراج تفاصيل الغرف والفضاءات (الاسم، المساحة التقديرية لكل غرفة، والأبعاد إن وجدت).
    5. استخراج التلميحات الإنشائية الجوهرية (مثل: عدد الأعمدة، الجدران الحاملة، الفتحات، ونوع السقف إن وجد).
    """

    ANALYSIS_PROMPT = """
    قم بتحليل المخطط الهندسي المرفق واستخراج بياناته بشكل دقيق ومهيكل:
    - استخرج قائمة الغرف/الفضاءات مع أسمائها ومساحاتها التقديرية.
    - احسب إجمالي المساحة التقريبية الظاهرة للمشروع بالمتر المربع.
    - حدد عدد الأدوار الظاهرة.
    - اذكر أي ملاحظات أو تلميحات إنشائية معمارية هامة.
    """

    def __init__(self, provider: BaseAIProvider):
        self.provider = provider

    async def analyze(
        self, 
        file_bytes: bytes, 
        mime_type: str, 
        fallback_land_area: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        تحليل المخطط واستخراج المكونات المعمارية والمساحات بأسلوب غير متزامن (Async).
        
        :param file_bytes: البايتات الثنائية لملف المخطط.
        :param mime_type: امتداد الملف (MIME Type).
        :param fallback_land_area: مساحة إضافية مرجعية للاستئناس في حال عدم وضوح أبعاد المخطط.
        :return: قاموس بيانات مفصل ومحقق يحتوى النتائج المعمارية والإنشائية.
        """
        try:
            # 1. استدعاء نموذج الرؤية الحاسوبية بالذكاء الاصطناعي وإلزامه بالـ AnalyzerResult Schema
            raw_result = await self.provider.analyze_vision(
                image_bytes=file_bytes,
                mime_type=mime_type,
                prompt=self.ANALYSIS_PROMPT,
                system_instruction=self.SYSTEM_INSTRUCTION,
                response_schema=AnalyzerResult,
                temperature=0.1,  # درجة حرارة منخفضة لضمان الدقة وتفادي الهلوسة الرقمية
            )

            # 2. مطابقة وتأكيد جودة البنية المستلمة (Schema Validation Parse)
            if isinstance(raw_result, dict):
                result_model = AnalyzerResult(**raw_result)
            elif isinstance(raw_result, AnalyzerResult):
                result_model = raw_result
            else:
                raise CalculationError("تعذر تحويل نتائج تحليل المخطط إلى هيكل النماذج المعتمد.")

            # 3. معالجة وتدقيق المساحات عبر أدوات التحقق الموحدة (CommonValidator)
            total_area = result_model.total_estimated_area
            if total_area <= 0 and fallback_land_area and fallback_land_area > 0:
                logger.info(f"تم اعتماد المساحة الاحتياطية ({fallback_land_area} م²) لعدم وضوح الأبعاد المباشرة.")
                total_area = float(fallback_land_area)
            else:
                total_area = CommonValidator.validate_non_negative_number(total_area, "total_estimated_area")

            floors = max(1, result_model.floors_detected)

            # 4. تنظيف وتدقيق بيانات الغرف الاستخراجية
            processed_rooms: List[Dict[str, Any]] = []
            for room in result_model.rooms:
                processed_rooms.append({
                    "name": room.name or "فضاء غير مسمى",
                    "estimated_area_sqm": CommonValidator.validate_non_negative_number(
                        room.estimated_area_sqm, f"room_area_{room.name}"
                    ),
                    "dimensions_text": room.dimensions_text or "غير محدد"
                })

            # 5. بناء الحصيلة النهائية واستخراج القاموس الجاهز للاستخدام في Facade و API
            final_output = {
                "blueprint_type": result_model.blueprint_type.value,
                "total_estimated_area_sqm": round(total_area, 2),
                "floors_detected": floors,
                "rooms_count": len(processed_rooms),
                "rooms": processed_rooms,
                "structural_hints": result_model.structural_hints or {},
                "raw_metadata": result_model.raw_ai_metadata or {}
            }

            logger.info(
                f"تم تحليل المخطط بنجاح: النوع {result_model.blueprint_type.value}، "
                f"المساحة {total_area} م²، عدد الغرف {len(processed_rooms)}."
            )
            return final_output

        except AIProviderError as e:
            logger.error(f"حدث خطأ من مزود الذكاء الاصطناعي أثناء تحليل المخطط: {str(e)}")
            raise CalculationError(
                message="تعذر استخراج البيانات المعمارية من المخطط بسبب خلل في مزود التحليل البصري.",
                details={"provider_error": str(e)}
            )
        except Exception as e:
            logger.exception("حدث خطأ غير متوقع أثناء تنفيذ عملية BlueprintAnalyzer")
            raise CalculationError(
                message=f"حدث خطأ أثناء معالجة وحساب مكونات المخطط الهندسي: {str(e)}"
            )
