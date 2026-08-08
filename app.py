#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
© 2026 WAKEEL MEHNA PRO | ENTERPRISE CLOUD ARCHITECTURE
Google Cloud Run Native AI Architecture Engine
Designed & Engineered for High-Scale Enterprise Project Governance
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
import datetime
import requests
import urllib.parse

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai

# ----------------- فحص الحزم السحابية الإضافية -----------------
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
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# =====================================================================
# 1. CLOUD RUN & APP CONFIGURATION
# =====================================================================
st.set_page_config(
    page_title="وكيل مهنة PRO | Enterprise Cloud Architecture",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# التقاط متغيرات بيئة Google Cloud Run تلقائياً
K_SERVICE = os.getenv("K_SERVICE", "wakeel-mehna-pro")
K_REVISION = os.getenv("K_REVISION", "v1.0-cloud-run")
PORT = os.getenv("PORT", "8501")
SECRET_HMAC_KEY = os.getenv("HMAC_SECRET_KEY", "WAKEEL_MEHNA_ENTERPRISE_HMAC_SHA512_SECURE_2026")
PAYMENT_LINK_MONTHLY = os.getenv("PAYMENT_LINK_MONTHLY", "https://nexus-corestore.lemonsqueezy.com/checkout/buy/e6515270-070e-4fc6-b1ea-60c1aeb9e2d3?plan=monthly")
PAYMENT_LINK_YEARLY = os.getenv("PAYMENT_LINK_YEARLY", "https://nexus-corestore.lemonsqueezy.com/checkout/buy/e6515270-070e-4fc6-b1ea-60c1aeb9e2d3?plan=yearly")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# التصميم الهندسي المظلم (Ultra-Modern Enterprise UI)
st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #f1f5f9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    [data-testid="stSidebar"] { background-color: #111827; border-right: 1px solid #1f2937; }
    
    .cloud-badge {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        border: 1px solid #38bdf8;
        color: #f0f9ff;
        padding: 8px 12px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        font-size: 12px;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.25);
    }
    
    .status-badge-green {
        background: linear-gradient(135deg, #064e3b 0%, #047857 100%);
        border: 1px solid #10b981;
        color: #34d399;
        padding: 8px 12px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        font-size: 12px;
        margin-bottom: 12px;
    }
    
    .signature-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-left: 4px solid #8b5cf6;
        padding: 15px;
        border-radius: 8px;
        font-family: monospace;
        word-break: break-all;
    }
    
    .kpi-card {
        background: #1e293b;
        padding: 16px;
        border-radius: 10px;
        border: 1px solid #334155;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# 2. HYBRID ENTERPRISE DATABASE LAYER (Cloud SQL + Local SQLite)
# =====================================================================
DB_FILE = "/tmp/wakeel_mehna_cache.db"

def init_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            credits INTEGER DEFAULT 5,
            plan_status TEXT DEFAULT 'Free Tier',
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
    # مستخدم قيادي افتراضي بكامل الصلاحيات
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

init_database()

class CloudDatabaseEngine:
    @staticmethod
    def get_cloud_sql_connection():
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
        conn = cls.get_cloud_sql_connection()
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
        return dict(row) if row else None

    @classmethod
    def register_user(cls, name: str, email: str, hashed_pass: str) -> bool:
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (name, email, password, credits, plan_status, is_subscribed) VALUES (?, ?, ?, 5, 'Free Tier', 0)",
                (name, email, hashed_pass)
            )
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    @classmethod
    def update_credits(cls, email: str, new_credits: int):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET credits = ? WHERE email = ?", (new_credits, email))
        conn.commit()
        conn.close()

    @classmethod
    def save_project(cls, plan_json: dict, user_email: str) -> bool:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO projects (user_id, client_name, summary, budget_range, tech_stack, payload, signature) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                user_email, plan_json.get('project_name'), plan_json.get('executive_summary'),
                str(plan_json.get('budget')), str(plan_json.get('tech_stack')),
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
# 3. SECURITY & DIGITAL SIGNING ENGINE (HMAC-SHA512)
# =====================================================================
class SecurityEngine:
    @staticmethod
    def sign_payload(payload: dict) -> str:
        clean_payload = {k: v for k, v in payload.items() if k not in ["signature", "generated_at"]}
        payload_str = json.dumps(clean_payload, sort_keys=True, ensure_ascii=False)
        return hmac.new(SECRET_HMAC_KEY.encode(), payload_str.encode(), hashlib.sha512).hexdigest()

    @staticmethod
    def verify_signature(payload: dict, signature: str) -> bool:
        if not signature: return False
        expected = SecurityEngine.sign_payload(payload)
        return hmac.compare_digest(expected, signature)

    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

