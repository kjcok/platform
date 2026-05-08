/**
 * 资产详情页交互逻辑
 */

// 注：API_BASE_URL 已在 common.js 中声明，此处不重复声明
// const API_BASE_URL = '/api/v1';  // 注释掉，使用common.js中的

let currentAsset = null;
let currentTab = 'rules';

/**
 * 初始化标签页
 */
function initTabs() {
    console.log('=== initTabs 被调用 ===');
    const tabs = document.querySelectorAll('.tab');
    console.log('找到标签数量:', tabs.length);
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            console.log('点击了标签:', tabName);
            switchTab(tabName);
        });
    });
}

/**
 * 切换标签页
 */
function switchTab(tabName) {
    console.log('=== switchTab 被调用 === 目标标签:', tabName);
    currentTab = tabName;
    
    // 更新标签样式
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    
    // 更新内容显示
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    const contentEl = document.getElementById(`tab-${tabName}`);
    console.log('找到内容元素:', contentEl ? '是' : '否');
    if (contentEl) {
        contentEl.classList.add('active');
    }
    
    // 加载对应数据
    if (tabName === 'rules') {
        loadRules();
    } else if (tabName === 'validations') {
        loadValidations();
    } else if (tabName === 'issues') {
        loadIssues();
    } else if (tabName === 'preview') {
        console.log('>>> 准备调用 loadDataPreview');
        loadDataPreview();
    }
}

/**
 * 初始化
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('=== DOMContentLoaded 触发 ===');
    console.log('页面脚本已加载');
    loadAssetDetail();
    initTabs();
    
    // 先加载规则
    switchTab('rules');
});

/**
 * 加载资产详情
 */
async function loadAssetDetail() {
    try {
        const response = await apiRequest(`${API_BASE_URL}/assets/${assetId}`);
        currentAsset = response.data;
        renderAssetHeader(currentAsset);
        
    } catch (error) {
        showError('加载资产详情失败: ' + error.message);
    }
}

/**
 * 渲染资产头部
 */
function renderAssetHeader(asset) {
    const headerHtml = `
        <div class="asset-header-top">
            <div class="asset-title-group">
                <div class="asset-name">${asset.name}</div>
                <div class="asset-meta">
                    <div class="asset-meta-item">
                        <span>📁</span>
                        <span>${asset.asset_type || '文件'}</span>
                    </div>
                    <div class="asset-meta-item">
                        <span>👤</span>
                        <span>${asset.owner || '未设置'}</span>
                    </div>
                    <div class="asset-meta-item">
                        <span>📊</span>
                        <span>质量权重: ${asset.weight || 5}</span>
                    </div>
                </div>
            </div>
            <div class="asset-actions">
                <button class="btn btn-primary" onclick="configureRule()">配置规则</button>
                <button class="btn btn-secondary" onclick="editAsset()">编辑资产</button>
            </div>
        </div>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">资产ID</div>
                <div class="info-value">#${asset.id}</div>
            </div>
            <div class="info-item">
                <div class="info-label">数据源类型</div>
                <div class="info-value">${asset.datasource_type || '本地文件'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">数据源路径</div>
                <div class="info-value">${asset.datasource_path || '-'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">创建时间</div>
                <div class="info-value">${formatDate(asset.created_at)}</div>
            </div>
        </div>
    `;
    
    document.getElementById('asset-header').innerHTML = headerHtml;
}

/**
 * 加载规则列表
 */
async function loadRules() {
    try {
        const response = await apiRequest(`${API_BASE_URL}/assets/${assetId}/rules`);
        const rules = response.data.rules;
        renderRulesList(rules);
        
        // 更新规则数量徽章
        const badge = document.getElementById('rules-count-badge');
        if (badge) {
            badge.textContent = rules ? rules.length : 0;
        }
        
    } catch (error) {
        showError('加载规则列表失败: ' + error.message);
    }
}

/**
 * 渲染规则列表
 */
