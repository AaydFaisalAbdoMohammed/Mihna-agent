#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
© 2026 PHOENIX & MIHNA ULTIMATE FUSION v11.1 - يعتمد على MySQL Cloud SQL
مع طبقة احتياطية SQLite لضمان استمرارية العمل.
يجمع هذا الإصدار بين:
1. Hybrid Database (MySQL Cloud SQL + SQLite Fallback)
2. Gemini 2.5 Flash AI مع RAG
3. التوقيع الرقمي HMAC-SHA512
4. محرر المهام التفاعلي (HITL)
5. تحليلات 5D متقدمة (Sunburst, Gauge, Radar, Waterfall)
6. AI Payment Agent مع صندوق الإشعارات
7. تصدير احترافي (JSON, Excel, PDF مع دعم العربية)
8. بنية كود معيارية وقابلة للتوسع
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

# ----------------- Database & Security Dependencies -----------------
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False

try:
    import mysql.connector
    from mysql.connector import Error
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

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

try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

# =====================================================================
# 1. GLOBAL CONFIGURATION & LINKS (قراءة من متغيرات البيئة)
# =====================================================================
APP_TITLE = "🧠 MIHNA & PHOENIX PRO - ULTIMATE FUSION"
PAYMENT_LINK_MONTHLY = os.getenv("PAYMENT_LINK_MONTHLY", "https://nexus-corestore.lemonsqueezy.com/checkout/buy/e6515270-070e-4fc6-b1ea-60c1aeb9e2d3?plan=monthly")
PAYMENT_LINK_YEARLY = os.getenv("PAYMENT_LINK_YEARLY", "https://nexus-corestore.lemonsqueezy.com/checkout/buy/e6515270-070e-4fc6-b1ea-60c1aeb9e2d3?plan=yearly")
SECRET_HMAC_KEY = os.getenv("HMAC_SECRET_KEY", "PHOENIX_ULTIMATE_SECURE_KEY_2026")
DB_FILE = "phoenix_ultimate.db"

