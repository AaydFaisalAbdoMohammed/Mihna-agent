#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
© 2026 PHOENIX & MIHNA AGENT PRO - ARCHITECTURAL ASSUMPTIONS ENGINE
الثوابت والفرضيات الهندسية المعمارية لحساب نسب البناء والتغطية والتكاليف
===============================================================================
"""

from dataclasses import dataclass, field
from typing import Dict, Any
from engineering.shared.validation import CommonValidator


@dataclass(frozen=True)
class ArchitecturalAssumptions:
    """
    مجموعة الثوابت والفرضيات المعمارية الحاكمة لتوزيع المساحات والتكاليف المبدئية.
    تم تعيين الكائن كـ frozen=True لضمان ثبات البيانات (Immutability) أثناء الحسابات.
    """

    # نسبة التغطية المسموحة من مساحة الأرض (Site Coverage Ratio) - 65% افتراضياً
    SITE_COVERAGE_RATIO: float = 0.65

    # نسبة مساحات الحركة والخدمات (الممرات، السلالم، المصاعد) - 15% افتراضياً
    CIRCULATION_RATIO: float = 0.15

    # نسبة الجدران والقواطع من المساحة الإجمالية - 10% افتراضياً
    WALLS_RATIO: float = 0.10

    # التكلفة المرجعية الأساسية للبناء للعام 2026 (دولار / متر مربع)
    COST_PER_SQM_BASE: float = 350.0

    # الحد الأقصى المسموح لعدد الأدوار السكنية القياسية
    MAX_RECOMMENDED_FLOORS: int = 5

    # توزيع النسب التقريبية للفضاءات المعمارية القياسية داخل المبنى
    SPACE_DISTRIBUTION_RATES: Dict[str, float] = field(
        default_factory=lambda: {
            "living_and_reception": 0.40,  # المجالس وصالات المعيشة
            "bedrooms": 0.30,             # غرف النوم
            "services_kitchen_baths": 0.15, # المطبخ والحمامات
            "circulation_and_entry": 0.15   # الممرات والمدخل
        }
    )

    def __post_init__(self) -> None:
        """
        التحقق الصارم من سلامة الفرضيات الثابتة فور إنشاء الكائن.
        """
        CommonValidator.validate_percentage(self.SITE_COVERAGE_RATIO * 100, "SITE_COVERAGE_RATIO")
        CommonValidator.validate_percentage(self.CIRCULATION_RATIO * 100, "CIRCULATION_RATIO")
        CommonValidator.validate_percentage(self.WALLS_RATIO * 100, "WALLS_RATIO")
        CommonValidator.validate_positive_number(self.COST_PER_SQM_BASE, "COST_PER_SQM_BASE")

    def calculate_net_usable_ratio(self) -> float:
        """
        حساب نسبة المساحة الصافية القابلة للاستخدام الصريح بعد خصم الحركة والجدران.
        """
        net_ratio = 1.0 - (self.CIRCULATION_RATIO + self.WALLS_RATIO)
        return max(0.0, net_ratio)

    def to_dict(self) -> Dict[str, Any]:
        """
        تحويل الفرضيات إلى قاموس جاهز للعرض أو التضمين في تقارير API.
        """
        return {
            "site_coverage_ratio": self.SITE_COVERAGE_RATIO,
            "circulation_ratio": self.CIRCULATION_RATIO,
            "walls_ratio": self.WALLS_RATIO,
            "cost_per_sqm_base": self.COST_PER_SQM_BASE,
            "net_usable_ratio": round(self.calculate_net_usable_ratio(), 2),
            "space_distribution_rates": self.SPACE_DISTRIBUTION_RATES
        }