function renderRulesList(rules) {
    const container = document.getElementById('rules-list');
    
    if (!rules || rules.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📋</div>
                <div class="empty-text">暂无规则</div>
                <button class="btn btn-primary" onclick="configureRule()">添加第一个规则</button>
            </div>
        `;
        return;
    }
    
    let html = '';
    rules.forEach(rule => {
        const shortLabel = getShortRuleLabel(rule.ge_expectation);
        const paramsText = formatRuleParams(rule.parameters);
        html += `
            <div class="rule-card">
                <div class="rule-card-header">
                    <div class="rule-name">${rule.name}<span class="rule-type-badge">${shortLabel}</span></div>
                </div>
                <div class="rule-info">
                    <div class="rule-info-item">
                        <div class="rule-info-label">字段</div>
                        <div class="rule-info-value">${rule.column_name || '-'}</div>
                    </div>
                    <div class="rule-info-item">
                        <div class="rule-info-label">状态</div>
                        <div class="rule-info-value">${rule.enabled ? '✅ 已启用' : '⏸️ 已禁用'}</div>
                    </div>
                </div>
                <div class="rule-params">${paramsText}</div>
                ${rule.description ? `<div class="rule-description">${rule.description}</div>` : ''}
                <div class="rule-actions">
                    <button class="btn btn-secondary btn-small" onclick="editRule(${rule.id})">编辑</button>
                    <button class="btn btn-danger btn-small" onclick="deleteRule(${rule.id})">删除</button>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

/**
 * 加载校验历史
 */
async function loadValidations() {
    try {
        const response = await apiRequest(`${API_BASE_URL}/assets/${assetId}/validations?limit=20`);
        const validations = response.data.validations;
        renderValidationsList(validations);
        
    } catch (error) {
        showError('加载校验历史失败: ' + error.message);
    }
}

/**
 * 渲染校验历史列表
 */
function renderValidationsList(validations) {
    const container = document.getElementById('validations-list');
    
    if (!validations || validations.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📊</div>
                <div class="empty-text">暂无校验记录</div>
            </div>
        `;
        return;
    }
    
    // 复用validations.html的渲染逻辑
    let html = '<table class="data-table"><thead><tr>';
    html += '<th>校验ID</th><th>执行时间</th><th>执行结果</th><th>状态</th><th>操作</th>';
    html += '</tr></thead><tbody>';
    
    validations.forEach(v => {
        const statusClass = v.status === 'success' ? 'status-success' : 'status-failed';
        const statusText = v.status === 'success' ? '成功' : '失败';
        
        html += `<tr>
            <td>#${v.id}</td>
            <td>${formatDate(v.executed_at)}</td>
            <td><span class="status-badge ${statusClass}">${statusText}</span></td>
            <td>${v.trigger_type === 'manual' ? '手动触发' : '定时任务'}</td>
            <td>
                <button class="btn btn-secondary" onclick="viewValidationDetail(${v.id})">查看详情</button>
            </td>
        </tr>`;
    });
    
    html += '</tbody></table>';
    container.innerHTML = html;
}

/**
 * 加载问题记录
 */
async function loadIssues() {
    try {
        const response = await apiRequest(`${API_BASE_URL}/assets/${assetId}/issues?limit=20`);
        const issues = response.data.issues;
        renderIssuesList(issues);
        
    } catch (error) {
        showError('加载问题记录失败: ' + error.message);
    }
}

/**
 * 渲染问题列表
 */
function renderIssuesList(issues) {
    const container = document.getElementById('issues-list');
    
    if (!issues || issues.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">✅</div>
                <div class="empty-text">暂无问题记录</div>
            </div>
        `;
        return;
    }
    
    let html = '<table class="data-table"><thead><tr>';
    html += '<th>问题ID</th><th>规则</th><th>字段</th><th>问题类型</th><th>严重程度</th><th>状态</th><th>操作</th>';
    html += '</tr></thead><tbody>';
    
    issues.forEach(issue => {
        const statusClass = `status-${issue.status}`;
        const statusText = getStatusText(issue.status);
        const priorityClass = `priority-${issue.priority}`;
        const priorityText = getPriorityText(issue.priority);
        
        html += `<tr>
            <td>#${issue.id}</td>
            <td>${issue.rule_name || '-'}</td>
            <td>${issue.column_name || '-'}</td>
            <td>${issue.issue_type || '-'}</td>
            <td><span class="status-badge ${priorityClass}">${priorityText}</span></td>
            <td><span class="status-badge ${statusClass}">${statusText}</span></td>
            <td>
                <button class="btn btn-secondary" onclick="viewIssue(${issue.id})">查看详情</button>
            </td>
        </tr>`;
    });
    
    html += '</tbody></table>';
    container.innerHTML = html;
}

/**
 * 配置规则
 */
function configureRule() {
    window.location.href = `/rule-config?asset_id=${assetId}`;
}

/**
 * 编辑资产
 */
function editAsset() {
    showWarning('编辑功能开发中...');
}

/**
 * 编辑规则
 */
function editRule(ruleId) {
    showWarning('规则编辑功能开发中...');
}

/**
 * 删除规则
 */
async function deleteRule(ruleId) {
    if (!confirm('确定要删除这个规则吗？此操作不可恢复。')) {
        return;
    }
    
    try {
        await apiRequest(`${API_BASE_URL}/rules/${ruleId}`, 'DELETE');
        showSuccess('规则删除成功');
        loadRules();
        
    } catch (error) {
        showError('删除规则失败: ' + error.message);
    }
}

/**
 * 查看校验详情
 */
function viewValidationDetail(historyId) {
    window.location.href = `/validations/${historyId}`;
}

/**
 * 查看问题详情
 */
function viewIssue(issueId) {
    window.location.href = `/issues`;
    showWarning('问题详情功能开发中...');
}

/**
 * 辅助函数：获取规则类型标签
 */
function getRuleTypeLabel(type) {
    const typeMap = {
        'completeness': '完整性校验',
        'uniqueness': '唯一性校验',
        'validity': '有效性校验',
        'range': '范围校验',
        'timeliness': '及时性校验',
        'consistency': '一致性校验',
        'custom_sql': '自定义SQL'
    };
    return typeMap[type] || type;
}

/**
 * 辅助函数：GE expectation 映射为精简中文标签
 */
function getShortRuleLabel(geExpectation) {
    const labelMap = {
        'expect_column_values_to_be_between': '数值范围',
        'expect_column_values_to_match_regex': '正则匹配',
        'expect_column_values_to_not_match_regex': '正则排除',
        'expect_column_values_to_match_regex_list': '多正则匹配',
        'expect_column_values_to_not_match_regex_list': '多正则排除',
        'expect_column_values_to_not_be_null': '非空校验',
        'expect_column_values_to_be_null': '为空校验',
        'expect_column_values_to_be_unique': '唯一性',
        'expect_column_values_to_be_in_set': '枚举值',
        'expect_column_values_to_not_be_in_set': '排除值',
        'expect_column_value_lengths_to_be_between': '长度范围',
        'expect_column_value_lengths_to_equal': '固定长度',
        'expect_column_values_to_match_strftime_format': '日期格式',
        'expect_column_values_to_be_dateutil_parseable': '日期可解析',
        'expect_column_values_to_be_increasing': '递增',
        'expect_column_values_to_be_decreasing': '递减',
        'expect_column_values_to_match_like_pattern': 'LIKE匹配',
        'expect_column_values_to_be_like': 'LIKE匹配',
        'expect_column_values_to_be_of_type': '数据类型',
        'expect_column_values_to_be_in_type_list': '类型列表',
        'expect_column_mean_to_be_between': '平均值范围',
        'expect_column_median_to_be_between': '中位数范围',
        'expect_column_stdev_to_be_between': '标准差范围',
        'expect_column_min_to_be_between': '最小值范围',
        'expect_column_max_to_be_between': '最大值范围',
        'expect_column_sum_to_be_between': '总和范围',
        'expect_column_unique_value_count_to_be_between': '唯一值数量',
        'expect_column_percentile_to_be_between': '百分位数',
        'expect_column_quantile_values_to_be_between': '分位数',
        'expect_column_distinct_values_to_be_in_set': '唯一值集合',
        'expect_column_distinct_values_to_contain_set': '唯一值包含',
        'expect_column_distinct_values_to_equal_set': '唯一值等于',
        'expect_column_pair_values_A_to_be_greater_than_B': '列对大于',
        'expect_column_pair_values_to_be_equal': '列对相等',
        'expect_column_pair_values_to_be_between': '列对差值',
        'expect_column_pair_values_to_not_be_null': '配对非空',
        'expect_table_row_count_to_be_between': '行数范围',
        'expect_table_columns_to_match_ordered_list': '列顺序',
        'expect_table_column_count_to_be_between': '列数量',
        'expect_table_columns_to_match_set': '列集合',
        'expect_multicolumn_sum_to_equal': '多列求和',
        'expect_multicolumn_values_to_be_unique': '多列唯一',
        'expect_json_values_to_have_keys': 'JSON键',
        'expect_json_schema_to_match': 'JSON Schema'
    };
    return labelMap[geExpectation] || '规则';
}

/**
 * 辅助函数：格式化规则参数为人类可读文本
 */
function formatRuleParams(parametersJson) {
    if (!parametersJson) return '-';
    
    let params = {};
    try {
        params = JSON.parse(parametersJson);
    } catch (e) {
        return '-';
    }
    
    const truncate = (str, len) => {
        if (!str) return str;
        const s = String(str);
        return s.length > len ? s.substring(0, len) + '...' : s;
    };
    
    const parts = [];
    
    // 范围类：min_value + max_value
    if ('min_value' in params && 'max_value' in params) {
        parts.push(`范围: ${params.min_value} ~ ${params.max_value}`);
    } else if ('min_value' in params) {
        parts.push(`最小值: ${params.min_value}`);
    } else if ('max_value' in params) {
        parts.push(`最大值: ${params.max_value}`);
    }
    
    // 正则
    if ('regex' in params) {
        parts.push(`正则: ${truncate(params.regex, 50)}`);
    }
    if ('regex_list' in params && Array.isArray(params.regex_list)) {
        parts.push(`正则列表: ${truncate(params.regex_list.join(', '), 50)}`);
    }
    
    // LIKE 模式
    if ('like_pattern' in params) {
        parts.push(`LIKE: ${truncate(params.like_pattern, 50)}`);
    } else if ('pattern' in params) {
        parts.push(`LIKE: ${truncate(params.pattern, 50)}`);
    }
    
    // 枚举值
    if ('value_set' in params && Array.isArray(params.value_set)) {
        let display = params.value_set.slice(0, 5).join(', ');
        if (params.value_set.length > 5) display += ', ...';
        parts.push(`允许值: ${display}`);
    }
    
    // 日期格式
    if ('strftime_format' in params) {
        parts.push(`日期格式: ${params.strftime_format}`);
    }
    
    // 数据类型
    if ('type_list' in params && Array.isArray(params.type_list)) {
        parts.push(`类型: ${params.type_list.join(', ')}`);
    }
    if ('type_' in params) {
        parts.push(`类型: ${params.type_}`);
    }
    
    // 通过率
    if ('mostly' in params) {
        const pct = Math.round(parseFloat(params.mostly) * 100);
        parts.push(`通过率 ≥ ${pct}%`);
    }
    
    // 严格模式
    if ('strictly' in params) {
        parts.push(`严格模式: ${params.strictly ? '是' : '否'}`);
    }
    
    // 对比列
    if ('column_B' in params) {
        parts.push(`对比列: ${params.column_B}`);
    }
    
    // JSON 键
    if ('expected_keys' in params && Array.isArray(params.expected_keys)) {
        parts.push(`期望键: ${truncate(params.expected_keys.join(', '), 50)}`);
    }
    
    // 列集合/列表
    if ('column_list' in params && Array.isArray(params.column_list)) {
        parts.push(`列顺序: ${truncate(params.column_list.join(' → '), 50)}`);
    }
    if ('column_set' in params && Array.isArray(params.column_set)) {
        let display = params.column_set.slice(0, 3).join(', ');
        if (params.column_set.length > 3) display += ', ...';
        parts.push(`列集合: ${display}`);
    }
    if ('exact_match' in params) {
        parts.push(`精确匹配: ${params.exact_match}`);
    }
    
    // 多列
    if ('columns_list' in params && Array.isArray(params.columns_list)) {
        let display = params.columns_list.slice(0, 3).join(', ');
        if (params.columns_list.length > 3) display += ', ...';
        parts.push(`参与列: ${display}`);
    }
    if ('sum_total' in params) {
        parts.push(`目标和: ${params.sum_total}`);
    }
    
    // 分位数
    if ('quantiles' in params) {
        parts.push(`分位数: ${params.quantiles}`);
    }
    if ('percentile' in params) {
        parts.push(`百分位: ${params.percentile}`);
    }
    if ('ranges' in params) {
        parts.push(`范围: ${truncate(String(params.ranges), 50)}`);
    }
    
    return parts.length > 0 ? parts.join(' | ') : '-';
}

/**
 * 辅助函数：获取状态文本
 */
function getStatusText(status) {
    const statusMap = {
        'pending': '待处理',
        'processing': '处理中',
        'resolved': '已解决',
        'closed': '已关闭',
        'ignored': '已忽略'
    };
    return statusMap[status] || status;
}

/**
 * 辅助函数：获取优先级文本
 */
function getPriorityText(priority) {
    const priorityMap = {
        'high': '高',
        'medium': '中',
        'low': '低'
    };
    return priorityMap[priority] || priority;
}

/**
 * 辅助函数：格式化日期
 */
function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN');
}

/**
 * API请求封装
 */
async function apiRequest(url, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
    }
    
    const response = await fetch(url, options);
    const result = await response.json();
    
    if (!response.ok) {
        throw new Error(result.message || '请求失败');
    }
    
    return result;
}

