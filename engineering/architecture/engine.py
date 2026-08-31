#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
© 2026 PHOENIX & MIHNA AGENT PRO - ARCHITECTURAL ENGINE
المحرك المعماري لحساب سيناريوهات البناء، توزيع المساحات الوظيفية، والتكلفة التقديرية
===============================================================================
"""

import logging
from typing import Any, Dict
from engineering.architecture.assumptions import ArchitecturalAssumptions
from engineering.shared.validation import CommonValidator
from engineering.shared.errors import CalculationError

logger = logging.getLogger(__name__)


class ArchitecturalEngine:
    """
    المحرك المعماري الرئيسي لحساب وتحليل سيناريوهات البناء،
    توزيع المساحات النفعية، وحساب مساحات الأدوار والتكلفة المبدئية.
    """

    def __init__(self, assumptions: ArchitecturalAssumptions = ArchitecturalAssumptions()):
        self.assumptions = assumptions

    async def generate_layout(self, land_area: float, num_floors: int) -> Dict[str, Any]:
        """
        توليد وتقسيم المسقط المعماري وحساب المساحات والتكلفة بأسلوب غير معطل (Async).

        :param land_area: مساحة الأرض الإجمالية بالمتر المربع.
        :param num_floors: عدد الأدوار المطلوبة.
        :return: قاموس مفصل يحتوي على حسابات البصمة المعمارية، المساحة الصافية، وتوزيع الغرف.
        """
        try:
            # 1. التحقق الصارم من المدخلات
            valid_land_area = CommonValidator.validate_positive_number(land_area, "land_area")
            valid_floors = int(CommonValidator.validate_positive_number(num_floors, "num_floors"))

            if valid_floors > self.assumptions.MAX_RECOMMENDED_FLOORS:
                logger.warning(
                    f"عدد الأدوار المطلوبة ({valid_floors}) يتجاوز الحد الموصى به "
                    f"({self.assumptions.MAX_RECOMMENDED_FLOORS})."
                )

            # 2. حساب مساحة الدور الأرضي (Footprint) والمساحة المبنية الإجمالية (BUA)
            floor_plate = valid_land_area * self.assumptions.SITE_COVERAGE_RATIO
            total_built_area = floor_plate * valid_floors

            # 3. حساب مساحات الحركة والجدران والمساحة النفعية الصافية
            net_ratio = self.assumptions.calculate_net_usable_ratio()
            net_usable_area = total_built_area * net_ratio
            circulation_area = total_built_area * self.assumptions.CIRCULATION_RATIO
            walls_area = total_built_area * self.assumptions.WALLS_RATIO

            # 4. توزيع المساحة النفعية على الفضاءات المعمارية الأساسية
            space_breakdown = {}
            for space_name, ratio in self.assumptions.SPACE_DISTRIBUTION_RATES.items():
                space_breakdown[space_name] = round(net_usable_area * ratio, 2)

            # 5. التكلفة التقديرية المبدئية للبناء
            estimated_cost = total_built_area * self.assumptions.COST_PER_SQM_BASE

            logger.info(
                f"تم توليد المخطط المعماري: مساحة الأرض {valid_land_area} م²، "
                f"إجمالي البناء {round(total_built_area, 2)} م² عبر {valid_floors} أدوار."
            )

            return {
                "land_area_sqm": valid_land_area,
                "num_floors": valid_floors,
                "ground_floor_footprint_sqm": round(floor_plate, 2),
                "total_built_area_sqm": round(total_built_area, 2),
                "net_usable_area_sqm": round(net_usable_area, 2),
                "circulation_area_sqm": round(circulation_area, 2),
                "walls_area_sqm": round(walls_area, 2),
                "estimated_cost_usd": round(estimated_cost, 2),
                "functional_space_breakdown": space_breakdown,
                "assumptions_used": self.assumptions.to_dict()
            }

        except Exception as e:
            logger.exception("حدث خطأ أثناء حساب المسقط المعماري في ArchitecturalEngine")
            raise CalculationError(
                message=f"فشل حساب المسقط المعماري وتوزيع المساحات: {str(e)}"
            )
