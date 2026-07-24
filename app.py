#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import re
import uuid
import requests
from datetime import datetime
import streamlit as st
import google.generativeai as genai
import config  # يحتوي على المفاتيح (LEMONSQUEEZY_API_KEY, etc.)

# ============================================================
# دوال الدفع عبر Lemon Squeezy (تكامل حقيقي)
# ============================================================
def create_checkout_url(user_email: str, user_name: str) -> str:
    """إنشاء رابط دفع فريد للمستخدم باستخدام Lemon Squeezy API."""
    # التحقق من صحة المفاتيح
    if not config.LEMONSQUEEZY_API_KEY or config.LEMONSQUEEZY_API_KEY == "your_api_key_here":
        raise Exception("⚠️ مفتاح Lemon Squeezy API غير مضبوط (تحقق من ملف .env أو st.secrets)")
    if not config.LEMONSQUEEZY_STORE_ID or config.LEMONSQUEEZY_STORE_ID == "your_store_id_here":
        raise Exception("⚠️ معرف المتجر (Store ID) غير مضبوط")
    if not config.MONTHLY_VARIANT_ID or config.MONTHLY_VARIANT_ID == "your_variant_id_here":
        raise Exception("⚠️ معرف الخطة الشهرية (Variant ID) غير مضبوط")

    # طباعة جزء من المفتاح للتشخيص
    print(f"🔑 API Key: {config.LEMONSQUEEZY_API_KEY[:10]}...")
    print(f"🏪 Store ID: {config.LEMONSQUEEZY_STORE_ID}")
    print(f"📦 Variant ID: {config.MONTHLY_VARIANT_ID}")

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
                    "custom": {"user_id": str(st.session_state.get("user_id", "guest"))}
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
        data = response.json()
        checkout_url = data.get("data", {}).get("attributes", {}).get("url")
        if checkout_url:
            return checkout_url
        raise Exception("لم يتم العثور على رابط الدفع في الاستجابة")
    else:
        error_detail = response.json().get("errors", [{"detail": response.text}])
        error_msg = error_detail[0].get("detail", response.text)
        raise Exception(f"فشل الطلب (HTTP {response.status_code}): {error_msg}")

def verify_webhook_signature(payload: dict, signature: str) -> bool:
    """التحقق من أن الطلب قادم من Lemon Squeezy."""
    import hmac, hashlib
    secret = config.LEMONSQUEEZY_WEBHOOK_SECRET
    expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

# ============================================================
# نظام الفريميوم (Freemium) - 5 استخدامات مجانية
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
# RAG: البحث عن خطط مشابهة في الذاكرة المحلية
# ============================================================
def search_similar_plans(idea: str, top_k: int = 3) -> list:
    import json, os
    from difflib import SequenceMatcher
    db_path = 'data/plans/seed_plans.json'
    if not os.path.exists(db_path):
        return []
    with open(db_path, 'r', encoding='utf-8') as f:
        plans = json.load(f)
    scored = []
    for plan in plans:
        summary = plan.get('project_summary', '')
        score = SequenceMatcher(None, idea.lower(), summary.lower()).ratio()
        scored.append((score, plan))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [plan for score, plan in scored[:top_k]]

# ============================================================
# HITL: عرض المهام مع إمكانية التعديل والاعتماد
# ============================================================
def display_tasks_with_hitl(tasks):
    modified_tasks = []
    st.markdown("### ✏️ مراجعة المهام (يمكنك تعديلها)")
    for idx, task in enumerate(tasks, 1):
        with st.container(border=True):
            st.markdown(f"**المهمة {idx}**")
            new_title = st.text_input(f"عنوان المهمة {idx}", value=task.get('title', ''))
            new_desc = st.text_area(f"وصف المهمة {idx}", value=task.get('description', ''))
            new_days = st.number_input(f"عدد الأيام {idx}", min_value=1, value=task.get('estimated_days', 2))
            new_priority = st.selectbox(
                f"الأولوية {idx}",
                ['High', 'Medium', 'Low'],
                index=['High', 'Medium', 'Low'].index(task.get('priority', 'Medium'))
            )
            modified_tasks.append({
                'title': new_title,
                'description': new_desc,
                'estimated_days': new_days,
                'priority': new_priority
            })
    if st.button("✅ اعتماد الخطة النهائية"):
        return modified_tasks
    return None

