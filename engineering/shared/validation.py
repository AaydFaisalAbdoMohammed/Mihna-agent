from typing import Union, List, Dict, Any, Optional
from engineering.shared.errors import ValidationError, CalculationError


class CommonValidator:
    """
    مجموعة من أدوات التحقق الموحدة للمحركات الهندسية والرياضية.
    تضمن الحماية من المدخلات غير المنطقية والقسمة على صفر والقيود الرياضية.
    """

    @staticmethod
    def validate_positive_number(val: Union[int, float], name: str) -> float:
        """
        التحقق من أن القيمة الرقمية أكبر تماماً من الصفر (Strictly Positive).
        تستخدم للمساحات، الأبعاد، والأحمال الهندسية.
        """
        if val is None or not isinstance(val, (int, float)):
            raise ValidationError(
                message=f"الحقل '{name}' يجب أن يكون قيمة رقمية.",
                details={"field_name": name, "provided_value": val}
            )
        
        if val <= 0:
            raise CalculationError(
                message=f"القيمة الخاصة بـ '{name}' يجب أن تكون أكبر من الصفر.",
                details={"field_name": name, "provided_value": val}
            )
        return float(val)

    @staticmethod
    def validate_non_negative_number(val: Union[int, float], name: str) -> float:
        """
        التحقق من أن القيمة الرقمية أكبر من أو تساوي الصفر (Non-negative).
        تستخدم للتكاليف المبدئية أو كميات المواد التي قد تكون صفرية.
        """
        if val is None or not isinstance(val, (int, float)):
            raise ValidationError(
                message=f"الحقل '{name}' يجب أن يكون قيمة رقمية.",
                details={"field_name": name, "provided_value": val}
            )
        
        if val < 0:
            raise CalculationError(
                message=f"القيمة الخاصة بـ '{name}' لا يمكن أن تكون سالبة.",
                details={"field_name": name, "provided_value": val}
            )
        return float(val)

    @staticmethod
    def validate_range(
        val: Union[int, float], 
        min_val: Union[int, float], 
        max_val: Union[int, float], 
        name: str
    ) -> float:
        """
        التحقق من وقوع القيمة ضمن مجالك المالي أو الهندسي المحدد (شامل الحدود).
        """
        if val is None or not isinstance(val, (int, float)):
            raise ValidationError(
                message=f"الحقل '{name}' يجب أن يكون قيمة رقمية.",
                details={"field_name": name, "provided_value": val}
            )

        if not (min_val <= val <= max_val):
            raise CalculationError(
                message=f"القيمة الخاصه بـ '{name}' يجب أن تكون حصراً بين {min_val} و {max_val}.",
                details={
                    "field_name": name, 
                    "provided_value": val, 
                    "min_boundary": min_val, 
                    "max_boundary": max_val
                }
            )
        return float(val)

    @staticmethod
    def validate_percentage(val: Union[int, float], name: str) -> float:
        """
        تحقق خاص بالنسب المئوية (من 0% إلى 100%).
        تستخدم لنظرية البناء (Site Coverage) أو نسب الإنجاز للمشاريع (Escrow Milestone).
        """
        return CommonValidator.validate_range(val, 0.0, 100.0, name)

    @staticmethod
    def validate_not_empty_list(val: List[Any], name: str) -> List[Any]:
        """
        التحقق من أن القائمة الممررة ليست فارغة وتحتوي على عناصر.
        تستخدم للتأكد من وجود عناصر هندسية (مثل قائمة الغرف أو الأعمدة المستخرجة).
        """
        if not isinstance(val, list) or len(val) == 0:
            raise ValidationError(
                message=f"القائمة الخاصة بـ '{name}' يجب ألا تكون فارغة وتتطلب عناصر فعالة.",
                details={"field_name": name, "provided_type": type(val).__name__}
            )
        return val

    @staticmethod
    def validate_required_keys(dictionary: Dict[str, Any], required_keys: List[str], context_name: str) -> Dict[str, Any]:
        """
        التحقق من وجود المفاتيح الإلزامية داخل القواميس المستخرجة من الـ AI JSON.
        """
        missing_keys = [key for key in required_keys if key not in dictionary or dictionary[key] is None]
        if missing_keys:
            raise ValidationError(
                message=f"بيانات '{context_name}' ناقصة وتفتقر إلى المفاتيح الإلزامية التالية: {', '.join(missing_keys)}",
                details={"context": context_name, "missing_keys": missing_keys}
            )
        return dictionary
