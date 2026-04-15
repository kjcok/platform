"""
Flask 主应用
提供数据质量评估平台的 Web 接口
"""
from flask import Flask, request, jsonify, send_from_directory, render_template
from file_manager import save_uploaded_file, check_file_exists
from ge_engine import run_evaluation
from report_renderer import generate_report
import os

app = Flask(__name__, template_folder='../../src/frontend/templates')

# 配置上传和报告目录（使用绝对路径）
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # src/backend
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))  # platform
UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'output', 'data')
REPORTS_FOLDER = os.path.join(PROJECT_ROOT, 'output', 'reports')

# 确保目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORTS_FOLDER, exist_ok=True)


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    上传数据文件并获取表头
    
    Returns:
        JSON: 包含 file_id 和 columns 的响应
    """
    if 'file' not in request.files:
        return jsonify({
            'status': 'error',
            'message': '没有上传文件'
        }), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({
            'status': 'error',
            'message': '文件名为空'
        }), 400
    
    # 保存文件并获取信息
    result = save_uploaded_file(file, UPLOAD_FOLDER)
    
    if result is None:
        return jsonify({
            'status': 'error',
            'message': '文件格式不支持或文件为空，仅支持 CSV、XLSX、XLS 格式'
        }), 400
    
    return jsonify({
        'status': 'success',
        'file_id': result['file_id'],
        'columns': result['columns']
    })


@app.route('/api/evaluate', methods=['POST'])
def evaluate_data():
    """
    执行数据质量评估
    
    Returns:
        JSON: 包含评估结果和报告 URL 的响应
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            'status': 'error',
            'message': '请求体不能为空'
        }), 400
    
    file_id = data.get('file_id')
    rules = data.get('rules', [])
    
    if not file_id:
        return jsonify({
            'status': 'error',
            'message': '缺少 file_id 参数'
        }), 400
    
    if not rules:
        return jsonify({
            'status': 'error',
            'message': '至少需要一条规则'
        }), 400
    
    # 检查文件是否存在
    if not check_file_exists(file_id, UPLOAD_FOLDER):
        return jsonify({
            'status': 'error',
            'message': '未找到该数据集，请重新上传'
        }), 404
    
    try:
        # 执行评估
        result_data = run_evaluation(file_id, rules, UPLOAD_FOLDER)
        
        # 生成报告
        report_filename = generate_report(result_data, REPORTS_FOLDER)
        
        return jsonify({
            'status': 'success',
            'report_url': f'/report/{report_filename}',
            'summary': {
                'success_percent': result_data['success_percent'],
                'total_rules': result_data['total_rules'],
                'passed_rules': result_data['passed_rules'],
                'failed_rules': result_data['failed_rules']
            }
        })
        
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except FileNotFoundError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'评估过程出错: {str(e)}'
        }), 500


@app.route('/report/<filename>')
def get_report(filename):
    """
    查看测评报告
    
    Args:
        filename: 报告文件名
        
    Returns:
        HTML: 报告页面
    """
    return send_from_directory(REPORTS_FOLDER, filename)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
