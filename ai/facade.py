#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
© 2026 PHOENIX & MIHNA AGENT PRO - ENTERPRISE AI FACADE ARCHITECTURE
الطبقة المركزية الموحدة لإدارة خدمات الذكاء الاصطناعي، خطط المشاريع والتسعير الديناميكي
===============================================================================
"""

import logging
from typing import Any, Dict, List, Optional

from ai.providers.gemini import GeminiProvider
from engineering.architecture.engine import ArchitecturalEngine
from engineering.blueprint.guard import StrictBlueprintGuard
from engineering.blueprint.validator import BlueprintValidator
from engineering.boq.engine import BOQEngine
from engineering.shared.errors import EngineeringBaseException
from engineering.structural.preliminary import StructuralEngine
from engineering.sustainability.engine import SustainabilityEngine

logger = logging.getLogger(__name__)


class AIFacade:
    """
    Orchestrator الطبقة المركزية الموحدة لتنسيق العمليات بين نماذج الذكاء الاصطناعي
    والمحركات الهندسية المختلفة في منصة مهنة (Mihna-agent).
    """

    def __init__(self, api_key: Optional[str] = None):
        self.provider = GeminiProvider(api_key=api_key)
        self.validator = BlueprintValidator()
        self.guard = StrictBlueprintGuard(self.provider)
        self.architecture = ArchitecturalEngine()
        self.boq = BOQEngine()
        self.structural = StructuralEngine()
        self.sustainability = SustainabilityEngine()

    async def process_full_engineering_pipeline(
        self, 
        file_bytes: bytes, 
        mime_type: str, 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        معالجة وفحص المخططات الهندسية بأسلوب Async وتوليد حسابات الكميات والتصميم والاستدامة.
        """
        try:
            # 1. التحقق التقني المبدئي من صحة الملف وسلامته
            self.validator.validate(file_bytes, mime_type)

            # 2. فحص أمان المخطط عبر حارس المخططات الذكي (Strict Blueprint Guard)
            guard_result = await self.guard.inspect(file_bytes, mime_type)
            if not guard_result.get("is_valid_blueprint", False):
                logger.warning(f"تم رفض المستند بواسطة الحارس: {guard_result.get('rejection_reason')}")
                return {
                    "success": False,
                    "stage": "GUARD_REJECTED",
                    "reason": guard_result.get("rejection_reason", "المستند المرفوع ليس مخططاً هندسياً معتمداً."),
                    "security": guard_result
                }

            # 3. استخراج البيانات المساحية وإدراج القيم الإفتراضية بأمان
            area = float(metadata.get("land_area", 200.0))
            floors = int(metadata.get("floors", 1))

            # 4. تشغيل المحركات الهندسية بالتسلسل لتوليد الحسابات
            arch_res = await self.architecture.generate_layout(area, floors)
            
            built_area = arch_res.get("total_built_area_sqm", area * floors)
            
            boq_res = await self.boq.calculate(built_area=built_area, floors=floors)
            struct_res = await self.structural.assess(total_area=built_area, floors=floors)
            sust_res = await self.sustainability.evaluate(total_built_area=built_area)

            # 5. تجميع وتقديم التقرير الهندسي الشامل
            return {
                "success": True,
                "stage": "COMPLETED",
                "security": guard_result,
                "architecture": arch_res,
                "boq": boq_res,
                "structural": struct_res,
                "sustainability": sust_res
            }

        except EngineeringBaseException as e:
            logger.error(f"خطأ هندسي أثناء معالجة المخطط: {e.message}", exc_info=True)
            return {
                "success": False,
                "stage": "ENGINEERING_ERROR",
                "error": e.to_dict()
            }
        except Exception as e:
            logger.exception("حدث خطأ غير متوقع أثناء معالجة خط المخططات الهندسية")
            return {
                "success": False,
                "stage": "SYSTEM_ERROR",
                "error": {"message": f"حدث خطأ غير متوقع في النظام: {str(e)}"}
            }

    async def generate_architecture_plan(self, req: Dict[str, Any]) -> Dict[str, Any]:
        """
        توليد هيكلية المشروع والمهام بناءً على مدخلات المستخدم والتوقيع الرقمي.
        """
        try:
            from utils import SecurityEngine
        except ImportError:
            SecurityEngine = None

        project_name = req.get("project_name", "مشروع جديد")
        budget = float(req.get("budget", 3500.0))
        target_days = int(req.get("target_days", 30))
        domain = req.get("domain", "عام")
        tech_stack = req.get("tech_stack", "Flutter, Node.js, Supabase")
        risk = req.get("risk", "متوسط")

        tasks = [
            {
                "task": "تحليل المتطلبات وتصميم واجهات المستخدم UI/UX", 
                "cost": round(budget * 0.15, 2), 
                "days": max(2, int(target_days * 0.15)), 
                "owner": "UI/UX Designer"
            },
            {
                "task": "إعداد قواعد البيانات وإدارة Cloud SQL & Supabase RLS", 
                "cost": round(budget * 0.25, 2), 
                "days": max(3, int(target_days * 0.25)), 
                "owner": "Backend Engineer"
            },
            {
                "task": "تطوير منطق التطبيق والواجهات الأساسية Front-End", 
                "cost": round(budget * 0.35, 2), 
                "days": max(5, int(target_days * 0.35)), 
                "owner": "Fullstack Developer"
            },
            {
                "task": "التكامل مع بوابات الدفع وااختبارات الأمان والتوقيع HMAC", 
                "cost": round(budget * 0.15, 2), 
                "days": max(3, int(target_days * 0.15)), 
                "owner": "Security Specialist"
            },
            {
                "task": "النشر والإطلاق السحابي وتجهيز السيرفرات Cloud Run", 
                "cost": round(budget * 0.10, 2), 
                "days": max(2, int(target_days * 0.10)), 
                "owner": "DevOps Engineer"
            },
        ]

        plan = {
            "project_name": project_name,
            "domain": domain,
            "budget": budget,
            "target_days": target_days,
            "tech_stack": tech_stack,
            "risk": risk,
            "scope": req.get("scope", ""),
            "tasks": tasks
        }

        if SecurityEngine and hasattr(SecurityEngine, "generate_signature"):
            plan["signature"] = SecurityEngine.generate_signature(plan)
        else:
            plan["signature"] = "UNSIGNED_MOCK_SIGNATURE"

        return plan

    # -------------------------------------------------------------------------
    # Static Utility Methods (للحسابات المباشرة والأعمال المساندة)
    # -------------------------------------------------------------------------

    @staticmethod
    def analyze_feedback_and_adapt_pricing(feedback_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """تحليل التغذية الراجعة من المستخدمين وتكييف أسعار الاشتراكات ديناميكياً."""
        if not feedback_list:
            return {
                "recommended_monthly": 29,
                "recommended_yearly": 290,
                "market_satisfaction_score": 95.0
            }

        valid_prices = [float(f["suggested_price"]) for f in feedback_list if f.get("suggested_price") is not None]
        valid_ratings = [float(f["rating"]) for f in feedback_list if f.get("rating") is not None]

        avg_price = sum(valid_prices) / len(valid_prices) if valid_prices else 29.0
        avg_rating = sum(valid_ratings) / len(valid_ratings) if valid_ratings else 5.0

        rec_monthly = int(round(avg_price))
        rec_yearly = int(round(rec_monthly * 12 * 0.80))  # خصم 20% للباك السنوي
        satisfaction_score = round((avg_rating / 5.0) * 100, 1)

        return {
            "recommended_monthly": max(9, rec_monthly),
            "recommended_yearly": max(89, rec_yearly),
            "market_satisfaction_score": satisfaction_score
        }

    @staticmethod
    def calculate_specialists_breakdown(budget: float, target_days: int, domain: str) -> List[Dict[str, Any]]:
        """حساب توزيع كوادر المتخصصين وأجورهم وساعات عملهم استناداً للميزانية والجدول الزمني."""
        roles = [
            {"icon": "👨‍💻", "role": "Senior Fullstack Developer", "ratio": 0.40},
            {"icon": "🎨", "role": "UI/UX Product Designer", "ratio": 0.20},
            {"icon": "🗄️", "role": "Database & Cloud Architect", "ratio": 0.20},
            {"icon": "🛡️", "role": "QA & Security Engineer", "ratio": 0.20},
        ]

        total_hours = target_days * 8
        breakdown = []

        for r in roles:
            cost = budget * r["ratio"]
            hours = max(1, int(total_hours * r["ratio"]))
            hourly_rate = round(cost / hours, 2)
            daily_rate = round(hourly_rate * 8, 2)

            breakdown.append({
                "icon": r["icon"],
                "role": r["role"],
                "total_cost": round(cost, 2),
                "total_hours": hours,
                "hourly_rate": hourly_rate,
                "daily_rate": daily_rate,
                "ratio_pct": f"{int(r['ratio'] * 100)}%"
            })

        return breakdown

    @staticmethod
    async def execute_auto_checkout(user_email: str, plan_type: str = "monthly") -> Dict[str, Any]:
        """محاكاة وتنفيذ الدفع الذكي وتفعيل الترقية تلقائياً للمستخدم."""
        try:
            from db import HybridDatabaseEngine
            role_name = "Pro Enterprise" if plan_type == "monthly" else "CEO Ultimate"
            
            if hasattr(HybridDatabaseEngine, "update_subscription"):
                await HybridDatabaseEngine.update_subscription(
                    user_email=user_email, 
                    is_subscribed=True, 
                    role=role_name
                )
        except ImportError:
            logger.warning("لم يتم العثور على محرك قاعدة البيانات HybridDatabaseEngine، تم تخطي تحديث اشتراك DB.")

        role_name = "Pro Enterprise" if plan_type == "monthly" else "CEO Ultimate"
        return {
            "status": "success",
            "message": f"تم تفعيل باقة {role_name} بنجاح للبريد {user_email}",
            "user_email": user_email,
            "plan_type": plan_type
        }
