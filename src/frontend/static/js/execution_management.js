// DataQ 数质宝 - 运行管理页面

let assets = [];
let selectedAssetIds = new Set();
let currentExecutionResult = null;

document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ DOM 加载完成');
    console.log('API_BASE_URL:', typeof API_BASE_URL !== 'undefined' ? API_BASE_URL : '❌ 未定义');
    console.log('apiRequest:', typeof apiRequest !== 'undefined' ? '✅ 已定义' : '❌ 未定义');
    console.log('getStatusBadge:', typeof getStatusBadge !== 'undefined' ? '✅ 已定义' : '❌ 未定义');
    console.log('formatDate:', typeof formatDate !== 'undefined' ? '✅ 已定义' : '❌ 未定义');
    
    try {
        loadAssets();
        loadRecentExecutions();
        console.log('✅ 数据加载函数已调用');
    } catch (error) {
        console.error('❌ 调用加载函数时出错:', error);
    }
});

/**
 * 加载资产列表
 */
async function loadAssets() {
    try {
        const response = await apiRequest(`${API_BASE_URL}/assets?page=1&per_page=100`);
        assets = Array.isArray(response.data) ? response.data : (response.data.assets || []);
        
        // 先渲染基础数据（快速显示，避免页面空白）
        renderAssetList(assets);
        
        // 异步并行加载附加信息（不阻塞页面显示）
        Promise.all(assets.map(asset => Promise.all([
            loadAssetScheduleStatus(asset),
            loadAssetLastExecution(asset)
        ]))).then(() => {
            renderAssetList(assets);
        }).catch(error => {
            console.warn('加载附加信息失败:', error);
        });
    } catch (error) {
        console.error('加载资产列表失败:', error);
        showError('加载资产列表失败: ' + error.message);
    }
}

/**
 * 加载资产的调度状态
 */
async function loadAssetScheduleStatus(asset) {
    try {
        const response = await apiRequest(`${API_BASE_URL}/assets/${asset.id}/schedule/status`);
        asset.schedule_status = response.data ? 'scheduled' : 'not_scheduled';
        asset.schedule_info = response.data;
    } catch (error) {
        asset.schedule_status = 'not_scheduled';
        asset.schedule_info = null;
    }
}

/**
 * 加载资产的最后执行记录
 */
async function loadAssetLastExecution(asset) {
    try {
        const response = await apiRequest(`${API_BASE_URL}/validations/history?asset_id=${asset.id}&page=1&per_page=1`);
        const histories = Array.isArray(response.data) ? response.data : (response.data.histories || []);
        
        if (histories.length > 0) {
            asset.last_execution = histories[0];
        } else {
            asset.last_execution = null;
        }
    } catch (error) {
        asset.last_execution = null;
    }
}

/**
 * 渲染资产列表
 */
function renderAssetList(assetsToRender) {
    const tbody = document.getElementById('asset-list-body');
    
    if (assetsToRender.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="loading">暂无数据</td></tr>';
        return;
    }
    
    tbody.innerHTML = assetsToRender.map(asset => `
        <tr>
            <td>
                <input type="checkbox" 
                       value="${asset.id}" 
                       onchange="toggleAssetSelection(${asset.id})"
                       ${selectedAssetIds.has(asset.id) ? 'checked' : ''}>
            </td>
            <td>#${asset.id}</td>
            <td>${asset.name}</td>
            <td>${asset.data_source}</td>
            <td>${asset.rule_count || 0} 条规则</td>
            <td>
                <span class="schedule-badge ${asset.schedule_status}">
                    ${asset.schedule_status === 'scheduled' ? '⏰ 已调度' : '❌ 未调度'}
                </span>
            </td>
            <td>
                ${asset.last_execution ? formatDate(asset.last_execution.start_time) : '-'}
            </td>
            <td>
                ${asset.last_execution ? getStatusBadge(asset.last_execution.status) : '-'}
            </td>
            <td>
                <button class="btn btn-success" onclick="runAsset(${asset.id})" title="立即运行">
                    ▶️ 运行
                </button>
                <button class="btn btn-secondary" onclick="configureSchedule(${asset.id})" title="配置调度">
                    ⏰ 调度
                </button>
                <button class="btn btn-primary" onclick="viewAssetDetail(${asset.id})" title="查看详情">
                    📊 详情
                </button>
            </td>
        </tr>
    `).join('');
}

/**
 * 切换全选
 */
