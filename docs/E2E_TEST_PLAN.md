# DataQ 平台 E2E 测试方案

## 一、测试概述

### 1.1 测试目标
使用 Playwright 对 DataQ 数据质量评估平台进行端到端测试，确保前端界面与后端 API 的正确对接，验证核心业务流程的完整性。

### 1.2 测试范围
- 前端页面渲染与交互
- 前端与后端 API 的对接
- 核心业务流程的完整性
- 错误处理与用户提示

### 1.3 测试环境
- **Python版本**: 3.10
- **虚拟环境**: `D:\Python\venv310`
- **激活脚本**: `D:\Python\venv310\Scripts\activate.bat`
- **后端框架**: Flask
- **后端地址**: `http://localhost:5000`
- **测试框架**: Playwright (Python)
- **浏览器**: Chromium（默认）

## 二、测试对象清单

### 2.1 页面列表（共7个核心页面）

| 序号 | 页面名称 | 路由 | 测试文件 | 优先级 |
|------|---------|------|----------|--------|
| 1 | 质量大盘 | `/dashboard` | `test_dashboard.py` | P0 |
| 2 | 资产管理 | `/assets` | `test_assets.py` | P0 |
| 3 | 资产详情 | `/assets/<id>` | `test_asset_detail.py` | P1 |
| 4 | 规则配置 | `/rule-config` | `test_rule_config.py` | P0 |
| 5 | 问题管理 | `/issues` | `test_issues.py` | P0 |
| 6 | 校验历史 | `/validations` | `test_validations.py` | P1 |
| 7 | 校验详情 | `/validations/<id>` | `test_validation_detail.py` | P1 |

### 2.2 API 接口测试对象（共36个）

按模块分类的API接口测试清单，详见 `API_FRONTEND_ANALYSIS.md`

## 三、测试内容设计

### 3.1 质量大盘页面测试（test_dashboard.py）

#### 测试用例列表

| 用例ID | 测试内容 | 前置条件 | 操作步骤 | 预期结果 |
|--------|---------|---------|---------|---------|
| DASH-001 | 页面加载 | 后端服务运行中 | 访问 `/dashboard` | 页面正常加载，无JS错误 |
| DASH-002 | 统计卡片显示 | 数据库有数据 | 检查统计卡片区域 | 显示资产总数、规则总数、校验次数、问题数量 |
| DASH-003 | 最近问题列表 | 数据库有未解决问题 | 检查问题列表区域 | 显示最近10个问题，包含标题、状态、优先级 |
| DASH-004 | 统计API调用 | 页面加载时 | 监听网络请求 | 调用 `/api/v1/statistics/overview`，返回200 |
| DASH-005 | 问题API调用 | 页面加载时 | 监听网络请求 | 调用 `/api/v1/issues?per_page=10`，返回200 |
| DASH-006 | 空数据状态 | 数据库为空 | 清空数据后访问 | 统计卡片显示0，问题列表显示"暂无问题" |

### 3.2 资产管理页面测试（test_assets.py）

#### 测试用例列表

| 用例ID | 测试内容 | 前置条件 | 操作步骤 | 预期结果 |
|--------|---------|---------|---------|---------|
| ASSET-001 | 页面加载 | 后端服务运行中 | 访问 `/assets` | 页面正常加载 |
| ASSET-002 | 资产列表显示 | 数据库有资产 | 检查表格区域 | 显示资产列表，包含ID、名称、类型、状态等列 |
| ASSET-003 | 创建资产-文件上传 | 准备CSV测试文件 | 点击"新建资产"→上传CSV→填写信息→提交 | 显示成功提示，列表新增资产 |
| ASSET-004 | 创建资产-字段解析 | 上传CSV后 | 检查字段选择器 | 正确显示CSV列名 |
| ASSET-005 | 搜索资产 | 数据库有多个资产 | 在搜索框输入关键词 | 列表过滤显示匹配的资产 |
| ASSET-006 | 筛选资产状态 | 数据库有不同状态的资产 | 选择状态筛选器 | 列表按状态过滤 |
| ASSET-007 | 删除资产 | 数据库有资产 | 点击删除按钮→确认 | 资产被删除，列表刷新 |
| ASSET-008 | 查看资产详情 | 数据库有资产 | 点击"查看详情"按钮 | 跳转到资产详情页 `/assets/<id>` |
| ASSET-009 | 编辑资产-按钮存在性 | 数据库有资产 | 检查操作列 | 应有"编辑"按钮（当前缺失，待修复） |
| ASSET-010 | 编辑资产-API调用 | 修复编辑按钮后 | 点击编辑→修改信息→保存 | 调用 PUT `/api/v1/assets/<id>`，返回200 |
| ASSET-011 | 创建资产API | 填写表单提交 | 监听网络请求 | 调用 POST `/api/v1/assets`，返回200 |
| ASSET-012 | 资产列表API | 页面加载 | 监听网络请求 | 调用 GET `/api/v1/assets`，返回200 |
| ASSET-013 | 文件上传API | 上传文件时 | 监听网络请求 | 调用 POST `/api/v1/upload`，返回200 |
| ASSET-014 | 空列表状态 | 数据库为空 | 访问页面 | 显示"暂无资产"提示和"新建资产"按钮 |
| ASSET-015 | 分页功能 | 数据库有超过10个资产 | 检查分页控件 | 显示分页器，点击下一页加载新数据 |