// 数据预览功能：DOM 加载完成后绑定事件，避免依赖 jQuery 的时机
document.addEventListener('DOMContentLoaded', function() {
    const previewTab = document.querySelector('[data-tab="preview"]');
    if (previewTab) {
        previewTab.addEventListener('click', function() {
            loadDataPreview();
        });
    }
});

function loadDataPreview() {
    console.log('=== loadDataPreview 被调用 ===');
    
    // 调用 API 获取真实数据预览
    apiRequest(`${API_BASE_URL}/assets/${assetId}/preview`)
        .then(response => {
            console.log('API 返回数据:', response);
            if (response.status === 'success') {
                renderDataPreview(response.data);
            } else {
                showError('加载数据预览失败: ' + (response.message || '未知错误'));
            }
        })
        .catch(error => {
            console.error('数据预览 API 调用失败:', error);
            showError('加载数据预览失败: ' + error.message);
        });
}

// 确保函数在全局作用域可用
window.loadDataPreview = loadDataPreview;

function showPreviewError(message) {
    var headerEl = document.getElementById('preview-header');
    var bodyEl = document.getElementById('preview-body');
    if (headerEl) {
        headerEl.innerHTML = '<tr><th class="text-danger">加载失败: ' + message + '</th></tr>';
    }
    if (bodyEl) {
        bodyEl.innerHTML = '';
    }
}

