#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import re
import uuid
import requests
from datetime import datetime
import streamlit as st

def init_auth():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = None
    if "username" not in st.session_state:
        st.session_state["username"] = None

import bcrypt
import re
import google.generativeai as genai
import config  # يحتوي على المفاتيح (LEMONSQUEEZY_API_KEY, etc.)
from cloudsql_utils import get_db_connection


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
    st.caption("🧠 خطط مشاريعك بذكاء وااحترافية")
    
    st.caption("🧠 خطط مشاريعك بذكاء وااحترافية")
    
    tab1, tab2 = st.tabs(["🔑 تسجيل الدخول", "📝 إنشاء حساب جديد"])
    
    with tab1:
        with st.form("login_form"):
            identifier = st.text_input("👤 اسم المستخدم أو البريد الإلكتروني")
            password = st.text_input("🔒 كلمة المرور", type="password")
            submitted = st.form_submit_button("تسجيل الدخول")
            if submitted:
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
            submitted = st.form_submit_button("إنشاء حساب")
            if submitted:
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

def update_db_schema():
    """تحديث هيكل جدول users لإضافة username و password_hash (إذا لزم الأمر)."""
    conn = get_db_connection()
    if not conn:
        return
    cursor = conn.cursor()
    try:
        # التحقق من وجود العمود username
        cursor.execute("SHOW COLUMNS FROM users LIKE 'username'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE users ADD COLUMN username VARCHAR(100) UNIQUE")
        cursor.execute("SHOW COLUMNS FROM users LIKE 'password_hash'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)")
        conn.commit()
        print("✅ تم تحديث هيكل جدول users.")
    except Exception as e:
        print(f"⚠️ تحديث الهيكل: {e}")
    finally:
        conn.close()

def main():
    init_auth()
    if not st.session_state.authenticated:
        render_login_page()
        return
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
    # زر تسجيل الخروج
    st.divider()
    if st.button("🚪 تسجيل الخروج", use_container_width=True):
        logout_user()
        st.rerun()


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