# ============================================================
# دالة توليد الخطة (المحرك الآمن) مع دعم RAG
# ============================================================
def generate_project_plan_safe(api_key: str, interview_data: dict) -> dict:
    """توليد خطة عمل باستخدام Gemini مع دعم RAG."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    # --- RAG: البحث عن خطط مشابهة ---
    similar_plans = search_similar_plans(interview_data["idea"], top_k=2)
    similar_context = ""
    if similar_plans:
        similar_context = "\n\n**مشاريع سابقة مشابهة وجدت في الذاكرة:**\n"
        for i, p in enumerate(similar_plans, 1):
            similar_context += f"{i}. {p.get('project_summary', '')[:150]}...\n"
            tasks = p.get('generated_tasks', [])[:3]
            for t in tasks:
                similar_context += f"   - {t.get('title', '')}\n"

    prompt = f"""
أنت خبير منتجات تقني (Technical Product Manager) في منصة "مهنة" للعمل الحر.
العميل التالي يريد بناء مشروع برمجي:
- الاسم: {interview_data["name"]}
- الفكرة: {interview_data["idea"]}
- الميزانية: {interview_data["budget"]}
- الجدول الزمني: {interview_data["timeline"]}
- التوجيه التقني: {interview_data["tech_pref"]}
{similar_context}

**مطلوب**: أخرج خطة عمل على شكل JSON فقط، بدون أي نص إضافي، وفق الهيكل التالي:
{{
  "client_name": "اسم العميل",
  "project_summary": "ملخص المشروع (جملة أو جملتين)",
  "suggested_tech_stack": ["تقنية1", "تقنية2", "تقنية3"],
  "estimated_budget_range": "نطاق الميزانية",
  "generated_tasks": [
    {{ "title": "المهمة", "description": "الوصف", "estimated_days": 2, "priority": "High" }}
  ]
}}
تأكد من أن الأولوية هي: High أو Medium أو Low.
"""
    response = model.generate_content(prompt)
    raw = response.text
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        match = re.search(r"{.*}", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError("لم نتمكن من استخراج JSON.")

# ============================================================
# دوال مساعدة أخرى (Telegram, Supabase)
# ============================================================
def send_telegram_alert(bot_token: str, chat_id: str, project_plan: dict) -> bool:
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        message = (
            f"🚀 *مشروع جديد في وكيل مهنة!*\n\n"
            f"👤 *العميل:* {project_plan['client_name']}\n"
            f"💰 *الميزانية:* {project_plan['estimated_budget_range']}\n"
            f"🛠️ *التقنيات:* {', '.join(project_plan['suggested_tech_stack'][:3])}...\n"
            f"📋 *عدد المهام:* {len(project_plan['generated_tasks'])}\n\n"
            f"✅ *تم التوليد بنجاح بواسطة Gemini 2.5 Flash*"
        )
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        response = requests.post(url, data=payload, timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def save_to_supabase(url: str, key: str, project_data: dict) -> bool:
    try:
        from supabase import create_client, Client
        supabase: Client = create_client(url, key)
        project_record = {
            "client_name": project_data["client_name"],
            "summary": project_data["project_summary"],
            "tech_stack": project_data["suggested_tech_stack"],
            "budget_range": project_data["estimated_budget_range"],
            "status": "pending_approval"
        }
        response = supabase.table("projects").insert(project_record).execute()
        if not response.data:
            return False
        project_id = response.data[0]["id"]
        tasks_to_insert = []
        for task in project_data["generated_tasks"]:
            tasks_to_insert.append({
                "project_id": project_id,
                "title": task["title"],
                "description": task["description"],
                "estimated_days": task["estimated_days"],
                "priority": task["priority"],
                "status": "open"
            })
        supabase.table("tasks").insert(tasks_to_insert).execute()
        return True
    except Exception:
        return False

# ============================================================
# الواجهة الرسومية الرئيسية (UI)
# ============================================================
st.set_page_config(
    page_title="وكيل مهنة - مخطط المشاريع الذكي",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        .main-header { text-align: center; padding: 1.5rem 0; }
        .main-header h1 { color: #1E3A8A; font-size: 2.8rem; font-weight: 800; }
        .main-header h1 span { color: #F5A623; }
        .main-header p { color: #4B5563; font-size: 1.2rem; margin-top: -10px; }
        .stButton button { width: 100%; background-color: #1E3A8A; color: white; font-weight: bold; border-radius: 8px; height: 3rem; }
        .stButton button:hover { background-color: #1D4ED8; border-color: #1D4ED8; }
        .card-task { background-color: #F9FAFB; padding: 1.2rem; border-radius: 8px; border-right: 5px solid #1E3A8A; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)



# ============================================================
# دوال عرض وإدارة المشاريع المحفوظة
# ============================================================
def get_user_projects(user_email: str = "guest@example.com") -> list:
    """استرجاع جميع مشاريع المستخدم من Cloud SQL (محسّن)."""
    try:
        conn = cloudsql_utils.get_db_connection()
        if not conn:
            return []
        cursor = conn.cursor(dictionary=True)
        # محاولة البحث باستخدام البريد الإلكتروني المحدد
        cursor.execute("SELECT id FROM users WHERE email = %s", (user_email,))
        user = cursor.fetchone()
        if not user:
            # إذا لم يتم العثور على المستخدم، جرب استخدام "guest@example.com"
            cursor.execute("SELECT id FROM users WHERE email = 'guest@example.com'")
            user = cursor.fetchone()
            if not user:
                # إذا لم يوجد مستخدم ضيف، قم بإنشائه
                cursor.execute("INSERT INTO users (email, name) VALUES ('guest@example.com', 'ضيف')")
                conn.commit()
                cursor.execute("SELECT id FROM users WHERE email = 'guest@example.com'")
                user = cursor.fetchone()
        user_id = user['id']
        cursor.execute("""
            SELECT id, client_name, summary, tech_stack, budget_range, created_at 
            FROM projects 
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (user_id,))
        projects = cursor.fetchall()
        conn.close()
        return projects
    except Exception as e:
        print(f"⚠️ خطأ في استرجاع المشاريع: {e}")
        return []



