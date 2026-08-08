#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
© 2026 PHOENIX & MIHNA PRO ENTERPRISE ARCHITECTURE v10.0 - ULTIMATE SaaS PLATFORM
محرك معالجة البيانات، الحفظ الدائم (SQLite/Cloud SQL)، وإشعارات WhatsApp
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

# =====================================================================
# 1. CONFIGURATION & LINKS
# =====================================================================
PAYMENT_LINK_MONTHLY = os.getenv("PAYMENT_LINK_MONTHLY", "https://nexus-corestore.lemonsqueezy.com/checkout/buy/e6515270-070e-4fc6-b1ea-60c1aeb9e2d3?plan=monthly")
PAYMENT_LINK_YEARLY = os.getenv("PAYMENT_LINK_YEARLY", "https://nexus-corestore.lemonsqueezy.com/checkout/buy/e6515270-070e-4fc6-b1ea-60c1aeb9e2d3?plan=yearly")

# =====================================================================
# 2. HYBRID DATABASE ENGINE (Cloud SQL + Permanent SQLite Fallback)
# =====================================================================
DB_FILE = "phoenix_app_data.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            credits INTEGER DEFAULT 5,
            plan_status TEXT DEFAULT 'Free Trial (5 Credits)',
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
    admin_email = "eng.alhiadri2020@gmail.com"
    cursor.execute("SELECT email FROM users WHERE email = ?", (admin_email,))
    if not cursor.fetchone():
        hashed_p = hashlib.sha256("123456".encode()).hexdigest()
        cursor.execute(
            "INSERT INTO users (name, email, password, credits, plan_status, is_subscribed) VALUES (?, ?, ?, ?, ?, ?)",
            ("AYAD FAISAL ABDO MOHAMMED", admin_email, hashed_p, 9999, "Enterprise Pro Owner", 1)
        )
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
        if row:
            return dict(row)
        return None

    @classmethod
    def register_user(cls, name: str, email: str, hashed_pass: str) -> bool:
        conn = cls.get_cloud_sql_conn()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO users (name, email, password, credits, plan_status) VALUES (%s, %s, %s, 5, 'Free Trial (5 Credits)')",
                        (name, email, hashed_pass)
                    )
                conn.close()
            except Exception: pass

        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (name, email, password, credits, plan_status, is_subscribed) VALUES (?, ?, ?, 5, 'Free Trial (5 Credits)', 0)",
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
                user_email, plan_json.get('project_name'), plan_json.get('executive_summary'),
                str(plan_json.get('budget')), json.dumps(plan_json.get('tech_stack', [])),
                json.dumps(plan_json, ensure_ascii=False), plan_json.get('signature')
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
    HMAC_KEY = os.getenv("HMAC_SECRET_KEY", "PHOENIX_SECURE_HMAC_KEY_2026_ENTERPRISE_ULTIMATE")

    @classmethod
    def sign_payload(cls, payload: dict) -> str:
        clean_payload = {k: v for k, v in payload.items() if k not in ["signature", "timestamp"]}
        payload_str = json.dumps(clean_payload, sort_keys=True, ensure_ascii=False)
        return hmac.new(cls.HMAC_KEY.encode(), payload_str.encode(), hashlib.sha512).hexdigest()

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
# 4. AI & EXTERNAL NOTIFICATION ENGINE (WhatsApp)
# =====================================================================
class PhoenixAI:
    @staticmethod
    def generate_architecture(api_key: str, req: dict, lang: str = "ar") -> dict:
        if not api_key:
            return PhoenixAI._mock_fallback(req)
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            prompt = f"Create JSON architecture plan for project {req['project_name']} with tasks, cost, days and priority."
            response = model.generate_content(prompt)
            match = re.search(r"\{.*\}", response.text, re.DOTALL)
            data = json.loads(match.group() if match else response.text)
            data["signature"] = VaultSecurity.sign_payload(data)
            data["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            return data
        except Exception:
            return PhoenixAI._mock_fallback(req)

    @staticmethod
    def _mock_fallback(req: dict) -> dict:
        b = req['budget']
        d = req['target_days']
        tasks = [
            {"id": 1, "task": "تحليل المتطلبات وتصميم المعمارية HLD/LLD", "days": max(1, int(d*0.15)), "cost": int(b*0.15), "priority": "High"},
            {"id": 2, "task": "بناء قواعد البيانات وتأمين APIs RLS", "days": max(1, int(d*0.35)), "cost": int(b*0.35), "priority": "High"},
            {"id": 3, "task": "تطوير واجهات المستخدم Frontend UI Components", "days": max(1, int(d*0.30)), "cost": int(b*0.30), "priority": "Medium"},
            {"id": 4, "task": "الاختبارات الشاملة والتكامل QA Deployment", "days": max(1, int(d*0.20)), "cost": int(b*0.20), "priority": "Low"}
        ]
        data = {
            "project_name": req['project_name'], "domain": req['domain'],
            "executive_summary": f"خطة هندسية لمشروع ({req['project_name']}) بتصميم فائق الجودة والأمان.",
            "tech_stack": [t.strip() for t in req['tech_stack'].split(",")],
            "budget": b, "target_days": d, "risk": req['risk'],
            "risk_score": 30, "confidence_score": 92, "tasks": tasks
        }
        data["signature"] = VaultSecurity.sign_payload(data)
        data["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        return data

class NotificationEngine:
    @staticmethod
    def send_whatsapp_link(phone_number: str, message: str):
        encoded_msg = urllib.parse.quote(message)
        clean_phone = re.sub(r'[^\d]', '', phone_number)
        return f"https://wa.me/{clean_phone}?text={encoded_msg}"

# =====================================================================
# 5. UI & APP ENGINE
# =====================================================================
def init_session():
    if "authenticated" not in st.session_state: st.session_state.authenticated = False
    if "current_user" not in st.session_state: st.session_state.current_user = None
    if "selected_plan" not in st.session_state: st.session_state.selected_plan = None

def main():
    st.set_page_config(page_title="PHOENIX PRO SaaS", page_icon="🚀", layout="wide")
    init_session()

    # ---- تسجيل الدخول والإنشاء الاحترافي ----
    if not st.session_state.authenticated:
        st.markdown("<h2 style='text-align:center;'>🚀 تسجيل الدخول إلى PHOENIX PRO</h2>", unsafe_allow_html=True)
        tab_log, tab_reg = st.tabs(["🔑 تسجيل الدخول", "📝 حساب جديد (5 محاولات مجانية)"])
        
        with tab_log:
            with st.form("login_form"):
                e = st.text_input("البريد الإلكتروني").strip().lower()
                p = st.text_input("كلمة المرور", type="password")
                submit_login = st.form_submit_button("تسجيل الدخول", type="primary", use_container_width=True)
                
                if submit_login:
                    u = DatabaseEngine.get_user(e)
                    if u and VaultSecurity.verify_password(p, u["password"]):
                        st.session_state.authenticated = True
                        st.session_state.current_user = u
                        st.success("تم الدخول بنجاح!")
                        st.rerun()
                    else:
                        st.error("بيانات الدخول غير صحيحة.")

        with tab_reg:
            with st.form("register_form"):
                name = st.text_input("الاسم الكامل")
                email = st.text_input("البريد الإلكتروني للتمكين").strip().lower()
                pass1 = st.text_input("كلمة سر الحساب", type="password")
                pass2 = st.text_input("تأكيد كلمة السر", type="password")
                submit_reg = st.form_submit_button("إنشاء حساب وتفعيل 5 محاولات", use_container_width=True)

                if submit_reg:
                    if not name or not email or not pass1 or not pass2:
                        st.error("❌ يرجى ملء جميع الحقول المطلوب.")
                    elif pass1 != pass2:
                        st.error("❌ كلمة السر وتأكيد كلمة السر غير متطابقين.")
                    elif len(pass1) < 6:
                        st.error("❌ يجب أن تتكون كلمة السر من 6 خانات على الأقل.")
                    else:
                        h_pass = VaultSecurity.hash_password(pass1)
                        if DatabaseEngine.register_user(name, email, h_pass):
                            st.success("✅ تم إنشاء الحساب بنجاح! يتم نقلك الآن...")
                            # تسجيل دخول تلقائي فور النواح
                            new_u = DatabaseEngine.get_user(email)
                            st.session_state.authenticated = True
                            st.session_state.current_user = new_u
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ البريد الإلكتروني مسجل مسبقاً، يرجى تسجيل الدخول.")
        return

    # ---- الواجهة الرئيسية بعد الدخول ----
    user = st.session_state.current_user
    db_user_fresh = DatabaseEngine.get_user(user['email'])
    if db_user_fresh: user = db_user_fresh

    # الشريط الجانبي (Sidebar)
    with st.sidebar:
        st.markdown(f"### 👤 {user['name']}")
        st.markdown(f"💳 **الرصيد:** `{user['credits']}` محاولات")
        st.markdown(f"📌 **الاشتراك:** `{user['plan_status']}`")
        
        st.divider()
        st.markdown("### 📲 إشعارات WhatsApp")
        wa_phone = st.text_input("رقم الواتساب (مع رمز الدولة)", value="+967")
        
        st.divider()
        st.markdown("### 🛒 الترقية وروابط الاشتراك")
        st.markdown(f"[💳 اشتراك شهري ($29)]({PAYMENT_LINK_MONTHLY})")
        st.markdown(f"[👑 اشتراك سنوي ($279)]({PAYMENT_LINK_YEARLY})")

        if st.button("🚪 تسجيل الخروج", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.rerun()

    st.markdown("<h1 style='text-align:center;'>🚀 PHOENIX & MIHNA PRO ARCHITECTURE</h1>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🏗️ بناء خطة المشروع", "📊 التحليلات الـ 5D", "🗄️ الأرشيف والتسجيل"])

    with tab1:
        st.subheader("إدخال بيانات المشروع")
        p_name = st.text_input("اسم المشروع", value="منصة تجارة سحابية")
        domain = st.selectbox("المجال التقني", ["التجارة الإلكترونية", "الذكاء الاصطناعي", "أنظمة SaaS"])
        budget = st.number_input("الميزانية ($)", value=3000)
        days = st.number_input("المدة (يوم)", value=20)
        tech = st.text_input("التقنيات", value="Flutter, Node.js, PostgreSQL")
        scope = st.text_area("وصف المشروع", value="بناء تطبيق منصة تجارية متكاملة مع الدفع والتكامل السحابي.")

        if st.button("⚡ توليد الخطة وتوقيعها", type="primary", use_container_width=True):
            if user['credits'] <= 0 and not user['is_subscribed']:
                st.error("❌ انتهت المحاولات المجانية الـ 5. يرجى الترقية للاستمرار.")
            else:
                req = {"project_name": p_name, "domain": domain, "budget": budget, "target_days": days, "tech_stack": tech, "scope": scope, "risk": "متوسط"}
                plan = PhoenixAI.generate_architecture("", req)
                DatabaseEngine.save_project(plan, user['email'])
                
                if not user['is_subscribed']:
                    new_c = max(0, user['credits'] - 1)
                    DatabaseEngine.update_credits(user['email'], new_c)
                
                st.session_state.selected_plan = plan
                st.success("✅ تم التوليد والحفظ بنجاح في قاعدة البيانات!")
                st.rerun()

        if st.session_state.selected_plan:
            plan = st.session_state.selected_plan
            st.divider()
            st.json(plan)
            
            wa_msg = f"🚀 مشروع جديد: {plan['project_name']}\n💰 الميزانية: ${plan['budget']}\n🔑 التوقيع: {plan['signature'][:20]}..."
            wa_url = NotificationEngine.send_whatsapp_link(wa_phone, wa_msg)
            st.markdown(f'<a href="{wa_url}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:10px 20px; border-radius:8px; font-weight:bold; cursor:pointer;">📲 إرسال تفاصيل المشروع عبر WhatsApp</button></a>', unsafe_allow_html=True)

            st.divider()
            st.markdown("### 📥 التصدير")
            col_ex1, col_ex2 = st.columns(2)
            with col_ex1:
                st.download_button("📦 تصدير ملف JSON", json.dumps(plan, ensure_ascii=False), "plan.json", "application/json")
            with col_ex2:
                if OPENPYXL_AVAILABLE:
                    buffer = io.BytesIO()
                    pd.DataFrame(plan.get("tasks", [])).to_excel(buffer, index=False)
                    st.download_button("📊 تصدير Excel", buffer.getvalue(), "tasks.xlsx")
                else:
                    csv_data = pd.DataFrame(plan.get("tasks", [])).to_csv(index=False).encode('utf-8')
                    st.download_button("📄 تصدير CSV (بديل Excel الآمن)", csv_data, "tasks.csv", "text/csv")

    with tab2:
        if st.session_state.selected_plan:
            plan = st.session_state.selected_plan
            df = pd.DataFrame(plan.get("tasks", []))
            st.plotly_chart(px.bar(df, x="task", y="cost", title="توزيع التكاليف حسب المهام"), use_container_width=True)
        else:
            st.info("قم بتوليد مشروع أولاً لعرض التحليلات.")

    with tab3:
        st.subheader("🗄️ المشاريع المحفوظة دائماً للمستخدم")
        projs = DatabaseEngine.get_projects(user['email'])
        if projs:
            st.dataframe(pd.DataFrame(projs), use_container_width=True)
        else:
            st.info("لا توجد مشاريع محفوظة حالياً.")

if __name__ == "__main__":
    main()
