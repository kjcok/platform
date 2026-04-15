"""
文件与元数据管理模块
负责接收上传的文件、保存、读取表头等操作
"""
import os
import uuid
import pandas as pd
from werkzeug.utils import secure_filename

# 支持的文件类型
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file, upload_folder='data'):
    """
    保存上传的文件
    
    Args:
        file: Flask 上传的文件对象
        upload_folder: 保存目录
        
    Returns:
        dict: 包含 file_id 和 columns 的字典，失败返回 None
    """
    if not file or file.filename == '':
        return None
    
    if not allowed_file(file.filename):
        return None
    
    # 生成唯一文件名
    original_filename = secure_filename(file.filename)
    file_extension = original_filename.rsplit('.', 1)[1].lower()
    file_id = f"data_{uuid.uuid4().hex}.{file_extension}"
    
    # 确保目录存在
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, file_id)
    
    # 保存文件
    file.save(file_path)
    
    # 读取表头
    try:
        columns = read_file_columns(file_path)
        return {
            'file_id': file_id,
            'columns': columns
        }
    except Exception as e:
        # 如果读取失败，删除文件
        if os.path.exists(file_path):
            os.remove(file_path)
        return None


def read_file_columns(file_path):
    """
    读取文件的列名
    
    Args:
        file_path: 文件路径
        
    Returns:
        list: 列名列表
    """
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path, nrows=0)
    elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
        df = pd.read_excel(file_path, nrows=0)
    else:
        raise ValueError(f"不支持的文件格式: {file_path}")
    
    return df.columns.tolist()


def get_file_path(file_id, upload_folder='data'):
    """
    获取文件的完整路径
    
    Args:
        file_id: 文件ID
        upload_folder: 文件目录
        
    Returns:
        str: 文件完整路径
    """
    return os.path.join(upload_folder, file_id)


def check_file_exists(file_id, upload_folder='data'):
    """
    检查文件是否存在
    
    Args:
        file_id: 文件ID
        upload_folder: 文件目录
        
    Returns:
        bool: 文件是否存在
    """
    file_path = get_file_path(file_id, upload_folder)
    return os.path.exists(file_path)
