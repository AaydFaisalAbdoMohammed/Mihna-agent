#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import streamlit as st
from db import HybridDatabaseEngine, SUPER_ADMIN_EMAILS
from utils import SecurityEngine, generate_qr_code_image, APP_BASE_URL

def render_auth_page():
    st.markdown("<h1 style='text-align: center;'>🚀 بوابة الدخول | PHOENIX & MIHNA AGENT PRO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8;'>سجل دخولك أو أنشئ حساباً جديداً للوصول إلى المنصة الهندسية الذكية</p>", unsafe_allow_html=True)
    st.write("<br>", unsafe_allow_html=True)

    query_params = st.query_params
    is_signup_mode = query_params.get("mode") == "signup"

    col_center, _ = st.columns([1, 0.01])
    with col_center:
        tab_login_title = "🔑 تسجيل الدخول"
        tab_signup_title = "✨ حساب جديد (5 محاولات مجانية)"
        
        if is_signup_mode:
            auth_tabs = st.tabs([tab_signup_title, tab_login_title])
            signup_tab_container = auth_tabs[0]
            login_tab_container = auth_tabs[1]
        else:
            auth_tabs = st.tabs([tab_login_title, tab_signup_title])
            login_tab_container = auth_tabs[0]
            signup_tab_container = auth_tabs[1]

        with login_tab_container:
            col_l1, col_l2 = st.columns([1.5, 1])
            with col_l1:
                with st.form("login_form"):
                    st.subheader("مرحباً بك مجدداً!")
                    email_input = st.text_input("البريد الإلكتروني", placeholder="name@domain.com").lower().strip()
                    password_input = st.text_input("كلمة المرور", type="password", placeholder="••••••••")
                    submit_login = st.form_submit_button("🚀 تسجيل الدخول", use_container_width=True)
                    
                    if submit_login:
                        u = HybridDatabaseEngine.get_user(email_input)
                        if u and SecurityEngine.verify_password(password_input, u["password_hash"]):
                            st.session_state.is_authenticated = True
                            st.session_state.user = {
                                'email': u['email'], 'username': u['full_name'] or u['username'] or "مهندس مهنة",
                                'credits': u['credits'], 'role': u['role'], 'is_subscribed': bool(u['is_subscribed']),
                                'is_admin': bool(u['is_admin']) or (u['email'] in SUPER_ADMIN_EMAILS)
                            }
                            HybridDatabaseEngine.log_audit(u['id'], "LOGIN_SUCCESS", "User logged in.")
                            st.success(f"🎉 أهلاً بك مجدداً {st.session_state.user['username']}!")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ بيانات الدخول غير صحيحة.")

            with col_l2:
                st.markdown("### 📲 امسح الـ QR للتسجيل السريع")
                st.caption("للحملات الإعلانية والجوال: امسح الرمز للتوجيه الفوري وإنشاء حساب جديد")
                
                clean_base_url = APP_BASE_URL.rstrip('/')
                signup_url = f"{clean_base_url}/?mode=signup"
                qr_bytes = generate_qr_code_image(signup_url)
                if qr_bytes:
                    st.image(qr_bytes, width=180, caption="امسح الرمز للكاميرا")

        with signup_tab_container:
            with st.form("signup_form"):
                st.subheader("انضم إلى منصة PHOENIX Enterprise")
                new_username = st.text_input("الاسم الكامل", placeholder="Alex Sterling")
                new_email = st.text_input("البريد الإلكتروني", placeholder="name@domain.com").lower().strip()
                new_password = st.text_input("كلمة المرور", type="password", placeholder="••••••••")
                confirm_password = st.text_input("تأكيد كلمة المرور", type="password", placeholder="••••••••")
                submit_signup = st.form_submit_button("✨ إنشاء حساب وتفعيل 5 نقاط هدية", use_container_width=True)
                
                if submit_signup:
                    if not new_username or not new_email or not new_password:
                        st.warning("⚠️ يرجى ملء كافة الحقول.")
                    elif new_password != confirm_password:
                        st.error("❌ كلمة المرور غير متطابقة.")
                    else:
                        existing = HybridDatabaseEngine.get_user(new_email)
                        if existing:
                            st.error("❌ البريد الإلكتروني مسجل مسبقاً.")
                        else:
                            hashed_p = SecurityEngine.hash_password(new_password)
                            if HybridDatabaseEngine.register_user(new_username, new_email, hashed_p):
                                is_super = (new_email in SUPER_ADMIN_EMAILS)
                                st.session_state.is_authenticated = True
                                st.session_state.user = {
                                    'email': new_email, 'username': new_username, 'credits': 5,
                                    'role': "Enterprise Owner / Super Admin" if is_super else "Free Trial",
                                    'is_subscribed': False, 'is_admin': is_super
                                }
                                st.balloons()
                                st.success("🎉 تم إنشاء الحساب وحفظ البيانات في قاعدة البيانات بنجاح!")
                                time.sleep(0.8)
                                st.rerun()
