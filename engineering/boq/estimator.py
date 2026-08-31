#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
© 2026 PHOENIX & MIHNA AGENT PRO - BOQ ESTIMATOR
حاسبة الأحجام والكميات الهندسية التفصيلية للخرسانات والحديد والتشطيبات
===============================================================================
"""

import logging
from typing import Any, Dict, Optional
from engineering.shared.validation import CommonValidator
from engineering.shared.errors import CalculationError

logger = logging.getLogger(__name__)


class BOQEstimator:
    """
    مُقَدِّر الكميات الإنشائية والمعمارية (Structural & Architectural Estimator).
    يقوم بحساب حجوم العناصر الخرسانية (القواعد، الأعمدة، الأسقف)، أوزان التسليح،
    ومساحات المحارة والدهانات بدقة مهنية مبنية على المساحات والأدوار.
    """

    def __init__(
        self, 
        concrete_density_kg_m3: float = 2400.0,
        rebar_ratio_slab_kg_m3: float = 100.0,
        rebar_ratio_column_kg_m3: float = 160.0,
        rebar_ratio_footing_kg_m3: float = 90.0
    ):
        """
        تهيئة كائن التقدير مع نسب التسليح القياسية لكل عنصر إنشائي.
        """
        self.concrete_density = concrete_density_kg_m3
        self.rebar_ratio_slab = rebar_ratio_slab_kg_m3      # نسبة تسليح الأسقف (كجم/م³)
        self.rebar_ratio_column = rebar_ratio_column_kg_m3  # نسبة تسليح الأعمدة (كجم/م³)
        self.rebar_ratio_footing = rebar_ratio_footing_kg_m3 # نسبة تسليح القواعد (كجم/م³)

    async def estimate_volumetric_quantities(
        self, 
        built_area_sqm: float, 
        floors: int = 1,
        typical_floor_height_m: float = 3.20
    ) -> Dict[str, Any]:
        """
        تقدير الحجوم الهندسية وكميات المواد بالتفصيل لجميع المكونات الخرسانية بأسلوب غير معطل (Async).

        :param built_area_sqm: إجمالي المساحة المبنية بالمتر المربع (BUA).
        :param floors: عدد الأدوار.
        :param typical_floor_height_m: ارتفاع الدور القياسي بالمتر.
        :return: قاموس يحتوي على تفاصيل حجوم الخرسانات وأوزان حديد التسليح لكل عنصر.
        """
        try:
            # 1. التحقق الصارم من المدخلات
            valid_bua = CommonValidator.validate_positive_number(built_area_sqm, "built_area_sqm")
            valid_floors = int(CommonValidator.validate_positive_number(floors, "floors"))
            valid_height = CommonValidator.validate_positive_number(typical_floor_height_m, "typical_floor_height_m")

            ground_floor_area = valid_bua / valid_floors

            # 2. حساب حجم خرسانات القواعد والأساسات (Footings & Foundations)
            # متوسط سماكة مكافئة للأساسات = 0.40 م من مساحة مسقط الدور الأرضي
            footings_concrete_m3 = ground_floor_area * 0.40
            footings_rebar_tons = (footings_concrete_m3 * self.rebar_ratio_footing) / 1000.0

            # 3. حساب حجم خرسانات الأعمدة والمحيط الإنشائي (Columns & Sherawalls)
            # تمثل القطاعات الخرسانية للأعمدة حوالي 4% من مساحة الدور مضروبة في الارتفاع
            columns_concrete_per_floor = (ground_floor_area * 0.04) * valid_height
            total_columns_concrete_m3 = columns_concrete_per_floor * valid_floors
            columns_rebar_tons = (total_columns_concrete_m3 * self.rebar_ratio_column) / 1000.0

            # 4. حساب حجم خرسانات الأسقف والكمرات (Slabs & Beams)
            # متوسط سمك السقف الخرساني مع الكمرات = 0.22 م لكل دور
            slabs_concrete_m3 = valid_bua * 0.22
            slabs_rebar_tons = (slabs_concrete_m3 * self.rebar_ratio_slab) / 1000.0

            # 5. تجميع الإجماليات الإنشائية
            total_concrete_m3 = footings_concrete_m3 + total_columns_concrete_m3 + slabs_concrete_m3
            total_rebar_tons = footings_rebar_tons + columns_rebar_tons + slabs_rebar_tons

            # 6. تقدير مساحات البياض والدهانات الداخلية والخارجية (Finishing Surfaces)
            # المساحة السطحية للجدران تعادل تقريباً 2.8 ضعف المساحة المبنية
            plaster_plaster_sqm = valid_bua * 2.80

            logger.info(
                f"تم إنجاز التقدير الحجمي: إجمالي الخرسانات {round(total_concrete_m3, 2)} م³، "
                f"إجمالي الحديد {round(total_rebar_tons, 2)} طن."
            )

            return {
                "built_area_sqm": valid_bua,
                "floors": valid_floors,
                "breakdown": {
                    "footings": {
                        "concrete_m3": round(footings_concrete_m3, 2),
                        "rebar_tons": round(footings_rebar_tons, 2)
                    },
                    "columns": {
                        "concrete_m3": round(total_columns_concrete_m3, 2),
                        "rebar_tons": round(columns_rebar_tons, 2)
                    },
                    "slabs_and_beams": {
                        "concrete_m3": round(slabs_concrete_m3, 2),
                        "rebar_tons": round(slabs_rebar_tons, 2)
                    }
                },
                "totals": {
                    "total_concrete_m3": round(total_concrete_m3, 2),
                    "total_rebar_tons": round(total_rebar_tons, 2),
                    "estimated_wall_plaster_sqm": round(plaster_plaster_sqm, 2)
                }
            }

        except Exception as e:
            logger.exception("حدث خطأ أثناء إجراء التقديرات الحجمية في BOQEstimator")
            raise CalculationError(
                message=f"فشل حساب حجوم العناصر الإنشائية والكميات: {str(e)}"
            )
