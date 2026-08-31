#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
© 2026 PHOENIX & MIHNA AGENT PRO - BOQ PRICING PROVIDER
مزود الأسعار الإقليمية والمعاملات المباشرة لمواد البناء والتشطيبات
===============================================================================
"""

import logging
from typing import Any, Dict, Optional
from engineering.shared.validation import CommonValidator
from engineering.shared.errors import CalculationError

logger = logging.getLogger(__name__)


class BOQPricingProvider:
    """
    مزود أسعار المواد والخدمات الإقليمي لحسابات جداول الكميات (BOQ).
    يدعم معملات التعديل الجغرافي، مستويات التشطيب المختلفة، ومعاملات التضخم أو التعقيد.
    """

    # المعاملات الإقليمية لأسعار مواد البناء والعمالة
    REGIONAL_MULTIPLIERS: Dict[str, float] = {
        "YE": 0.90,   # اليمن
        "SA": 1.20,   # المملكة العربية السعودية
        "AE": 1.35,   # الإمارات العربية المتحدة
        "EG": 0.85,   # مصر
        "DEFAULT": 1.00
    }

    # الأسعار الأساسية المرجعية (دولار أمريكي) لعام 2026
    BASE_PRICES: Dict[str, float] = {
        "steel_ton": 750.0,      # حديد التسليح (طن)
        "concrete_m3": 80.0,     # خرسانة مسلحة (متر مكعب)
        "blocks_unit": 0.75,     # البلوك/البلوك الخرساني (حبة)
        "excavation_m3": 8.0,    # الحفر والتسوية (متر مكعب)
        "finishing_sqm": 45.0    # التشطيبات الأساسية (متر مربع)
    }

    # معاملات جودة ونوع التشطيب المتاحة
    FINISHING_TIERS: Dict[str, float] = {
        "economy": 0.75,   # اقتصادية
        "standard": 1.00,  # قياسية
        "luxury": 1.80    # فاخرة
    }

    @classmethod
    def get_prices(
        cls, 
        region: str = "DEFAULT", 
        finishing_tier: str = "standard",
        complexity_factor: float = 1.0
    ) -> Dict[str, float]:
        """
        جلب قائمة الأسعار المعدلة إقليمياً والمدروسة حسب نوع التشطيب ومعامل التعقيد.

        :param region: رمز الدولة/المنقليم (YE, SA, AE, EG, DEFAULT).
        :param finishing_tier: مستوى التشطيب (economy, standard, luxury).
        :param complexity_factor: معامل التعقيد الإنشائي أو صعوبة الموقع (افتراضي 1.0).
        :return: قاموس يحتوي على الأسعار المعدلة لكل بند.
        """
        try:
            # 1. التحقق وتأكيد المدخلات
            clean_region = region.upper().strip() if region else "DEFAULT"
            mult = cls.REGIONAL_MULTIPLIERS.get(clean_region, cls.REGIONAL_MULTIPLIERS["DEFAULT"])

            clean_tier = finishing_tier.lower().strip() if finishing_tier else "standard"
            tier_mult = cls.FINISHING_TIERS.get(clean_tier, cls.FINISHING_TIERS["standard"])

            valid_complexity = CommonValidator.validate_positive_number(complexity_factor, "complexity_factor")

            # 2. احتساب الأسعار المعدلة
            prices = {}
            for item, base_price in cls.BASE_PRICES.items():
                final_price = base_price * mult * valid_complexity
                # تطبيق معامل مستوى التشطيب على بنود التشطيبات فقط
                if item == "finishing_sqm":
                    final_price *= tier_mult

                prices[item] = round(final_price, 2)

            return prices

        except Exception as e:
            logger.exception("حدث خطأ أثناء حساب الأسعار الإقليمية في BOQPricingProvider")
            raise CalculationError(
                message=f"فشل جلب أو تقييم الأسعار الإقليمية: {str(e)}"
            )

    @classmethod
    def calculate_item_cost(cls, item_key: str, quantity: float, region: str = "DEFAULT") -> float:
        """
        حساب التكلفة الإجمالية لبند محدد بناءً على الكمية والإقليم.
        """
        prices = cls.get_prices(region=region)
        if item_key not in prices:
            raise CalculationError(message=f"بند التسعير '{item_key}' غير معروف في جدول الأسعار.")

        valid_qty = CommonValidator.validate_non_negative_number(quantity, item_key)
        return round(prices[item_key] * valid_qty, 2)
