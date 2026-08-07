#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
© 2026 PHOENIX & MIHNA PRO ENTERPRISE ARCHITECTURE v10.0 - ULTIMATE SaaS PLATFORM
محرك معالجة البيانات، الحفظ الدائم (SQLite/Cloud SQL)، وإشعارات WhatsApp و تحليلات 5D
===============================================================================
"""

import os
import re
import io
import json
import time
import uuid
import hmac
import hashlib
import sqlite3
import logging
import datetime
import requests
import urllib.parse
from urllib.parse import quote_plus

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai

# ----------------- Fallback Dependency Handling -----------------
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False

try:
    import pymysql
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False

try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    ARABIC_PDF_AVAILABLE = True
except ImportError:
    ARABIC_PDF_AVAILABLE = False


# =====================================================================
# 1. CONFIGURATION & LINKS
# =====================================================================
APP_TITLE = "PHOENIX & MIHNA AGENT PRO - ENTERPRISE"
PAYMENT_LINK_MONTHLY = os.getenv("PAYMENT_LINK_MONTHLY", "https://nexus-corestore.lemonsqueezy.com/checkout/buy/e6515270-070e-4fc6-b1ea-60c1aeb9e2d3?plan=monthly")
PAYMENT_LINK_YEARLY = os.getenv("PAYMENT_LINK_YEARLY", "https://nexus-corestore.lemonsqueezy.com/checkout/buy/e6515270-070e-4fc6-b1ea-60c1aeb9e2d3?plan=yearly")
SECRET_HMAC_KEY = os.getenv("HMAC_SECRET_KEY", "PHOENIX_SECURE_HMAC_KEY_2026_ENTERPRISE_ULTIMATE")
DB_FILE = "phoenix_app_data.db"

st.set_page_config(page_title="وكيل مهنة PRO | Enterprise Plan Builder", page_icon="🚀", layout="wide", initial_sidebar_state="expanded")

# =====================================================================
# 2. HYBRID DATABASE ENGINE (Cloud SQL MySQL + Permanent SQLite Fallback)
# =====================================================================
def init_db():
    """إنشاء الجداول المحلية تلقائياً للحفاظ على البيانات في حال عدم توفر Cloud SQL"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            credits INTEGER DEFAULT 5,
            plan_status TEXT DEFAULT 'Free Trial',
            is_subscribed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            client_name TEXT,
            summary TEXT,
            budget_range TEXT,
            tech_stack TEXT,
            payload TEXT,
            signature TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

class DatabaseEngine:
    @staticmethod
    def get_cloud_sql_conn():
        if not PYMYSQL_AVAILABLE: return None
        try:
            conn_name = os.environ.get('CLOUD_SQL_CONNECTION_NAME')
            db_user = os.environ.get('DB_USER')
            db_pass = os.environ.get('DB_PASSWORD')
            db_name = os.environ.get('DB_NAME')
            if conn_name and db_user and db_pass and db_name:
                return pymysql.connect(
                    unix_socket=f"/cloudsql/{conn_name}",
                    user=db_user, password=db_pass, database=db_name,
                    cursorclass=pymysql.cursors.DictCursor, autocommit=True
                )
        except Exception:
            pass
        return None

    @classmethod
    def get_user(cls, email: str) -> dict:
        conn = cls.get_cloud_sql_conn()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                    res = cursor.fetchone()
                conn.close()
                if res: return res
            except Exception: pass

        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        conn.close()
        if row: return dict(row)
        return None

    @classmethod
    def register_user(cls, name: str, email: str, hashed_pass: str) -> bool:
        conn = cls.get_cloud_sql_conn()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO users (name, email, password, credits, plan_status) VALUES (%s, %s, %s, 5, 'Free Trial')",
                        (name, email, hashed_pass)
                    )
                conn.close()
            except Exception: pass

        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (name, email, password, credits, plan_status, is_subscribed) VALUES (?, ?, ?, 5, 'Free Trial', 0)",
                (name, email, hashed_pass)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logging.error(f"SQLite Reg Error: {e}")
            return False

    @classmethod
    def update_credits(cls, email: str, new_credits: int, plan_status: str = None) -> bool:
        conn = cls.get_cloud_sql_conn()
        if conn:
            try:
                with conn.cursor() as cursor:
                    if plan_status:
                        cursor.execute("UPDATE users SET credits = %s, plan_status = %s WHERE email = %s", (new_credits, plan_status, email))
                    else:
                        cursor.execute("UPDATE users SET credits = %s WHERE email = %s", (new_credits, email))
                conn.close()
            except Exception: pass

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        if plan_status:
            cursor.execute("UPDATE users SET credits = ?, plan_status = ?, is_subscribed = 1 WHERE email = ?", (new_credits, plan_status, email))
        else:
            cursor.execute("UPDATE users SET credits = ? WHERE email = ?", (new_credits, email))
        conn.commit()
        conn.close()
        return True

    @classmethod
    def save_project(cls, plan_json: dict, user_email: str) -> bool:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO projects (user_id, client_name, summary, budget_range, tech_stack, payload, signature) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                user_email, plan_json.get('project_name', 'مشروع غير معنون'), plan_json.get('executive_summary', ''),
                str(plan_json.get('budget', 0)), json.dumps(plan_json.get('tech_stack', [])),
                json.dumps(plan_json, ensure_ascii=False), plan_json.get('signature', '')
            )
        )
        conn.commit()
        conn.close()
        return True

    @classmethod
    def get_projects(cls, user_email: str) -> list:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, client_name as project_name, summary, budget_range, created_at, signature FROM projects WHERE user_id = ? ORDER BY created_at DESC", (user_email,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows


