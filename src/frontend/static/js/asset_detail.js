/**
 * 资产详情页交互逻辑
 */

// 注：API_BASE_URL 已在 common.js 中声明，此处不重复声明
// const API_BASE_URL = '/api/v1';  // 注释掉，使用common.js中的

let currentAsset = null;
let currentTab = 'rules';

/**
 * 初始化
 */
document.addEventListener('DOMContentLoaded', () => {
    loadAssetDetail();
    initTabs();
    
    // 先加载规则，根据规则数量决定默认标签页
    loadRules().then(() => {
        // 如果有规则且URL没有指定标签页，默认显示规则列表
        const rulesContainer = document.getElementById('rules-list');
        if (rulesContainer && !rulesContainer.querySelector('.empty-state')) {
            // 有规则，确保显示规则列表标签页
            switchTab('rules');
        }
    });
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
 * 初始化标签页
 */
function initTabs() {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            switchTab(tabName);
        });
    });
}

/**
 * 切换标签页
 */
function switchTab(tabName) {
    currentTab = tabName;
    
    // 更新标签样式
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    
    // 更新内容显示
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.getElementById(`tab-${tabName}`).classList.add('active');
    
    // 加载对应数据
    if (tabName === 'rules') {
        loadRules();
    } else if (tabName === 'validations') {
        loadValidations();
    } else if (tabName === 'issues') {
        loadIssues();
    }
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
        html += `
            <div class="rule-card">
                <div class="rule-card-header">
                    <div class="rule-name">${rule.name}</div>
                    <span class="rule-badge ${rule.strength === 'strong' ? 'badge-strong' : 'badge-weak'}">
                        ${rule.strength === 'strong' ? '强规则' : '弱规则'}
                    </span>
                </div>
                <div class="rule-info">
                    <div class="rule-info-item">
                        <div class="rule-info-label">规则类型</div>
                        <div class="rule-info-value">${getRuleTypeLabel(rule.rule_type)}</div>
                    </div>
                    <div class="rule-info-item">
                        <div class="rule-info-label">字段</div>
                        <div class="rule-info-value">${rule.column_name || '-'}</div>
                    </div>
                    <div class="rule-info-item">
                        <div class="rule-info-label">状态</div>
                        <div class="rule-info-value">${rule.enabled ? '✅ 已启用' : '⏸️ 已禁用'}</div>
                    </div>
                </div>
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
 * 查看规则列表（从标签页跳转）
 */
function viewRules() {
    switchTab('rules');
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
