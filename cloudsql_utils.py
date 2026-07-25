#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import mysql.connector
from mysql.connector import Error
import streamlit as st

def get_db_connection():
    db_host = os.getenv("DB_HOST", "8.231.102.92")
    db_user = os.getenv("DB_USER", "mihna.app.user")
    db_pass = os.getenv("DB_PASSWORD", "101519Ayad@")
    db_name = os.getenv("DB_NAME", "mihna_agent")
    db_port = int(os.getenv("DB_PORT", 3306))
    
    # المحاولة الأولى: الاتصال المباشر عبر TCP / IP
    try:
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_pass,
            database=db_name,
            port=db_port,
            connect_timeout=5,
            use_pure=True
        )
        if conn.is_connected():
            return conn
    except Exception as e_tcp:
        # المحاولة الثانية: الاتصال عبر Socket إذا كان معرفاً
        cloud_sql_socket = os.getenv("DB_SOCKET", "/cloudsql/project-d699d925-921c-4e54-8c4:us-central1:mihna-agent")
        if os.path.exists(cloud_sql_socket):
            try:
                conn = mysql.connector.connect(
                    user=db_user,
                    password=db_pass,
                    database=db_name,
                    unix_socket=cloud_sql_socket,
                    connect_timeout=5,
                    use_pure=True
                )
                if conn.is_connected():
                    return conn
            except Exception:
                pass
        
        # إظهار رسالة تنبيهية واضحة بدون تعطيل واجهة المستخدم
        st.warning(f"⚠️ يتعذر الاتصال الخارجي بقاعدة البيانات حالياً ({e_tcp}). تم تفعيل وضع الاستجابة المرن.")
        return None

def save_to_cloudsql(project_data, user_id=None):
    if user_id is None:
        user_id = st.session_state.get("user_id")
    if user_id is None:
        st.error("⚠️ يجب تسجيل الدخول أولاً")
        return False
    conn = get_db_connection()
    if not conn:
        return True # السماح للمستخدم بالمتابعة في الجلسة المحلية
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            conn.close()
            return True
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
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        if conn:
            conn.close()
        return True

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
    except Exception:
        if conn:
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
    except Exception:
        if conn:
            conn.close()
        return []
