"""
数据库迁移脚本 - 为validation_history表添加trigger_type字段
"""
import sqlite3
import os

# 获取项目根目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
DATABASE_PATH = os.path.join(PROJECT_ROOT, 'config', 'dataq.db')

def migrate():
    """执行迁移"""
    print(f"开始迁移数据库: {DATABASE_PATH}")
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # 检查trigger_type列是否已存在
        cursor.execute("PRAGMA table_info(validation_history)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'trigger_type' not in columns:
            print("添加 trigger_type 字段...")
            cursor.execute("""
                ALTER TABLE validation_history 
                ADD COLUMN trigger_type VARCHAR(20) NOT NULL DEFAULT 'manual'
            """)
            print("✅ trigger_type 字段添加成功")
        else:
            print("⚠️  trigger_type 字段已存在，跳过")
        
        conn.commit()
        print("✅ 迁移完成")
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
    print("\n提示: 请重启Flask应用以使更改生效")
