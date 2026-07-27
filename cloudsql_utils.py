#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import mysql.connector
from mysql.connector import Error
import streamlit as st

CLOUD_SQL_CONNECTION_NAME = os.getenv("CLOUD_SQL_CONNECTION_NAME", "project-d699d925-921c-4e54-8c4:asia-south1:mihna-agent")
DB_USER = os.getenv("DB_USER", "mihna.app.user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "101519Ayad@")
DB_NAME = os.getenv("DB_NAME", "mihna_agent")

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            unix_socket=f"/cloudsql/{CLOUD_SQL_CONNECTION_NAME}",
            connect_timeout=10,
            use_pure=True
        )
        if conn.is_connected():
            return conn
        st.error("⚠️ الاتصال بقاعدة البيانات غير نشط")
        return None
    except Error as e:
        st.error(f"❌ فشل الاتصال بقاعدة البيانات (Socket): {e}")
        return None
    except Exception as e:
        st.error(f"❌ خطأ غير متوقع: {e}")
        return None

def save_to_cloudsql(project_data, user_id=None):
    if user_id is None:
        user_id = st.session_state.get("user_id")
    if user_id is None:
        st.error("⚠️ يجب تسجيل الدخول أولاً")
        return False
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            conn.close()
            st.error("⚠️ المستخدم غير موجود")
            return False
        cursor.execute("""
            INSERT INTO projects (user_id, client_name, summary, tech_stack, budget_range) 
            VALUES (%s, %s, %s, %s, %s)
        """, (
            user_id,
            project_data.get('client_name', 'عميل غير معروف'),
            project_data.get('project_summary', 'لا يوجد ملخص'),
            json.dumps(project_data.get('suggested_tech_stack', [])),
            project_data.get('estimated_budget_range', 'غير محدد')
        ))
        project_id = cursor.lastrowid
        for task in project_data.get('generated_tasks', []):
            cursor.execute("""
                INSERT INTO tasks (project_id, title, description, estimated_days, priority) 
                VALUES (%s, %s, %s, %s, %s)
            """, (
                project_id,
                task.get('title', 'مهمة بدون عنوان'),
                task.get('description', 'لا يوجد وصف'),
                task.get('estimated_days', 2),
                task.get('priority', 'Medium')
            ))
        conn.commit()
        conn.close()
        return True
    except Error as e:
        st.error(f"❌ خطأ في حفظ المشروع: {e}")
        conn.close()
        return False

def get_similar_projects(idea: str, top_k: int = 3) -> list:
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, client_name, summary, tech_stack 
            FROM projects 
            WHERE summary LIKE %s 
            LIMIT %s
        """, (f"%{idea}%", top_k))
        results = cursor.fetchall()
        conn.close()
        return results
    except Error as e:
        st.error(f"⚠️ فشل البحث عن مشاريع مشابهة: {e}")
        conn.close()
        return []

def get_all_projects(user_id=None):
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        if user_id:
            cursor.execute("""
                SELECT id, client_name, summary, tech_stack, budget_range, created_at 
                FROM projects 
                WHERE user_id = %s
                ORDER BY created_at DESC
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT id, client_name, summary, tech_stack, budget_range, created_at 
                FROM projects 
                ORDER BY created_at DESC
            """)
        results = cursor.fetchall()
        conn.close()
        return results
    except Error as e:
        st.error(f"⚠️ فشل استرجاع المشاريع: {e}")
        conn.close()
        return []
