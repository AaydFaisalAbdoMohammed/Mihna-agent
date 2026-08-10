#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
© 2026 PHOENIX & MIHNA AGENT PRO ENTERPRISE ARCHITECTURE v14.0 - ULTIMATE SaaS
محرك معالجة البيانات الهجين المتكامل (PostgreSQL / MySQL / SQLite) المعتمد على
جميع جداول الـ Schema، الذكاء الاصطناعي (Gemini)، التوقيع الرقمي (HMAC-SHA512)،
لوحة قيادة المدراء المتقدمة (CEO Admin Dashboard)، مولد الـ QR Code للتسجيل السريع،
التحليلات الهندسية 6D بمؤشرات نصف دائرية ملونة، وحساب أجور الكوادر والمتخصصين.
===============================================================================
"""

import os
import re
import io
import json
import time
import uuid
import hmac
import hashlib
import sqlite3
import logging
import datetime
import requests
import urllib.parse
from urllib.parse import quote_plus

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ----------------- Optional Dependencies Imports -----------------
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False

try:
    import pymysql
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False

try:
    import sqlalchemy
    from sqlalchemy import text
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

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

# =====================================================================
# 1. CONFIGURATION & SETTINGS
# =====================================================================
APP_TITLE = "MIHNA AGENT & PHOENIX PRO - ENTERPRISE v14.0"
PAYMENT_LINK_MONTHLY = os.getenv("PAYMENT_LINK_MONTHLY", "https://nexus-corestore.lemonsqueezy.com/checkout/buy/e6515270-070e-4fc6-b1ea-60c1aeb9e2d3?plan=monthly")
PAYMENT_LINK_YEARLY = os.getenv("PAYMENT_LINK_YEARLY", "https://nexus-corestore.lemonsqueezy.com/checkout/buy/e6515270-070e-4fc6-b1ea-60c1aeb9e2d3?plan=yearly")
SECRET_HMAC_KEY = os.getenv("HMAC_SECRET_KEY", "PHOENIX_SECURE_HMAC_KEY_2026_ENTERPRISE_ULTIMATE")

# App Connection Base URL
APP_BASE_URL = os.getenv("APP_URL", "https://mihna-core-50335759464.asia-south1.run.app")

# Owner & Super Admin Credentials
SUPER_ADMIN_EMAIL = "eng.alhiadri2021@gmail.com"

# Cloud SQL / DB Connection Configuration
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASSWORD", "101519Ayad@%")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_HOST = os.getenv("DB_HOST", "34.93.187.161")
DB_PORT = os.getenv("DB_PORT", "5432")
INSTANCE_CONN = os.getenv("INSTANCE_CONNECTION_NAME", "project-d699d925-921c-4e54-8c4:asia-south1:mihna-core-ay")

# SQLite Fallback DB File
SQLITE_DB_FILE = "phoenix_mihna_hybrid.db"

# =====================================================================
# 2. HYBRID DATABASE ENGINE (PostgreSQL / SQLite Engine)
# =====================================================================
class HybridDatabaseEngine:
    _sqlalchemy_engine = None

    @classmethod
    def get_sqlalchemy_engine(cls):
        if not SQLALCHEMY_AVAILABLE:
            return None
        if cls._sqlalchemy_engine is None:
            try:
                encoded_pass = quote_plus(DB_PASS)
                if os.path.exists(f"/cloudsql/{INSTANCE_CONN}"):
                    db_url = f"postgresql+psycopg2://{DB_USER}:{encoded_pass}@/{DB_NAME}?host=/cloudsql/{INSTANCE_CONN}"
                else:
                    db_url = f"postgresql+psycopg2://{DB_USER}:{encoded_pass}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
                cls._sqlalchemy_engine = sqlalchemy.create_engine(db_url, pool_pre_ping=True)
            except Exception as e:
                logging.error(f"PostgreSQL Engine Error: {e}")
                cls._sqlalchemy_engine = None
        return cls._sqlalchemy_engine

    @classmethod
    def init_db(cls):
        """تهيئة الجداول الأساسية لربط البيانات بشكل متكامل"""
        pg_engine = cls.get_sqlalchemy_engine()
        if pg_engine:
            try:
                with pg_engine.connect() as conn:
                    conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS users (
                            id SERIAL PRIMARY KEY,
                            email VARCHAR(255) UNIQUE NOT NULL,
                            username VARCHAR(100),
                            full_name VARCHAR(255),
                            password_hash VARCHAR(255) NOT NULL,
                            role VARCHAR(100) DEFAULT 'Free Trial',
                            credits INT DEFAULT 5,
                            is_subscribed INT DEFAULT 0,
                            is_admin INT DEFAULT 0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """))
                    conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS project_plans (
                            id SERIAL PRIMARY KEY,
                            user_id INT REFERENCES users(id) ON DELETE CASCADE,
                            project_name VARCHAR(255),
                            domain VARCHAR(255),
                            budget NUMERIC(12,2),
                            target_days INT,
                            risk_tolerance VARCHAR(50),
                            tech_stack TEXT,
                            scope_of_work TEXT,
                            plan_signature TEXT,
                            is_tampered INT DEFAULT 0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """))
                    conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS feedback (
                            id SERIAL PRIMARY KEY,
                            user_email VARCHAR(255) NOT NULL,
                            rating INT DEFAULT 5,
                            suggested_price NUMERIC(10,2) DEFAULT 29.00,
                            requested_feature TEXT,
                            comments TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """))
                    conn.commit()
            except Exception as e:
                logging.error(f"PostgreSQL Init Warning: {e}")

        # Local SQLite
        try:
            conn = sqlite3.connect(SQLITE_DB_FILE)
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE NOT NULL, username TEXT, full_name TEXT, password_hash TEXT NOT NULL, role TEXT DEFAULT 'Free Trial', credits INTEGER DEFAULT 5, is_subscribed INTEGER DEFAULT 0, is_admin INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS project_plans (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, project_name TEXT, domain TEXT, budget REAL, target_days INTEGER, risk_tolerance TEXT, tech_stack TEXT, scope_of_work TEXT, plan_signature TEXT, is_tampered INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT NOT NULL, rating INTEGER DEFAULT 5, suggested_price REAL DEFAULT 29.00, requested_feature TEXT, comments TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

            # Seed CEO Super Admin
            cursor.execute("SELECT email FROM users WHERE email = ?", (SUPER_ADMIN_EMAIL,))
            if not cursor.fetchone():
                hashed_p = hashlib.sha256("123456".encode()).hexdigest()
                cursor.execute(
                    "INSERT INTO users (full_name, username, email, password_hash, credits, role, is_subscribed, is_admin) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    ("Eng. Ayad Al-Hiadri (CEO)", "alhiadri", SUPER_ADMIN_EMAIL, hashed_p, 99999, "Enterprise Owner / Super Admin", 1, 1)
                )
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"SQLite Init Error: {e}")

    @classmethod
    def get_user(cls, email: str) -> dict:
        email_clean = email.strip().lower()
        pg_engine = cls.get_sqlalchemy_engine()
        if pg_engine:
            try:
                with pg_engine.connect() as conn:
                    res = conn.execute(
                        text("SELECT id, email, username, full_name, password_hash, role, credits, is_subscribed, is_admin FROM users WHERE email = :email"),
                        {"email": email_clean}
                    ).fetchone()
                    if res:
                        return {"id": res[0], "email": res[1], "username": res[2], "full_name": res[3], "password_hash": res[4], "role": res[5], "credits": res[6], "is_subscribed": res[7], "is_admin": res[8]}
            except Exception: pass

        try:
            conn = sqlite3.connect(SQLITE_DB_FILE)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email_clean,))
            row = cursor.fetchone()
            conn.close()
            if row:
                d = dict(row)
                return {
                    "id": d["id"], "email": d["email"], "username": d.get("username", ""),
                    "full_name": d["full_name"], "password_hash": d["password_hash"],
                    "role": d["role"], "credits": d["credits"],
                    "is_subscribed": d["is_subscribed"], "is_admin": d.get("is_admin", 0)
                }
        except Exception: pass
        return None

    @classmethod
    def register_user(cls, full_name: str, email: str, password_hash: str) -> bool:
        email_clean = email.strip().lower()
        username = email_clean.split('@')[0]
        success = False
        is_admin_flag = 1 if email_clean == SUPER_ADMIN_EMAIL else 0
        role_flag = "Enterprise Owner / Super Admin" if is_admin_flag else "Free Trial"

        pg_engine = cls.get_sqlalchemy_engine()
        if pg_engine:
            try:
                with pg_engine.connect() as conn:
                    conn.execute(
                        text("INSERT INTO users (full_name, username, email, password_hash, credits, role, is_subscribed, is_admin) VALUES (:fn, :un, :em, :ph, 5, :rl, 0, :ia)"),
                        {"fn": full_name, "un": username, "em": email_clean, "ph": password_hash, "rl": role_flag, "ia": is_admin_flag}
                    )
                    conn.commit()
                    success = True
            except Exception: pass

        try:
            conn = sqlite3.connect(SQLITE_DB_FILE)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (full_name, username, email, password_hash, credits, role, is_subscribed, is_admin) VALUES (?, ?, ?, ?, 5, ?, 0, ?)", (full_name, username, email_clean, password_hash, role_flag, is_admin_flag))
            conn.commit()
            conn.close()
            success = True
        except Exception as e:
            logging.error(f"SQLite Register Error: {e}")

        return success

    @classmethod
    def add_admin_privilege(cls, target_email: str) -> bool:
        target_clean = target_email.strip().lower()
        pg_engine = cls.get_sqlalchemy_engine()
        if pg_engine:
            try:
                with pg_engine.connect() as conn:
                    conn.execute(text("UPDATE users SET is_admin = 1, role = 'Enterprise Admin Supervisor' WHERE email = :email"), {"email": target_clean})
                    conn.commit()
            except Exception: pass

        try:
            conn = sqlite3.connect(SQLITE_DB_FILE)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_admin = 1, role = 'Enterprise Admin Supervisor' WHERE email = ?", (target_clean,))
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    @classmethod
    def update_user_subscription(cls, email: str, role: str, credits: int = 9999) -> bool:
        email_clean = email.strip().lower()
        pg_engine = cls.get_sqlalchemy_engine()
        if pg_engine:
            try:
                with pg_engine.connect() as conn:
                    conn.execute(
                        text("UPDATE users SET role = :role, credits = :credits, is_subscribed = 1 WHERE email = :email"),
                        {"role": role, "credits": credits, "email": email_clean}
                    )
                    conn.commit()
            except Exception: pass

        try:
            conn = sqlite3.connect(SQLITE_DB_FILE)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET role = ?, credits = ?, is_subscribed = 1 WHERE email = ?", (role, credits, email_clean))
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    @classmethod
    def update_credits(cls, email: str, new_credits: int) -> bool:
        email_clean = email.strip().lower()
        pg_engine = cls.get_sqlalchemy_engine()
        if pg_engine:
            try:
                with pg_engine.connect() as conn:
                    conn.execute(text("UPDATE users SET credits = :credits WHERE email = :email"), {"credits": new_credits, "email": email_clean})
                    conn.commit()
            except Exception: pass

        try:
            conn = sqlite3.connect(SQLITE_DB_FILE)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET credits = ? WHERE email = ?", (new_credits, email_clean))
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    @classmethod
    def save_project_plan_full(cls, plan_json: dict, user_email: str) -> bool:
        user = cls.get_user(user_email)
        user_id = user['id'] if user else 1
        p_name = plan_json.get('project_name', 'مشروع جديد')
        domain = plan_json.get('domain', 'تقنية المعلومات')
        budget = float(plan_json.get('budget', 0))
        target_days = int(plan_json.get('target_days', 30))
        risk = plan_json.get('risk', 'متوسط')
        tech = json.dumps(plan_json.get('tech_stack', plan_json.get('tech', '')), ensure_ascii=False)
        scope = plan_json.get('scope', plan_json.get('executive_summary', ''))
        sig = plan_json.get('signature', '')

        pg_engine = cls.get_sqlalchemy_engine()
        if pg_engine:
            try:
                with pg_engine.connect() as conn:
                    conn.execute(
                        text("""INSERT INTO project_plans (user_id, project_name, domain, budget, target_days, risk_tolerance, tech_stack, scope_of_work, plan_signature, is_tampered)
                                VALUES (:uid, :pn, :dm, :bg, :td, :rk, :tc, :sc, :sg, 0)"""),
                        {"uid": user_id, "pn": p_name, "dm": domain, "bg": budget, "td": target_days, "rk": risk, "tc": tech, "sc": scope, "sg": sig}
                    )
                    conn.commit()
            except Exception as e:
                logging.error(f"PG Plan Save Warning: {e}")

        try:
            conn = sqlite3.connect(SQLITE_DB_FILE)
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO project_plans (user_id, project_name, domain, budget, target_days, risk_tolerance, tech_stack, scope_of_work, plan_signature, is_tampered)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)""",
                (user_id, p_name, domain, budget, target_days, risk, tech, scope, sig)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logging.error(f"SQLite Plan Save Error: {e}")
            return False

    @classmethod
    def save_feedback(cls, user_email: str, rating: int, suggested_price: float, requested_feature: str, comments: str) -> bool:
        email_clean = user_email.strip().lower()
        pg_engine = cls.get_sqlalchemy_engine()
        if pg_engine:
            try:
                with pg_engine.connect() as conn:
                    conn.execute(
                        text("INSERT INTO feedback (user_email, rating, suggested_price, requested_feature, comments) VALUES (:em, :rt, :sp, :rf, :cm)"),
                        {"em": email_clean, "rt": rating, "sp": suggested_price, "rf": requested_feature, "cm": comments}
                    )
                    conn.commit()
            except Exception: pass

        try:
            conn = sqlite3.connect(SQLITE_DB_FILE)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO feedback (user_email, rating, suggested_price, requested_feature, comments) VALUES (?, ?, ?, ?, ?)",
                (email_clean, rating, suggested_price, requested_feature, comments)
            )
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    @classmethod
    def get_all_users_admin(cls) -> list:
        users = []
        try:
            conn = sqlite3.connect(SQLITE_DB_FILE)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, full_name, username, email, role, credits, is_subscribed, is_admin, created_at FROM users ORDER BY created_at DESC")
            rows = cursor.fetchall()
            conn.close()
            for r in rows:
                users.append(dict(r))
        except Exception: pass
        return users

    @classmethod
    def get_all_feedback(cls) -> list:
        feedbacks = []
        try:
            conn = sqlite3.connect(SQLITE_DB_FILE)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM feedback ORDER BY created_at DESC")
            rows = cursor.fetchall()
            conn.close()
            for r in rows:
                feedbacks.append(dict(r))
        except Exception: pass
        return feedbacks

HybridDatabaseEngine.init_db()

# =====================================================================
# 3. SECURITY ENGINE & HMAC SIGNATURES
# =====================================================================
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

# =====================================================================
# 4. AI ARCHITECTURE & SPECIALIST PAYROLL ENGINE
# =====================================================================
class PhoenixAI:
    @staticmethod
    def generate_architecture(req: dict, api_key: str = None) -> dict:
        if GEMINI_AVAILABLE and api_key:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-2.5-flash")
                prompt = f"""قم بإنشاء خطة معمارية هندسية بتنسيق JSON للمشروع التالي:
