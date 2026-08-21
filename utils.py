#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import io
import re
import json
import hmac
import hashlib
import datetime
import urllib.parse
import pandas as pd
import plotly.graph_objects as go

# Optional Dependencies
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False

try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    ARABIC_PDF_AVAILABLE = True
except ImportError:
    ARABIC_PDF_AVAILABLE = False

# Global Links & Secrets
PAYMENT_LINK_MONTHLY = os.getenv("PAYMENT_LINK_MONTHLY", "https://nexus-corestore.lemonsqueezy.com/checkout/buy/e6515270-070e-4fc6-b1ea-60c1aeb9e2d3?plan=monthly")
PAYMENT_LINK_YEARLY = os.getenv("PAYMENT_LINK_YEARLY", "https://nexus-corestore.lemonsqueezy.com/checkout/buy/e6515270-070e-4fc6-b1ea-60c1aeb9e2d3?plan=yearly")
SECRET_HMAC_KEY = os.getenv("HMAC_SECRET_KEY", "PHOENIX_SECURE_HMAC_KEY_2026_ENTERPRISE_ULTIMATE")
APP_BASE_URL = os.getenv("APP_URL", "https://mihna-core-50335759464.asia-south1.run.app")

class SecurityEngine:
    @staticmethod
    def hash_password(password: str) -> str:
        if BCRYPT_AVAILABLE:
            salt = bcrypt.gensalt()
            return bcrypt.hashpw(password.encode(), salt).decode()
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        if BCRYPT_AVAILABLE and hashed.startswith("$2b$"):
            try:
                return bcrypt.checkpw(password.encode(), hashed.encode())
            except Exception:
                return False
        return hashlib.sha256(password.encode()).hexdigest() == hashed

    @staticmethod
    def generate_signature(data_dict: dict) -> str:
        clean_payload = {k: v for k, v in data_dict.items() if k not in ["signature", "timestamp", "is_tampered"]}
        serialized = json.dumps(clean_payload, sort_keys=True, ensure_ascii=False)
        return hmac.new(SECRET_HMAC_KEY.encode(), serialized.encode(), hashlib.sha512).hexdigest()

    @staticmethod
    def verify_signature(data_dict: dict, signature: str) -> bool:
        if not signature:
            return False
        expected_sig = SecurityEngine.generate_signature(data_dict)
        return hmac.compare_digest(expected_sig, signature)

class NotificationEngine:
    @staticmethod
    def create_whatsapp_link(phone: str, message: str) -> str:
        encoded_msg = urllib.parse.quote(message)
        clean_phone = re.sub(r'[^\d]', '', str(phone))
        return f"https://wa.me/{clean_phone}?text={encoded_msg}"

