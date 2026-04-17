# 规则配置页面重构计划

## 📅 创建日期
**2026-04-15**

---

## 🎯 重构目标

根据用户反馈，将规则配置页面从**3步向导式**改为**单页式布局**，并实现以下改进：

### 核心需求
1. ✅ **后端API已添加**: `GET /api/v1/assets/{asset_id}/columns` - 获取资产字段列表
2. ⏸️ **前端重构待完成**: 
   - 选择式而非输入式（从后端读取字段列表）
   - 合并模板选择和参数配置为一个页面
   - 支持多字段选择（多选框/下拉框）

---

## 📋 当前状态分析

### 已完成
- ✅ 后端API: `/api/v1/assets/<int:asset_id>/columns`
  - 支持CSV/Excel文件读取表头
  - 支持Database/API类型（示例数据）
  - 返回字段名和类型

- ✅ 前端已有基础功能:
  - 7种规则模板定义
  - 资产选择器（当URL无asset_id时）
  - 动态参数表单生成
  - SQL预览

### 待改进
- ❌ 仍使用3步向导（步骤条）
- ❌ 字段输入为文本框（非选择式）
- ❌ 模板选择和参数配置分离
- ❌ 未调用后端API获取字段列表

---

## 🏗️ 重构方案

### 方案A: 渐进式重构（推荐）

**优点**: 
- 保留现有代码结构
- 逐步替换组件
- 风险较低

**步骤**:
1. 隐藏步骤条，改为单页显示
2. 左侧边栏：模板列表 + 资产选择
3. 右侧主区域：配置表单（基本信息 + 参数 + SQL预览）
4. 添加字段选择器组件（调用后端API）
5. 参数类型改为select/multi-select

**预计工作量**: 4-6小时

---

### 方案B: 完全重写

**优点**:
- 代码更清晰
- 架构更合理
- 易于维护

**缺点**:
- 工作量大
- 需要充分测试

**步骤**:
1. 创建新的HTML模板 `rule_config_v2.html`
2. 创建新的JS文件 `rule_config_v2.js`
3. 实现左右分栏布局
4. 集成字段选择器
5. 测试后替换旧版本

**预计工作量**: 8-10小时

---

## 📐 新页面布局设计

```
┌─────────────────────────────────────────────────────┐
│  规则配置 - DataQ 数质宝                              │
├──────────────┬──────────────────────────────────────┤
│              │                                      │
│  【左侧边栏】  │        【右侧主区域】                 │
│              │                                      │
│  📋 选择模板  │  ┌────────────────────────────┐    │
│  ┌────────┐  │  │  完整性校验                  │    │
│  │✅ 完整性│  │  │  检查字段是否为空             │    │
│  ├────────┤  │  └────────────────────────────┘    │
│  │🔑 唯一性│  │                                      │
│  ├────────┤  │  ┌────────────────────────────┐    │
│  │✔️ 有效性│  │  │  选择资产                    │    │
│  ├────────┤  │  │  [下拉框: 用户数据表 ▼]      │    │
│  │📊 范围  │  │  └────────────────────────────┘    │
│  ├────────┤  │                                      │
│  │⏰ 及时性│  │  ┌────────────────────────────┐    │
│  ├────────┤  │  │  规则名称                    │    │
│  │🔗 一致性│  │  │  [输入框: ______________]    │    │
│  ├────────┤  │  └────────────────────────────┘    │
│  │💻 自定义│  │                                      │
│  └────────┘  │  ┌────────────────────────────┐    │
│              │  │  选择字段 (可多选)           │    │
│  🏠 选择资产  │  │  ☑ user_id                 │    │
│  ┌────────┐  │  │  ☑ email                   │    │
│  │[下拉框] │  │  │  ☐ phone                   │    │
│  └────────┘  │  │  ☐ created_at              │    │
│              │  └────────────────────────────┘    │
│              │                                      │
│              │  ┌────────────────────────────┐    │
│              │  │  规则强度                    │    │
│              │  │  ○ 强规则  ○ 弱规则         │    │
│              │  └────────────────────────────┘    │
│              │                                      │
│              │  ┌────────────────────────────┐    │
│              │  │  SQL预览                     │    │
│              │  │  SELECT COUNT(*) ...        │    │
│              │  └────────────────────────────┘    │
│              │                                      │
│              │  [取消] [保存规则]                  │
└──────────────┴──────────────────────────────────────┘
```