# ============================================================
# منصة التحليل المتقدمة للمشاريع
# ============================================================
def get_project_details(project_id):
    """استرجاع كامل تفاصيل المشروع من قاعدة البيانات."""
    try:
        conn = cloudsql_utils.get_db_connection()
        if not conn:
            return None
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
        project = cursor.fetchone()
        if project:
            cursor.execute("SELECT * FROM tasks WHERE project_id = %s", (project_id,))
            tasks = cursor.fetchall()
            project['tasks'] = tasks
        conn.close()
        return project
    except Exception as e:
        return None

def calculate_project_metrics(project):
    """حساب مقاييس متقدمة للمشروع."""
    tasks = project.get('tasks', [])
    metrics = {
        'total_tasks': len(tasks),
        'total_days': sum(t.get('estimated_days', 0) for t in tasks),
        'high_priority': sum(1 for t in tasks if t.get('priority') == 'High'),
        'medium_priority': sum(1 for t in tasks if t.get('priority') == 'Medium'),
        'low_priority': sum(1 for t in tasks if t.get('priority') == 'Low'),
        'estimated_cost': 0,
        'risk_score': 0,
        'confidence_score': 0
    }
    # تقدير التكلفة بناءً على الأيام والأولويات
    if metrics['total_days'] > 0:
        # فرضية: متوسط تكلفة اليوم = 150 دولار للمطور
        metrics['estimated_cost'] = metrics['total_days'] * 150
        # درجة المخاطرة: نسبة المهام عالية الأولوية + نسبة المهام الطويلة (>5 أيام)
        high_ratio = metrics['high_priority'] / metrics['total_tasks'] if metrics['total_tasks'] > 0 else 0
        long_tasks = sum(1 for t in tasks if t.get('estimated_days', 0) > 5)
        long_ratio = long_tasks / metrics['total_tasks'] if metrics['total_tasks'] > 0 else 0
        metrics['risk_score'] = min(100, int((high_ratio * 0.6 + long_ratio * 0.4) * 100))
        # درجة الثقة: كلما زادت المهام وزادت التفاصيل، زادت الثقة
        avg_desc_len = sum(len(t.get('description', '')) for t in tasks) / metrics['total_tasks'] if metrics['total_tasks'] > 0 else 0
        metrics['confidence_score'] = min(100, int((min(metrics['total_tasks'] / 10, 1) * 0.5 + min(avg_desc_len / 100, 1) * 0.5) * 100))
    return metrics