### 3.3 资产详情页面测试（test_asset_detail.py）

#### 测试用例列表

| 用例ID | 测试内容 | 前置条件 | 操作步骤 | 预期结果 |
|--------|---------|---------|---------|---------|
| DETAIL-001 | 页面加载 | 数据库有资产 | 访问 `/assets/1` | 页面正常加载，显示资产信息 |
| DETAIL-002 | 资产头部信息 | 数据库有资产 | 检查头部区域 | 显示资产名称、类型、负责人、权重等 |
| DETAIL-003 | 规则列表显示 | 资产有规则 | 切换到"规则列表"标签 | 显示规则卡片列表 |
| DETAIL-004 | 规则空状态 | 资产无规则 | 切换到"规则列表"标签 | 显示"暂无规则"和"添加第一个规则"按钮 |
| DETAIL-005 | 添加规则 | 资产详情页 | 点击"配置规则"按钮 | 跳转到 `/rule-config?asset_id=1` |
| DETAIL-006 | 删除规则 | 资产有规则 | 点击规则的"删除"按钮→确认 | 调用 DELETE `/api/v1/rules/<id>`，规则消失 |
| DETAIL-007 | 编辑规则-按钮存在性 | 资产有规则 | 检查规则操作按钮 | 应有"编辑"按钮（当前未实现） |
| DETAIL-008 | 校验历史标签 | 资产有校验记录 | 切换到"校验历史"标签 | 显示校验历史列表 |
| DETAIL-009 | 问题记录标签 | 资产有问题 | 切换到"问题记录"标签 | 显示问题列表 |
| DETAIL-010 | 查看详情跳转 | 有校验记录 | 点击"查看详情" | 跳转到 `/validations/<history_id>` |
| DETAIL-011 | 资产详情API | 页面加载 | 监听网络请求 | 调用 GET `/api/v1/assets/1`，返回200 |
| DETAIL-012 | 规则列表API | 加载规则标签 | 监听网络请求 | 调用 GET `/api/v1/assets/1/rules`，返回200 |
| DETAIL-013 | 校验历史API | 加载校验标签 | 监听网络请求 | 调用 GET `/api/v1/assets/1/validations`，返回200 |
| DETAIL-014 | 问题记录API | 加载问题标签 | 监听网络请求 | 调用 GET `/api/v1/assets/1/issues`，返回200 |

### 3.4 规则配置向导测试（test_rule_config.py）

#### 测试用例列表

| 用例ID | 测试内容 | 前置条件 | 操作步骤 | 预期结果 |
|--------|---------|---------|---------|---------|
| RULE-001 | 页面加载 | 后端服务运行中 | 访问 `/rule-config?asset_id=1` | 页面正常加载，显示步骤条 |
| RULE-002 | 步骤1-模板选择 | 页面加载 | 检查模板卡片 | 显示7种规则模板（完整性、唯一性等） |
| RULE-003 | 选择模板 | 在步骤1 | 点击"完整性校验"模板 | 模板卡片高亮，点击"下一步"进入步骤2 |
| RULE-004 | 步骤2-基本信息表单 | 进入步骤2 | 检查表单字段 | 显示规则名称、规则强度、规则描述输入框 |
| RULE-005 | 步骤2-模板参数表单 | 选择了完整性模板 | 检查参数字段 | 显示"字段名"和"通过率阈值"输入框 |
| RULE-006 | 表单验证-必填项 | 步骤2表单 | 不填写规则名称→点击下一步 | 显示验证错误提示 |
| RULE-007 | 步骤3-SQL预览 | 填写完整表单→下一步 | 检查SQL预览区域 | 显示生成的SQL语句 |
| RULE-008 | 步骤3-配置摘要 | 进入步骤3 | 检查摘要信息 | 显示规则名称、类型、强度等摘要 |
| RULE-009 | 复制SQL | 步骤3 | 点击"复制SQL"按钮 | SQL复制到剪贴板，显示成功提示 |
| RULE-010 | 上一步/下一步 | 在步骤2或3 | 点击"上一步" | 返回上一步骤，状态保持 |
| RULE-011 | 取消向导 | 任何步骤 | 点击"取消"按钮 | 跳转到资产管理页面 |
| RULE-012 | 创建规则 | 填写完整→步骤3 | 点击"创建规则" | 调用 POST `/api/v1/assets/1/rules`，返回200 |
| RULE-013 | 创建成功跳转 | 创建规则成功后 | 等待1.5秒 | 自动跳转到 `/assets/1` 资产详情页 |
| RULE-014 | 加载状态 | 创建规则时 | 点击"创建规则"后 | 显示加载遮罩"正在创建规则..." |
| RULE-015 | 不同模板参数 | 选择不同模板 | 分别选择7种模板 | 每种模板显示不同的参数字段 |
| RULE-016 | 自定义SQL模板 | 选择自定义SQL | 检查参数字段 | 显示"SQL语句"textarea输入框 |

