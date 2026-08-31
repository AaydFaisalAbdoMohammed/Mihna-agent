from typing import Any, Dict, Optional


class EngineeringBaseException(Exception):
    """
    Base exception for all domain & engineering errors in Mihna-agent.
    يسمح بتمرير الرسالة وتفاصيل إضافية عن الخطأ لدعم الـ Logging و الـ API Responses.
    """
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """تحويل الاستثناء إلى Qualified Dictionary مخصص للـ API Responses."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


class ValidationError(EngineeringBaseException):
    """يُطلق عند وجود أخطاء العامة في المدخلات الهندسية أو البيانات المتوقعة."""
    pass


class FileValidationError(ValidationError):
    """يُطلق عند وجود خلل تقني في الملف (الحجم، الامتداد، Magic Bytes)."""
    pass


class BlueprintSecurityError(EngineeringBaseException):
    """يُطلق عندما يرفض حارس المخططات الملف لأسباب أمنية أو عدم مطابقته لمخطط هندسي."""
    pass


class AIProviderError(EngineeringBaseException):
    """يُطلق عند حدوث خطأ في الاتصال، معالجة الـ Prompts، أو استخراج JSON من مزود الذكاء الاصطناعي."""
    pass


class CalculationError(EngineeringBaseException):
    """يُطلق عند فشل الحسابات الهندسية أو مدخلات رياضية غير منطقية (مثل القسمة على صفر أو قيم سالبة)."""
    pass


class DomainRuleViolationError(EngineeringBaseException):
    """يُطلق عند انتهاك إحدى قواعد نطاق العمل (Business Domain Rules)."""
    pass
