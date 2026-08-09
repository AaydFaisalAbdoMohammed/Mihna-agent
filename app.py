#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
© 2026 PHOENIX & WAKEEL MEHNA PRO - CLOUD SQL FULL INTEGRATION
===============================================================================
"""

import os
import re
import io
import json
import time
import hmac
import hashlib
import sqlite3
import logging
import datetime
import urllib.parse

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai

# ----------------- Dependencies -----------------
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
    from reportlab.lib.pagesizes import A4
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
# 1. CONFIGURATION & CLOUD SQL SETTINGS
# =====================================================================
APP_TITLE = "🧠 WAKEEL MEHNA PRO - ULTIMATE FUSION"
PAYMENT_LINK_MONTHLY = os.getenv("PAYMENT_LINK_MONTHLY", "https://nexus-corestore.lemonsqueezy.com/checkout/buy/e6515270-070e-4fc6-b1ea-60c1aeb9e2d3?plan=monthly")
PAYMENT_LINK_YEARLY = os.getenv("PAYMENT_LINK_YEARLY", "https://nexus-corestore.lemonsqueezy.com/checkout/buy/e6515270-070e-4fc6-b1ea-60c1aeb9e2d3?plan=yearly")
SECRET_HMAC_KEY = os.getenv("HMAC_SECRET_KEY", "PHOENIX_ULTIMATE_SECURE_KEY_2026")
DB_FILE = "phoenix_ultimate.db"

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
# 2. DATABASE ENGINE MATCHING CLOUD SQL SCHEMA
# =====================================================================
@st.cache_resource(ttl=600)
def get_db_connection():
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
            return conn
    except Exception as e:
        logging.error(f"❌ MySQL Connection Failed: {e}")
    return None

def init_db_tables_sqlite():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            username TEXT,
            password_hash TEXT NOT NULL,
            is_premium INTEGER DEFAULT 0,
            free_uses INTEGER DEFAULT 5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            client_name TEXT,
            summary TEXT,
            tech_stack TEXT,
            budget_range TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            title TEXT,
            description TEXT,
            estimated_days INTEGER,
            priority TEXT,
            status TEXT DEFAULT 'pending'
        )
    ''')
    conn.commit()
    conn.close()

init_db_tables_sqlite()

class DatabaseEngine:
    @staticmethod
    def _get_connection():
        conn = get_db_connection()
        if conn:
            return conn, "mysql"
        else:
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
                return dict(user) if user else None
            else:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
                row = cursor.fetchone()
                conn.close()
                return dict(row) if row else None
        except Exception as e:
            logging.error(f"Get User Error: {e}")
            if conn: conn.close()
            return None

    @staticmethod
    def register_user(name: str, email: str, username: str, hashed_pass: str) -> bool:
        conn, db_type = DatabaseEngine._get_connection()
        try:
            if db_type == "mysql":
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (name, email, username, password_hash, is_premium, free_uses) VALUES (%s, %s, %s, %s, 0, 5)",
                    (name, email, username, hashed_pass)
                )
                conn.commit()
                conn.close()
                return True
            else:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (name, email, username, password_hash, is_premium, free_uses) VALUES (?, ?, ?, ?, 0, 5)",
                    (name, email, username, hashed_pass)
                )
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            logging.error(f"Register Error: {e}")
            if conn: conn.close()
            return False

    @staticmethod
    def update_uses(user_id: int, free_uses: int, is_premium: int = None) -> bool:
        conn, db_type = DatabaseEngine._get_connection()
        try:
            if db_type == "mysql":
                cursor = conn.cursor()
                if is_premium is not None:
                    cursor.execute("UPDATE users SET free_uses = %s, is_premium = %s WHERE id = %s", (free_uses, is_premium, user_id))
                else:
                    cursor.execute("UPDATE users SET free_uses = %s WHERE id = %s", (free_uses, user_id))
                conn.commit()
                conn.close()
                return True
            else:
                cursor = conn.cursor()
                if is_premium is not None:
                    cursor.execute("UPDATE users SET free_uses = ?, is_premium = ? WHERE id = ?", (free_uses, is_premium, user_id))
                else:
                    cursor.execute("UPDATE users SET free_uses = ? WHERE id = ?", (free_uses, user_id))
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            logging.error(f"Update Uses Error: {e}")
            if conn: conn.close()
            return False

    @staticmethod
    def save_project_with_tasks(user_id: int, plan_json: dict) -> bool:
        conn, db_type = DatabaseEngine._get_connection()
        try:
            tech_str = json.dumps(plan_json.get('tech_stack', []))
            if db_type == "mysql":
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO projects (user_id, client_name, summary, tech_stack, budget_range, status) VALUES (%s, %s, %s, %s, %s, %s)",
                    (user_id, plan_json.get('project_name'), plan_json.get('executive_summary'), tech_str, str(plan_json.get('budget')), 'active')
                )
                project_id = cursor.lastrowid
                
                for t in plan_json.get('tasks', []):
                    cursor.execute(
                        "INSERT INTO tasks (project_id, title, description, estimated_days, priority, status) VALUES (%s, %s, %s, %s, %s, %s)",
                        (project_id, t.get('title'), t.get('description'), t.get('days'), t.get('priority'), 'pending')
                    )
                conn.commit()
                conn.close()
                return True
            else:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO projects (user_id, client_name, summary, tech_stack, budget_range, status) VALUES (?, ?, ?, ?, ?, ?)",
                    (user_id, plan_json.get('project_name'), plan_json.get('executive_summary'), tech_str, str(plan_json.get('budget')), 'active')
                )
                project_id = cursor.lastrowid
                
                for t in plan_json.get('tasks', []):
                    cursor.execute(
                        "INSERT INTO tasks (project_id, title, description, estimated_days, priority, status) VALUES (?, ?, ?, ?, ?, ?)",
                        (project_id, t.get('title'), t.get('description'), t.get('days'), t.get('priority'), 'pending')
                    )
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            logging.error(f"Save Project Error: {e}")
            if conn: conn.close()
            return False

    @staticmethod
    def get_projects(user_id: int) -> list:
        conn, db_type = DatabaseEngine._get_connection()
        try:
            if db_type == "mysql":
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM projects WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
                rows = cursor.fetchall()
                conn.close()
                return [dict(r) for r in rows] if rows else []
            else:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM projects WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
                rows = cursor.fetchall()
                conn.close()
                return [dict(r) for r in rows] if rows else []
        except Exception as e:
            logging.error(f"Get Projects Error: {e}")
            if conn: conn.close()
            return []

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
    def hash_password(cls, password: str) -> str:
        if BCRYPT_AVAILABLE:
            salt = bcrypt.gensalt()
            return bcrypt.hashpw(password.encode(), salt).decode()
        return hashlib.sha256(password.encode()).hexdigest()

    @classmethod
    def verify_password(cls, password: str, hashed: str) -> bool:
        if BCRYPT_AVAILABLE and str(hashed).startswith("$2b$"):
            try:
                return bcrypt.checkpw(password.encode(), hashed.encode())
            except Exception:
                return False
        return hashlib.sha256(password.encode()).hexdigest() == hashed

# =====================================================================
# 4. AI GENERATION ENGINE
# =====================================================================
class PhoenixAI:
    @staticmethod
    def generate_architecture(api_key: str, req: dict) -> dict:
        if not api_key:
            return PhoenixAI._mock_fallback(req)
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            prompt = f"""
أنت مهندس معماري لأنظمة البرمجيات في منصة وكيل مهنة PRO.
قم بتحليل متطلبات المشروع التالية وإرجاع نتيجة مخصصة بصيغة JSON فقط:

