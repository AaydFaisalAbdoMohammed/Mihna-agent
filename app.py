#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
© 2026 PHOENIX & MIHNA AGENT PRO - Ultimate Enterprise (دمج الكود 7 و 1)
يعمل تلقائياً: محلياً (SQLite) وسحابياً (MySQL Cloud SQL)
===============================================================================
"""

import os
import re
import json
import uuid
import hashlib
import hmac
import secrets
import logging
import requests
import datetime
import urllib.parse
import sqlite3
from io import BytesIO

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai

# ----------------- Dependency Handling -----------------
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
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# =====================================================================
# 1. TRANSLATION & DICTIONARY ENGINE
# =====================================================================
TRANSLATIONS = {
    "ar": {
        "title": "🧠 وكيل مهنة & PHOENIX PRO",
        "subtitle": "منصة إدارة المشاريع والهندسة المعمارية الذكية والمشفرة",
        "login_tab": "🔑 تسجيل الدخول",
        "signup_tab": "📝 حساب جديد",
        "email": "البريد الإلكتروني / اسم المستخدم",
        "password": "كلمة المرور",
        "confirm_password": "تأكيد كلمة المرور",
        "full_name": "الاسم الكامل / اسم المنظمة",
        "login_btn": "تسجيل الدخول",
        "signup_btn": "إنشاء حساب",
        "logout": "🚪 تسجيل الخروج",
        "user": "المستخدم",
        "credits": "⚡ المحاولات المتبقية",
        "plan": "نوع الاشتراك",
        "gemini_key": "🔑 مفتاح Gemini API",
        "tg_title": "📲 إشعارات Telegram",
        "wa_title": "📲 إشعارات WhatsApp",
        "sub_title": "💳 الترقية والاشتراكات",
        "tab_gen": "🚀 إنشاء خطة وهندسة جديدة",
        "tab_analytics": "📊 التحليلات التفاعلية",
        "tab_dashboard": "🗄️ أرشيف مشاريعك",
        "tab_export": "📦 التصدير والتوثيق",
        "client": "🏢 اسم العميل / الشركة",
        "budget": "💰 الميزانية المقدرة",
        "timeline": "⏱️ الجدول الزمني",
        "tech": "🛠️ التقنيات المفضلة",
        "scope": "💡 صف رؤية أو فكرة مشروعك بالتفصيل",
        "generate_btn": "🚀 توليد الخطة والتوقيع المشفر",
        "export_json": "📦 تصدير JSON المشفر",
        "export_excel": "📊 تصدير جدول Excel",
        "export_pdf": "📄 تصدير تقرير PDF",
        "export_txt": "📝 تصدير نصي (TXT)",
        "activate_code": "رمز التفعيل / الكوبون",
        "activate_btn": "تفعيل الكود",
    },
    "en": {
        "title": "🧠 MIHNA & PHOENIX PRO ENTERPRISE",
        "subtitle": "AI-Powered Architecture & Project Engineering Management",
        "login_tab": "🔑 Login",
        "signup_tab": "📝 Sign Up",
        "email": "Email / Username",
        "password": "Password",
        "confirm_password": "Confirm Password",
        "full_name": "Full Name / Organization",
        "login_btn": "Sign In",
        "signup_btn": "Create Account",
        "logout": "🚪 Logout",
        "user": "User",
        "credits": "⚡ Remaining Credits",
        "plan": "Current Plan",
        "gemini_key": "🔑 Gemini API Key",
        "tg_title": "📲 Telegram Alerts",
        "wa_title": "📲 WhatsApp Alerts",
        "sub_title": "💳 Subscriptions & Upgrades",
        "tab_gen": "🚀 Generate Architecture Plan",
        "tab_analytics": "📊 Interactive Analytics",
        "tab_dashboard": "🗄️ Projects Archive",
        "tab_export": "📦 Secure Export",
        "client": "🏢 Client / Company Name",
        "budget": "💰 Estimated Budget",
        "timeline": "⏱️ Target Timeline",
        "tech": "🛠️ Preferred Tech Stack",
        "scope": "💡 Project Vision / Detailed Scope",
        "generate_btn": "🚀 Generate Architecture & Sign",
        "export_json": "📦 Export Signed JSON",
        "export_excel": "📊 Export Excel Sheet",
        "export_pdf": "📄 Export PDF Document",
        "export_txt": "📝 Export Text (TXT)",
        "activate_code": "Activation Code",
        "activate_btn": "Activate Code",
    }
}

# =====================================================================
# 2. SECURITY ENGINE (BCRYPT + HMAC)
# =====================================================================
class VaultSecurity:
    HMAC_KEY = os.getenv("HMAC_KEY", secrets.token_hex(32))

    @classmethod
    def sign_payload(cls, payload: dict) -> str:
        clean_payload = {k: v for k, v in payload.items() if k not in ["signature", "timestamp"]}
        payload_str = json.dumps(clean_payload, sort_keys=True, ensure_ascii=False)
        return hmac.new(cls.HMAC_KEY.encode(), payload_str.encode(), hashlib.sha512).hexdigest()[:32]

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
# 3. HYBRID DATABASE ENGINE (SQLite Local + Cloud SQL MySQL)
# =====================================================================
DB_FILE = "phoenix_ultimate.db"

class DatabaseEngine:
    @staticmethod
    def init_db():
        # SQLite Local fallback
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                email TEXT UNIQUE,
                password TEXT,
                credits INTEGER DEFAULT 5,
                plan_status TEXT DEFAULT 'Free Trial',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
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

    @staticmethod
    def get_db_connection():
        # 1. Try MySQL via Cloud SQL (For Production)
        try:
            if PYMYSQL_AVAILABLE and os.getenv("CLOUD_SQL_CONNECTION_NAME"):
                conn = pymysql.connect(
                    unix_socket=f"/cloudsql/{os.getenv('CLOUD_SQL_CONNECTION_NAME')}",
                    user=os.getenv("DB_USER", "root"),
                    password=os.getenv("DB_PASSWORD", ""),
                    database=os.getenv("DB_NAME", "mihna_agent"),
                    cursorclass=pymysql.cursors.DictCursor,
                    autocommit=True
                )
                return conn
        except Exception:
            pass
        # 2. Fallback to Local SQLite (For Local Development)
        return None 

    @classmethod
    def get_user(cls, identifier: str):
        conn = cls.get_db_connection()
        if conn:
            try:
                with conn.cursor() as c:
                    c.execute("SELECT * FROM users WHERE email = %s OR username = %s", (identifier, identifier))
                    return c.fetchone()
            finally:
                conn.close()

        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ? OR username = ?", (identifier, identifier))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None

    @classmethod
    def register_user(cls, username: str, email: str, hashed_pass: str, credits=5, plan_status="Free Trial"):
        conn = cls.get_db_connection()
        if conn:
            try:
                with conn.cursor() as c:
                    c.execute("INSERT INTO users (username, email, password, credits, plan_status) VALUES (%s, %s, %s, %s, %s)",
                              (username, email, hashed_pass, credits, plan_status))
                    return True
            except Exception:
                return False
            finally:
                conn.close()

        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("INSERT INTO users (username, email, password, credits, plan_status) VALUES (?, ?, ?, ?, ?)",
                      (username, email, hashed_pass, credits, plan_status))
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    @classmethod
    def update_credits(cls, identifier: str, credits: int, status: str = None):
        conn = cls.get_db_connection()
        if conn:
            try:
                with conn.cursor() as c:
                    if status:
                        c.execute("UPDATE users SET credits=%s, plan_status=%s WHERE email=%s OR username=%s", (credits, status, identifier, identifier))
                    else:
                        c.execute("UPDATE users SET credits=%s WHERE email=%s OR username=%s", (credits, identifier, identifier))
                return True
            finally:
                conn.close()

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        if status:
            c.execute("UPDATE users SET credits=?, plan_status=? WHERE email=? OR username=?", (credits, status, identifier, identifier))
        else:
            c.execute("UPDATE users SET credits=? WHERE email=? OR username=?", (credits, identifier, identifier))
        conn.commit()
        conn.close()
        return True

    @classmethod
    def save_project(cls, identifier: str, plan_json: dict):
        # Save to Cloud SQL
        conn = cls.get_db_connection()
        if conn:
            try:
                with conn.cursor() as c:
                    c.execute("""
                        INSERT INTO projects (user_id, client_name, summary, budget_range, tech_stack, payload, signature)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        identifier, plan_json.get('client', 'غير محدد'), plan_json.get('executive_summary', ''),
                        plan_json.get('budget_str', ''), json.dumps(plan_json.get('tech_stack', [])),
                        json.dumps(plan_json, ensure_ascii=False), plan_json.get('signature', '')
                    ))
                return True
            except Exception:
                return False
            finally:
                conn.close()

        # Fallback to SQLite
        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("""
                INSERT INTO projects (user_id, client_name, summary, budget_range, tech_stack, payload, signature)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                identifier, plan_json.get('client'), plan_json.get('executive_summary'),
                plan_json.get('budget_str'), json.dumps(plan_json.get('tech_stack', [])),
                json.dumps(plan_json, ensure_ascii=False), plan_json.get('signature')
            ))
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    @classmethod
    def get_projects(cls, identifier: str):
        conn = cls.get_db_connection()
        if conn:
            try:
                with conn.cursor() as c:
                    c.execute("SELECT id, client_name, summary, budget_range, created_at, signature FROM projects WHERE user_id = %s ORDER BY created_at DESC", (identifier,))
                    return c.fetchall()
            finally:
                conn.close()

        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT id, client_name, summary, budget_range, created_at, signature FROM projects WHERE user_id = ? ORDER BY created_at DESC", (identifier,))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

    @classmethod
    def get_similar_projects(cls, keyword: str, top_k: int = 2) -> list:
        # RAG Search via SQLite (Simplified)
        try:
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            words = [w for w in re.findall(r'\w+', keyword) if len(w) > 3]
            if not words:
                return []
            conditions = " OR ".join(["(summary LIKE ? OR client_name LIKE ?)" for _ in words[:3]])
            params = []
            for w in words[:3]:
                pattern = f"%{w}%"
                params.extend([pattern, pattern])
            c.execute(f"SELECT summary, client_name FROM projects WHERE {conditions} LIMIT {top_k}", params)
            return c.fetchall()
        except Exception:
            return []

# =====================================================================
# 4. AI CORE ENGINE (GEMINI + RAG)
# =====================================================================
class PhoenixAI:
    @staticmethod
    def generate_architecture(api_key: str, req: dict, lang: str = "ar") -> dict:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        similar = DatabaseEngine.get_similar_projects(req.get("desc", ""), top_k=2)
        context = ""
        if similar:
            context = "\n\n**📚 مشاريع سابقة مشابهة (RAG Memory Context):**\n"
            for p in similar:
                context += f"- {p.get('summary', '')[:150]}...\n"

        lang_str = "اللغة العربية" if lang == "ar" else "English Language"
        prompt = f"""
أنت مهندس معمارية نظم وخبير إدارة مشاريع برمجية.
قم بتحليل متطلبات المشروع التالية لبناء خطة عمل وتنفيذ هيكلية كاملة:

📋 **البيانات والمدخلات:**
- العميل / المنظمة: {req['client']}
- النطاق والرؤية: {req['desc']}
- الميزانية المستهدفة: {req['budget']}
- الجدول الزمني: {req['timeline']}
- التقنيات التفضيلية: {req['tech']}
{context}

🎯 **المطلوب:**
قم بتوليد استجابة بصيغة JSON فقط بالتنسيق التالي:
{{
  "client": "{req['client']}",
  "executive_summary": "ملخص تنفيذي هندسي شامل باللغة ({lang_str})",
  "tech_stack": ["تقنية 1", "تقنية 2", "تقنية 3"],
  "budget_str": "{req['budget']}",
  "timeline": "{req['timeline']}",
  "risk_score": 25,
  "confidence_score": 90,
  "tasks": [
    {{
      "title": "عنوان المهمة",
      "description": "وصف تفصيلي ودقيق للمهمة",
      "days": 4,
      "cost": 600,
      "priority": "High"
    }}
  ]
}}
"""
        try:
            response = model.generate_content(prompt)
            raw = response.text
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                data = json.loads(match.group())
            else:
                data = json.loads(raw.strip())

            data["signature"] = VaultSecurity.sign_payload(data)
            data["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            return data
        except Exception as e:
            raise ValueError(f"فشل توليد الخطة عبر الذكاء الاصطناعي: {e}")

# =====================================================================
# 5. NOTIFICATION ENGINE (WhatsApp & Telegram)
# =====================================================================
class NotificationEngine:
    @staticmethod
    def send_telegram(bot_token: str, chat_id: str, message: str) -> bool:
        if not bot_token or not chat_id:
            return False
        try:
            res = requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage",
                                json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}, timeout=5)
            return res.status_code == 200
        except Exception:
            return False

    @staticmethod
    def get_whatsapp_link(phone_number: str, message: str) -> str:
        encoded_msg = urllib.parse.quote(message)
        clean_phone = re.sub(r'[^\d]', '', phone_number)
        return f"https://wa.me/{clean_phone}?text={encoded_msg}"

# =====================================================================
# 6. ADVANCED ANALYTICS ENGINE
# =====================================================================
class AnalyticsEngine:
    @staticmethod
    def compute_metrics(plan: dict) -> dict:
        tasks = plan.get("tasks", [])
        total_days = sum(int(t.get('days', 0)) for t in tasks)
        total_tasks = len(tasks)
        high = sum(1 for t in tasks if str(t.get('priority', '')).lower() == 'high')
        med = sum(1 for t in tasks if str(t.get('priority', '')).lower() == 'medium')
        low = sum(1 for t in tasks if str(t.get('priority', '')).lower() == 'low')
        base_cost = total_days * 150
        overhead = base_cost * 0.20
        total_cost = base_cost + overhead
        high_ratio = high / total_tasks if total_tasks else 0
        long_tasks = sum(1 for t in tasks if int(t.get('days', 0)) > 5)
        long_ratio = long_tasks / total_tasks if total_tasks else 0
        risk_score = min(100, int((high_ratio * 0.6 + long_ratio * 0.4) * 100))
        confidence_score = plan.get('confidence_score', 85)
        return {
            'total_days': total_days, 'total_tasks': total_tasks, 'high': high, 'med': med, 'low': low,
            'base_cost': base_cost, 'overhead': overhead, 'total_cost': total_cost,
            'risk_score': risk_score, 'confidence_score': confidence_score,
            'avg_days': total_days / total_tasks if total_tasks else 0
        }

    @staticmethod
    def render_analytics(plan: dict):
        m = AnalyticsEngine.compute_metrics(plan)
        tasks = plan.get("tasks", [])
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📅 إجمالي الأيام", f"{m['total_days']} يوم")
        c2.metric("💰 التكلفة المقدرة", f"${m['total_cost']:,.0f}", delta=f"${m['base_cost']:,.0f} أساسي")
        c3.metric("⚠️ درجة المخاطرة", f"{m['risk_score']}%", delta="عالية" if m['risk_score'] > 50 else "منخفضة")
        c4.metric("🎯 نسبة الثقة", f"{m['confidence_score']}%")
        st.divider()
        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            fig1 = go.Figure(data=[go.Pie(
                labels=['عالية (High)', 'متوسطة (Medium)', 'منخفضة (Low)'],
                values=[m['high'], m['med'], m['low']],
                marker=dict(colors=['#ef4444', '#f59e0b', '#10b981']), hole=0.35
            )])
            fig1.update_layout(title="توزيع المهام حسب الأولوية")
            st.plotly_chart(fig1, use_container_width=True)
        with col_chart2:
            if tasks:
                df_tasks = pd.DataFrame(tasks)
                fig2 = px.bar(
                    df_tasks, x='title', y='days', color='priority',
                    title="المدة الزمنية لكل مهمة",
                    color_discrete_map={'High': '#ef4444', 'Medium': '#f59e0b', 'Low': '#10b981'}
                )
                st.plotly_chart(fig2, use_container_width=True)

# =====================================================================
# 7. EXPORT ENGINE
# =====================================================================
class ExportEngine:
    @staticmethod
    def generate_pdf(plan: dict) -> bytes:
        if not REPORTLAB_AVAILABLE: return b""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []
        elements.append(Paragraph(f"<b>Enterprise Architecture Document</b>", styles['Title']))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"<b>Client:</b> {plan.get('client')}", styles['Normal']))
        elements.append(Paragraph(f"<b>Signature:</b> {plan.get('signature')}", styles['Normal']))
        elements.append(Spacer(1, 12))
        table_data = [["Task", "Days", "Cost ($)", "Priority"]]
        for t in plan.get("tasks", []):
            table_data.append([t.get('title', ''), str(t.get('days', '')), f"${t.get('cost', 0)}", t.get('priority', '')])
        t = Table(table_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e3a8a")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1"))
        ]))
        elements.append(t)
        doc.build(elements)
        return buffer.getvalue()

    @staticmethod
    def generate_excel(plan: dict) -> bytes:
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            pd.DataFrame([{
                'العميل': plan.get('client'), 'الملخص': plan.get('executive_summary'),
                'الميزانية': plan.get('budget_str'), 'التوقيع الرقمي': plan.get('signature')
            }]).to_excel(writer, sheet_name='الملخص', index=False)
            if plan.get('tasks'):
                pd.DataFrame(plan['tasks']).to_excel(writer, sheet_name='المهام', index=False)
        return buffer.getvalue()

    @staticmethod
    def generate_txt(plan: dict) -> bytes:
        txt = f"=== خطة مشروع: {plan.get('client')} ===\n"
        txt += f"التاريخ: {plan.get('timestamp')}\n"
        txt += f"التوقيع الرقمي: {plan.get('signature')}\n\n"
        txt += f"الملخص التنفيذي:\n{plan.get('executive_summary')}\n\n"
        txt += "المهام التنفيذية:\n"
        for i, t in enumerate(plan.get("tasks", []), 1):
            txt += f"{i}. {t.get('title')} ({t.get('priority')}) - {t.get('days')} أيام\n"
            txt += f"   الوصف: {t.get('description')}\n"
        return txt.encode('utf-8')

# =====================================================================
# 8. HITL (HUMAN-IN-THE-LOOP) TASK EDITOR
# =====================================================================
def render_hitl_editor(plan: dict):
    st.markdown("### ✏️ مراجعة وتعديل المهام التفاعلي (HITL)")
    tasks = plan.get("tasks", [])
    updated_tasks = []
    p_options = ["High", "Medium", "Low"]

    for idx, task in enumerate(tasks):
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            with c1:
                title = st.text_input(f"المهمة #{idx+1}", value=task.get('title', ''), key=f"hitl_t_{idx}")
            with c2:
                days = st.number_input(f"الأيام", min_value=1, value=int(task.get('days', 2)), key=f"hitl_d_{idx}")
            with c3:
                cost = st.number_input(f"التكلفة ($)", min_value=0, value=int(task.get('cost', 100)), key=f"hitl_c_{idx}")
            with c4:
                curr_prio = str(task.get('priority', 'Medium')).capitalize()
                idx_prio = p_options.index(curr_prio) if curr_prio in p_options else 1
                prio = st.selectbox(f"الأولوية", p_options, index=idx_prio, key=f"hitl_p_{idx}")
            desc = st.text_area(f"الوصف #{idx+1}", value=task.get('description', ''), key=f"hitl_desc_{idx}", height=60)
            updated_tasks.append({
                "title": title, "description": desc, "days": days, "cost": cost, "priority": prio
            })

    if st.button("✅ اعتماد التعديلات وتحديث التوقيع الرقمي", type="primary", use_container_width=True):
        plan["tasks"] = updated_tasks
        plan["signature"] = VaultSecurity.sign_payload(plan)
        st.session_state.selected_plan = plan
        st.success("✅ تم تحديث الخطة، التوقيع المشفر، والتحليلات بنجاح!")
        st.rerun()

# =====================================================================
# 9. AUTHENTICATION PAGE
# =====================================================================
def render_auth_page(t):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"<h1 style='text-align:center;'>{t['title']}</h1>", unsafe_allow_html=True)
        tab_login, tab_signup = st.tabs([t["login_tab"], t["signup_tab"]])
        with tab_login:
            identifier = st.text_input(t["email"], key="login_id")
            password = st.text_input(t["password"], type="password", key="login_pass")
            if st.button(t["login_btn"], use_container_width=True, type="primary"):
                user = DatabaseEngine.get_user(identifier)
                if user and VaultSecurity.verify_password(password, user["password"]):
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("❌ بيانات الدخول غير صحيحة.")
        with tab_signup:
            username = st.text_input("اسم المستخدم", key="signup_user")
            email = st.text_input("البريد الإلكتروني", key="signup_email")
            p1 = st.text_input(t["password"], type="password", key="signup_p1")
            p2 = st.text_input(t["confirm_password"], type="password", key="signup_p2")
            if st.button(t["signup_btn"], use_container_width=True):
                if p1 != p2: st.error("⚠️ كلمتا المرور غير متطابقتين.")
                elif not username or not email or not p1: st.error("⚠️ يرجى إكمال جميع الحقول.")
                else:
                    hashed = VaultSecurity.hash_password(p1)
                    if DatabaseEngine.register_user(username, email, hashed):
                        st.success("✅ تم إنشاء الحساب! سجل الدخول الآن.")
                    else:
                        st.error("❌ اسم المستخدم أو البريد الإلكتروني مستخدم بالفعل.")

# =====================================================================
# 10. MAIN ENTRY & UI
# =====================================================================
def init_session():
    if "authenticated" not in st.session_state: st.session_state.authenticated = False
    if "user" not in st.session_state: st.session_state.user = None
    if "selected_plan" not in st.session_state: st.session_state.selected_plan = None
    if "lang" not in st.session_state: st.session_state.lang = "ar"

def inject_css():
    direction = "rtl" if st.session_state.lang == "ar" else "ltr"
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
        html, body, .stApp {{ font-family: 'Cairo', sans-serif !important; direction: {direction}; background-color: #0b0f19 !important; color: #f8fafc !important; }}
        [data-testid="stSidebar"] {{ background-color: #0f172a !important; }}
        .stButton button {{ border-radius: 8px !important; font-weight: 700 !important; width: 100%; }}
        p, span, div, a, h1, h2, h3, h4, h5, h6 {{ word-wrap: break-word !important; overflow-wrap: break-word !important; }}
    </style>
    """, unsafe_allow_html=True)