def generate_qr_code_image(target_url: str) -> bytes:
    if QRCODE_AVAILABLE:
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(target_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#1E293B", back_color="#FFFFFF")
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return buf.getvalue()
    return b""

def generate_excel_download(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    if OPENPYXL_AVAILABLE:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Project Tasks')
        return output.getvalue()
    else:
        return df.to_csv(index=False).encode('utf-8')

def generate_pdf_plan(plan: dict, signature: str, detailed_text: str) -> bytes:
    buffer = io.BytesIO()
    if not REPORTLAB_AVAILABLE:
        buffer.write(detailed_text.encode('utf-8'))
        return buffer.getvalue()

    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()

    def prepare_text(text_val):
        if ARABIC_PDF_AVAILABLE:
            try:
                reshaped = arabic_reshaper.reshape(text_val)
                return get_display(reshaped)
            except Exception:
                return text_val
        return text_val

    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, alignment=1)
    body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=10, leading=14, alignment=2)

    story.append(Paragraph(prepare_text(f"خطة مشروع: {plan['project_name']}"), title_style))
    story.append(Spacer(1, 15))
    
    info_text = f"المجال التقني: {plan['domain']} | الميزانية: ${plan['budget']} | المدة: {plan['target_days']} يوم"
    story.append(Paragraph(prepare_text(info_text), body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph(prepare_text("--- تفاصيل الخطة التنفيذية والكوادر المخصصة ---"), title_style))
    for line in detailed_text.split("\n"):
        if line.strip():
            story.append(Paragraph(prepare_text(line.strip()), body_style))
            story.append(Spacer(1, 4))

    story.append(Spacer(1, 15))
    story.append(Paragraph(prepare_text(f"التوقيع الرقمي HMAC-SHA512: {signature[:40]}..."), body_style))

    doc.build(story)
    return buffer.getvalue()

def build_detailed_plan_text(plan: dict) -> str:
    from ai import PhoenixAI
    p_name = plan.get('project_name', 'المشروع')
    domain = plan.get('domain', 'تقني')
    budget = float(plan.get('budget', 0))
    days = int(plan.get('target_days', 0))
    tech = plan.get('tech', plan.get('tech_stack', 'Flutter, Node.js, Supabase, PostgreSQL'))
    risk = plan.get('risk', 'متوسط')
    tasks = plan.get('tasks', [])
    
    working_hours_per_day = 8
    total_man_hours = days * working_hours_per_day
    daily_rate = budget / max(1, days)
    hourly_rate = budget / max(1, total_man_hours)
    
    contingency_rate = 0.15 if risk == "عالي" else (0.10 if risk == "متوسط" else 0.05)
    contingency_amount = budget * contingency_rate
    effective_operational_budget = budget - contingency_amount
    
    cloud_infra_cost = budget * 0.10
    dev_labor_cost = effective_operational_budget - cloud_infra_cost

    specialists = PhoenixAI.calculate_specialists_breakdown(budget, days, domain)
    specialists_str = ""
    for s in specialists:
        specialists_str += f"""
* {s['icon']} **{s['role']}**
  * ⏱️ **إجمالي الساعات:** {s['total_hours']} ساعة ({s['allocated_days']} أيام عمل)
  * 💵 **أجر الساعة الهندسية:** ${s['hourly_rate']:,.2f} / ساعة | **اليومي:** ${s['daily_rate']:,.2f} / يوم
  * 💰 **إجمالي المستحقات:** `${s['total_cost']:,.2f}` ({s['ratio_pct']}% من ميزانية الكوادر)
"""

    tasks_breakdown_str = ""
    for idx, t in enumerate(tasks, 1):
        t_cost = float(t.get('cost', 0))
        t_days = int(t.get('days', t.get('estimated_days', 1)))
        t_hours = t_days * working_hours_per_day
        cost_percentage = (t_cost / max(1, budget)) * 100
        daily_t_cost = t_cost / max(1, t_days)
        hourly_t_cost = t_cost / max(1, t_hours)
        
        tasks_breakdown_str += f"""
#### Phase {idx}: {t.get('task', t.get('title', 'مهمة'))}
* ⏱️ **المدة الزمنية:** {t_days} أيام عمل ({t_hours} ساعة هندسية)
* 💰 **التكلفة المخصصة:** ${t_cost:,.2f} ({cost_percentage:.1f}% من إجمالي الميزانية)
* 📊 **المعدل اليومي للإنفاق:** ${daily_t_cost:,.2f} / يوم | **الساعة:** ${hourly_t_cost:,.2f} / ساعة
* 📌 **الحالة التنفيذية:** {t.get('status', 'مخطط')}
"""

    return f"""📌 **المستند التنفيذي والهندسي المتكامل لمشروع ({p_name})**
*تاريخ التوليد والتوقيع الرقمي: {plan.get('generated_at', datetime.datetime.now().strftime('%Y-%m-%d'))}*

---

### 1. نظرة عامة والأهداف التنفيذية (Executive Summary & KPIs)
يهدف مشروع **{p_name}** إلى تقديم حل سحابي برمجي فائق الأداء في قطاع **{domain}**، معتمداً على البيئة والتقنيات: **({tech})**.
* **الميزانية الكلية (Total Budget):** `${budget:,.2f}`
* **المدى الزمني المستهدف (Timeline):** `{days}` يوماً تقويمياً.
* **مستوى تحمل المخاطر (Risk Profile):** `{risk}`.

---

### 2. توزيع الكوادر والتخصصات الهندسية وأجورهم (Engineering Specialists & Payroll Allocation)
تم استخدام خوارزمية **Phoenix Resource Allocation Engine** لتحديد الكوادر الدقيقة المطلوبة وحساب أجورهم:
{specialists_str}

---

### 3. الحسابات المالية والهندسية التفصيلية (Precise Cost & Time Allocation)
* ⏳ **إجمالي الساعات الهندسية (Total Man-Hours):** `{total_man_hours:,}` ساعة عمل ({working_hours_per_day} ساعات/يوم).
* 💵 **معدل التكلفة اليومي الكلي:** `${daily_rate:,.2f}` / يوم.
* ⏱️ **معدل تكلفة الساعة الهندسية:** `${hourly_rate:,.2f}` / ساعة.
* 🛡️ **احتياطي الطوارئ والمخاطر ({contingency_rate*100:.0f}% Risk Reserve):** `${contingency_amount:,.2f}`.
* ☁️ **تكاليف البنية التحتية والاستضافة Cloud Infrastructure:** `${cloud_infra_cost:,.2f}`.
* 🛠️ **صافي ميزانية تطوير الكوادر (Effective Dev Budget):** `${dev_labor_cost:,.2f}`.

---

### 4. التفصيل المرحلي للمهام (Work Breakdown Structure)
{tasks_breakdown_str}

---

### 5. مصفوفة الأمان والتوقيع الرقمي المشفر (Digital HMAC Signature)
* **التوقيع الرقمي:** تم توقيع هذه الخطة رسمياً وحفظها في قاعدة بيانات Cloud SQL.
* **تشفير HMAC-SHA512:** المعيار السري المعتمد في المؤسسة.
"""

def create_half_doughnut_gauge(val: float, title: str, color: str, prefix: str = "", suffix: str = "", max_val: float = 100):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=val,
        number={'prefix': prefix, 'suffix': suffix, 'font': {'size': 26, 'color': color}},
        title={'text': title, 'font': {'size': 14, 'color': '#94A3B8'}},
        gauge={
            'shape': "angular",
            'axis': {'range': [0, max_val], 'tickwidth': 1, 'tickcolor': "#475569"},
            'bar': {'color': color, 'thickness': 0.75},
            'bgcolor': "rgba(15, 23, 42, 0.6)",
            'bordercolor': "rgba(255,255,255,0.1)",
        }
    ))
    fig.update_layout(
        height=180,
        margin=dict(l=15, r=15, t=30, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#FFFFFF")
    )
    return fig
