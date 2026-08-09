#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
© 2026 PHOENIX & WAKEEL MEHNA PRO - ULTIMATE FUSION v12.0
متوافق تماماً مع Cloud SQL Schema (users, projects, tasks)
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

import streamlit as st
import pandas as pd
import numpy as np
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
# 1. CONFIGURATION
# =====================================================================
APP_TITLE = "🧠 وكيل مهنة PRO | Ultimate Fusion"
PAYMENT_LINK_MONTHLY = os.getenv("PAYMENT_LINK_MONTHLY", "https://nexus-corestore.lemonsqueezy.com/checkout/buy/e6515270-070e-4fc6-b1ea-60c1aeb9e2d3?plan=monthly")
PAYMENT_LINK_YEARLY = os.getenv("PAYMENT_LINK_YEARLY", "https://nexus-corestore.lemonsqueezy.com/checkout/buy/e6515270-070e-4fc6-b1ea-60c1aeb9e2d3?plan=yearly")
SECRET_HMAC_KEY = os.getenv("HMAC_SECRET_KEY", "PHOENIX_ULTIMATE_SECURE_KEY_2026")
DB_FILE = "phoenix_ultimate.db"

CLOUD_SQL_CONNECTION_NAME = os.getenv("CLOUD_SQL_CONNECTION_NAME", "project-d699d925-921c-4e54-8c4:asia-south1:mihna-agent")
DB_USER = os.getenv("DB_USER", "mihna_app_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "101519Ayad@")
DB_NAME = os.getenv("DB_NAME", "mihna_agent")

st.set_page_config(
    page_title="وكيل مهنة PRO",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================================
# 2. DATABASE ENGINE (MATCHING EXACT CLOUD SQL SCHEMA)
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
        return None
    except Exception as e:
        logging.error(f"MySQL Error: {e}")
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
            is_premium BOOLEAN DEFAULT 0,
            free_uses INTEGER DEFAULT 5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
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
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (project_id) REFERENCES projects (id)
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
                cursor.execute("SELECT * FROM users WHERE email = %s OR username = %s", (email, email))
                user = cursor.fetchone()
                conn.close()
                return dict(user) if user else None
            else:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE email = ? OR username = ?", (email, email))
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
    def update_uses(email: str, free_uses: int, is_premium: bool = False) -> bool:
        conn, db_type = DatabaseEngine._get_connection()
        try:
            if db_type == "mysql":
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users SET free_uses = %s, is_premium = %s WHERE email = %s",
                    (free_uses, 1 if is_premium else 0, email)
                )
                conn.commit()
                conn.close()
                return True
            else:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users SET free_uses = ?, is_premium = ? WHERE email = ?",
                    (free_uses, 1 if is_premium else 0, email)
                )
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            logging.error(f"Update Uses Error: {e}")
            if conn: conn.close()
            return False

    @staticmethod
    def save_project_with_tasks(user_id: str, plan_json: dict) -> bool:
        conn, db_type = DatabaseEngine._get_connection()
        try:
            tech_str = json.dumps(plan_json.get('tech_stack', [])) if isinstance(plan_json.get('tech_stack'), list) else str(plan_json.get('tech_stack', ''))
            if db_type == "mysql":
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO projects (user_id, client_name, summary, tech_stack, budget_range, status)
                    VALUES (%s, %s, %s, %s, %s, 'active')
                    """,
                    (
                        user_id,
                        plan_json.get('project_name', 'مشروع غير معنون'),
                        plan_json.get('executive_summary', ''),
                        tech_str,
                        str(plan_json.get('budget', 0))
                    )
                )
                project_id = cursor.lastrowid
                for t in plan_json.get('tasks', []):
                    cursor.execute(
                        """
                        INSERT INTO tasks (project_id, title, description, estimated_days, priority, status)
                        VALUES (%s, %s, %s, %s, %s, 'pending')
                        """,
                        (project_id, t.get('title'), t.get('description'), t.get('days', 1), t.get('priority', 'Medium'))
                    )
                conn.commit()
                conn.close()
                return True
            else:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO projects (user_id, client_name, summary, tech_stack, budget_range, status)
                    VALUES (?, ?, ?, ?, ?, 'active')
                    """,
                    (
                        user_id,
                        plan_json.get('project_name', 'مشروع غير معنون'),
                        plan_json.get('executive_summary', ''),
                        tech_str,
                        str(plan_json.get('budget', 0))
                    )
                )
                project_id = cursor.lastrowid
                for t in plan_json.get('tasks', []):
                    cursor.execute(
                        """
                        INSERT INTO tasks (project_id, title, description, estimated_days, priority, status)
                        VALUES (?, ?, ?, ?, ?, 'pending')
                        """,
                        (project_id, t.get('title'), t.get('description'), t.get('days', 1), t.get('priority', 'Medium'))
                    )
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            logging.error(f"Save Relational Project Error: {e}")
            if conn: conn.close()
            return False

    @staticmethod
    def get_projects(user_id: str) -> list:
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
# 3. SECURITY & AI ENGINES
# =====================================================================
class VaultSecurity:
    @classmethod
    def sign_payload(cls, payload: dict) -> str:
        clean = {k: v for k, v in payload.items() if k not in ["signature", "timestamp", "generated_at"]}
        p_str = json.dumps(clean, sort_keys=True, ensure_ascii=False)
        return hmac.new(SECRET_HMAC_KEY.encode(), p_str.encode(), hashlib.sha512).hexdigest()

    @classmethod
    def hash_password(cls, password: str) -> str:
        if BCRYPT_AVAILABLE:
            return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        return hashlib.sha256(password.encode()).hexdigest()

    @classmethod
    def verify_password(cls, password: str, hashed: str) -> bool:
        if BCRYPT_AVAILABLE and str(hashed).startswith("$2b$"):
            try:
                return bcrypt.checkpw(password.encode(), hashed.encode())
            except Exception:
                return False
        return hashlib.sha256(password.encode()).hexdigest() == hashed

