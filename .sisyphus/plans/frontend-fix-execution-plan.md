# DataQ 前端修复执行计划

## 问题说明
当前系统存在以下 3 个前端问题：
1. ❌ **缺少 jQuery 引入** - 导致 `$ is not defined` 错误
2. ❌ **校验历史页面报错** - `Unexpected token '<'` 错误
3. ❌ **数据预览功能不可用** - 资产详情页数据预览不显示

---

## 执行修复步骤

### ✅ 修复 1: base.html 添加 jQuery

**文件**: `src/frontend/templates/base.html`  
**行号**: 第 46-48 行

**修改前**:
```html
    <!-- 引入脚本 -->
    <script src="{{ url_for('static', filename='js/common.js') }}"></script>
    {% block extra_js %}{% endblock %}
```

**修改后** (替换为):
```html
    <!-- 引入 jQuery -->
    <script src="https://cdn.jsdelivr.net/npm/jquery@3.7.1/dist/jquery.min.js"></script>
    <!-- 引入通用脚本 -->
    <script src="{{ url_for('static', filename='js/common.js') }}"></script>
    {% block extra_js %}{% endblock %}
```

---

### ✅ 修复 2: 完整替换 validations.js

**文件**: `src/frontend/static/js/validations.js`  
**操作**: 删除原有内容，完全替换为以下内容:

```javascript
// DataQ 数质宝 - 校验历史页面

document.addEventListener('DOMContentLoaded', function() {
    loadValidations();
});

async function loadValidations() {
    try {
        const response = await apiRequest(`${API_BASE_URL}/validations/history`);
        // 兼容两种数据格式：{data: [...]} 或 {data: {histories: [...]}}
        const histories = Array.isArray(response.data) 
            ? response.data 
            : (response.data.histories || []);
        
        const tbody = document.getElementById('validations-table-body');
        
        if (histories.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="loading">暂无数据</td></tr>';
            return;
        }
        
        tbody.innerHTML = histories.map(history => `
            <tr>
                <td>#${history.id}</td>
                <td>${history.asset_name || '-'}</td>
                <td>${history.total_rules || 0}</td>
                <td>${(history.success_rate || 0).toFixed(1)}%</td>
                <td>${getStatusBadge(history.status)}</td>
                <td>${formatDate(history.created_at)}</td>
                <td>
                    <button class="btn btn-primary btn-sm" onclick="viewValidationDetail(${history.id})">详情</button>
                    <button class="btn btn-outline-primary btn-sm" onclick="exportJson(${history.id})" title="导出JSON结果">
                        <i class="fas fa-download"></i> 导出
                    </button>
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('加载校验历史失败:', error);
        showError('加载校验历史失败: ' + error.message);
    }
}

function viewValidationDetail(historyId) {
    // 跳转到校验详情页
    window.location.href = `/validations/${historyId}`;
}

function exportJson(historyId) {
    window.open(`${API_BASE_URL}/validations/history/${historyId}/export/json?download=true`, '_blank');
}
```

---

### ✅ 修复 3: asset_detail.js 添加数据预览

**文件**: `src/frontend/static/js/asset_detail.js`  
**位置**: 文件末尾（第 503 行附近）  
**操作**: 替换旧的预览代码（如果有）或追加以下内容:

```javascript
// ========== 数据预览功能 ==========

// 点击预览标签时加载数据
$(document).on('click', '#tab-preview', function() {
    loadDataPreview();
});

function loadDataPreview() {
    const assetId = getAssetIdFromUrl();
    
    $.ajax({
        url: `${API_BASE_URL}/assets/${assetId}/preview`,
        method: 'GET',
        success: function(response) {
            if (response.status === 'success') {
                renderDataPreview(response.data);
            } else {
                $('#preview-header').html('<tr><th class="text-danger">加载失败: ' + (response.message || '未知错误') + '</th></tr>');
            }
        },
        error: function(xhr) {
            const msg = xhr.responseJSON?.message || '加载数据预览失败';
            $('#preview-header').html('<tr><th class="text-danger">加载失败: ' + msg + '</th></tr>');
        }
    });
}

function renderDataPreview(data) {
    // 更新统计信息
    $('#preview-stats').html(`
        <span class="badge badge-info">总列数: <span id="col-count">${data.total_columns}</span></span>
        <span class="badge badge-info">总行数: <span id="row-count">${data.total_rows}</span></span>
        <span class="badge badge-secondary">预览: 前 <span id="preview-count">${data.preview_rows}</span> 行</span>
    `);
    
    // 渲染表头
    let headerHtml = '<tr>';
    data.columns.forEach(col => {
        headerHtml += `<th class="table-cell-truncate" title="${col}">${col}</th>`;
    });
    headerHtml += '</tr>';
    $('#preview-header').html(headerHtml);
    
    // 渲染数据行
    let bodyHtml = '';
    data.rows.forEach(row => {
        bodyHtml += '<tr>';
        row.forEach(cell => {
            const cellValue = cell === null || cell === undefined ? '' : String(cell);
            bodyHtml += `<td class="table-cell-truncate" title="${cellValue}">${cellValue}</td>`;
        });
        bodyHtml += '</tr>';
    });
    $('#preview-body').html(bodyHtml);
}

function getAssetIdFromUrl() {
    const pathParts = window.location.pathname.split('/');
    return pathParts[pathParts.length - 1];
}
```

---

## 验证步骤

按顺序执行以下验证：

| 序号 | 验证项 | 操作 | 预期结果 |
|-----|-------|-----|---------|
| 1 | jQuery 已加载 | F12 打开控制台，输入 `$` | 输出函数代码，无报错 |
| 2 | 校验历史页面正常 | 访问 `/validations` | 表格正常显示，无 `Unexpected token '<'` 错误 |
| 3 | 数据预览可用 | 进入资产详情页，点击"数据预览"标签 | 表格正确显示数据，统计信息正确 |
| 4 | 导出功能可用 | 在历史列表页点击"导出"按钮 | 正确下载 JSON 文件 |

---

## 回滚方案

如果出现问题，按以下优先级恢复：

1. **紧急回滚**: `git checkout HEAD -- src/frontend/templates/base.html src/frontend/static/js/validations.js src/frontend/static/js/asset_detail.js`
2. **分步排查**: 先只恢复 base.html，确认无问题后再调整 JS
3. **日志收集**: 截图保存控制台错误、Network 面板请求信息，便于排查问题

---

## 前置依赖确认

修改前请确认以下全局函数已存在（由 common.js 提供）：
- ✅ `API_BASE_URL` 变量
- ✅ `apiRequest()` 函数
- ✅ `formatDate()` 函数
- ✅ `getStatusBadge()` 函数
- ✅ `showError()` 函数

如果缺少任何一项，请先修复依赖再执行本计划。

---

**预计修改时间**: 5 分钟  
**预计验证时间**: 3 分钟  
**总计**: 8 分钟