function toggleSelectAll() {
    const selectAllCheckbox = document.getElementById('select-all');
    const checkboxes = document.querySelectorAll('#asset-list-body input[type="checkbox"]');
    
    if (selectAllCheckbox.checked) {
        assets.forEach(asset => selectedAssetIds.add(asset.id));
    } else {
        selectedAssetIds.clear();
    }
    
    checkboxes.forEach(cb => cb.checked = selectAllCheckbox.checked);
    renderAssetList(getFilteredAssets());
}

/**
 * 切换单个资产选择
 */
function toggleAssetSelection(assetId) {
    if (selectedAssetIds.has(assetId)) {
        selectedAssetIds.delete(assetId);
    } else {
        selectedAssetIds.add(assetId);
    }
    
    // 更新全选框状态
    const selectAllCheckbox = document.getElementById('select-all');
    selectAllCheckbox.checked = selectedAssetIds.size === assets.length && assets.length > 0;
}

/**
 * 批量运行选中的资产
 */
async function batchRunSelected() {
    if (selectedAssetIds.size === 0) {
        showWarning('请先选择要运行的资产');
        return;
    }
    
    showInfo(`正在运行 ${selectedAssetIds.size} 个资产...`);
    
    const results = [];
    for (const assetId of selectedAssetIds) {
        try {
            const result = await runSingleAsset(assetId);
            results.push({ assetId, success: true, result });
        } catch (error) {
            results.push({ assetId, success: false, error: error.message });
        }
    }
    
    // 显示批量运行结果
    showBatchRunResults(results);
    
    // 刷新列表
    await loadAssets();
    await loadRecentExecutions();
}

/**
 * 运行所有激活的资产
 */
async function runAllActiveAssets() {
    const activeAssets = assets.filter(a => a.is_active && a.rule_count > 0);
    
    if (activeAssets.length === 0) {
        showWarning('没有可运行的资产（需要激活且有规则）');
        return;
    }
    
    showInfo(`正在运行所有 ${activeAssets.length} 个激活资产...`);
    
    selectedAssetIds = new Set(activeAssets.map(a => a.id));
    await batchRunSelected();
}

/**
 * 运行单个资产
 */
async function runSingleAsset(assetId) {
    const response = await fetch(`${API_BASE_URL}/validations`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            asset_id: assetId,
            auto_archive: true,
            auto_create_issue: false
        })
    });

    const result = await response.json();

    if (!response.ok) {
        throw new Error(result.message || '请求失败');
    }

    return result;
}

/**
 * 运行单个资产
 */
async function runAsset(assetId) {
    const asset = assets.find(a => a.id === assetId);
    if (!asset) return;
    
    showInfo(`正在运行资产 "${asset.name}"...`);
    
    try {
        const result = await runSingleAsset(assetId);
        const execStatus = result.data?.status || 'success';
        
        if (execStatus === 'success' || execStatus === 'partial') {
            showSuccess(`资产 "${asset.name}" 运行完成 - ${result.data?.passed_rules || 0} 条规则通过, ${result.data?.failed_rules || 0} 条失败`);
        } else if (execStatus === 'failed') {
            showWarning(`资产 "${asset.name}" 运行完成, 但存在失败规则 - ${result.data?.passed_rules || 0} 条规则通过, ${result.data?.failed_rules || 0} 条失败`);
        } else {
            showSuccess(`资产 "${asset.name}" 运行完成`);
        }
        
        // 显示执行结果
        showExecutionResult(result.data);
        
        // 刷新列表
        await loadAssets();
        await loadRecentExecutions();
    } catch (error) {
        showError('运行失败: ' + error.message);
    }
}

/**
 * 配置调度
 */
function configureSchedule(assetId) {
    const asset = assets.find(a => a.id === assetId);
    if (!asset) return;
    
    // 使用模态框替代prompt
    showScheduleModal(assetId, asset.name);
}

/**
 * 显示调度配置模态框
 */