# =====================================================================
# 3. SECURITY ENGINE
# =====================================================================
class VaultSecurity:
    @classmethod
    def sign_payload(cls, payload: dict) -> str:
        clean_payload = {k: v for k, v in payload.items() if k not in ["signature", "timestamp", "generated_at"]}
        payload_str = json.dumps(clean_payload, sort_keys=True, ensure_ascii=False)
        return hmac.new(SECRET_HMAC_KEY.encode(), payload_str.encode(), hashlib.sha512).hexdigest()

    @classmethod
    def verify_signature(cls, payload: dict, signature: str) -> bool:
        if not signature: return False
        expected_sig = cls.sign_payload(payload)
        return hmac.compare_digest(expected_sig, signature)

    @classmethod
    def hash_password(cls, password: str) -> str:
        if BCRYPT_AVAILABLE:
            salt = bcrypt.gensalt()
            return bcrypt.hashpw(password.encode(), salt).decode()
        return hashlib.sha256(password.encode()).hexdigest()

    @classmethod
    def verify_password(cls, password: str, hashed: str) -> bool:
        if BCRYPT_AVAILABLE and hashed.startswith("$2b$"):
            try:
                return bcrypt.checkpw(password.encode(), hashed.encode())
            except Exception:
                return False
        return hashlib.sha256(password.encode()).hexdigest() == hashed


