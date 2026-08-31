# -*- coding: utf-8 -*-
"""
AI Module Initialization for Phoenix & Wakeel Mehna Pro
يوفر هذا الملف الواجهة الموحدة لخدمات الذكاء الاصطناعي مع آلية أمان وتوافق ذكية (Fallback Engine).
"""

import logging

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# آلية الاستيراد الآمن وتوفير PhoenixAI
# -----------------------------------------------------------------------------
PhoenixAI = None

try:
    # المحاولة الأولى: استيراد الواجهة الرئيسية AIFacade
    from ai.facade import AIFacade as PhoenixAI
except ImportError:
    try:
        # المحاولة الثانية: استيراد المزود الرئيسي GeminiProvider
        from ai.providers.gemini import GeminiProvider as PhoenixAI
    except ImportError:
        logger.warning("تعذر استيراد AIFacade أو GeminiProvider، تم تفعيل كلاس PhoenixAI الاحتياطي.")


# -----------------------------------------------------------------------------
# كلاس احتياطي (Fallback Class) لحماية التطبيق من الانهيار عند غياب الموديولات
# -----------------------------------------------------------------------------
if PhoenixAI is None:
    class SafePhoenixAI:
        """
        كلاس احتياطي يضم الخوارزميات والواجهات الأساسية لضمان عمل الواجهات والأقسام
        حتى في حال وجود مشكلة في استيراد خدمات الذكاء الاصطناعي.
        """
        @staticmethod
        def calculate_specialists_breakdown(budget: float, days: int, domain: str):
            budget = float(budget or 0)
            days = int(days or 1)
            
            # توزيع افتراضي موثوق للكوادر الهندسية
            return [
                {
                    "icon": "👷‍♂️",
                    "role": "مهندس موقع رئيسي (Site Engineer)",
                    "total_hours": days * 8,
                    "allocated_days": days,
                    "hourly_rate": round((budget * 0.40) / max(1, days * 8), 2),
                    "daily_rate": round((budget * 0.40) / max(1, days), 2),
                    "total_cost": round(budget * 0.40, 2),
                    "ratio_pct": 40
                },
                {
                    "icon": "📐",
                    "role": "مهندس تصميم واستشاري (Consultant)",
                    "total_hours": int(days * 4),
                    "allocated_days": max(1, int(days * 0.5)),
                    "hourly_rate": round((budget * 0.30) / max(1, days * 4), 2),
                    "daily_rate": round((budget * 0.30) / max(1, int(days * 0.5)), 2),
                    "total_cost": round(budget * 0.30, 2),
                    "ratio_pct": 30
                },
                {
                    "icon": "🔍",
                    "role": "مراقب جودة والسلامة (QA/QC Engineer)",
                    "total_hours": int(days * 4),
                    "allocated_days": max(1, int(days * 0.5)),
                    "hourly_rate": round((budget * 0.30) / max(1, days * 4), 2),
                    "daily_rate": round((budget * 0.30) / max(1, int(days * 0.5)), 2),
                    "total_cost": round(budget * 0.30, 2),
                    "ratio_pct": 30
                }
            ]

        async def generate_json(self, *args, **kwargs):
            return {}

        async def analyze_vision(self, *args, **kwargs):
            return {}

    PhoenixAI = SafePhoenixAI


# تصدير الكلاسات المتاحة رسمياً
__all__ = ["PhoenixAI"]
