from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class BlueprintTypeEnum(str, Enum):
    ARCHITECTURAL = "architectural"
    STRUCTURAL = "structural"
    MEP = "mep"
    SITE_PLAN = "site_plan"
    NON_ENGINEERING = "non_engineering"


class GuardAnalysisResult(BaseModel):
    """نتيجة فحص حارس المخططات (Blueprint Guard)."""
    is_engineering_blueprint: bool = Field(
        ..., 
        description="هل المستند المرفوع مخطط هندسي أصيل؟"
    )
    confidence_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="درجة ثقة النموذج في القرر (0.0 إلى 1.0)"
    )
    detected_type: BlueprintTypeEnum = Field(
        default=BlueprintTypeEnum.NON_ENGINEERING, 
        description="نوع المخطط المكتشف"
    )
    rejection_reason: Optional[str] = Field(
        default=None, 
        description="سبب الرفض في حال كان المستند غير هندسي"
    )


class RoomDetails(BaseModel):
    """تفاصيل الغرفة المستخرجة من المخطط المعماري."""
    name: str = Field(..., description="اسم الفضاء أو الغرفة (مثل: مجلس، نوم، مطبخ)")
    estimated_area_sqm: float = Field(..., ge=0.0, description="المساحة التقديرية بالمتر المربع")
    dimensions_text: Optional[str] = Field(default=None, description="الأبعاد الظاهرة إن وجدت (مثل: 4x5)")


class AnalyzerResult(BaseModel):
    """النتائج الاستخراجية التفصيلية لمحتوى المخطط الهندسي."""
    blueprint_type: BlueprintTypeEnum = Field(..., description="نوع المخطط المحلل")
    total_estimated_area: float = Field(..., ge=0.0, description="إجمالي المساحة المقدرة")
    floors_detected: int = Field(default=1, ge=1, description="عدد الأدوار المكتشفة في الرسم")
    rooms: List[RoomDetails] = Field(default_factory=list, description="قائمة الغرف والفضاءات")
    structural_hints: Dict[str, Any] = Field(
        default_factory=dict, 
        description="تلميحات العناصر الإنشائية (الأعمدة، الجدران الحاملة)"
    )
    raw_ai_metadata: Dict[str, Any] = Field(
        default_factory=dict, 
        description="بيانات إضافية وصفية ممررة من النموذج"
    )
