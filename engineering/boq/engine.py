#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
© 2026 PHOENIX & MIHNA AGENT PRO - BOQ ENGINE
المنسق والمنفذ الرئيسي لحسابات مقايسة الكميات وتكاليف البناء التقديرية
===============================================================================
"""

import logging
from typing import Any, Dict, List, Optional

from engineering.boq.pricing import BOQPricingProvider
from engineering.shared.errors import CalculationError
from engineering.shared.validation import CommonValidator

logger = logging.getLogger(__name__)


class BOQEngine:
    """
    محرك مقايسة الكميات والتكاليف (BOQ Engine).
    يقوم بحساب كميات المواد الإنشائية والتشطيبات واستخراج التكلفة الإجمالية
    بناءً على المساحة المبنية، عدد الأدوار، والإقليم المستهدف بأسلوب غير معطل (Async).
    """

    def __init__(self, pricing_provider: Optional[BOQPricingProvider] = None):
        self.pricing_provider = pricing_provider or BOQPricingProvider()

    async def calculate(
        self,
        built_area: float,
        floors: int = 1,
        region: str = "DEFAULT",
        finishing_tier: str = "standard",
        contingency_rate: float = 0.10
    ) -> Dict[str, Any]:
        """
        حساب جدول الكميات والتكاليف التقديرية للمشروع بشكل غير متزامن.

        :param built_area: المساحة المبنية الإجمالية (BUA) بالمتر المربع.
        :param floors: عدد أدوار المبنى.
        :param region: رمز الدولة/المنطقة لحساب الأسعار الإقليمية.
        :param finishing_tier: مستوى جودة التشطيب (economy, standard, luxury).
        :param contingency_rate: نسبة الطوارئ والاحتياطي المالي (افتراضي 10%).
        :return: قاموس مفصل بالبنود، الكميات، الأسعار الفردية، والإجمالي النهائي.
        """
        try:
            # 1. التحقق الصارم من المدخلات
            valid_area = CommonValidator.validate_positive_number(built_area, "built_area")
            valid_floors = int(CommonValidator.validate_positive_number(floors, "floors"))
            valid_contingency = CommonValidator.validate_percentage(
                contingency_rate * 100, "contingency_rate"
            ) / 100.0

            # 2. جلب الأسعار الإقليمية المعدلة حسب الإقليم ونوع التشطيب
            prices = self.pricing_provider.get_prices(
                region=region,
                finishing_tier=finishing_tier
            )

            # 3. حساب الكميات الإنشائية والمعمارية بناءً على القواعد الهندسية للأنشطة
            # - حديد التسليح: متوسط 42 كجم/م² أي 0.042 طن/م² (يتعدل طفيفاً بزيادة الأدوار)
            steel_factor = 0.042 * (1.0 + (valid_floors - 1) * 0.03)
            steel_ton = valid_area * steel_factor

            # - الخرسانة المسلحة: متوسط 0.40 م³/م²
            concrete_m3 = valid_area * 0.40

            # - البلوك/الطابوق: متوسط 12.5 حبة/م²
            blocks_pcs = valid_area * 12.5

            # - أعمال الحفر والتسوية: تقدير مرجعي بناءً على مساحة مسقط الدور الأرضي
            ground_floor_area = valid_area / valid_floors
            excavation_m3 = ground_floor_area * 1.80

            # - مساحة التشطيبات: تعادل المساحة المبنية الإجمالية
            finishing_sqm = valid_area

            # 4. بناء قائمة البنود بالتفصيل وتطبيق الأسعار
            items: List[Dict[str, Any]] = [
                {
                    "item_code": "CIV-01",
                    "item": "أعمال الحفر والتسوية للموقع",
                    "qty": round(excavation_m3, 2),
                    "unit": "متر مكعب",
                    "unit_price_usd": prices["excavation_m3"],
                    "total_usd": round(excavation_m3 * prices["excavation_m3"], 2)
                },
                {
                    "item_code": "CIV-02",
                    "item": "حديد التسليح عالي المقاومة",
                    "qty": round(steel_ton, 2),
                    "unit": "طن",
                    "unit_price_usd": prices["steel_ton"],
                    "total_usd": round(steel_ton * prices["steel_ton"], 2)
                },
                {
                    "item_code": "CIV-03",
                    "item": "الخرسانة المسلحة الجاهزة",
                    "qty": round(concrete_m3, 2),
                    "unit": "متر مكعب",
                    "unit_price_usd": prices["concrete_m3"],
                    "total_usd": round(concrete_m3 * prices["concrete_m3"], 2)
                },
                {
                    "item_code": "CIV-04",
                    "item": "مباني الطابوق/البلوك الخرساني",
                    "qty": round(blocks_pcs, 0),
                    "unit": "حبة",
                    "unit_price_usd": prices["blocks_unit"],
                    "total_usd": round(blocks_pcs * prices["blocks_unit"], 2)
                },
                {
                    "item_code": "FIN-01",
                    "item": f"أعمال التشطيبات التكاملية ({finishing_tier.capitalize()})",
                    "qty": round(finishing_sqm, 2),
                    "unit": "متر مربع",
                    "unit_price_usd": prices["finishing_sqm"],
                    "total_usd": round(finishing_sqm * prices["finishing_sqm"], 2)
                }
            ]

            # 5. حساب المجموع المباشر، طوارئ المشروع، والتكلفة الكلية
            subtotal = sum(item["total_usd"] for item in items)
            contingency_amount = subtotal * valid_contingency
            total_cost = subtotal + contingency_amount

            logger.info(
                f"تم حساب جدول الكميات بنجاح: المساحة {valid_area} م²، الإقليم '{region}'، "
                f"الإجمالي المباشر: {round(subtotal, 2)}$."
            )

            return {
                "built_area_sqm": valid_area,
                "floors": valid_floors,
                "region": region,
                "finishing_tier": finishing_tier,
                "items": items,
                "subtotal_usd": round(subtotal, 2),
                "contingency_rate_pct": f"{int(valid_contingency * 100)}%",
                "contingency_usd": round(contingency_amount, 2),
                "total_usd": round(total_cost, 2)
            }

        except Exception as e:
            logger.exception("حدث خطأ أثناء تنفيذ حسابات BOQEngine")
            raise CalculationError(
                message=f"فشل إعداد جدول الكميات والتكاليف: {str(e)}"
            )
