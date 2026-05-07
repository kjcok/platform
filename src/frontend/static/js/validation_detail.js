// DataQ 数质宝 - 校验详情页面

let historyId = null;
let validationData = null;
let ruleResults = [];

document.addEventListener('DOMContentLoaded', function() {
    // 从URL获取history_id
    const pathParts = window.location.pathname.split('/');
    historyId = pathParts[pathParts.length - 1];
    
    if (historyId) {
        loadValidationDetail();
    }
    
    // 绑定筛选事件
    document.getElementById('filter-result').addEventListener('change', filterRules);
    document.getElementById('search-rule').addEventListener('input', debounce(filterRules, 300));
});

/**
 * 加载校验详情
 */
async function loadValidationDetail() {
    try {
        showLoading(true);
        
        // 获取校验历史详情
        const response = await apiRequest(`${API_BASE_URL}/validations/history/${historyId}`);
        validationData = response.data;
        
        // 渲染基本信息
        renderBasicInfo();
        
        // 渲染统计卡片
        renderStatsCards();
        
        // 加载规则校验结果
        await loadRuleResults();
        
        showLoading(false);
        
    } catch (error) {
        console.error('加载校验详情失败:', error);
        showError('加载校验详情失败: ' + error.message);
        showLoading(false);
    }
}

/**
 * 渲染基本信息
 */
function renderBasicInfo() {
    document.getElementById('history-id').textContent = `#${validationData.id}`;
    document.getElementById('asset-name').textContent = validationData.asset_name || '-';
    document.getElementById('status').innerHTML = getStatusBadge(validationData.status);
    document.getElementById('start-time').textContent = formatDate(validationData.start_time);
    document.getElementById('end-time').textContent = validationData.end_time ? formatDate(validationData.end_time) : '-';
    document.getElementById('error-message').textContent = validationData.error_message || '无';
}

/**
 * 渲染统计卡片（基于实际加载的规则结果列表计算，确保与表格一致）
 */
function renderStatsCards() {
    const total = ruleResults.length;
    const failed = ruleResults.filter(r => r.status === 'failed' || r.status === 'error').length;
    const passed = total - failed;
    const successRate = total > 0 ? (passed / total * 100) : 0;

    document.getElementById('total-rules').textContent = total;
    document.getElementById('passed-rules').textContent = passed;
    document.getElementById('failed-rules').textContent = failed;
    document.getElementById('success-rate').textContent = successRate.toFixed(1) + '%';
}

/**
 * 加载规则校验结果
 */
async function loadRuleResults() {
    try {
        // 调用 API获取规则校验结果列表
        const response = await apiRequest(`${API_BASE_URL}/validations/history/${historyId}/rules`);
        ruleResults = response.data.rules;

        // 基于实际规则列表重新计算统计卡片，确保与表格数据一致
        renderStatsCards();

        renderRuleTable(ruleResults);
        
    } catch (error) {
        console.error('加载规则结果失败:', error);
        document.getElementById('rules-table-body').innerHTML = 
            '<tr><td colspan="6" class="loading">加载失败</td></tr>';
    }
}

/**
 * 渲染规则表格
 */
function renderRuleTable(rules) {
    const tbody = document.getElementById('rules-table-body');
    
    if (rules.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="loading">暂无数据</td></tr>';
        return;
    }
    
    tbody.innerHTML = rules.map(rule => `
        <tr>
            <td>${rule.rule_name}</td>
            <td>${getRuleTypeLabel(rule.rule_type)}</td>
            <td>${getResultBadge(rule.status)}</td>
            <td>${rule.failed_records || 0}</td>
            <td>
                ${rule.status === 'failed' || rule.status === 'error' ?
                    `<button class="btn btn-primary" onclick="viewExceptions(${rule.id})">查看异常</button>` :
                    '<span style="color: #999;">-</span>'
                }
            </td>
        </tr>
    `).join('');
}

/**
 * 筛选规则
 */
function filterRules() {
    const resultFilter = document.getElementById('filter-result').value;
    const searchText = document.getElementById('search-rule').value.toLowerCase();

    let filtered = ruleResults;

    // 按结果筛选
    if (resultFilter) {
        filtered = filtered.filter(r => r.status === resultFilter);
    }

    // 按名称搜索
    if (searchText) {
        filtered = filtered.filter(r => r.rule_name.toLowerCase().includes(searchText));
    }

    renderRuleTable(filtered);
}

/**
 * 查看异常数据
 */
async function viewExceptions(ruleId) {
    try {
        // 调用 API获取异常数据
        const response = await apiRequest(
            `${API_BASE_URL}/validations/history/${historyId}/exceptions?rule_id=${ruleId}`
        );
        
        const exceptions = response.data.exceptions;
        renderExceptions(exceptions);
        
        // 启用下载按钮
        document.getElementById('download-btn').disabled = false;
        
    } catch (error) {
        console.error('加载异常数据失败:', error);
        showError('加载异常数据失败: ' + error.message);
    }
}

/**
 * 渲染异常数据
 */
function renderExceptions(exceptions) {
    const container = document.getElementById('exceptions-content');
    
    if (exceptions.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">✅</div>
                <p>该规则没有异常数据</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = `
        <table class="data-table">
            <thead>
                <tr>
                    <th>行号</th>
                    <th>字段名</th>
                    <th>实际值</th>
                    <th>期望值</th>
                </tr>
            </thead>
            <tbody>
                ${exceptions.map(exc => `
                    <tr>
                        <td>${exc.row_number}</td>
                        <td>${exc.column_name}</td>
                        <td><code>${exc.actual_value || '(空)'}</code></td>
                        <td>${exc.expected_value}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
        <p style="margin-top: 1rem; color: #666; font-size: 0.875rem;">
            共 ${exceptions.length} 条异常数据
        </p>
    `;
}

/**
 * 下载异常数据
 */
async function downloadExceptions() {
    try {
        // 调用 API下载异常数据
        window.open(`${API_BASE_URL}/validations/history/${historyId}/exceptions/download`, '_blank');
        
    } catch (error) {
        console.error('下载异常数据失败:', error);
        showError('下载失败: ' + error.message);
    }
}

/**
 * 辅助函数：获取规则类型标签
 */
function getRuleTypeLabel(type) {
    const typeMap = {
        'completeness': '完整性',
        'uniqueness': '唯一性',
        'timeliness': '及时性',
        'validity': '有效性',
        'consistency': '一致性',
        'stability': '稳定性'
    };
    return typeMap[type] || type;
}

/**
 * 辅助函数：获取结果徽章
 */
function getResultBadge(result) {
    if (result === 'passed') {
        return '<span class="badge badge-success">通过</span>';
    } else {
        return '<span class="badge badge-danger">失败</span>';
    }
}

/**
 * 显示/隐藏加载状态
 */
function showLoading(show) {
    // 可以添加全局加载指示器
}

/**
 * 防抖函数
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