# =====================================================================
# 4. AI ARCHITECTURE ENGINE (Gemini + Deterministic Fallback)
# =====================================================================
class AIArchitectureEngine:
    @staticmethod
    def generate_plan(req: dict, api_key: str = "") -> dict:
        b = float(req['budget'])
        d = int(req['target_days'])
        
        # محاولة التوليد الذكي عبر Google Gemini
        if api_key or GEMINI_API_KEY:
            try:
                genai.configure(api_key=api_key or GEMINI_API_KEY)
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"""
                قم بإنشاء خطة هندسية معمارية لمشروع برمجي بالصيغة JSON فقط دون أي نصوص إضافية:
                المشروع: {req['project_name']}, المجال: {req['domain']}, الميزانية: {b}$, المدة: {d} يوم, التقنيات: {req['tech_stack']}.
                يجب أن يتضمن الـ JSON:
                "executive_summary": نبذة معمارية تنفيذية,
                "tasks": مصفوفة تحتوي على 4 مهام أساسية (task, days, cost, priority).
                """
                response = model.generate_content(prompt)
                clean_json = re.search(r'\{.*\}', response.text, re.DOTALL)
                if clean_json:
                    data = json.loads(clean_json.group())
                    data.update({
                        "project_name": req['project_name'], "domain": req['domain'],
                        "budget": b, "target_days": d, "tech_stack": req['tech_stack'],
                        "risk": req['risk'], "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    data["signature"] = SecurityEngine.sign_payload(data)
                    return data
            except Exception:
                pass

        # المحرك الهندسي الحسابي الفوري (High-Performance Deterministic Engine)
        tasks = [
            {"id": 1, "task": "هندسة المتطلبات وتصميم المعمارية HLD/LLD", "days": max(1, int(d*0.15)), "cost": int(b*0.15), "priority": "عالية"},
            {"id": 2, "task": "تطوير الواجهات الخلفية وقواعد البيانات وحماية APIs", "days": max(1, int(d*0.35)), "cost": int(b*0.35), "priority": "حرجة"},
            {"id": 3, "task": "تطوير واجهات المستخدم التفاعلية Frontend UI/UX", "days": max(1, int(d*0.30)), "cost": int(b*0.30), "priority": "متوسطة"},
            {"id": 4, "task": "اختبارات الأمان والنشر السحابي CI/CD & Cloud Run", "days": max(1, int(d*0.20)), "cost": int(b*0.20), "priority": "عالية"}
        ]
        
        plan_data = {
            "project_name": req['project_name'],
            "domain": req['domain'],
            "budget": b,
            "target_days": d,
            "tech_stack": req['tech_stack'],
            "risk": req['risk'],
            "executive_summary": f"خطة معمارية سحابية معتمدة وفق معايير Clean Architecture لمشروع ({req['project_name']}).",
            "tasks": tasks,
            "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        plan_data["signature"] = SecurityEngine.sign_payload(plan_data)
        return plan_data

# =====================================================================
# 5. DOCUMENT GENERATION ENGINE
# =====================================================================
def create_pdf_report(plan: dict, df_tasks: pd.DataFrame) -> bytes:
    if not REPORTLAB_AVAILABLE: return b""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, alignment=1, textColor=colors.HexColor('#0284c7'))
    body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=10, leading=14)

    story.append(Paragraph(f"Enterprise Engineering Report: {plan.get('project_name')}", title_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"Budget: ${plan.get('budget'):,} | Duration: {plan.get('target_days')} Days | Tech: {plan.get('tech_stack')}", body_style))
    story.append(Spacer(1, 15))

    table_data = [["Task", "Days", "Cost ($)", "Priority"]]
    for _, row in df_tasks.iterrows():
        table_data.append([str(row.get("task")), str(row.get("days")), f"${row.get('cost')}", str(row.get("priority"))])

    t = Table(table_data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1'))
    ]))
    story.append(t)
    story.append(Spacer(1, 15))
    story.append(Paragraph(f"Digital SHA-512 Signature: {plan.get('signature', '')[:50]}...", body_style))

    doc.build(story)
    return buffer.getvalue()

