"""
数据质量评估平台测试用例
包含单元测试和接口测试
"""
import unittest
import os
import sys
import json
import tempfile
import pandas as pd

# 添加后端代码路径到系统路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'backend'))

from app import app
from file_manager import save_uploaded_file, check_file_exists, read_file_columns
from ge_engine import run_evaluation
from report_renderer import generate_report


class TestFileManager(unittest.TestCase):
    """文件管理模块测试"""
    
    def setUp(self):
        """创建测试环境"""
        self.test_dir = tempfile.mkdtemp()
        self.app = app.test_client()
        
    def tearDown(self):
        """清理测试环境"""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_upload_valid_csv(self):
        """TC-U1: 正常上传 CSV 文件"""
        # 创建测试 CSV 文件
        csv_content = "id,name,age\n1,Alice,25\n2,Bob,30\n3,Charlie,35"
        csv_path = os.path.join(self.test_dir, 'test.csv')
        with open(csv_path, 'w') as f:
            f.write(csv_content)
        
        # 模拟上传
        with open(csv_path, 'rb') as f:
            response = self.app.post('/api/upload', 
                                   data={'file': (f, 'test.csv')},
                                   content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('file_id', data)
        self.assertEqual(sorted(data['columns']), ['age', 'id', 'name'])
    
    def test_upload_empty_file(self):
        """TC-U2: 上传空文件"""
        empty_path = os.path.join(self.test_dir, 'empty.csv')
        with open(empty_path, 'w') as f:
            pass
        
        with open(empty_path, 'rb') as f:
            response = self.app.post('/api/upload',
                                   data={'file': (f, 'empty.csv')},
                                   content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
    
    def test_upload_invalid_format(self):
        """TC-U3: 上传不支持的格式"""
        txt_path = os.path.join(self.test_dir, 'test.txt')
        with open(txt_path, 'w') as f:
            f.write('This is a text file')
        
        with open(txt_path, 'rb') as f:
            response = self.app.post('/api/upload',
                                   data={'file': (f, 'test.txt')},
                                   content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')


class TestEvaluationEngine(unittest.TestCase):
    """测评执行引擎测试"""
    
    def setUp(self):
        """创建测试数据和环境"""
        self.test_dir = tempfile.mkdtemp()
        
        # 创建测试 CSV 文件
        df = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
            'age': [25, 30, 35, 40, 45],
            'email': ['alice@test.com', 'bob@test.com', None, 'david@test.com', 'eve@test.com']
        })
        
        self.test_file = os.path.join(self.test_dir, 'test_data.csv')
        df.to_csv(self.test_file, index=False)
        
        # 生成 file_id
        self.file_id = os.path.basename(self.test_file)
    
    def tearDown(self):
        """清理测试环境"""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_all_rules_pass(self):
        """TC-E1: 全部规则通过"""
        rules = [
            {'column': 'id', 'rule_type': 'unique'},
            {'column': 'age', 'rule_type': 'between', 'params': {'min_value': 0, 'max_value': 100}},
            {'column': 'name', 'rule_type': 'not_null'}
        ]
        
        result = run_evaluation(self.file_id, rules, self.test_dir)
        
        self.assertEqual(result['total_rules'], 3)
        self.assertEqual(result['passed_rules'], 3)
        self.assertEqual(result['failed_rules'], 0)
        self.assertEqual(result['success_percent'], 100.0)
    
    def test_partial_rules_fail(self):
        """TC-E2: 部分规则未通过"""
        rules = [
            {'column': 'age', 'rule_type': 'between', 'params': {'min_value': 0, 'max_value': 30}}
        ]
        
        result = run_evaluation(self.file_id, rules, self.test_dir)
        
        self.assertLess(result['success_percent'], 100.0)
        self.assertGreater(result['details'][0]['unexpected_count'], 0)
    
    def test_file_not_found(self):
        """TC-E3: 目标文件不存在"""
        rules = [{'column': 'id', 'rule_type': 'unique'}]
        
        with self.assertRaises(FileNotFoundError):
            run_evaluation('nonexistent.csv', rules, self.test_dir)
    
    def test_column_not_exist(self):
        """TC-E4: 规则配置包含不存在的列"""
        rules = [{'column': 'address', 'rule_type': 'not_null'}]
        
        with self.assertRaises(ValueError) as context:
            run_evaluation(self.file_id, rules, self.test_dir)
        
        self.assertIn("列 'address' 不存在于数据集中", str(context.exception))
    
    def test_unsupported_rule_type(self):
        """TC-E5: 不支持的规则类型"""
        rules = [{'column': 'id', 'rule_type': 'magic_check'}]
        
        with self.assertRaises(ValueError) as context:
            run_evaluation(self.file_id, rules, self.test_dir)
        
        self.assertIn("不支持的规则类型", str(context.exception))


class TestReportRenderer(unittest.TestCase):
    """报告渲染器测试"""
    
    def setUp(self):
        """创建测试环境"""
        self.test_dir = tempfile.mkdtemp()
        self.app = app
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        """清理测试环境"""
        import shutil
        self.app_context.pop()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_render_perfect_report(self):
        """TC-R1: 渲染完美质量报告"""
        result_data = {
            'total_rules': 3,
            'passed_rules': 3,
            'failed_rules': 0,
            'success_percent': 100.0,
            'details': [],
            'total_rows': 100,
            'columns': ['id', 'name', 'age']
        }
        
        report_filename = generate_report(result_data, self.test_dir)
        report_path = os.path.join(self.test_dir, report_filename)
        
        self.assertTrue(os.path.exists(report_path))
        
        with open(report_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        self.assertIn('100.0%', html_content)
        self.assertIn('总体成功率', html_content)
    
    def test_render_failed_report(self):
        """TC-R2: 渲染含失败明细的报告"""
        result_data = {
            'total_rules': 2,
            'passed_rules': 1,
            'failed_rules': 1,
            'success_percent': 50.0,
            'details': [
                {
                    'column': 'age',
                    'rule_type': 'between',
                    'success': False,
                    'unexpected_count': 5,
                    'unexpected_percent': 10.0,
                    'element_count': 50,
                    'sample_unexpected': [150, 200, -5]
                },
                {
                    'column': 'id',
                    'rule_type': 'unique',
                    'success': True,
                    'unexpected_count': 0,
                    'unexpected_percent': 0,
                    'element_count': 50
                }
            ],
            'total_rows': 50,
            'columns': ['id', 'age']
        }
        
        report_filename = generate_report(result_data, self.test_dir)
        report_path = os.path.join(self.test_dir, report_filename)
        
        self.assertTrue(os.path.exists(report_path))
        
        with open(report_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        self.assertIn('age', html_content)
        self.assertIn('5', html_content)  # 异常数量
        self.assertIn('异常值示例', html_content)


class TestAPIEndpoints(unittest.TestCase):
    """API 接口测试"""
    
    def setUp(self):
        """创建测试客户端"""
        self.app = app.test_client()
        self.app.testing = True
    
    def test_upload_endpoint(self):
        """测试上传接口"""
        # 创建测试文件
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("id,name,age\n1,Alice,25\n2,Bob,30")
            temp_path = f.name
        
        try:
            with open(temp_path, 'rb') as f:
                response = self.app.post('/api/upload',
                                       data={'file': (f, 'test.csv')},
                                       content_type='multipart/form-data')
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data['status'], 'success')
        finally:
            os.unlink(temp_path)
    
    def test_evaluate_without_file(self):
        """测试评估接口 - 缺少文件"""
        response = self.app.post('/api/evaluate',
                               data=json.dumps({'rules': []}),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
    
    def test_evaluate_without_rules(self):
        """测试评估接口 - 缺少规则"""
        response = self.app.post('/api/evaluate',
                               data=json.dumps({'file_id': 'test.csv'}),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')


if __name__ == '__main__':
    # 运行所有测试
    unittest.main(verbosity=2)
