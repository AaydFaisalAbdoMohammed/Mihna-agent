import os
import streamlit as st
from utils import create_checkout_url
from db import logout_user, init_usage

def render_sidebar():
    """رندر القائمة الجانبية المكتملة مع الدفع والإشعارات والحسابات."""
    with st.sidebar:
        st.divider()
        st.write(f"👤 **مرحباً, {st.session_state.get('username', 'المستخدم')}**")
        
        # 1. رصيد الاستخدام والاشتراك
        init_usage()
        if st.session_state.get("is_premium", False):
            st.success("✨ مشترك مميز (غير محدود)")
        else:
            remaining = st.session_state.get("free_uses", 0)
            if remaining > 0:
                st.info(f"⚡ متبقي {remaining} تحويلات مجانية")
            else:
                st.warning("🚫 انتهت استخداماتك! اشترك للمتابعة.")
        
        st.divider()
        st.markdown("### 💳 الاشتراك والترقية")
        
        # 2. بوابة الدفع المباشر
        user_email_input = st.text_input(
            "✉️ البريد الإلكتروني للدفع", 
            value=st.session_state.get("user_email", ""), 
            key="checkout_email_sidebar"
        )
        if st.button("💎 اشترك الآن (9.99$ شهرياً)", use_container_width=True, key="btn_checkout_direct"):
            if not user_email_input:
                st.warning("⚠️ يرجى إدخال البريد الإلكتروني أولاً")
            else:
                try:
                    url = create_checkout_url(user_email_input, st.session_state.get("username", "Guest"))
                    st.success("✅ تم إنشاء رابط الدفع بنجاح!")
                    st.markdown(f"👉 **[اضغط هنا لإتمام عملية الدفع عبر Lemon Squeezy]({url})**")
                except Exception as e:
                    st.error(f"❌ {e}")

        with st.expander("💎 تفاصيل خطط الاشتراك"):
            st.markdown("""
            - **📦 مجاني**: 5 تحويلات
            - **🚀 شهري**: 9.99$ - تحويلات غير محدودة
            - **🏆 سنوي**: 99.99$ - خصم 20%
            """)

        st.divider()
        
        # 3. حالة إشعارات التلجرام
        st.markdown("### 📲 إشعارات التلجرام")
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if bot_token and chat_id:
            st.success("🟢 إشعارات التلجرام: متصلة ونشطة")
        else:
            st.warning("⚠️ متغيرات TELEGRAM_BOT_TOKEN أو TELEGRAM_CHAT_ID غير متوفرة")

        st.divider()
        
        # 4. تسجيل الخروج
        if st.button("🚪 تسجيل الخروج", use_container_width=True, key="logout_btn_sidebar"):
            logout_user()
            st.rerun()