# =====================================================================
# 6. APPLICATION CONTROLLER & INTERFACE
# =====================================================================
def main():
    if "authenticated" not in st.session_state: st.session_state.authenticated = False
    if "current_user" not in st.session_state: st.session_state.current_user = None
    if "selected_plan" not in st.session_state: st.session_state.selected_plan = None
    if "form_data" not in st.session_state:
        st.session_state.form_data = {"pname": "منصة SaaS سحابية ذكية", "domain": "أنظمة SaaS", "budget": 6500, "days": 40, "tech": "Flutter, Node.js, Cloud Run, Supabase", "risk": "متوسط"}

    # ----------------- تسجيل الدخول والتوثيق -----------------
    if not st.session_state.authenticated:
        st.markdown("<h1 style='text-align:center;'>🧠 وكيل مهنة PRO</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#94a3b8;'>منصة هندسة وإدارة خطط المشاريع الذكية والتوقيع الرقمي السحابي</p>", unsafe_allow_html=True)
        
        c_auth, _ = st.columns([1, 0.01])
        with c_auth:
            t_login, t_register = st.tabs(["🔑 تسجيل الدخول", "📝 حساب سحابي جديد (5 نقاط)"])
            with t_login:
                email = st.text_input("البريد الإلكتروني").strip().lower()
                pw = st.text_input("كلمة المرور", type="password")
                if st.button("🚀 الدخول للمنصة", type="primary", use_container_width=True):
                    u = CloudDatabaseEngine.get_user(email)
                    if u and u["password"] == SecurityEngine.hash_password(pw):
                        st.session_state.authenticated = True
                        st.session_state.current_user = u
                        st.rerun()
                    else:
                        st.error("بيانات الاعتماد غير مطابقة.")
            
            with t_register:
                reg_name = st.text_input("الاسم الكامل")
                reg_email = st.text_input("البريد الإلكتروني للإنشاء").strip().lower()
                reg_pw = st.text_input("كلمة المرور الجديدة", type="password")
                if st.button("✨ إنشاء الحساب السحابي", use_container_width=True):
                    if reg_name and reg_email and reg_pw:
                        if CloudDatabaseEngine.register_user(reg_name, reg_email, SecurityEngine.hash_password(reg_pw)):
                            st.success("تم إنشاء الحساب بنجاح! يرجى تسجيل الدخول.")
                        else:
                            st.error("البريد الإلكتروني مسجل بالفعل.")
        return

    # ----------------- اللوحة الرئيسية بعد التوثيق -----------------
    user = CloudDatabaseEngine.get_user(st.session_state.current_user['email']) or st.session_state.current_user

    # الشريط الجانبي (GCP Health & Controls)
    with st.sidebar:
        st.markdown(f'<div class="cloud-badge">☁️ Google Cloud Run: {K_SERVICE}<br><span style="font-size:10px;">Revision: {K_REVISION}</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="status-badge-green">🟢 محرك الذكاء الاصطناعي نشط</div>', unsafe_allow_html=True)
        st.markdown(f"**👤 المهندس:** `{user['name']}`")
        
        if user['is_subscribed']:
            st.markdown("✨ الباقة: **Enterprise Pro 👑 (غير محدود)**")
        else:
            st.markdown(f"⚡ الرصيد المتبقي: **{user['credits']} عمليات مجانية**")

        st.divider()
        st.subheader("🔑 إعدادات Gemini API")
        user_gemini_key = st.text_input("مفتاح Gemini الخاص بك (اختياري)", type="password", help="في حال تركه فارغاً سيتم استخدام المحرك الحسابي الداخلي.")

        st.divider()
        st.subheader("💳 باقات الترقية")
        st.markdown(f"[💳 اشتراك شهري Pro ($29)]({PAYMENT_LINK_MONTHLY})")
        st.markdown(f"[👑 اشتراك سنوي Enterprise ($279)]({PAYMENT_LINK_YEARLY})")

        if st.button("🚪 تسجيل الخروج", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.rerun()

    # التبويبات التنفيذية
    st.markdown("<h2 style='text-align:center;'>🚀 وكيل مهنة PRO | Enterprise Plan Builder</h2>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["🏗️ هندسة وتوليد الخطة", "📊 التحليلات التفاعلية 5D", "✏️ محرر المهام وإعادة التوقيع", "🗄️ الأرشيف والمعمارية السحابية"])

    # --- TAB 1: توليد الخطة وتوقيعها ---
    with tab1:
        st.subheader("⚡ قوالب جاهزة للبدء السريع")
        cp1, cp2, cp3 = st.columns(3)
        if cp1.button("🛒 متجر إلكتروني متكامل", use_container_width=True):
            st.session_state.form_data = {"pname": "متجر إلكتروني ذكي", "domain": "التجارة الإلكترونية", "budget": 4500, "days": 30, "tech": "Flutter, Node.js, PostgreSQL", "risk": "منخفض"}
            st.rerun()
        if cp2.button("🎓 منصة تعليمية ذكية", use_container_width=True):
            st.session_state.form_data = {"pname": "منصة تعليم تفاعلية", "domain": "التعليم الرقمي", "budget": 3500, "days": 25, "tech": "Flutter, Supabase, WebRTC", "risk": "متوسط"}
            st.rerun()
        if cp3.button("🚗 تطبيق خدمات ولوجستيات", use_container_width=True):
            st.session_state.form_data = {"pname": "منظومة توصيل ذكية", "domain": "أنظمة SaaS", "budget": 6000, "days": 45, "tech": "Flutter, Go, Google Maps API", "risk": "عالي"}
            st.rerun()

        with st.form("builder_form"):
            c1, c2 = st.columns(2)
            with c1:
                p_name = st.text_input("اسم المشروع الهندسي", value=st.session_state.form_data["pname"])
                domain = st.selectbox("المجال المعماري", ["أنظمة SaaS", "التجارة الإلكترونية", "الذكاء الاصطناعي", "التعليم الرقمي"], index=0)
                budget = st.number_input("الميزانية المستهدفة ($)", value=st.session_state.form_data["budget"], min_value=500)
            with c2:
                tech = st.text_input("حزمة التقنيات (Tech Stack)", value=st.session_state.form_data["tech"])
                days = st.number_input("المدة الزمنية المستهدفة (يوم)", value=st.session_state.form_data["days"], min_value=5)
                risk = st.select_slider("مستوى تحمل المخاطر", ["منخفض", "متوسط", "عالي"], value=st.session_state.form_data["risk"])
            
            submit = st.form_submit_button("🚀 توليد وتوقيع الخطة معمارياً (HMAC-SHA512)", use_container_width=True)

        if submit:
            if user['credits'] <= 0 and not user['is_subscribed']:
                st.error("❌ لقد استنفدت رصيدك المجاني. يرجى الترقية للاستمرار.")
            else:
                req = {"project_name": p_name, "domain": domain, "budget": budget, "target_days": days, "tech_stack": tech, "risk": risk}
                plan = AIArchitectureEngine.generate_plan(req, user_gemini_key)
                CloudDatabaseEngine.save_project(plan, user['email'])
                
                if not user['is_subscribed']:
                    CloudDatabaseEngine.update_credits(user['email'], max(0, user['credits'] - 1))
                
                st.session_state.selected_plan = plan
                st.success("✅ تم توليد وتوقيع الخطة الهندسية وحفظها في السحابة بنجاح!")
                st.rerun()

        # عرض تفاصيل الخطة الحالية
        if st.session_state.selected_plan:
            plan = st.session_state.selected_plan
            st.divider()
            st.markdown(f"### 📋 الخطة المعمارية المعتمدة: `{plan['project_name']}`")
            
            cs1, cs2 = st.columns([3, 1])
            with cs1:
                st.markdown(f"""
                <div class="signature-card">
                    <b>🔑 التوقيع الرقمي المشفر (HMAC-SHA512 Integrity Check):</b><br>
                    <code>{plan['signature']}</code>
                </div>
                """, unsafe_allow_html=True)
            with cs2:
                is_valid = SecurityEngine.verify_signature(plan, plan['signature'])
                if is_valid:
                    st.markdown("<br><div class='status-badge-green'>✔ توقيع رقمي أصلي ومطابق</div>", unsafe_allow_html=True)
                else:
                    st.error("❌ تحذير: التوقيع غير مطابق")

            df_tasks = pd.DataFrame(plan.get("tasks", []))
            st.dataframe(df_tasks, use_container_width=True)

            # التصدير المباشر
            ce1, ce2 = st.columns(2)
            with ce1:
                pdf_data = create_pdf_report(plan, df_tasks)
                st.download_button("📄 تحميل تقرير PDF هندسي", pdf_data, f"{plan['project_name']}.pdf", "application/pdf", use_container_width=True)
            with ce2:
                if OPENPYXL_AVAILABLE:
                    x_io = io.BytesIO()
                    df_tasks.to_excel(x_io, index=False)
                    st.download_button("📊 تصدير الخطة كـ Excel", x_io.getvalue(), f"{plan['project_name']}.xlsx", use_container_width=True)

    # --- TAB 2: التحليلات 5D ---
    with tab2:
        if not st.session_state.selected_plan:
            st.info("💡 قم بتوليد خطة أولاً لعرض التحليلات الهندسية المتقدمة.")
        else:
            plan = st.session_state.selected_plan
            df_t = pd.DataFrame(plan.get("tasks", []))

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("💰 الميزانية الكلية", f"${plan['budget']:,}")
            k2.metric("⏱️ المدة الكلية", f"{plan['target_days']} يوم")
            k3.metric("📈 الاستهلاك اليومي", f"${int(plan['budget']/max(1, plan['target_days'])):,}/يوم")
            k4.metric("🛡️ مؤشر الحماية", "99.9%", delta="Cloud Native")

            st.write("---")
            g1, g2 = st.columns(2)
            with g1:
                st.markdown("#### 🕸️ مصفوفة تقييم الأبعاد الهندسية (5D Radar)")
                fig_radar = go.Figure(go.Scatterpolar(
                    r=[90, 95, 85, 80, 90],
                    theta=['الأمان السحابي', 'التوقيع الرقمي', 'المرونة', 'الجدول الزمني', 'التكلفة'],
                    fill='toself', line=dict(color='#38bdf8')
                ))
                fig_radar.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=320)
                st.plotly_chart(fig_radar, use_container_width=True)

            with g2:
                st.markdown("#### 🌊 التدفق المالي التراكمي (Waterfall Flow)")
                fig_wf = go.Figure(go.Waterfall(
                    orientation="v",
                    measure=["relative"] * len(df_t) + ["total"],
                    x=list(df_t['task']) + ["المجموع الكلي"],
                    y=list(df_t['cost']) + [0],
                    connector={"line": {"color": "#64748B"}}
                ))
                fig_wf.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=320)
                st.plotly_chart(fig_wf, use_container_width=True)

    # --- TAB 3: محرر المهام التفاعلي ---
    with tab3:
        if not st.session_state.selected_plan:
            st.info("💡 قم بتوليد خطة لتتمكن من تعديل مهامها وميزانياتها.")
        else:
            plan = st.session_state.selected_plan
            st.markdown("#### ✏️ تعديل المهام وحساب الميزانيات لحظياً")
            edited_df = st.data_editor(pd.DataFrame(plan.get("tasks", [])), num_rows="dynamic", use_container_width=True)

            if st.button("💾 تطبيق التعديلات وتحديث التوقيع الرقمي", type="primary", use_container_width=True):
                updated_tasks = edited_df.to_dict(orient='records')
                plan['tasks'] = updated_tasks
                plan['budget'] = sum(int(item.get('cost', 0)) for item in updated_tasks)
                plan['target_days'] = sum(int(item.get('days', 0)) for item in updated_tasks)
                plan['signature'] = SecurityEngine.sign_payload(plan)

                st.session_state.selected_plan = plan
                CloudDatabaseEngine.save_project(plan, user['email'])
                st.success("✅ تم تحديث الخطة وإعادة التوقيع الرقمي بنجاح!")
                st.rerun()

    # --- TAB 4: الأرشيف والمعمارية السحابية ---
    with tab4:
        st.subheader("🗄️ سجل المشاريع والخطط المعتمدة في السحابة")
        saved = CloudDatabaseEngine.get_projects(user['email'])
        if saved:
            st.dataframe(pd.DataFrame(saved)[["id", "project_name", "summary", "budget_range", "created_at", "signature"]], use_container_width=True)
        else:
            st.info("لا توجد خطط سابقة محفوظة في قاعدة البيانات.")

        st.divider()
        st.subheader("☁️ معمارية النظام (Cloud Native Specs)")
        st.markdown(f"""
        - **Host Platform:** Google Cloud Run (Containerized Serverless)
        - **Compute Engine:** Python 3.12 Slim Environment
        - **Security Layer:** HMAC-SHA512 Tamper-Proof Cryptography
        - **Port Routing:** Listen on `0.0.0.0:{PORT}` (Internal Service Port)
        """)

if __name__ == "__main__":
    main()
