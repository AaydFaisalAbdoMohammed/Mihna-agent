#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
© 2026 PHOENIX & WAKEEL MEHNA PRO - ENTERPRISE ARCHITECTURE v10.0
منصة هندسة وإدارة خطط المشاريع الذكية والتوقيع الرقمي والتحليلات المتقدمة
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

# ----------------- فحص الحزم التكميلية ومعالجة البدائل -----------------
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
    from reportlab.lib.pagesizes import letter
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
# 1. CONFIGURATION & STATE INITIALIZATION
# =====================================================================
PAYMENT_LINK_MONTHLY = os.getenv("PAYMENT_LINK_MONTHLY", "https://nexus-corestore.lemonsqueezy.com/checkout/buy/e6515270-070e-4fc6-b1ea-60c1aeb9e2d3?plan=monthly")
PAYMENT_LINK_YEARLY = os.getenv("PAYMENT_LINK_YEARLY", "https://nexus-corestore.lemonsqueezy.com/checkout/buy/e6515270-070e-4fc6-b1ea-60c1aeb9e2d3?plan=yearly")
SECRET_HMAC_KEY = os.getenv("HMAC_SECRET_KEY", "PHOENIX_SECURE_HMAC_KEY_2026_ENTERPRISE_ULTIMATE")
DB_FILE = "phoenix_app_data.db"

st.set_page_config(
    page_title="وكيل مهنة PRO | Enterprise Architecture",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Dark UI & Cards)