def render_advanced_analytics(projects):
    """عرض تحليلات متقدمة مع رسوم بيانية وجداول تفاعلية."""
    if not projects:
        st.info("ℹ️ لا توجد مشاريع لعرضها.")
        return
    
    # تحويل المشاريع إلى DataFrame
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    
    data = []
    for p in projects:
        metrics = calculate_project_metrics(p)
        data.append({
            'id': p['id'],
            'العميل': p['client_name'],
            'الملخص': p['summary'][:60] + '...',
            'الميزانية': p['budget_range'],
            'عدد المهام': metrics['total_tasks'],
            'إجمالي الأيام': metrics['total_days'],
            'تكلفة تقديرية ($)': metrics['estimated_cost'],
            'درجة المخاطرة': metrics['risk_score'],
            'درجة الثقة': metrics['confidence_score'],
            'تاريخ الإنشاء': p['created_at']
        })
    
    df = pd.DataFrame(data)
    
    # ===== 1. إحصائيات سريعة (بطاقات) =====
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📋 إجمالي المشاريع", len(df))
    with col2:
        st.metric("💰 متوسط التكلفة التقديرية", f"${df['تكلفة تقديرية ($)'].mean():,.0f}")
    with col3:
        st.metric("📌 متوسط عدد المهام", f"{df['عدد المهام'].mean():.1f}")
    with col4:
        st.metric("⚠️ متوسط درجة المخاطرة", f"{df['درجة المخاطرة'].mean():.0f}%")
    
    st.divider()
    
    # ===== 2. رسوم بيانية تفاعلية =====
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # مخطط توزيع المهام حسب الأولوية (لكل مشروع)
        st.markdown("#### 🎯 توزيع الأولويات")
        priority_data = []
        for p in projects:
            tasks = p.get('tasks', [])
            high = sum(1 for t in tasks if t.get('priority') == 'High')
            medium = sum(1 for t in tasks if t.get('priority') == 'Medium')
            low = sum(1 for t in tasks if t.get('priority') == 'Low')
            priority_data.append({'المشروع': p['client_name'], 'عالية': high, 'متوسطة': medium, 'منخفضة': low})
        if priority_data:
            df_priority = pd.DataFrame(priority_data)
            fig1 = px.bar(df_priority, x='المشروع', y=['عالية', 'متوسطة', 'منخفضة'], 
                          title="توزيع الأولويات", barmode='group', color_discrete_sequence=['#ff4b4b', '#ffa500', '#2ecc71'])
            st.plotly_chart(fig1, use_container_width=True)
    
    with col_chart2:
        # مخطط التكلفة التقديرية مقابل المخاطرة
        st.markdown("#### ⚖️ التكلفة مقابل المخاطرة")
        fig2 = px.scatter(df, x='تكلفة تقديرية ($)', y='درجة المخاطرة', 
                          size='عدد المهام', color='العميل',
                          title="التكلفة مقابل المخاطرة",
                          labels={'تكلفة تقديرية ($)': 'التكلفة التقديرية ($)', 'درجة المخاطرة': 'نسبة المخاطرة %'})
        st.plotly_chart(fig2, use_container_width=True)
    
    col_chart3, col_chart4 = st.columns(2)
    
    with col_chart3:
        # مخطط دائري لمتوسط توزيع المهام
        st.markdown("#### 🧩 متوسط توزيع الأولويات")
        avg_high = df_priority['عالية'].mean() if 'df_priority' in locals() else 0
        avg_medium = df_priority['متوسطة'].mean() if 'df_priority' in locals() else 0
        avg_low = df_priority['منخفضة'].mean() if 'df_priority' in locals() else 0
        fig3 = go.Figure(data=[go.Pie(labels=['عالية', 'متوسطة', 'منخفضة'], 
                                      values=[avg_high, avg_medium, avg_low],
                                      marker=dict(colors=['#ff4b4b', '#ffa500', '#2ecc71']))])
        fig3.update_layout(title="متوسط توزيع الأولويات")
        st.plotly_chart(fig3, use_container_width=True)
    
    with col_chart4:
        # مخطط زمني (خط) لتطور عدد المشاريع
        st.markdown("#### 📈 تطور المشاريع")
        df['تاريخ الإنشاء'] = pd.to_datetime(df['تاريخ الإنشاء'])
        df_sorted = df.sort_values('تاريخ الإنشاء')
        fig4 = px.line(df_sorted, x='تاريخ الإنشاء', y='عدد المهام', 
                       title="عدد المهام حسب تاريخ الإنشاء",
                       markers=True, labels={'عدد المهام': 'عدد المهام', 'تاريخ الإنشاء': 'التاريخ'})
        st.plotly_chart(fig4, use_container_width=True)
    
    st.divider()
    
    # ===== 3. جداول تفاعلية قابلة للفرز =====
    st.markdown("### 📊 جدول تحليلات المشاريع")
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # ===== 4. مقارنة بين مشروعين =====
    st.markdown("### 🔍 مقارنة بين مشروعين")
    if len(df) >= 2:
        col_comp1, col_comp2 = st.columns(2)
        with col_comp1:
            proj1_name = st.selectbox("اختر المشروع الأول", df['العميل'].tolist(), key="comp1")
        with col_comp2:
            proj2_name = st.selectbox("اختر المشروع الثاني", df['العميل'].tolist(), key="comp2")
        
        if proj1_name and proj2_name and proj1_name != proj2_name:
            p1 = df[df['العميل'] == proj1_name].iloc[0]
            p2 = df[df['العميل'] == proj2_name].iloc[0]
            comp_df = pd.DataFrame({
                'المعيار': ['عدد المهام', 'إجمالي الأيام', 'التكلفة التقديرية ($)', 'درجة المخاطرة', 'درجة الثقة'],
                proj1_name: [p1['عدد المهام'], p1['إجمالي الأيام'], p1['تكلفة تقديرية ($)'], p1['درجة المخاطرة'], p1['درجة الثقة']],
                proj2_name: [p2['عدد المهام'], p2['إجمالي الأيام'], p2['تكلفة تقديرية ($)'], p2['درجة المخاطرة'], p2['درجة الثقة']]
            })
            st.dataframe(comp_df, use_container_width=True, hide_index=True)
    
    # ===== 5. نظام تقييم تلقائي للخطط =====
    st.markdown("### ⭐ نظام التقييم الذكي للخطط")
    selected_project = st.selectbox("اختر مشروعاً لتقييمه", df['العميل'].tolist(), key="eval_project")
    if selected_project:
        project_row = df[df['العميل'] == selected_project].iloc[0]
        score = 0
        # معايير التقييم
        if project_row['عدد المهام'] >= 5:
            score += 20
        elif project_row['عدد المهام'] >= 3:
            score += 10
        if project_row['إجمالي الأيام'] >= 10:
            score += 20
        elif project_row['إجمالي الأيام'] >= 5:
            score += 10
        if project_row['درجة المخاطرة'] < 30:
            score += 30
        elif project_row['درجة المخاطرة'] < 60:
            score += 15
        if project_row['درجة الثقة'] > 70:
            score += 30
        elif project_row['درجة الثقة'] > 50:
            score += 15
        st.progress(score / 100)
        st.metric("درجة الجودة", f"{score}/100")
        if score >= 80:
            st.success("✅ خطة ممتازة، جاهزة للتنفيذ!")
        elif score >= 60:
            st.info("📌 خطة جيدة، يمكن تحسينها.")
        else:
            st.warning("⚠️ خطة تحتاج إلى مراجعة وتفاصيل إضافية.")