اسم المشروع: {req['project_name']}
المجال: {req['domain']}
الميزانية: {req['budget']}
الأيام المستهدفة: {req['target_days']}
التقنيات: {req['tech_stack']}
نطاق العمل: {req['scope']}

قم بإرجاع JSON فقط يحوي: project_name, domain, budget, target_days, risk, executive_summary, tech_stack (قائمة), tasks (قائمة كائنات بها: id, task, days, cost, status, priority)."""
                response = model.generate_content(prompt)
                match = re.search(r"\{.*\}", response.text, re.DOTALL)
                if match:
                    data = json.loads(match.group())
                    data["scope"] = req['scope']
                    data["signature"] = SecurityEngine.generate_signature(data)
                    data["generated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    return data
            except Exception as e:
                logging.error(f"Gemini API Exception fallback: {e}")

        return PhoenixAI._fallback_architecture(req)

    @staticmethod
    def _fallback_architecture(req: dict) -> dict:
        b = float(req['budget'])
        d = int(req['target_days'])
        tasks = [
            {"id": 1, "task": "تحليل المتطلبات وتصميم المعمارية HLD/LLD", "days": max(1, int(d*0.15)), "cost": int(b*0.15), "status": "مخطط", "priority": "High"},
            {"id": 2, "task": "بناء قواعد البيانات وتأمين APIs RLS Backend", "days": max(1, int(d*0.35)), "cost": int(b*0.35), "status": "مخطط", "priority": "High"},
            {"id": 3, "task": "تطوير واجهات المستخدم Frontend & UI Components", "days": max(1, int(d*0.30)), "cost": int(b*0.30), "status": "مخطط", "priority": "Medium"},
            {"id": 4, "task": "الاختبارات الشاملة QA & Cloud Deployment", "days": max(1, int(d*0.20)), "cost": int(b*0.20), "status": "مخطط", "priority": "Low"}
        ]
        
        tech_list = [t.strip() for t in req['tech_stack'].split(",")] if isinstance(req['tech_stack'], str) else req['tech_stack']

        data = {
            "project_name": req['project_name'],
            "domain": req['domain'],
            "executive_summary": f"خطة هندسية تنفيذية فائقة الدقة لمشروع ({req['project_name']}) بتصميم أمني ومعماري متكامل.",
            "tech": req['tech_stack'],
            "tech_stack": tech_list,
            "scope": req.get('scope', ''),
            "budget": b,
            "target_days": d,
            "risk": req.get('risk', 'متوسط'),
            "tasks": tasks,
            "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        data["signature"] = SecurityEngine.generate_signature(data)
        return data

    @staticmethod
    def calculate_specialists_breakdown(budget: float, target_days: int, domain: str) -> list:
        total_man_hours = target_days * 8
        dev_budget = budget * 0.75

        if "ذكاء" in domain or "SaaS" in domain:
            roles_ratio = [
                {"role": "مهندس المعمارية والذكاء الاصطناعي (AI/Cloud Architect)", "ratio": 0.25, "icon": "🧠"},
                {"role": "مطور خلفية النظم (Senior Backend Engineer)", "ratio": 0.25, "icon": "⚙️"},
                {"role": "مطور واجهات المستخدم (Frontend/Mobile Engineer)", "ratio": 0.20, "icon": "💻"},
                {"role": "مصمم تجربة وواجهة المستخدم (UI/UX Designer)", "ratio": 0.12, "icon": "🎨"},
                {"role": "مهندس جودة واختبار الأمان (QA & Security Engineer)", "ratio": 0.10, "icon": "🛡️"},
                {"role": "مدير المشروع الهندسي (Agile Project Manager)", "ratio": 0.08, "icon": "📊"}
            ]
        else:
            roles_ratio = [
                {"role": "مهندس البرمجيات الرئيسي (Lead Software Engineer)", "ratio": 0.22, "icon": "🏗️"},
                {"role": "مطور خلفية النظم (Backend Developer)", "ratio": 0.26, "icon": "⚙️"},
                {"role": "مطور واجهات التطبيق (Frontend Developer)", "ratio": 0.22, "icon": "💻"},
                {"role": "مصمم واجهات المستخدم (UI/UX Designer)", "ratio": 0.12, "icon": "🎨"},
                {"role": "مهندس فحص الجودة (QA Specialist)", "ratio": 0.10, "icon": "🧪"},
                {"role": "مدير المشروع (Technical Project Manager)", "ratio": 0.08, "icon": "📋"}
            ]

        specialists = []
        for r in roles_ratio:
            allocated_cost = dev_budget * r["ratio"]
            allocated_hours = total_man_hours * r["ratio"]
            allocated_days = allocated_hours / 8
            hourly_rate = allocated_cost / max(1, allocated_hours)
            daily_rate = hourly_rate * 8

            specialists.append({
                "icon": r["icon"],
                "role": r["role"],
                "ratio_pct": round(r["ratio"] * 100, 1),
                "total_cost": round(allocated_cost, 2),
                "total_hours": round(allocated_hours, 1),
                "allocated_days": round(allocated_days, 1),
                "hourly_rate": round(hourly_rate, 2),
                "daily_rate": round(daily_rate, 2)
            })

        return specialists

    @staticmethod
    def analyze_feedback_and_adapt_pricing(feedbacks: list) -> dict:
        if not feedbacks:
            return {
                "recommended_monthly": 29,
                "recommended_yearly": 279,
                "market_satisfaction_score": 93.5
            }
        
        avg_price = np.mean([f['suggested_price'] for f in feedbacks if f['suggested_price'] > 0]) if feedbacks else 29
        avg_rating = np.mean([f['rating'] for f in feedbacks if f.get('rating') is not None]) if feedbacks else 4.5
        
        rec_monthly = max(19, int(avg_price))
        rec_yearly = int(rec_monthly * 9.5)

        return {
            "recommended_monthly": rec_monthly,
            "recommended_yearly": rec_yearly,
            "market_satisfaction_score": round(float(avg_rating) * 20, 1)
        }

# =====================================================================
# 5. UTILITIES & VISUAL GAUGES
# =====================================================================
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

def create_half_doughnut_gauge(val: float, title: str, color: str, prefix: str = "", suffix: str = "", max_val: float = 100):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=val,
        number={'prefix': prefix, 'suffix': suffix, 'font': {'size': 24, 'color': color}},
        title={'text': title, 'font': {'size': 13, 'color': '#94A3B8'}},
        gauge={
            'shape': "angular",
            'axis': {'range': [0, max_val], 'tickwidth': 1, 'tickcolor': "#475569"},
            'bar': {'color': color, 'thickness': 0.75},
            'bgcolor': "rgba(15, 23, 42, 0.6)",
            'bordercolor': "rgba(255,255,255,0.1)",
        }
    ))
    fig.update_layout(
        height=170,
        margin=dict(l=15, r=15, t=25, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#FFFFFF")
    )
    return fig

# =====================================================================
# 6. UI APPLICATION INITIALIZATION
# =====================================================================
def init_session():
    if 'is_authenticated' not in st.session_state: st.session_state.is_authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = {'email': '', 'username': 'زائر', 'credits': 5, 'role': 'Free Trial', 'is_subscribed': False, 'is_admin': False}
    if 'current_plan' not in st.session_state: st.session_state.current_plan = None
    if 'plan_signature' not in st.session_state: st.session_state.plan_signature = None

def render_auth_page():
    st.markdown("<h1 style='text-align: center;'>🚀 بوابة الدخول | MIHNA AGENT & PHOENIX PRO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8;'>قم بتسجيل الدخول أو إنشاء حساب جديد للحصول على 5 محاولات مجانية</p>", unsafe_allow_html=True)
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
                    st.subheader("مرحباً بك!")
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
                                'is_admin': bool(u['is_admin']) or (u['email'] == SUPER_ADMIN_EMAIL)
                            }
                            st.success(f"🎉 أهلاً بك {st.session_state.user['username']}!")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ بيانات الدخول غير صحيحة.")

            with col_l2:
                st.markdown("### 📲 امسح الـ QR للتسجيل السريع")
                clean_base_url = APP_BASE_URL.rstrip('/')
                signup_url = f"{clean_base_url}/?mode=signup"
                qr_bytes = generate_qr_code_image(signup_url)
                if qr_bytes:
                    st.image(qr_bytes, width=170, caption="امسح الرمز للتسجيل المباشر")

        with signup_tab_container:
            with st.form("signup_form"):
                st.subheader("انضم للمنصة الذكية")
                new_username = st.text_input("الاسم الكامل", placeholder="Ayad Al-Hiadri")
                new_email = st.text_input("البريد الإلكتروني", placeholder="name@domain.com").lower().strip()
                new_password = st.text_input("كلمة المرور", type="password", placeholder="••••••••")
                confirm_password = st.text_input("تأكيد كلمة المرور", type="password", placeholder="••••••••")
                submit_signup = st.form_submit_button("✨ إنشاء حساب وتفعيل 5 نقاط مجانية", use_container_width=True)
                
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
                                is_super = (new_email == SUPER_ADMIN_EMAIL)
                                st.session_state.is_authenticated = True
                                st.session_state.user = {
                                    'email': new_email, 'username': new_username, 'credits': 5,
                                    'role': "Enterprise Owner / Super Admin" if is_super else "Free Trial",
                                    'is_subscribed': False, 'is_admin': is_super
                                }
                                st.balloons()
                                st.success("🎉 تم إنشاء الحساب بنجاح!")
                                time.sleep(0.8)
                                st.rerun()

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
        st.session_state.user['is_admin'] = bool(fresh_u['is_admin']) or (fresh_u['email'] == SUPER_ADMIN_EMAIL)

    with st.sidebar:
        st.title("🛡️ MIHNA AGENT")
        st.caption("Enterprise Architecture v14.0")
        st.divider()

        st.markdown(f"👤 المستخدم: **{st.session_state.user['username']}**")
        if st.session_state.user['is_subscribed']:
            st.markdown(f"الاشتراك: **{st.session_state.user['role']}**")
            st.markdown("الرصيد: **غير محدود ♾️**")
        else:
            st.markdown(f"الرصيد المتاح: `{st.session_state.user['credits']}` نقاط")

        if st.button("🚪 تسجيل الخروج", use_container_width=True):
            st.session_state.clear()
            st.rerun()

        st.divider()
        all_fb = HybridDatabaseEngine.get_all_feedback()
        adapted_insights = PhoenixAI.analyze_feedback_and_adapt_pricing(all_fb)

        st.markdown(f'<a href="{PAYMENT_LINK_MONTHLY}" target="_blank" style="display:block; text-align:center; background:#2563EB; color:white; padding:10px; border-radius:8px; font-weight:bold; text-decoration:none;">💳 ترقية باقة Pro (${adapted_insights["recommended_monthly"]}/شهر)</a>', unsafe_allow_html=True)

    st.title("🚀 وكيل مهنة PRO | MIHNA AGENT & PHOENIX Enterprise")
    st.caption("المنصة المتقدمة لهندسة خطط المشاريع وحساب أجور المتخصصين ببيئة أمان HMAC-SHA512")

    is_ceo_owner = (st.session_state.user['email'] == SUPER_ADMIN_EMAIL) or st.session_state.user['is_admin']
    
    if is_ceo_owner:
        tab1, tab2, tab3, tab4, tab_admin = st.tabs([
            "🏗️ بناء الخطة والكوادر", "📊 التحليلات التفاعلية 6D", "🔄 التغذية الراجعة والنجوم", "💳 الحساب والاشتراكات", "👑 لوحة الإدارة العليا (CEO Panel)"
        ])
    else:
        tab1, tab2, tab3, tab4 = st.tabs([
            "🏗️ بناء الخطة والكوادر", "📊 التحليلات التفاعلية 6D", "🔄 التغذية الراجعة والنجوم", "💳 الحساب والاشتراكات"
        ])

    # TAB 1: BUILD PLAN
    with tab1:
        with st.form("project_form"):
            col1, col2 = st.columns(2)
            with col1:
                project_name = st.text_input("اسم المشروع", value="منصة تجارة سحابية الذكية")
                domain = st.selectbox("المجال التقني", ["التجارة الإلكترونية", "التعليم الرقمي", "الخدمات واللوجستيات", "الذكاء الاصطناعي", "أنظمة SaaS"])
                budget = st.number_input("الميزانية التقديرية ($)", min_value=500, value=3500)
            with col2:
                tech_stack = st.text_input("التقنيات المستخدمة", value="Flutter, Node.js, PostgreSQL, Supabase")
                target_days = st.number_input("المدة الزمنية (يوم)", min_value=5, value=30)
                risk_tolerance = st.select_slider("تحمل المخاطر", options=["منخفض جداً", "متوسط", "عالي"])

            project_scope = st.text_area("نطاق العمل (Scope of Work)", placeholder="اكتب تفاصيل ومتطلبات المشروع هنا...")
            gemini_key = st.text_input("مفتاح Gemini API (اختياري للذكاء الاصطناعي المباشر)", type="password")

            submit_btn = st.form_submit_button("🚀 توليد الخطة وحساب الكوادر (1 نقطة)", use_container_width=True)

        if submit_btn:
            if st.session_state.user['credits'] < 1 and not st.session_state.user['is_subscribed']:
                st.error("❌ لقد استنفدت نقاطك المجانية! يرجى الترقية للاستمرار.")
            else:
                with st.spinner("⏳ جاري تحليل المتطلبات، توزيع الكوادر، والتوقيع الرقمي..."):
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
                    st.success("✅ تم توليد الخطة وحساب الكوادر وتوقيعها رقمياً بنجاح!")

        if st.session_state.current_plan:
            st.divider()
            st.info(f"🔑 **التوقيع الرقمي المشفر (HMAC-SHA512):**\n`{st.session_state.plan_signature}`")

            st.markdown("### 👥 الكوادر والمتخصصون المطلوبون وأجورهم المخصصة")
            specs = PhoenixAI.calculate_specialists_breakdown(
                st.session_state.current_plan['budget'],
                st.session_state.current_plan['target_days'],
                st.session_state.current_plan['domain']
            )
            st.dataframe(pd.DataFrame(specs)[["icon", "role", "total_cost", "total_hours", "hourly_rate", "daily_rate", "ratio_pct"]], use_container_width=True)

            st.markdown("### 📋 مراحل ونطاق المهام الفنية")
            df_tasks = pd.DataFrame(st.session_state.current_plan.get('tasks', []))
            st.dataframe(df_tasks, use_container_width=True)

    # TAB 2: ANALYTICS 6D
    with tab2:
        if not st.session_state.current_plan:
            st.info("💡 قم بتوليد خطة مشروع أولاً لعرض التحليلات الهندسية.")
        else:
            plan = st.session_state.current_plan
            p_budget = float(plan['budget'])
            p_days = int(plan['target_days'])
            p_hours = p_days * 8
            daily_cost = p_budget / max(1, p_days)

            g_col1, g_col2, g_col3 = st.columns(3)
            with g_col1:
                st.plotly_chart(create_half_doughnut_gauge(daily_cost, "💰 التكلفة اليومية الكلية", "#3B82F6", prefix="$", suffix="/يوم", max_val=daily_cost*2), use_container_width=True)
            with g_col2:
                st.plotly_chart(create_half_doughnut_gauge(p_hours, "⏱️ ساعات العمل الهندسية", "#8B5CF6", suffix=" ساعة", max_val=p_hours*1.5), use_container_width=True)
            with g_col3:
                st.plotly_chart(create_half_doughnut_gauge(p_days, "📅 الأيام المستهدفة", "#06B6D4", suffix=" يوم", max_val=p_days*1.5), use_container_width=True)

    # TAB 3: FEEDBACK & LIVE STARS
    with tab3:
        st.subheader("🔄 تقييم المنصة وإبداء الرأي")
        st.markdown("**حدد تقييمك بالنجوم (احصل على 1 نقطة إضافية):**")
        stars_selection = st.feedback("stars")
        rating_stars = (stars_selection + 1) if stars_selection is not None else 5

        with st.form("feedback_form"):
            suggested_p = st.number_input("ما هو السعر الشهري العادل من وجهة نظرك؟ ($)", min_value=5, max_value=200, value=29)
            req_feature = st.selectbox("الميزة الأكثر أهمية للخدمة", ["تصدير تقارير احترافية بالعربية PDF", "ربط أوتوماتيكي مع Cloud SQL", "إشعارات فورية عبر الواتساب والتليجرام"])
            comments = st.text_area("ملاحظات إضافية لتطوير المنصة")
            submit_fb = st.form_submit_button("🚀 إرسال التقييم وتحديث الرصيد")

            if submit_fb:
                if HybridDatabaseEngine.save_feedback(st.session_state.user['email'], rating_stars, suggested_p, req_feature, comments):
                    new_c = st.session_state.user['credits'] + 1
                    HybridDatabaseEngine.update_credits(st.session_state.user['email'], new_c)
                    st.session_state.user['credits'] = new_c
                    st.balloons()
                    st.success("🎉 شكراً لك! تم إضافة 1 نقطة مجانية لحسابك.")
                    time.sleep(1)
                    st.rerun()

    # TAB 4: ACCOUNT
    with tab4:
        st.subheader("👤 بيانات الحساب والاشتراك")
        st.write(f"**الاسم:** {st.session_state.user['username']}")
        st.write(f"**البريد:** {st.session_state.user['email']}")
        st.write(f"**نوع الحساب:** {st.session_state.user['role']}")
        st.write(f"**الرصيد الحالي:** {st.session_state.user['credits']} نقطة")

    # TAB ADMIN: CEO CONTROL CENTER
    if is_ceo_owner:
        with tab_admin:
            st.subheader("👑 لوحة الإدارة العليا (CEO Panel)")
            all_users = HybridDatabaseEngine.get_all_users_admin()
            
            st.markdown("### 🔑 إضافة صلاحية مشرف جديد")
            col_add1, col_add2 = st.columns([2, 1])
            with col_add1:
                target_email = st.text_input("البريد الإلكتروني للترقية لمشرف", placeholder="supervisor@domain.com").lower().strip()
            with col_add2:
                st.write("<br>", unsafe_allow_html=True)
                if st.button("✨ تفعيل المشرف", use_container_width=True):
                    if target_email and HybridDatabaseEngine.add_admin_privilege(target_email):
                        st.success(f"✅ تم تفعيل صلاحية المشرف لـ {target_email}")
                        time.sleep(1)
                        st.rerun()

            st.markdown("### 📋 سجل جميع المستخدمين والاشتراكات")
            if all_users:
                st.dataframe(pd.DataFrame(all_users)[["id", "full_name", "username", "email", "role", "credits", "is_subscribed", "is_admin", "created_at"]], use_container_width=True)

if __name__ == "__main__":
    main()
