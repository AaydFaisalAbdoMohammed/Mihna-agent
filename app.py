#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import re
import uuid
import requests
import bcrypt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import base64
from datetime import datetime
import streamlit as st
import google.generativeai as genai
import config
import cloudsql_utils

# ============================================================
# نظام AI Gateway (مرن لإدارة مفاتيح Gemini)
# ============================================================
def get_active_gemini_key():
    env_key = os.getenv("GEMINI_API_KEY")
    if env_key and len(env_key) > 5:
        return env_key
    user_key = st.session_state.get("user_gemini_key")
    if user_key and len(user_key) > 5:
        return user_key
    return None

def render_enterprise_sidebar():
    with st.sidebar:
        st.markdown("### ⚙️ مركز إدارة الذكاء الاصطناعي")
        active_key = get_active_gemini_key()
        if active_key:
            st.success("🟢 محرك Gemini AI: نشط وجاهز")
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
        st.caption("• Cloud Run Cluster: **asia-south1 (Active)**")
        st.caption("• DB Engine: **MySQL TCP Pure Native**")
        st.caption("• Architecture: **Clean Architecture Modular**")

# ============================================================
# نظام المصادقة
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
    conn = cloudsql_utils.get_db_connection()
    if not conn:
        return False, "تعذر الاتصال بقاعدة البيانات"
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
    if cursor.fetchone():
        conn.close()
        return False, "اسم المستخدم أو البريد الإلكتروني موجود بالفعل"
    hashed_pw = hash_password(password)
    try:
        cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)", (username, email, hashed_pw))
        conn.commit()
        conn.close()
        return True, "تم إنشاء الحساب بنجاح!"
    except Exception as e:
        conn.close()
        return False, f"خطأ في إنشاء الحساب: {e}"