function showScheduleModal(assetId, assetName) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'block';
    modal.id = 'schedule-modal';
    
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 500px;">
            <div class="modal-header">
                <h3>⏰ 配置调度 - ${assetName}</h3>
                <span class="close" onclick="closeScheduleModal()">&times;</span>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label class="form-label">调度类型</label>
                    <select id="schedule-type" class="form-control" onchange="onScheduleTypeChange()">
                        <option value="interval">间隔调度</option>
                        <option value="cron">Cron表达式调度</option>
                    </select>
                </div>
                
                <div id="interval-config" class="form-group">
                    <label class="form-label">间隔小时数</label>
                    <input type="number" id="interval-hours" class="form-control" value="24" min="1" max="168">
                    <small class="form-hint">每多少小时执行一次校验</small>
                </div>
                
                <div id="cron-config" class="form-group" style="display: none;">
                    <label class="form-label">Cron表达式</label>
                    <input type="text" id="cron-expression" class="form-control" value="0 9 * * *" placeholder="分 时 日 月 周">
                    <small class="form-hint">格式: 分 时 日 月 周，例如 "0 9 * * *" 表示每天9点</small>
                </div>
                
                <div class="form-group">
                    <label class="form-label">
                        <input type="checkbox" id="auto-archive" checked> 自动归档异常数据
                    </label>
                </div>
                
                <div class="form-group">
                    <label class="form-label">
                        <input type="checkbox" id="auto-create-issue" checked> 失败时自动创建问题工单
                    </label>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeScheduleModal()">取消</button>
                <button class="btn btn-primary" onclick="saveSchedule(${assetId})">保存配置</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

/**
 * 调度类型变化
 */
function onScheduleTypeChange() {
    const scheduleType = document.getElementById('schedule-type').value;
    const intervalConfig = document.getElementById('interval-config');
    const cronConfig = document.getElementById('cron-config');
    
    if (scheduleType === 'interval') {
        intervalConfig.style.display = 'block';
        cronConfig.style.display = 'none';
    } else {
        intervalConfig.style.display = 'none';
        cronConfig.style.display = 'block';
    }
}

/**
 * 保存调度配置
 */
async function saveSchedule(assetId) {
    const scheduleType = document.getElementById('schedule-type').value;
    const autoArchive = document.getElementById('auto-archive').checked;
    const autoCreateIssue = document.getElementById('auto-create-issue').checked;
    
    let scheduleData = {
        schedule_type: scheduleType,
        auto_archive: autoArchive,
        auto_create_issue: autoCreateIssue
    };
    
    if (scheduleType === 'interval') {
        const hours = parseInt(document.getElementById('interval-hours').value);
        if (!hours || hours < 1) {
            showWarning('请输入有效的间隔小时数');
            return;
        }
        scheduleData.interval_hours = hours;
    } else if (scheduleType === 'cron') {
        const cronExpr = document.getElementById('cron-expression').value.trim();
        if (!cronExpr) {
            showWarning('请输入Cron表达式');
            return;
        }
        scheduleData.cron_expression = cronExpr;
    }
    
    closeScheduleModal();
    await setupSchedule(assetId, scheduleData);
}

/**
 * 关闭调度模态框
 */
function closeScheduleModal() {
    const modal = document.getElementById('schedule-modal');
    if (modal) {
        modal.remove();
    }
}

/**
 * 设置调度
 */
async function setupSchedule(assetId, scheduleData) {
    try {
        const response = await apiRequest(`${API_BASE_URL}/assets/${assetId}/schedule`, {
            method: 'POST',
            body: JSON.stringify(scheduleData)
        });
        
        showSuccess('调度配置成功');
        await loadAssets();
    } catch (error) {
        showError('调度配置失败: ' + error.message);
    }
}

/**
 * 查看资产详情
 */
function viewAssetDetail(assetId) {
    window.location.href = `/assets/${assetId}`;
}

/**
 * 加载最近执行记录
 */
async function loadRecentExecutions() {
    try {
        const response = await apiRequest(`${API_BASE_URL}/validations/history?page=1&per_page=20`);
        const executions = Array.isArray(response.data) ? response.data : (response.data.histories || []);
        
        renderExecutionHistory(executions);
    } catch (error) {
        console.error('加载执行记录失败:', error);
    }
}

/**
 * 渲染执行历史
 */
function renderExecutionHistory(executions) {
    const tbody = document.getElementById('execution-history-body');
    
    if (executions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="loading">暂无执行记录</td></tr>';
        return;
    }
    
    tbody.innerHTML = executions.map(exec => `
        <tr>
            <td>#${exec.id}</td>
            <td>${exec.asset_name || '-'}</td>
            <td>${exec.trigger_type || '手动'}</td>
            <td>${exec.total_rules || 0}</td>
            <td>
                <span style="color: #28a745;">${exec.passed_rules || 0}</span> / 
                <span style="color: #dc3545;">${exec.failed_rules || 0}</span>
            </td>
            <td>${(exec.success_rate || 0).toFixed(1)}%</td>
            <td>${formatDate(exec.start_time)}</td>
            <td>${getStatusBadge(exec.status)}</td>
            <td>
                <button class="btn btn-primary" onclick="viewExecutionDetail(${exec.id})">详情</button>
                <button class="btn btn-secondary" onclick="exportExecutionJson(${exec.id})" title="导出JSON结果">导出</button>
            </td>
        </tr>
    `).join('');
}

