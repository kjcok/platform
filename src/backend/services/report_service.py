"""
自定义报告渲染器
负责将测评结果渲染为 HTML 报告
"""
import os
import uuid
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

# 获取项目根目录和模板目录
# 使用绝对路径，确保在任何工作目录下都能正确找到模板
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # src/backend
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))  # platform
TEMPLATE_DIR = os.path.join(PROJECT_ROOT, 'src', 'frontend', 'templates')

# 初始化 Jinja2 环境
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


# 规则类型中文映射
RULE_NAMES = {
    'not_null': '非空检查',
    'unique': '唯一性检查',
    'between': '数值范围',
    'in_set': '枚举值检查',
    'match_regex': '正则匹配',
    'type_string': '字符串类型',
    'type_integer': '整数类型',
    'type_float': '浮点数类型'
}


def get_rule_name(rule_type):
    """获取规则类型的中文名称"""
    return RULE_NAMES.get(rule_type, rule_type)


def generate_report(result_data, reports_folder='reports'):
    """
    生成数据质量评估报告
    
    Args:
        result_data: 测评结果字典
        reports_folder: 报告保存目录
        
    Returns:
        str: 报告文件的相对路径
    """
    # 确保目录存在
    os.makedirs(reports_folder, exist_ok=True)
    
    # 生成报告文件名
    report_filename = f"report_{uuid.uuid4().hex}.html"
    report_path = os.path.join(reports_folder, report_filename)
    
    # 添加生成时间
    result_data['generated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 使用 Jinja2 渲染模板
    template = env.get_template('report_template.html')
    html_content = template.render(get_rule_name=get_rule_name, **result_data)
    
    # 保存报告
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return report_filename
