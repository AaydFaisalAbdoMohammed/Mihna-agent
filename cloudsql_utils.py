import os
import json
import mysql.connector
from mysql.connector import Error

def get_db_connection():
    """إنشاء اتصال بقاعدة البيانات مع مهلة زمنية."""
    import mysql.connector
    import os
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "8.231.102.92"),
            user=os.getenv("DB_USER", "mihna_user"),
            password=os.getenv("DB_PASSWORD", "Mihna@2026Secure!"),
            database=os.getenv("DB_NAME", "mihna_db"),
            port=os.getenv("DB_PORT", 3306),
            connect_timeout=10,  # مهلة 10 ثواني
            connection_timeout=10
        )
    except Exception as e:
        print(f"⚠️ فشل الاتصال بقاعدة البيانات: {e}")
        return Nonedef save_to_cloudsql(project_data, user_email="guest@example.com"):
    """حفظ بيانات المشروع والمهام في Cloud SQL مع الحفاظ على البيانات السابقة"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # 1. جلب أو إنشاء المستخدم 
        cursor.execute("SELECT id FROM users WHERE email = %s", (user_email,))
        user = cursor.fetchone()
        
        if not user:
            cursor.execute(
                "INSERT INTO users (email, name, free_uses) VALUES (%s, %s, %s)",
                (user_email, project_data.get('client_name', 'عميل جديد'), 5)
            )
            user_id = cursor.lastrowid
        else:
            user_id = user[0]

        # 2. إدراج المشروع
        cursor.execute(
            """
            INSERT INTO projects (user_id, client_name, summary, tech_stack, budget_range)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                user_id,
                project_data.get('client_name', 'غير محدد'),
                project_data.get('project_summary', 'لا يوجد ملخص'),
                json.dumps(project_data.get('suggested_tech_stack', [])),
                project_data.get('estimated_budget_range', 'غير محدد')
            )
        )
        project_id = cursor.lastrowid

        # 3. إدراج المهام المرتبطة
        for task in project_data.get('generated_tasks', []):
            cursor.execute(
                """
                INSERT INTO tasks (project_id, title, description, estimated_days, priority)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    project_id,
                    task.get('title', 'مهمة جديدة'),
                    task.get('description', ''),
                    task.get('estimated_days', 1),
                    task.get('priority', 'medium')
                )
            )
        
        # تأكيد الحفظ
        conn.commit()
        print(f"✅ تم حفظ المشروع والمهام بنجاح في Cloud SQL (ID: {project_id})")
        return True
        
    except Error as e:
        # التراجع في حال حدوث خطأ للحفاظ على تناسق البيانات وعدم وجود بيانات جزئية
        conn.rollback()
        print(f"❌ فشل الحفظ في Cloud SQL: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        conn.close()

def get_similar_projects(idea, top_k=3):
    """(RAG) استرجاع مشاريع سابقة مشابهة باستخدام البحث النصي"""
    conn = get_db_connection()
    if not conn:
        return []
        
    try:
        # استخدام القواميس لسهولة التعامل مع البيانات لاحقاً
        cursor = conn.cursor(dictionary=True) 
        cursor.execute(
            """
            SELECT client_name, summary, tech_stack 
            FROM projects 
            WHERE summary LIKE %s 
            LIMIT %s
            """,
            (f"%{idea}%", top_k)
        )
        results = cursor.fetchall()
        return results
    except Error as e:
        print(f"⚠️ فشل البحث عن مشاريع مشابهة: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        conn.close()
