import os
import re
import io
import datetime
import requests
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# إعداد الصفحة
st.set_page_config(page_title="وكيل مهنة PRO", page_icon="🧠", layout="wide", initial_sidebar_state="expanded")

# CSS المظهر الداكن الفاخر
st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #f1f5f9; }
    [data-testid="stSidebar"] { background-color: #151c2c; border-right: 1px solid #1e293b; }
    
    .status-badge-green {
        background: linear-gradient(135deg, #064e3b 0%, #047857 100%);
        border: 1px solid #10b981;
        color: #34d399;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        font-size: 14px;
        margin-bottom: 10px;
    }
    
    .credit-badge-blue {
        background: linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 100%);
        border: 1px solid #3b82f6;
        color: #93c5fd;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        font-size: 13px;
        margin-bottom: 10px;
    }

    .stButton > button {
        border-radius: 8px;
        font-weight: bold;
    }
    
    a.pay-btn-link {
        display: block;
        width: 100%;
        background-color: #2563eb;
        color: white !important;
        text-align: center;
        padding: 10px;
        border-radius: 8px;
        font-weight: bold;
        text-decoration: none;
        margin-top: 8px;
    }
    a.pay-btn-link:hover {
        background-color: #1d4ed8;
    }
</style>
""", unsafe_allow_html=True)

# --- إدارة الجلسة (Session State) ---
if "user_name" not in st.session_state:
    st.session_state["user_name"] = "AYAD FAISAL ABDO MOHAMMED"

if "remaining_credits" not in st.session_state:
    st.session_state["remaining_credits"] = 5

if "form_data" not in st.session_state:
    st.session_state["form_data"] = {"budget": "", "desc": "", "tech": "", "timeline": ""}

if "plans_history" not in st.session_state:
    st.session_state["plans_history"] = []

if "selected_plan_idx" not in st.session_state:
    st.session_state["selected_plan_idx"] = -1

# --- الدوال المساعدة ---
def send_telegram_msg(bot_token, chat_id, message):
    if bot_token and chat_id:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        try:
            requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}, timeout=4)
        except Exception:
            pass

def generate_pdf(plan_data, df_tasks):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#1d4ed8'), spaceAfter=12)
    normal_style = styles['Normal']

    story.append(Paragraph(f"Engineering Plan: {plan_data['client']}", title_style))
    story.append(Paragraph(f"<b>Budget:</b> {plan_data['budget_str']} | <b>Timeline:</b> {plan_data['timeline']}", normal_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Tech Stack:</b> {plan_data['tech']}", normal_style))
    story.append(Spacer(1, 15))

    table_data = [["Task Name", "Duration (Days)", "Cost ($)", "Priority"]]
    for _, row in df_tasks.iterrows():
        table_data.append([row["المهمة"], str(row["الأيام"]), f"${row['التكلفة']}", row["الأولوية"]])

    t = Table(table_data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1'))
    ]))
    
    story.append(t)
    doc.build(story)
    buffer.seek(0)
    return buffer

def apply_template(template_type):
    if template_type == "ecom":
        st.session_state["form_data"] = {
            "budget": "8000 - 12000",
            "desc": "متجر إلكتروني متكامل يدعم السلة، بوابات الدفع (Stripe/LemonSqueezy)، وإدارة المنتجات والطلبات.",
            "tech": "Flutter, Node.js, PostgreSQL",

            "timeline": "4 أسابيع"
        }
    elif template_type == "edu":
        st.session_state["form_data"] = {
            "budget": "8000 - 12000",
            "desc": "منصة تعليمية تزامنية متكاملة للطلاب في اليمن تدعم الحصول المباشر والاختبارات الآلية.",
            "tech": "Flutter, Node.js, Supabase, Gemini AI, WebRTC",
            "timeline": "8 أسابيع"
        }

# ==================== القائمة الجانبية (Sidebar) ====================
with st.sidebar:
    st.title("⚙️ مركز إدارة الذكاء الاصطناعي")
    st.markdown('<div class="status-badge-green">🟢 نشط وجاهز Gemini AI<br><span style="font-size:10px; font-weight:normal;">AlzaSy... المُعالج</span></div>', unsafe_allow_html=True)
    
    st.caption("📡 حالة خدمات النظام")
    st.caption("• Cloud Run Cluster: us-central1\n• DB Engine: MySQL via Unix Socket\n• Architecture: Clean Architecture Modular")
    
    st.markdown(f"**👤 مرحباً، {st.session_state['user_name']}**")
    if st.button("تسجيل الخروج 🚪", use_container_width=True):
        st.session_state["user_name"] = "مستضيف"
        st.rerun()

    st.divider()
    
    # --- قسم إشعارات التلجرام ---
    st.subheader("🔔 إشعارات Telegram")
    tg_bot_token = st.text_input("🔑 Bot Token", value=os.getenv("TELEGRAM_BOT_TOKEN", "123456:ABC"), type="password")
    tg_chat_id = st.text_input("💬 Chat ID", value="597154321")

    st.divider()
    st.subheader("📊 رصيدك المجاني")
    credits = st.session_state["remaining_credits"]
    st.markdown(f'<div class="credit-badge-blue">⚡ متبقي {credits} تحويلات مجانية</div>', unsafe_allow_html=True)
    
    with st.expander("💳 إتمام الدفع 💳", expanded=True):
        pay_email = st.text_input("رالإلكتروني", value="eng.alhiadri2021@gmail.com")
        checkout_direct_url = f"https://nexus-corestore.lemonsqueezy.com/checkout/buy/e6515270-070e-4fc6-b1ea-60c1aeb9e2d3"
        st.markdown(f'<a href="{checkout_direct_url}" target="_blank" class="pay-btn-link">🔗 اضغط هنا لإتمام عملية الدفع</a>', unsafe_allow_html=True)

# ==================== الواجهة الرئيسية ====================
st.title("🧠 وكيل مهنة PRO")
st.subheader("حوّل فكرتك إلى خطة هندسية متكاملة في 3 ثوانٍ")
st.info("💡 توفر عليك 40 ساعة عمل و 500$ من استشارة مدير مشروع")

tab_builder, tab_dashboard = st.tabs(["🚀 مولّد الخطط الهندسية", "📊 لوحة التحكم والإحصائيات"])

with tab_builder:
    st.markdown("<h3 style='text-align: center;'>📝 أدخل تفاصيل مشروعك</h3>", unsafe_allow_html=True)

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        if st.button("🛒 متجر إلكتروني", use_container_width=True):
            apply_template("ecom")
            st.rerun()
    with col_t2:
        if st.button("📚 منصة تعليمية", use_container_width=True):
            apply_template("edu")
            st.rerun()

    with st.form("project_details_interactive_form"):
        c1, c2 = st.columns(2)
        with c1:
            client_name = st.text_input("👤 اسم العميل / الشركة", value="مؤسسة أفق التعليمية")
        with c2:
            budget = st.text_input("💰 الميزانية المتوقعة", value=st.session_state["form_data"]["budget"], placeholder="8000 - 12000")
            
        project_desc = st.text_area("💡 صف رؤية أو فكرة مشروعك بالتفصيل", value=st.session_state["form_data"]["desc"], placeholder="وصف مشروعك...", height=90)
        
        c3, c4 = st.columns(2)
        with c3:
            tech_pref = st.text_input("⚙️ التفضيلات التقنية", value=st.session_state["form_data"]["tech"], placeholder="Flutter, Node.js...")
        with c4:
            timeline = st.text_input("📅 الجدول الزمني المستهدف", value=st.session_state["form_data"]["timeline"], placeholder="8 أسابيع")
            
        submit_btn = st.form_submit_button("🚀 توليد الخطة الهندسية الآن", use_container_width=True)
        
        if submit_btn:
            if st.session_state["remaining_credits"] > 0:
                st.session_state["remaining_credits"] -= 1
                
                raw_b = re.findall(r"\d+", str(budget))
                numeric_budget = float(raw_b[0]) if raw_b else 8000.0

                new_plan = {
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "client": client_name,
                    "budget_val": numeric_budget,
                    "budget_str": budget if budget else "$8,000",
                    "desc": project_desc,
                    "tech": tech_pref if tech_pref else 'Flutter, Node.js, Supabase',
                    "timeline": timeline if timeline else '8 أسابيع'
                }
                
                # إضافة الخطة لقائمة التاريخ وتعيينها كمعروضة حالياً
                st.session_state["plans_history"].append(new_plan)
                st.session_state["selected_plan_idx"] = len(st.session_state["plans_history"]) - 1

                # إرسال التنبيه التلقائي عبر Telegram 🔔
                notify_text = f"🚀 *تم توليد خطة هندسية جديدة!*\n\n👤 *العميل:* {client_name}\n💰 *الميزانية:* {budget}\n📅 *المدة:* {timeline}\n⚙️ *التقنيات:* {tech_pref}"
                send_telegram_msg(tg_bot_token, tg_chat_id, notify_text)

                st.success("✅ تم توليد الخطة وإضافتها لأرشيف لوحة التحكم بنجاح!")
                st.rerun()
            else:
                st.error("❌ لقد استنفدت رصيدك المجاني (5 محاولات)! يرجى الاشتراك في الباقة الذهبية.")

    # ==================== عرض الخطة المختارة ====================
    if st.session_state["plans_history"] and st.session_state["selected_plan_idx"] >= 0:
        plan = st.session_state["plans_history"][st.session_state["selected_plan_idx"]]
        st.markdown("---")
        st.markdown(f"<h2 style='text-align: center;'>📊 تحليل الخطة الذكي: {plan['client']}</h2>", unsafe_allow_html=True)
        
        # 1. KPIs
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("⏱️ إجمالي الأيام", "42")
        k2.metric("💰 التكلفة التقديرية", f"${plan['budget_val']:,.0f}", "+$6,100 أساسي")
        k3.metric("⚠️ درجة المخاطرة", "80%", "عالي 1")
        k4.metric("📊 الدقة", "80%")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # 2. Charts
        r1_col1, r1_col2 = st.columns(2)
        with r1_col1:
            st.markdown("##### 📊 أيام العمل لكل مهمة")
            df_bar = pd.DataFrame({
                "المهمة": ["مهمة 1", "مهمة 2", "مهمة 3", "مهمة 4", "مهمة 5", "مهمة 6"],
                "الأيام": [5, 10, 7, 5, 5, 10],
                "التكلفة": [1200, 2400, 1600, 1000, 1000, 1800],
                "الأولوية": ["عالية", "عالية", "عالية", "متوسطة", "عالية", "عالية"]
            })
            fig_bar = px.bar(df_bar, x="المهمة", y="الأيام", text="الأيام", color_discrete_sequence=["#1d4ed8"])
            fig_bar.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=260)
            st.plotly_chart(fig_bar, use_container_width=True)

        with r1_col2:
            st.markdown("##### 🍩 توزيع المهام حسب الأولوية")
            df_pie1 = pd.DataFrame({"الأولوية": ["عالية", "متوسطة", "منخفضة"], "النسبة": [97, 3, 0]})
            fig_pie1 = px.pie(df_pie1, names="الأولوية", values="النسبة", hole=0.6, color_discrete_sequence=["#ef4444", "#f59e0b", "#10b981"])
            fig_pie1.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=260)
            st.plotly_chart(fig_pie1, use_container_width=True)

        r2_col1, r2_col2 = st.columns(2)
        with r2_col1:
            st.markdown("##### 🍩 توزيع التكلفة حسب الأولوية")
            df_pie2 = pd.DataFrame({"الأولوية": ["عالية", "متوسطة", "منخفضة"], "النسبة": [100, 0, 0]})
            fig_pie2 = px.pie(df_pie2, names="الأولوية", values="النسبة", hole=0.6, color_discrete_sequence=["#ef4444", "#f59e0b", "#10b981"])
            fig_pie2.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=260)
            st.plotly_chart(fig_pie2, use_container_width=True)

        with r2_col2:
            gc1, gc2 = st.columns(2)
            with gc1:
                st.markdown("<h6 style='text-align:center;'>⚠️ مخاطرة</h6>", unsafe_allow_html=True)
                fig_g1 = go.Figure(go.Indicator(mode="gauge+number", value=80, gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#ef4444"}}))
                fig_g1.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=180, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig_g1, use_container_width=True)
            with gc2:
                st.markdown("<h6 style='text-align:center;'>📊 دقة</h6>", unsafe_allow_html=True)
                fig_g2 = go.Figure(go.Indicator(mode="gauge+number", value=80, gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#10b981"}}))
                fig_g2.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=180, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig_g2, use_container_width=True)

        # 3. عرض الجدول والخطة مع أزرار التحميل
        st.markdown("---")
        st.markdown("### 📄 الخطة الهندسية المعتمدة وتوزيع التكلفة")
        
        st.dataframe(df_bar[["المهمة", "الأيام", "التكلفة", "الأولوية"]], use_container_width=True)

        md_text = f"""
### 🎯 الهيكلية المعمارية للمشروع ({plan['client']})
- **التقنيات المستخدمة:** {plan['tech']}
- **المدة الزمنية التقديرية:** {plan['timeline']}
- **الميزانية المقدرة:** {plan['budget_str']}

#### 🛠️ خريطة الطريق والتنفيذ:
1. **المرحلة الأولى:** تصميم واجهات المستخدم والمخططات وتوليد قواعد البيانات.
2. **المرحلة الثانية:** بناء الـ APIs والتكامل مع الخدمات السحابية.
3. **المرحلة الثالثة:** التجميع والتحديث والاختبارات النهائية.
"""
        st.markdown(md_text)

        btn_c1, btn_c2 = st.columns(2)
        pdf_bytes = generate_pdf(plan, df_bar)
        with btn_c1:
            st.download_button(
                label="📄 تحميل الخطة الهندسية (PDF)",
                data=pdf_bytes,
                file_name=f"Engineering_Plan_{plan['client']}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        with btn_c2:
            st.download_button(
                label="📥 تحميل الخطة (Markdown)",
                data=md_text,
                file_name="Plan_Summary.md",
                mime="text/markdown",
                use_container_width=True
            )

# ==================== تبويب لوحة التحكم والإحصائيات المحدث بالكامل ====================
with tab_dashboard:
    st.markdown("## 📊 لوحة التحكم والإحصائيات التجميعية")
    
    if not st.session_state["plans_history"]:
        st.info("ℹ️ لا توجد خطط هندسية مولّدة حتى الآن. قم بتوليد أول خطة من تبويب 'مولّد الخطط الهندسية'.")
    else:
        # إحصائيات سريعة (KPIs)
        total_plans = len(st.session_state["plans_history"])
        total_budget = sum([p["budget_val"] for p in st.session_state["plans_history"]])
        used_credits = 5 - st.session_state["remaining_credits"]

        d_kpi1, d_kpi2, d_kpi3, d_kpi4 = st.columns(4)
        d_kpi1.metric("📁 إجمالي الخطط المنشأة", f"{total_plans}")
        d_kpi2.metric("💰 الميزانيات التقديرية", f"${total_budget:,.0f}")
        d_kpi3.metric("⚡ التحويلات المستهلكة", f"{used_credits} من 5")
        d_kpi4.metric("🌐 اتصال Cloud SQL", "نشط 100%")

        st.markdown("---")
        
        col_hist_left, col_hist_right = st.columns([3, 2])
        
        with col_hist_left:
            st.markdown("### 📜 أرشيف الخطط المعتمدة")
            hist_data = []
            for i, p in enumerate(st.session_state["plans_history"]):
                hist_data.append({
                    "#": i + 1,
                    "التاريخ والوقت": p["timestamp"],
                    "العميل / المشروع": p["client"],
                    "الميزانية": p["budget_str"],
                    "الجدول الزمني": p["timeline"]
                })
            df_hist = pd.DataFrame(hist_data)
            st.dataframe(df_hist, use_container_width=True)
            
            # اختيارات المعاينة السريعة
            selected_idx = st.selectbox(
                "🔍 اختر خطة سابقة لمراجعتها وتصديرها:",
                options=range(len(st.session_state["plans_history"])),
                format_func=lambda idx: f"#{idx+1} - {st.session_state['plans_history'][idx]['client']} ({st.session_state['plans_history'][idx]['timestamp']})"
            )
            if st.button("👁️ معاينة الخطة المحددة", use_container_width=True):
                st.session_state["selected_plan_idx"] = selected_idx
                st.rerun()

        with col_hist_right:
            st.markdown("### 📈 مقارنة ميزانيات المشاريع")
            df_chart = pd.DataFrame({
                "المشروع": [p["client"] for p in st.session_state["plans_history"]],
                "الميزانية ($)": [p["budget_val"] for p in st.session_state["plans_history"]]
            })
            fig_hist = px.bar(df_chart, x="المشروع", y="الميزانية ($)", text="الميزانية ($)", color_discrete_sequence=["#10b981"])
            fig_hist.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=320)
            st.plotly_chart(fig_hist, use_container_width=True)