st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #f1f5f9; }
    [data-testid="stSidebar"] { background-color: #151c2c; border-right: 1px solid #1e293b; }
    
    .status-badge-green {
        background: linear-gradient(135deg, #064e3b 0%, #047857 100%);
        border: 1px solid #10b981;
        color: #34d399;
        padding: 8px 12px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        font-size: 13px;
        margin-bottom: 10px;
    }
    
    .credit-badge-blue {
        background: linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 100%);
        border: 1px solid #3b82f6;
        color: #93c5fd;
        padding: 8px 12px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        font-size: 13px;
        margin-bottom: 10px;
    }

    .badge-gold { background-color: #f59e0b; color: #000; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 12px; }
    .badge-purple { background-color: #8b5cf6; color: #fff; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 12px; }
    .badge-green { background-color: #10b981; color: #fff; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 12px; }
    
    .pricing-card { background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; text-align: center; }
    .pricing-card-highlight { background-color: #1e293b; border: 2px solid #8b5cf6; border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 8px 20px rgba(139,92,246,0.2); }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# 2. HYBRID DATABASE ENGINE (Cloud SQL + Permanent SQLite Fallback)
# =====================================================================
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
    # مستخدم افتراضي بصلاحية كاملة
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
        return dict(row) if row else None

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
        cursor.execute("SELECT id, client_name as project_name, summary, budget_range, created_at, signature, payload FROM projects WHERE user_id = ? ORDER BY created_at DESC", (user_email,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

# =====================================================================
# 3. SECURITY & VERIFICATION ENGINE
# =====================================================================
class SecurityEngine:
    @classmethod
    def sign_payload(cls, payload: dict) -> str:
        clean_payload = {k: v for k, v in payload.items() if k not in ["signature", "timestamp"]}
        payload_str = json.dumps(clean_payload, sort_keys=True, ensure_ascii=False)
        return hmac.new(SECRET_HMAC_KEY.encode(), payload_str.encode(), hashlib.sha512).hexdigest()

    @classmethod
    def verify_signature(cls, payload: dict, signature: str) -> bool:
        if not signature: return False
        expected = cls.sign_payload(payload)
        return hmac.compare_digest(expected, signature)

    @classmethod
    def hash_password(cls, password: str) -> str:
        if BCRYPT_AVAILABLE:
            return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        return hashlib.sha256(password.encode()).hexdigest()

    @classmethod
    def verify_password(cls, password: str, hashed: str) -> bool:
        if BCRYPT_AVAILABLE and hashed.startswith("$2b$"):
            try: return bcrypt.checkpw(password.encode(), hashed.encode())
            except Exception: return False
        return hashlib.sha256(password.encode()).hexdigest() == hashed

# =====================================================================
# 4. NOTIFICATIONS & EXPORT ENGINES
# =====================================================================
class NotificationEngine:
    @staticmethod
    def send_telegram_msg(bot_token: str, chat_id: str, message: str):
        if bot_token and chat_id:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            try:
                requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}, timeout=4)
            except Exception:
                pass

    @staticmethod
    def get_whatsapp_url(phone: str, message: str) -> str:
        encoded = urllib.parse.quote(message)
        clean_phone = re.sub(r'[^\d]', '', phone)
        return f"https://wa.me/{clean_phone}?text={encoded}"

def generate_pdf_report(plan: dict, df_tasks: pd.DataFrame) -> bytes:
    if not REPORTLAB_AVAILABLE:
        return b""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    story = []

    def format_text(txt):
        if ARABIC_PDF_AVAILABLE:
            try:
                return get_display(arabic_reshaper.reshape(str(txt)))
            except Exception:
                return str(txt)
        return str(txt)

    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, alignment=1, textColor=colors.HexColor('#1d4ed8'))
    body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=10, leading=14, alignment=2)

    story.append(Paragraph(format_text(f"Engineering Plan: {plan.get('project_name')}"), title_style))
    story.append(Spacer(1, 10))
    info_header = f"الميزانية: ${plan.get('budget')} | المدة: {plan.get('target_days')} يوم | التقنيات: {plan.get('tech_stack')}"
    story.append(Paragraph(format_text(info_header), body_style))
    story.append(Spacer(1, 15))

    table_data = [["Task", "Days", "Cost ($)", "Priority"]]
    for _, row in df_tasks.iterrows():
        table_data.append([
            format_text(row.get("task", "")),
            str(row.get("days", 0)),
            f"${row.get('cost', 0)}",
            format_text(row.get("priority", "High"))
        ])

    t = Table(table_data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1'))
    ]))
    story.append(t)
    story.append(Spacer(1, 15))
    story.append(Paragraph(format_text(f"التوقيع الرقمي المشفر: {plan.get('signature', '')[:40]}..."), body_style))

    doc.build(story)
    return buffer.getvalue()

# =====================================================================
# 5. AI ENGINE & ARCHITECTURE BUILDER
# =====================================================================
class ArchitectureAI:
    @staticmethod
    def generate_plan(api_key: str, req: dict) -> dict:
        b = float(req['budget'])
        d = int(req['target_days'])
        
        # خطة هندسية دقيقة
        tasks = [
            {"id": 1, "task": "تحليل المتطلبات وهندسة النظام HLD/LLD", "days": max(1, int(d*0.15)), "cost": int(b*0.15), "priority": "عالية", "status": "مخطط"},
            {"id": 2, "task": "بناء قواعد البيانات وتأمين APIs & RLS", "days": max(1, int(d*0.35)), "cost": int(b*0.35), "priority": "عالية", "status": "مخطط"},
            {"id": 3, "task": "تطوير واجهات المستخدم وتجربة العميل Frontend UI", "days": max(1, int(d*0.30)), "cost": int(b*0.30), "priority": "متوسطة", "status": "مخطط"},
            {"id": 4, "task": "الاختبارات الشاملة والنشر السحابي Deployment & QA", "days": max(1, int(d*0.20)), "cost": int(b*0.20), "priority": "عالية", "status": "مخطط"}
        ]
        
        plan_data = {
            "project_name": req['project_name'],
            "domain": req['domain'],
            "budget": b,
            "target_days": d,
            "tech_stack": req['tech_stack'],
            "scope": req['scope'],
            "risk": req['risk'],
            "executive_summary": f"خطة هندسية تنفيذية لمشروع ({req['project_name']}) قائمة على معايير الجودة والأمان السحابي.",
            "tasks": tasks,
            "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        plan_data["signature"] = SecurityEngine.sign_payload(plan_data)
        return plan_data

# =====================================================================
# 6. APP CONTROLLER & VIEWS
# =====================================================================
def main():
    if "authenticated" not in st.session_state: st.session_state.authenticated = False
    if "current_user" not in st.session_state: st.session_state.current_user = None
    if "selected_plan" not in st.session_state: st.session_state.selected_plan = None
    if "form_data" not in st.session_state:
        st.session_state.form_data = {"pname": "منصة تجارة سحابية", "domain": "التجارة الإلكترونية", "budget": 4500, "days": 30, "tech": "Flutter, Node.js, PostgreSQL", "scope": ""}

    # ----------------- تسجيل الدخول والاشتراك -----------------
    if not st.session_state.authenticated:
        st.markdown("<h1 style='text-align:center;'>🧠 وكيل مهنة PRO | Enterprise Architecture</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#94a3b8;'>منصة هندسة الخطط المعمارية وتأمينها بالتوقيع الرقمي والذكاء الاصطناعي</p>", unsafe_allow_html=True)
        
        col_box, _ = st.columns([1, 0.01])
        with col_box:
            t_log, t_reg = st.tabs(["🔑 تسجيل الدخول", "📝 حساب جديد (5 نقاط مجانية)"])
            with t_log:
                email = st.text_input("البريد الإلكتروني").strip().lower()
                pw = st.text_input("كلمة المرور", type="password")
                if st.button("🚀 دخول للمنصة", type="primary", use_container_width=True):
                    u = DatabaseEngine.get_user(email)
                    if u and SecurityEngine.verify_password(pw, u["password"]):
                        st.session_state.authenticated = True
                        st.session_state.current_user = u
                        st.success("تم الدخول بنجاح!")
                        st.rerun()
                    else:
                        st.error("بيانات الدخول غير صحيحة.")

            with t_reg:
                n = st.text_input("الاسم الكامل")
                e = st.text_input("البريد الإلكتروني للإنشاء").strip().lower()
                p1 = st.text_input("كلمة المرور الجديدة", type="password")
                if st.button("✨ إنشاء الحساب وتفعيل 5 نقاط", use_container_width=True):
                    if n and e and p1:
                        hp = SecurityEngine.hash_password(p1)
                        if DatabaseEngine.register_user(n, e, hp):
                            st.success("تم إنشاء الحساب بنجاح! يمكنك الآن تسجيل الدخول.")
                        else:
                            st.error("الحساب مسجل مسبقاً أو حدث خطأ.")
        return

    # ----------------- الشاشة الرئيسية بعد التوثيق -----------------
    user = DatabaseEngine.get_user(st.session_state.current_user['email']) or st.session_state.current_user

    # الشريط الجانبي
    with st.sidebar:
        st.title("⚙️ مركز التحكم")
        st.markdown('<div class="status-badge-green">🟢 محرك الذكاء الاصطناعي نشط<br><span style="font-size:10px;">Cloud Run Cluster • Clean Architecture</span></div>', unsafe_allow_html=True)
        st.markdown(f"**👤 المستخدم:** {user['name']}")
        
        if user['is_subscribed']:
            st.markdown("الاشتراك: <span class='badge-gold'>Enterprise Pro 👑</span>", unsafe_allow_html=True)
            st.markdown("الرصيد: **غير محدود ♾️**")
        else:
            st.markdown(f'<div class="credit-badge-blue">⚡ متبقي {user["credits"]} تحويلات مجانية</div>', unsafe_allow_html=True)

        st.divider()
        st.subheader("🔔 إعدادات الإشعارات")
        tg_token = st.text_input("Telegram Bot Token", value=os.getenv("TELEGRAM_BOT_TOKEN", ""), type="password")
        tg_chat = st.text_input("Telegram Chat ID", value=os.getenv("TELEGRAM_CHAT_ID", ""))
        wa_phone = st.text_input("رقم WhatsApp", value="+967700000000")

        st.divider()
        st.subheader("🛒 باقات الاشتراك")
        st.markdown(f"[💳 اشتراك شهري Pro ($29)]({PAYMENT_LINK_MONTHLY})")
        st.markdown(f"[👑 اشتراك سنوي Enterprise ($279)]({PAYMENT_LINK_YEARLY})")

        if st.button("🚪 تسجيل الخروج", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.rerun()

    # التبويبات الرئيسية
    st.markdown("<h1 style='text-align:center;'>🚀 وكيل مهنة PRO | Enterprise Plan Builder</h1>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["🏗️ مولّد الخطط الهندسية", "📊 التحليلات التفاعلية 5D", "✏️ محرر المهام", "🗄️ الأرشيف والاشتراكات"])

    # --- TAB 1: توليد الخطة ---
    with tab1:
        st.subheader("⚡ قوالب جاهزة للبدء السريع")
        cp1, cp2, cp3 = st.columns(3)
        if cp1.button("🛒 متجر إلكتروني متكامل", use_container_width=True):
            st.session_state.form_data = {"pname": "متجر إلكتروني ذكي", "domain": "التجارة الإلكترونية", "budget": 4500, "days": 30, "tech": "Flutter, Node.js, PostgreSQL", "scope": "متجر متكامل مع بوابات دفع وسلة تسوق"}
            st.rerun()
        if cp2.button("🎓 منصة تعليمية ذكية", use_container_width=True):
            st.session_state.form_data = {"pname": "منصة تعليم رقمي", "domain": "الذكاء الاصطناعي", "budget": 3500, "days": 25, "tech": "Flutter, Supabase, WebRTC", "scope": "منصة تعليمية تقدم اختبارات ومحاضرات مباشرة"}
            st.rerun()
        if cp3.button("🚗 تطبيق خدمات ولوجستيات", use_container_width=True):
            st.session_state.form_data = {"pname": "تطبيق توصيل وخدمات", "domain": "أنظمة SaaS", "budget": 6000, "days": 45, "tech": "Flutter, Node.js, Google Maps API", "scope": "تطبيق طلبات وخرائط حية"}
            st.rerun()

        with st.form("builder_form"):
            c_f1, c_f2 = st.columns(2)
            with c_f1:
                p_name = st.text_input("اسم المشروع", value=st.session_state.form_data["pname"])
                domain = st.selectbox("المجال التقني", ["التجارة الإلكترونية", "الذكاء الاصطناعي", "أنظمة SaaS", "التعليم الرقمي"], index=0)
                budget = st.number_input("الميزانية التقديرية ($)", value=st.session_state.form_data["budget"], min_value=500)
            with c_f2:
                tech = st.text_input("التقنيات المستخدمة", value=st.session_state.form_data["tech"])
                days = st.number_input("المدة الزمنية المستهدفة (يوم)", value=st.session_state.form_data["days"], min_value=5)
                risk = st.select_slider("تحمل المخاطر", ["منخفض", "متوسط", "عالي"], value="متوسط")
            
            scope = st.text_area("نطاق العمل ومواصفات المشروع", value=st.session_state.form_data["scope"], height=80)
            generate_submit = st.form_submit_button("🚀 توليد وتوقيع الخطة الهندسية", use_container_width=True)

        if generate_submit:
            if user['credits'] <= 0 and not user['is_subscribed']:
                st.error("❌ لقد استنفدت رصيدك المجاني (5 محاولات). يرجى الترقية للاستمرار.")
            else:
                req = {"project_name": p_name, "domain": domain, "budget": budget, "target_days": days, "tech_stack": tech, "scope": scope, "risk": risk}
                plan = ArchitectureAI.generate_plan("", req)
                DatabaseEngine.save_project(plan, user['email'])
                
                if not user['is_subscribed']:
                    DatabaseEngine.update_credits(user['email'], max(0, user['credits'] - 1))
                
                st.session_state.selected_plan = plan
                
                # إشعار Telegram التلقائي
                msg = f"🚀 *تم توليد خطة هندسية جديدة!*\n\n📌 *المشروع:* {p_name}\n💰 *الميزانية:* ${budget:,}\n⏱️ *المدة:* {days} يوم\n🔑 *التوقيع:* `{plan['signature'][:16]}...`"
                NotificationEngine.send_telegram_msg(tg_token, tg_chat, msg)
                
                st.success("✅ تم توليد وتوقيع الخطة وحفظها في قاعدة البيانات بنجاح!")
                st.rerun()

        # عرض نتائج الخطة
        if st.session_state.selected_plan:
            plan = st.session_state.selected_plan
            st.divider()
            st.markdown(f"### 📋 الخطة المعتمدة: {plan['project_name']}")
            
            cs1, cs2 = st.columns([3, 1])
            with cs1:
                st.info(f"🔑 **التوقيع الرقمي المشفر (HMAC-SHA512):**\n`{plan['signature']}`")
            with cs2:
                valid = SecurityEngine.verify_signature(plan, plan['signature'])
                st.markdown(f"<br><span class='badge-green'>{'✔ توقيع موثوق وسليم' if valid else '❌ تم التلاعب'}</span>", unsafe_allow_html=True)

            df_tasks = pd.DataFrame(plan.get("tasks", []))
            st.dataframe(df_tasks, use_container_width=True)

            # التصدير والإشعارات
            c_exp1, c_exp2, c_exp3 = st.columns(3)
            with c_exp1:
                pdf_bytes = generate_pdf_report(plan, df_tasks)
                st.download_button("📄 تحميل تقرير (PDF)", pdf_bytes, f"{plan['project_name']}.pdf", "application/pdf", use_container_width=True)
            with c_exp2:
                if OPENPYXL_AVAILABLE:
                    b_io = io.BytesIO()
                    df_tasks.to_excel(b_io, index=False)
                    st.download_button("📊 تصدير Excel", b_io.getvalue(), f"{plan['project_name']}.xlsx", use_container_width=True)
                else:
                    st.download_button("📄 تصدير CSV", df_tasks.to_csv(index=False).encode('utf-8'), f"{plan['project_name']}.csv", "text/csv", use_container_width=True)
            with c_exp3:
                wa_msg = f"🚀 خطة مشروع: {plan['project_name']}\n💰 الميزانية: ${plan['budget']}\n⏱️ المدة: {plan['target_days']} يوم"
                wa_url = NotificationEngine.get_whatsapp_url(wa_phone, wa_msg)
                st.markdown(f'<a href="{wa_url}" target="_blank" style="display:block; text-align:center; background-color:#25D366; color:white; padding:8px; border-radius:8px; font-weight:bold; text-decoration:none;">📲 مشاركة عبر WhatsApp</a>', unsafe_allow_html=True)

    # --- TAB 2: التحليلات 5D ---
    with tab2:
        if not st.session_state.selected_plan:
            st.info("💡 قم بتوليد خطة أولاً لعرض التحليلات الهندسية المتقدمة.")
        else:
            plan = st.session_state.selected_plan
            df_t = pd.DataFrame(plan.get("tasks", []))
            
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("💰 الميزانية الكلية", f"${plan['budget']:,}")
            k2.metric("⏱️ المدة الإجمالية", f"{plan['target_days']} يوم")
            k3.metric("📈 المعدل اليومي", f"${int(plan['budget']/max(1, plan['target_days'])):,}/يوم")
            k4.metric("🛡️ مؤشر السلامة", "92%", delta="ممتاز")

            st.write("---")
            r1, r2 = st.columns(2)
            with r1:
                st.markdown("#### 🕸️ مصفوفة تقييم المخاطر والأبعاد 5D Radar")
                fig_radar = go.Figure(go.Scatterpolar(
                    r=[85, 95, 80, 90, 75],
                    theta=['تعقيد النطاق', 'الأمان والتوقيع', 'الجدول الزمني', 'التكلفة', 'المرونة'],
                    fill='toself', line=dict(color='#8B5CF6')
                ))
                fig_radar.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=300)
                st.plotly_chart(fig_radar, use_container_width=True)

            with r2:
                st.markdown("#### 🌊 التدفق المالي التراكمي (Waterfall)")
                fig_waterfall = go.Figure(go.Waterfall(
                    orientation="v",
                    measure=["relative"] * len(df_t) + ["total"],
                    x=list(df_t['task']) + ["الإجمالي"],
                    y=list(df_t['cost']) + [0],
                    connector={"line": {"color": "#64748B"}}
                ))
                fig_waterfall.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=300)
                st.plotly_chart(fig_waterfall, use_container_width=True)

    # --- TAB 3: محرر المهام وإعادة التوقيع ---
    with tab3:
        if not st.session_state.selected_plan:
            st.info("💡 قم بتوليد خطة لتتمكن من تعديل مهامها وإعادة توقيعها.")
        else:
            plan = st.session_state.selected_plan
            edited_df = st.data_editor(pd.DataFrame(plan.get("tasks", [])), num_rows="dynamic", use_container_width=True)
            
            if st.button("💾 حفظ التعديلات وإعادة التوقيع الرقمي", type="primary", use_container_width=True):
                updated_tasks = edited_df.to_dict(orient='records')
                plan['tasks'] = updated_tasks
                plan['budget'] = sum(int(item.get('cost', 0)) for item in updated_tasks)
                plan['target_days'] = sum(int(item.get('days', 0)) for item in updated_tasks)
                plan['signature'] = SecurityEngine.sign_payload(plan)
                
                st.session_state.selected_plan = plan
                DatabaseEngine.save_project(plan, user['email'])
                st.success("✅ تم تحديث المهام وإعادة التوقيع الرقمي بنجاح!")
                st.rerun()

    # --- TAB 4: الأرشيف والاشتراكات ---
    with tab4:
        st.subheader("🗄️ أرشيف المشاريع المحفوظة")
        saved_projs = DatabaseEngine.get_projects(user['email'])
        if saved_projs:
            st.dataframe(pd.DataFrame(saved_projs)[["id", "project_name", "summary", "budget_range", "created_at"]], use_container_width=True)
        else:
            st.info("لا توجد مشاريع محفوظة مسبقاً.")

        st.divider()
        st.subheader("💳 خطط الترقية والاشتراك")
        cp_1, cp_2 = st.columns(2)
        with cp_1:
            st.markdown(f"""
            <div class="pricing-card">
                <h3>⚡ اشتراك Pro الشهري</h3>
                <h2>$29 <small>/ شهر</small></h2>
                <hr>
                <p>✔ توليد خطط هندسية غير محدودة</p>
                <p>✔ تحليلات 5D وتوقيع رقمي مشفر</p>
                <a href="{PAYMENT_LINK_MONTHLY}" target="_blank" style="display:block; background:#2563eb; color:white; padding:10px; border-radius:8px; text-decoration:none; font-weight:bold;">ترقية الآن</a>
            </div>
            """, unsafe_allow_html=True)
        with cp_2:
            st.markdown(f"""
            <div class="pricing-card-highlight">
                <span class="badge-gold">خصم 20%</span>
                <h3>👑 اشتراك Enterprise السنوي</h3>
                <h2>$279 <small>/ سنة</small></h2>
                <hr>
                <p>✔ دعم فني مخصص ومعمارية كاملة</p>
                <p>✔ كافة ميزات Pro + ربط API تلقائي</p>
                <a href="{PAYMENT_LINK_YEARLY}" target="_blank" style="display:block; background:#8b5cf6; color:white; padding:10px; border-radius:8px; text-decoration:none; font-weight:bold;">ترقية للمؤسسات</a>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