/**
 * 导出执行结果为JSON
 */
function exportExecutionJson(historyId) {
    window.open(`${API_BASE_URL}/validations/history/${historyId}/export/json?download=true`, '_blank');
}

/**
 * 查看执行详情
 */
async function viewExecutionDetail(historyId) {
    try {
        const response = await apiRequest(`${API_BASE_URL}/validations/history/${historyId}`);
        const execution = response.data;
        
        // 获取规则级别的详细结果
        const rulesResponse = await apiRequest(`${API_BASE_URL}/validations/history/${historyId}/rules`);
        const ruleResults = Array.isArray(rulesResponse.data) ? rulesResponse.data : (rulesResponse.data.rules || []);
        
        showExecutionResultWithRules(execution, ruleResults);
    } catch (error) {
        showError('加载执行详情失败: ' + error.message);
    }
}

/**
 * 显示执行结果（简单版）
 */
function showExecutionResult(result) {
    currentExecutionResult = result;
    
    const content = document.getElementById('execution-result-content');
    content.innerHTML = `
        <div class="result-stats">
            <div class="stat-card">
                <div class="stat-value">${result.total_rules || 0}</div>
                <div class="stat-label">规则总数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #28a745;">${result.passed_rules || 0}</div>
                <div class="stat-label">通过规则</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #dc3545;">${result.failed_rules || 0}</div>
                <div class="stat-label">失败规则</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${(result.success_rate || 0).toFixed(1)}%</div>
                <div class="stat-label">成功率</div>
            </div>
        </div>
        
        <p><strong>状态:</strong> ${getStatusBadge(result.status)}</p>
        <p><strong>开始时间:</strong> ${formatDate(result.start_time)}</p>
        <p><strong>结束时间:</strong> ${result.end_time ? formatDate(result.end_time) : '-'}</p>
        ${result.error_message ? `<p style="color: red;"><strong>错误信息:</strong> ${result.error_message}</p>` : ''}
    `;
    
    // 如果有失败规则，显示创建问题按钮
    const createIssueBtn = document.getElementById('create-issue-btn');
    if (result.failed_rules > 0) {
        createIssueBtn.style.display = 'inline-block';
    } else {
        createIssueBtn.style.display = 'none';
    }
    
    document.getElementById('execution-result-modal').style.display = 'block';
}

/**
 * 显示执行结果（带规则详情）
 */
function showExecutionResultWithRules(execution, ruleResults) {
    currentExecutionResult = execution;
    
    const content = document.getElementById('execution-result-content');
    
    let ruleResultsHtml = '';
    if (ruleResults && ruleResults.length > 0) {
        ruleResultsHtml = `
            <h4 style="margin-top: 1.5rem; margin-bottom: 1rem;">规则执行详情</h4>
            ${ruleResults.map(rule => `
                <div class="rule-result-item ${rule.status === 'success' ? 'passed' : 'failed'}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong>${rule.rule_name}</strong>
                        <span class="status-badge ${rule.status === 'success' ? 'success' : 'failed'}">
                            ${rule.status === 'success' ? '✅ 通过' : '❌ 失败'}
                        </span>
                    </div>
                    <div style="margin-top: 0.5rem; font-size: 0.875rem; color: #666;">
                        <div>字段: ${rule.column_name || '全表'}</div>
                        <div>通过率: ${(rule.pass_rate || 0).toFixed(2)}%</div>
                        ${rule.failed_records > 0 ? `<div>失败记录: ${rule.failed_records}</div>` : ''}
                    </div>
                </div>
            `).join('')}
        `;
    }
    
    content.innerHTML = `
        <div class="result-stats">
            <div class="stat-card">
                <div class="stat-value">${execution.total_rules || 0}</div>
                <div class="stat-label">规则总数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #28a745;">${execution.passed_rules || 0}</div>
                <div class="stat-label">通过规则</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #dc3545;">${execution.failed_rules || 0}</div>
                <div class="stat-label">失败规则</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${(execution.success_rate || 0).toFixed(1)}%</div>
                <div class="stat-label">成功率</div>
            </div>
        </div>
        
        <p><strong>资产:</strong> ${execution.asset_name}</p>
        <p><strong>状态:</strong> ${getStatusBadge(execution.status)}</p>
        <p><strong>触发方式:</strong> ${execution.trigger_type || '手动'}</p>
        <p><strong>开始时间:</strong> ${formatDate(execution.start_time)}</p>
        <p><strong>结束时间:</strong> ${execution.end_time ? formatDate(execution.end_time) : '-'}</p>
        ${execution.error_message ? `<p style="color: red;"><strong>错误信息:</strong> ${execution.error_message}</p>` : ''}
        
        ${ruleResultsHtml}
    `;
    
    // 如果有失败规则，显示创建问题按钮
    const createIssueBtn = document.getElementById('create-issue-btn');
    if (execution.failed_rules > 0) {
        createIssueBtn.style.display = 'inline-block';
    } else {
        createIssueBtn.style.display = 'none';
    }
    
    document.getElementById('execution-result-modal').style.display = 'block';
}