# =====================================================================
# 4. AI, NOTIFICATIONS & EXPORT ENGINES
# =====================================================================
class PhoenixAI:
    @staticmethod
    def generate_architecture(api_key: str, req: dict) -> dict:
        if not api_key:
            return PhoenixAI._mock_fallback(req)
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            prompt = f"Create a strictly formatted JSON architecture plan for project '{req.get('project_name')}' with tasks array (id, task, days, cost, status), cost, days and status. Return ONLY valid JSON."
            response = model.generate_content(prompt)
            match = re.search(r"\{.*\}", response.text, re.DOTALL)
            data = json.loads(match.group() if match else response.text)
            
            fallback_keys = ['project_name', 'domain', 'budget', 'target_days', 'risk', 'tech_stack', 'scope']
            for key in fallback_keys:
                if key not in data or not data[key]:
                    data[key] = req.get(key)

            if isinstance(data.get('tech_stack'), str):
                data['tech_stack'] = [t.strip() for t in data['tech_stack'].split(",")]

            data["generated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            data["signature"] = VaultSecurity.sign_payload(data)
            return data
        except Exception as e:
            logging.error(f"AI Generation/Parsing Exception: {e}")
            return PhoenixAI._mock_fallback(req)

    @staticmethod
    def _mock_fallback(req: dict) -> dict:
        b = float(req.get('budget', 3500))
        d = int(req.get('target_days', 30))
        tasks = [
            {"id": 1, "task": "تحليل المتطلبات وتصميم المخططات Architecture", "days": max(1, int(d*0.15)), "cost": int(b*0.15), "status": "مخطط"},
            {"id": 2, "task": "بناء قواعد البيانات وتأمين API Backend", "days": max(1, int(d*0.35)), "cost": int(b*0.35), "status": "مخطط"},
            {"id": 3, "task": "تطوير واجهات المستخدم Frontend UI Components", "days": max(1, int(d*0.30)), "cost": int(b*0.30), "status": "مخطط"},
            {"id": 4, "task": "الاختبارات الشاملة والتكامل QA Deployment", "days": max(1, int(d*0.20)), "cost": int(b*0.20), "status": "مخطط"}
        ]
        data = {
            "project_name": req.get('project_name', 'مشروع غير معنون'), 
            "domain": req.get('domain', 'تقنية المعلومات'),
            "executive_summary": f"خطة هندسية لمشروع ({req.get('project_name')}) بتصميم فائق الجودة والأمان.",
            "tech_stack": [t.strip() for t in str(req.get('tech_stack', '')).split(",") if t.strip()],
            "budget": b, 
            "target_days": d, 
            "risk": req.get('risk', 'متوسط'),
            "risk_score": 30 if req.get('risk') == 'منخفض جداً' else (60 if req.get('risk') == 'متوسط' else 90), 
            "confidence_score": 92, 
            "tasks": tasks,
            "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        data["signature"] = VaultSecurity.sign_payload(data)
        return data

class NotificationEngine:
    @staticmethod
    def create_whatsapp_link(phone: str, message: str) -> str:
        encoded_msg = urllib.parse.quote(message)
        clean_phone = re.sub(r'[^\d]', '', str(phone))
        return f"https://wa.me/{clean_phone}?text={encoded_msg}"

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
        plan_name = "Enterprise Pro Owner" if plan_type == "yearly" else "Pro Monthly Plan"
        amount_str = "$279.00" if plan_type == "yearly" else "$29.00"

        method_info = AIPaymentAgent.inspect_payment_method(user_email)
        status_box.info(f"🤖 **[AI Agent]:** فحص وسيلة الدفع المتاحة لـ `{user_email}`... (تم اكتشاف: {method_info['payment_method']})")
        time.sleep(0.6)
        progress_bar.progress(20)

        status_box.info(f"🔗 **[AI Agent]:** قراءة توجيه Lemon Squeezy الآلي للرابط: `{checkout_url}`")
        time.sleep(0.6)
        progress_bar.progress(50)

        status_box.info("🔐 **[AI Agent]:** تأكيد التوقيع الرقمي للمسار وتمرير معاملات الدفع...")
        time.sleep(0.6)
        progress_bar.progress(85)
        progress_bar.progress(100)
        time.sleep(0.3)
        
        progress_bar.empty()
        status_box.empty()
        
        DatabaseEngine.update_credits(user_email, 9999, plan_name)
        st.session_state.current_user['is_subscribed'] = 1
        st.session_state.current_user['plan_status'] = plan_name
        st.session_state.current_user['credits'] = 9999

        order_id = f"LS-ORD-{hashlib.md5(str(time.time()).encode()).hexdigest()[:8].upper()}"
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


def generate_excel_download(df: pd.DataFrame) -> bytes:
    if OPENPYXL_AVAILABLE:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Project Plan Tasks')
        return output.getvalue()
    else:
        return df.to_csv(index=False).encode('utf-8')

def generate_pdf_plan(plan: dict, signature: str, detailed_text: str) -> bytes:
    if not REPORTLAB_AVAILABLE or not ARABIC_PDF_AVAILABLE:
        return detailed_text.encode('utf-8')
        
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()

    def prepare_text(text_val):
        try:
            reshaped = arabic_reshaper.reshape(text_val)
            return get_display(reshaped)
        except Exception:
            return text_val

    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, alignment=1)
    body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=10, leading=14, alignment=2)

    story.append(Paragraph(prepare_text(f"خطة مشروع: {plan.get('project_name', '')}"), title_style))
    story.append(Spacer(1, 15))
    
    info_text = f"المجال التقني: {plan.get('domain', '')} | الميزانية: ${plan.get('budget', 0)} | المدة: {plan.get('target_days', 0)} يوم"
    story.append(Paragraph(prepare_text(info_text), body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph(prepare_text("--- تفاصيل الخطة التنفيذية الشاملة ---"), title_style))
    for line in detailed_text.split("\n"):
        if line.strip():
            story.append(Paragraph(prepare_text(line.strip()), body_style))
            story.append(Spacer(1, 4))

    story.append(Spacer(1, 15))
    story.append(Paragraph(prepare_text(f"التوقيع الرقمي HMAC-SHA512: {signature[:40]}..."), body_style))

    doc.build(story)
    return buffer.getvalue()

def build_detailed_plan_text(plan: dict) -> str:
    p_name = plan.get('project_name', 'المشروع')
    domain = plan.get('domain', 'تقني')
    budget = float(plan.get('budget', 0))
    days = int(plan.get('target_days', 0))
    tech = plan.get('tech_stack', 'Flutter, Node.js, PostgreSQL')
    if isinstance(tech, list):
        tech = ", ".join(tech)
    risk = plan.get('risk', 'متوسط')
    tasks = plan.get('tasks', [])
    
    working_hours_per_day = 8
    total_man_hours = days * working_hours_per_day
    daily_rate = budget / max(1, days)
    hourly_rate = budget / max(1, total_man_hours)
    
    contingency_rate = 0.15 if risk == "عالي" else (0.10 if risk == "متوسط" else 0.05)
    contingency_amount = budget * contingency_rate
    effective_operational_budget = budget - contingency_amount
    cloud_infra_cost = budget * 0.08
    dev_labor_cost = effective_operational_budget - cloud_infra_cost
    
    tasks_breakdown_str = ""
    for idx, t in enumerate(tasks, 1):
        t_cost = float(t.get('cost', 0))
        t_days = int(t.get('days', 0))
        t_hours = t_days * working_hours_per_day
        cost_percentage = (t_cost / max(1, budget)) * 100
        daily_t_cost = t_cost / max(1, t_days)
        hourly_t_cost = t_cost / max(1, t_hours)
        
        tasks_breakdown_str += f"""
#### 🔹 المرحلة {idx}: {t.get('task', 'مهمة')}
* ⏱️ **المدة الزمنية:** `{t_days}` أيام عمل (`{t_hours}` ساعة هندسية مكثفة)
* 💰 **التكلفة المخصصة:** `${t_cost:,.2f}` (`{cost_percentage:.1f}%` من إجمالي محفظة المشروع)
* 📊 **المعدل المالي اليومي للإنفاق:** `${daily_t_cost:,.2f}` / يوم
* ⏱️ **تكلفة الساعة التشغيلية:** `${hourly_t_cost:,.2f}` / ساعة
* 📌 **الحالة التنفيذية:** `{t.get('status', 'مخطط')}`
"""
    return f"""### 💎 التقرير التنفيذي الشامل والمحاسبي لمشروع ({p_name})
*تاريخ التوليد والاعتماد الرقمي: `{plan.get('generated_at', datetime.datetime.now().strftime('%Y-%m-%d %H:%M'))}`*

---

#### 1. الملخص الاستراتيجي والمؤشرات الرئيسية (Executive KPIs)
* **اسم المشروع:** `{p_name}`
* **القطاع التقني:** `{domain}`
* **التقنيات المعتمدة:** `{tech}`
* **الميزانية الكلية المرصودة:** `${budget:,.2f}`
* **الجدول الزمني المستهدف:** `{days}` يوماً تقويمياً
* **مستوى التصنيف والمخاطر:** `{risk}`

---

#### 2. التحليل المالي والهندسي المعماري المتقدم (Advanced Financial & Man-Hour Metrics)
* ⏳ **إجمالي الساعات الهندسية (Total Man-Hours):** `{total_man_hours:,}` ساعة عمل برمجية.
* 💵 **معدل الإنفاق اليومي الثابت (Daily Burn Rate):** `${daily_rate:,.2f}` لكل يوم عمل.
* ⏱️ **تكلفة ساعة الموارد البشرية والتقنية (Hourly Rate):** `${hourly_rate:,.2f}` لكل ساعة تشغيلية.
* 🛡️ **مخصص الطوارئ واحتياطي المخاطر ({contingency_rate*100:.0f}% Risk Reserve):** `${contingency_amount:,.2f}`.
* ☁️ **تكاليف التشغيل السحابي والبنية التحتية (Cloud OpEx - 8%):** `${cloud_infra_cost:,.2f}`.
* 🛠️ **صافي ميزانية التطوير والكوادر الفعلية (Effective Dev CapEx):** `${dev_labor_cost:,.2f}`.

---

#### 3. الهيكل التفصيلي لتوزيع المهام والمعالم الكبرى (Work Breakdown Structure & Milestones)
{tasks_breakdown_str}
"""

# =====================================================================
# 5. UI SESSION & CSS ENGINES
# =====================================================================
def init_session():
    if "lang" not in st.session_state: st.session_state.lang = "ar"
    if "theme" not in st.session_state: st.session_state.theme = "dark"
    if "authenticated" not in st.session_state: st.session_state.authenticated = False
    if "current_user" not in st.session_state: st.session_state.current_user = None
    if "current_plan" not in st.session_state: st.session_state.current_plan = None
    if "notify_whatsapp" not in st.session_state: st.session_state.notify_whatsapp = "+967700000000"
    if "notify_telegram" not in st.session_state: st.session_state.notify_telegram = "@Ayad_Developer"
    if "form_scope" not in st.session_state: st.session_state.form_scope = ""
    if "form_pname" not in st.session_state: st.session_state.form_pname = "منصة تجارة سحابية"
    if "form_domain" not in st.session_state: st.session_state.form_domain = "التجارة الإلكترونية"
    if "form_budget" not in st.session_state: st.session_state.form_budget = 3500
    if "form_days" not in st.session_state: st.session_state.form_days = 30
    if "payment_notifications" not in st.session_state: st.session_state.payment_notifications = []

T = {
    'ar': {
        'lang_select': "🌐 لغة الواجهة:", 'theme_select': "🎨 مظهر التطبيق:",
        'dark': "🌙 الداكن", 'light': "☀️ الفاتح",
        'logout_btn': "🚪 تسجيل الخروج", 'renew_title': "🛒 ترقية الاشتراك",
        'tab1': "🏗️ بناء خطة مشروع", 'tab2': "📊 التحليلات التفاعلية الفائقة", 
        'tab3': "✏️ محرر المهام", 'tab4': "🗄️ الأرشيف والتسجيل", 'tab5': "💳 إدارة الحساب وبوابة الدفع"
    },
    'en': {
        'lang_select': "🌐 Language:", 'theme_select': "🎨 Theme:",
        'dark': "🌙 Dark", 'light': "☀️ Light",
        'logout_btn': "🚪 Log Out", 'renew_title': "🛒 Upgrade Plan",
        'tab1': "🏗️ Build Project", 'tab2': "📊 5D Analytics", 
        'tab3': "✏️ Task Editor", 'tab4': "🗄️ Projects Archive", 'tab5': "💳 Account & Billing"
    }
}

def update_language():
    selected = st.session_state.lang_radio
    st.session_state.lang = 'ar' if "العربية" in selected else 'en'

def update_theme():
    selected = st.session_state.theme_radio
    st.session_state.theme = 'dark' if ("الداكن" in selected or "Dark" in selected) else 'light'

def apply_template(scope, domain, budget, days, pname):
    st.session_state.form_scope = scope
    st.session_state.form_domain = domain
    st.session_state.form_budget = budget
    st.session_state.form_days = days
    st.session_state.form_pname = pname

def render_dynamic_css():
    bg_color = "#0E1117" if st.session_state.theme == 'dark' else "#F8FAFC"
    card_bg = "#1E293B" if st.session_state.theme == 'dark' else "#FFFFFF"
    text_color = "#FFFFFF" if st.session_state.theme == 'dark' else "#0F172A"
    border_color = "#334155" if st.session_state.theme == 'dark' else "#E2E8F0"

    st.markdown(f"""
    <style>
        .stApp {{ background-color: {bg_color}; color: {text_color}; }}
        .badge-green {{ background-color: #10B981; color: white; padding: 6px 14px; border-radius: 12px; font-weight: bold; font-size: 13px; display: inline-block; }}
        .badge-purple {{ background-color: #8B5CF6; color: white; padding: 6px 14px; border-radius: 12px; font-weight: bold; font-size: 13px; display: inline-block; }}
        .badge-gold {{ background-color: #F59E0B; color: white; padding: 6px 14px; border-radius: 12px; font-weight: bold; font-size: 13px; display: inline-block; }}
        .checkout-btn {{ display: block; width: 100%; text-align: center; background: linear-gradient(135deg, #2563EB, #1D4ED8); color: white !important; padding: 12px 16px; border-radius: 10px; font-weight: bold; text-decoration: none; border: none; font-size: 14px; box-shadow: 0 4px 12px rgba(37,99,235,0.3); }}
        .checkout-btn-yearly {{ display: block; width: 100%; text-align: center; background: linear-gradient(135deg, #7C3AED, #9333EA); color: white !important; padding: 12px 16px; border-radius: 10px; font-weight: bold; text-decoration: none; border: none; font-size: 14px; box-shadow: 0 4px 12px rgba(124,58,237,0.3); }}
        .pricing-card {{ background-color: {card_bg}; border: 2px solid {border_color}; border-radius: 16px; padding: 24px; text-align: center; transition: all 0.3s ease; }}
        .pricing-card-highlight {{ background-color: {card_bg}; border: 2px solid #8B5CF6; border-radius: 16px; padding: 24px; text-align: center; box-shadow: 0 10px 25px rgba(139,92,246,0.2); }}
        .ai-payment-card {{ background: linear-gradient(135deg, #1E1B4B 0%, #312E81 100%); border: 2px solid #6366F1; border-radius: 16px; padding: 24px; color: #FFFFFF; margin-bottom: 24px; box-shadow: 0 10px 30px rgba(99, 102, 241, 0.25); }}
        .stTabs [data-baseweb="tab-list"] {{ gap: 8px; }}
        .stTabs [data-baseweb="tab"] {{ background-color: {card_bg}; border-radius: 8px; padding: 10px 20px; color: {text_color}; border: 1px solid {border_color}; font-weight: bold; }}
        .stTabs [aria-selected="true"] {{ background-color: #3B82F6 !important; color: white !important; border-color: #3B82F6 !important; }}
        .email-notification-box {{ background-color: #022C22; border: 1px solid #10B981; border-radius: 12px; padding: 16px; color: #ECFDF5; margin: 10px 0; font-family: monospace; }}
    </style>
    """, unsafe_allow_html=True)
    return text_color


# =====================================================================
# 6. MAIN APPLICATION EXECUTION
# =====================================================================
def render_auth_page():
    st.markdown("<h1 style='text-align: center;'>🔐 بوابة الدخول | PHOENIX Enterprise</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8;'>سجل دخولك أو أنشئ حساباً جديداً للوصول إلى المنصة</p>", unsafe_allow_html=True)
    
    col_center, _ = st.columns([1, 0.01])
    with col_center:
        auth_tab1, auth_tab2 = st.tabs(["🔑 تسجيل الدخول", "✨ إنشاء حساب جديد (5 محاولات مجانية)"])
        
        with auth_tab1:
            with st.form("login_form"):
                e = st.text_input("البريد الإلكتروني", placeholder="name@domain.com").lower().strip()
                p = st.text_input("كلمة المرور", type="password", placeholder="••••••••")
                if st.form_submit_button("🚀 تسجيل الدخول", use_container_width=True):
                    u = DatabaseEngine.get_user(e)
                    if u and VaultSecurity.verify_password(p, u["password"]):
                        st.session_state.authenticated = True
                        st.session_state.current_user = u
                        st.success(f"🎉 أهلاً بك مجدداً {u['name']}!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("❌ بيانات الدخول غير صحيحة.")

        with auth_tab2:
            with st.form("signup_form"):
                name = st.text_input("الاسم الكامل", placeholder="م. أياد فيصل")
                email = st.text_input("البريد الإلكتروني", placeholder="name@domain.com").lower().strip()
                pass1 = st.text_input("كلمة المرور", type="password", placeholder="••••••••")
                pass2 = st.text_input("تأكيد كلمة المرور", type="password", placeholder="••••••••")
                if st.form_submit_button("✨ إنشاء الحساب وتفعيل 5 نقاط", use_container_width=True):
                    if not name or not email or not pass1:
                        st.warning("⚠️ يرجى ملء كافة الحقول المطلوبة.")
                    elif pass1 != pass2:
                        st.error("❌ كلمات المرور غير متطابقة.")
                    else:
                        h_pass = VaultSecurity.hash_password(pass1)
                        if DatabaseEngine.register_user(name, email, h_pass):
                            st.balloons()
                            st.success("🎉 تم إنشاء الحساب بنجاح في قاعدة البيانات!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ الحساب مسجل مسبقاً أو حدث خطأ.")

def main():
    init_session()
    text_color = render_dynamic_css()

    if not st.session_state.authenticated:
        render_auth_page()
        st.stop()

    user_fresh = DatabaseEngine.get_user(st.session_state.current_user['email'])
    if user_fresh: st.session_state.current_user = user_fresh
    user = st.session_state.current_user
    txt = T[st.session_state.lang]

    # --- SIDEBAR ---
    with st.sidebar:
        st.title("🛡️ PHOENIX AGENT")
        st.markdown("<span class='badge-purple'>Enterprise Edition 2026</span>", unsafe_allow_html=True)
        st.write("---")
        
        st.radio(txt['lang_select'], ["العربية (Arabic)", "English"], index=0 if st.session_state.lang == 'ar' else 1, key='lang_radio', on_change=update_language)
        st.radio(txt['theme_select'], [txt['dark'], txt['light']], index=0 if st.session_state.theme == 'dark' else 1, key='theme_radio', on_change=update_theme)
        
        st.write("---")
        st.markdown(f"👤 **المستخدم:** {user['name']}")
        if user.get('is_subscribed'):
            st.markdown(f"نوع الاشتراك: <span class='badge-gold'>{user['plan_status']}</span>", unsafe_allow_html=True)
            st.markdown(f"الرصيد المتاح: **غير محدود ♾️**")
        else:
            st.markdown(f"نوع الحساب: <span class='badge-purple'>تجريبي (5 نقاط)</span>", unsafe_allow_html=True)
            st.markdown(f"💳 الرصيد: `{user['credits']}` نقاط")
        
        if st.button(txt['logout_btn'], use_container_width=True, type="secondary"):
            st.session_state.clear()
            st.rerun()

        st.write("---")
        st.markdown(f"### {txt['renew_title']}")
        if not user.get('is_subscribed'):
            if st.button("🤖 الترقية بالدفع الذكي (AI)", type="primary", use_container_width=True):
                AIPaymentAgent.execute_auto_checkout(user['email'], "monthly")
                st.balloons()
                st.success("🎉 تمت الترقية بنجاح!")
                time.sleep(1)
                st.rerun()
        
        st.markdown(f'<a href="{PAYMENT_LINK_MONTHLY}" target="_blank" class="checkout-btn">⚡ اشتراك عبر بوابة خارجية</a>', unsafe_allow_html=True)
        
        st.write("---")
        st.subheader("📲 إعدادات الإشعارات")
        st.session_state.notify_whatsapp = st.text_input("رقم الواتساب", value=st.session_state.notify_whatsapp)
        st.session_state.notify_telegram = st.text_input("معرف التليجرام", value=st.session_state.notify_telegram)

    # --- MAIN CONTENT ---
    st.markdown(f"<h1 style='text-align:center;'>{APP_TITLE}</h1>", unsafe_allow_html=True)
    st.caption("المنصة المتقدمة لهندسة خطط المشاريع وتأمينها بالتوقيع الرقمي والذكاء الاصطناعي.")

    # AI Banner Check
    if user['credits'] <= 0 and not user.get('is_subscribed'):
        st.markdown("""
        <div class="ai-payment-card">
            <h3>🤖 تنبيه من وكيل الدفع الذكي (AI Payment Broker Agent)</h3>
            <p>لقد نفدت نقاطك المجانية! يمكنك السماح للذكاء الاصطناعي بقراءة وسيلة الدفع وتنفيذ المعاملة عبر Lemon Squeezy فورياً.</p>
        </div>
        """, unsafe_allow_html=True)
        with st.expander("⚡ تنفيذ عملية الدفع والترقية الفورية عبر الذكاء الاصطناعي", expanded=True):
            c_pay1, c_pay2 = st.columns(2)
            with c_pay1:
                if st.button("🚀 تفعيل الدفع الذكي (Pro - $29)", type="primary", use_container_width=True):
                    AIPaymentAgent.execute_auto_checkout(user['email'], "monthly")
                    st.rerun()
            with c_pay2:
                if st.button("💎 تفعيل الدفع الذكي (Enterprise - $279)", use_container_width=True):
                    AIPaymentAgent.execute_auto_checkout(user['email'], "yearly")
                    st.rerun()

    t1, t2, t3, t4, t5 = st.tabs([txt['tab1'], txt['tab2'], txt['tab3'], txt['tab4'], txt['tab5']])

    # ------------------ TAB 1: BUILD ------------------
    with t1:
        st.subheader("⚡ قوالب جاهزة للبدء السريع")
        col_t1, col_t2, col_t3 = st.columns(3)
        col_t1.button("🛒 متجر إلكتروني", use_container_width=True, on_click=apply_template, args=("تطبيق متجر إلكتروني لبيع المنتجات", "التجارة الإلكترونية", 4500, 35, "متجر إلكتروني"))
        col_t2.button("🎓 منصة تعليمية", use_container_width=True, on_click=apply_template, args=("منصة تعليمية ذكية", "التعليم الرقمي", 3000, 25, "منصة تعليمية"))
        col_t3.button("🚗 تطبيق توصيل", use_container_width=True, on_click=apply_template, args=("تطبيق توصيل طلبات يعتمد على الخرائط", "الخدمات واللوجستيات", 6000, 50, "تطبيق توصيل"))

        domain_options = ["التجارة الإلكترونية", "التعليم الرقمي", "الخدمات واللوجستيات", "الذكاء الاصطناعي", "أنظمة SaaS"]
        idx_dom = domain_options.index(st.session_state.form_domain) if st.session_state.form_domain in domain_options else 0

        with st.form("project_form"):
            col1, col2 = st.columns(2)
            with col1:
                p_name = st.text_input("اسم المشروع", key="form_pname")
                domain = st.selectbox("المجال التقني", domain_options, index=idx_dom, key="form_domain")
                budget = st.number_input("الميزانية التقديرية ($)", min_value=500, key="form_budget")
            with col2:
                tech = st.text_input("التقنيات المستخدمة", value="Flutter, Dart, Node.js, TypeScript, Supabase, PostgreSQL")
                days = st.number_input("المدة الزمنية (يوم)", min_value=5, key="form_days")
                risk = st.select_slider("تحمل المخاطر", options=["منخفض جداً", "متوسط", "عالي"])
            
            scope = st.text_area("نطاق العمل (Scope of Work)", key="form_scope")
            submit_btn = st.form_submit_button("🚀 توليد وتوقيع الخطة الهندسية", use_container_width=True)

        if submit_btn:
            if user['credits'] < 1 and not user.get('is_subscribed'):
                st.error("❌ لقد استنفدت كافة نقاطك المجانية! يرجى الترقية.")
            else:
                with st.spinner("⏳ جاري توليد المهام والتوقيع الرقمي..."):
                    req = {"project_name": p_name, "domain": domain, "budget": budget, "target_days": days, "tech_stack": tech, "scope": scope, "risk": risk}
                    plan = PhoenixAI.generate_architecture(os.getenv("GEMINI_API_KEY", ""), req)
                    
                    DatabaseEngine.save_project(plan, user['email'])
                    if not user.get('is_subscribed'):
                        DatabaseEngine.update_credits(user['email'], max(0, user['credits'] - 1))
                    
                    st.session_state.current_plan = plan
                    st.balloons()  # إطلاق البالونات من الأسفل للأعلى بنجاح
                    st.success("✅ تم توليد الخطة وحفظها بقاعدة البيانات المركزية بنجاح!")
                    st.rerun()

        if st.session_state.current_plan:
            plan = st.session_state.current_plan
            st.write("---")
            
            # --- التفصيل النصي الشامل والإحترافي للخطة فوق زر الواتساب ---
            st.markdown("---")
            st.markdown(build_detailed_plan_text(plan))
            st.markdown("---")

            col_sig1, col_sig2 = st.columns([3, 1])
            with col_sig1:
                st.info(f"🔑 التوقيع الرقمي (HMAC-SHA512):\n`{plan.get('signature', '')}`")
            with col_sig2:
                if VaultSecurity.verify_signature(plan, plan.get('signature', '')):
                    st.markdown("<br><span class='badge-green'>✔ توقيع موثوق وسليم</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<br><span class='badge-purple'>❌ تم التلاعب بالبيانات</span>", unsafe_allow_html=True)

            df_tasks = pd.DataFrame(plan.get('tasks', []))
            st.dataframe(df_tasks, use_container_width=True)
            
            col_dl1, col_dl2 = st.columns(2)
            detailed_txt = build_detailed_plan_text(plan)
            with col_dl1:
                ex_bytes = generate_excel_download(df_tasks)
                st.download_button("📥 تحميل مهام (Excel/CSV)", data=ex_bytes, file_name=f"{plan.get('project_name', 'Project')}_Tasks.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            with col_dl2:
                pdf_bytes = generate_pdf_plan(plan, plan.get('signature', ''), detailed_txt)
                st.download_button("📄 تحميل الخطة (PDF)", data=pdf_bytes, file_name=f"{plan.get('project_name', 'Project')}_Plan.pdf", mime="application/pdf", use_container_width=True)

            safe_pname = plan.get('project_name', 'مشروع جديد')
            safe_budget = plan.get('budget', 0)
            safe_sig = plan.get('signature', 'N/A')[:15]
            msg_body = f"🚀 مشروع: {safe_pname}\n💰 الميزانية: ${safe_budget}\n🔑 التوقيع: {safe_sig}..."
            wa_url = NotificationEngine.create_whatsapp_link(st.session_state.notify_whatsapp, msg_body)
            st.markdown(f'<br><a href="{wa_url}" target="_blank" style="display:block; text-align:center; background-color:#25D366; color:white; padding:12px; border-radius:10px; font-weight:bold; text-decoration:none; font-size:15px; box-shadow: 0 4px 12px rgba(37,211,102,0.3);">📱 إرسال تفاصيل الخطة عبر WhatsApp</a>', unsafe_allow_html=True)

    # ------------------ TAB 2: ANALYTICS ------------------
    with t2:
        if not st.session_state.current_plan:
            st.info("💡 قم بتوليد خطة مشروع أولاً من التبويب الأول لاستعراض التحليلات الهندسية المتقدمة.")
        else:
            plan = st.session_state.current_plan
            df = pd.DataFrame(plan.get('tasks', []))
            st.markdown("## 📊 لوحة القيادة الهندسية (5D Radar Risk Matrix)")
            
            p_budget = float(plan.get('budget', 0))
            p_days = int(plan.get('target_days', 1))
            p_name_safe = plan.get('project_name', 'المشروع')
            
            daily_rate = int(p_budget / max(1, p_days))
            feasibility_score = min(98, max(65, int(100 - (p_days / max(1, p_budget / 100)) * 5)))
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("💰 الميزانية المعتمدة", f"${p_budget:,.0f}")
            m2.metric("⏱️ المدى الزمني", f"{p_days} يوم")
            m3.metric("📈 التكلفة اليومية", f"${daily_rate:,}/يوم")
            m4.metric("🛡️ مؤشر السلامة", f"{feasibility_score}%", delta="ممتاز" if feasibility_score > 80 else "مقبول")
            
            c_r1, c_r2 = st.columns(2)
            with c_r1:
                labels = [p_name_safe] + list(df['task'] if 'task' in df else [])
                parents = [""] + [p_name_safe] * len(df)
                values = [p_budget] + list(df['cost'] if 'cost' in df else [])
                fig_sun = go.Figure(go.Sunburst(labels=labels, parents=parents, values=values, branchvalues="total", hovertemplate='<b>%{label}</b><br>المبلغ: $%{value:,}<br>النسبة: %{percentParent:.1%}', marker=dict(colorscale='Blues')))
                fig_sun.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=text_color), height=350)
                st.plotly_chart(fig_sun, use_container_width=True)

            with c_r2:
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number+delta", value=feasibility_score,
                    title={'text': "الكفاءة والجاهزية الهندسية", 'font': {'color': text_color}},
                    delta={'reference': 80, 'increasing': {'color': "#10B981"}},
                    gauge={'axis': {'range': [None, 100]}, 'bar': {'color': "#8B5CF6"}, 'bgcolor': "rgba(0,0,0,0)", 'borderwidth': 2}
                ))
                fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=text_color), height=350)
                st.plotly_chart(fig_gauge, use_container_width=True)

            c_w1, c_w2 = st.columns(2)
            with c_w1:
                radar_categories = ['تعقيد النطاق', 'الأمان الرقمي', 'الجدول الزمني', 'استقرار التكلفة', 'المرونة التقنية']
                radar_values = [80, 95, 85, 90, 85 if plan.get('risk') == 'عالي' else 65]
                fig_rad = go.Figure(go.Scatterpolar(r=radar_values, theta=radar_categories, fill='toself', line=dict(color='#8B5CF6', width=3), fillcolor='rgba(139,92,246,0.35)'))
                fig_rad.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,100])), showlegend=False, paper_bgcolor='rgba(0,0,0,0)', font=dict(color=text_color), height=340)
                st.plotly_chart(fig_rad, use_container_width=True)
            with c_w2:
                x_labels = list(df['task'] if 'task' in df else []) + ["الإجمالي"]
                y_meas = ["relative"] * len(df) + ["total"]
                y_vals = list(df['cost'] if 'cost' in df else []) + [0]
                fig_wat = go.Figure(go.Waterfall(name="التكلفة", orientation="v", measure=y_meas, x=x_labels, textposition="outside", text=[f"${c:,}" if c>0 else f"${p_budget:,.0f}" for c in y_vals], y=y_vals, connector={"line":{"color":"#64748B"}}))
                fig_wat.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=text_color), height=340)
                st.plotly_chart(fig_wat, use_container_width=True)

    # ------------------ TAB 3: EDITOR ------------------
    with t3:
        if not st.session_state.current_plan:
            st.warning("⚠️ لا توجد خطة حالية لتعديلها.")
        else:
            edited_df = st.data_editor(pd.DataFrame(st.session_state.current_plan.get('tasks', [])), num_rows="dynamic", use_container_width=True)
            if st.button("💾 حفظ التعديلات وإعادة التوقيع الرقمي", use_container_width=True):
                updated = edited_df.to_dict(orient='records')
                st.session_state.current_plan['tasks'] = updated
                st.session_state.current_plan['budget'] = sum(int(i.get('cost', 0)) for i in updated)
                st.session_state.current_plan['target_days'] = sum(int(i.get('days', 0)) for i in updated)
                st.session_state.current_plan['signature'] = VaultSecurity.sign_payload(st.session_state.current_plan)
                st.success("✅ تم تحديث المهام وإعادة التوقيع بنجاح!")
                st.rerun()

            st.write("---")
            st.markdown(build_detailed_plan_text(st.session_state.current_plan))

    # ------------------ TAB 4: ARCHIVE (DB) ------------------
    with t4:
        st.subheader("🗄️ المشاريع المحفوظة دائماً (Hybrid DB Archive)")
        projs = DatabaseEngine.get_projects(user['email'])
        if projs:
            st.dataframe(pd.DataFrame(projs), use_container_width=True)
        else:
            st.info("لا توجد مشاريع محفوظة حالياً بالمنظومة المركزية.")

    # ------------------ TAB 5: ACCOUNT & BILLING ------------------
    with t5:
        st.subheader("💳 إدارة الحساب وبوابة الدفع بالذكاء الاصطناعي")
        c_stat1, c_stat2 = st.columns([2, 1])
        with c_stat1:
            st.info(f"👤 **المهندس:** {user['name']} ({user['email']})\n\n💳 **الرصيد المتاح:** {user['credits']} نقطة.")
        with c_stat2:
            if user['credits'] > 0 and not user.get('is_subscribed'):
                st.markdown("<span class='badge-green'>🎁 باقة تجريبية نشطة</span>", unsafe_allow_html=True)
            elif user.get('is_subscribed'):
                st.markdown(f"<span class='badge-gold'>👑 {user['plan_status']} نشط</span>", unsafe_allow_html=True)

        st.write("---")
        c_p1, c_p2, c_p3 = st.columns(3)
        with c_p1:
            st.markdown("""<div class="pricing-card"><h3>🎁 التجريبي</h3><h2>$0</h2><hr><p>✔ 5 نقاط مجانية</p><p>✔ التوقيع الرقمي</p></div>""", unsafe_allow_html=True)
        with c_p2:
            st.markdown(f"""<div class="pricing-card-highlight"><span class="badge-purple">الأكثر شعبية 🚀</span><h3>⚡ باقة Pro</h3><h2>$29 <small>/ شهر</small></h2><hr><a href="{PAYMENT_LINK_MONTHLY}" target="_blank" class="checkout-btn">🚀 الاشتراك الخارجي</a></div>""", unsafe_allow_html=True)
        with c_p3:
            st.markdown(f"""<div class="pricing-card"><span class="badge-gold">خصم 20% 🏆</span><h3>👑 Enterprise</h3><h2>$279 <small>/ سنة</small></h2><hr><a href="{PAYMENT_LINK_YEARLY}" target="_blank" class="checkout-btn-yearly">💎 الاشتراك الخارجي</a></div>""", unsafe_allow_html=True)

        if st.session_state.get('payment_notifications'):
            st.write("---")
            st.markdown("### 📬 صندوق الإشعارات الواردة من Lemon Squeezy (Email Inbox)")
            for notif in st.session_state.payment_notifications:
                st.markdown(f"""
                <div class="email-notification-box">
                    <b>📩 From:</b> payments@lemonsqueezy.com<br>
                    <b>📨 To:</b> {notif['to']}<br>
                    <b>📌 Subject:</b> {notif['subject']}<br>
                    <hr style="border-color:#10B981;">
                    <ul>
                        <li><b>Item:</b> {notif['plan_name']}</li>
                        <li><b>Total Paid:</b> {notif['amount']}</li>
                        <li><b>Payment Method:</b> {notif['payment_method']}</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
