// DataQ 数质宝 - 问题管理页面

let currentIssues = [];
let selectedIssueIds = [];
let currentIssueId = null;
let currentStatus = null;

document.addEventListener('DOMContentLoaded', function() {
    loadIssues();
    loadStats();
    
    // 检查URL参数，如果有issue_id则自动打开详情
    const urlParams = new URLSearchParams(window.location.search);
    const issueId = urlParams.get('issue_id');
    if (issueId) {
        // 等待数据加载完成后打开详情
        setTimeout(() => {
            viewIssue(parseInt(issueId));
        }, 500);
    }
});

/**
 * 加载问题列表
 */
async function loadIssues() {
    try {
        const statusFilter = document.getElementById('status-filter').value;
        const priorityFilter = document.getElementById('priority-filter').value;
        const searchText = document.getElementById('search-input').value;
        
        let url = `${API_BASE_URL}/issues?`;
        if (statusFilter) url += `status=${statusFilter}&`;
        if (priorityFilter) url += `priority=${priorityFilter}&`;
        if (searchText) url += `search=${encodeURIComponent(searchText)}&`;
        
        const response = await apiRequest(url);
        // API返回格式：{ status: 'success', data: [issues数组], pagination: {...} }
        currentIssues = Array.isArray(response.data) ? response.data : (response.data.issues || []);
        
        renderIssuesTable();
        updateBatchButtons();
        
    } catch (error) {
        console.error('加载问题列表失败:', error);
        showError('加载问题列表失败: ' + error.message);
    }
}

/**
 * 渲染问题表格
 */
function renderIssuesTable() {
    const tbody = document.getElementById('issues-table-body');
    
    if (currentIssues.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="loading">暂无数据</td></tr>';
        return;
    }
    
    tbody.innerHTML = currentIssues.map(issue => `
        <tr>
            <td class="checkbox-col">
                <input type="checkbox" class="issue-checkbox" 
                       value="${issue.id}" 
                       onchange="updateSelection()">
            </td>
            <td>#${issue.id}</td>
            <td>${issue.asset_name || '-'}</td>
            <td>${issue.rule_name || '-'}</td>
            <td>${getPriorityBadge(issue.priority)}</td>
            <td>${getStatusBadge(issue.status)}</td>
            <td>${issue.assignee || '-'}</td>
            <td>${formatDate(issue.created_at)}</td>
            <td>
                <button class="btn btn-primary" onclick="viewIssue(${issue.id})">查看</button>
            </td>
        </tr>
    `).join('');
}

/**
 * 加载统计数据
 */
async function loadStats() {
    try {
        const response = await apiRequest(`${API_BASE_URL}/statistics/overview`);
        const stats = response.data.issues;
        
        document.getElementById('pending-count').textContent = stats.pending || 0;
        document.getElementById('processing-count').textContent = stats.processing || 0;
        document.getElementById('resolved-count').textContent = stats.resolved || 0;
        document.getElementById('total-count').textContent = stats.total || 0;
        
    } catch (error) {
        console.error('加载统计数据失败:', error);
    }
}

/**
 * 按状态筛选
 */
function filterByStatus(status) {
    document.getElementById('status-filter').value = status;
    loadIssues();
}

/**
 * 防抖加载
 */
let debounceTimer;
function debounceLoadIssues() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(loadIssues, 300);
}

/**
 * 全选/取消全选
 */
function toggleSelectAll() {
    const selectAll = document.getElementById('select-all');
    const checkboxes = document.querySelectorAll('.issue-checkbox');
    
    checkboxes.forEach(cb => {
        cb.checked = selectAll.checked;
    });
    
    updateSelection();
}

/**
 * 更新选中状态
 */
function updateSelection() {
    const checkboxes = document.querySelectorAll('.issue-checkbox:checked');
    selectedIssueIds = Array.from(checkboxes).map(cb => parseInt(cb.value));
    
    updateBatchButtons();
}

/**
 * 更新批量操作按钮状态
 */
function updateBatchButtons() {
    const hasSelection = selectedIssueIds.length > 0;
    document.getElementById('batch-ignore-btn').disabled = !hasSelection;
    document.getElementById('batch-recheck-btn').disabled = !hasSelection;
}

/**
 * 查看问题详情
 */
async function viewIssue(issueId) {
    try {
        currentIssueId = issueId;
        
        // 调用 API获取问题详情
        const response = await apiRequest(`${API_BASE_URL}/issues/${issueId}`);
        const issue = response.data;
        
        // 渲染详情内容
        renderIssueDetail(issue);
        
        // 显示模态框
        document.getElementById('issue-modal').classList.add('show');
        
    } catch (error) {
        console.error('加载问题详情失败:', error);
        showError('加载问题详情失败: ' + error.message);
    }
}

