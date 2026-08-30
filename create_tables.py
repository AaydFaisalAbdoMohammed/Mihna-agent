import os
os.environ["DB_ENGINE_TYPE"] = "mysql"

from db import HybridDatabaseEngine

def run():
    print("⏳ جاري تهيئة الجداول وهيكلة قاعدة البيانات (MySQL / Hybrid)...")
    try:
        HybridDatabaseEngine.init_db()
        print("✅ تم إنشاء وتجهيز كافة الجداول بنجاح!")
    except Exception as e:
        print(f"❌ حدث خطأ أثناء تنفيذ التهيئة: {e}")

if __name__ == "__main__":
    run()