/**
 * 从执行结果创建问题工单
 */
function createIssueFromResult() {
    if (!currentExecutionResult) return;
    
    // 跳转到问题管理页面，并预填充信息
    const params = new URLSearchParams({
        validation_history_id: currentExecutionResult.id,
        asset_id: currentExecutionResult.asset_id,
        title: `${currentExecutionResult.asset_name} - 校验失败问题`,
        description: `校验执行ID: ${currentExecutionResult.id}\n失败规则数: ${currentExecutionResult.failed_rules}\n成功率: ${(currentExecutionResult.success_rate || 0).toFixed(1)}%`
    });
    
    window.location.href = `/issues?${params.toString()}`;
}

/**
 * 显示批量运行结果
 */
function showBatchRunResults(results) {
    const successCount = results.filter(r => r.success).length;
    const failCount = results.filter(r => !r.success).length;
    
    if (failCount === 0) {
        showSuccess(`批量运行完成: 成功 ${successCount} 个资产`);
    } else {
        let message = `批量运行完成: 成功 ${successCount} 个, 失败 ${failCount} 个`;
        
        const failedAssets = results.filter(r => !r.success);
        const firstFew = failedAssets.slice(0, 3);
        
        firstFew.forEach(r => {
            const asset = assets.find(a => a.id === r.assetId);
            message += `\n- ${asset ? asset.name : `#${r.assetId}`}: ${r.error}`;
        });
        
        if (failedAssets.length > 3) {
            message += `\n... 还有 ${failedAssets.length - 3} 个失败`;
        }
        
        showWarning(message);  // 批量运行有失败用 warning 而不是 error
    }
}

/**
 * 过滤资产
 */
function filterAssets() {
    const searchTerm = document.getElementById('search-asset').value.toLowerCase();
    const statusFilter = document.getElementById('filter-status').value;
    
    const filtered = assets.filter(asset => {
        // 搜索过滤
        const matchesSearch = !searchTerm || 
            asset.name.toLowerCase().includes(searchTerm) ||
            asset.data_source.toLowerCase().includes(searchTerm);
        
        // 状态过滤
        let matchesStatus = true;
        if (statusFilter === 'scheduled') {
            matchesStatus = asset.schedule_status === 'scheduled';
        } else if (statusFilter === 'not_scheduled') {
            matchesStatus = asset.schedule_status === 'not_scheduled';
        }
        
        return matchesSearch && matchesStatus;
    });
    
    renderAssetList(filtered);
}

/**
 * 关闭模态框
 */
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

/**
 * 获取状态徽章HTML
 */
function getStatusBadge(status) {
    const badges = {
        'success': '<span class="status-badge success">✅ 成功</span>',
        'partial': '<span class="status-badge" style="background: #fff3cd; color: #856404;">⚠️ 部分成功</span>',
        'failed': '<span class="status-badge failed">❌ 失败</span>',
        'failed': '<span class="status-badge failed">❌ 失败</span>',
        'running': '<span class="status-badge running">⏳ 运行中</span>',
        'pending': '<span class="status-badge running">⏸️ 等待中</span>'
    };
    
    return badges[status] || `<span class="status-badge">${status}</span>`;
}

/**
 * 格式化日期
 */
function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN');
}