function renderDataPreview(data) {
    console.log('=== renderDataPreview 被调用 === 数据:', data);
    
    const container = document.getElementById('preview-list');
    console.log('preview-list 容器存在:', !!container);
    
    if (!container) {
        console.error('preview-list 容器不存在!');
        return;
    }
    
    // 按照校验历史相同的方式渲染表格
    let html = '<table class="data-table"><thead><tr>';
    
    // 渲染表头（最多显示10列）
    const displayColumns = data.columns.slice(0, 10);
    for (var i = 0; i < displayColumns.length; i++) {
        html += '<th>' + displayColumns[i] + '</th>';
    }
    // 如果超过10列，显示提示
    if (data.columns.length > 10) {
        html += '<th>...（共' + data.columns.length + '列）</th>';
    }
    html += '</tr></thead><tbody>';
    
    // 渲染数据行（最多显示10行，已在后端处理）
    var displayRows = data.rows;
    for (var j = 0; j < displayRows.length; j++) {
        var row = displayRows[j];
        html += '<tr>';
        // 每行也最多显示10列
        for (var k = 0; k < Math.min(row.length, 10); k++) {
            var cell = row[k];
            var cellValue = (cell === null || cell === undefined) ? '' : String(cell);
            html += '<td>' + cellValue + '</td>';
        }
        if (row.length > 10) {
            html += '<td>...</td>';
        }
        html += '</tr>';
    }
    
    html += '</tbody></table>';
    
    // 显示统计信息
    html += '<div class="mt-2 text-muted small">';
    html += '显示前 ' + displayRows.length + ' 行数据（共 ' + data.total_rows + ' 行），';
    html += '显示前 10 列（共 ' + data.total_columns + ' 列）';
    html += '</div>';
    
    console.log('生成的HTML:', html);
    container.innerHTML = html;
    console.log('=== 数据预览渲染完成 ===');
    
    // 渲染健康检查
    checkRenderHealth(container);
}