### 3.5 问题管理页面测试（test_issues.py）

#### 测试用例列表

| 用例ID | 测试内容 | 前置条件 | 操作步骤 | 预期结果 |
|--------|---------|---------|---------|---------|
| ISSUE-001 | 页面加载 | 数据库有问题 | 访问 `/issues` | 页面正常加载 |
| ISSUE-002 | 统计卡片显示 | 数据库有不同状态问题 | 检查统计卡片区域 | 显示待处理、处理中、已解决、全部问题数量 |
| ISSUE-003 | 问题列表显示 | 数据库有问题 | 检查表格区域 | 显示问题列表，包含ID、资产、规则、状态、优先级等 |
| ISSUE-004 | 按状态筛选 | 数据库有不同状态问题 | 选择状态筛选器 | 列表按状态过滤，统计API重新调用 |
| ISSUE-005 | 按优先级筛选 | 数据库有不同优先级问题 | 选择优先级筛选器 | 列表按优先级过滤 |
| ISSUE-006 | 搜索问题 | 数据库有多个问题 | 输入关键词搜索 | 列表实时过滤（防抖300ms） |
| ISSUE-007 | 点击统计卡片筛选 | 在统计卡片区域 | 点击"待处理"卡片 | 状态筛选器自动选择"待处理"，列表刷新 |
| ISSUE-008 | 查看问题详情 | 问题列表 | 点击"查看详情"按钮 | 弹出详情模态框，显示完整信息 |
| ISSUE-009 | 问题详情-基本信息 | 打开详情模态框 | 检查模态框内容 | 显示标题、描述、资产、规则、状态、优先级 |
| ISSUE-010 | 问题详情-异常数据 | 问题有异常数据 | 检查模态框 | 显示异常数据表格 |
| ISSUE-011 | 更新问题状态 | 打开详情模态框 | 选择新状态→点击"更新状态" | 调用 PUT `/api/v1/issues/<id>/status`，返回200 |
| ISSUE-012 | 重新校验问题 | 打开详情模态框 | 点击"重新校验"按钮 | 调用 POST `/api/v1/issues/<id>/recheck`，返回200 |
| ISSUE-013 | 状态流转 | 更新状态后 | 检查列表 | 问题状态已更新，统计卡片数值变化 |
| ISSUE-014 | 批量操作按钮 | 选中多个问题 | 检查批量操作栏 | "忽略选中"和"重新校验"按钮变为可用 |
| ISSUE-015 | 问题列表API | 页面加载 | 监听网络请求 | 调用 GET `/api/v1/issues`，返回200 |
| ISSUE-016 | 统计API | 页面加载 | 监听网络请求 | 调用 GET `/api/v1/statistics/overview`，返回200 |
| ISSUE-017 | 问题详情API | 查看详情时 | 监听网络请求 | 调用 GET `/api/v1/issues/<id>`，返回200 |

### 3.6 校验历史页面测试（test_validations.py）

#### 测试用例列表

| 用例ID | 测试内容 | 前置条件 | 操作步骤 | 预期结果 |
|--------|---------|---------|---------|---------|
| VALID-001 | 页面加载 | 数据库有校验记录 | 访问 `/validations` | 页面正常加载 |
| VALID-002 | 校验列表显示 | 数据库有校验记录 | 检查表格区域 | 显示校验历史列表 |
| VALID-003 | 查看详情跳转 | 有校验记录 | 点击"查看详情" | 跳转到 `/validations/<history_id>` |
| VALID-004 | 校验历史API | 页面加载 | 监听网络请求 | 调用 GET `/api/v1/validations/history`，返回200 |

