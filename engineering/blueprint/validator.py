from typing import Optional
from engineering.shared.errors import ValidationError

class BlueprintValidator:
    MAX_FILE_SIZE = 20 * 1024 * 1024
    ALLOWED_MIMES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}

    @staticmethod
    def detect_magic_bytes(data: bytes) -> Optional[str]:
        if data.startswith(b"\xff\xd8\xff"): return "image/jpeg"
        if data.startswith(b"\x89PNG\r\n\x1a\n"): return "image/png"
        if data.startswith(b"%PDF-"): return "application/pdf"
        if len(data) >= 12 and data[0:4] == b"RIFF" and data[8:12] == b"WEBP": return "image/webp"
        return None

    def validate(self, file_bytes: bytes, mime_type: str) -> bool:
        if not file_bytes or len(file_bytes) > self.MAX_FILE_SIZE:
            raise ValidationError("File missing or exceeds 20MB limit.")
        if mime_type not in self.ALLOWED_MIMES:
            raise ValidationError(f"Unsupported MIME type: {mime_type}")
        detected = self.detect_magic_bytes(file_bytes)
        if not detected or detected != mime_type:
            raise ValidationError("File signature (magic bytes) does not match reported MIME type.")
        return True
