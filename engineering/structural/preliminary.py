#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
© 2026 PHOENIX & MIHNA AGENT PRO - PRELIMINARY STRUCTURAL ENGINE
المحرك الإنشائي الأولي لحساب الأحمال التصميمية، تقدير الأعمدة، ومواصفات الخرسانة
===============================================================================
"""

import logging
import math
from typing import Any, Dict, Optional

from engineering.shared.errors import CalculationError
from engineering.shared.validation import CommonValidator
from engineering.structural.models import StructuralAssessmentResult

logger = logging.getLogger(__name__)


class StructuralEngine:
    """
    المحرك الإنشائي الأولي (Preliminary Structural Engine).
    يقوم بحساب أحمال التجميع الجاذبية (Gravity Loads)، الحمل المصمم (Factored Load U.L.S)،
    العدد التقريبي للأعمدة المطلوب، وتحديد رتبة الخرسانة والحديد الموصى بها.
    """

    # معاملات الأحمال التصميمية وفقاً لكود ACI 318 / ASCE 7
    DEAD_LOAD_FACTOR: float = 1.2
    LIVE_LOAD_FACTOR: float = 1.6

    # الأحمال الميتة الافتراضية للأسقف والتشطيبات والقواطع (kN/m²)
    DEFAULT_DEAD_LOAD_KN: float = 4.5  # تشمل وزن بلاطة السقف + التشطيبات + الجدران

    async def assess(
        self, 
        total_area: float, 
        floors: int, 
        live_load_kn: float = 2.0,
        custom_dead_load_kn: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        تقييم الأحمال الإنشائية الأولية وحساب قطاعات الأعمدة بأسلوب غير متزامن (Async).

        :param total_area: مساحة المسقط الأفقي للدور بالمتر المربع.
        :param floors: عدد الأدوار.
        :param live_load_kn: الحمل الحي المصمم (kN/m²) - 2.0 للمباني السكنية.
        :param custom_dead_load_kn: حمل ميت مخصص إن وجد (kN/m²).
        :return: قاموس نتائج مفصل وموثق متوافق مع StructuralAssessmentResult.
        """
        try:
            # 1. التحقق الصارم من المدخلات
            valid_area = CommonValidator.validate_positive_number(total_area, "total_area")
            valid_floors = int(CommonValidator.validate_positive_number(floors, "floors"))
            valid_live_load = CommonValidator.validate_non_negative_number(live_load_kn, "live_load_kn")

            dead_load = custom_dead_load_kn if custom_dead_load_kn is not None else self.DEFAULT_DEAD_LOAD_KN
            valid_dead_load = CommonValidator.validate_positive_number(dead_load, "dead_load")

            # 2. حساب الحمل المصمم الأقصى (Ultimate Factored Load Wu)
            factored_load = (self.DEAD_LOAD_FACTOR * valid_dead_load) + (self.LIVE_LOAD_FACTOR * valid_live_load)

            # 3. حساب إجمالي الأحمال الجاذبية المنقولة للأساسات (Total Ultimate Load)
            # المساحة المبنية الإجمالية = مساحة الدور × عدد الأدوار
            total_bua = valid_area * valid_floors
            total_gravity_load = total_bua * factored_load

            # 4. تقدير عدد الأعمدة بناءً على مسافة الشبكة الإنشائية القياسية (شبكة 4m x 4m إلى 5m x 5m)
            # متوسط المساحة المخدومة لكل عمود = 16 - 20 متر مربع
            columns_count = max(4, int(math.ceil(valid_area / 18.0)))

            # 5. حساب متوسط الحمل المحوري التقديري لجميع الأدوار على العمود الواحد (kN)
            estimated_load_per_column_kn = round(total_gravity_load / columns_count, 2)

            # 6. اختيار رتبة الخرسانة والحديد الموصى بها بناءً على ارتفاع المبنى والأحمال
            if valid_floors <= 3:
                recommended_concrete = "C25/30 (f'c = 25 MPa)"
                recommended_steel = "Grade 60 / FY 420 MPa"
            elif valid_floors <= 8:
                recommended_concrete = "C30/37 (f'c = 30 MPa)"
                recommended_steel = "Grade 60 / FY 420 MPa"
            else:
                recommended_concrete = "C40/50 (f'c = 40 MPa)"
                recommended_steel = "Grade 75 / FY 520 MPa"

            # 7. مطابقة البيانات مع Schema / StructuralAssessmentResult
            assessment_data = {
                "factored_load_kn_m2": round(factored_load, 2),
                "total_gravity_load_kn": round(total_gravity_load, 2),
                "estimated_columns_count": columns_count,
                "load_per_column_kn": estimated_load_per_column_kn,
                "recommended_concrete": recommended_concrete,
                "recommended_steel": recommended_steel,
                "is_preliminary": True
            }

            # التحقق عبر النموذج الإنشائي المعتمد
            result_model = StructuralAssessmentResult(**assessment_data)

            logger.info(
                f"تم تقييم المنشأ إنشائياً: الحمل الكلي {round(total_gravity_load, 2)} kN، "
                f"عدد الأعمدة {columns_count}، الخرسانة {recommended_concrete}."
            )

            return result_model.model_dump()

        except Exception as e:
            logger.exception("حدث خطأ أثناء إجراء التقييم الإنشائي الأولي في StructuralEngine")
            raise CalculationError(
                message=f"فشل التقييم الإنشائي الأولي للأحمال والأعمدة: {str(e)}"
            )
