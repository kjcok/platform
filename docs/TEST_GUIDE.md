# DataQ 平台 E2E 测试使用指南

## 📋 测试方案概述

已完成的工作：
- ✅ **API与前端对照分析**: 识别出36个API接口，19个已连接前端，17个未连接
- ✅ **E2E测试方案策划**: 详细的测试用例设计（见 `E2E_TEST_PLAN.md`）
- ✅ **Playwright环境搭建**: 使用Python 3.10虚拟环境安装完成
- ✅ **测试框架搭建**: pytest + playwright 配置完成
- ✅ **核心测试用例**: 资产管理(14个)、规则配置(15个)

## 🚀 快速开始

### 1. 环境准备

```bash
# 激活Python 3.10虚拟环境
D:\Python\venv310\Scripts\activate.bat

# 启动Flask后端（另一个终端）
cd d:\work\dataquality\dataq\platform
python src/backend/app.py
```

### 2. 运行测试

#### 方式1: 使用测试运行脚本（推荐）

```bash
# 无头模式（快速，默认）
cd d:\work\dataquality\dataq\platform\tests
python run_tests.py

# 有头模式（可见浏览器，用于调试）
python run_tests.py --mode headed

# 慢动作模式（500ms延迟，用于观察）
python run_tests.py --mode headed --slowmo 500

# 测试单个文件
python run_tests.py --file test_assets.py

# UI交互模式（时间旅行调试）
python run_tests.py --mode ui
```

#### 方式2: 直接使用pytest

```bash
cd d:\work\dataquality\dataq\platform\tests

# 运行所有测试
python -m pytest e2e/ -v

# 运行特定测试文件
python -m pytest e2e/test_assets.py -v

# 运行特定测试用例
python -m pytest e2e/test_assets.py::TestAssetsPage::test_ASSET_001_page_loads -v

# 带截图和视频
python -m pytest e2e/ -v --screenshot=only-on-failure --video=retain-on-failure
```

## 📁 测试文件结构

```
tests/
├── conftest.py              # ✅ 全局fixture（环境检查、错误捕获）
├── pytest.ini               # ✅ pytest配置
├── run_tests.py             # ✅ 测试运行脚本
├── e2e/                     # E2E测试用例
│   ├── test_assets.py       # ✅ 资产管理测试（14个用例）
│   ├── test_rule_config.py  # ✅ 规则配置测试（15个用例）
│   ├── test_dashboard.py    # ⏳ 待实现
│   ├── test_issues.py       # ⏳ 待实现
│   ├── test_validations.py  # ⏳ 待实现
│   └── test_validation_detail.py  # ⏳ 待实现
├── fixtures/                # 测试数据
│   └── files/               # 测试文件（CSV等）
├── utils/                   # 测试工具函数
└── pages/                   # Page Object Model（可选）
```

## 📊 测试用例清单

### 已完成（29个用例）

#### 资产管理测试（test_assets.py - 14个）

| 用例ID | 测试内容 | 状态 |
|--------|---------|------|
| ASSET-001 | 页面加载 | ✅ 已实现 |
| ASSET-002 | 资产列表显示 | ✅ 已实现 |
| ASSET-003 | 创建资产按钮 | ✅ 已实现 |
| ASSET-005 | 搜索资产 | ✅ 已实现 |
| ASSET-006 | 状态筛选 | ✅ 已实现 |
| ASSET-007 | 删除资产 | ✅ 已实现 |
| ASSET-008 | 查看详情跳转 | ✅ 已实现 |
| ASSET-009 | 编辑按钮存在性 | ✅ 已实现 |
| ASSET-010 | 编辑资产功能 | ✅ 已实现 |
| ASSET-011 | API调用验证 | ✅ 已实现 |
| ASSET-014 | 空列表状态 | ⏸️ 跳过（需空数据库） |

#### 规则配置测试（test_rule_config.py - 15个）