/**
 * 渲染问题详情
 */
function renderIssueDetail(issue) {
    const modalBody = document.getElementById('modal-body');
    
    modalBody.innerHTML = `
        <div class="detail-section">
            <h4>基本信息</h4>
            <div class="detail-grid">
                <div class="detail-item">
                    <span class="detail-label">问题ID</span>
                    <span class="detail-value">#${issue.id}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">资产名称</span>
                    <span class="detail-value">${issue.asset_name || '-'}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">规则名称</span>
                    <span class="detail-value">${issue.rule_name || '-'}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">规则强度</span>
                    <span class="detail-value">${issue.strength ? getStrengthBadge(issue.strength) : '-'}</span>
                </div>
            </div>
        </div>
        
        <div class="detail-section">
            <h4>问题描述</h4>
            <p style="color: #666; line-height: 1.6;">${issue.description || '无描述'}</p>
        </div>
        
        <div class="detail-section">
            <h4>当前状态</h4>
            <div style="margin-bottom: 1rem;">${getStatusBadge(issue.status)}</div>
            
            <h4 style="margin-top: 1.5rem;">更改状态</h4>
            <div class="status-selector">
                <button class="status-btn ${issue.status === 'pending' ? 'active' : ''}" 
                        onclick="selectStatus('pending')">
                    待处理
                </button>
                <button class="status-btn ${issue.status === 'processing' ? 'active' : ''}" 
                        onclick="selectStatus('processing')">
                    处理中
                </button>
                <button class="status-btn ${issue.status === 'resolved' ? 'active' : ''}" 
                        onclick="selectStatus('resolved')">
                    已解决
                </button>
                <button class="status-btn ${issue.status === 'closed' ? 'active' : ''}" 
                        onclick="selectStatus('closed')">
                    已关闭
                </button>
            </div>
        </div>
        
        <div class="detail-section">
            <h4>其他信息</h4>
            <div class="detail-grid">
                <div class="detail-item">
                    <span class="detail-label">优先级</span>
                    <span class="detail-value">${getPriorityBadge(issue.priority)}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">负责人</span>
                    <span class="detail-value">${issue.assignee || '未分配'}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">创建时间</span>
                    <span class="detail-value">${formatDate(issue.created_at)}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">更新时间</span>
                    <span class="detail-value">${formatDate(issue.updated_at)}</span>
                </div>
            </div>
        </div>
    `;
}

/**
 * 选择状态
 */
