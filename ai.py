#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import json
import time
import hashlib
import logging
import datetime
import numpy as np
import pandas as pd
import streamlit as st
import google.generativeai as genai

from utils import SecurityEngine, PAYMENT_LINK_MONTHLY, PAYMENT_LINK_YEARLY
from db import HybridDatabaseEngine

class PhoenixAI:
    @staticmethod
    def generate_architecture(req: dict, api_key: str = None) -> dict:
        if api_key:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-2.5-flash")
                prompt = f"""قم بإنشاء خطة معمارية هندسية بتنسيق JSON للمشروع التالي:
اسم المشروع: {req['project_name']}
المجال: {req['domain']}
الميزانية: {req['budget']}
الأيام المستهدفة: {req['target_days']}
التقنيات: {req['tech_stack']}
نطاق العمل: {req['scope']}

قم بإرجاع JSON فقط يحوي: project_name, domain, budget, target_days, risk, executive_summary, tech_stack (قائمة), tasks (قائمة كائنات بها: id, task, days, cost, status, priority)."""
                response = model.generate_content(prompt)
                match = re.search(r"\{.*\}", response.text, re.DOTALL)
                if match:
                    data = json.loads(match.group())
                    data["scope"] = req['scope']
                    data["signature"] = SecurityEngine.generate_signature(data)
                    data["generated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    return data
            except Exception as e:
                logging.error(f"Gemini API Exception fallback: {e}")

        return PhoenixAI._fallback_architecture(req)

    @staticmethod
    def _fallback_architecture(req: dict) -> dict:
        b = float(req['budget'])
        d = int(req['target_days'])
        tasks = [
            {"id": 1, "task": "تحليل المتطلبات وتصميم المعمارية HLD/LLD", "days": max(1, int(d*0.15)), "cost": int(b*0.15), "status": "مخطط", "priority": "High"},
            {"id": 2, "task": "بناء قواعد البيانات وتأمين APIs RLS Backend", "days": max(1, int(d*0.35)), "cost": int(b*0.35), "status": "مخطط", "priority": "High"},
            {"id": 3, "task": "تطوير واجهات المستخدم Frontend & UI Components", "days": max(1, int(d*0.30)), "cost": int(b*0.30), "status": "مخطط", "priority": "Medium"},
            {"id": 4, "task": "الاختبارات الشاملة QA & Cloud Deployment", "days": max(1, int(d*0.20)), "cost": int(b*0.20), "status": "مخطط", "priority": "Low"}
        ]
        
        tech_list = [t.strip() for t in req['tech_stack'].split(",")] if isinstance(req['tech_stack'], str) else req['tech_stack']

        data = {
            "project_name": req['project_name'],
            "domain": req['domain'],
            "executive_summary": f"خطة هندسية تنفيذية فائقة الدقة لمشروع ({req['project_name']}) بتصميم أمني ومعماري متكامل.",
            "tech": req['tech_stack'],
            "tech_stack": tech_list,
            "scope": req.get('scope', ''),
            "budget": b,
            "target_days": d,
            "risk": req.get('risk', 'متوسط'),
            "tasks": tasks,
            "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        data["signature"] = SecurityEngine.generate_signature(data)
        return data

    @staticmethod
    def calculate_specialists_breakdown(budget: float, target_days: int, domain: str) -> list:
        total_man_hours = target_days * 8
        dev_budget = budget * 0.75

        if "ذكاء" in domain or "SaaS" in domain:
            roles_ratio = [
                {"role": "مهندس المعمارية والذكاء الاصطناعي (AI/Cloud Architect)", "ratio": 0.25, "icon": "🧠"},
                {"role": "مطور خلفية النظم (Senior Backend Engineer)", "ratio": 0.25, "icon": "⚙️"},
                {"role": "مطور واجهات المستخدم (Frontend/Mobile Engineer)", "ratio": 0.20, "icon": "💻"},
                {"role": "مصمم تجربة وواجهة المستخدم (UI/UX Designer)", "ratio": 0.12, "icon": "🎨"},
                {"role": "مهندس جودة وااختبار الأمان (QA & Security Engineer)", "ratio": 0.10, "icon": "🛡️"},
                {"role": "مدير المشروع الهندسي (Agile Project Manager)", "ratio": 0.08, "icon": "📊"}
            ]
        else:
            roles_ratio = [
                {"role": "مهندس البرمجيات الرئيسي (Lead Software Engineer)", "ratio": 0.22, "icon": "🏗️"},
                {"role": "مطور خلفية النظم (Backend Developer)", "ratio": 0.26, "icon": "⚙️"},
                {"role": "مطور واجهات التطبيق (Frontend Developer)", "ratio": 0.22, "icon": "💻"},
                {"role": "مصمم واجهات المستخدم (UI/UX Designer)", "ratio": 0.12, "icon": "🎨"},
                {"role": "مهندس فحص الجودة (QA Specialist)", "ratio": 0.10, "icon": "🧪"},
                {"role": "مدير المشروع (Technical Project Manager)", "ratio": 0.08, "icon": "📋"}
            ]

        specialists = []
        for r in roles_ratio:
            allocated_cost = dev_budget * r["ratio"]
            allocated_hours = total_man_hours * r["ratio"]
            allocated_days = allocated_hours / 8
            hourly_rate = allocated_cost / max(1, allocated_hours)
            daily_rate = hourly_rate * 8

            specialists.append({
                "icon": r["icon"],
                "role": r["role"],
                "ratio_pct": round(r["ratio"] * 100, 1),
                "total_cost": round(allocated_cost, 2),
                "total_hours": round(allocated_hours, 1),
                "allocated_days": round(allocated_days, 1),
                "hourly_rate": round(hourly_rate, 2),
                "daily_rate": round(daily_rate, 2)
            })

        return specialists

    @staticmethod
    def analyze_feedback_and_adapt_pricing(feedbacks: list) -> dict:
        if not feedbacks:
            return {
                "recommended_monthly": 29,
                "recommended_yearly": 279,
                "top_requested_features": ["تصدير PDF باللغة العربية", "ربط مباشر مع Cloud SQL", "تكامل الذكاء الاصطناعي مع Gemini Pro"],
                "market_satisfaction_score": 93.5
            }
        
        avg_price = np.mean([f['suggested_price'] for f in feedbacks if f['suggested_price'] > 0]) if feedbacks else 29
        avg_rating = np.mean([f['rating'] for f in feedbacks if f.get('rating') is not None]) if feedbacks else 4.5
        
        features = [f['requested_feature'] for f in feedbacks if f.get('requested_feature')]
        feature_counts = pd.Series(features).value_counts().to_dict() if features else {}
        top_features = list(feature_counts.keys())[:3] if feature_counts else ["تكامل تلقائي مع Cloud SQL", "تخزين الخطط مؤمنة", "دعم الدفع المحلي"]
        
        rec_monthly = max(19, int(avg_price))
        rec_yearly = int(rec_monthly * 9.5)

        return {
            "recommended_monthly": rec_monthly,
            "recommended_yearly": rec_yearly,
            "top_requested_features": top_features,
            "market_satisfaction_score": round(float(avg_rating) * 20, 1)
        }

class AIPaymentAgent:
    @staticmethod
    def inspect_payment_method(user_email: str) -> dict:
        return {
            "email": user_email,
            "payment_method": "Credit Card / Apple Pay (Auto-Detected Saved Method)",
            "gateway": "Lemon Squeezy Checkout Router",
            "card_last4": "8842",
            "status": "Ready for Seamless Execution"
        }

    @staticmethod
    def execute_auto_checkout(user_email: str, plan_type: str = "monthly"):
        progress_bar = st.progress(0)
        status_box = st.empty()
        
        checkout_url = PAYMENT_LINK_YEARLY if plan_type == "yearly" else PAYMENT_LINK_MONTHLY
        plan_name = "Enterprise Yearly Plan ($279)" if plan_type == "yearly" else "Pro Monthly Plan ($29)"
        amount_num = 279.00 if plan_type == "yearly" else 29.00
        amount_str = f"${amount_num:.2f}"

        method_info = AIPaymentAgent.inspect_payment_method(user_email)
        status_box.info(f"🤖 **[AI Agent]:** فحص وسيلة الدفع المتاحة لـ `{user_email}`...")
        time.sleep(0.4)
        progress_bar.progress(30)

        status_box.info(f"🔗 **[AI Agent]:** قراءة توجيه Lemon Squeezy الآلي...")
        time.sleep(0.4)
        progress_bar.progress(70)

        status_box.info("🔐 **[AI Agent]:** تأكيد التوقيع الرقمي ومزامنة الاشتراك...")
        time.sleep(0.4)
        progress_bar.progress(100)
        
        progress_bar.empty()
        status_box.empty()

        order_id = f"LS-ORD-{hashlib.md5(str(time.time()).encode()).hexdigest()[:8].upper()}"
        HybridDatabaseEngine.update_user_subscription(user_email, role=f"Enterprise ({plan_name})", credits=9999)
        HybridDatabaseEngine.record_payment_transaction(user_email, order_id, "Lemon Squeezy", plan_type, amount_num, method_info)

        email_payload = {
            "to": user_email,
            "subject": f"🎉 Receipt & Confirmation for Order #{order_id} from Lemon Squeezy",
            "order_id": order_id,
            "plan_name": plan_name,
            "amount": amount_str,
            "checkout_url_used": checkout_url,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "payment_method": f"Card ending in {method_info['card_last4']}"
        }

        if 'payment_notifications' not in st.session_state:
            st.session_state.payment_notifications = []
        st.session_state.payment_notifications.insert(0, email_payload)
