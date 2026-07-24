#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cloud SQL Utilities - دوال مساعدة للاتصال بقاعدة البيانات
"""

import os
import json
import sys
import mysql.connector
from mysql.connector import Error

def get_db_connection():
    """
    إنشاء اتصال بقاعدة بيانات Cloud SQL مع مهلة زمنية ومعالجة أخطاء مفصلة.
    """
    # قراءة بيانات الاتصال من متغيرات البيئة أو استخدام القيم الافتراضية
    host = os.getenv("DB_HOST", "8.231.102.92")
    user = os.getenv("DB_USER", "mihna-app-user")
    password = os.getenv("DB_PASSWORD", "101519Ayad@")
    database = os.getenv("DB_NAME", "mihna-agent")
    port = os.getenv("DB_PORT", 3306)
    
    print(f"🔍 محاولة الاتصال بـ: host={host}, user={user}, database={database}, port={port}")
    
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
            connect_timeout=10,
            connection_timeout=10,
            use_pure=True,
            ssl_disabled=False  # تأكد من استخدام SSL إذا كان مطلوباً
        )
        if conn.is_connected():
            print("✅ تم الاتصال بقاعدة البيانات بنجاح!")
            return conn
        else:
            print("⚠️ الاتصال بقاعدة البيانات غير نشط")
            return None
    except Error as e:
        print(f"❌ فشل الاتصال بقاعدة البيانات: {e}")
        print(f"   - رقم الخطأ: {e.errno}")
        print(f"   - رسالة الخطأ: {e.msg}")
        return None
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {e}")
        return None

def save_to_cloudsql(project_data, user_id=None):
    """
    حفظ خطة المشروع في Cloud SQL.
    """
    if user_id is None:
        try:
            import streamlit as st
            user_id = st.session_state.get("user_id")
        except:
            user_id = None
    
    if user_id is None:
        print("⚠️ user_id غير موجود في الجلسة")
        return False
    
    conn = get_db_connection()
    if not conn:
        print("⚠️ تعذر الاتصال بقاعدة البيانات")
        return False
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # التحقق من وجود المستخدم
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            print(f"⚠️ المستخدم {user_id} غير موجود")
            conn.close()
            return False
        
        # إدراج المشروع
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
        
        # إدراج المهام
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
        print(f"✅ تم حفظ المشروع (ID: {project_id}) بنجاح")
        return True
    except Error as e:
        print(f"❌ خطأ في حفظ المشروع: {e}")
        conn.close()
        return False

def get_similar_projects(idea: str, top_k: int = 3) -> list:
    """
    استرجاع مشاريع سابقة مشابهة باستخدام البحث النصي.
    """
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
        print(f"⚠️ فشل البحث عن مشاريع مشابهة: {e}")
        conn.close()
        return []

def get_all_projects(user_id=None):
    """
    استرجاع جميع مشاريع المستخدم (أو الكل إذا لم يُحدد مستخدم).
    """
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
        print(f"⚠️ فشل استرجاع المشاريع: {e}")
        conn.close()
        return []

print("✅ تم تحميل cloudsql_utils.py بنجاح!")
