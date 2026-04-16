"""
数据库初始化脚本
用于首次运行或重置数据库
"""
import sys
import os

# 添加后端代码路径到系统路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'backend'))

from models import init_db, engine, Base
import shutil


def reset_database():
    """
    重置数据库（删除旧数据库并重新创建）
    """
    # 获取数据库路径
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
    DATABASE_PATH = os.path.join(PROJECT_ROOT, 'config', 'dataq.db')
    
    # 如果数据库存在，先删除
    if os.path.exists(DATABASE_PATH):
        print(f"⚠️  发现现有数据库: {DATABASE_PATH}")
        response = input("是否删除并重新创建？(y/n): ")
        if response.lower() == 'y':
            os.remove(DATABASE_PATH)
            print("✅ 旧数据库已删除")
        else:
            print("❌ 操作取消")
            return
    
    # 初始化新数据库
    init_db()
    print("\n📊 数据库表结构:")
    print("  - assets (资产表)")
    print("  - rules (规则表)")
    print("  - validation_history (校验历史表)")
    print("  - issues (问题清单表)")
    print("  - exception_data (异常数据归档表)")
    print("\n✅ 数据库初始化完成！")


if __name__ == '__main__':
    reset_database()