function selectStatus(status) {
    currentStatus = status;
    
    // 更新按钮样式
    document.querySelectorAll('.status-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
}

/**
 * 更新问题状态
 */
async function updateIssueStatus() {
    if (!currentStatus) {
        showWarning('请先选择要更新的状态');
        return;
    }
    
    try {
        await apiRequest(`${API_BASE_URL}/issues/${currentIssueId}/status`, 'PUT', {
            status: currentStatus
        });
        
        showSuccess('状态更新成功');
        closeModal();
        loadIssues();
        loadStats();
        
    } catch (error) {
        console.error('更新状态失败:', error);
        showError('更新状态失败: ' + error.message);
    }
}

/**
 * 重新校验问题
 */
async function recheckIssue() {
    if (!confirm('确定要重新校验这个问题吗？')) {
        return;
    }
    
    try {
        await apiRequest(`${API_BASE_URL}/issues/${currentIssueId}/recheck`, 'POST');
        
        showSuccess('重新校验已启动');
        closeModal();
        loadIssues();
        
    } catch (error) {
        console.error('重新校验失败:', error);
        showError('重新校验失败: ' + error.message);
    }
}

/**
 * 关闭模态框
 */
function closeModal() {
    document.getElementById('issue-modal').classList.remove('show');
    currentIssueId = null;
    currentStatus = null;
}

/**
 * 批量忽略
 */
async function batchIgnore() {
    if (selectedIssueIds.length === 0) {
        showWarning('请先选择要忽略的问题');
        return;
    }
    
    if (!confirm(`确定要忽略选中的 ${selectedIssueIds.length} 个问题吗？`)) {
        return;
    }
    
    try {
        // TODO: 实现批量忽略API
        // await apiRequest(`${API_BASE_URL}/issues/batch-ignore`, 'POST', {
        //     issue_ids: selectedIssueIds
        // });
        
        showSuccess(`已忽略 ${selectedIssueIds.length} 个问题（功能开发中）`);
        
        // 清除选择
        document.querySelectorAll('.issue-checkbox').forEach(cb => cb.checked = false);
        document.getElementById('select-all').checked = false;
        selectedIssueIds = [];
        updateBatchButtons();
        loadIssues();
        
    } catch (error) {
        console.error('批量忽略失败:', error);
        showError('批量忽略失败: ' + error.message);
    }
}

/**
 * 批量重新校验
 */
async function batchRecheck() {
    if (selectedIssueIds.length === 0) {
        showWarning('请先选择要重新校验的问题');
        return;
    }
    
    if (!confirm(`确定要重新校验选中的 ${selectedIssueIds.length} 个问题吗？`)) {
        return;
    }
    
    try {
        // TODO: 实现批量重新校验API
        // await apiRequest(`${API_BASE_URL}/issues/batch-recheck`, 'POST', {
        //     issue_ids: selectedIssueIds
        // });
        
        showSuccess(`已启动 ${selectedIssueIds.length} 个问题的重新校验（功能开发中）`);
        
        // 清除选择
        document.querySelectorAll('.issue-checkbox').forEach(cb => cb.checked = false);
        document.getElementById('select-all').checked = false;
        selectedIssueIds = [];
        updateBatchButtons();
        loadIssues();
        
    } catch (error) {
        console.error('批量重新校验失败:', error);
        showError('批量重新校验失败: ' + error.message);
    }
}

// 点击模态框外部关闭
document.addEventListener('click', function(event) {
    const modal = document.getElementById('issue-modal');
    if (event.target === modal) {
        closeModal();
    }
});

/**
 * 打开新建问题模态框
 */
async function openCreateIssueModal() {
    try {
        // 加载资产列表
        const response = await apiRequest(`${API_BASE_URL}/assets?page=1&per_page=100`);
        const assets = Array.isArray(response.data) ? response.data : (response.data.assets || []);
        
        // 填充资产下拉框
        const assetSelect = document.getElementById('create-issue-asset');
        assetSelect.innerHTML = '<option value="">-- 请选择资产 --</option>';
        assets.forEach(asset => {
            assetSelect.innerHTML += `<option value="${asset.id}">${asset.name}</option>`;
        });
        
        // 清空规则下拉框
        const ruleSelect = document.getElementById('create-issue-rule');
        ruleSelect.innerHTML = '<option value="">-- 请选择规则（可选） --</option>';
        
        // 清空表单
        document.getElementById('create-issue-title').value = '';
        document.getElementById('create-issue-description').value = '';
        document.getElementById('create-issue-priority').value = 'medium';
        document.getElementById('create-issue-assignee').value = '';
        document.getElementById('create-issue-contact').value = '';
        
        // 显示模态框
        document.getElementById('create-issue-modal').classList.add('show');
        
    } catch (error) {
        console.error('加载资产列表失败:', error);
        showError('加载资产列表失败: ' + error.message);
    }
}

/**
 * 资产选择变化，加载该资产的规则列表
 */
async function onAssetChange() {
    const assetId = document.getElementById('create-issue-asset').value;
    const ruleSelect = document.getElementById('create-issue-rule');
    
    // 清空规则下拉框
    ruleSelect.innerHTML = '<option value="">-- 请选择规则（可选） --</option>';
    
    if (!assetId) {
        return;
    }
    
    try {
        const response = await apiRequest(`${API_BASE_URL}/assets/${assetId}/rules`);
        const rules = Array.isArray(response.data) ? response.data : (response.data.rules || []);
        
        rules.filter(r => r.is_active).forEach(rule => {
            ruleSelect.innerHTML += `<option value="${rule.id}">${rule.name}</option>`;
        });
        
    } catch (error) {
        console.error('加载规则列表失败:', error);
        showError('加载规则列表失败: ' + error.message);
    }
}

/**
 * 关闭新建问题模态框
 */
function closeCreateIssueModal() {
    document.getElementById('create-issue-modal').classList.remove('show');
}

/**
 * 创建问题
 */
async function createIssue() {
    const assetId = parseInt(document.getElementById('create-issue-asset').value);
    const ruleId = document.getElementById('create-issue-rule').value;
    const title = document.getElementById('create-issue-title').value.trim();
    const description = document.getElementById('create-issue-description').value.trim();
    const priority = document.getElementById('create-issue-priority').value;
    const assignee = document.getElementById('create-issue-assignee').value.trim();
    const contactInfo = document.getElementById('create-issue-contact').value.trim();
    
    if (!assetId || !title) {
        showWarning('请填写必填项：关联资产和问题标题');
        return;
    }
    
    try {
        const data = {
            asset_id: assetId,
            rule_id: ruleId ? parseInt(ruleId) : null,
            title: title,
            description: description,
            priority: priority,
            assignee: assignee || null,
            contact_info: contactInfo || null
        };
        
        await apiRequest(`${API_BASE_URL}/issues`, 'POST', data);
        
        showSuccess('问题工单创建成功');
        closeCreateIssueModal();
        loadIssues();
        loadStats();
        
    } catch (error) {
        console.error('创建问题失败:', error);
        showError('创建问题失败: ' + error.message);
    }
}