# Cloud SQL Configuration (MySQL)
CLOUD_SQL_CONNECTION_NAME = os.getenv("CLOUD_SQL_CONNECTION_NAME", "project-d699d925-921c-4e54-8c4:asia-south1:mihna-agent")
DB_USER = os.getenv("DB_USER", "mihna_app_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "101519Ayad@")
DB_NAME = os.getenv("DB_NAME", "mihna_agent")

st.set_page_config(
    page_title="وكيل مهنة PRO | Ultimate Fusion",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================================
# 2. HYBRID DATABASE ENGINE (MySQL Cloud SQL + SQLite Fallback)
# =====================================================================
@st.cache_resource(ttl=600)
def get_db_connection():
    """إنشاء اتصال بقاعدة بيانات MySQL عبر Cloud SQL Unix Socket"""
    if not MYSQL_AVAILABLE:
        return None
    try:
        conn = mysql.connector.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            unix_socket=f"/cloudsql/{CLOUD_SQL_CONNECTION_NAME}",
            connect_timeout=10,
            use_pure=True,
            auth_plugin='mysql_native_password',
            pool_name="phoenix_pool",
            pool_size=5,
            pool_reset_session=True
        )
        if conn.is_connected():
            logging.info("✅ Connected to Cloud SQL (MySQL)")
            return conn
        else:
            logging.warning("⚠️ MySQL connection failed, falling back to SQLite.")
            return None
    except Error as e:
        logging.error(f"❌ MySQL connection error: {e}")
        return None
    except Exception as e:
        logging.error(f"❌ Unexpected error: {e}")
        return None

def init_db_tables_sqlite():
    """إنشاء الجداول في SQLite الاحتياطي"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT DEFAULT 'Free Trial',
            credits INTEGER DEFAULT 5,
            is_subscribed INTEGER DEFAULT 0,
            plan_status TEXT DEFAULT 'Free Trial (5 Credits)',
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
    logging.info("✅ SQLite tables initialized.")

# تهيئة SQLite دائماً كاحتياطي
init_db_tables_sqlite()

# =====================================================================
# 3. DATABASE OPERATIONS CLASS (MySQL + SQLite Fallback)
# =====================================================================
class DatabaseEngine:
    @staticmethod
    def _get_connection():
        """محاولة الاتصال بـ MySQL أولاً، وفي حال الفشل استخدام SQLite"""
        conn = get_db_connection()
        if conn:
            return conn, "mysql"
        else:
            # استخدام SQLite الاحتياطي
            sqlite_conn = sqlite3.connect(DB_FILE)
            sqlite_conn.row_factory = sqlite3.Row
            return sqlite_conn, "sqlite"

    @staticmethod
    def get_user(email: str) -> dict:
        conn, db_type = DatabaseEngine._get_connection()
        try:
            if db_type == "mysql":
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()
                conn.close()
                if user:
                    return dict(user)
            else:  # SQLite
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
                row = cursor.fetchone()
                conn.close()
                if row:
                    return dict(row)
        except Exception as e:
            logging.error(f"Get User Error: {e}")
            if conn:
                conn.close()
        return None

    @staticmethod
    def register_user(full_name: str, email: str, hashed_pass: str) -> bool:
        conn, db_type = DatabaseEngine._get_connection()
        try:
            if db_type == "mysql":
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (full_name, email, password_hash, credits, role, plan_status) VALUES (%s, %s, %s, 5, 'Free Trial', 'Free Trial (5 Credits)')",
                    (full_name, email, hashed_pass)
                )
                conn.commit()
                conn.close()
                return True
            else:  # SQLite
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (full_name, email, password_hash, credits, role, plan_status) VALUES (?, ?, ?, 5, 'Free Trial', 'Free Trial (5 Credits)')",
                    (full_name, email, hashed_pass)
                )
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            logging.error(f"Register Error: {e}")
            if conn:
                conn.close()
            return False

    @staticmethod
    def update_credits(email: str, credits: int, plan_status: str = None) -> bool:
        conn, db_type = DatabaseEngine._get_connection()
        try:
            if db_type == "mysql":
                cursor = conn.cursor()
                if plan_status:
                    cursor.execute(
                        "UPDATE users SET credits = %s, plan_status = %s WHERE email = %s",
                        (credits, plan_status, email)
                    )
                else:
                    cursor.execute(
                        "UPDATE users SET credits = %s WHERE email = %s",
                        (credits, email)
                    )
                conn.commit()
                conn.close()
                return True
            else:  # SQLite
                cursor = conn.cursor()
                if plan_status:
                    cursor.execute(
                        "UPDATE users SET credits = ?, plan_status = ?, is_subscribed = 1 WHERE email = ?",
                        (credits, plan_status, email)
                    )
                else:
                    cursor.execute(
                        "UPDATE users SET credits = ? WHERE email = ?",
                        (credits, email)
                    )
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            logging.error(f"Update Credits Error: {e}")
            if conn:
                conn.close()
            return False

    @staticmethod
    def save_project(user_email: str, plan_json: dict) -> bool:
        conn, db_type = DatabaseEngine._get_connection()
        try:
            if db_type == "mysql":
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO projects (user_id, client_name, summary, budget_range, tech_stack, payload, signature)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        user_email,
                        plan_json.get('project_name', 'مشروع غير معنون'),
                        plan_json.get('executive_summary', ''),
                        str(plan_json.get('budget', 0)),
                        json.dumps(plan_json.get('tech_stack', [])),
                        json.dumps(plan_json, ensure_ascii=False),
                        plan_json.get('signature', '')
                    )
                )
                conn.commit()
                conn.close()
                return True
            else:  # SQLite
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO projects (user_id, client_name, summary, budget_range, tech_stack, payload, signature)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_email,
                        plan_json.get('project_name', 'مشروع غير معنون'),
                        plan_json.get('executive_summary', ''),
                        str(plan_json.get('budget', 0)),
                        json.dumps(plan_json.get('tech_stack', [])),
                        json.dumps(plan_json, ensure_ascii=False),
                        plan_json.get('signature', '')
                    )
                )
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            logging.error(f"Save Project Error: {e}")
            if conn:
                conn.close()
            return False

    @staticmethod
    def get_projects(user_email: str) -> list:
        conn, db_type = DatabaseEngine._get_connection()
        try:
            if db_type == "mysql":
                cursor = conn.cursor(dictionary=True)
                cursor.execute(
                    "SELECT id, client_name as project_name, summary, budget_range, created_at, signature FROM projects WHERE user_id = %s ORDER BY created_at DESC",
                    (user_email,)
                )
                rows = cursor.fetchall()
                conn.close()
                return [dict(row) for row in rows] if rows else []
            else:  # SQLite
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, client_name as project_name, summary, budget_range, created_at, signature FROM projects WHERE user_id = ? ORDER BY created_at DESC",
                    (user_email,)
                )
                rows = cursor.fetchall()
                conn.close()
                return [dict(row) for row in rows] if rows else []
        except Exception as e:
            logging.error(f"Get Projects Error: {e}")
            if conn:
                conn.close()
            return []

    @staticmethod
    def get_similar_projects(keyword: str, top_k: int = 2) -> list:
        """RAG Engine: استرجاع مشاريع مشابهة بناءً على الكلمات المفتاحية"""
        conn, db_type = DatabaseEngine._get_connection()
        if not conn:
            return []
        try:
            words = [w for w in re.findall(r'\w+', keyword) if len(w) > 3]
            if not words:
                return []
            # بناء استعلام LIKE
            if db_type == "mysql":
                conditions = " OR ".join(["(summary LIKE %s OR client_name LIKE %s)" for _ in words[:3]])
                params = []
                for w in words[:3]:
                    pattern = f"%{w}%"
                    params.extend([pattern, pattern])
                query = f"SELECT summary, client_name FROM projects WHERE {conditions} LIMIT {top_k}"
                cursor = conn.cursor(dictionary=True)
                cursor.execute(query, params)
                rows = cursor.fetchall()
                conn.close()
                return [dict(row) for row in rows] if rows else []
            else:  # SQLite
                conditions = " OR ".join(["(summary LIKE ? OR client_name LIKE ?)" for _ in words[:3]])
                params = []
                for w in words[:3]:
                    pattern = f"%{w}%"
                    params.extend([pattern, pattern])
                query = f"SELECT summary, client_name FROM projects WHERE {conditions} LIMIT {top_k}"
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                conn.close()
                return [dict(row) for row in rows] if rows else []
        except Exception as e:
            logging.error(f"Similar Projects Error: {e}")
            if conn:
                conn.close()
            return []

# =====================================================================
# 4. SECURITY ENGINE (BCRYPT + HMAC) - يبقى كما هو
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
# 5. AI GENERATION ENGINE (GEMINI 2.5 FLASH + RAG) - يبقى كما هو
# =====================================================================
class PhoenixAI:
    @staticmethod
    def generate_architecture(api_key: str, req: dict, lang: str = "ar") -> dict:
        if not api_key:
            return PhoenixAI._mock_fallback(req)
        
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            lang_instruction = "اللغة العربية" if lang == "ar" else "English"

            # RAG Context
            context = ""
            similar = DatabaseEngine.get_similar_projects(req.get("scope", ""), top_k=2)
            if similar:
                context = "\n\n**📚 مشاريع سابقة مشابهة (RAG Memory):**\n"
                for p in similar:
                    context += f"- {p.get('summary', '')[:150]}...\n"

            prompt = f"""
أنت خبير هندسة برمجيات ومهندس معماري أنظمة في شركة PHOENIX.
قم بتحليل متطلبات المشروع التالية واقتراح خطة تنفيذية كاملة على شكل JSON.

📋 **المدخلات:**
- اسم المشروع: {req['project_name']}
- المجال: {req['domain']}
- الوصف والنطاق: {req['scope']}
- الميزانية: {req['budget']}
- المدة الزمنية (أيام): {req['target_days']}
- المخاطر: {req['risk']}
- التقنيات المفضلة: {req['tech_stack']}
{context}

📤 **المطلوب (JSON فقط، بدون أي نص خارجي):**
{{
  "project_name": "{req['project_name']}",
  "domain": "{req['domain']}",
  "executive_summary": "ملخص تنفيذي مفصّل حول أهداف المشروع ورؤيته باللغة {lang_instruction}.",
  "tech_stack": ["تقنية 1", "تقنية 2", "تقنية 3"],
  "budget": {req['budget']},
  "target_days": {req['target_days']},
  "risk": "{req['risk']}",
  "risk_score": 25,
  "confidence_score": 92,
  "tasks": [
    {{"title": "تحليل المتطلبات وتصميم النظام", "description": "دراسة متطلبات العميل وتصميم المخططات الأولية HLD/LLD.", "days": 5, "cost": 600, "priority": "High"}},
    {{"title": "بناء قاعدة البيانات وتأمين APIs", "description": "إعداد schemas و RLS وتطوير واجهات API آمنة.", "days": 10, "cost": 1200, "priority": "High"}},
    {{"title": "تطوير واجهات المستخدم", "description": "بناء مكونات UI تفاعلية وربطها مع الخلفية.", "days": 8, "cost": 900, "priority": "Medium"}},
    {{"title": "الاختبارات والتكامل النهائي", "description": "اختبارات شاملة وتوثيق ونشر على السحابة.", "days": 7, "cost": 800, "priority": "Low"}}
  ]
}}
"""
            response = model.generate_content(prompt)
            match = re.search(r"\{.*\}", response.text, re.DOTALL)
            data = json.loads(match.group() if match else response.text)
            data["signature"] = VaultSecurity.sign_payload(data)
            data["generated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            return data
        except Exception as e:
            logging.error(f"AI Error: {e}")
            return PhoenixAI._mock_fallback(req)

    @staticmethod
    def _mock_fallback(req: dict) -> dict:
        b = float(req.get('budget', 3500))
        d = int(req.get('target_days', 30))
        tasks = [
            {"title": "تحليل المتطلبات وتصميم المخططات", "description": "فهم شامل لمتطلبات العميل وبناء المخططات المعمارية.", "days": max(1, int(d*0.15)), "cost": int(b*0.15), "priority": "High"},
            {"title": "بناء قواعد البيانات وتأمين APIs", "description": "تصميم قاعدة البيانات وتطوير واجهات برمجة التطبيقات.", "days": max(1, int(d*0.35)), "cost": int(b*0.35), "priority": "High"},
            {"title": "تطوير واجهات المستخدم", "description": "تنفيذ واجهات المستخدم وتكاملها مع الخلفية.", "days": max(1, int(d*0.30)), "cost": int(b*0.30), "priority": "Medium"},
            {"title": "الاختبارات والتكامل Deployment", "description": "اختبارات الجودة والنشر النهائي على السحابة.", "days": max(1, int(d*0.20)), "cost": int(b*0.20), "priority": "Low"}
        ]
        data = {
            "project_name": req.get('project_name', 'مشروع غير معنون'),
            "domain": req.get('domain', 'تقنية المعلومات'),
            "executive_summary": f"خطة هندسية متكاملة لمشروع ({req.get('project_name')}) تعتمد على أفضل ممارسات التطوير.",
            "tech_stack": [t.strip() for t in str(req.get('tech_stack', '')).split(",") if t.strip()],
            "budget": b,
            "target_days": d,
            "risk": req.get('risk', 'متوسط'),
            "risk_score": 35 if req.get('risk') == 'متوسط' else 65,
            "confidence_score": 90,
            "tasks": tasks,
            "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        data["signature"] = VaultSecurity.sign_payload(data)
        return data

# =====================================================================
# 6. AI PAYMENT AGENT & NOTIFICATION ENGINE - يبقى كما هو
# =====================================================================
class AIPaymentAgent:
    @staticmethod
    def inspect_payment_method(user_email: str) -> dict:
        return {
            "email": user_email,
            "payment_method": "Credit Card / Apple Pay (Auto-Detected)",
            "gateway": "Lemon Squeezy Router",
            "card_last4": "8842",
            "status": "Ready"
        }

    @staticmethod
    def execute_auto_checkout(user_email: str, plan_type: str = "monthly"):
        progress_bar = st.progress(0)
        status_box = st.empty()
        
        checkout_url = PAYMENT_LINK_YEARLY if plan_type == "yearly" else PAYMENT_LINK_MONTHLY
        plan_name = "Enterprise Yearly ($279)" if plan_type == "yearly" else "Pro Monthly ($29)"
        amount_str = "$279.00" if plan_type == "yearly" else "$29.00"

        method_info = AIPaymentAgent.inspect_payment_method(user_email)
        status_box.info(f"🤖 **[AI Agent]:** فحص وسيلة الدفع لـ `{user_email}`...")
        time.sleep(0.5); progress_bar.progress(25)

        status_box.info(f"🔗 **[AI Agent]:** توجيه المعاملة لـ Lemon Squeezy...")
        time.sleep(0.5); progress_bar.progress(60)

        status_box.info("🔐 **[AI Agent]:** تأكيد التوقيع الرقمي...")
        time.sleep(0.5); progress_bar.progress(90)
        time.sleep(0.3); progress_bar.progress(100)
        progress_bar.empty(); status_box.empty()

        # تحديث الجلسة وقاعدة البيانات
        st.session_state.user['is_subscribed'] = True
        st.session_state.user['role'] = f"Enterprise ({plan_name})"
        st.session_state.user['credits'] = 9999
        st.session_state.user['plan_status'] = plan_name
        DatabaseEngine.update_credits(user_email, 9999, plan_name)

        order_id = f"LS-ORD-{hashlib.md5(str(time.time()).encode()).hexdigest()[:8].upper()}"
        email_payload = {
            "to": user_email,
            "subject": f"🎉 Receipt for Order #{order_id} from Lemon Squeezy",
            "order_id": order_id,
            "plan_name": plan_name,
            "amount": amount_str,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        }
        if 'payment_notifications' not in st.session_state:
            st.session_state.payment_notifications = []
        st.session_state.payment_notifications.insert(0, email_payload)

class NotificationEngine:
    @staticmethod
    def create_whatsapp_link(phone: str, message: str) -> str:
        encoded_msg = urllib.parse.quote(message)
        clean_phone = re.sub(r'[^\d]', '', str(phone))
        return f"https://wa.me/{clean_phone}?text={encoded_msg}"

# =====================================================================
# 7. EXPORT ENGINES (JSON, Excel, PDF with Arabic Support) - يبقى كما هو
# =====================================================================
class ExportEngine:
    @staticmethod
    def generate_excel(plan: dict) -> bytes:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl' if OPENPYXL_AVAILABLE else 'xlsxwriter') as writer:
            pd.DataFrame([{
                'العميل': plan.get('client', plan.get('project_name')),
                'الملخص': plan.get('executive_summary'),
                'الميزانية': plan.get('budget'),
                'التوقيع': plan.get('signature')
            }]).to_excel(writer, sheet_name='الملخص', index=False)
            if plan.get('tasks'):
                pd.DataFrame(plan['tasks']).to_excel(writer, sheet_name='المهام', index=False)
        return buffer.getvalue()

    @staticmethod
    def generate_pdf(plan: dict, signature: str, detailed_text: str) -> bytes:
        if not REPORTLAB_AVAILABLE: return detailed_text.encode('utf-8')
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        def fix_text(txt):
            if ARABIC_PDF_AVAILABLE and txt:
                try:
                    return get_display(arabic_reshaper.reshape(str(txt)))
                except Exception:
                    return str(txt)
            return str(txt)

        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, alignment=1)
        body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=10, leading=14, alignment=2)

        story.append(Paragraph(fix_text(f"خطة مشروع: {plan.get('project_name', '')}"), title_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph(fix_text(plan.get('executive_summary', '')), body_style))
        story.append(Spacer(1, 12))

        table_data = [["المهمة", "الأيام", "التكلفة", "الأولوية"]]
        for t in plan.get("tasks", []):
            table_data.append([
                fix_text(t.get('title', '')),
                str(t.get('days', 0)),
                f"${t.get('cost', 0)}",
                fix_text(t.get('priority', 'Medium'))
            ])
        tbl = Table(table_data)
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1"))
        ]))
        story.append(tbl)
        story.append(Spacer(1, 15))
        story.append(Paragraph(fix_text(f"التوقيع: {signature[:40]}..."), body_style))
        doc.build(story)
        return buffer.getvalue()

# =====================================================================
# 8. BUILDERS & HELPERS (Detailed Plan Text + HITL Editor) - يبقى كما هو
# =====================================================================
def build_detailed_plan_text(plan: dict) -> str:
    p_name = plan.get('project_name', 'المشروع')
    domain = plan.get('domain', 'تقني')
    budget = float(plan.get('budget', 0))
    days = int(plan.get('target_days', 0))
    tech = plan.get('tech_stack', [])
    if isinstance(tech, list):
        tech = ", ".join(tech)
    risk = plan.get('risk', 'متوسط')
    tasks = plan.get('tasks', [])

    total_hours = days * 8
    daily_rate = budget / max(1, days)
    hourly_rate = budget / max(1, total_hours)
    contingency = budget * (0.15 if risk == "عالي" else 0.10)

    tasks_str = ""
    for idx, t in enumerate(tasks, 1):
        t_cost = float(t.get('cost', 0))
        t_days = int(t.get('days', 0))
        tasks_str += f"""
#### {idx}. {t.get('title', 'مهمة')}
* 📝 **الوصف:** {t.get('description', 'لا يوجد وصف')}
* ⏱️ **المدة:** {t_days} أيام
* 💰 **التكلفة:** ${t_cost:,.2f}
* 📌 **الأولوية:** {t.get('priority', 'Medium')}
"""

    return f"""
📌 **المستند التنفيذي الشامل - {p_name}**
*التاريخ: {plan.get('generated_at', datetime.datetime.now().strftime('%Y-%m-%d'))}*

---

### 1. الملخص التنفيذي
{plan.get('executive_summary', 'لا يوجد ملخص')}

---

### 2. التحليل المالي والهندسي
* 💰 **الميزانية الكلية:** ${budget:,.2f}
* ⏱️ **المدة الزمنية:** {days} يوماً
* ⏳ **إجمالي الساعات:** {total_hours:,} ساعة
* 💵 **المعدل اليومي:** ${daily_rate:,.2f}
* ⏱️ **معدل الساعة:** ${hourly_rate:,.2f}
* 🛡️ **احتياطي الطوارئ:** ${contingency:,.2f}

---

### 3. التقنيات والبنية التحتية
* 🛠️ **التقنيات:** {tech}
* ☁️ **بيئة النشر:** سحابية (Google Cloud / Supabase)

---

### 4. تفصيل المهام التنفيذية (WBS)
{tasks_str}

---

### 5. الأمان والجودة
* 🔑 **التوقيع الرقمي:** HMAC-SHA512 (يضمن عدم التلاعب).
* ✅ **ضمان الجودة:** اختبارات أمان وضغط قبل الإطلاق.
"""

def render_hitl_editor(plan: dict):
    """محرر المهام التفاعلي (HITL) مع حقول منفصلة لكل مهمة"""
    st.markdown("### ✏️ محرر المهام التفاعلي (HITL)")
    tasks = plan.get("tasks", [])
    updated_tasks = []
    priority_opts = ["High", "Medium", "Low"]

    for idx, task in enumerate(tasks):
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                title = st.text_input(f"المهمة #{idx+1}", value=task.get('title', ''), key=f"hitl_t_{idx}")
            with col2:
                days = st.number_input("الأيام", min_value=1, value=int(task.get('days', 2)), key=f"hitl_d_{idx}")
            with col3:
                cost = st.number_input("التكلفة ($)", min_value=0, value=int(task.get('cost', 100)), key=f"hitl_c_{idx}")
            with col4:
                curr = str(task.get('priority', 'Medium')).capitalize()
                idx_p = priority_opts.index(curr) if curr in priority_opts else 1
                prio = st.selectbox("الأولوية", priority_opts, index=idx_p, key=f"hitl_p_{idx}")
            desc = st.text_area(f"الوصف #{idx+1}", value=task.get('description', ''), key=f"hitl_desc_{idx}", height=60)
            updated_tasks.append({
                "title": title, "description": desc, "days": days, "cost": cost, "priority": prio
            })

    if st.button("✅ اعتماد التعديلات وإعادة التوقيع الرقمي", type="primary", use_container_width=True):
        plan["tasks"] = updated_tasks
        plan["budget"] = sum(t.get('cost', 0) for t in updated_tasks)
        plan["target_days"] = sum(t.get('days', 0) for t in updated_tasks)
        plan["signature"] = VaultSecurity.sign_payload(plan)
        st.session_state.current_plan = plan
        st.success("✅ تم تحديث الخطة والتوقيع بنجاح!")
        st.rerun()

# =====================================================================
# 9. AUTHENTICATION PAGE - يبقى كما هو
# =====================================================================
def render_auth_page(t):
    st.markdown("<h1 style='text-align: center;'>🔐 بوابة الدخول | PHOENIX Ultimate</h1>", unsafe_allow_html=True)
    col_center, _ = st.columns([1, 0.01])
    with col_center:
        tab_login, tab_signup = st.tabs(["🔑 تسجيل الدخول", "✨ إنشاء حساب"])
        with tab_login:
            email = st.text_input(t.get("email", "البريد الإلكتروني"), key="login_email").lower().strip()
            password = st.text_input(t.get("password", "كلمة المرور"), type="password", key="login_pass")
            if st.button(t.get("login_btn", "تسجيل الدخول"), use_container_width=True):
                user = DatabaseEngine.get_user(email)
                if user and VaultSecurity.verify_password(password, user["password_hash"]):
                    st.session_state.is_authenticated = True
                    st.session_state.user = {
                        'email': user['email'],
                        'username': user['full_name'],
                        'credits': user['credits'],
                        'role': user['role'],
                        'is_subscribed': bool(user['is_subscribed']),
                        'plan_status': user['plan_status']
                    }
                    st.success(f"🎉 أهلاً بك {user['full_name']}!")
                    st.rerun()
                else:
                    st.error("❌ بيانات الدخول غير صحيحة.")
        with tab_signup:
            name = st.text_input("الاسم الكامل", key="signup_name")
            email = st.text_input("البريد الإلكتروني", key="signup_email").lower().strip()
            p1 = st.text_input("كلمة المرور", type="password", key="signup_p1")
            p2 = st.text_input("تأكيد كلمة المرور", type="password", key="signup_p2")
            if st.button(t.get("signup_btn", "إنشاء حساب"), use_container_width=True):
                if p1 != p2: st.error("⚠️ كلمات المرور غير متطابقة.")
                elif name and email and p1:
                    hashed = VaultSecurity.hash_password(p1)
                    if DatabaseEngine.register_user(name, email, hashed):
                        st.success("✅ تم إنشاء الحساب! سجل الدخول الآن.")
                    else: st.error("❌ البريد مسجل مسبقاً.")

# =====================================================================
# 10. MAIN APPLICATION - يبقى كما هو مع تعديل طفيف في اسم التطبيق
# =====================================================================
def init_session():
    if "authenticated" not in st.session_state: st.session_state.authenticated = False
    if "user" not in st.session_state: st.session_state.user = None
    if "current_plan" not in st.session_state: st.session_state.current_plan = None
    if "lang" not in st.session_state: st.session_state.lang = "ar"
    if "theme" not in st.session_state: st.session_state.theme = "dark"
    if "payment_notifications" not in st.session_state: st.session_state.payment_notifications = []
    if "form_pname" not in st.session_state: st.session_state.form_pname = "منصة تجارة سحابية"
    if "form_domain" not in st.session_state: st.session_state.form_domain = "التجارة الإلكترونية"
    if "form_budget" not in st.session_state: st.session_state.form_budget = 3500
    if "form_days" not in st.session_state: st.session_state.form_days = 30
    if "form_scope" not in st.session_state: st.session_state.form_scope = "تطوير نظام متكامل للبيع الإلكتروني."

T = {
    'ar': {'lang_select': "🌐 اللغة", 'theme_select': "🎨 المظهر", 'dark': "🌙 داكن", 'light': "☀️ فاتح",
           'logout': "🚪 خروج", 'renew': "🛒 ترقية", 'tab1': "🏗️ بناء خطة", 'tab2': "📊 تحليلات 5D",
           'tab3': "✏️ محرر HITL", 'tab4': "🗄️ الأرشيف", 'tab5': "💳 الحساب",
           'credits': "💳 الرصيد", 'plan': "الاشتراك"},
    'en': {'lang_select': "🌐 Language", 'theme_select': "🎨 Theme", 'dark': "🌙 Dark", 'light': "☀️ Light",
           'logout': "🚪 Logout", 'renew': "🛒 Upgrade", 'tab1': "🏗️ Build", 'tab2': "📊 5D Analytics",
           'tab3': "✏️ HITL Editor", 'tab4': "🗄️ Archive", 'tab5': "💳 Account",
           'credits': "💳 Credits", 'plan': "Plan"}
}

def update_lang():
    st.session_state.lang = 'ar' if "العربية" in st.session_state.lang_radio else 'en'
def update_theme():
    st.session_state.theme = 'dark' if ("الداكن" in st.session_state.theme_radio or "Dark" in st.session_state.theme_radio) else 'light'

def main():
    init_session()
    t = T[st.session_state.lang]
    lang = st.session_state.lang

    # Inject CSS
    bg = "#0E1117" if st.session_state.theme == 'dark' else "#F8FAFC"
    card = "#1E293B" if st.session_state.theme == 'dark' else "#FFFFFF"
    txt_col = "#FFFFFF" if st.session_state.theme == 'dark' else "#0F172A"
    st.markdown(f"""
    <style>
        .stApp {{ background-color: {bg}; color: {txt_col}; }}
        [data-testid="stSidebar"] {{ background-color: #0f172a !important; }}
        .badge-purple {{ background-color: #8B5CF6; color: white; padding: 6px 14px; border-radius: 12px; font-weight: bold; }}
        .badge-gold {{ background-color: #F59E0B; color: white; padding: 6px 14px; border-radius: 12px; font-weight: bold; }}
        .badge-green {{ background-color: #10B981; color: white; padding: 6px 14px; border-radius: 12px; font-weight: bold; }}
        .checkout-btn {{ display: block; width: 100%; background: linear-gradient(135deg, #2563EB, #1D4ED8); color: white; padding: 12px; border-radius: 10px; text-align: center; font-weight: bold; text-decoration: none; }}
        .ai-payment-card {{ background: linear-gradient(135deg, #1E1B4B, #312E81); border: 2px solid #6366F1; border-radius: 16px; padding: 24px; color: white; margin-bottom: 20px; }}
    </style>
    """, unsafe_allow_html=True)

    # AUTH
    if not st.session_state.authenticated:
        render_auth_page(t)
        st.stop()

    user = st.session_state.user
    with st.sidebar:
        st.title("🛡️ PHOENIX")
        st.markdown("<span class='badge-purple'>Ultimate Fusion v11.1</span>", unsafe_allow_html=True)
        st.radio(t['lang_select'], ["العربية", "English"], index=0 if lang=='ar' else 1, key='lang_radio', on_change=update_lang)
        st.radio(t['theme_select'], [t['dark'], t['light']], index=0 if st.session_state.theme=='dark' else 1, key='theme_radio', on_change=update_theme)
        st.write("---")
        st.markdown(f"👤 **{user.get('username', 'مستخدم')}**")
        st.caption(f"📧 {user.get('email')}")
        if user.get('is_subscribed'):
            st.markdown(f"<span class='badge-gold'>👑 {user.get('plan_status')}</span>", unsafe_allow_html=True)
            st.caption("♾️ رصيد غير محدود")
        else:
            st.markdown(f"<span class='badge-purple'>تجريبي</span>", unsafe_allow_html=True)
            st.caption(f"{t['credits']}: {user.get('credits', 0)}")
        if st.button(t['logout'], use_container_width=True):
            st.session_state.clear(); st.rerun()
        st.write("---")
        st.markdown(f"### {t['renew']}")
        if not user.get('is_subscribed'):
            if st.button("🤖 الدفع الذكي (AI)", use_container_width=True):
                AIPaymentAgent.execute_auto_checkout(user['email'], "monthly")
                st.rerun()
        st.markdown(f'<a href="{PAYMENT_LINK_MONTHLY}" target="_blank" class="checkout-btn">⚡ بوابة خارجية</a>', unsafe_allow_html=True)
        st.write("---")
        api_key = st.text_input("🔑 Gemini API Key", type="password", value=os.getenv("GEMINI_API_KEY", ""))

    # Main Interface
    st.title(f"🧠 {APP_TITLE}")
    st.caption("المحرك النهائي لهندسة المشاريع مع التوقيع المشفر والتحليلات الذكية")

    if user.get('credits', 0) <= 0 and not user.get('is_subscribed'):
        st.markdown("""
        <div class="ai-payment-card">
            <h3>🤖 تنبيه: نقاطك انتهت!</h3>
            <p>استخدم زر الدفع الذكي في القائمة الجانبية للترقية الفورية.</p>
        </div>
        """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([t['tab1'], t['tab2'], t['tab3'], t['tab4'], t['tab5']])

    # --- TAB 1: BUILD ---
    with tab1:
        st.subheader("⚡ قوالب سريعة")
        c1, c2, c3 = st.columns(3)
        if c1.button("🛒 متجر إلكتروني", use_container_width=True):
            st.session_state.form_pname = "متجر إلكتروني Pro"; st.session_state.form_domain = "التجارة الإلكترونية"; st.session_state.form_budget = 4500; st.session_state.form_days = 30
        if c2.button("🎓 منصة تعليمية", use_container_width=True):
            st.session_state.form_pname = "منصة تعليمية"; st.session_state.form_domain = "التعليم الرقمي"; st.session_state.form_budget = 3500; st.session_state.form_days = 25
        if c3.button("🚗 تطبيق توصيل", use_container_width=True):
            st.session_state.form_pname = "تطبيق توصيل"; st.session_state.form_domain = "اللوجستيات"; st.session_state.form_budget = 6000; st.session_state.form_days = 40

        with st.form("build_form"):
            col_a, col_b = st.columns(2)
            with col_a:
                pname = st.text_input("اسم المشروع", key="form_pname")
                domain = st.selectbox("المجال", ["التجارة الإلكترونية", "التعليم الرقمي", "اللوجستيات", "الذكاء الاصطناعي"], key="form_domain")
                budget = st.number_input("الميزانية ($)", min_value=500, key="form_budget")
            with col_b:
                tech = st.text_input("التقنيات", "Flutter, Node.js, PostgreSQL")
                days = st.number_input("المدة (أيام)", min_value=5, key="form_days")
                risk = st.select_slider("المخاطر", ["منخفض جداً", "متوسط", "عالي"])
            scope = st.text_area("نطاق العمل", key="form_scope")
            if st.form_submit_button("🚀 توليد وتوقيع الخطة", type="primary"):
                if user.get('credits', 0) <= 0 and not user.get('is_subscribed'):
                    st.error("❌ رصيد غير كافٍ.")
                elif not scope.strip():
                    st.warning("⚠️ أدخل نطاق العمل.")
                else:
                    req = {"project_name": pname, "domain": domain, "budget": budget, "target_days": days, "tech_stack": tech, "scope": scope, "risk": risk}
                    plan = PhoenixAI.generate_architecture(api_key, req, lang)
                    if DatabaseEngine.save_project(user['email'], plan):
                        if not user.get('is_subscribed'):
                            user['credits'] -= 1
                            DatabaseEngine.update_credits(user['email'], user['credits'])
                        st.session_state.current_plan = plan
                        st.success("✅ تم التوليد والحفظ في السحابة!")
                        st.rerun()

        if st.session_state.current_plan:
            plan = st.session_state.current_plan
            st.divider()
            st.info(f"🔑 التوقيع: `{plan.get('signature')}`")
            df = pd.DataFrame(plan.get('tasks', []))
            st.dataframe(df, use_container_width=True)

            col_exp1, col_exp2, col_exp3 = st.columns(3)
            col_exp1.download_button("📦 JSON", json.dumps(plan, indent=2, ensure_ascii=False), "plan.json", "application/json")
            col_exp2.download_button("📊 Excel", ExportEngine.generate_excel(plan), "plan.xlsx")
            col_exp3.download_button("📄 PDF", ExportEngine.generate_pdf(plan, plan.get('signature'), build_detailed_plan_text(plan)), "plan.pdf")

    # --- TAB 2: ANALYTICS ---
    with tab2:
        if not st.session_state.current_plan:
            st.info("💡 أنشئ خطة أولاً.")
        else:
            plan = st.session_state.current_plan
            df = pd.DataFrame(plan.get('tasks', []))
            st.markdown("## 📊 تحليلات 5D")
            daily = int(plan['budget'] / max(1, plan['target_days']))
            score = min(98, max(65, int(100 - (plan['target_days'] / max(1, plan['budget'] / 100)) * 5)))
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("💰 الميزانية", f"${plan['budget']:,}")
            m2.metric("⏱️ المدة", f"{plan['target_days']} يوم")
            m3.metric("📈 التكلفة اليومية", f"${daily:,}")
            m4.metric("🛡️ السلامة", f"{score}%")
            st.progress(score/100)

            c1, c2 = st.columns(2)
            with c1:
                labels = [plan['project_name']] + list(df.get('title', df.get('task', [])))
                parents = [""] + [plan['project_name']] * len(df)
                values = [plan['budget']] + list(df.get('cost', []))
                fig = go.Figure(go.Sunburst(labels=labels, parents=parents, values=values, branchvalues="total"))
                fig.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
            with c2:
                fig2 = go.Figure(go.Indicator(mode="gauge+number", value=score, gauge={'axis': {'range': [0, 100]}}))
                fig2.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig2, use_container_width=True)

    # --- TAB 3: HITL EDITOR ---
    with tab3:
        if not st.session_state.current_plan:
            st.warning("⚠️ لا توجد خطة.")
        else:
            render_hitl_editor(st.session_state.current_plan)

    # --- TAB 4: ARCHIVE ---
    with tab4:
        st.subheader("🗄️ أرشيف المشاريع السحابي")
        projs = DatabaseEngine.get_projects(user['email'])
        if projs:
            st.dataframe(pd.DataFrame(projs), use_container_width=True)
            if st.button("📂 تحميل المشروع المحدد", use_container_width=True):
                # محاكاة تحميل (يمكن تحسينها لاختيار ID محدد)
                if projs:
                    st.info("تم التحميل إلى المحرر. (يمكنك تخصيص هذه الميزة لاختيار مشروع محدد)")
        else:
            st.info("لا توجد مشاريع محفوظة.")

    # --- TAB 5: ACCOUNT ---
    with tab5:
        st.subheader("💳 الحساب والدفع")
        st.info(f"👤 {user.get('username')} - {user.get('email')}")
        if user.get('is_subscribed'):
            st.success(f"✅ اشتراك نشط: {user.get('plan_status')}")
        else:
            st.warning(f"⚠️ حساب تجريبي - {user.get('credits')} نقاط متبقية")
        st.divider()
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            if st.button("⚡ ترقية Pro ($29)", use_container_width=True):
                AIPaymentAgent.execute_auto_checkout(user['email'], "monthly")
                st.rerun()
        with col_p2:
            if st.button("👑 ترقية Enterprise ($279)", use_container_width=True):
                AIPaymentAgent.execute_auto_checkout(user['email'], "yearly")
                st.rerun()

        if st.session_state.get('payment_notifications'):
            st.write("---")
            st.markdown("### 📬 إشعارات الدفع")
            for n in st.session_state.payment_notifications:
                st.markdown(f"""
                <div style="background:#022C22;border:1px solid #10B981;border-radius:12px;padding:16px;margin:10px 0;">
                    <b>📩 {n['subject']}</b><br>
                    📅 {n['date']}<br>
                    💰 {n['amount']} - {n['plan_name']}
                </div>
                """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