class PhoenixAI:
    @staticmethod
    def generate_architecture(api_key: str, req: dict, lang: str = "ar") -> dict:
        if not api_key:
            return PhoenixAI._fallback(req)
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            prompt = f"""
أنت خبير مهندس برمجيات ومطور أنظمة. أنشئ خطة عمل لمشروع:
- الاسم: {req['project_name']}
- المجال: {req['domain']}
- النطاق: {req['scope']}
- الميزانية: {req['budget']}
- المدة بالأيام: {req['target_days']}

أخرج النتيجة بتنسيق JSON حصراً بالشكل التالي:
{{
  "project_name": "{req['project_name']}",
  "domain": "{req['domain']}",
  "executive_summary": "ملخص شامل باللغة العربية",
  "tech_stack": ["Flutter", "Node.js"],
  "budget": {req['budget']},
  "target_days": {req['target_days']},
  "tasks": [
    {{"title": "تصميم النظام", "description": "وصف المهمة", "days": 5, "cost": 500, "priority": "High"}}
  ]
}}
"""
            res = model.generate_content(prompt)
            match = re.search(r"\{.*\}", res.text, re.DOTALL)
            data = json.loads(match.group() if match else res.text)
            data["signature"] = VaultSecurity.sign_payload(data)
            data["generated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            return data
        except Exception:
            return PhoenixAI._fallback(req)

    @staticmethod
    def _fallback(req: dict) -> dict:
        b = float(req.get('budget', 3500))
        d = int(req.get('target_days', 30))
        data = {
            "project_name": req.get('project_name', 'مشروع جديد'),
            "domain": req.get('domain', 'عام'),
            "executive_summary": f"خطة عمل هندسية متكاملة لمشروع {req.get('project_name')}.",
            "tech_stack": [t.strip() for t in str(req.get('tech_stack', '')).split(",") if t.strip()],
            "budget": b,
            "target_days": d,
            "tasks": [
                {"title": "تحليل المتطلبات وتصميم المخططات", "description": "دراسة جدوى وتصميم معمارية النظام.", "days": max(1, int(d*0.2)), "cost": int(b*0.2), "priority": "High"},
                {"title": "بناء قواعد البيانات و APIs", "description": "إعداد Cloud SQL وتطوير واجهات البرمجة.", "days": max(1, int(d*0.4)), "cost": int(b*0.4), "priority": "High"},
                {"title": "تطوير واجهات الواجهة والتكامل", "description": "ربط الشاشات وتفعيل الاختبارات.", "days": max(1, int(d*0.4)), "cost": int(b*0.4), "priority": "Medium"}
            ],
            "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        data["signature"] = VaultSecurity.sign_payload(data)
        return data

# =====================================================================
# 4. AUTHENTICATION & SESSION MANAGEMENT
# =====================================================================
def render_auth_page():
    st.markdown("<h1 style='text-align: center;'>🔐 بوابة الدخول | وكيل مهنة PRO</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        tab_login, tab_signup = st.tabs(["🔑 تسجيل الدخول", "✨ إنشاء حساب جديد"])
        with tab_login:
            login_input = st.text_input("البريد الإلكتروني أو اسم المستخدم", key="login_input").lower().strip()
            password = st.text_input("كلمة المرور", type="password", key="login_pass")
            if st.button("تسجيل الدخول", use_container_width=True, type="primary"):
                user = DatabaseEngine.get_user(login_input)
                if user and VaultSecurity.verify_password(password, user["password_hash"]):
                    # توحيد اسم المبيّن في Session State
                    st.session_state.is_authenticated = True
                    st.session_state.user = {
                        'id': str(user['id']),
                        'email': user['email'],
                        'name': user['name'],
                        'username': user.get('username', user['email']),
                        'is_premium': bool(user['is_premium']),
                        'free_uses': user['free_uses']
                    }
                    st.success(f"🎉 أهلاً بك {user['name']}!")
                    st.rerun()
                else:
                    st.error("❌ بيانات الدخول غير صحيحة.")
        with tab_signup:
            name = st.text_input("الاسم الكامل", key="signup_name")
            username = st.text_input("اسم المستخدم (Username)", key="signup_username").lower().strip()
            email = st.text_input("البريد الإلكتروني", key="signup_email").lower().strip()
            p1 = st.text_input("كلمة المرور", type="password", key="signup_p1")
            p2 = st.text_input("تأكيد كلمة المرور", type="password", key="signup_p2")
            if st.button("إنشاء حساب جديد", use_container_width=True):
                if p1 != p2: st.error("⚠️كلمات المرور غير متطابقة.")
                elif name and email and p1 and username:
                    hashed = VaultSecurity.hash_password(p1)
                    if DatabaseEngine.register_user(name, email, username, hashed):
                        st.success("✅ تم إنشاء الحساب بنجاح! يمكنك الدخول الآن.")
                    else: st.error("❌ البريد الإلكتروني أو اسم المستخدم مسجل مسبقاً.")

# =====================================================================
# 5. MAIN APPLICATION
# =====================================================================
def main():
    if "is_authenticated" not in st.session_state:
        st.session_state.is_authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "current_plan" not in st.session_state:
        st.session_state.current_plan = None

    if not st.session_state.is_authenticated:
        render_auth_page()
        st.stop()

    user = st.session_state.user

    # Sidebar
    with st.sidebar:
        st.title("🚀 وكيل مهنة PRO")
        st.caption("نسخة المسابقات المعمارية v12.0")
        st.write("---")
        st.markdown(f"👤 **{user['name']}**")
        st.caption(f"📧 {user['email']}")
        st.caption(f"🆔 @{user['username']}")
        
        if user['is_premium']:
            st.success("👑 حساب ممتاز (Unlimited)")
        else:
            st.info(f"💳 الاستخدامات المتبقية: {user['free_uses']}")

        if st.button("🚪 تسجيل الخروج", use_container_width=True):
            st.session_state.clear()
            st.rerun()

        st.write("---")
        api_key = st.text_input("🔑 Gemini API Key", type="password", value=os.getenv("GEMINI_API_KEY", ""))

    # Main Interface Body
    st.title(f"🧠 {APP_TITLE}")
    
    tab1, tab2, tab3 = st.tabs(["🏗️ إنشاء خطة مشروع", "📊 تحليلات وهندسة", "🗄️ أرشيف Cloud SQL"])

    with tab1:
        with st.form("build_form"):
            col1, col2 = st.columns(2)
            with col1:
                pname = st.text_input("اسم المشروع", value="منصة خدمة تجارية")
                domain = st.selectbox("المجال", ["التجارة الإلكترونية", "الذكاء الاصطناعي", "التعليم الرقمي", "اللوجستيات"])
                budget = st.number_input("الميزانية التقديرية ($)", min_value=500, value=3000)
            with col2:
                tech = st.text_input("التقنيات المستهدفة", "Flutter, Supabase, Python Cloud Run")
                days = st.number_input("المدة (أيام)", min_value=5, value=20)
            scope = st.text_area("نطاق العمل والمتطلبات الأساسية", value="تطوير نظام متكامل مع لوحة تحكم وإدارات سحابية.")
            
            if st.form_submit_button("🚀 توليد وتخزين في Cloud SQL", type="primary"):
                if not user['is_premium'] and user['free_uses'] <= 0:
                    st.error("❌ نفذت نقاطك المجانية! نرجو الترقية.")
                else:
                    req = {"project_name": pname, "domain": domain, "budget": budget, "target_days": days, "tech_stack": tech, "scope": scope}
                    plan = PhoenixAI.generate_architecture(api_key, req)
                    
                    # حفظ العلاقات الكاملة
                    if DatabaseEngine.save_project_with_tasks(user['id'], plan):
                        if not user['is_premium']:
                            user['free_uses'] -= 1
                            DatabaseEngine.update_uses(user['email'], user['free_uses'])
                        st.session_state.current_plan = plan
                        st.success("✅ تم توليد الخطة وحفظ المشروع مع المهام في Cloud SQL بنجاح!")
                        st.rerun()

        if st.session_state.current_plan:
            plan = st.session_state.current_plan
            st.divider()
            st.subheader(f"📋 الخطة التنفيذية: {plan['project_name']}")
            st.info(f"🔑 التوقيع الرقمي HMAC-SHA512: `{plan.get('signature')}`")
            st.write(plan.get('executive_summary'))
            st.dataframe(pd.DataFrame(plan.get('tasks', [])), use_container_width=True)

    with tab2:
        if st.session_state.current_plan:
            plan = st.session_state.current_plan
            df = pd.DataFrame(plan.get('tasks', []))
            st.markdown("## 📊 التحليلات الهندسية")
            m1, m2 = st.columns(2)
            m1.metric("💰 إجمالي الميزانية", f"${plan['budget']:,}")
            m2.metric("⏱️ إجمالي الأيام", f"{plan['target_days']} يوم")
            
            fig = px.bar(df, x='title', y='days', color='priority', title="توزيع الأيام حسب الأولوية")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("قم بتوليد خطة من التبويب الأول لعرض التحليلات.")

    with tab3:
        st.subheader("🗄️ المشاريع المحفوظة في قاعدة البيانات (Cloud SQL)")
        projects = DatabaseEngine.get_projects(user['id'])
        if projects:
            st.dataframe(pd.DataFrame(projects), use_container_width=True)
        else:
            st.info("لا توجد مشاريع سابقة في حسابك.")

if __name__ == "__main__":
    main()
