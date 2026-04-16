"""
数据库迁移脚本：为 exception_data 表添加 issue_id 字段
"""
import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
backend_path = os.path.join(project_root, 'src', 'backend')
sys.path.insert(0, backend_path)

from db_utils import get_session
from sqlalchemy import text

def migrate():
    """执行数据库迁移"""
    session = get_session()
    
    try:
        # 检查 issue_id 列是否已存在
        result = session.execute(text("""
            PRAGMA table_info(exception_data)
        """))
        columns = [row[1] for row in result.fetchall()]
        
        if 'issue_id' not in columns:
            print("正在添加 issue_id 字段到 exception_data 表...")
            
            # 添加 issue_id 列
            session.execute(text("""
                ALTER TABLE exception_data 
                ADD COLUMN issue_id INTEGER REFERENCES issues(id)
            """))
            
            session.commit()
            print("[OK] 成功添加 issue_id 字段")
        else:
            print("[INFO] issue_id 字段已存在，跳过迁移")
        
        print("[OK] 数据库迁移完成")
        
    except Exception as e:
        session.rollback()
        print(f"[ERROR] 迁移失败: {e}")
        raise
    finally:
        session.close()


if __name__ == '__main__':
    print("=" * 80)
    print("执行数据库迁移：添加 exception_data.issue_id 字段")
    print("=" * 80)
    migrate()
