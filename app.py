#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
© 2026 PHOENIX & WAKEEL MEHNA PRO ENTERPRISE v15.0 - HYBRID ULTIMATE
الواجهة الرئيسية ومسار تشغيل المنصة الهندسية المتكاملة
الربط المباشر مع محركات التكعيب، العقود الذكية ZKP، التوأم الرقمي، والمخططات
===============================================================================
"""

import os
import json
import time
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from PIL import Image

# -----------------------------------------------------------------------------
# 1. الاستيراد من الوحدات والمحركات المتقدمة (Modules Import)
# -----------------------------------------------------------------------------
from telephony import TelephonyEngine, render_telephony_widget
from db import HybridDatabaseEngine, SUPER_ADMIN_EMAILS
from auth import render_auth_page
from ai.facade import AIFacade
from utils import (
    SecurityEngine, NotificationEngine, generate_excel_download,
    generate_pdf_plan, build_detailed_plan_text, create_half_doughnut_gauge,
    PAYMENT_LINK_MONTHLY, PAYMENT_LINK_YEARLY
)

# استيراد محركات المحاكاة والهندسة المتطورة من النظام
try:
    from engine_core import (
        EngineeringTakeoffEngine,
        ZeroKnowledgeEscrow,
        GenerativeArchitecturalEngine,
        LiveTwinEngine,
        get_geo_contractors_enterprise
    )
    ENGINES_AVAILABLE = True
except ImportError:
    ENGINES_AVAILABLE = False

APP_TITLE = "PHOENIX & WAKEEL MEHNA PRO ENTERPRISE v15.0"

# -----------------------------------------------------------------------------
# 2. إدارة الجلسة والحالة (Session State Initialization)
# -----------------------------------------------------------------------------
def init_session():
    if 'lang' not in st.session_state: st.session_state.lang = 'ar'
    if 'theme' not in st.session_state: st.session_state.theme = 'dark'
    if 'is_authenticated' not in st.session_state: st.session_state.is_authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = {
            'email': '', 'username': 'زائر', 'credits': 5, 
            'role': 'Free Trial', 'is_subscribed': False, 'is_admin': False
        }
    if 'current_plan' not in st.session_state: st.session_state.current_plan = None
    if 'plan_signature' not in st.session_state: st.session_state.plan_signature = None
    if 'notify_whatsapp' not in st.session_state: st.session_state.notify_whatsapp = "+967700000000"
    if 'notify_telegram' not in st.session_state: st.session_state.notify_telegram = "@Ayad_Developer"
    if 'form_scope' not in st.session_state: st.session_state.form_scope = ""
    if 'form_pname' not in st.session_state: st.session_state.form_pname = "برج سكني تجاري متكامل"
    if 'form_domain' not in st.session_state: st.session_state.form_domain = "الهندسة والإنشاءات (ConTech)"
    if 'form_budget' not in st.session_state: st.session_state.form_budget = 45000
    if 'form_days' not in st.session_state: st.session_state.form_days = 120
    if 'payment_notifications' not in st.session_state: st.session_state.payment_notifications = []
    if 'engineering_analysis_result' not in st.session_state: st.session_state.engineering_analysis_result = None
    if 'zkp_proofs' not in st.session_state: st.session_state.zkp_proofs = []

# -----------------------------------------------------------------------------
# 3. النصوص والقواميس المزدوجة (Translations)
# -----------------------------------------------------------------------------
T = {
    'ar': {
        'title': "🚀 PHOENIX & WAKEEL MEHNA PRO Enterprise v15.0",
        'subtitle': "منصة ConTech & Enterprise الهندسية: قراءة المخططات، حاسبة التكعيب، العقود الذكية ZKP والتوأم الرقمي.",
        'lang_select': "🌐 لغة الواجهة (Language):",
        'theme_select': "🎨 مظهر التطبيق (Theme):",
        'dark': "🌙 الداكن (Dark)", 'light': "☀️ الفاتح (Light)",
        'user': "👤 المستخدم:", 'credits': "💳 الرصيد الحالي:", 'points': "نقاط مجانية",
        'renew_title': "🛒 ترقية الاشتراك", 'renew_btn': "⚡ اشترك الآن وترقية الحساب",
        'logout_btn': "🚪 تسجيل الخروج", 'notify_settings': "📲 إعدادات الإشعارات الفورية",
        'wa_phone': "رقم الواتساب", 'tg_handle': "معرف التليجرام",
        'tab1': "🏗️ الخطة التشغيلية والكوادر", 
        'tab_eng': "📐 قراءة المخططات والتكعيب التلقائي",
        'tab_arch': "🏛️ المخطط المعماري التوليدي 2D",
        'tab_twin': "🌐 المحاكاة الميدانية والتوأم الرقمي",
        'tab_escrow': "🔐 الضمان المشفر ZKP Escrow",
        'tab_telephony': "📞 الاتصالات والمرافق",
        'tab2': "📊 التحليلات الهندسية 6D",
        'tab3': "✏️ محرر المهام والتقرير", 
        'tab4': "🔄 التغذية الراجعة والتسعير",
        'tab5': "💳 الحساب والاشتراكات", 
        'tab6': "🗄️ الأرشيف والتكامل Cloud SQL",
        'tab_admin': "👑 لوحة الإدارة العليا (CEO Panel)",
        'quick_templates': "⚡ قوالب هندسية جاهزة للبدء السريع",
        'building': "🏢 برج سكني تجاري", 'villa': "🏡 villa حديثة (Smart Villa)", 'bridge': "🌉 منشأة خرسانية/جسر",
        'p_name': "اسم المشروع الهندسي", 'tech_domain': "المجال والتخصص", 'budget': "الميزانية التقديرية ($)",
        'tech_stack': "المواصفات والتقنيات", 'target_days': "المدة الزمنية (يوم)", 'risk_level': "درجة المخاطرة الإنشائية",
        'scope': "نطاق العمل والتفاصيل الإنشائية",
        'generate_btn': "🚀 توليد الخطة، حساب الكوادر والتوقيع المشفر (1 نقطة)",
        'export_excel': "📥 تحميل جدول الكميات (Excel)", 'export_pdf': "📄 تحميل العقد والتكعيب (PDF)",
        'detailed_plan': "📜 التقرير التنفيذي الشامل", 'save_re_sign': "💾 حفظ التعديلات وإعادة التوقيع الرقمي",
        'digital_sig': "🔑 التوقيع المشفر (HMAC-SHA512):",
        'sig_valid': "✔ توقيع موثوق وسليم", 'sig_invalid': "❌ تم التلاعب بالبيانات",
        'send_wa': "📱 إرسال عبر WhatsApp", 'send_tg': "📲 إشعار Telegram Bot",
    },
    'en': {
        'title': "🚀 PHOENIX & WAKEEL MEHNA PRO Enterprise v15.0",
        'subtitle': "ConTech & Enterprise Engine: AI Takeoff, ZKP Escrow, Generative Blueprints & Live Digital Twin.",
        'lang_select': "🌐 Interface Language:",
        'theme_select': "🎨 Application Theme:",
        'dark': "🌙 Dark", 'light': "☀️ Light",
        'user': "👤 User:", 'credits': "💳 Current Balance:", 'points': "points",
        'renew_title': "🛒 Upgrade Plan", 'renew_btn': "⚡ Upgrade & Subscribe Now",
        'logout_btn': "🚪 Log Out", 'notify_settings': "📲 Instant Notification Settings",
        'wa_phone': "WhatsApp Phone", 'tg_handle': "Telegram Handle",
        'tab1': "🏗️ Operational Plan & Payroll", 
        'tab_eng': "📐 Blueprint Takeoff Engine",
        'tab_arch': "🏛️ Generative 2D Blueprint",
        'tab_twin': "🌐 Live Field Twin Simulation",
        'tab_escrow': "🔐 ZKP Smart Escrow Agent",
        'tab_telephony': "📞 Telephony & Communications",
        'tab2': "📊 Advanced 6D Analytics",
        'tab3': "✏️ Task Editor & Text Report", 
        'tab4': "🔄 Dynamic Pricing & Feedback",
        'tab5': "💳 Account & Subscriptions", 
        'tab6': "🗄️ Cloud SQL Archive",
        'tab_admin': "👑 CEO & Admin Panel",
        'quick_templates': "⚡ Quick Start Engineering Templates",
        'building': "🏢 Commercial Tower", 'villa': "🏡 Smart Luxury Villa", 'bridge': "🌉 Structural Bridge/Infrastructure",
        'p_name': "Project Name", 'tech_domain': "Technical Domain", 'budget': "Estimated Budget ($)",
        'tech_stack': "Tech Specifications", 'target_days': "Target Timeline (Days)", 'risk_level': "Risk Level",
        'scope': "Scope of Work",
        'generate_btn': "🚀 Generate Plan, Payroll & Sign (1 Credit)",
        'export_excel': "📥 Download BOQ (Excel)", 'export_pdf': "📄 Download Contract (PDF)",
        'detailed_plan': "📜 Extended Executive Report", 'save_re_sign': "💾 Save Edits & Re-Sign Digitally",
        'digital_sig': "🔑 Encrypted HMAC Signature:",
        'sig_valid': "✔ Valid Signature", 'sig_invalid': "❌ Invalid Signature",
        'send_wa': "📱 Send via WhatsApp", 'send_tg': "📲 Notify Telegram Bot",
    }
}

def update_language():
    selected = st.session_state.lang_radio
    st.session_state.lang = 'ar' if "العربية" in selected else 'en'

def update_theme():
    selected = st.session_state.theme_radio
    st.session_state.theme = 'dark' if ("الداكن" in selected or "Dark" in selected) else 'light'

def apply_template(scope, domain, budget, days, pname):
    st.session_state.form_scope = scope
    st.session_state.form_domain = domain
    st.session_state.form_budget = budget
    st.session_state.form_days = days
    st.session_state.form_pname = pname

def generate_fallback_architecture(req):
    """توليد هيكل افتراضي احترافي للمشاريع الهندسية"""
    b = req.get("budget", 45000)
    d = req.get("target_days", 120)
    pname = req.get("project_name", "مشروع إنشائي جديد")
    domain = req.get("domain", "الهندسة والإنشاءات")
    
    tasks = [
        {"id": 1, "task": "الدراسات المساحية واختبارات التربة الجيوتقنية", "duration_days": int(d*0.10), "cost": b*0.08, "owner": "مهندس التربة والمساحة"},
        {"id": 2, "task": "التصميم المعماري والإنشائي واعتمد المخططات", "duration_days": int(d*0.15), "cost": b*0.12, "owner": "المهندس المصمم"},
        {"id": 3, "task": "أعمال الحفريات والأساسات والخرسانة المسلحة (الركائز)", "duration_days": int(d*0.30), "cost": b*0.35, "owner": "مقاول الخرسانات"},
        {"id": 4, "task": "الهيكل العظمي والمباني والمرافق الكهروميكانيكية (MEP)", "duration_days": int(d*0.30), "cost": b*0.30, "owner": "مهندس الموقع والكهرباء"},
        {"id": 5, "task": "التشطيبات النهائية والفحص وتسليم المفتاح", "duration_days": int(d*0.15), "cost": b*0.15, "owner": "استشاري الجودة"}
    ]
    
    plan_data = {
        "project_name": pname,
        "domain": domain,
        "budget": b,
        "target_days": d,
        "tech_stack": req.get("tech_stack", "خرسانة مسلحة C30/35, حديد تسليح High-Yield, نظامات MEP ذكية"),
        "risk": req.get("risk", "متوسط"),
        "scope": req.get("scope", "نطاق عمل هندسي متكامل للمشروع الإنشائي"),
        "tasks": tasks
    }
    plan_data["signature"] = SecurityEngine.generate_signature(plan_data)
    return plan_data

# -----------------------------------------------------------------------------
# 4. الدالة الرئيسية للمنصة (Main Streamlit Entrypoint)
# -----------------------------------------------------------------------------
def main():
    st.set_page_config(page_title=APP_TITLE, page_icon="🏗️", layout="wide")
    init_session()

    if not st.session_state.is_authenticated:
        render_auth_page()
        return

    fresh_u = HybridDatabaseEngine.get_user(st.session_state.user['email'])
    if fresh_u:
        st.session_state.user['credits'] = fresh_u['credits']
        st.session_state.user['role'] = fresh_u['role']
        st.session_state.user['is_subscribed'] = bool(fresh_u['is_subscribed'])
        st.session_state.user['is_admin'] = bool(fresh_u['is_admin']) or (fresh_u['email'] in SUPER_ADMIN_EMAILS)

    lang = st.session_state.lang
    txt = T[lang]

    bg_color = "#0E1117" if st.session_state.theme == 'dark' else "#F8FAFC"
    text_color = "#FFFFFF" if st.session_state.theme == 'dark' else "#0F172A"

    st.markdown(f"""
    <style>
        .stApp {{ background-color: {bg_color}; color: {text_color}; }}
        .badge-green {{ background-color: #10B981; color: white; padding: 6px 14px; border-radius: 12px; font-weight: bold; font-size: 13px; display: inline-block; }}
        .badge-purple {{ background-color: #8B5CF6; color: white; padding: 6px 14px; border-radius: 12px; font-weight: bold; font-size: 13px; display: inline-block; }}
        .badge-gold {{ background-color: #F59E0B; color: white; padding: 6px 14px; border-radius: 12px; font-weight: bold; font-size: 13px; display: inline-block; }}
        .checkout-btn {{ display: block; width: 100%; text-align: center; background: linear-gradient(135deg, #2563EB, #1D4ED8); color: white !important; padding: 12px 16px; border-radius: 10px; font-weight: bold; text-decoration: none; border: none; font-size: 14px; }}
        .checkout-btn-yearly {{ display: block; width: 100%; text-align: center; background: linear-gradient(135deg, #7C3AED, #9333EA); color: white !important; padding: 12px 16px; border-radius: 10px; font-weight: bold; text-decoration: none; border: none; font-size: 14px; }}
        .ai-payment-card {{ background: linear-gradient(135deg, #1E1B4B 0%, #312E81 100%); border: 2px solid #6366F1; border-radius: 16px; padding: 24px; color: #FFFFFF; margin-bottom: 24px; }}
        .feedback-card {{ background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%); border: 1px solid #3B82F6; border-radius: 14px; padding: 20px; color: #F8FAFC; margin-bottom: 15px; }}
        .stat-card-box {{ background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 14px; padding: 16px; text-align: center; margin-bottom: 10px; }}
        .user-feedback-item {{ background: rgba(15, 23, 42, 0.8); border-right: 4px solid #F59E0B; border-radius: 8px; padding: 14px; margin-bottom: 12px; }}
    </style>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # الشريط الجانبي (Sidebar)
    # -------------------------------------------------------------------------
    with st.sidebar:
        st.title("🏗️ WAKEEL MEHNA PRO")
        st.markdown("<span class='badge-purple'>ConTech Enterprise v15.0</span>", unsafe_allow_html=True)
        st.divider()

        st.radio(txt['lang_select'], ["العربية (Arabic)", "English"], index=0 if lang == 'ar' else 1, key='lang_radio', on_change=update_language)
        st.radio(txt['theme_select'], [txt['dark'], txt['light']], index=0 if st.session_state.theme == 'dark' else 1, key='theme_radio', on_change=update_theme)

        st.divider()
        st.markdown(f"{txt['user']} **{st.session_state.user['username']}**")

        if st.session_state.user['is_subscribed']:
            st.markdown(f"الاشتراك: <span class='badge-gold'>{st.session_state.user['role']}</span>", unsafe_allow_html=True)
            st.markdown("الرصيد: **غير محدود ♾️**")
        else:
            st.markdown(f"الحساب: <span class='badge-purple'>تجريبي</span>", unsafe_allow_html=True)
            st.markdown(f"{txt['credits']} `{st.session_state.user['credits']}` {txt['points']}")

        if st.button(txt['logout_btn'], use_container_width=True):
            st.session_state.clear()
            st.rerun()

        st.divider()
        st.markdown(f"### {txt['renew_title']}")
        all_fb = HybridDatabaseEngine.get_all_feedback()
        adapted_insights = AIFacade.analyze_feedback_and_adapt_pricing(all_fb)

        if not st.session_state.user['is_subscribed']:
            if st.button("🤖 الدفع الذكي والتفعيل السريع", type="primary", use_container_width=True):
                AIFacade.execute_auto_checkout(st.session_state.user['email'], "monthly")
                st.balloons()
                st.success("🎉 تم ترقية حسابك المباشر بنجاح!")
                time.sleep(1)
                st.rerun()

        st.markdown(f'<a href="{PAYMENT_LINK_MONTHLY}" target="_blank" class="checkout-btn">💳 {txt["renew_btn"]} (${adapted_insights["recommended_monthly"]}/m)</a>', unsafe_allow_html=True)
        st.write("")
        st.markdown(f'<a href="{PAYMENT_LINK_YEARLY}" target="_blank" class="checkout-btn-yearly">👑 الاشتراك السنوي (${adapted_insights["recommended_yearly"]}/y)</a>', unsafe_allow_html=True)

        st.divider()
        st.subheader(txt['notify_settings'])
        st.session_state.notify_whatsapp = st.text_input(txt['wa_phone'], value=st.session_state.notify_whatsapp)
        st.session_state.notify_telegram = st.text_input(txt['tg_handle'], value=st.session_state.notify_telegram)

    # -------------------------------------------------------------------------
    # الواجهة الرئيسية وتوزيع التبويبات (Tabs Architecture)
    # -------------------------------------------------------------------------
    st.title(txt['title'])
    st.caption(txt['subtitle'])

    if st.session_state.user['credits'] <= 0 and not st.session_state.user['is_subscribed']:
        st.markdown("""
        <div class="ai-payment-card">
            <h3>🤖 تنبيه وكيل التسعير التكيفي والاشتراكات</h3>
            <p>لقد استنفدت النقاط التجريبية المتاحة. يرجى الترقية لتفعيل أداة التكعيب الهندسي والعقود المشفرة ZKP دون قيود.</p>
        </div>
        """, unsafe_allow_html=True)

    is_ceo_owner = (st.session_state.user['email'] in SUPER_ADMIN_EMAILS) or st.session_state.user['is_admin']
    
    tab_labels = [
        txt['tab1'], 
        txt['tab_eng'], 
        txt['tab_arch'],
        txt['tab_twin'],
        txt['tab_escrow'],
        txt['tab_telephony'],
        txt['tab2'], 
        txt['tab3'], 
        txt['tab4'], 
        txt['tab5'], 
        txt['tab6']
    ]
    if is_ceo_owner:
        tab_labels.append(txt['tab_admin'])

    tabs = st.tabs(tab_labels)
    tab1, tab_eng, tab_arch, tab_twin, tab_escrow, tab_telephony, tab2, tab3, tab4, tab5, tab6 = tabs[:11]
    tab_admin = tabs[11] if is_ceo_owner else None

    # =========================================================================
    # TAB 1: BUILD OPERATIONAL PLAN & PAYROLL
    # =========================================================================
    with tab1:
        st.subheader(txt['quick_templates'])
        col_t1, col_t2, col_t3 = st.columns(3)
        col_t1.button(txt['building'], use_container_width=True, on_click=apply_template, args=("إنشاء برج تجاري 12 طابق شامل الخرسانة المسلحة والواجهات الزجاجية", "الهندسة والإنشاءات", 150000, 180, "برج تجاري متكامل"))
        col_t2.button(txt['villa'], use_container_width=True, on_click=apply_template, args=("بناء فيلا حديثة بنظام الذكاء الاصطناعي والطاقة الشمسية والأرقام الهندسية", "السكن الذكي", 45000, 90, "فيلا ذكية مستدامة"))
        col_t3.button(txt['bridge'], use_container_width=True, on_click=apply_template, args=("إنشاء جسر خرساني مسبق الإجهاد بطول 120 متر مع الأرصفة والحمايات الإنشائية", "البنية التحتية", 220000, 240, "مشروع جسر خرساني"))

        domain_options = ["الهندسة والإنشاءات (ConTech)", "السكن الذكي", "البنية التحتية", "التطوير العقاري", "أنظمة إدارة المشاريع SaaS"]
        domain_idx = domain_options.index(st.session_state.form_domain) if st.session_state.form_domain in domain_options else 0

        with st.form("project_form"):
            col1, col2 = st.columns(2)
            with col1:
                project_name = st.text_input(txt['p_name'], key="form_pname")
                domain = st.selectbox(txt['tech_domain'], domain_options, index=domain_idx, key="form_domain")
                budget = st.number_input(txt['budget'], min_value=1000, key="form_budget")
            with col2:
                tech_stack = st.text_input(txt['tech_stack'], value="خرسانة C30/35, حديد High-Yield, أنظمة MEP")
                target_days = st.number_input(txt['target_days'], min_value=5, key="form_days")
                risk_tolerance = st.select_slider(txt['risk_level'], options=["منخفض جداً", "متوسط", "عالي"])

            project_scope = st.text_area(txt['scope'], key="form_scope", placeholder="اكتب التفاصيل والمواصفات الإنشائية والهندسية هنا...")
            gemini_key = st.text_input("مفتاح Gemini API (اختياري للتحليل الذكي المباشر)", type="password", key="gemini_key_input")

            submit_btn = st.form_submit_button(txt['generate_btn'], use_container_width=True)

        if submit_btn:
            if st.session_state.user['credits'] < 1 and not st.session_state.user['is_subscribed']:
                st.error("❌ لقد استنفدت نقاطك المجانية! يرجى الترقية للاستمرار.")
            else:
                with st.spinner("⏳ جاري تحليل المتطلبات الإنشائية، توزيع الكوادر، وتوقيع الخطة رقمياً..."):
                    req = {
                        "project_name": project_name, "domain": domain, "budget": budget,
                        "target_days": target_days, "tech_stack": tech_stack, "scope": project_scope, "risk": risk_tolerance
                    }
                    
                    active_key = gemini_key.strip() if gemini_key and gemini_key.strip() else os.environ.get("GEMINI_API_KEY")
                    
                    try:
                        if active_key:
                            ai_facade = AIFacade(api_key=active_key)
                            plan = ai_facade.generate_architecture(req)
                        else:
                            st.info("ℹ️ تم استخدام محرك التوليد الهندسي الافتراضي المدمج.")
                            plan = generate_fallback_architecture(req)

                        HybridDatabaseEngine.save_project_plan_full(plan, st.session_state.user['email'])

                        if not st.session_state.user['is_subscribed']:
                            new_c = max(0, st.session_state.user['credits'] - 1)
                            HybridDatabaseEngine.update_credits(st.session_state.user['email'], new_c)
                            st.session_state.user['credits'] = new_c

                        st.session_state.current_plan = plan
                        st.session_state.plan_signature = plan.get("signature")
                        st.success("✅ تم توليد الخطة وحساب أجور الكوادر وتوقيع العقد رقمياً!")
                    except Exception as e:
                        st.warning(f"⚠️ تعذر الاتصال بالمحرك الخارجي ({str(e)}). تم تفعيل المحرك الافتراضي.")
                        plan = generate_fallback_architecture(req)
                        HybridDatabaseEngine.save_project_plan_full(plan, st.session_state.user['email'])
                        st.session_state.current_plan = plan
                        st.session_state.plan_signature = plan.get("signature")
                        st.success("✅ تم توليد الخطة الهندسية الموثوقة بنجاح!")

        if st.session_state.current_plan:
            st.divider()
            col_sig1, col_sig2 = st.columns([3, 1])
            with col_sig1:
                st.info(f"{txt['digital_sig']}\n`{st.session_state.plan_signature}`")
            with col_sig2:
                is_valid = SecurityEngine.verify_signature(st.session_state.current_plan, st.session_state.plan_signature)
                if is_valid:
                    st.markdown(f"<br><span class='badge-green'>{txt['sig_valid']}</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<br><span class='badge-purple'>{txt['sig_invalid']}</span>", unsafe_allow_html=True)

            st.markdown("### 👥 الكوادر والاستشاريون المطلوبون وأجورهم المخصصة")
            specs = AIFacade.calculate_specialists_breakdown(
                st.session_state.current_plan['budget'],
                st.session_state.current_plan['target_days'],
                st.session_state.current_plan['domain']
            )
            df_specs = pd.DataFrame(specs)
            st.dataframe(df_specs[["icon", "role", "total_cost", "total_hours", "hourly_rate", "daily_rate", "ratio_pct"]], use_container_width=True)

            st.markdown("### 📋 المراحل الإنشائية ونطاق المهام الفنية")
            df_tasks = pd.DataFrame(st.session_state.current_plan.get('tasks', []))
            st.dataframe(df_tasks, use_container_width=True)

            col_dl1, col_dl2, col_dl3 = st.columns(3)
            with col_dl1:
                st.download_button("📦 تصدير ملف JSON", json.dumps(st.session_state.current_plan, ensure_ascii=False), "plan.json", "application/json", use_container_width=True)
            with col_dl2:
                excel_bytes = generate_excel_download(df_tasks)
                st.download_button(txt['export_excel'], excel_bytes, f"{st.session_state.current_plan['project_name']}_BOQ.xlsx", use_container_width=True)
            with col_dl3:
                detailed_txt = build_detailed_plan_text(st.session_state.current_plan)
                pdf_bytes = generate_pdf_plan(st.session_state.current_plan, st.session_state.plan_signature, detailed_txt)
                st.download_button(txt['export_pdf'], pdf_bytes, f"{st.session_state.current_plan['project_name']}_Contract.pdf", "application/pdf", use_container_width=True)

    # =========================================================================
    # TAB ENG: BLUEPRINT READER & AUTOMATED TAKEOFF (المحرك الإنشائي والتكعيب)
    # =========================================================================
    with tab_eng:
        st.header("📐 قراءة المخططات واستخراج حساب الكميات (Automated BOQ Takeoff)")
        st.caption("الفحص التلقائي بالرؤية الحاسوبية وقراءات الحسابات الهندسية (خرسانة، حديد تسليح، طابوق، كهروميكانيك).")

        uploaded_file = st.file_uploader("اختر ملف المخطط الهندسي (PDF, DWG, DXF, PNG, JPG):", type=["pdf", "png", "jpg", "jpeg", "dwg", "dxf"], key="blueprint_uploader")

        col_a1, col_a2, col_a3 = st.columns(3)
        with col_a1:
            land_area = st.number_input("مساحة البناء الإجمالية لكل طابق (م²):", min_value=30.0, value=250.0, step=10.0, key="eng_land_area")
        with col_a2:
            floors_count = st.number_input("عدد الطوابق:", min_value=1, value=3, step=1, key="eng_floors_count")
        with col_a3:
            quality_tier = st.selectbox("مستوى جودة التشطيب والإنشاء:", ["Standard", "Economy", "Luxury"], key="eng_quality_tier")

        if st.button("🔍 تشغيل الفحص الإنشائي وتكعيب المواد", type="primary", use_container_width=True):
            if uploaded_file is None:
                st.warning("يرجى رفع ملف المخطط الهندسي للبدء.")
            else:
                file_bytes = uploaded_file.read()
                filename = uploaded_file.name
                
                with st.spinner("جاري فحص المخطط بالرؤية الحاسوبية واستخراج كميات المواد..."):
                    # 1. التثبت والتأكد بالرؤية الحاسوبية (Computer Vision Guard)
                    is_valid_file = True
                    if ENGINES_AVAILABLE:
                        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                            img = Image.open(uploaded_file)
                            is_valid_file, guard_msg = EngineeringTakeoffEngine.computer_vision_blueprint_guard(img)
                            if not is_valid_file:
                                st.error(f"❌ تم رفض الملف: {guard_msg}")
                    
                    if is_valid_file:
                        # 2. حساب جدول الكميات التكعيبي BOQ Computation
                        if ENGINES_AVAILABLE:
                            boq_results = EngineeringTakeoffEngine.compute_boq_from_dimensions(land_area, floors_count, quality_tier)
                        else:
                            boq_results = {
                                "concrete_m3": land_area * floors_count * 0.35,
                                "rebar_tons": (land_area * floors_count * 0.35) * 0.12,
                                "masonry_blocks": land_area * floors_count * 45,
                                "estimated_cost_usd": land_area * floors_count * 220
                            }

                        st.session_state.engineering_analysis_result = {
                            "success": True,
                            "filename": filename,
                            "boq": boq_results
                        }
                        st.success("✅ تم الفحص الهيكلي وتكعيب كميات البناء بنجاح!")

        # عرض التقرير الهندسي ونتائج التكعيب
        res = st.session_state.engineering_analysis_result
        if res and res.get("success"):
            boq = res.get("boq", {})
            st.divider()
            st.subheader("📊 ملخص الكميات والمواد المحسوبة (Calculated Quantities)")
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("📦 الخرسانة المسلحة الإجمالية", f"{boq.get('concrete_m3', 0):,.1f} م³")
            m2.metric("🏗️ حديد التسليح (High-Tensile)", f"{boq.get('rebar_tons', 0):,.2f} طن")
            m3.metric("🧱 عدد البلوك/الطابوق الإجمالي", f"{boq.get('masonry_blocks', 0):,.0f} قطعة")
            m4.metric("💰 التكلفة التقديرية الإجمالية", f"${boq.get('estimated_cost_usd', 0):,.2f}")

            # جدول تفصيلي للمواد
            boq_table_data = [
                {"المادة / البند": "خرسانة مسلحة (C30/35)", "الكمية": f"{boq.get('concrete_m3', 0):,.1f}", "الوحدة": "م³", "ملاحظات": "أساسات + أعمدة + أسقف"},
                {"المادة / البند": "حديد تسليح مضاد للزلازل", "الكمية": f"{boq.get('rebar_tons', 0):,.2f}", "الوحدة": "طن", "ملاحظات": "معدل 120-140 كجم/م³"},
                {"المادة / البند": "طابوق أحمر / أسمنتي", "الكمية": f"{boq.get('masonry_blocks', 0):,.0f}", "الوحدة": "قطعة", "ملاحظات": "جدران خارجية وداخلية"},
                {"المادة / البند": "أعمال الكهروميكانيك MEP", "الكمية": "1", "الوحدة": "مقطوعية", "ملاحظات": "تأسيسات كهرباء وسباكة وتكييف"}
            ]
            st.table(pd.DataFrame(boq_table_data))

    # =========================================================================
    # TAB ARCH: GENERATIVE 2D ARCHITECTURAL BLUEPRINT (المخطط المعماري التوليدي)
    # =========================================================================
    with tab_arch:
        st.header("🏛️ محرك المخططات المعمارية التوليدية 2D Blueprint Engine")
        st.caption("توليد وتحديث المخططات المعمارية التفاعلية وإمكانية توزيع الغرف والأعمدة إنشائياً.")

        col_g1, col_g2, col_g3 = st.columns(3)
        with col_g1:
            arch_width = st.slider("عرض المبنى (أمتار):", 8.0, 30.0, 15.0, 0.5)
        with col_g2:
            arch_length = st.slider("طول المبنى (أمتار):", 10.0, 40.0, 20.0, 0.5)
        with col_g3:
            building_type = st.selectbox("نوع المبنى المعماري:", ["Residential Villa", "Commercial Space", "Administrative Office"])

        if st.button("✏️ رسم وتوليد المخطط المعماري التفاعلي", type="primary", use_container_width=True):
            if ENGINES_AVAILABLE:
                fig_arch = GenerativeArchitecturalEngine.render_plotly_blueprint(arch_width, arch_length, building_type)
                st.plotly_chart(fig_arch, use_container_width=True)
            else:
                st.info("💡 المحرك المعماري التوليديPlotly جاهز للتشغيل عند ربطه بالموديول الرئيسي.")

    # =========================================================================
    # TAB TWIN: LIVE FIELD SIMULATION & DIGITAL TWIN (التوأم الرقمي)
    # =========================================================================
    with tab_twin:
        st.header("🌐 محاكاة التوأم الرقمي والواقع الميداني (Live Twin Engine)")
        st.caption("محاكاة الأجهاد الإنشائي وفحص موقع العمل مقارنة بنسبة التنفيذ الفعلية.")

        col_tw1, col_tw2 = st.columns(2)
        with col_tw1:
            soil_type = st.selectbox("نوع تربة الموقع:", ["Solid Rock", "Clay", "Sandy", "Saturated Silt"])
            seismic_zone = st.slider("مؤشر النشاط الزلزالي (Seismic Index):", 0.0, 0.5, 0.15, 0.05)
        with col_tw2:
            execution_pct = st.slider("نسبة الإنجاز الميداني الفعلي (%):", 0, 100, 35, 5)
            total_project_fund = st.number_input("إجمالي قيمة العقد المالي ($):", value=100000)

        if st.button("🧪 تشغيل اختبار الإجهاد والمطابقة الميدانية", type="primary", use_container_width=True):
            if ENGINES_AVAILABLE:
                twin_res = LiveTwinEngine.simulate_field_stress(soil_type, seismic_zone, execution_pct, total_project_fund)
                
                st.subheader("📌 نتائج تحليل السلامة الميدانية والتوأم الرقمي")
                c_tw1, c_tw2, c_tw3 = st.columns(3)
                c_tw1.metric("مؤشر الاستقرار الإنشائي", f"{twin_res.get('stability_score', 92)}%")
                c_tw2.metric("المستحقات المالية المجهزة للتحرير", f"${twin_res.get('releasable_amount', 35000):,.2f}")
                c_tw3.metric("مستوى خطورة الهبوط", twin_res.get('settlement_risk', 'Low'))
                
                st.info(f"💡 **توصية التوأم الرقمي:** {twin_res.get('recommendation', 'الموقع آمن، يمكن إفراج الدفعة المالية التالية عبر الضمان المشفر.')}")

    # =========================================================================
    # TAB ESCROW: ZKP SMART CONTRACT ESCROW AGENT (الضمان المشفر)
    # =========================================================================
    with tab_escrow:
        st.header("🔐 وكيل الضمان المالي المشفر (Zero-Knowledge Proof Escrow)")
        st.caption("تأمين أموال الدفعات الإنشائية وإدارتها تلقائياً دون الكشف عن تفاصيل التسعير السرية.")

        col_e1, col_e2 = st.columns(2)
        with col_e1:
            contractor_id = st.text_input("معرف المقاول / المهندس المنفذ:", value="CTR-YEM-2026-99")
            escrow_amount = st.number_input("مبلغ الدفعة المشفرة ($):", value=15000)
        with col_e2:
            milestone_name = st.text_input("اسم المرحلة الإنشائية:", value="صب خرسانة سقف الطابق الأول")
            milestone_progress = st.slider("نسبة تحقق المرحلة (%):", 0, 100, 100)

        if st.button("🔑 إنشاء اثبات مشفر ZKP وإيداع الدفعة", type="primary", use_container_width=True):
            if ENGINES_AVAILABLE:
                zkp_proof = ZeroKnowledgeEscrow.generate_proof(contractor_id, escrow_amount, milestone_name)
                st.session_state.zkp_proofs.append(zkp_proof)
                st.success("✅ تم توليد إثبات Zero-Knowledge وتأمين مبلغ الدفعة بنجاح!")

        if st.session_state.zkp_proofs:
            st.divider()
            st.subheader("📜 سجل العقود المشفرة ZKP Proofs")
            for proof in st.session_state.zkp_proofs:
                st.code(json.dumps(proof, indent=2, ensure_ascii=False), language="json")

    # =========================================================================
    # TAB TELEPHONY: COMMUNICATIONS & MESSAGING
    # =========================================================================
    with tab_telephony:
        st.header("📞 مركز الاتصالات الموحد والرسائل النصية (Telephony Hub)")
        st.caption("أداة مجانية للاتصال المباشر عبر SIP/WebRTC وتوجيه الرسائل النصية الفورية للعملاء والفرق الفنية.")
        
        col_tel1, col_tel2 = st.columns([1, 1])
        
        with col_tel1:
            st.subheader("🎙️ لوحة الاتصال الصوتي المباشر")
            render_telephony_widget()
            
        with col_tel2:
            st.subheader("💬 بوابة إرسال الرسائل النصية والـ SMS")
            with st.form("sms_dispatcher_form"):
                target_phone = st.text_input("رقم هاتف المستلم (مع الرمز الدولي)", value=st.session_state.notify_whatsapp)
                message_text = st.text_area("نص الرسالة الفورية", value="مرحباً، تم تحديث بيانات مشروعك بنجاح في منصة PHOENIX PRO.")
                send_sms_btn = st.form_submit_button("🚀 إرسال الرسالة النصية الآن")
                
                if send_sms_btn:
                    if target_phone:
                        telephony_eng = TelephonyEngine()
                        res = telephony_eng.send_sms(target_phone, message_text)
                        if res.get("success"):
                            st.success(f"✅ تم إرسال الرسالة بنجاح إلى الرقم {target_phone}")
                        else:
                            st.error(f"❌ تعذر الإرسال: {res.get('error')}")
                    else:
                        st.warning("يرجى إدخال رقم هاتف المستلم أولاً.")

    # =========================================================================
    # TAB 2: ADVANCED 6D INTERACTIVE ANALYTICS
    # =========================================================================
    with tab2:
        if not st.session_state.current_plan:
            st.info("💡 قم بتوليد خطة مشروع أولاً لعرض التحليلات الهندسية المتقدمة.")
        else:
            plan = st.session_state.current_plan
            df = pd.DataFrame(plan.get('tasks', []))
            
            p_budget = float(plan['budget'])
            p_days = int(plan['target_days'])
            p_hours = p_days * 8
            daily_cost = p_budget / max(1, p_days)
            
            risk_val = plan.get('risk', 'متوسط')
            risk_penalty = 20 if risk_val == "عالي" else (10 if risk_val == "متوسط" else 5)
            budget_efficiency = min(100, max(40, int((p_budget / (p_days * 100)) * 50)))
            success_rate = min(98, max(55, int(budget_efficiency + (40 - risk_penalty))))
            failure_rate = round(100.0 - success_rate, 1)
            tech_readiness = 92.5 if "PostgreSQL" in str(plan.get('tech_stack')) else 84.0

            st.markdown("## 📊 لوحة القيادة الهندسية وتفصيل الجودة والمخاطر 6D")
            st.caption("رسومات نص دائرية ومؤشرات تفاعلية ملونة تشرح التكلفة، الأيام، الساعات، نسبة النجاح، والمخاطر لكل مشروع بدقة متناهية.")

            g_col1, g_col2, g_col3 = st.columns(3)
            with g_col1:
                fig1 = create_half_doughnut_gauge(daily_cost, "💰 التكلفة اليومية الكلية", "#3B82F6", prefix="$", suffix="/يوم", max_val=daily_cost*2)
                st.plotly_chart(fig1, use_container_width=True)
            with g_col2:
                fig2 = create_half_doughnut_gauge(p_hours, "⏱️ إجمالي ساعات العمل الهندسية", "#8B5CF6", suffix=" ساعة", max_val=p_hours*1.5)
                st.plotly_chart(fig2, use_container_width=True)
            with g_col3:
                fig3 = create_half_doughnut_gauge(p_days, "📅 الأيام التقويمية المستهدفة", "#06B6D4", suffix=" يوم", max_val=p_days*1.5)
                st.plotly_chart(fig3, use_container_width=True)

            g_col4, g_col5, g_col6 = st.columns(3)
            with g_col4:
                fig4 = create_half_doughnut_gauge(success_rate, "🌟 نسبة النجاح المتوقعة للمشروع", "#10B981", suffix="%")
                st.plotly_chart(fig4, use_container_width=True)
            with g_col5:
                fig5 = create_half_doughnut_gauge(failure_rate, "⚠️ نسبة المخاطر والفشل المحتملة", "#EF4444", suffix="%")
                st.plotly_chart(fig5, use_container_width=True)
            with g_col6:
                fig6 = create_half_doughnut_gauge(tech_readiness, "🛡️ جاهزية البنية والتكتم الأمني", "#F59E0B", suffix="%")
                st.plotly_chart(fig6, use_container_width=True)

            st.divider()

            st.markdown("### 📝 المتطلبات التفصيلية والشرح المباشر للمشروع")
            col_desc1, col_desc2 = st.columns(2)

            with col_desc1:
                st.markdown(f"""
                <div class="stat-card-box" style="text-align: right;">
                    <h4 style="color: #60A5FA;">💵 تفاصيل توزيع الميزانية والأيام</h4>
                    <p>• <b>الميزانية الإجمالية:</b> ${p_budget:,.2f}</p>
                    <p>• <b>معدل الإنفاق اليومي:</b> ${daily_cost:,.2f} / يوم عمل</p>
                    <p>• <b>معدل التكلفة للساعة:</b> ${(p_budget / max(1, p_hours)):,.2f} / ساعة</p>
                    <p>• <b>احتياطي الطوارئ الموصى به:</b> ${(p_budget * 0.1):,.2f} (10%)</p>
                </div>
                """, unsafe_allow_html=True)

            with col_desc2:
                st.markdown(f"""
                <div class="stat-card-box" style="text-align: right;">
                    <h4 style="color: #34D399;">🧠 تقييم فرصة النجاح والمخاطر</h4>
                    <p>• <b>احتمالية النجاح التنفيذي:</b> <span style="color: #10B981; font-weight: bold;">{success_rate}%</span></p>
                    <p>• <b>مستوى تحمل المخاطرة:</b> {plan.get('risk', 'متوسط')}</p>
                    <p>• <b>توصية النظام الأمني:</b> تفعيل HMAC Signature وتأمين جداول RLS في Cloud SQL.</p>
                </div>
                """, unsafe_allow_html=True)

            st.divider()
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                st.markdown("### 🍩 التحليل المالي المتداخل (Sunburst)")
                labels = [plan['project_name']] + [t.get('task', t.get('title', 'مهمة')) for t in plan.get('tasks', [])]
                parents = [""] + [plan['project_name']] * len(df)
                values = [plan['budget']] + [t.get('cost', 0) for t in plan.get('tasks', [])]
                fig_sunburst = go.Figure(go.Sunburst(labels=labels, parents=parents, values=values, branchvalues="total", marker=dict(colorscale='Blues')))
                fig_sunburst.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color=text_color), height=320)
                st.plotly_chart(fig_sunburst, use_container_width=True)

            with col_c2:
                st.markdown("### 🕸️ تقييم الأبعاد (5D Radar Risk Matrix)")
                radar_cats = ['تعقيد النطاق', 'الأمان الرقمي', 'التحكم بالجدول', 'استقرار التكلفة', 'المرونة التقنية']
                radar_vals = [80, 95, 85, 90, 70]
                fig_radar = go.Figure(go.Scatterpolar(r=radar_vals, theta=radar_cats, fill='toself', line=dict(color='#8B5CF6')))
                fig_radar.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color=text_color), height=320)
                st.plotly_chart(fig_radar, use_container_width=True)

    # =========================================================================
    # TAB 3: TASK EDITOR & DETAILED REPORT
    # =========================================================================
    with tab3:
        st.subheader(txt['tab3'])
        if not st.session_state.current_plan:
            st.warning("⚠️ لا توجد خطة حالية لتعديلها.")
        else:
            edited_df = st.data_editor(
                pd.DataFrame(st.session_state.current_plan['tasks']),
                num_rows="dynamic", use_container_width=True, key="task_editor"
            )
            if st.button(txt['save_re_sign'], type="primary", use_container_width=True):
                st.session_state.current_plan['tasks'] = edited_df.to_dict(orient="records")
                new_sig = SecurityEngine.generate_signature(st.session_state.current_plan)
                st.session_state.current_plan['signature'] = new_sig
                st.session_state.plan_signature = new_sig
                HybridDatabaseEngine.save_project_plan_full(st.session_state.current_plan, st.session_state.user['email'])
                st.success("✅ تم حفظ التعديلات وإعادة التوقيع الرقمي بنجاح!")
                st.rerun()

            st.divider()
            st.markdown(f"### {txt['detailed_plan']}")
            st.markdown(build_detailed_plan_text(st.session_state.current_plan))

    # =========================================================================
    # TAB 4: CLOSED-LOOP FEEDBACK & DYNAMIC PRICING
    # =========================================================================
    with tab4:
        st.subheader("🔄 نظام التغذية الراجعة والتسعير التكيفي (AI Closed-Loop Feedback)")
        st.caption("نظام ربط آراء العملاء بضبط الخيارات السعرية تلقائياً وفق احتياج السوق.")

        col_fb1, col_fb2 = st.columns([1, 1])

        with col_fb1:
            st.markdown("### 📝 شاركنا رأيك (واربح 1 نقطة مجانية أوتوماتيكياً)")
            
            st.markdown("**تقييمك الكلي للمنصة (حدد عدد النجوم):**")
            stars_selection = st.feedback("stars")
            rating_stars = (stars_selection + 1) if stars_selection is not None else 5
            
            star_display = "🌟" * rating_stars
            st.caption(f"التقييم المختار: **{star_display}** ({rating_stars} من 5 نجوم)")

            with st.form("feedback_form"):
                suggested_p = st.number_input("ما هو السعر الشهري العادل بالدولار لهذه الخدمة؟ ($)", min_value=5, max_value=200, value=29)
                req_feature = st.selectbox("ما هي الميزة الأكثر أهمية التي ترغب بإضافتها؟", [
                    "تصدير تقارير احترافية بالعربية PDF",
                    "ربط أوتوماتيكي مع Cloud SQL و Cloud Run",
                    "إشعارات فورية عبر الواتساب والتليجرام",
                    "تكامل مع الذكاء الاصطناعي المباشر Gemini Pro",
                    "إدارة الميزانية المتعددة للعملات"
                ])
                comments = st.text_area("ملاحظات إضافية أو مقترحات لتطوير المنصة", placeholder="اكتب تعليقك وطموحك للمنصة هنا...")
                submit_fb = st.form_submit_button("🚀 إرسال التغذية الراجعة وتحديث النظام")

                if submit_fb:
                    if HybridDatabaseEngine.save_feedback(st.session_state.user['email'], rating_stars, suggested_p, req_feature, comments):
                        new_c = st.session_state.user['credits'] + 1
                        HybridDatabaseEngine.update_credits(st.session_state.user['email'], new_c)
                        st.session_state.user['credits'] = new_c
                        
                        st.balloons()
                        st.success("🎉 شكراً لك! تم إضافة 1 نقطة مجانية إلى حسابك وحفظ التقييم كاملاً!")
                        time.sleep(1)
                        st.rerun()

        with col_fb2:
            st.markdown("### 🏆 لوحة إثبات احتياج السوق وقوة التكيف")
            feedbacks = HybridDatabaseEngine.get_all_feedback()
            adapted = AIFacade.analyze_feedback_and_adapt_pricing(feedbacks)

            st.markdown(f"""
            <div class="feedback-card">
                <h4>🤖 Dynamic Pricing Engine Response:</h4>
                <p>• <b>متوسط السعر المقترح من العملاء:</b> ${adapted['recommended_monthly']}/شهر</p>
                • <b>الاشتراك السنوي المحسوب تلقائياً:</b> ${adapted['recommended_yearly']}/سنة<br>
                • <b>مؤشر رضا السوق (PMF Score):</b> {adapted['market_satisfaction_score']}%<br>
                • <b>إجمالي الآراء المسجلة:</b> {len(feedbacks)} تقييم حقيقي
            </div>
            """, unsafe_allow_html=True)

            st.markdown("#### 💬 سجل آراء جميع العملاء الحية (Live Stream):")
            if feedbacks:
                for f in feedbacks:
                    stars_count = f.get('rating', 5) or 5
                    stars_str = "🌟" * stars_count
                    comment_text = f.get('comments', '') or "لا توجد ملاحظات إضافية."
                    
                    st.markdown(f"""
                    <div class="user-feedback-item">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <b>👤 البريد: <code>{f['user_email']}</code></b>
                            <span style="font-size: 16px;">{stars_str} ({stars_count}/5)</span>
                        </div>
                        <p style="margin-top: 6px; margin-bottom: 4px;">💵 <b>السعر المقترح:</b> ${f['suggested_price']} | 💡 <b>الميزة المطلوبة:</b> {f['requested_feature']}</p>
                        <p style="color: #94A3B8; font-style: italic; margin-bottom: 0;">💬 <b>التعليق:</b> {comment_text}</p>
                        <small style="color: #64748B;">📅 التاريخ: {f.get('created_at', 'مؤخراً')}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("لا توجد تقييمات سابقة بعد. كن أول من يشارك رأيه!")

    # =========================================================================
    # TAB 5: ACCOUNT & SUBSCRIPTIONS
    # =========================================================================
    with tab5:
        st.subheader(txt['tab5'])
        col_acc1, col_acc2 = st.columns(2)
        with col_acc1:
            st.markdown("### 👤 بيانات الحساب")
            st.write(f"**الاسم:** {st.session_state.user['username']}")
            st.write(f"**البريد:** {st.session_state.user['email']}")
            st.write(f"**نوع الاشتراك:** {st.session_state.user['role']}")
            st.write(f"**الرصيد المتاح:** {st.session_state.user['credits']} نقطة")

        with col_acc2:
            st.markdown("### 🛒 خطط الترقية المتاحة (التسيعر الديناميكي المكيّف)")
            st.markdown(f'<a href="{PAYMENT_LINK_MONTHLY}" target="_blank" class="checkout-btn">💳 الاشتراك الشهري (${adapted_insights["recommended_monthly"]})</a>', unsafe_allow_html=True)
            st.write("")
            st.markdown(f'<a href="{PAYMENT_LINK_YEARLY}" target="_blank" class="checkout-btn-yearly">👑 الاشتراك السنوي (${adapted_insights["recommended_yearly"]})</a>', unsafe_allow_html=True)

        if st.session_state.payment_notifications:
            st.divider()
            st.markdown("### 📩 سجل إشعارات الدفع والعمليات الذكية")
            for notif in st.session_state.payment_notifications:
                st.markdown(f"""
                <div class="stat-card-box" style="text-align: right;">
                    <b>المستلم:</b> {notif['to']}<br>
                    <b>رقم الطلب:</b> {notif['order_id']}<br>
                    <b>الباقة:</b> {notif['plan_name']} ({notif['amount']})<br>
                    <b>التاريخ:</b> {notif['date']}
                </div>
                """, unsafe_allow_html=True)

    # =========================================================================
    # TAB 6: CLOUD DB ARCHIVE
    # =========================================================================
    with tab6:
        st.subheader("🗄️ الأرشيف والتكامل مع Cloud SQL")
        st.caption("عرض أحدث المشاريع المسجلة في هيكل الجداول الكامل.")
        
        saved_projs = HybridDatabaseEngine.get_projects(st.session_state.user['email'])
        if saved_projs:
            st.dataframe(pd.DataFrame(saved_projs), use_container_width=True)
        else:
            st.info("لا توجد مشاريع محفوظة حالياً.")

    # =========================================================================
    # TAB ADMIN: CEO CONTROL PANEL
    # =========================================================================
    if is_ceo_owner and tab_admin is not None:
        with tab_admin:
            st.subheader("👑 لوحة قيادة الإدارة العليا والمالك (CEO Control Center)")
            st.caption("صفحة الإدارة المركزية والتحكم بكافة صلاحيات واستعلامات المنصة.")

            all_users = HybridDatabaseEngine.get_all_users_admin()
            total_users_count = len(all_users)
            subscribed_count = len([u for u in all_users if u['is_subscribed']])
            admin_supervisors_count = len([u for u in all_users if u.get('is_admin')])

            m_adm1, m_adm2, m_adm3, m_adm4 = st.columns(4)
            m_adm1.metric("👥 إجمالي المستخدمين المسجلين", total_users_count)
            m_adm2.metric("💳 عدد الاشتراكات المدفوعة", subscribed_count)
            m_adm3.metric("👑 المشرفين المعتمدين", admin_supervisors_count)
            m_adm4.metric("📈 نسبة التحويل للاشتراك", f"{round((subscribed_count/max(1, total_users_count))*100, 1)}%")

            st.divider()

            st.markdown("### 🔑 تعيين وإضافة مشرف جديد (Grant Supervisor Admin Privilege)")
            col_add_adm1, col_add_adm2 = st.columns([2, 1])
            with col_add_adm1:
                target_admin_email = st.text_input("أدخل البريد الإلكتروني للمستخدم لترقيته إلى مشرف", placeholder="supervisor@domain.com").lower().strip()
            with col_add_adm2:
                st.write("<br>", unsafe_allow_html=True)
                if st.button("✨ تفعيل صلاحية المشرف", type="primary", use_container_width=True):
                    if target_admin_email:
                        if HybridDatabaseEngine.add_admin_privilege(target_admin_email):
                            st.success(f"✅ تم منح صلاحيات المشرف بنجاح لـ `{target_admin_email}`!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ فشل العثور على البريد الإلكتروني في قاعدة البيانات.")

            st.divider()

            st.markdown("### 📋 سجل جميع المستخدمين وااشتراكاتهم الحية")
            if all_users:
                df_admin_users = pd.DataFrame(all_users)
                st.dataframe(df_admin_users[["id", "full_name", "email", "role", "credits", "is_subscribed", "is_admin", "created_at"]], use_container_width=True)

            st.markdown("### 💬 طلبات ورغبات المستخدمين من جدول التغذية الراجعة (User Demands & Needs)")
            admin_fb = HybridDatabaseEngine.get_all_feedback()
            if admin_fb:
                df_admin_fb = pd.DataFrame(admin_fb)
                st.dataframe(df_admin_fb[["user_email", "rating", "suggested_price", "requested_feature", "comments", "created_at"]], use_container_width=True)
            else:
                st.info("لا توجد طلبات مدخلة حتى الآن.")

if __name__ == "__main__":
    main()