اسم المشروع: {req['project_name']}
المجال: {req['domain']}
الوصف: {req['scope']}
الميزانية: {req['budget']}
الأيام: {req['target_days']}
التقنيات: {req['tech_stack']}

تنسيق JSON المطلوب:
{{
  "project_name": "{req['project_name']}",
  "domain": "{req['domain']}",
  "executive_summary": "ملخص تنفيذي للمشروع",
  "tech_stack": ["تقنية 1", "تقنية 2"],
  "budget": {req['budget']},
  "target_days": {req['target_days']},
  "tasks": [
    {{"title": "عنوان المهمة", "description": "الوصف التفصيلي", "days": 5, "cost": 500, "priority": "High"}}
  ]
}}
"""
            response = model.generate_content(prompt)
            match = re.search(r"\{.*\}", response.text, re.DOTALL)
            data = json.loads(match.group() if match else response.text)
            data["signature"] = VaultSecurity.sign_payload(data)
            return data
        except Exception as e:
            logging.error(f"AI Error: {e}")
            return PhoenixAI._mock_fallback(req)

    @staticmethod
    def _mock_fallback(req: dict) -> dict:
        b = float(req.get('budget', 3500))
        d = int(req.get('target_days', 30))
        data = {
            "project_name": req.get('project_name', 'مشروع جديد'),
            "domain": req.get('domain', 'عام'),
            "executive_summary": f"خطة هندسية لتطوير {req.get('project_name')}",
            "tech_stack": [t.strip() for t in str(req.get('tech_stack', '')).split(",") if t.strip()],
            "budget": b,
            "target_days": d,
            "tasks": [
                {"title": "التصميم الهندسي المبدئي", "description": "دراسة المخططات وواجهات التفاعل", "days": max(1, int(d*0.2)), "cost": int(b*0.2), "priority": "High"},
                {"title": "تطوير قواعد البيانات والأمن", "description": "إعداد السحابة وإنشاء الجداول والتحقق", "days": max(1, int(d*0.4)), "cost": int(b*0.4), "priority": "High"},
                {"title": "تطوير التطبيق والربط", "description": "برمجة واجهة المستخدم ودمج APIs", "days": max(1, int(d*0.4)), "cost": int(b*0.4), "priority": "Medium"}
            ]
        }
        data["signature"] = VaultSecurity.sign_payload(data)
        return data

# =====================================================================
# 5. AUTHENTICATION CONTROLLER (FIXED LOGIN BUG)
# =====================================================================
def init_session():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "current_plan" not in st.session_state:
        st.session_state.current_plan = None

def render_auth_page():
    st.markdown("<h1 style='text-align: center;'>🔐 بوابة الدخول | وكيل مهنة PRO</h1>", unsafe_allow_html=True)
    
    col_main = st.columns([1, 2, 1])[1]
    with col_main:
        tab_login, tab_signup = st.tabs(["🔑 تسجيل الدخول", "✨ إنشاء حساب جديد"])
        
        with tab_login:
            email = st.text_input("البريد الإلكتروني", key="login_email").lower().strip()
            password = st.text_input("كلمة المرور", type="password", key="login_pass")
            
            if st.button("تسجيل الدخول", use_container_width=True, type="primary"):
                user = DatabaseEngine.get_user(email)
                if user and VaultSecurity.verify_password(password, user["password_hash"]):
                    st.session_state.authenticated = True  # FIX: Match key used in main
                    st.session_state.user = user
                    st.success(f"🎉 أهلاً بك {user['name']}!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ البريد الإلكتروني أو كلمة المرور غير صحيحة.")

        with tab_signup:
            name = st.text_input("الاسم الكامل", key="signup_name")
            username = st.text_input("اسم المستخدم (Username)", key="signup_username").strip()
            email = st.text_input("البريد الإلكتروني", key="signup_email").lower().strip()
            p1 = st.text_input("كلمة المرور", type="password", key="signup_p1")
            p2 = st.text_input("تأكيد كلمة المرور", type="password", key="signup_p2")
            
            if st.button("إنشاء حساب جديد", use_container_width=True):
                if p1 != p2:
                    st.error("⚠️ كلمتا المرور غير متطابقتين.")
                elif name and email and username and p1:
                    hashed = VaultSecurity.hash_password(p1)
                    if DatabaseEngine.register_user(name, email, username, hashed):
                        st.success("✅ تم إنشاء الحساب بنجاح! يمكنك الآن تسجيل الدخول.")
                    else:
                        st.error("❌ البريد أو اسم المستخدم مسجل بالفعل.")

# =====================================================================
# 6. MAIN APPLICATION WORKFLOW
# =====================================================================
def main():
    init_session()

    if not st.session_state.authenticated:
        render_auth_page()
        st.stop()

    user = st.session_state.user

    # Sidebar
    with st.sidebar:
        st.title("🚀 وكيل مهنة PRO")
        st.markdown(f"👤 **{user.get('name')}**")
        st.caption(f"📧 {user.get('email')}")
        st.caption(f"🏷️ Username: @{user.get('username')}")
        
        st.write("---")
        if user.get('is_premium'):
            st.success("👑 حساب ممتاز (Premium)")
        else:
            st.info(f"💳 الاستخدامات المتبقية: {user.get('free_uses', 0)}")
            
        if st.button("🚪 تسجيل الخروج", use_container_width=True):
            st.session_state.clear()
            st.rerun()

        st.write("---")
        api_key = st.text_input("🔑 Gemini API Key", type="password", value=os.getenv("GEMINI_API_KEY", ""))

    # Main Tabs
    st.title("🧠 لوحة تحكم وكيل مهنة PRO")
    tab1, tab2, tab3 = st.tabs(["🏗️ إنشاء مشروع", "📊 تحليلات الخطة", "🗄️ الأرشيف السحابي"])

    with tab1:
        with st.form("project_form"):
            col1, col2 = st.columns(2)
            with col1:
                pname = st.text_input("اسم المشروع", "منصة خدمات سحابية")
                domain = st.selectbox("المجال", ["تطبيقات جوال", "ذكاء اصطناعي", "تجارة إلكترونية", "أنظمة إدارية"])
                budget = st.number_input("الميزانية التقديرية ($)", min_value=100, value=3500)
            with col2:
                days = st.number_input("المدة الزمنية (أيام)", min_value=1, value=30)
                tech = st.text_input("التقنيات", "Flutter, Supabase, Python")
            
            scope = st.text_area("نطاق ومواصفات المشروع")
            
            if st.form_submit_button("🚀 توليد وحفظ الخطة", type="primary"):
                if not user.get('is_premium') and user.get('free_uses', 0) <= 0:
                    st.error("❌ انتهت النقاط المجانية. يرجى الترقية للوصول غير المحدود.")
                else:
                    req = {"project_name": pname, "domain": domain, "budget": budget, "target_days": days, "tech_stack": tech, "scope": scope}
                    plan = PhoenixAI.generate_architecture(api_key, req)
                    
                    if DatabaseEngine.save_project_with_tasks(user['id'], plan):
                        if not user.get('is_premium'):
                            user['free_uses'] -= 1
                            DatabaseEngine.update_uses(user['id'], user['free_uses'])
                        st.session_state.current_plan = plan
                        st.success("✅ تم التوليد بنجاح وحفظ البيانات في Cloud SQL!")
                        st.rerun()

        if st.session_state.current_plan:
            plan = st.session_state.current_plan
            st.divider()
            st.markdown(f"### 📋 الخطة الحالية: {plan.get('project_name')}")
            st.write(plan.get('executive_summary'))
            st.dataframe(pd.DataFrame(plan.get('tasks', [])), use_container_width=True)

    with tab2:
        if st.session_state.current_plan:
            plan = st.session_state.current_plan
            df = pd.DataFrame(plan.get('tasks', []))
            fig = px.bar(df, x='title', y='cost', color='priority', title="توزيع التكاليف على المهام")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("قم بتوليد خطة في تبويب 'إنشاء مشروع' لعرض التحليلات.")

    with tab3:
        st.subheader("🗄️ المشاريع المحفوظة في قاعدة البيانات")
        projects = DatabaseEngine.get_projects(user['id'])
        if projects:
            st.dataframe(pd.DataFrame(projects), use_container_width=True)
        else:
            st.info("لا توجد مشاريع محفوظة سابقاً.")

if __name__ == "__main__":
    main()
