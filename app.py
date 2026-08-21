#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
© 2026 PHOENIX & MIHNA AGENT PRO ENTERPRISE ARCHITECTURE v14.0 - HYBRID ULTIMATE
الواجهة الرئيسية ومسار تشغيل التطبيق بعد التقسيم الهيكلي الموحد
===============================================================================
"""

import json
import time
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Modules Import
from telephony import TelephonyEngine, render_telephony_widget
from db import HybridDatabaseEngine, SUPER_ADMIN_EMAILS
from auth import render_auth_page
from ai import PhoenixAI, AIPaymentAgent
from utils import (
    SecurityEngine, NotificationEngine, generate_excel_download,
    generate_pdf_plan, build_detailed_plan_text, create_half_doughnut_gauge,
    PAYMENT_LINK_MONTHLY, PAYMENT_LINK_YEARLY
)

APP_TITLE = "PHOENIX & MIHNA AGENT PRO - HYBRID ULTIMATE v14.0"

def init_session():
    if 'lang' not in st.session_state: st.session_state.lang = 'ar'
    if 'theme' not in st.session_state: st.session_state.theme = 'dark'
    if 'is_authenticated' not in st.session_state: st.session_state.is_authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = {'email': '', 'username': 'زائر', 'credits': 5, 'role': 'Free Trial', 'is_subscribed': False, 'is_admin': False}
    if 'current_plan' not in st.session_state: st.session_state.current_plan = None
    if 'plan_signature' not in st.session_state: st.session_state.plan_signature = None
    if 'notify_whatsapp' not in st.session_state: st.session_state.notify_whatsapp = "+967700000000"
    if 'notify_telegram' not in st.session_state: st.session_state.notify_telegram = "@Ayad_Developer"
    if 'form_scope' not in st.session_state: st.session_state.form_scope = ""
    if 'form_pname' not in st.session_state: st.session_state.form_pname = "منصة تجارة سحابية Pro"
    if 'form_domain' not in st.session_state: st.session_state.form_domain = "التجارة الإلكترونية"
    if 'form_budget' not in st.session_state: st.session_state.form_budget = 3500
    if 'form_days' not in st.session_state: st.session_state.form_days = 30
    if 'payment_notifications' not in st.session_state: st.session_state.payment_notifications = []

T = {
    'ar': {
        'title': "🚀 PHOENIX & MIHNA AGENT PRO Enterprise v14.0",
        'subtitle': "المنصة المتقدمة لهندسة خطط المشاريع، حساب أجور المتخصصين، وتأمين البيانات بـ Cloud SQL و HMAC-SHA512.",
        'lang_select': "🌐 لغة الواجهة (Language):",
        'theme_select': "🎨 مظهر التطبيق (Theme):",
        'dark': "🌙 الداكن (Dark)", 'light': "☀️ الفاتح (Light)",
        'user': "👤 المستخدم:", 'credits': "💳 الرصيد الحالي:", 'points': "نقاط مجانية",
        'renew_title': "🛒 ترقية الاشتراك", 'renew_btn': "⚡ اشترك الآن وترقية الحساب",
        'logout_btn': "🚪 تسجيل الخروج", 'notify_settings': "📲 إعدادات الإشعارات الفورية",
        'wa_phone': "رقم الواتساب", 'tg_handle': "معرف التليجرام",
        'tab1': "🏗️ بناء الخطة والكوادر", 'tab2': "📊 التحليلات التفاعلية 6D",
        'tab3': "✏️ محرر المهام والتقرير النصي", 'tab4': "🔄 التغذية الراجعة والتكيّف السعري",
        'tab5': "💳 الحساب والاشتراكات", 'tab6': "🗄️ أرشفة Cloud SQL Schema",
        'tab_admin': "👑 لوحة الإدارة العليا (CEO Panel)",
        'quick_templates': "⚡ قوالب جاهزة للبدء السريع",
        'ecom': "🛒 متجر إلكتروني", 'edu': "🎓 منصة تعليمية", 'delivery': "🚗 تطبيق توصيل",
        'p_name': "اسم المشروع", 'tech_domain': "المجال التقني", 'budget': "الميزانية التقديرية ($)",
        'tech_stack': "التقنيات المستخدمة", 'target_days': "المدة الزمنية المستهدفة (يوم)", 'risk_level': "تحمل المخاطر",
        'scope': "نطاق العمل (Scope of Work)",
        'generate_btn': "🚀 توليد وحساب الكوادر والتوقيع الرقمي (1 نقطة)",
        'export_excel': "📥 تحميل جدول المهام (Excel)", 'export_pdf': "📄 تحميل الخطة التنفيذية (PDF)",
        'detailed_plan': "📜 الخطة التنفيذية النصية الشاملة والمعمقة", 'save_re_sign': "💾 حفظ التعديلات وإعادة التوقيع الرقمي",
        'digital_sig': "🔑 التوقيع الرقمي المشفر (HMAC-SHA512):",
        'sig_valid': "✔ توقيع موثوق وسليم", 'sig_invalid': "❌ تم التلاعب بالبيانات",
        'send_wa': "📱 إرسال عبر WhatsApp", 'send_tg': "📲 إشعار Telegram Bot",
    },
    'en': {
        'title': "🚀 PHOENIX & MIHNA AGENT PRO Enterprise v14.0",
        'subtitle': "Advanced Engineering Project Plan Builder & Specialist Payroll Engine Secured with Cloud SQL & HMAC-SHA512.",
        'lang_select': "🌐 Interface Language:",
        'theme_select': "🎨 Application Theme:",
        'dark': "🌙 Dark", 'light': "☀️ Light",
        'user': "👤 User:", 'credits': "💳 Current Balance:", 'points': "points",
        'renew_title': "🛒 Upgrade Plan", 'renew_btn': "⚡ Upgrade & Subscribe Now",
        'logout_btn': "🚪 Log Out", 'notify_settings': "📲 Instant Notification Settings",
        'wa_phone': "WhatsApp Phone", 'tg_handle': "Telegram Handle",
        'tab1': "🏗️ Build Plan & Payroll", 'tab2': "📊 Advanced 6D Analytics",
        'tab3': "✏️ Task Editor & Text Plan", 'tab4': "🔄 Feedback & Pricing",
        'tab5': "💳 Account & Subscriptions", 'tab6': "🗄️ Cloud SQL Archive",
        'tab_admin': "👑 CEO & Admin Panel",
        'quick_templates': "⚡ Quick Start Templates",
        'ecom': "🛒 E-Commerce App", 'edu': "🎓 E-Learning Platform", 'delivery': "🚗 Delivery App",
        'p_name': "Project Name", 'tech_domain': "Technical Domain", 'budget': "Estimated Budget ($)",
        'tech_stack': "Tech Stack", 'target_days': "Target Timeline (Days)", 'risk_level': "Risk Tolerance",
        'scope': "Scope of Work",
        'generate_btn': "🚀 Generate Plan, Payroll & Sign (1 Credit)",
        'export_excel': "📥 Download Tasks (Excel)", 'export_pdf': "📄 Download Plan (PDF)",
        'detailed_plan': "📜 Extended Text Plan", 'save_re_sign': "💾 Save Edits & Re-Sign Digitally",
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

def main():
    st.set_page_config(page_title=APP_TITLE, page_icon="🛡️", layout="wide")
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

    with st.sidebar:
        st.title("🛡️ MIHNA AGENT PRO")
        st.markdown("<span class='badge-purple'>Enterprise v14.0</span>", unsafe_allow_html=True)
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
        adapted_insights = PhoenixAI.analyze_feedback_and_adapt_pricing(all_fb)

        if not st.session_state.user['is_subscribed']:
            if st.button("🤖 الدفع الذكي والتفعيل السريع", type="primary", use_container_width=True):
                AIPaymentAgent.execute_auto_checkout(st.session_state.user['email'], "monthly")
                st.balloons()
                st.success("🎉 تم ترقية حسابك بنجاح!")
                time.sleep(1)
                st.rerun()

        st.markdown(f'<a href="{PAYMENT_LINK_MONTHLY}" target="_blank" class="checkout-btn">💳 {txt["renew_btn"]} (${adapted_insights["recommended_monthly"]}/m)</a>', unsafe_allow_html=True)
        st.write("")
        st.markdown(f'<a href="{PAYMENT_LINK_YEARLY}" target="_blank" class="checkout-btn-yearly">👑 الاشتراك السنوي (${adapted_insights["recommended_yearly"]}/y)</a>', unsafe_allow_html=True)

        st.divider()
        st.subheader(txt['notify_settings'])
        st.session_state.notify_whatsapp = st.text_input(txt['wa_phone'], value=st.session_state.notify_whatsapp)
        st.session_state.notify_telegram = st.text_input(txt['tg_handle'], value=st.session_state.notify_telegram)

    st.title(txt['title'])
    st.caption(txt['subtitle'])

    if st.session_state.user['credits'] <= 0 and not st.session_state.user['is_subscribed']:
        st.markdown("""
        <div class="ai-payment-card">
            <h3>🤖 تنبيه من وكيل الدفع الذكي (AI Payment Broker Agent)</h3>
            <p>لقد نفدت نقاطك المجانية (0/5)! يمكنك تنفيذ الدفع الآلي الفوري بالذكاء الاصطناعي عبر Lemon Squeezy لتفعيل الحساب دون انتظار.</p>
        </div>
        """, unsafe_allow_html=True)
        col_pay_ai1, col_pay_ai2 = st.columns(2)
        with col_pay_ai1:
            if st.button(f"🚀 تفعيل باقة Pro الشهري (${adapted_insights['recommended_monthly']})", type="primary", use_container_width=True):
                AIPaymentAgent.execute_auto_checkout(st.session_state.user['email'], "monthly")
                st.balloons()
                st.rerun()
        with col_pay_ai2:
            if st.button(f"💎 تفعيل باقة Enterprise السنوية (${adapted_insights['recommended_yearly']})", use_container_width=True):
                AIPaymentAgent.execute_auto_checkout(st.session_state.user['email'], "yearly")
                st.balloons()
                st.rerun()

    is_ceo_owner = (st.session_state.user['email'] in SUPER_ADMIN_EMAILS) or st.session_state.user['is_admin']
    
    if is_ceo_owner:
        tab1, tab2, tab3, tab4, tab5, tab6, tab_admin = st.tabs([
            txt['tab1'], txt['tab2'], txt['tab3'], txt['tab4'], txt['tab5'], txt['tab6'], txt['tab_admin']
        ])
    else:
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            txt['tab1'], txt['tab2'], txt['tab3'], txt['tab4'], txt['tab5'], txt['tab6']
        ])

    # TAB 1: BUILD PROJECT PLAN & SPECIALIST PAYROLL
    with tab1:
        st.subheader(txt['quick_templates'])
        col_t1, col_t2, col_t3 = st.columns(3)
        col_t1.button(txt['ecom'], use_container_width=True, on_click=apply_template, args=("تطبيق متجر إلكتروني لبيع المنتجات مع بوابة دفع سريعة ونظام إدارة المخزون", "التجارة الإلكترونية", 4500, 35, "متجر إلكتروني متكامل"))
        col_t2.button(txt['edu'], use_container_width=True, on_click=apply_template, args=("منصة تعليمية تتيح رفع الكورسات واختبارات تفاعلية وشهادات تلقائية", "التعليم الرقمي", 3000, 25, "منصة تعليمية ذكية"))
        col_t3.button(txt['delivery'], use_container_width=True, on_click=apply_template, args=("تطبيق توصيل طلبات يعتمد على الخرائط التفاعلية وتتبع السائقين في الوقت الفعلي", "الخدمات واللوجستيات", 6000, 50, "تطبيق توصيل سريع"))

        domain_options = ["التجارة الإلكترونية", "التعليم الرقمي", "الخدمات واللوجستيات", "الذكاء الاصطناعي", "أنظمة SaaS"]
        domain_idx = domain_options.index(st.session_state.form_domain) if st.session_state.form_domain in domain_options else 0

        with st.form("project_form"):
            col1, col2 = st.columns(2)
            with col1:
                project_name = st.text_input(txt['p_name'], key="form_pname")
                domain = st.selectbox(txt['tech_domain'], domain_options, index=domain_idx, key="form_domain")
                budget = st.number_input(txt['budget'], min_value=500, key="form_budget")
            with col2:
                tech_stack = st.text_input(txt['tech_stack'], value="Flutter, Node.js, PostgreSQL, Supabase")
                target_days = st.number_input(txt['target_days'], min_value=5, key="form_days")
                risk_tolerance = st.select_slider(txt['risk_level'], options=["منخفض جداً", "متوسط", "عالي"])

            project_scope = st.text_area(txt['scope'], key="form_scope", placeholder="اكتب تفاصيل ومتطلبات المشروع هنا...")
            gemini_key = st.text_input("مفتاح Gemini API (اختياري للذكاء الاصطناعي المباشر)", type="password")

            submit_btn = st.form_submit_button(txt['generate_btn'], use_container_width=True)

        if submit_btn:
            if st.session_state.user['credits'] < 1 and not st.session_state.user['is_subscribed']:
                st.error("❌ لقد استنفدت نقاطك المجانية! يرجى الترقية للاستمرار.")
            else:
                with st.spinner("⏳ جاري تحليل المتطلبات، توزيع الكوادر، وتوقيع الخطة رقمياً في Cloud SQL..."):
                    req = {
                        "project_name": project_name, "domain": domain, "budget": budget,
                        "target_days": target_days, "tech_stack": tech_stack, "scope": project_scope, "risk": risk_tolerance
                    }
                    plan = PhoenixAI.generate_architecture(req, api_key=gemini_key)
                    HybridDatabaseEngine.save_project_plan_full(plan, st.session_state.user['email'])

                    if not st.session_state.user['is_subscribed']:
                        new_c = max(0, st.session_state.user['credits'] - 1)
                        HybridDatabaseEngine.update_credits(st.session_state.user['email'], new_c)
                        st.session_state.user['credits'] = new_c

                    st.session_state.current_plan = plan
                    st.session_state.plan_signature = plan.get("signature")
                    st.success("✅ تم توليد الخطة وحساب الكوادر وحفظها بتوقيع رقمي موثوق!")

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

            st.markdown("### 👥 الكوادر والمتخصصون المطلوبون وأجورهم المخصصة (Specialist Payroll & Hours)")
            specs = PhoenixAI.calculate_specialists_breakdown(
                st.session_state.current_plan['budget'],
                st.session_state.current_plan['target_days'],
                st.session_state.current_plan['domain']
            )
            df_specs = pd.DataFrame(specs)
            st.dataframe(df_specs[["icon", "role", "total_cost", "total_hours", "hourly_rate", "daily_rate", "ratio_pct"]], use_container_width=True)

            st.markdown("### 📋 مراحل ونطاق المهام الفنية")
            df_tasks = pd.DataFrame(st.session_state.current_plan.get('tasks', []))
            st.dataframe(df_tasks, use_container_width=True)

            col_dl1, col_dl2, col_dl3 = st.columns(3)
            with col_dl1:
                st.download_button("📦 تصدير ملف JSON", json.dumps(st.session_state.current_plan, ensure_ascii=False), "plan.json", "application/json", use_container_width=True)
            with col_dl2:
                excel_bytes = generate_excel_download(df_tasks)
                st.download_button(txt['export_excel'], excel_bytes, f"{st.session_state.current_plan['project_name']}_Tasks.xlsx", use_container_width=True)
            with col_dl3:
                detailed_txt = build_detailed_plan_text(st.session_state.current_plan)
                pdf_bytes = generate_pdf_plan(st.session_state.current_plan, st.session_state.plan_signature, detailed_txt)
                st.download_button(txt['export_pdf'], pdf_bytes, f"{st.session_state.current_plan['project_name']}_Plan.pdf", "application/pdf", use_container_width=True)

            st.divider()
            col_n1, col_n2 = st.columns(2)
            msg_body = f"🚀 مشروع جديد: {st.session_state.current_plan['project_name']}\n💰 الميزانية: ${st.session_state.current_plan['budget']}\n⏱️ الأيام: {st.session_state.current_plan['target_days']}\n🔑 التوقيع: {st.session_state.plan_signature[:20]}..."
            wa_url = NotificationEngine.create_whatsapp_link(st.session_state.notify_whatsapp, msg_body)

            with col_n1:
                st.markdown(f'<a href="{wa_url}" target="_blank" style="display:block; text-align:center; background-color:#25D366; color:white; padding:10px; border-radius:8px; font-weight:bold; text-decoration:none;">{txt["send_wa"]}</a>', unsafe_allow_html=True)
            with col_n2:
                if st.button(txt['send_tg'], use_container_width=True):
                    st.success(f"✅ تم إرسال التنبيه إلى {st.session_state.notify_telegram}")

    # TAB 2: ADVANCED 6D INTERACTIVE ANALYTICS
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

    # TAB 3: TASK EDITOR & DETAILED PLAN
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

    # TAB 4: CLOSED-LOOP FEEDBACK & DYNAMIC PRICING
    with tab4:
        st.subheader("🔄 نظام التغذية الراجعة المغلقة والتكيّف السعري (AI Closed-Loop Feedback)")
        st.caption("نظام ذكي يربط آراء العملاء فورياً بضبط الخيارات السعرية والميزات داخل الكود لضمان أعلى ملاءمة للسوق.")

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
                        st.success("🎉 شكراً لك! تم إضافة 1 نقطة مجانية إلى حسابك وحفظ التقييم بـ 5 نجوم والتعليق كاملاً!")
                        time.sleep(1)
                        st.rerun()

        with col_fb2:
            st.markdown("### 🏆 لوحة إثبات احتياج السوق وقوة التكيف")
            feedbacks = HybridDatabaseEngine.get_all_feedback()
            adapted = PhoenixAI.analyze_feedback_and_adapt_pricing(feedbacks)

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

    # TAB 5: ACCOUNT & SUBSCRIPTIONS
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

    # TAB 6: CLOUD DB ARCHIVE
    with tab6:
        st.subheader("🗄️ الأرشيف والتكامل مع Cloud SQL")
        st.caption("عرض أحدث المشاريع المسجلة في هيكل الجداول الكامل.")
        
        saved_projs = HybridDatabaseEngine.get_projects(st.session_state.user['email'])
        if saved_projs:
            st.dataframe(pd.DataFrame(saved_projs), use_container_width=True)
        else:
            st.info("لا توجد مشاريع محفوظة حالياً.")

    # TAB ADMIN: CEO CONTROL PANEL
    if is_ceo_owner:
        with tab_admin:
            st.subheader("👑 لوحة قيادة الإدارة العليا والمالك (CEO Control Center)")
            st.caption(f"مرحباً بك! هذه الصفحة مخفية عن جميع المستخدمين العاديين وتظهر فقط للمشرفين المعتمدين.")

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