def main():
    st.set_page_config(page_title="وكيل مهنة PRO - Phoenix", page_icon="🧠", layout="wide")
    init_session()
    DatabaseEngine.init_db()

    t = TRANSLATIONS[st.session_state.lang]
    inject_css()

    if not st.session_state.authenticated:
        render_auth_page(t)
        return

    user = st.session_state.user
    with st.sidebar:
        st.markdown(f"### 👤 {user.get('username')}")
        st.caption(f"📧 {user.get('email')}")
        st.info(f"⚡ {t['credits']}: {user.get('credits', 0)}")
        if st.button(t["logout"], use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.rerun()
        st.divider()
        if st.button("🌐 العربية" if st.session_state.lang == "ar" else "🌐 English", use_container_width=True):
            st.session_state.lang = "en" if st.session_state.lang == "ar" else "ar"
            st.rerun()
        st.divider()
        st.markdown("### ⚙️ إعدادات الذكاء")
        api_key = st.text_input(t["gemini_key"], type="password", value=os.getenv("GEMINI_API_KEY", ""))
        st.divider()
        st.markdown("### 📲 إشعارات")
        tg_bot = st.text_input("Telegram Token", type="password", value=os.getenv("TELEGRAM_BOT_TOKEN", ""))
        tg_chat = st.text_input("Telegram Chat ID", value=os.getenv("TELEGRAM_CHAT_ID", ""))
        wa_num = st.text_input("رقم WhatsApp (دولة)", value="+967700000000")
        st.divider()
        act_code = st.text_input(t["activate_code"], type="password")
        if st.button(t["activate_btn"], use_container_width=True):
            if act_code in ["PRO2026", "PHOENIX", "MIHNA"]:
                DatabaseEngine.update_credits(user.get("email"), 9999, "VIP Unlimited")
                user["credits"] = 9999
                st.success("✨ تم تفعيل الحساب غير المحدود!")
                st.rerun()

    st.title(f"🧠 {t['title']}")
    tab_gen, tab_an, tab_dash, tab_exp = st.tabs([t["tab_gen"], t["tab_analytics"], t["tab_dashboard"], t["tab_export"]])

    with tab_gen:
        c1, c2 = st.columns(2)
        with c1:
            client = st.text_input(t["client"], value="مؤسسة أفق التعليمية")
            budget = st.text_input(t["budget"], value="8000 - 12000 $")
        with c2:
            timeline = st.text_input(t["timeline"], value="8 أسابيع")
            tech = st.text_input(t["tech"], value="Flutter, Node.js, Supabase")
        desc = st.text_area(t["scope"], height=120)
        if st.button(t["generate_btn"], type="primary", use_container_width=True):
            if not api_key: st.error("❌ يرجى توفير مفتاح Gemini API")
            elif user.get("credits", 0) <= 0: st.error("🚫 رصيدك انتهى! اشترك أو استخدم كود التفعيل.")
            else:
                with st.spinner("🔄 جارٍ توليد الخطة..."):
                    try:
                        req = {"client": client, "desc": desc, "budget": budget, "timeline": timeline, "tech": tech}
                        plan = PhoenixAI.generate_architecture(api_key, req, lang=st.session_state.lang)
                        if DatabaseEngine.save_project(user.get("email"), plan):
                            user["credits"] -= 1
                            DatabaseEngine.update_credits(user.get("email"), user["credits"])
                            st.session_state.selected_plan = plan
                            msg = f"🚀 مشروع جديد: {client}\n💰 {budget}\n🔑 {plan.get('signature')}"
                            NotificationEngine.send_telegram(tg_bot, tg_chat, msg)
                            st.success("✅ تم التوليد والحفظ! قم بمراجعة الخطة.")
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ خطأ: {e}")

        if st.session_state.selected_plan:
            plan = st.session_state.selected_plan
            st.markdown(f"**🏢 العميل:** {plan.get('client')}")
            st.code(plan.get('signature'), language="text")
            st.markdown(f"**📌 الملخص:** {plan.get('executive_summary')}")
            
            wa_msg = f"🚀 مشروع: {plan['client']}\n💰 {plan['budget_str']}\n🔑 توقيع: {plan['signature']}"
            wa_url = NotificationEngine.get_whatsapp_link(wa_num, wa_msg)
            st.markdown(f'<a href="{wa_url}" target="_blank"><button style="background:#25D366;color:white;padding:8px;border-radius:8px;border:none;width:100%;font-weight:bold;">📲 إرسال عبر WhatsApp</button></a>', unsafe_allow_html=True)
            
            render_hitl_editor(plan)

    with tab_an:
        if st.session_state.selected_plan:
            AnalyticsEngine.render_analytics(st.session_state.selected_plan)
        else:
            st.info("💡 قم بتوليد خطة أولاً لعرض التحليلات.")

    with tab_dash:
        projects = DatabaseEngine.get_projects(user.get("email"))
        if projects:
            st.dataframe(pd.DataFrame(projects), use_container_width=True, hide_index=True)
        else:
            st.info("لا توجد مشاريع سابقة.")

    with tab_exp:
        if st.session_state.selected_plan:
            plan = st.session_state.selected_plan
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.download_button(t["export_json"], json.dumps(plan, indent=2, ensure_ascii=False), "project.json", "application/json", use_container_width=True)
            with c2:
                st.download_button(t["export_excel"], ExportEngine.generate_excel(plan), "project.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            with c3:
                st.download_button(t["export_pdf"], ExportEngine.generate_pdf(plan), "project.pdf", "application/pdf", use_container_width=True)
            with c4:
                st.download_button(t["export_txt"], ExportEngine.generate_txt(plan), "project.txt", "text/plain", use_container_width=True)
        else:
            st.info("💡 أنشئ خطة أولاً لتفعيل التصدير.")

if __name__ == "__main__":
    main()
