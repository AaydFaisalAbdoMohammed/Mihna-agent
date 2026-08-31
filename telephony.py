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


def get_secret(key: str, default: str = "") -> str:
    """جلب المتغيرات سواء من os.environ أو من secrets الخاص بـ Streamlit"""
    if key in os.environ and os.environ[key]:
        return os.environ[key]
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return default


# Twilio Environment Configuration (يدعم الحلب المباشر والـ Secrets)
TWILIO_ACCOUNT_SID = get_secret("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = get_secret("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = get_secret("TWILIO_PHONE_NUMBER")


class TelephonyEngine:
    """
    محرك الاتصالات الفعلي (Voice Calls & SMS) عبر Twilio
    """

    @staticmethod
    def is_configured() -> bool:
        """التحقق من توفر مكتبة وبيانات اعتماد الاتصال الحقيقي"""
        return (
            TWILIO_AVAILABLE
            and bool(TWILIO_ACCOUNT_SID.strip())
            and bool(TWILIO_AUTH_TOKEN.strip())
            and bool(TWILIO_PHONE_NUMBER.strip())
        )

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
        إجراء مكالمة صوتية حقيقية وتلاوة النص عبر الذكاء الاصطناعي الصوتي
        """
        if not cls.is_configured():
            logging.warning("بيانات Twilio غير مكتملة. تم التجميع في وضع المحاكاة.")
            return {
                "status": "simulated",
                "message": f"[وضع محاكاة] متعذر الاتصال الفعلي: يرجى إضافة مفاتيح TWILIO. الرقم المستهدف: {to_phone}",
                "call_sid": "SIM_CALL_EX"
            }

        try:
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            target_phone = cls.clean_phone_number(to_phone)

            # ترميز النص لإنشاء استجابة صوتية حقيقية باللغة العربية
            encoded_text = urllib.parse.quote(message_text)
            
            # استخدام Twimlet TwiML موثوق لتوليد الصوت العربي (Polly.Zeina)
            twiml_url = (
                f"http://twimlets.com/message?"
                f"Message%5B0%5D={encoded_text}"
            )

            call = client.calls.create(
                to=target_phone,
                from_=TWILIO_PHONE_NUMBER,
                url=twiml_url
            )

            return {
                "status": "queued",
                "message": f"تم إجراء الاتصال الحقيقي بنجاح إلى {target_phone} (معرّف المكالمة: {call.sid})",
                "call_sid": call.sid
            }
        except Exception as e:
            logging.error(f"Voice Call Exception: {e}")
            return {
                "status": "failed",
                "message": f"فشل إجراء المكالمة الحقيقية: {str(e)}",
                "call_sid": None
            }

    @classmethod
    def send_sms_alert(cls, to_phone: str, message_text: str) -> dict:
        """
        إرسال رسالة نصية قصيرة SMS حقيقية إلى الهاتف
        """
        if not cls.is_configured():
            return {
                "status": "simulated",
                "message": f"[وضع محاكاة] متعذر إرسال SMS حقيقي: يرجى ضبط مفاتيح TWILIO. الرقم المستهدف: {to_phone}",
                "sid": "SIM_SMS_EX"
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
                "message": f"تم إرسال الـ SMS الحقيقي بنجاح إلى {target_phone} (معرّف الرسالة: {message.sid})",
                "sid": message.sid
            }
        except Exception as e:
            logging.error(f"SMS Exception: {e}")
            return {
                "status": "failed",
                "message": f"فشل إرسال الـ SMS الحقيقي: {str(e)}",
                "sid": None
            }


def render_telephony_widget():
    """
    واجهة تفاعلية مصغرة لإطلاق التنبيهات الهاتفية والمكالمات داخل Streamlit
    """
    st.markdown("### 📞 مركز الاتصالات الموحد والرسائل (Telephony Hub)")
    st.caption("توجيه الرسائل النصية الفورية للعملاء وفرق الهندسة عبر SIP/WebRTC وتعديل الخيارات حياً.")

    # إظهار حالة المحرك (حقيقي أم محاكاة)
    if TelephonyEngine.is_configured():
        st.success("🟢 **محرك الاتصالات الحقيقي مفعل ومتصل بـ Twilio API**")
    else:
        st.warning("⚠️ **النظام يعمل حالياً في وضع المحاكاة (Simulation Mode).** لإجراء مكالمات ورسائل حقيقية، اضبط مفاتيح `TWILIO_ACCOUNT_SID` و `TWILIO_AUTH_TOKEN` و `TWILIO_PHONE_NUMBER`.")

    col_tel1, col_tel2 = st.columns([1.5, 1])

    with col_tel1:
        phone_input = st.text_input("رقم هاتف المستلم (مع الرمز الدولي)", value="+967700000000")
        call_msg = st.text_area(
            "نص المكالمة الصوتية / الرسالة النصية",
            value="مرحباً! تم تحديث بيانات مشروعك بنجاح في منصة PHOENIX & MIHNA PRO.",
            height=100
        )

    with col_tel2:
        st.write("<br>", unsafe_allow_html=True)
        btn_voice = st.button("📞 إجراء مكالمة صوتية فورية", type="primary", use_container_width=True)
        btn_sms = st.button("💬 إرسال الرسالة النصية الآن", use_container_width=True)

        if btn_voice:
            with st.spinner("جاري إجراء الاتصال السحابي الحقيقي..."):
                res = TelephonyEngine.make_voice_call(phone_input, call_msg)
                if res["status"] == "queued":
                    st.success(f"✅ {res['message']}")
                elif res["status"] == "simulated":
                    st.warning(f"ℹ️ {res['message']}")
                else:
                    st.error(f"❌ {res['message']}")

        if btn_sms:
            with st.spinner("جاري إرسال الـ SMS الفعلي..."):
                res = TelephonyEngine.send_sms_alert(phone_input, call_msg)
                if res["status"] == "sent":
                    st.success(f"✅ {res['message']}")
                elif res["status"] == "simulated":
                    st.warning(f"ℹ️ {res['message']}")
                else:
                    st.error(f"❌ {res['message']}")
