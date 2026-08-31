#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
© 2026 PHOENIX & MIHNA AGENT PRO - STRUCTURAL DATA MODELS
نماذج البيانات والعقود الهندسية الخاصة بالتصميم والتقييم الإنشائي الأولي
===============================================================================
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class StructuralAssessmentResult(BaseModel):
    """
    نموذج مخرجات التقييم الإنشائي الأولي (Preliminary Structural Assessment Result Schema).
    يغلف نتائج حساب الأحمال الجاذبية، عدد الأعمدة، ومواصفات المواد الإنشائية الموصى بها.
    """

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
        extra="ignore"
    )

    factored_load_kn_m2: float = Field(
        ...,
        gt=0.0,
        description="الحمل التصميمي الأقصى الموزع لكل متر مربع (Ultimate Factored Load Wu) بالـ kN/m²"
    )

    total_gravity_load_kn: float = Field(
        ...,
        gt=0.0,
        description="إجمالي الحمل الجاذبي التصميمي للمنشأ الكامل بالـ kN"
    )

    estimated_columns_count: int = Field(
        ...,
        ge=4,
        description="العدد التقديري للأعمدة الإنشائية المطلوبة للمبنى (الحد الأدنى 4 أعمدة)"
    )

    load_per_column_kn: float = Field(
        ...,
        gt=0.0,
        description="متوسط الحمل المحوري المنقول للعمود الواحد شامل كافة الأدوار بالـ kN"
    )

    recommended_concrete: str = Field(
        ...,
        description="رتبة الخرسانة المسلحة الموصى بها (مثال: C30/37 f'c = 30 MPa)"
    )

    recommended_steel: str = Field(
        default="Grade 60 / FY 420 MPa",
        description="رتبة وعلامة حديد التسليح الموصى بها"
    )

    is_preliminary: bool = Field(
        default=True,
        description="مؤشر يحدد ما إذا كانت الحسابات أولية وتقديرية للمرحلة المفهومية"
    )

    structural_metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="بيانات وصفيّة إضافية حركية متعلقة بعناصر التحليل الإنشائي"
    )


class ColumnSectionEstimate(BaseModel):
    """
    نموذج أبعاد وقطاعات الأعمدة التقديرية (Column Dimensions Model).
    """

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    column_id: str = Field(..., description="معرف العمود الإنشائي (مثل C1, C2)")
    width_cm: float = Field(..., gt=0.0, description="عرض قطاع العمود بالسنتمتر")
    depth_cm: float = Field(..., gt=0.0, description="عمق قطاع العمود بالسنتمتر")
    rebar_count: int = Field(..., ge=4, description="عدد أسياخ حديد التسليح الطولي")
    rebar_diameter_mm: int = Field(..., ge=12, description="قطر أسياخ حديد التسليح بالمليمتر")


class FootingSectionEstimate(BaseModel):
    """
    نموذج أبعاد الأساسات والقواعد الخرسانية (Footing Dimensions Model).
    """

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    footing_id: str = Field(..., description="معرف القاعدة (مثل F1, F2)")
    length_m: float = Field(..., gt=0.0, description="طول القاعدة بالمتر")
    width_m: float = Field(..., gt=0.0, description="عرض القاعدة بالمتر")
    thickness_cm: float = Field(..., gt=0.0, description="سماكة القاعدة بالسنتمتر")
    steel_mesh_bottom: str = Field(..., description="شبكة التسليح السفلية (مثل T14@15cm)")