### 3.7 校验详情页面测试（test_validation_detail.py）

#### 测试用例列表

| 用例ID | 测试内容 | 前置条件 | 操作步骤 | 预期结果 |
|--------|---------|---------|---------|---------|
| VDETAIL-001 | 页面加载 | 数据库有校验记录 | 访问 `/validations/1` | 页面正常加载 |
| VDETAIL-002 | 校验基本信息 | 页面加载 | 检查头部区域 | 显示校验ID、状态、执行时间、触发类型等 |
| VDETAIL-003 | 规则结果列表 | 校验有规则结果 | 检查规则结果区域 | 显示各规则的校验结果（成功/失败） |
| VDETAIL-004 | 异常数据表格 | 有失败的规则 | 选择失败规则 | 显示异常数据表格 |
| VDETAIL-005 | 下载异常数据 | 有异常数据 | 点击"下载CSV"按钮 | 调用下载API，触发文件下载 |
| VDETAIL-006 | 校验详情API | 页面加载 | 监听网络请求 | 调用 GET `/api/v1/validations/history/1`，返回200 |
| VDETAIL-007 | 规则结果API | 页面加载 | 监听网络请求 | 调用 GET `/api/v1/validations/history/1/rules`，返回200 |
| VDETAIL-008 | 异常数据API | 选择规则后 | 监听网络请求 | 调用 GET `/api/v1/validations/history/1/exceptions`，返回200 |

## 四、测试数据准备

### 4.1 测试数据库初始化脚本

创建 `tests/fixtures/init_test_data.py`：

```python
"""
测试数据初始化脚本
创建测试用的资产、规则、校验记录、问题等数据
"""

def create_test_assets(session):
    """创建测试资产"""
    assets = [
        {
            'name': '测试用户数据',
            'asset_type': 'file',
            'datasource_type': 'local_file',
            'datasource_path': '/data/test_users.csv',
            'owner': '测试员',
            'weight': 5,
            'status': 'active'
        },
        {
            'name': '测试订单数据',
            'asset_type': 'file',
            'datasource_type': 'local_file',
            'datasource_path': '/data/test_orders.csv',
            'owner': '测试员',
            'weight': 8,
            'status': 'active'
        }
    ]
    # 插入数据库...

def create_test_rules(session):
    """创建测试规则"""
    rules = [
        {
            'asset_id': 1,
            'name': '用户ID非空校验',
            'rule_type': 'completeness',
            'column_name': 'user_id',
            'strength': 'strong',
            'enabled': True
        },
        {
            'asset_id': 1,
            'name': '邮箱格式校验',
            'rule_type': 'validity',
            'column_name': 'email',
            'strength': 'weak',
            'enabled': True
        }
    ]
    # 插入数据库...

def create_test_issues(session):
    """创建测试问题"""
    issues = [
        {
            'asset_id': 1,
            'rule_id': 1,
            'title': '用户ID存在空值',
            'status': 'pending',
            'priority': 'high',
            'description': '发现5条记录的用户ID为空'
        },
        {
            'asset_id': 1,
            'rule_id': 2,
            'title': '邮箱格式不正确',
            'status': 'processing',
            'priority': 'medium',
            'description': '发现3条记录的邮箱格式错误'
        }
    ]
    # 插入数据库...
```

### 4.2 测试文件准备

在 `tests/fixtures/files/` 目录准备：

- `test_users.csv` - 包含用户数据的CSV文件（用于上传测试）
- `test_orders.csv` - 包含订单数据的CSV文件

示例 `test_users.csv`：
```csv
user_id,username,email,age
1,张三,zhangsan@example.com,25
2,李四,lisi@example.com,30
3,王五,,28
,赵六,zhaoliu@example.com,35
5,孙七,sunqi@invalid,22
```

## 五、测试执行策略

### 5.1 测试模式

#### 模式1: 有头模式（Headed Mode）
- 用于调试和演示
- 可以看到浏览器操作过程
- 命令: `pytest tests/e2e/ --headed --slowmo=500`

#### 模式2: 无头模式（Headless Mode）
- 用于CI/CD和批量测试
- 执行速度快
- 命令: `pytest tests/e2e/ --headed=False`

#### 模式3: UI模式（UI Mode）
- 用于测试开发和调试
- 提供时间旅行调试功能
- 命令: `pytest tests/e2e/ --ui`

### 5.2 测试执行顺序

