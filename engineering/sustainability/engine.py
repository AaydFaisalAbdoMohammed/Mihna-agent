#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
© 2026 PHOENIX & MIHNA AGENT PRO - SUSTAINABILITY & ENERGY ENGINE
محرك الاستدامة وتقييم كفاءة الطاقة، البصمة الكربونية، وأنظمة الطاقة الشمسية
===============================================================================
"""

import logging
from typing import Any, Dict, Optional

from engineering.shared.errors import CalculationError
from engineering.shared.validation import CommonValidator

logger = logging.getLogger(__name__)


class SustainabilityEngine:
    """
    محرك تقييم الاستدامة والطاقة (Sustainability & Energy Engine).
    يقوم بحساب استهلاك الطاقة السنوي التقديري، حساب قدرة المحطة الشمسية الكهروضوئية (PV)
    الموصى بها، تقدير انبعاثات البصمة الكربونية، واقتراح مواصفات العزل الحراري.
    """

    # متوسط استهلاك الطاقة المرجعي للمتر المربع السكني سنويًا (kWh/m²/year)
    DEFAULT_ANNUAL_KWH_PER_SQM: float = 110.0

    # متوسط ساعات الذروة الشمسية اليومية (Peak Sun Hours - PSH) - السائد في منطقة MENA
    DEFAULT_PEAK_SUN_HOURS: float = 5.2

    # معامل انبعاثات CO2 المرجعي بناءً على إنتاج المواد وتأثير البناء (Tons CO2/m²)
    DEFAULT_CO2_PER_SQM_FACTOR: float = 0.24

    async def evaluate(
        self, 
        total_built_area: float,
        region: str = "DEFAULT",
        peak_sun_hours: Optional[float] = None,
        custom_kwh_per_sqm: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        تقييم الاستدامة وبصمة الطاقة للمبنى بشكل غير متزامن (Async).

        :param total_built_area: المساحة المبنية الإجمالية (BUA) بالمتر المربع.
        :param region: رمز المنطقة لضبط التوصيات والمعايير الجغرافية.
        :param peak_sun_hours: عدد ساعات الذروة الشمسية اليومية المخصصة.
        :param custom_kwh_per_sqm: معدل استهلاك الطاقة المخصص لكل متر مربع.
        :return: قاموس مفصل يوضح نتائج تقييم الاستدامة وكفاءة المبنى.
        """
        try:
            # 1. التحقق الصارم من المدخلات
            valid_bua = CommonValidator.validate_positive_number(total_built_area, "total_built_area")

            psh = peak_sun_hours if peak_sun_hours is not None else self.DEFAULT_PEAK_SUN_HOURS
            valid_psh = CommonValidator.validate_positive_number(psh, "peak_sun_hours")

            kwh_rate = custom_kwh_per_sqm if custom_kwh_per_sqm is not None else self.DEFAULT_ANNUAL_KWH_PER_SQM
            valid_kwh_rate = CommonValidator.validate_positive_number(kwh_rate, "custom_kwh_per_sqm")

            # 2. حساب الاستهلاك السنوي المتوقع للطاقة (kWh/Year)
            annual_kwh = valid_bua * valid_kwh_rate

            # 3. حساب قدرة النظام الشمسي الموصى به (kWp) لتغطية الاستهلاك الأساسي
            # الاستهلاك اليومي المتوقع = الاستهلاك السنوي / 365
            # قدرة النظام الكهروضوئي = الاستهلاك اليومي / (ساعات الذروة × كفاءة النظام 0.82)
            daily_kwh = annual_kwh / 365.0
            system_efficiency_factor = 0.82
            solar_capacity_kwp = daily_kwh / (valid_psh * system_efficiency_factor)

            # 4. حساب البصمة الكربونية المقدرة لتشغيل ومواد المبنى (Tons CO2)
            co2_tons = valid_bua * self.DEFAULT_CO2_PER_SQM_FACTOR

            # 5. تحديد توصيات العزل الحراري وأنظمة التظليل حسب المنطقة
            if region.upper() in ["YE", "SA", "AE"]:
                insulation_recommendation = "Extruded Polystyrene (XPS) 50mm - High Thermal Mass"
                glazing_recommendation = "Double Glazed Low-E Glass (U-value <= 1.8)"
            else:
                insulation_recommendation = "Standard XPS 50mm Insulation Board"
                glazing_recommendation = "Double Glazed Clear Glass"

            logger.info(
                f"تم تقييم الاستدامة للمبنى: المساحة {valid_bua} م²، "
                f"الطاقة الشمسية {round(solar_capacity_kwp, 2)} kWp، "
                f"الانبعاثات الكربونية {round(co2_tons, 2)} طن."
            )

            return {
                "built_area_sqm": valid_bua,
                "annual_energy_kwh": round(annual_kwh, 2),
                "daily_energy_kwh": round(daily_kwh, 2),
                "solar_pv_kwp_recommended": round(solar_capacity_kwp, 2),
                "co2_footprint_tons": round(co2_tons, 2),
                "peak_sun_hours_used": valid_psh,
                "insulation_rating": insulation_recommendation,
                "glazing_recommendation": glazing_recommendation,
                "sustainability_rating": "Green Building Class B Standard"
            }

        except Exception as e:
            logger.exception("حدث خطأ أثناء إجراء حسابات محرك الاستدامة في SustainabilityEngine")
            raise CalculationError(
                message=f"فشل تقييم مؤشرات الاستدامة والطاقة الشمسية: {str(e)}"
            )
