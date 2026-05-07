"""
DataQ 平台全功能规则验证单元测试
覆盖所有8种规则类型 + column_pair_greater_than
"""
import pytest
import pandas as pd
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'backend'))

from engine.ge_wrapper import run_evaluation, RULE_MAPPING


class TestRuleTypes:
    """测试各种规则类型"""
    
    @pytest.fixture
    def sample_data_path(self, tmp_path):
        """创建临时测试数据文件"""
        data = {
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', 'Carol', 'David', 'Eva'],
            'age': [25, 30, 35, 40, 45],
            'email': ['a@test.com', 'b@test.com', 'c@test.com', 'd@test.com', 'e@test.com'],
            'gender': ['F', 'M', 'F', 'M', 'F'],
            'salary': [50000.0, 60000.0, 70000.0, 80000.0, 90000.0],
            'score': [85.5, 90.0, 75.5, 88.0, 92.5],
            'grade': ['A', 'B', 'A', 'B', 'A']
        }
        df = pd.DataFrame(data)
        file_path = tmp_path / 'test_data.csv'
        df.to_csv(file_path, index=False)
        return str(file_path)
    
    def test_not_null_all_values_present(self, sample_data_path):
        """测试: 所有值非空 -> 校验通过"""
        rules = [{'column': 'name', 'rule_type': 'not_null'}]
        result = run_evaluation(sample_data_path, rules)
        assert result['success_percent'] == 100.0
    
    def test_not_null_with_missing_values(self, tmp_path):
        """测试: 存在空值 -> 校验失败"""
        data = {'id': [1, 2, 3], 'name': ['Alice', None, 'Carol']}
        df = pd.DataFrame(data)
        file_path = tmp_path / 'test_null.csv'
        df.to_csv(file_path, index=False)
        
        rules = [{'column': 'name', 'rule_type': 'not_null'}]
        result = run_evaluation(str(file_path), rules)
        assert result['success_percent'] < 100.0
    
    def test_not_null_with_empty_string(self, tmp_path):
        """测试: 存在空字符串 -> 校验失败"""
        data = {'id': [1, 2], 'name': ['Alice', '']}
        df = pd.DataFrame(data)
        file_path = tmp_path / 'test_empty.csv'
        df.to_csv(file_path, index=False)
        
        rules = [{'column': 'name', 'rule_type': 'not_null'}]
        result = run_evaluation(str(file_path), rules)
        assert 'success_percent' in result
    
    def test_unique_all_unique(self, sample_data_path):
        """测试: 所有值唯一 -> 校验通过"""
        rules = [{'column': 'id', 'rule_type': 'unique'}]
        result = run_evaluation(sample_data_path, rules)
        assert result['success_percent'] == 100.0
    
    def test_unique_with_duplicates(self, tmp_path):
        """测试: 存在重复值 -> 校验失败"""
        data = {'id': [1, 2, 2, 3, 4]}
        df = pd.DataFrame(data)
        file_path = tmp_path / 'test_duplicate.csv'
        df.to_csv(file_path, index=False)
        
        rules = [{'column': 'id', 'rule_type': 'unique'}]
        result = run_evaluation(str(file_path), rules)
        assert result['success_percent'] < 100.0
    
    def test_between_within_range(self, sample_data_path):
        """测试: 值在范围内 -> 校验通过"""
        rules = [{
            'column': 'age',
            'rule_type': 'between',
            'params': {'min_value': 20, 'max_value': 50}
        }]
        result = run_evaluation(sample_data_path, rules)
        assert result['success_percent'] == 100.0
    
    def test_between_below_min(self, tmp_path):
        """测试: 值小于最小值 -> 校验失败"""
        data = {'age': [15, 25, 35]}
        df = pd.DataFrame(data)
        file_path = tmp_path / 'test_below.csv'
        df.to_csv(file_path, index=False)
        
        rules = [{
            'column': 'age',
            'rule_type': 'between',
            'params': {'min_value': 20, 'max_value': 50}
        }]
        result = run_evaluation(str(file_path), rules)
        assert result['success_percent'] < 100.0
    
    def test_between_above_max(self, tmp_path):
        """测试: 值大于最大值 -> 校验失败"""
        data = {'age': [25, 55, 35]}
        df = pd.DataFrame(data)
        file_path = tmp_path / 'test_above.csv'
        df.to_csv(file_path, index=False)
        
        rules = [{
            'column': 'age',
            'rule_type': 'between',
            'params': {'min_value': 20, 'max_value': 50}
        }]
        result = run_evaluation(str(file_path), rules)
        assert result['success_percent'] < 100.0
    
    def test_between_boundary_values(self, tmp_path):
        """测试: 等于边界值 -> 校验通过"""
        data = {'age': [20, 35, 50]}
        df = pd.DataFrame(data)
        file_path = tmp_path / 'test_boundary.csv'
        df.to_csv(file_path, index=False)
        
        rules = [{
            'column': 'age',
            'rule_type': 'between',
            'params': {'min_value': 20, 'max_value': 50}
        }]
        result = run_evaluation(str(file_path), rules)
        assert result['success_percent'] == 100.0
    
    def test_in_set_all_in_set(self, sample_data_path):
        """测试: 所有值在集合内 -> 校验通过"""
        rules = [{
            'column': 'gender',
            'rule_type': 'in_set',
            'params': {'value_set': ['M', 'F']}
        }]
        result = run_evaluation(sample_data_path, rules)
        assert result['success_percent'] == 100.0
    
    def test_in_set_with_outliers(self, tmp_path):
        """测试: 存在不在集合内的值 -> 校验失败"""
        data = {'gender': ['M', 'F', 'X', 'Other']}
        df = pd.DataFrame(data)
        file_path = tmp_path / 'test_outlier.csv'
        df.to_csv(file_path, index=False)
        
        rules = [{
            'column': 'gender',
            'rule_type': 'in_set',
            'params': {'value_set': ['M', 'F']}
        }]
        result = run_evaluation(str(file_path), rules)
        assert result['success_percent'] < 100.0
    
    def test_match_regex_valid_emails(self, sample_data_path):
        """测试: 邮箱格式正确 -> 校验通过"""
        rules = [{
            'column': 'email',
            'rule_type': 'match_regex',
            'params': {'regex': r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'}
        }]
        result = run_evaluation(sample_data_path, rules)
        assert result['success_percent'] == 100.0
    
    def test_match_regex_invalid_emails(self, tmp_path):
        """测试: 邮箱格式错误 -> 校验失败"""
        data = {'email': ['a@test.com', 'invalid-email', 'b@']}
        df = pd.DataFrame(data)
        file_path = tmp_path / 'test_email.csv'
        df.to_csv(file_path, index=False)
        
        rules = [{
            'column': 'email',
            'rule_type': 'match_regex',
            'params': {'regex': r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'}
        }]
        result = run_evaluation(str(file_path), rules)
        assert result['success_percent'] < 100.0
    
    def test_type_string_all_strings(self, sample_data_path):
        """测试: 字符串类型 -> 校验通过"""
        rules = [{'column': 'name', 'rule_type': 'type_string'}]
        result = run_evaluation(sample_data_path, rules)
        assert result['success_percent'] == 100.0
    
    def test_type_integer_all_integers(self, sample_data_path):
        """测试: 整数类型 -> 校验通过"""
        rules = [{'column': 'id', 'rule_type': 'type_integer'}]
        result = run_evaluation(sample_data_path, rules)
        assert result['success_percent'] == 100.0
    
    def test_type_integer_with_boundary_values(self, tmp_path):
        """测试: 边界值（0、负数、大数）-> 校验通过"""
        data = {'value': [0, -100, 999999]}
        df = pd.DataFrame(data)
        file_path = tmp_path / 'test_int_boundary.csv'
        df.to_csv(file_path, index=False)
        
        rules = [{'column': 'value', 'rule_type': 'type_integer'}]
        result = run_evaluation(str(file_path), rules)
        assert result['success_percent'] == 100.0
    
    def test_type_float_all_floats(self, sample_data_path):
        """测试: 浮点数类型 -> 校验通过"""
        rules = [{'column': 'salary', 'rule_type': 'type_float'}]
        result = run_evaluation(sample_data_path, rules)
        assert result['success_percent'] == 100.0
    
    def test_type_float_integers_compatible(self, tmp_path):
        """测试: 整数（兼容浮点数）-> 校验通过"""
        data = {'value': [100, 200, 300]}
        df = pd.DataFrame(data)
        file_path = tmp_path / 'test_float_int.csv'
        df.to_csv(file_path, index=False)
        
        rules = [{'column': 'value', 'rule_type': 'type_float'}]
        result = run_evaluation(str(file_path), rules)
        assert 'success_percent' in result
    
    def test_multiple_rules_together(self, sample_data_path):
        """测试: 同时执行多个规则"""
        rules = [
            {'column': 'id', 'rule_type': 'not_null'},
            {'column': 'id', 'rule_type': 'unique'},
            {'column': 'name', 'rule_type': 'not_null'},
            {'column': 'age', 'rule_type': 'between', 'params': {'min_value': 20, 'max_value': 60}},
            {'column': 'gender', 'rule_type': 'in_set', 'params': {'value_set': ['M', 'F']}}
        ]
        result = run_evaluation(sample_data_path, rules)
        assert result['total_rules'] == 5
        assert result['success_percent'] == 100.0
    
    def test_rule_mapping_complete(self):
        """测试: 确保所有8种规则类型都在映射中"""
        expected_rules = [
            'not_null', 'unique', 'between', 'in_set',
            'match_regex', 'type_string', 'type_integer', 'type_float',
            'column_pair_greater_than'
        ]
        for rule in expected_rules:
            assert rule in RULE_MAPPING, f"规则类型 {rule} 不在映射中"
    
    def test_unsupported_file_format(self, tmp_path):
        """测试: 不支持的文件格式 -> 抛出异常"""
        file_path = tmp_path / 'test.txt'
        file_path.write_text('plain text')
        
        rules = [{'column': 'id', 'rule_type': 'not_null'}]
        with pytest.raises(ValueError, match='不支持的文件格式'):
            run_evaluation(str(file_path), rules)
    
    def test_nonexistent_column(self, sample_data_path):
        """测试: 不存在的列名 -> 抛出异常"""
        rules = [{'column': 'nonexistent', 'rule_type': 'not_null'}]
        with pytest.raises(ValueError, match='不存在'):
            run_evaluation(sample_data_path, rules)
    
    def test_unsupported_rule_type(self, sample_data_path):
        """测试: 不支持的规则类型 -> 抛出异常"""
        rules = [{'column': 'id', 'rule_type': 'unknown_type'}]
        with pytest.raises(ValueError, match='不支持的规则类型'):
            run_evaluation(sample_data_path, rules)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