```
Phase 1: 页面加载测试（独立，无依赖）
  ├─ DASH-001: 质量大盘加载
  ├─ ASSET-001: 资产管理加载
  ├─ RULE-001: 规则配置加载
  ├─ ISSUE-001: 问题管理加载
  └─ VALID-001: 校验历史加载

Phase 2: 数据展示测试（需要测试数据）
  ├─ DASH-002~006: 大盘统计和问题列表
  ├─ ASSET-002~006: 资产列表、搜索、筛选
  ├─ ISSUE-002~007: 问题统计、列表、筛选
  └─ VALID-002~003: 校验列表

Phase 3: 交互操作测试（修改数据）
  ├─ ASSET-003~004: 创建资产（文件上传）
  ├─ RULE-002~016: 规则配置向导全流程
  ├─ ISSUE-008~013: 问题详情和状态流转
  └─ ASSET-007: 删除资产

Phase 4: API对接测试（验证网络请求）
  ├─ 所有页面的API调用验证
  ├─ 请求参数验证
  ├─ 响应数据验证
  └─ 错误处理验证
```

### 5.3 测试隔离

- 每个测试用例独立运行，不依赖其他测试的状态
- 使用 `@pytest.fixture(autouse=True)` 自动清理测试数据
- 测试前后执行数据库回滚

## 六、预期结果与通过标准

### 6.1 通过标准

- **核心流程**: 100% 通过（P0用例）
- **主要功能**: ≥ 90% 通过（P0+P1用例）
- **全部功能**: ≥ 80% 通过（所有用例）
- **API对接**: 100% 已连接的API都能正确调用
- **错误处理**: 所有错误场景都有用户提示

### 6.2 失败处理

- 截图保存失败现场
- 录制视频（可选）
- 保存页面HTML
- 记录控制台错误日志
- 记录网络请求日志

## 七、测试报告

### 7.1 报告内容

- 测试执行摘要（总数、通过、失败、跳过）
- 按模块统计通过率
- 失败用例详情（含截图）
- API调用统计
- 性能指标（页面加载时间、API响应时间）

### 7.2 报告格式

- HTML报告（Playwright自带）
- JUnit XML报告（用于CI/CD集成）
- 自定义Markdown报告

## 八、后续优化建议

### 8.1 短期优化（1-2周）

1. 补充缺失的前端功能（编辑按钮、规则编辑等）
2. 完善错误处理的用户提示
3. 增加API响应时间的断言

### 8.2 中期优化（1个月）

1. 实现调度管理和告警管理的前端界面
2. 增加性能测试（页面加载时间、API响应时间）
3. 实现视觉回归测试（截图对比）

### 8.3 长期优化（2-3个月）

1. 集成到CI/CD流程（GitHub Actions）
2. 实现自动化每日回归测试
3. 增加移动端兼容性测试
4. 实现API契约测试（OpenAPI Spec验证）

## 九、环境配置步骤

### 9.1 安装Playwright

```bash
# 激活虚拟环境
D:\Python\venv310\Scripts\activate.bat

# 安装Playwright
pip install playwright pytest-playwright

# 安装浏览器
playwright install chromium
```

### 9.2 项目结构

```
tests/
├── conftest.py              # 全局fixture配置
├── fixtures/                # 测试数据
│   ├── init_test_data.py    # 数据初始化脚本
│   └── files/               # 测试文件
│       ├── test_users.csv
│       └── test_orders.csv
├── e2e/                     # E2E测试用例
│   ├── test_dashboard.py
│   ├── test_assets.py
│   ├── test_asset_detail.py
│   ├── test_rule_config.py
│   ├── test_issues.py
│   ├── test_validations.py
│   └── test_validation_detail.py
├── utils/                   # 测试工具函数
│   └── api_helpers.py       # API辅助函数
├── pages/                   # Page Object Model
│   ├── dashboard_page.py
│   ├── assets_page.py
│   ├── rule_config_page.py
│   └── issues_page.py
├── pytest.ini               # pytest配置
└── playwright.config.py     # Playwright配置
```

## 十、风险与注意事项

### 10.1 已知风险

1. **测试数据污染**: 测试可能修改数据库，需确保测试后回滚
2. **异步加载**: 前端大量使用异步API，需正确处理等待逻辑
3. **端口冲突**: 确保5000端口未被占用
4. **浏览器兼容性**: 当前只测试Chromium，后续需扩展

### 10.2 注意事项

1. 测试执行前确保Flask服务已启动
2. 使用独立的测试数据库或事务回滚
3. 测试文件路径使用绝对路径
4. 截图和视频保存在 `test-results/` 目录
5. 敏感信息（如API密钥）不要写入测试代码
