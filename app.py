#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
╔══════════════════════════════════════════════════════════════════╗
║  وكيل مهنة PRO - مدير المشاريع الذكي المعتمد على Gemini     ║
║  Version: 5.0 (Enterprise Grade - Production Ready)           ║
║  Architecture: Modular, Scalable, Secure, AI-Powered         ║
║  Features: Auth, RAG, HITL, Payments, Telegram, Analytics   ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import json
import re
import uuid
import requests
import bcrypt
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from io import BytesIO
import base64
from datetime import datetime
import streamlit as st
import google.generativeai as genai
import config
import cloudsql_utils

# ============================================================
# 1. نظام AI Gateway (إدارة مفاتيح Gemini المرنة)
# ============================================================
def get_active_gemini_key() -> str:
    """الحصول على مفتاح Gemini من متغير البيئة أو إدخال المستخدم."""
    env_key = os.getenv("GEMINI_API_KEY")
    if env_key and len(env_key) > 5:
        return env_key
    user_key = st.session_state.get("user_gemini_key")
    if user_key and len(user_key) > 5:
        return user_key
    return None

def render_enterprise_sidebar():
    """عرض الشريط الجانبي المتطور مع مركز إدارة الذكاء الاصطناعي."""
    with st.sidebar:
        st.markdown("### ⚙️ مركز إدارة الذكاء الاصطناعي")
        active_key = get_active_gemini_key()
        if active_key:
            st.success("🟢 محرك Gemini AI: نشط وجاهز")
            st.caption(f"🔑 المفتاح: {active_key[:8]}...")
        else:
            st.warning("⚡ المحرك يعمل في وضع العرض التفاعلي (Demo Mode)")
            user_key_input = st.text_input(
                "🔑 مفتاح Gemini API الخاص بك (اختياري)",
                type="password",
                help="أدخل المفتاح الخاص بك لتفعيل القدرات الكاملة للنموذج"
            )
            if user_key_input:
                st.session_state["user_gemini_key"] = user_key_input
                st.rerun()
        st.divider()
        st.markdown("#### 📡 حالة خدمات النظام")
        st.caption("• Cloud Run Cluster: **us-central1 (Active)**")
        st.caption("• DB Engine: **MySQL via Unix Socket**")
        st.caption("• Architecture: **Clean Architecture Modular**")
        st.caption("• Security: **bcrypt + JWT Sessions**")

# ============================================================
# 2. نظام المصادقة (تسجيل الدخول / إنشاء حساب)
# ============================================================
def init_auth():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.user_email = None

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_user(username: str, email: str, password: str) -> tuple:
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return False, "⚠️ البريد الإلكتروني غير صالح"
    if len(username) < 3:
        return False, "⚠️ اسم المستخدم يجب أن يكون 3 أحرف على الأقل"
    if len(password) < 6:
        return False, "⚠️ كلمة المرور يجب أن تكون 6 أحرف على الأقل"
    conn = cloudsql_utils.get_db_connection()
    if not conn:
        return False, "⚠️ تعذر الاتصال بقاعدة البيانات"
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
    if cursor.fetchone():
        conn.close()
        return False, "⚠️ اسم المستخدم أو البريد الإلكتروني موجود بالفعل"
    hashed_pw = hash_password(password)
    try:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
            (username, email, hashed_pw)
        )
        conn.commit()
        conn.close()
        return True, "✅ تم إنشاء الحساب بنجاح! يمكنك تسجيل الدخول الآن."
    except Exception as e:
        conn.close()
        return False, f"❌ خطأ في إنشاء الحساب: {e}"

def login_user(identifier: str, password: str) -> tuple:
    if not identifier or not password:
        return False, "⚠️ يرجى ملء جميع الحقول"
    conn = cloudsql_utils.get_db_connection()
    if not conn:
        return False, "⚠️ تعذر الاتصال بقاعدة البيانات"
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, username, email, password_hash FROM users WHERE username = %s OR email = %s",
        (identifier, identifier)
    )
    user = cursor.fetchone()
    conn.close()
    if not user:
        return False, "⚠️ المستخدم غير موجود"
    if not verify_password(password, user['password_hash']):
        return False, "⚠️ كلمة المرور غير صحيحة"
    st.session_state.authenticated = True
    st.session_state.user_id = user['id']
    st.session_state.username = user['username']
    st.session_state.user_email = user['email']
    return True, "✅ تم تسجيل الدخول بنجاح!"

def logout_user():
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.user_email = None