def get_user_projects(user_email: str = "guest@example.com") -> list:
    """استرجاع جميع مشاريع المستخدم من Cloud SQL (محسّن)."""
    try:
        conn = cloudsql_utils.get_db_connection()
        if not conn:
            return []
        cursor = conn.cursor(dictionary=True)
        # محاولة البحث باستخدام البريد الإلكتروني المحدد
        cursor.execute("SELECT id FROM users WHERE email = %s", (user_email,))
        user = cursor.fetchone()
        if not user:
            # إذا لم يتم العثور على المستخدم، جرب استخدام "guest@example.com"
            cursor.execute("SELECT id FROM users WHERE email = 'guest@example.com'")
            user = cursor.fetchone()
            if not user:
                # إذا لم يوجد مستخدم ضيف، قم بإنشائه
                cursor.execute("INSERT INTO users (email, name) VALUES ('guest@example.com', 'ضيف')")
                conn.commit()
                cursor.execute("SELECT id FROM users WHERE email = 'guest@example.com'")
                user = cursor.fetchone()
        user_id = user['id']
        cursor.execute("""
            SELECT id, client_name, summary, tech_stack, budget_range, created_at 
            FROM projects 
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (user_id,))
        projects = cursor.fetchall()
        conn.close()
        return projects
    except Exception as e:
        print(f"⚠️ خطأ في استرجاع المشاريع: {e}")
        return []

def display_project_dashboard():
    st.subheader("📊 لوحة تحكم مشاريعك")
    
    # استخدام بريد إلكتروني ثابت للضيف
    user_email = "guest@example.com"
    projects = get_user_projects(user_email)
    
    # رسالة تصحيح مؤقتة (يمكن إزالتها لاحقاً)
    st.caption(f"🔍 عدد المشاريع المسترجعة: {len(projects)}")
    """عرض لوحة تحكم المشاريع المحفوظة."""
    st.subheader("📊 لوحة تحكم مشاريعك")
    
    user_email = st.session_state.get("user_email", "guest@example.com")
    projects = get_user_projects(user_email)
    
    if not projects:
        st.info("ℹ️ لم تقم بإنشاء أي مشاريع بعد. استخدم وكيل مهنة لإنشاء خطتك الأولى!")
        return
    
    # إحصائيات سريعة
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📋 عدد المشاريع", len(projects))
    with col2:
        # حساب متوسط الميزانية
        avg_budget = 0
        for p in projects:
            try:
                budget_range = p.get('budget_range', '0-0').split('-')
                if len(budget_range) == 2:
                    avg_budget += (int(budget_range[0].strip()) + int(budget_range[1].strip())) / 2
            except:
                pass
        avg_budget = avg_budget / len(projects) if projects else 0
        st.metric("💰 متوسط الميزانية", f"${avg_budget:,.0f}")
    with col3:
        # حساب عدد المهام الكلي
        total_tasks = 0
        for p in projects:
            try:
                conn = cloudsql_utils.get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM tasks WHERE project_id = %s", (p['id'],))
                    total_tasks += cursor.fetchone()[0]
                    conn.close()
            except:
                pass
        st.metric("📌 إجمالي المهام", total_tasks)
    
    st.divider()
    
    # عرض المشاريع في جدول
    st.markdown("### 📋 قائمة مشاريعك")
    
    # جدول المشاريع
    table_data = []
    for p in projects:
        table_data.append({
            "🆔": p['id'],
            "👤 العميل": p['client_name'],
            "📝 الملخص": p['summary'][:80] + "..." if p['summary'] and len(p['summary']) > 80 else p['summary'],
            "💰 الميزانية": p['budget_range'],
            "📅 التاريخ": p['created_at'].strftime("%Y-%m-%d") if p['created_at'] else "غير محدد"
        })
    
    st.dataframe(table_data, use_container_width=True, hide_index=True)
    
    # اختيار مشروع لعرض تفاصيله
    st.markdown("### 🔍 عرض تفاصيل مشروع")
    project_ids = [f"{p['id']} - {p['client_name']}" for p in projects]
    selected = st.selectbox("اختر مشروعاً لعرض تفاصيله", project_ids, key="project_selector")
    
    if selected:
        selected_id = int(selected.split(' - ')[0])
        # عرض تفاصيل المشروع المختار
        with st.expander(f"📄 تفاصيل مشروع {selected}", expanded=True):
            try:
                conn = cloudsql_utils.get_db_connection()
                if conn:
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("SELECT * FROM projects WHERE id = %s", (selected_id,))
                    project = cursor.fetchone()
                    if project:
                        st.markdown(f"**👤 العميل:** {project['client_name']}")
                        st.markdown(f"**📝 الملخص:** {project['summary']}")
                        st.markdown(f"**🛠️ التقنيات:** {project['tech_stack']}")
                        st.markdown(f"**💰 الميزانية:** {project['budget_range']}")
                        st.markdown(f"**📅 تاريخ الإنشاء:** {project['created_at']}")
                        
                        # عرض المهام
                        cursor.execute("SELECT title, description, estimated_days, priority FROM tasks WHERE project_id = %s", (selected_id,))
                        tasks = cursor.fetchall()
                        if tasks:
                            st.markdown("#### 📋 المهام")
                            for task in tasks:
                                emoji = "🔴" if task['priority'] == 'High' else "🟡" if task['priority'] == 'Medium' else "🟢"
                                st.markdown(f"- {emoji} **{task['title']}** ({task['priority']}) - {task['estimated_days']} أيام")
                                st.caption(f"  {task['description']}")
                        else:
                            st.info("لا توجد مهام لهذا المشروع")
                    conn.close()
            except Exception as e:
                st.error(f"⚠️ فشل تحميل تفاصيل المشروع: {e}")

def main():
    # الهيدر
    st.markdown('<div class="main-header"><h1>🧠 وكيل مهنة <span>PRO</span></h1></div>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; margin-top: -20px;">حوّل فكرتك إلى خطة هندسية متكاملة في 3 ثوانٍ</p>', unsafe_allow_html=True)
    st.info("💡 **توفر عليك 40 ساعة عمل و 500$ من استشارة مدير مشروع**", icon="💎")
    st.divider()
    
    # إضافة تبويبين: "إنشاء خطة" و "لوحة التحكم"
    tab1, tab2 = st.tabs(["🚀 إنشاء خطة جديدة", "📊 لوحة تحكم مشاريعك"])
    
    with tab2:
        display_project_dashboard()
        st.divider()
    
    with tab1:

        # الشريط الجانبي
        with st.sidebar:
            st.header("⚙️ إعدادات الاتصال")
            try:
                key_preview = config.LEMONSQUEEZY_API_KEY[:10] if config.LEMONSQUEEZY_API_KEY else "غير موجود"
                st.caption(f"🔑 Lemon Squeezy Key: {key_preview}...")
            except:
                st.caption("🔑 Lemon Squeezy Key: غير محمّل")

            gemini_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
            if gemini_key:
                st.success("✅ Gemini متصل (جاهز للتوليد)")
            else:
                st.error("❌ Gemini غير متصل (يرجى إضافة المفتاح في st.secrets)")

            supabase_url = st.text_input("🔗 Supabase URL (اختياري)", value=os.getenv("SUPABASE_URL", ""))
            supabase_key = st.text_input("⚡ Supabase Service Key (اختياري)", value=os.getenv("SUPABASE_SERVICE_KEY", ""), type="password")

            st.divider()
            st.header("🤖 إشعارات Telegram (الميزة الذهبية)")
            st.caption("احصل على تنبيه فوري على هاتفك عند إنشاء أي مشروع جديد!")
            telegram_token = st.text_input("🔑 Bot Token", type="password", placeholder="مثال: 123456:ABC-DEF")
            telegram_chat_id = st.text_input("💬 Chat ID", placeholder="مثال: 987654321")
            if telegram_token and telegram_chat_id:
                st.success("✅ سيتم إرسال الإشعارات إلى هاتفك فوراً!")

            st.divider()
            st.subheader("📊 رصيدك المجاني")
            init_usage()
            if st.session_state.is_premium:
                st.success("✨ مشترك مميز (غير محدود)")
            else:
                st.info(f"⚡ متبقي {st.session_state.free_uses} تحويلات مجانية")
                if st.session_state.free_uses <= 0:
                    st.warning("🚫 انتهت استخداماتك! اشترك للمتابعة.")

            # نموذج الدفع عبر Lemon Squeezy
            if st.button("💎 اشترك الآن (9.99$ شهرياً)"):
                st.session_state.show_payment = True

            if st.session_state.get("show_payment", False):
                with st.expander("💳 إتمام الدفع", expanded=True):
                    st.markdown("**أدخل بريدك الإلكتروني لاستلام رابط الدفع**")
                    with st.form("payment_form"):
                        user_email = st.text_input("✉️ البريد الإلكتروني")
                        submitted = st.form_submit_button("🔗 إنشاء رابط الدفع")
                        if submitted:
                            if user_email:
                                try:
                                    checkout_url = create_checkout_url(user_email, "عميل")
                                    st.success("✅ تم إنشاء رابط الدفع بنجاح!")
                                    st.markdown(f"[اضغط هنا لإتمام الدفع]({checkout_url})")
                                    st.session_state.show_payment = False
                                except Exception as e:
                                    st.error(f"❌ فشل إنشاء رابط الدفع: {e}")
                            else:
                                st.warning("⚠️ يرجى إدخال بريدك الإلكتروني")

            with st.expander("💎 خطط الاشتراك"):
                st.write("**مجاني**: 5 تحويلات")
                st.write("**شهري**: 9.99$ - تحويلات غير محدودة")
                st.write("**سنوي**: 99.99$ - خصم 20%")

            st.divider()
            st.caption("🌟 يثق بنا: 5 عملاء حقيقيون في اليمن")
            st.caption("🏅 أفضل وكيل تخطيط في الشرق الأوسط")

        # نموذج إدخال المشروع
        st.markdown("### 📝 أدخل تفاصيل مشروعك")
        col_q1, col_q2 = st.columns(2)
        with col_q1:
            if st.button("📚 منصة تعليمية"):
                st.session_state.example = "education"
        with col_q2:
            if st.button("🛒 متجر إلكتروني"):
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
                client_name = st.text_input("👤 اسم العميل / الشركة", value=default_name)
            with col2:
                budget = st.text_input("💰 الميزانية المتوقعة", placeholder="مثال: 2000 - 3000 دولار", value=default_budget)
            project_idea = st.text_area("💡 صف رؤية أو فكرة مشروعك بالتفصيل", height=120, value=default_idea)
            word_count = len(project_idea.split()) if project_idea else 0
            st.caption(f"📝 {word_count} كلمة (يُفضل 50-100 كلمة)")
            col3, col4 = st.columns(2)
            with col3:
                timeline = st.text_input("📅 الجدول الزمني المستهدف", placeholder="4 أسابيع", value=default_timeline)
            with col4:
                tech_pref = st.text_input("⚙️ تفضيلات تقنية (اختياري)", value=default_tech)
            submitted = st.form_submit_button("🚀 توليد الخطة الهندسية الآن")

        # معالجة الطلب
        if submitted:
            if not gemini_key:
                st.error("❌ يرجى إدخال مفتاح Gemini API.")
                return
            if not client_name or not project_idea:
                st.error("❌ يرجى ملء اسم العميل وفكرة المشروع.")
                return
            if not can_use():
                st.error("🚫 لقد استنفذت استخداماتك المجانية. يرجى الاشتراك الشهري للمتابعة!")
                return

            interview_data = {
                "name": client_name,
                "idea": project_idea,
                "budget": budget if budget else "تحدد بعد التحليل",
                "timeline": timeline if timeline else "غير محدد",
                "tech_pref": tech_pref if tech_pref else "اعتمد أفضل الممارسات"
            }

            with st.spinner('🔄 وكيل مهنة يحلل المتطلبات...'):
                try:
                    # 1. توليد الخطة (مع RAG)
                    plan_json = generate_project_plan_safe(gemini_key, interview_data)
                    deduct_usage()

                    # 2. حفظ في Supabase (إن وجدت المفاتيح)
                    if supabase_url and supabase_key:
                        if save_to_supabase(supabase_url, supabase_key, plan_json):
                            st.success("☁️ تم حفظ الخطة في Supabase!")
                        else:
                            st.warning("⚠️ فشل الحفظ في Supabase، لكن الخطة متاحة.")

                    # 3. إرسال إشعار Telegram (إن وجدت المفاتيح)
                    if telegram_token and telegram_chat_id:
                        with st.spinner('📱 جاري إرسال الإشعار إلى Telegram...'):
                            alert_sent = send_telegram_alert(telegram_token, telegram_chat_id, plan_json)
                            if alert_sent:
                                st.toast('🚀 تم إرسال إشعار Telegram إلى هاتفك!', icon='📱')
                            else:
                                st.toast('⚠️ فشل إرسال الإشعار، تحقق من المفاتيح.', icon='⚠️')

                    # 4. HITL: عرض المهام للتعديل قبل الاعتماد
                    tasks = plan_json.get("generated_tasks", [])
                    if tasks:
                        st.info("🔄 يمكنك الآن مراجعة المهام وتعديلها قبل حفظ الخطة.")
                        edited_tasks = display_tasks_with_hitl(tasks)
                        if edited_tasks:
                            plan_json['generated_tasks'] = edited_tasks
                            st.success("✅ تم اعتماد الخطة المعدلة!")
                        else:
                            st.warning("⏳ لم يتم اعتماد الخطة بعد (يمكنك متابعة التعديل).")

                    # 5. عرض النتيجة بشكل احترافي
                    st.success("✅ تم توليد الخطة بنجاح!")
                    st.divider()

                    if plan_json.get("project_summary"):
                        st.markdown("### 📌 ملخص المشروع")
                        st.info(plan_json["project_summary"])
                    else:
                        st.warning("⚠️ لم يتم العثور على ملخص للمشروع")

                    tech_stack = plan_json.get("suggested_tech_stack", [])
                    if tech_stack:
                        st.markdown("### 🛠️ التقنيات المقترحة")
                        cols = st.columns(min(len(tech_stack), 4))
                        for i, tech in enumerate(tech_stack):
                            cols[i % len(cols)].markdown(f"- {tech}")
                    else:
                        st.warning("⚠️ لم يتم اقتراح أي تقنيات")

                    if tasks:
                        st.markdown("### 📋 المهام المقترحة")
                        for idx, task in enumerate(tasks, 1):
                            title = task.get("title", f"المهمة {idx}")
                            description = task.get("description", "لا يوجد وصف لهذه المهمة")
                            days = task.get("estimated_days", "غير محدد")
                            priority = task.get("priority", "Medium")
                            emoji = "🔴" if priority == "High" else "🟡" if priority == "Medium" else "🟢"
                            with st.container(border=True):
                                col1, col2 = st.columns([4, 1])
                                with col1:
                                    st.markdown(f"**{idx}. {title}**")
                                with col2:
                                    st.markdown(f"{emoji} {priority}")
                                st.caption(f"📅 المدة: {days} أيام")
                                st.write(description)
                    else:
                        st.warning("⚠️ لم يتم توليد أي مهام. حاول إعادة صياغة فكرة المشروع.")

                    with st.expander("📄 عرض هيكل JSON الخام (للتحميل والفحص)"):
                        st.json(plan_json)

                    # أزرار التحميل
                    st.divider()
                    st.markdown("### 💾 تحميل الخطة")
                    session_id = str(uuid.uuid4())[:8]
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    base_filename = f"project_plan_{timestamp}_{session_id}"

                    json_str = json.dumps(plan_json, indent=2, ensure_ascii=False)
                    st.download_button(
                        label="📥 تحميل خطة العمل (JSON)",
                        data=json_str,
                        file_name=f"{base_filename}.json",
                        mime="application/json",
                        key="download_json_final"
                    )

                    txt_content = f"=== خطة مشروع {plan_json.get('client_name', 'عميل')} ===\n\n"
                    txt_content += f"الملخص: {plan_json.get('project_summary', 'لا يوجد ملخص')}\n\n"
                    txt_content += "=== المهام ===\n"
                    for i, task in enumerate(tasks, 1):
                        txt_content += f"{i}. {task.get('title', 'بدون عنوان')} ({task.get('priority', 'Medium')}) - {task.get('estimated_days', '?')} أيام\n"
                        txt_content += f"   {task.get('description', 'لا يوجد وصف')}\n\n"

                    st.download_button(
                        label="📥 تحميل خطة العمل (نصي)",
                        data=txt_content,
                        file_name=f"{base_filename}.txt",
                        mime="text/plain",
                        key="download_txt_final"
                    )

                    st.markdown("### ⭐ تقييمك للخطة")
                    rating = st.select_slider("ما مدى دقة الخطة؟", options=[1,2,3,4,5], value=4)
                    if rating < 3:
                        st.warning("سنحسن الخطة بناءً على ملاحظاتك، شكراً لك!")
                    else:
                        st.success("شكراً لتقييمك الإيجابي!")

                    st.balloons()

                except Exception as e:
                    st.error(f"❌ خطأ: {e}")

if __name__ == "__main__":
    main()