def login_user(identifier: str, password: str) -> tuple:
    conn = cloudsql_utils.get_db_connection()
    if not conn:
        return False, "تعذر الاتصال بقاعدة البيانات"
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, username, email, password_hash FROM users WHERE username = %s OR email = %s", (identifier, identifier))
    user = cursor.fetchone()
    conn.close()
    if not user:
        return False, "المستخدم غير موجود"
    if not verify_password(password, user['password_hash']):
        return False, "كلمة المرور غير صحيحة"
    st.session_state.authenticated = True
    st.session_state.user_id = user['id']
    st.session_state.username = user['username']
    st.session_state.user_email = user['email']
    return True, "تم تسجيل الدخول بنجاح!"

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
        .stButton button { width: 100%; background-color: #1E3A8A; color: white; border-radius: 8px; height: 3rem; }
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="auth-title">🧠 وكيل مهنة <span>PRO</span></div>', unsafe_allow_html=True)
    st.markdown('<p class="auth-subtitle">خطط مشاريعك بذكاء واحترافية</p>')
    
    tab1, tab2 = st.tabs(["🔑 تسجيل الدخول", "📝 إنشاء حساب جديد"])
    
    with tab1:
        with st.form("login_form"):
            identifier = st.text_input("👤 اسم المستخدم أو البريد الإلكتروني")
            password = st.text_input("🔒 كلمة المرور", type="password")
            if st.form_submit_button("تسجيل الدخول"):
                if not identifier or not password:
                    st.error("⚠️ يرجى ملء جميع الحقول")
                else:
                    success, msg = login_user(identifier, password)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
    
    with tab2:
        with st.form("signup_form"):
            new_username = st.text_input("👤 اسم المستخدم")
            new_email = st.text_input("✉️ البريد الإلكتروني")
            new_password = st.text_input("🔒 كلمة المرور", type="password")
            confirm_password = st.text_input("🔒 تأكيد كلمة المرور", type="password")
            if st.form_submit_button("إنشاء حساب"):
                if not new_username or not new_email or not new_password:
                    st.error("⚠️ يرجى ملء جميع الحقول")
                elif new_password != confirm_password:
                    st.error("⚠️ كلمتا المرور غير متطابقتين")
                elif len(new_password) < 6:
                    st.error("⚠️ كلمة المرور يجب أن تكون 6 أحرف على الأقل")
                elif not re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
                    st.error("⚠️ بريد إلكتروني غير صالح")
                else:
                    success, msg = create_user(new_username, new_email, new_password)
                    if success:
                        st.success(msg)
                    else:
                        st.error(f"❌ {msg}")

# ============================================================
# نظام الفريميوم
# ============================================================
def init_usage():
    if 'free_uses' not in st.session_state:
        st.session_state.free_uses = 5
        st.session_state.is_premium = False

def can_use():
    init_usage()
    return st.session_state.is_premium or st.session_state.free_uses > 0

def deduct_usage():
    init_usage()
    if not st.session_state.is_premium:
        st.session_state.free_uses -= 1
    return True

# ============================================================
# دوال الدفع (Lemon Squeezy)
# ============================================================
def create_checkout_url(user_email: str, user_name: str) -> str:
    if not config.LEMONSQUEEZY_API_KEY:
        raise Exception("مفتاح Lemon Squeezy غير مضبوط")
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
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code in (200, 201):
        return response.json()["data"]["attributes"]["url"]
    raise Exception(f"فشل الدفع: {response.text}")

# ============================================================
# توليد الخطة (RAG + Gemini)
# ============================================================
def generate_project_plan_safe(api_key: str, interview_data: dict) -> dict:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    similar_plans = cloudsql_utils.get_similar_projects(interview_data["idea"], top_k=2)
    similar_context = ""
    if similar_plans:
        similar_context = "\n\n**مشاريع سابقة مشابهة:**\n"
        for i, p in enumerate(similar_plans, 1):
            similar_context += f"{i}. {p.get('summary', '')[:150]}...\n"
    
    prompt = f"""
أنت خبير منتجات تقني في منصة "مهنة" للعمل الحر.
العميل التالي يريد بناء مشروع برمجي:
- الاسم: {interview_data["name"]}
- الفكرة: {interview_data["idea"]}
- الميزانية: {interview_data["budget"]}
- الجدول الزمني: {interview_data["timeline"]}
- التوجيه التقني: {interview_data["tech_pref"]}
{similar_context}

أخرج خطة عمل على شكل JSON فقط:
{{
  "client_name": "اسم العميل",
  "project_summary": "ملخص المشروع",
  "suggested_tech_stack": ["تقنية1", "تقنية2", "تقنية3"],
  "estimated_budget_range": "نطاق الميزانية",
  "generated_tasks": [
    {{ "title": "المهمة", "description": "الوصف", "estimated_days": 2, "priority": "High" }}
  ]
}}
"""
    response = model.generate_content(prompt)
    try:
        return json.loads(response.text.strip())
    except:
        match = re.search(r"{.*}", response.text, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError("لم نتمكن من استخراج JSON.")

# ============================================================
# لوحة التحكم المتطورة
# ============================================================
def display_project_dashboard():
    st.subheader("📊 لوحة تحكم مشاريعك")
    try:
        user_id = st.session_state.get("user_id")
        projects = cloudsql_utils.get_all_projects(user_id)
        if not projects:
            st.info("💡 لا توجد مشاريع حالياً. ابدأ بإنشاء خطة جديدة!")
            return
        
        df = pd.DataFrame(projects)
        st.success(f"✅ عدد المشاريع: {len(projects)}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📋 عدد المشاريع", len(projects))
        with col2:
            avg_budget = df['budget_range'].apply(lambda x: int(re.findall(r'\d+', str(x))[0]) if re.findall(r'\d+', str(x)) else 0).mean()
            st.metric("💰 متوسط الميزانية", f"${avg_budget:,.0f}")
        with col3:
            st.metric("📌 حالة الاتصال", "نشط 🟢")
        
        st.dataframe(df, use_container_width=True)
        
        if len(projects) > 1:
            fig = px.bar(df, x='client_name', y='budget_range', title="الميزانية حسب العميل")
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"⚠️ تعذر تحميل البيانات: {e}")

# ============================================================
# الواجهة الرئيسية
# ============================================================
st.set_page_config(page_title="وكيل مهنة - مخطط المشاريع الذكي", page_icon="🧠", layout="wide")

def main():
    init_auth()
    if not st.session_state.authenticated:
        render_login_page()
        return

    render_enterprise_sidebar()

    st.markdown("""
    <style>
        .main-header h1 { color: #1E3A8A; font-size: 2.8rem; text-align: center; }
        .main-header h1 span { color: #F5A623; }
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="main-header"><h1>🧠 وكيل مهنة <span>PRO</span></h1></div>', unsafe_allow_html=True)
    st.info("💡 **توفر عليك 40 ساعة عمل و 500$ من استشارة مدير مشروع**", icon="💎")
    st.divider()

    with st.sidebar:
        st.write(f"👤 مرحباً, {st.session_state.username}")
        if st.button("🚪 تسجيل الخروج"):
            logout_user()
            st.rerun()
        st.divider()
        st.header("⚙️ إعدادات إضافية")
        st.divider()
        st.subheader("📊 رصيدك المجاني")
        init_usage()
        if st.session_state.is_premium:
            st.success("✨ مشترك مميز")
        else:
            st.info(f"⚡ متبقي {st.session_state.free_uses} تحويلات")
        st.divider()
        if st.button("💎 اشترك الآن (9.99$ شهرياً)"):
            st.session_state.show_payment = True
        if st.session_state.get("show_payment", False):
            with st.expander("💳 إتمام الدفع"):
                user_email = st.text_input("✉️ البريد الإلكتروني")
                if st.button("🔗 إنشاء رابط الدفع"):
                    try:
                        url = create_checkout_url(user_email, st.session_state.username)
                        st.success(f"[اضغط هنا للدفع]({url})")
                        st.session_state.show_payment = False
                    except Exception as e:
                        st.error(f"❌ {e}")

    tab1, tab2 = st.tabs(["🚀 إنشاء خطة جديدة", "📊 لوحة تحكم مشاريعك"])
    with tab2:
        display_project_dashboard()
    with tab1:
        st.markdown("### 📝 أدخل تفاصيل مشروعك")
        with st.form("project_form"):
            col1, col2 = st.columns(2)
            with col1:
                client_name = st.text_input("👤 اسم العميل / الشركة")
            with col2:
                budget = st.text_input("💰 الميزانية المتوقعة", placeholder="2000 - 3000 دولار")
            project_idea = st.text_area("💡 صف فكرة مشروعك", height=120)
            col3, col4 = st.columns(2)
            with col3:
                timeline = st.text_input("📅 الجدول الزمني", placeholder="4 أسابيع")
            with col4:
                tech_pref = st.text_input("⚙️ تفضيلات تقنية (اختياري)")
            submitted = st.form_submit_button("🚀 توليد الخطة الهندسية الآن")
        
        if submitted:
            gemini_key = get_active_gemini_key()
            if not gemini_key:
                st.error("❌ مفتاح Gemini مفقود. يرجى إدخاله في مركز إدارة الذكاء الاصطناعي (الشريط الجانبي).")
                return
            if not client_name or not project_idea:
                st.error("❌ يرجى ملء جميع الحقول")
                return
            if not can_use():
                st.error("🚫 انتهت استخداماتك المجانية")
                return
            interview_data = {
                "name": client_name,
                "idea": project_idea,
                "budget": budget or "غير محدد",
                "timeline": timeline or "غير محدد",
                "tech_pref": tech_pref or "حسب الوكيل"
            }
            with st.spinner("🔄 جاري التوليد..."):
                try:
                    plan_json = generate_project_plan_safe(gemini_key, interview_data)
                    deduct_usage()
                    cloudsql_utils.save_to_cloudsql(plan_json, st.session_state.user_id)
                    st.success("✅ تم توليد وحفظ الخطة بنجاح!")
                    st.json(plan_json)
                except Exception as e:
                    st.error(f"❌ خطأ: {e}")

if __name__ == "__main__":
    main()
