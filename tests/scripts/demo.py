"""
示例脚本：演示如何使用数据质量评估平台
自动上传文件、配置规则、执行评估并生成报告
"""
import requests
import json

# API 基础 URL
BASE_URL = 'http://localhost:5000'


def demo_evaluation():
    """演示完整的数据质量评估流程"""
    
    print("=" * 60)
    print("数据质量评估平台 - 示例演示")
    print("=" * 60)
    
    # 步骤 1: 上传示例数据文件
    print("\n[步骤 1] 上传示例数据文件...")
    import os
    sample_data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample_data.csv')
    with open(sample_data_path, 'rb') as f:
        response = requests.post(f'{BASE_URL}/api/upload', 
                               files={'file': ('sample_data.csv', f)})
    
    if response.status_code != 200:
        print(f"❌ 上传失败: {response.json()['message']}")
        return
    
    upload_result = response.json()
    file_id = upload_result['file_id']
    columns = upload_result['columns']
    
    print(f"✅ 上传成功!")
    print(f"   文件ID: {file_id}")
    print(f"   字段列表: {', '.join(columns)}")
    
    # 步骤 2: 配置质量规则
    print("\n[步骤 2] 配置质量规则...")
    rules = [
        {
            "column": "id",
            "rule_type": "unique",
            "params": {}
        },
        {
            "column": "id",
            "rule_type": "not_null",
            "params": {}
        },
        {
            "column": "age",
            "rule_type": "between",
            "params": {
                "min_value": 18,
                "max_value": 65
            }
        },
        {
            "column": "age",
            "rule_type": "not_null",
            "params": {}
        },
        {
            "column": "email",
            "rule_type": "not_null",
            "params": {}
        },
        {
            "column": "gender",
            "rule_type": "in_set",
            "params": {
                "value_set": ["男", "女"]
            }
        },
        {
            "column": "salary",
            "rule_type": "between",
            "params": {
                "min_value": 0,
                "max_value": 100000
            }
        }
    ]
    
    print(f"✅ 已配置 {len(rules)} 条规则:")
    for i, rule in enumerate(rules, 1):
        print(f"   {i}. {rule['column']} - {rule['rule_type']}")
    
    # 步骤 3: 执行评估
    print("\n[步骤 3] 执行数据质量评估...")
    eval_request = {
        "file_id": file_id,
        "rules": rules
    }
    
    response = requests.post(f'{BASE_URL}/api/evaluate',
                           json=eval_request)
    
    if response.status_code != 200:
        print(f"❌ 评估失败: {response.json()['message']}")
        return
    
    eval_result = response.json()
    
    print(f"✅ 评估完成!")
    print(f"\n📊 评估摘要:")
    print(f"   总规则数: {eval_result['summary']['total_rules']}")
    print(f"   通过规则: {eval_result['summary']['passed_rules']}")
    print(f"   失败规则: {eval_result['summary']['failed_rules']}")
    print(f"   成功率: {eval_result['summary']['success_percent']}%")
    
    # 步骤 4: 查看报告
    report_url = f"{BASE_URL}{eval_result['report_url']}"
    print(f"\n📄 报告地址: {report_url}")
    print(f"\n💡 提示: 在浏览器中打开上述链接查看详细报告")
    
    # 步骤 5: 下载并保存报告（可选）
    print("\n[步骤 5] 下载报告到本地...")
    report_response = requests.get(report_url)
    if report_response.status_code == 200:
        report_filename = eval_result['report_url'].split('/')[-1]
        import os
        os.makedirs('../../output/reports', exist_ok=True)
        with open(f"../../output/reports/{report_filename}", 'w', encoding='utf-8') as f:
            f.write(report_response.text)
        print(f"✅ 报告已保存: output/reports/{report_filename}")
    
    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


if __name__ == '__main__':
    try:
        demo_evaluation()
    except requests.exceptions.ConnectionError:
        print("❌ 错误: 无法连接到服务器")
        print("   请确保 Flask 应用正在运行 (python app.py)")
    except Exception as e:
        print(f"❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