| 用例ID | 测试内容 | 状态 |
|--------|---------|------|
| RULE-001 | 页面加载 | ✅ 已实现 |
| RULE-002 | 模板选择步骤 | ✅ 已实现 |
| RULE-003 | 选择模板 | ✅ 已实现 |
| RULE-004 | 基本信息表单 | ✅ 已实现 |
| RULE-005 | 模板参数表单 | ✅ 已实现 |
| RULE-006 | 表单验证 | ✅ 已实现 |
| RULE-007 | SQL预览 | ✅ 已实现 |
| RULE-008 | 配置摘要 | ✅ 已实现 |
| RULE-009 | 复制SQL | ✅ 已实现 |
| RULE-010 | 导航按钮 | ✅ 已实现 |
| RULE-011 | 取消向导 | ✅ 已实现 |
| RULE-012 | 创建规则API | ✅ 已实现 |
| RULE-013 | 成功跳转 | ✅ 已实现 |
| RULE-014 | 加载状态 | ✅ 已实现 |
| RULE-015 | 不同模板 | ✅ 已实现 |

### 待实现（36个用例）

- **质量大盘** (DASH-001 ~ DASH-006): 6个
- **资产详情** (DETAIL-001 ~ DETAIL-014): 14个
- **问题管理** (ISSUE-001 ~ ISSUE-017): 17个
- **校验历史** (VALID-001 ~ VALID-004): 4个
- **校验详情** (VDETAIL-001 ~ VDETAIL-008): 8个

## 🔍 测试报告

### 截图和视频

测试失败时自动保存：
- **截图**: `test-results/` 目录
- **视频**: `test-results/` 目录
- **追踪文件**: 可用于Playwright UI模式调试

### 查看测试报告

```bash
# 查看失败截图
dir test-results\*.png

# 使用Playwright UI查看追踪文件
python -m playwright show-trace test-results\trace.zip
```

## 🐛 调试技巧

### 1. 慢动作模式

```bash
python run_tests.py --mode headed --slowmo 500
```

可以看到浏览器每一步操作，适合调试失败的测试。

### 2. UI模式

```bash
python run_tests.py --mode ui
```

提供时间旅行调试功能，可以：
- 查看每一步的DOM快照
- 查看网络请求
- 查看控制台日志
- 回放测试执行过程

### 3. 单个测试调试

```bash
# 运行单个测试，带详细输出
python -m pytest e2e/test_assets.py::TestAssetsPage::test_ASSET_010_edit_asset_functionality -v -s
```

### 4. 暂停测试

在测试代码中添加：
```python
page.pause()  # 暂停测试，打开Playwright Inspector
```

## 📝 发现的问题

### 已修复
1. ✅ **资产编辑功能**: HTML中缺少`data-source`隐藏字段，已添加
2. ✅ **上传API路径**: 从`/api/upload`迁移到`/api/v1/upload`
3. ✅ **资产详情路由**: 添加`/assets/<int:asset_id>`路由和页面

### 待修复（来自API对照分析）
1. **规则编辑功能**: asset_detail.js中editRule()只显示警告
2. **批量问题操作**: issues.js中API调用被注释
3. **执行校验功能**: 缺少触发校验的界面
4. **调度配置**: 完全未实现前端界面
5. **告警管理**: 完全未实现

## 🎯 下一步建议

### 优先级 P0（本周）
1. 补充问题管理测试（ISSUE-001 ~ ISSUE-017）
2. 补充资产详情测试（DETAIL-001 ~ DETAIL-014）
3. 修复规则编辑功能
4. 运行完整测试套件，统计通过率

### 优先级 P1（下周）
1. 补充质量大盘测试
2. 补充校验历史和详情测试
3. 实现执行校验功能界面
4. 实现批量问题操作

### 优先级 P2（未来）
1. 实现调度配置界面
2. 实现告警管理界面
3. 集成到CI/CD流程
4. 增加性能测试

## 💡 常见问题

### Q: 测试失败显示"后端服务未运行"
A: 确保Flask应用已启动：
```bash
python src/backend/app.py
```

### Q: 测试执行很慢
A: 使用无头模式：
```bash
python run_tests.py
```

### Q: 如何查看失败原因
A: 查看终端输出，或查看test-results目录的截图和视频

### Q: 测试数据会污染数据库吗
A: 当前测试使用真实数据库，建议：
- 使用独立的测试数据库
- 或在测试前后执行数据回滚

## 📚 参考文档

- [Playwright Python文档](https://playwright.dev/python/docs/intro)
- [pytest文档](https://docs.pytest.org/)
- [API与前端对照分析](API_FRONTEND_ANALYSIS.md)
- [E2E测试方案](E2E_TEST_PLAN.md)
