#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
© 2026 PHOENIX & MIHNA AGENT PRO - ENTERPRISE AI FACADE ARCHITECTURE
الطبقة المركزية الموحدة لإدارة خدمات الذكاء الاصطناعي، خطط المشاريع والتسعير الديناميكي
===============================================================================
"""

from typing import Any, Dict, List, Optional
from ai.providers.gemini import GeminiProvider
from engineering.blueprint.validator import BlueprintValidator
from engineering.blueprint.guard import StrictBlueprintGuard
from engineering.architecture.engine import ArchitecturalEngine
from engineering.boq.engine import BOQEngine
from engineering.structural.preliminary import StructuralEngine
from engineering.sustainability.engine import SustainabilityEngine


class AIFacade:
    """Orchestrator الطبقة المركزية لتأطير العمليات المعقدة وتنفيذها بطلب واحد."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.provider = GeminiProvider(api_key=api_key)
        self.validator = BlueprintValidator()
        self.guard = StrictBlueprintGuard(self.provider)
        self.architecture = ArchitecturalEngine()
        self.boq = BOQEngine()
        self.structural = StructuralEngine()
        self.sustainability = SustainabilityEngine()

    def process_full_engineering_pipeline(self, file_bytes: bytes, mime_type: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """معالجة وفحص المخططات الهندسية وتوليد حسابات الكميات والاستدامة."""
        self.validator.validate(file_bytes, mime_type)
        guard_result = self.guard.inspect(file_bytes, mime_type)
        if not guard_result.get("is_valid_blueprint"):
            return {"success": False, "reason": guard_result.get("rejection_reason"), "stage": "GUARD_REJECTED"}

        area = float(metadata.get("land_area", 200.0))
        floors = int(metadata.get("floors", 1))

        arch_res = self.architecture.generate_layout(area, floors)
        boq_res = self.boq.calculate(built_area=arch_res["total_built_area_sqm"], floors=floors)
        struct_res = self.structural.assess(total_area=arch_res["total_built_area_sqm"], floors=floors)
        sust_res = self.sustainability.evaluate(total_built_area=arch_res["total_built_area_sqm"])

        return {
            "success": True,
            "security": guard_result,
            "architecture": arch_res,
            "boq": boq_res,
            "structural": struct_res,
            "sustainability": sust_res
        }

    def generate_architecture(self, req: Dict[str, Any]) -> Dict[str, Any]:
        """توليد هيكلية المشروع والمهام بناءً على مدخلات المستخدم والتوقيع الرقمي."""
        from utils import SecurityEngine

        project_name = req.get("project_name", "مشروع جديد")
        budget = float(req.get("budget", 3500))
        target_days = int(req.get("target_days", 30))
        domain = req.get("domain", "عام")
        tech_stack = req.get("tech_stack", "Flutter, Node.js, Supabase")
        risk = req.get("risk", "متوسط")

        # تقسيم التكلفة والمهام التقديرية للمشروع
        tasks = [
            {"task": "تحليل المتطلبات وتصميم واجهات المستخدم UI/UX", "cost": budget * 0.15, "days": max(2, int(target_days * 0.15)), "owner": "UI/UX Designer"},
            {"task": "إعداد قواعد البيانات وإدارة Cloud SQL & Supabase RLS", "cost": budget * 0.25, "days": max(3, int(target_days * 0.25)), "owner": "Backend Engineer"},
            {"task": "تطوير منطق التطبيق والواجهات الأساسية Front-End", "cost": budget * 0.35, "days": max(5, int(target_days * 0.35)), "owner": "Fullstack Developer"},
            {"task": "التكامل مع بوابات الدفع واختبارات الأمان والتوقيع HMAC", "cost": budget * 0.15, "days": max(3, int(target_days * 0.15)), "owner": "Security Specialist"},
            {"task": "النشر والإطلاق السحابي وتجهيز السيرفرات Cloud Run", "cost": budget * 0.10, "days": max(2, int(target_days * 0.10)), "owner": "DevOps Engineer"},
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

        # توليد التوقيع الرقمي لحماية الخطة من التلاعب
        plan["signature"] = SecurityEngine.generate_signature(plan)
        return plan

    # -------------------------------------------------------------------------
    # Static Utility Methods (لاستدعائها مباشرة دون الحاجة لـ Instance)
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

        valid_prices = [float(f['suggested_price']) for f in feedback_list if f.get('suggested_price') is not None]
        valid_ratings = [float(f['rating']) for f in feedback_list if f.get('rating') is not None]

        avg_price = sum(valid_prices) / len(valid_prices) if valid_prices else 29.0
        avg_rating = sum(valid_ratings) / len(valid_ratings) if valid_ratings else 5.0

        rec_monthly = int(round(avg_price))
        rec_yearly = int(round(rec_monthly * 12 * 0.80))  # خصم 20% للسنوي
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
    def execute_auto_checkout(user_email: str, plan_type: str = "monthly") -> Dict[str, Any]:
        """محاكاة وتنفيد الدفع الذكي وتفعيل الترقية تلقائياً للمستخدم."""
        from db import HybridDatabaseEngine

        role_name = "Pro Enterprise" if plan_type == "monthly" else "CEO Ultimate"
        HybridDatabaseEngine.update_subscription(user_email=user_email, is_subscribed=True, role=role_name)
        
        return {
            "status": "success",
            "message": f"تم تفعيل باقة {role_name} بنجاح للبريد {user_email}",
            "user_email": user_email,
            "plan_type": plan_type
        }
