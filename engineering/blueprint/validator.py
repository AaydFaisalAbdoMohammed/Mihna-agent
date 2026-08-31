import logging
from typing import Optional, Set
from engineering.shared.errors import FileValidationError

logger = logging.getLogger(__name__)


class BlueprintValidator:
    """
    مكون فحص الأمان المبدئي والتحقق التقني من ملفات المخططات الهندسية.
    يقوم بالتحقق من الحجم، نوع الملف، ومطابقة التوقيع الرقمي (Magic Bytes) للملفات.
    """

    MAX_FILE_SIZE: int = 20 * 1024 * 1024  # الحد الأقصى 20 ميجابايت
    ALLOWED_MIMES: Set[str] = {
        "image/jpeg",
        "image/png",
        "image/webp",
        "application/pdf",
    }

    @staticmethod
    def detect_magic_bytes(data: bytes) -> Optional[str]:
        """
        التعرف على نوع الملف الأصلي بقرائة التوقيع الثنائي (Magic Bytes) لضمان عدم التلاعب بالامتداد.
        """
        if not data:
            return None

        # JPEG Magic Bytes
        if data.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"

        # PNG Magic Bytes
        if data.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"

        # PDF Magic Bytes
        if data.startswith(b"%PDF-"):
            return "application/pdf"

        # WebP Magic Bytes
        if len(data) >= 12 and data[0:4] == b"RIFF" and data[8:12] == b"WEBP":
            return "image/webp"

        return None

    def validate(self, file_bytes: bytes, mime_type: str) -> bool:
        """
        فحص الملف تقنياً والتأكد من مطابقتي للمعايير الأمنية والهندسية قبل إرساله للـ AI.
        """
        if not file_bytes:
            raise FileValidationError(
                message="ملف المخطط مفقود أو فارغ تماماً.",
                details={"provided_size": 0}
            )

        file_size = len(file_bytes)
        if file_size > self.MAX_FILE_SIZE:
            raise FileValidationError(
                message=f"حجم الملف ينتهك الحد الأقصى المسموح به وهو 20 ميجابايت.",
                details={
                    "file_size_bytes": file_size,
                    "max_allowed_bytes": self.MAX_FILE_SIZE,
                    "file_size_mb": round(file_size / (1024 * 1024), 2)
                }
            )

        # تنظيف وتحسين الـ MIME الممرر من المتصفح أو العميل
        normalized_mime = mime_type.lower().strip() if mime_type else ""

        # فحص توقيع الملف المباشر من الذاكرة (Magic Bytes)
        detected_mime = self.detect_magic_bytes(file_bytes)

        if not detected_mime:
            raise FileValidationError(
                message="فشل النظام في التعرف على التوقيع الرقمي للملف. قد يكون الملف تالفاً أو امتداده غير مدعوم.",
                details={"reported_mime": mime_type}
            )

        if detected_mime not in self.ALLOWED_MIMES:
            raise FileValidationError(
                message=f"نوع الملف المكتشف '{detected_mime}' غير مدعوم. الأنواع المسموحة فقط هي: PDF, PNG, JPEG, WEBP.",
                details={"detected_mime": detected_mime, "allowed_mimes": list(self.ALLOWED_MIMES)}
            )

        # في حال تم التلاعب باسم/نوع الملف بالمرسل وكان يختلف عن التوقيع الحقيقي المكتشف
        if normalized_mime and normalized_mime != detected_mime:
            logger.warning(
                f"تنبيه أمان: تم إرسال MIME برقم '{normalized_mime}' لكن التوقيع الرقمي الحقيقي هو '{detected_mime}'."
            )

        return True