---

## 🔧 技术实现细节

### 1. 后端API增强（已完成✅）

**接口**: `GET /api/v1/assets/{asset_id}/columns`

**返回格式**:
```json
{
  "status": "success",
  "data": {
    "asset_id": 1,
    "asset_name": "用户数据表",
    "columns": [
      {"name": "user_id", "type": "integer"},
      {"name": "username", "type": "string"},
      {"name": "email", "type": "string"},
      {"name": "phone", "type": "string"},
      {"name": "created_at", "type": "datetime"}
    ],
    "total": 5
  }
}
```

**实现逻辑**:
- CSV/Excel: 使用pandas读取表头
- Database: 查询information_schema（待实现）
- API: 返回示例字段（待优化）

---

### 2. 前端组件设计

#### 2.1 模板选择器（左侧边栏）

```javascript
// 紧凑的模板列表项
function renderTemplateList() {
    return TEMPLATES.map(template => `
        <div class="template-item" data-template-id="${template.id}" 
             onclick="selectTemplate('${template.id}')">
            <div class="template-icon">${template.icon}</div>
            <div class="template-info">
                <div class="template-name">${template.name}</div>
                <div class="template-desc">${template.description}</div>
            </div>
        </div>
    `).join('');
}
```

#### 2.2 资产选择器

```javascript
async function loadAssetSelector() {
    const response = await apiRequest(`${API_BASE_URL}/assets?page=1&per_page=100`);
    const assets = Array.isArray(response.data) ? response.data : (response.data.assets || []);
    
    const selector = document.getElementById('asset-selector');
    selector.innerHTML = '<option value="">-- 请选择资产 --</option>' +
        assets.map(asset => 
            `<option value="${asset.id}">${asset.name} (${asset.asset_type})</option>`
        ).join('');
}
```

#### 2.3 字段选择器（核心改进）

```javascript
async function loadFieldSelector(assetId) {
    if (!assetId) return;
    
    try {
        const response = await apiRequest(`${API_BASE_URL}/assets/${assetId}/columns`);
        const columns = response.data.columns || [];
        
        // 渲染多选框
        const container = document.getElementById('field-selector-container');
        container.innerHTML = columns.map(col => `
            <label class="field-checkbox">
                <input type="checkbox" name="selected_fields" value="${col.name}">
                <span>${col.name}</span>
                <span class="field-type">${col.type}</span>
            </label>
        `).join('');
        
    } catch (error) {
        showError('加载字段列表失败: ' + error.message);
    }
}

// 获取选中的字段
function getSelectedFields() {
    const checkboxes = document.querySelectorAll('input[name="selected_fields"]:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}
```

#### 2.4 参数表单生成器

```javascript
function renderConfigForm(template) {
    let html = '';
    
    // 基本信息
    html += `
        <div class="form-section">
            <div class="form-group">
                <label>规则名称 <span class="required">*</span></label>
                <input type="text" id="rule-name" required>
            </div>
            
            <div class="form-group">
                <label>规则强度</label>
                <div class="radio-group">
                    <label><input type="radio" name="strength" value="strong" checked> 强规则</label>
                    <label><input type="radio" name="strength" value="weak"> 弱规则</label>
                </div>
            </div>
        </div>
    `;
    
    // 字段选择（针对需要字段的模板）
    if (template.params.some(p => p.name === 'column_name')) {
        html += `
            <div class="form-section">
                <label>选择字段 <span class="required">*</span></label>
                <div id="field-selector-container" class="field-selector">
                    <!-- 动态加载字段列表 -->
                </div>
                <div class="form-hint">可选择多个字段，用逗号分隔</div>
            </div>
        `;
    }
    
    // 其他参数
    template.params.forEach(param => {
        if (param.name !== 'column_name') {
            html += renderParamField(param);
        }
    });
    
    return html;
}
```

