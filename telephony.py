#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import logging
import urllib.parse
import streamlit as st

# Twilio SDK Integration
try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

# Twilio Environment Configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")

class TelephonyEngine:
    """
    محرك المكالمات الصوتية والتنبيهات الهاتفية الذكية لأصحاب الأعمال
    """

    @staticmethod
    def is_configured() -> bool:
        """التحقق من توفر مكتبة وبيانات اعتماد الاتصال"""
        return TWILIO_AVAILABLE and bool(TWILIO_ACCOUNT_SID) and bool(TWILIO_AUTH_TOKEN) and bool(TWILIO_PHONE_NUMBER)

    @staticmethod
    def clean_phone_number(phone: str) -> str:
        """تنظيف وتنسيق رقم الهاتف بالصيغة الدولية E.164"""
        cleaned = re.sub(r'[^\d+]', '', str(phone).strip())
        if not cleaned.startswith('+'):
            cleaned = '+' + cleaned
        return cleaned

    @classmethod
    def make_voice_call(cls, to_phone: str, message_text: str, language: str = 'ar-SA') -> dict:
        """
        إجراء مكالمة صوتية وتلاوة التنبيه بصوت تفاعلي للعميل/صاحب العمل
        """
        if not cls.is_configured():
            logging.warning("Twilio credentials not fully set. Running in simulation mode.")
            return {
                "status": "simulated",
                "message": f"[محاكاة مكالمة] تم الاتصال بالرقم {to_phone} وتلاوة: '{message_text}'",
                "call_sid": "SIM_CALL_123456789"
            }

        try:
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            target_phone = cls.clean_phone_number(to_phone)

            # بناء تعليمات TwiML لتلاوة النص بالصوت
            # استخدام صوت محلي عربي موجه
            voice_param = "Polly.Zeina" if language.startswith("ar") else "Polly.Joanna"
            encoded_text = urllib.parse.quote(message_text)
            twiml_url = f"https://twimlets.com/message?Message%5B0%5D={encoded_text}&Voice={voice_param}"

            call = client.calls.create(
                to=target_phone,
                from_=TWILIO_PHONE_NUMBER,
                url=twiml_url
            )

            return {
                "status": "queued",
                "message": f"تم إطلاق المكالمة بنجاح إلى {target_phone}",
                "call_sid": call.sid
            }
        except Exception as e:
            logging.error(f"Voice Call Exception: {e}")
            return {
                "status": "failed",
                "message": f"فشل إجراء المكالمة: {str(e)}",
                "call_sid": None
            }

    @classmethod
    def send_sms_alert(cls, to_phone: str, message_text: str) -> dict:
        """
        إرسال رسالة نصية قصيرة SMS عاجلة
        """
        if not cls.is_configured():
            return {
                "status": "simulated",
                "message": f"[محاكاة SMS] تم إرسال الرسالة إلى {to_phone}: '{message_text}'",
                "sid": "SIM_SMS_123456789"
            }

        try:
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            target_phone = cls.clean_phone_number(to_phone)

            message = client.messages.create(
                body=message_text,
                from_=TWILIO_PHONE_NUMBER,
                to=target_phone
            )

            return {
                "status": "sent",
                "message": f"تم إرسال الـ SMS بنجاح إلى {target_phone}",
                "sid": message.sid
            }
        except Exception as e:
            logging.error(f"SMS Exception: {e}")
            return {
                "status": "failed",
                "message": f"فشل إرسال الـ SMS: {str(e)}",
                "sid": None
            }


def render_telephony_widget():
    """
    واجهة تفاعلية مصغرة لإطلاق التنبيهات الهاتفية والمكالمات داخل Streamlit
    """
    st.markdown("### 📞 محرك المكالمات والاتصال الهاتفي المباشر (Voice & SMS Alerts)")
    st.caption("أرسل تنبيهات صوتية أوتوماتيكية لأصحاب الأعمال فور توليد خطط المشاريع أو التعديلات الهامة.")

    col_tel1, col_tel2 = st.columns([1.5, 1])

    with col_tel1:
        phone_input = st.text_input("رقم هاتف صاحب العمل (بالصيغة الدولية)", value="+967700000000")
        call_msg = st.text_area(
            "رسالة المكالمة الصوتية (سيتم تحويل النص إلى صوت أثناء المكالمة)",
            value="مرحباً بك! تم توليد وتحديث خطة مشروعك الهندسية بنجاح عبر منصة مهنة برؤ. يرجى مراجعة لوحة التحكم.",
            height=100
        )

    with col_tel2:
        st.write("<br>", unsafe_allow_html=True)
        btn_voice = st.button("📞 إجراء مكالمة صوتية فورية", type="primary", use_container_width=True)
        btn_sms = st.button("💬 إرسال تنبيه SMS عاجل", use_container_width=True)

        if btn_voice:
            with st.spinner("جاري الاتصال بهاتف صاحب العمل..."):
                res = TelephonyEngine.make_voice_call(phone_input, call_msg)
                if res["status"] in ["queued", "simulated"]:
                    st.success(f"✅ {res['message']}")
                else:
                    st.error(f"❌ {res['message']}")

        if btn_sms:
            with st.spinner("جاري إرسال الرسالة النصية..."):
                res = TelephonyEngine.send_sms_alert(phone_input, call_msg)
                if res["status"] in ["sent", "simulated"]:
                    st.success(f"✅ {res['message']}")
                else:
                    st.error(f"❌ {res['message']}")