def render_login_page():
    st.set_page_config(page_title="وكيل مهنة - تسجيل الدخول", page_icon="🔐", layout="centered")
    st.markdown("""
    <style>
        .auth-title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #1E3A8A; }
        .auth-title span { color: #F5A623; }
        .auth-subtitle { text-align: center; color: #666; margin-bottom: 2rem; }
        .stButton button { width: 100%; background-color: #1E3A8A; color: white; border-radius: 8px; height: 3rem; transition: 0.3s; }
        .stButton button:hover { background-color: #1D4ED8; transform: scale(1.02); }
        .stTabs [data-baseweb="tab-list"] { gap: 2rem; }
        .stTabs [data-baseweb="tab"] { font-size: 1.1rem; font-weight: 600; }
        .stTabs [aria-selected="true"] { color: #1E3A8A; border-bottom: 3px solid #F5A623; }
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="auth-title">🧠 وكيل مهنة <span>PRO</span></div>', unsafe_allow_html=True)
    st.markdown('<p class="auth-subtitle">خطط مشاريعك بذكاء واحترافية</p>')
    tab1, tab2 = st.tabs(["🔑 تسجيل الدخول", "📝 إنشاء حساب جديد"])
    with tab1:
        with st.form("login_form"):
            identifier = st.text_input("👤 اسم المستخدم أو البريد الإلكتروني", placeholder="أدخل اسم المستخدم أو البريد")
            password = st.text_input("🔒 كلمة المرور", type="password", placeholder="أدخل كلمة المرور")
            if st.form_submit_button("🚀 تسجيل الدخول", use_container_width=True):
                success, msg = login_user(identifier, password)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
    with tab2:
        with st.form("signup_form"):
            new_username = st.text_input("👤 اسم المستخدم", placeholder="اختر اسم مستخدم فريد")
            new_email = st.text_input("✉️ البريد الإلكتروني", placeholder="example@email.com")
            new_password = st.text_input("🔒 كلمة المرور", type="password", placeholder="6 أحرف على الأقل")
            confirm_password = st.text_input("🔒 تأكيد كلمة المرور", type="password", placeholder="أعد كتابة كلمة المرور")
            if st.form_submit_button("📝 إنشاء حساب", use_container_width=True):
                if not new_username or not new_email or not new_password:
                    st.error("⚠️ يرجى ملء جميع الحقول")
                elif new_password != confirm_password:
                    st.error("⚠️ كلمتا المرور غير متطابقتين")
                elif len(new_password) < 6:
                    st.error("⚠️ كلمة المرور يجب أن تكون 6 أحرف على الأقل")
                else:
                    success, msg = create_user(new_username, new_email, new_password)
                    if success:
                        st.success(msg)
                    else:
                        st.error(f"❌ {msg}")

# ============================================================
# 3. نظام الفريميوم (5 استخدامات مجانية)
# ============================================================
def init_usage():
    if 'free_uses' not in st.session_state:
        st.session_state.free_uses = 5
        st.session_state.is_premium = False

def can_use() -> bool:
    init_usage()
    return st.session_state.is_premium or st.session_state.free_uses > 0

def deduct_usage() -> bool:
    init_usage()
    if not st.session_state.is_premium:
        st.session_state.free_uses -= 1
    return True

# ============================================================
# 4. دوال الدفع (Lemon Squeezy)
# ============================================================
def create_checkout_url(user_email: str, user_name: str) -> str:
    if not config.LEMONSQUEEZY_API_KEY:
        raise ValueError("⚠️ مفتاح Lemon Squeezy غير مضبوط في الإعدادات")
    url = "https://api.lemonsqueezy.com/v1/checkouts"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.LEMONSQUEEZY_API_KEY}"
    }
    payload = {
        "data": {
            "type": "checkouts",
            "attributes": {
                "checkout_data": {
                    "email": user_email,
                    "name": user_name,
                    "custom": {"source": "mihna-agent"}
                }
            },
            "relationships": {
                "store": {"data": {"type": "stores", "id": str(config.LEMONSQUEEZY_STORE_ID)}},
                "variant": {"data": {"type": "variants", "id": str(config.MONTHLY_VARIANT_ID)}}
            }
        }
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code in (200, 201):
            return response.json()["data"]["attributes"]["url"]
        error_msg = response.json().get("errors", [{"detail": response.text}])[0].get("detail", response.text)
        raise Exception(f"❌ فشل الدفع: {error_msg}")
    except Exception as e:
        raise Exception(f"❌ خطأ في الدفع: {e}")

# ============================================================
# 5. إشعارات Telegram
# ============================================================
def send_telegram_alert(bot_token: str, chat_id: str, project_plan: dict) -> bool:
    if not bot_token or not chat_id:
        return False
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        message = (
            f"🚀 *مشروع جديد في وكيل مهنة PRO!*\n\n"
            f"👤 *العميل:* {project_plan.get('client_name', 'غير معروف')}\n"
            f"📋 *عدد المهام:* {len(project_plan.get('generated_tasks', []))}\n"
            f"💰 *الميزانية:* {project_plan.get('estimated_budget_range', 'غير محددة')}\n"
            f"🛠️ *التقنيات:* {', '.join(project_plan.get('suggested_tech_stack', ['غير محددة'])[:3])}\n\n"
            f"✅ تم التوليد بواسطة Gemini 2.5 Flash"
        )
        response = requests.post(url, data={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }, timeout=5)
        return response.status_code == 200
    except Exception:
        return False

# ============================================================
# 6. HITL: تعديل المهام يدوياً
# ============================================================
def display_tasks_with_hitl(tasks: list) -> list | None:
    if not tasks:
        return None
    modified_tasks = []
    st.markdown("### ✏️ مراجعة المهام (يمكنك تعديلها قبل الاعتماد)")
    st.caption("قم بتعديل العناوين، الأوصاف، المدة، أو الأولوية حسب رؤيتك")
    for idx, task in enumerate(tasks, 1):
        with st.container(border=True):
            st.markdown(f"#### 📌 المهمة {idx}")
            col1, col2 = st.columns([2, 1])
            with col1:
                new_title = st.text_input(f"العنوان {idx}", value=task.get('title', ''), key=f"hitl_title_{idx}")
                new_desc = st.text_area(f"الوصف {idx}", value=task.get('description', ''), key=f"hitl_desc_{idx}", height=60)
            with col2:
                new_days = st.number_input(f"المدة (أيام) {idx}", min_value=1, value=task.get('estimated_days', 2), key=f"hitl_days_{idx}")
                priority_options = ['High', 'Medium', 'Low']
                current_priority = task.get('priority', 'Medium')
                safe_index = priority_options.index(current_priority) if current_priority in priority_options else 1
                new_priority = st.selectbox(f"الأولوية {idx}", priority_options, index=safe_index, key=f"hitl_priority_{idx}")
            modified_tasks.append({
                'title': new_title,
                'description': new_desc,
                'estimated_days': new_days,
                'priority': new_priority
            })
    if st.button("✅ اعتماد الخطة النهائية", use_container_width=True):
        return modified_tasks
    return None

# ============================================================
# 7. توليد الخطة (RAG + Gemini)
# ============================================================
def generate_project_plan_safe(api_key: str, interview_data: dict) -> dict:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    similar_plans = cloudsql_utils.get_similar_projects(interview_data["idea"], top_k=2)
    similar_context = ""
    if similar_plans:
        similar_context = "\n\n**📚 مشاريع سابقة مشابهة (تم استرجاعها من الذاكرة):**\n"
        for i, p in enumerate(similar_plans, 1):
            summary = p.get('summary', '')[:150]
            similar_context += f"{i}. {summary}...\n"
    prompt = f"""
أنت خبير منتجات تقني محترف في منصة "مهنة" للعمل الحر.
العميل التالي يريد بناء مشروع برمجي:

📋 **بيانات العميل:**
- الاسم: {interview_data["name"]}
- الفكرة: {interview_data["idea"]}
- الميزانية: {interview_data["budget"]}
- الجدول الزمني: {interview_data["timeline"]}
- التوجيه التقني: {interview_data["tech_pref"]}
{similar_context}

🎯 **المطلوب:**
أخرج خطة عمل على شكل JSON فقط (بدون أي نص إضافي) وفق الهيكل التالي:
{{
  "client_name": "اسم العميل",
  "project_summary": "ملخص المشروع بالعربية (جملة أو جملتين)",
  "suggested_tech_stack": ["تقنية1", "تقنية2", "تقنية3"],
  "estimated_budget_range": "نطاق الميزانية",
  "generated_tasks": [
    {{ "title": "عنوان المهمة", "description": "وصف المهمة", "estimated_days": 2, "priority": "High" }}
  ]
}}

📌 **ملاحظات:**
- الأولوية يجب أن تكون: High أو Medium أو Low
- عدد المهام: من 4 إلى 7 مهام
- استخدم اللغة العربية في جميع الحقول
- استفد من المشاريع المشابهة إن وجدت
"""
    try:
        response = model.generate_content(prompt)
        raw = response.text
        try:
            return json.loads(raw.strip())
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise ValueError("لم نتمكن من استخراج JSON صحيح من نموذج Gemini.")
    except Exception as e:
        raise ValueError(f"فشل توليد الخطة: {e}")

# ============================================================
# 8. تصدير PDF و Excel (للخطة)
# ============================================================
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def generate_excel(plan_json):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        summary_df = pd.DataFrame({
            'البيان': ['اسم العميل', 'الملخص', 'الميزانية', 'تاريخ التوليد'],
            'القيمة': [
                plan_json.get('client_name', ''),
                plan_json.get('project_summary', ''),
                plan_json.get('estimated_budget_range', ''),
                datetime.now().strftime("%Y-%m-%d %H:%M")
            ]
        })
        summary_df.to_excel(writer, sheet_name='ملخص', index=False)
        tasks = plan_json.get('generated_tasks', [])
        if tasks:
            tasks_df = pd.DataFrame(tasks)
            tasks_df.to_excel(writer, sheet_name='المهام', index=False)
        tech_stack = plan_json.get('suggested_tech_stack', [])
        if tech_stack:
            tech_df = pd.DataFrame({'التقنيات المقترحة': tech_stack})
            tech_df.to_excel(writer, sheet_name='التقنيات', index=False)
        workbook = writer.book
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for col_num, col in enumerate(worksheet.columns):
                max_len = max(len(str(cell.value)) for cell in col) + 2
                worksheet.set_column(col_num, col_num, min(max_len, 50))
    return output.getvalue()

def generate_pdf(plan_json):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    arabic_style = ParagraphStyle(
        'ArabicStyle',
        parent=normal_style,
        fontName='Helvetica',
        fontSize=10,
        alignment=0,
        spaceAfter=6
    )
    elements = []
    elements.append(Paragraph("🧠 خطة مشروع - وكيل مهنة PRO", title_style))
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph(f"<b>اسم العميل:</b> {plan_json.get('client_name', 'غير محدد')}", arabic_style))
    elements.append(Paragraph(f"<b>الميزانية المقترحة:</b> {plan_json.get('estimated_budget_range', 'غير محددة')}", arabic_style))
    elements.append(Paragraph(f"<b>تاريخ التوليد:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", arabic_style))
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph("<b>📌 ملخص المشروع</b>", heading_style))
    elements.append(Paragraph(plan_json.get('project_summary', 'لا يوجد ملخص'), arabic_style))
    elements.append(Spacer(1, 0.1*inch))
    tech_stack = plan_json.get('suggested_tech_stack', [])
    if tech_stack:
        elements.append(Paragraph("<b>🛠️ التقنيات المقترحة</b>", heading_style))
        tech_text = "، ".join(tech_stack)
        elements.append(Paragraph(tech_text, arabic_style))
        elements.append(Spacer(1, 0.1*inch))
    tasks = plan_json.get('generated_tasks', [])
    if tasks:
        elements.append(Paragraph("<b>📋 المهام</b>", heading_style))
        for idx, task in enumerate(tasks, 1):
            priority = task.get('priority', 'Medium')
            emoji = "🔴" if priority == "High" else "🟡" if priority == "Medium" else "🟢"
            task_text = f"{emoji} <b>{idx}. {task.get('title', 'بدون عنوان')}</b> ({priority}) - {task.get('estimated_days', 2)} أيام"
            elements.append(Paragraph(task_text, arabic_style))
            desc = task.get('description', 'لا يوجد وصف')
            elements.append(Paragraph(f"&nbsp;&nbsp;{desc}", arabic_style))
            elements.append(Spacer(1, 0.05*inch))
    doc.build(elements)
    return buffer.getvalue()

# ============================================================
# 9. محرك التحليل المتقدم (Advanced Analytics Engine)
# ============================================================
def calculate_project_metrics(project_data: dict) -> dict:
    tasks = project_data.get('generated_tasks', [])
    total_days = sum(t.get('estimated_days', 0) for t in tasks)
    total_tasks = len(tasks)
    high_priority = sum(1 for t in tasks if t.get('priority') == 'High')
    medium_priority = sum(1 for t in tasks if t.get('priority') == 'Medium')
    low_priority = sum(1 for t in tasks if t.get('priority') == 'Low')
    base_cost = total_days * 150
    overhead = base_cost * 0.2
    total_cost = base_cost + overhead
    cost_per_task = total_cost / total_tasks if total_tasks else 0
    high_ratio = high_priority / total_tasks if total_tasks else 0
    long_tasks = sum(1 for t in tasks if t.get('estimated_days', 0) > 5)
    long_ratio = long_tasks / total_tasks if total_tasks else 0
    risk_score = min(100, int((high_ratio * 0.6 + long_ratio * 0.4) * 100))
    avg_desc_len = sum(len(t.get('description', '')) for t in tasks) / total_tasks if total_tasks else 0
    confidence_score = min(100, int((min(total_tasks / 10, 1) * 0.5 + min(avg_desc_len / 100, 1) * 0.5) * 100))
    roi = total_cost * 0.3
    return {
        'total_days': total_days,
        'total_tasks': total_tasks,
        'high_priority': high_priority,
        'medium_priority': medium_priority,
        'low_priority': low_priority,
        'base_cost': base_cost,
        'overhead': overhead,
        'total_cost': total_cost,
        'cost_per_task': cost_per_task,
        'risk_score': risk_score,
        'confidence_score': confidence_score,
        'roi': roi,
        'avg_days_per_task': total_days / total_tasks if total_tasks else 0,
        'long_tasks': long_tasks
    }

def render_advanced_analytics(plan_json: dict):
    st.markdown("## 📊 تحليل الخطة الذكي")
    metrics = calculate_project_metrics(plan_json)
    tasks = plan_json.get('generated_tasks', [])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📅 إجمالي الأيام", metrics['total_days'], delta=None)
    with col2:
        st.metric("💰 التكلفة التقديرية", f"${metrics['total_cost']:,.0f}", delta=f"${metrics['base_cost']:,.0f} أساسي")
    with col3:
        st.metric("⚠️ درجة المخاطرة", f"{metrics['risk_score']}%", delta="عالي" if metrics['risk_score'] > 50 else "منخفض")
    with col4:
        st.metric("📊 الثقة", f"{metrics['confidence_score']}%", delta=None)
    st.divider()
    
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        fig1 = go.Figure(data=[go.Pie(
            labels=['عالية', 'متوسطة', 'منخفضة'],
            values=[metrics['high_priority'], metrics['medium_priority'], metrics['low_priority']],
            marker=dict(colors=['#ff4b4b', '#ffa500', '#2ecc71']),
            hole=0.3
        )])
        fig1.update_layout(title="توزيع المهام حسب الأولوية")
        st.plotly_chart(fig1, use_container_width=True)
    with col_chart2:
        if tasks:
            task_names = [f"مهمة {i+1}" for i in range(len(tasks))]
            task_days = [t.get('estimated_days', 0) for t in tasks]
            colors = ['#1E3A8A' if t.get('priority')=='High' else '#F5A623' if t.get('priority')=='Medium' else '#2ecc71' for t in tasks]
            fig2 = go.Figure(data=[go.Bar(
                x=task_names,
                y=task_days,
                marker_color=colors,
                text=task_days,
                textposition='auto'
            )])
            fig2.update_layout(title="أيام العمل لكل مهمة", xaxis_title="المهام", yaxis_title="أيام")
            st.plotly_chart(fig2, use_container_width=True)
    
    col_chart3, col_chart4 = st.columns(2)
    with col_chart3:
        if tasks:
            priority_cost = {'High': 0, 'Medium': 0, 'Low': 0}
            for t in tasks:
                priority = t.get('priority', 'Medium')
                days = t.get('estimated_days', 0)
                priority_cost[priority] += days * 150
            fig3 = go.Figure(data=[go.Pie(
                labels=['عالية', 'متوسطة', 'منخفضة'],
                values=[priority_cost['High'], priority_cost['Medium'], priority_cost['Low']],
                marker=dict(colors=['#ff4b4b', '#ffa500', '#2ecc71'])
            )])
            fig3.update_layout(title="توزيع التكلفة حسب الأولوية")
            st.plotly_chart(fig3, use_container_width=True)
    with col_chart4:
        fig4 = make_subplots(rows=1, cols=2, subplot_titles=("المخاطرة", "الثقة"))
        fig4.add_trace(go.Indicator(
            mode="gauge+number+delta",
            value=metrics['risk_score'],
            title={'text': "مخاطرة"},
            delta={'reference': 50},
            gauge={'axis': {'range': [None, 100]},
                   'steps': [
                       {'range': [0, 30], 'color': "#2ecc71"},
                       {'range': [30, 70], 'color': "#ffa500"},
                       {'range': [70, 100], 'color': "#ff4b4b"}
                   ],
                   'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 90}}
        ), row=1, col=1)
        fig4.add_trace(go.Indicator(
            mode="gauge+number+delta",
            value=metrics['confidence_score'],
            title={'text': "ثقة"},
            delta={'reference': 70},
            gauge={'axis': {'range': [None, 100]},
                   'steps': [
                       {'range': [0, 40], 'color': "#ff4b4b"},
                       {'range': [40, 70], 'color': "#ffa500"},
                       {'range': [70, 100], 'color': "#2ecc71"}
                   ],
                   'threshold': {'line': {'color': "green", 'width': 4}, 'thickness': 0.75, 'value': 80}}
        ), row=1, col=2)
        fig4.update_layout(height=300)
        st.plotly_chart(fig4, use_container_width=True)
    
    st.markdown("### 📋 جدول التحليل التفصيلي")
    df_analytics = pd.DataFrame({
        'المقياس': ['إجمالي الأيام', 'عدد المهام', 'عالية الأولوية', 'متوسطة الأولوية', 'منخفضة الأولوية',
                   'التكلفة الأساسية', 'التكاليف الإضافية', 'التكلفة الإجمالية', 'التكلفة لكل مهمة',
                   'درجة المخاطرة', 'درجة الثقة', 'العائد المتوقع (ROI)', 'متوسط الأيام لكل مهمة', 'مهام طويلة (>5 أيام)'],
        'القيمة': [
            metrics['total_days'], metrics['total_tasks'], metrics['high_priority'],
            metrics['medium_priority'], metrics['low_priority'],
            f"${metrics['base_cost']:,.0f}", f"${metrics['overhead']:,.0f}",
            f"${metrics['total_cost']:,.0f}", f"${metrics['cost_per_task']:,.2f}",
            f"{metrics['risk_score']}%", f"{metrics['confidence_score']}%",
            f"${metrics['roi']:,.0f}", f"{metrics['avg_days_per_task']:.1f} أيام",
            metrics['long_tasks']
        ]
    })
    st.dataframe(df_analytics, use_container_width=True, hide_index=True)
    
    st.markdown("### 💡 توصيات ذكية")
    recommendations = []
    if metrics['risk_score'] > 70:
        recommendations.append("⚠️ **مخاطرة عالية**: يُوصى بتقسيم المهام عالية الأولوية إلى مهام أصغر لتقليل المخاطر.")
    if metrics['confidence_score'] < 50:
        recommendations.append("📝 **تفاصيل غير كافية**: يُوصى بإضافة تفاصيل أكثر للمهام لزيادة دقة التقدير.")
    if metrics['total_days'] > 30:
        recommendations.append("⏳ **جدول زمني طويل**: يُوصى بتقسيم المشروع إلى مراحل (Phases) لتسهيل التتبع.")
    if metrics['high_priority'] / metrics['total_tasks'] > 0.5:
        recommendations.append("🔥 **كثافة عالية الأولوية**: يُوصى بإعادة تقييم الأولويات لتجنب ضغط العمل.")
    if not recommendations:
        recommendations.append("✅ **خطة متوازنة**: الخطة تبدو جيدة ومتوازنة. استمر في التنفيذ.")
    for rec in recommendations:
        st.info(rec)
    
    # تصدير تقرير التحليل
    st.markdown("### 📥 تصدير تقرير التحليل")
    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        try:
            st.download_button(
                label="📄 تحميل تقرير التحليل (PDF)",
                data=generate_analytics_pdf(plan_json, metrics),
                file_name=f"analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.warning(f"⚠️ تعذر إنشاء PDF: {e}")
    with col_exp2:
        try:
            st.download_button(
                label="📊 تحميل تقرير التحليل (Excel)",
                data=generate_analytics_excel(plan_json, metrics),
                file_name=f"analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.warning(f"⚠️ تعذر إنشاء Excel: {e}")

def generate_analytics_pdf(plan_json, metrics):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []
    elements.append(Paragraph("📊 تقرير التحليل الذكي - وكيل مهنة PRO", styles['Title']))
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph(f"<b>العميل:</b> {plan_json.get('client_name', 'غير محدد')}", styles['Normal']))
    elements.append(Paragraph(f"<b>تاريخ التقرير:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))
    data = [
        ['المقياس', 'القيمة'],
        ['إجمالي الأيام', str(metrics['total_days'])],
        ['عدد المهام', str(metrics['total_tasks'])],
        ['عالية الأولوية', str(metrics['high_priority'])],
        ['متوسطة الأولوية', str(metrics['medium_priority'])],
        ['منخفضة الأولوية', str(metrics['low_priority'])],
        ['التكلفة الأساسية', f"${metrics['base_cost']:,.0f}"],
        ['التكاليف الإضافية', f"${metrics['overhead']:,.0f}"],
        ['التكلفة الإجمالية', f"${metrics['total_cost']:,.0f}"],
        ['درجة المخاطرة', f"{metrics['risk_score']}%"],
        ['درجة الثقة', f"{metrics['confidence_score']}%"],
        ['العائد المتوقع (ROI)', f"${metrics['roi']:,.0f}"]
    ]
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)
    doc.build(elements)
    return buffer.getvalue()

def generate_analytics_excel(plan_json, metrics):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df = pd.DataFrame({
            'المقياس': ['إجمالي الأيام', 'عدد المهام', 'عالية الأولوية', 'متوسطة الأولوية', 'منخفضة الأولوية',
                       'التكلفة الأساسية', 'التكاليف الإضافية', 'التكلفة الإجمالية', 'التكلفة لكل مهمة',
                       'درجة المخاطرة', 'درجة الثقة', 'العائد المتوقع (ROI)', 'متوسط الأيام لكل مهمة', 'مهام طويلة (>5 أيام)'],
            'القيمة': [
                metrics['total_days'], metrics['total_tasks'], metrics['high_priority'],
                metrics['medium_priority'], metrics['low_priority'],
                f"${metrics['base_cost']:,.0f}", f"${metrics['overhead']:,.0f}",
                f"${metrics['total_cost']:,.0f}", f"${metrics['cost_per_task']:,.2f}",
                f"{metrics['risk_score']}%", f"{metrics['confidence_score']}%",
                f"${metrics['roi']:,.0f}", f"{metrics['avg_days_per_task']:.1f} أيام",
                metrics['long_tasks']
            ]
        })
        df.to_excel(writer, index=False, sheet_name='التحليل')
        workbook = writer.book
        worksheet = writer.sheets['التحليل']
        for i, col in enumerate(df.columns):
            max_len = max(len(str(cell)) for cell in df[col]) + 2
            worksheet.set_column(i, i, min(max_len, 50))
    return output.getvalue()

# ============================================================
# 10. لوحة التحكم المتطورة (مع التحليلات)
# ============================================================
def display_project_dashboard():
    st.subheader("📊 لوحة تحكم مشاريعك")
    try:
        user_id = st.session_state.get("user_id")
        projects = cloudsql_utils.get_all_projects(user_id)
        if not projects:
            st.info("💡 لا توجد مشاريع حالياً. ابدأ بإنشاء خطة جديدة من التبويب المجاور!")
            return
        df = pd.DataFrame(projects)
        st.success(f"✅ عدد المشاريع: {len(projects)}")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📋 إجمالي المشاريع", len(projects))
        with col2:
            try:
                budgets = [int(re.findall(r'\d+', str(b))[0]) for b in df['budget_range'] if re.findall(r'\d+', str(b))]
                avg_budget = sum(budgets)/len(budgets) if budgets else 0
                st.metric("💰 متوسط الميزانية", f"${avg_budget:,.0f}")
            except:
                st.metric("💰 متوسط الميزانية", "غير متاح")
        with col3:
            st.metric("📌 عدد المهام", "متاح")
        with col4:
            st.metric("🟢 الحالة", "نشط")
        st.markdown("### 📋 قائمة المشاريع")
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # التحليل المتقدم عند اختيار مشروع
        if len(projects) > 0:
            st.markdown("### 🔍 تحليل متقدم لمشروع معين")
            project_options = [f"{p['id']} - {p['client_name']}" for p in projects]
            selected = st.selectbox("اختر مشروعاً لتحليله", project_options)
            if selected:
                selected_id = int(selected.split(' - ')[0])
                conn = cloudsql_utils.get_db_connection()
                if conn:
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("SELECT * FROM projects WHERE id = %s", (selected_id,))
                    project = cursor.fetchone()
                    if project:
                        cursor.execute("SELECT * FROM tasks WHERE project_id = %s", (selected_id,))
                        tasks = cursor.fetchall()
                        conn.close()
                        full_project = {
                            'client_name': project['client_name'],
                            'project_summary': project['summary'],
                            'suggested_tech_stack': json.loads(project['tech_stack']) if project['tech_stack'] else [],
                            'estimated_budget_range': project['budget_range'],
                            'generated_tasks': tasks
                        }
                        render_advanced_analytics(full_project)
        
        # رسوم بيانية عامة
        if len(projects) > 1:
            st.markdown("### 📈 تحليل المشاريع")
            fig = px.bar(df, x='client_name', y='budget_range', 
                         title="الميزانية حسب العميل",
                         color='client_name')
            st.plotly_chart(fig, use_container_width=True)
            if 'created_at' in df.columns:
                df['date'] = pd.to_datetime(df['created_at']).dt.date
                fig2 = px.line(df.groupby('date').size().reset_index(name='count'),
                               x='date', y='count',
                               title="عدد المشاريع حسب التاريخ",
                               markers=True)
                st.plotly_chart(fig2, use_container_width=True)
    except Exception as e:
        st.warning(f"⚠️ تعذر تحميل البيانات: {e}")

# ============================================================
# 11. الواجهة الرئيسية
# ============================================================
st.set_page_config(
    page_title="وكيل مهنة - مخطط المشاريع الذكي",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    init_auth()
    if not st.session_state.authenticated:
        render_login_page()
        return
    render_enterprise_sidebar()
    st.markdown("""
    <style>
        .main-header { text-align: center; padding: 1rem 0; }
        .main-header h1 { color: #1E3A8A; font-size: 2.8rem; font-weight: 800; }
        .main-header h1 span { color: #F5A623; }
        .main-header p { color: #4B5563; font-size: 1.1rem; margin-top: -5px; }
        .stButton button { width: 100%; background-color: #1E3A8A; color: white; border-radius: 8px; height: 3rem; transition: 0.3s; }
        .stButton button:hover { background-color: #1D4ED8; transform: scale(1.02); }
        .quick-btn { background-color: #F5A623 !important; color: white !important; }
        .quick-btn:hover { background-color: #E69500 !important; }
        .card-task { background-color: #F9FAFB; padding: 1.2rem; border-radius: 8px; border-right: 5px solid #1E3A8A; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
        .stExpander { border: 1px solid #e0e0e0; border-radius: 8px; }
        .stTabs [data-baseweb="tab-list"] { gap: 2rem; }
        .stTabs [data-baseweb="tab"] { font-size: 1.1rem; font-weight: 600; }
        .stTabs [aria-selected="true"] { color: #1E3A8A; border-bottom: 3px solid #F5A623; }
        .stAlert { border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div class="main-header">
        <h1>🧠 وكيل مهنة <span>PRO</span></h1>
        <p>حوّل فكرتك إلى خطة هندسية متكاملة في 3 ثوانٍ</p>
    </div>
    """, unsafe_allow_html=True)
    st.info("💡 **توفر عليك 40 ساعة عمل و 500$ من استشارة مدير مشروع**", icon="💎")
    st.divider()
    
    with st.sidebar:
        st.write(f"👤 **مرحباً, {st.session_state.username}**")
        if st.button("🚪 تسجيل الخروج", use_container_width=True):
            logout_user()
            st.rerun()
        st.divider()
        st.header("⚙️ إعدادات إضافية")
        st.divider()
        st.subheader("📊 رصيدك المجاني")
        init_usage()
        if st.session_state.is_premium:
            st.success("✨ مشترك مميز (غير محدود)")
        else:
            remaining = st.session_state.free_uses
            if remaining > 0:
                st.info(f"⚡ متبقي {remaining} تحويلات مجانية")
            else:
                st.warning("🚫 انتهت استخداماتك! اشترك للمتابعة.")
        st.divider()
        if st.button("💎 اشترك الآن (9.99$ شهرياً)", use_container_width=True):
            st.session_state.show_payment = True
        if st.session_state.get("show_payment", False):
            with st.expander("💳 إتمام الدفع", expanded=True):
                user_email = st.text_input("✉️ البريد الإلكتروني", placeholder="أدخل بريدك الإلكتروني")
                if st.button("🔗 إنشاء رابط الدفع", use_container_width=True):
                    if not user_email:
                        st.warning("⚠️ يرجى إدخال البريد الإلكتروني")
                    else:
                        try:
                            url = create_checkout_url(user_email, st.session_state.username)
                            st.success("✅ تم إنشاء رابط الدفع!")
                            st.markdown(f"[🔗 اضغط هنا لإتمام الدفع]({url})", unsafe_allow_html=True)
                            st.session_state.show_payment = False
                        except Exception as e:
                            st.error(f"❌ {e}")
        with st.expander("💎 خطط الاشتراك"):
            st.markdown("""
            - **📦 مجاني**: 5 تحويلات
            - **🚀 شهري**: 9.99$ - تحويلات غير محدودة
            - **🏆 سنوي**: 99.99$ - خصم 20%
            """)
        st.divider()
        st.caption("🌟 يثق بنا: 5 عملاء حقيقيون في اليمن")
        st.caption("🏅 أفضل وكيل تخطيط في الشرق الأوسط")
    
    tab1, tab2 = st.tabs(["🚀 إنشاء خطة جديدة", "📊 لوحة تحكم مشاريعك"])
    with tab2:
        display_project_dashboard()
    with tab1:
        st.markdown("### 📝 أدخل تفاصيل مشروعك")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("📚 منصة تعليمية", use_container_width=True, key="edu_btn"):
                st.session_state.example = "education"
        with col_btn2:
            if st.button("🛒 متجر إلكتروني", use_container_width=True, key="shop_btn"):
                st.session_state.example = "ecommerce"
        if "example" not in st.session_state:
            st.session_state.example = ""
        if st.session_state.example == "education":
            default_name = "مؤسسة أفق التعليمية"
            default_idea = "منصة تعليمية تفاعلية للطلاب في اليمن تدعم الفصول المباشرة والاختبارات الآلية ولوحة تحكم للمعلمين، مع نظام دفع محلي وتجربة مستخدم محسّنة لسرعات الإنترنت المنخفضة"
            default_budget = "8000 - 12000"
            default_timeline = "8 أسابيع"
            default_tech = "Flutter, Node.js, Supabase, Gemini AI, WebRTC"
        elif st.session_state.example == "ecommerce":
            default_name = "متجر اليمن الرقمي"
            default_idea = "منصة تجارة إلكترونية بسيطة وآمنة تعمل في اليمن، تدعم المنتجات المحلية والدفع عند الاستلام، مع لوحة تحكم للتجار"
            default_budget = "5000 - 8000"
            default_timeline = "6 أسابيع"
            default_tech = "Flutter, Node.js, Supabase, Stripe"
        else:
            default_name = default_idea = default_budget = default_timeline = default_tech = ""
        with st.form("project_form"):
            col1, col2 = st.columns(2)
            with col1:
                client_name = st.text_input("👤 اسم العميل / الشركة", value=default_name, placeholder="أدخل اسم العميل")
            with col2:
                budget = st.text_input("💰 الميزانية المتوقعة", placeholder="مثال: 2000 - 3000 دولار", value=default_budget)
            project_idea = st.text_area("💡 صف رؤية أو فكرة مشروعك بالتفصيل", height=120, value=default_idea,
                                        placeholder="اكتب فكرة مشروعك هنا بتفصيل معقول...")
            word_count = len(project_idea.split()) if project_idea else 0
            st.caption(f"📝 {word_count} كلمة (يُفضل 50-100 كلمة)")
            col3, col4 = st.columns(2)
            with col3:
                timeline = st.text_input("📅 الجدول الزمني المستهدف", placeholder="مثال: 4 أسابيع", value=default_timeline)
            with col4:
                tech_pref = st.text_input("⚙️ تفضيلات تقنية (اختياري)", value=default_tech,
                                          placeholder="مثال: Flutter, Node.js, Supabase")
            submitted = st.form_submit_button("🚀 توليد الخطة الهندسية الآن", use_container_width=True)
        
        if submitted:
            gemini_key = get_active_gemini_key()
            if not gemini_key:
                st.error("❌ مفتاح Gemini مفقود. يرجى إدخاله في مركز إدارة الذكاء الاصطناعي (الشريط الجانبي).")
                st.stop()
            if not client_name or not project_idea:
                st.error("❌ يرجى ملء اسم العميل وفكرة المشروع.")
                st.stop()
            if not can_use():
                st.error("🚫 انتهت استخداماتك المجانية. يرجى الاشتراك للمتابعة.")
                st.stop()
            interview_data = {
                "name": client_name,
                "idea": project_idea,
                "budget": budget if budget else "تحدد بعد التحليل",
                "timeline": timeline if timeline else "غير محدد",
                "tech_pref": tech_pref if tech_pref else "اعتمد أفضل الممارسات"
            }
            with st.spinner("🔄 وكيل مهنة يحلل المتطلبات ويبحث في الذاكرة..."):
                try:
                    plan_json = generate_project_plan_safe(gemini_key, interview_data)
                    deduct_usage()
                    cloudsql_utils.save_to_cloudsql(plan_json, st.session_state.user_id)
                    bot_token = st.secrets.get("TELEGRAM_BOT_TOKEN", os.getenv("TELEGRAM_BOT_TOKEN"))
                    chat_id = st.secrets.get("TELEGRAM_CHAT_ID", os.getenv("TELEGRAM_CHAT_ID"))
                    if bot_token and chat_id:
                        send_telegram_alert(bot_token, chat_id, plan_json)
                    
                    st.success("✅ تم توليد الخطة بنجاح!")
                    st.divider()
                    
                    # عرض التحليلات المتقدمة أولاً
                    render_advanced_analytics(plan_json)
                    
                    # ملخص المشروع
                    if plan_json.get("project_summary"):
                        st.markdown("### 📌 ملخص المشروع")
                        st.info(plan_json["project_summary"])
                    tech_stack = plan_json.get("suggested_tech_stack", [])
                    if tech_stack:
                        st.markdown("### 🛠️ التقنيات المقترحة")
                        cols = st.columns(min(len(tech_stack), 4))
                        for i, tech in enumerate(tech_stack):
                            cols[i % len(cols)].markdown(f"- {tech}")
                    
                    # HITL
                    tasks = plan_json.get("generated_tasks", [])
                    if tasks:
                        edited_tasks = display_tasks_with_hitl(tasks)
                        if edited_tasks:
                            plan_json['generated_tasks'] = edited_tasks
                            st.success("✅ تم اعتماد الخطة المعدلة!")
                    
                    # عرض المهام النهائية
                    final_tasks = plan_json.get("generated_tasks", [])
                    if final_tasks:
                        st.markdown("### 📋 المهام المقترحة")
                        for idx, task in enumerate(final_tasks, 1):
                            priority = task.get("priority", "Medium")
                            emoji = "🔴" if priority == "High" else "🟡" if priority == "Medium" else "🟢"
                            with st.container(border=True):
                                col1, col2 = st.columns([4, 1])
                                with col1:
                                    st.markdown(f"**{idx}. {task.get('title', 'بدون عنوان')}**")
                                with col2:
                                    st.markdown(f"{emoji} {priority}")
                                st.caption(f"📅 المدة: {task.get('estimated_days', 'غير محدد')} أيام")
                                st.write(task.get("description", "لا يوجد وصف"))
                    else:
                        st.warning("⚠️ لم يتم توليد أي مهام. حاول إعادة صياغة فكرة المشروع.")
                    
                    # JSON الخام
                    with st.expander("📄 عرض هيكل JSON الخام (للتحميل والفحص)"):
                        st.json(plan_json)
                    
                    # أزرار التحميل (JSON, TXT, PDF, Excel)
                    st.divider()
                    st.markdown("### 💾 تحميل الخطة")
                    session_id = str(uuid.uuid4())[:8]
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"project_plan_{timestamp}_{session_id}"
                    
                    # JSON
                    json_data = json.dumps(plan_json, indent=2, ensure_ascii=False)
                    st.download_button(
                        label="📥 تحميل خطة العمل (JSON)",
                        data=json_data,
                        file_name=f"{filename}.json",
                        mime="application/json",
                        key="download_json",
                        use_container_width=True
                    )
                    
                    # TXT
                    txt_data = f"=== خطة مشروع {plan_json.get('client_name', 'عميل')} ===\n\n"
                    txt_data += f"الملخص: {plan_json.get('project_summary', 'لا يوجد ملخص')}\n\n"
                    txt_data += "=== المهام ===\n"
                    for idx, task in enumerate(final_tasks, 1):
                        txt_data += f"{idx}. {task.get('title', 'بدون عنوان')} ({task.get('priority', 'Medium')}) - {task.get('estimated_days', '?')} أيام\n"
                        txt_data += f"   {task.get('description', 'لا يوجد وصف')}\n\n"
                    st.download_button(
                        label="📥 تحميل خطة العمل (نصي)",
                        data=txt_data,
                        file_name=f"{filename}.txt",
                        mime="text/plain",
                        key="download_txt",
                        use_container_width=True
                    )
                    
                    # PDF
                    try:
                        pdf_data = generate_pdf(plan_json)
                        st.download_button(
                            label="📄 تحميل خطة العمل (PDF)",
                            data=pdf_data,
                            file_name=f"{filename}.pdf",
                            mime="application/pdf",
                            key="download_pdf",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.warning(f"⚠️ تعذر إنشاء PDF: {e}")
                    
                    # Excel
                    try:
                        excel_data = generate_excel(plan_json)
                        st.download_button(
                            label="📊 تحميل خطة العمل (Excel)",
                            data=excel_data,
                            file_name=f"{filename}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="download_excel",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.warning(f"⚠️ تعذر إنشاء Excel: {e}")
                    
                    # تقييم المستخدم
                    st.divider()
                    st.markdown("### ⭐ تقييمك للخطة")
                    rating = st.select_slider("ما مدى دقة الخطة؟", options=[1, 2, 3, 4, 5], value=4)
                    if rating < 3:
                        st.warning("سنحسن الخطة بناءً على ملاحظاتك، شكراً لك!")
                    else:
                        st.success("شكراً لتقييمك الإيجابي!")
                    
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ حدث خطأ أثناء توليد الخطة: {e}")

if __name__ == "__main__":
    main()

def get_db_connection():
    try:
        import os, pymysql
        connection = pymysql.connect(
            unix_socket=f"/cloudsql/{os.environ.get('CLOUD_SQL_CONNECTION_NAME')}",
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASSWORD'),
            database=os.environ.get('DB_NAME'),
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        print(f"Database connection error: {e}")
        return None