---

### 3. CSS样式设计

```css
/* 字段选择器 */
.field-selector {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 0.75rem;
    padding: 1rem;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    max-height: 300px;
    overflow-y: auto;
}

.field-checkbox {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem;
    border-radius: 4px;
    cursor: pointer;
    transition: background 0.2s;
}

.field-checkbox:hover {
    background: #f5f7fa;
}

.field-checkbox input[type="checkbox"] {
    width: 18px;
    height: 18px;
    cursor: pointer;
}

.field-type {
    margin-left: auto;
    font-size: 0.75rem;
    color: #999;
    background: #f0f0f0;
    padding: 2px 6px;
    border-radius: 3px;
}
```

---

## 📝 实施步骤

### Phase 1: 后端API测试（30分钟）
1. 启动Flask应用
2. 测试`GET /api/v1/assets/1/columns`
3. 验证CSV文件字段读取
4. 检查返回格式

### Phase 2: 前端布局重构（2小时）
1. 修改HTML结构（移除步骤条）
2. 实现左右分栏布局
3. 添加模板列表样式
4. 调整响应式设计

### Phase 3: 字段选择器开发（2小时）
1. 实现loadFieldSelector函数
2. 创建多选框UI
3. 添加全选/反选功能
4. 集成到参数表单

### Phase 4: 表单逻辑优化（1.5小时）
1. 修改selectTemplate函数
2. 更新renderConfigForm
3. 实现getSelectedFields
4. 调整SQL生成逻辑

### Phase 5: 测试与调试（1小时）
1. 测试不同资产类型
2. 验证字段选择功能
3. 检查SQL预览
4. 测试规则创建

---

## 🎯 预期效果

### 用户体验提升
- ✅ **一步到位**: 无需点击"下一步"，所有配置在一个页面
- ✅ **可视化选择**: 字段列表直观展示，勾选即可
- ✅ **实时反馈**: 选择资产后立即加载字段
- ✅ **减少错误**: 避免手动输入字段名拼写错误

### 开发效率提升
- ✅ **代码简化**: 移除步骤管理逻辑
- ✅ **易于扩展**: 新增模板只需添加到TEMPLATES数组
- ✅ **维护方便**: 单一页面结构清晰

---

## ⚠️ 注意事项

1. **向后兼容**: 保留旧的3步向导作为fallback
2. **性能优化**: 字段列表超过100个时启用虚拟滚动
3. **错误处理**: 资产无字段时的友好提示
4. **移动端适配**: 小屏幕改为上下布局

---

## 📊 进度跟踪

| 任务 | 状态 | 预计时间 | 实际时间 |
|------|------|---------|---------|
| 后端API开发 | ✅ 完成 | 30min | 30min |
| HTML布局重构 | ⏸️ 待开始 | 2h | - |
| 字段选择器开发 | ⏸️ 待开始 | 2h | - |
| 表单逻辑优化 | ⏸️ 待开始 | 1.5h | - |
| 测试与调试 | ⏸️ 待开始 | 1h | - |
| **总计** | **20%完成** | **7h** | **30min** |

---

## 🚀 下一步行动

**建议**: 在下次会话中继续完成前端重构，或先测试当前已修复的其他功能（Toast消息、统计卡片点击、API配置等）。

**快速验证后端API**:
```bash
# 启动Flask
python src/backend/app.py

# 测试API（浏览器访问）
http://localhost:5000/api/v1/assets/1/columns
```

---

**文档版本**: v1.0  
**最后更新**: 2026-04-15  
**作者**: AI Assistant