/**
 * 检测渲染是否正常 - 表格渲染健康检查
 */
function checkRenderHealth(container) {
    setTimeout(() => {
        const table = container.querySelector('table');
        if (!table) return;
        
        const rect = table.getBoundingClientRect();
        const computedStyle = window.getComputedStyle(table);
        
        // 检测指标1：元素是否有可见尺寸
        const hasVisibleSize = rect.width > 10 && rect.height > 10;
        
        // 检测指标2：display属性是否正常
        const displayOk = computedStyle.display !== 'none' && computedStyle.visibility !== 'hidden';
        
        // 检测指标3：透明度是否正常
        const opacityOk = parseFloat(computedStyle.opacity) > 0.1;
        
        // 检测指标4：不在视口外（避免绝对定位偏移）
        const isInViewport = rect.right > 0 && rect.bottom > 0;
        
        if (!hasVisibleSize || !displayOk || !opacityOk || !isInViewport) {
            console.warn('⚠️ 表格渲染异常，启用降级显示模式');
            
            // 降级方案：显示警告
            const warning = document.createElement('div');
            warning.className = 'alert alert-warning mt-2';
            warning.innerHTML = `
                <strong>⚠️ 显示提示：</strong>
                检测到渲染异常，表格可能无法正常显示。
                <button class="btn btn-sm btn-primary ml-2" onclick="location.reload()">
                    刷新页面
                </button>
            `;
            container.insertBefore(warning, table);
        }
    }, 100);
}

/**
 * 强制显示全部表格（带性能保护）
 */
function forceShowFullTable(btn) {
    if (!confirm('列数较多，可能导致浏览器卡顿。确定要显示全部吗？')) return;
    
    btn.disabled = true;
    btn.textContent = '渲染中...';
    
    setTimeout(() => {
        const table = btn.closest('.preview-container').querySelector('table');
        if (table) {
            table.style.tableLayout = 'auto';
        }
        btn.closest('.alert').remove();
    }, 100);
}

function getAssetIdFromUrl() {
    const pathParts = window.location.pathname.split('/');
    return pathParts[pathParts.length - 1];
}
