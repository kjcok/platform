// DataQ 数质宝 - 校验历史页面

document.addEventListener('DOMContentLoaded', function() {
    loadValidations();
});

async function loadValidations() {
    try {
        const response = await apiRequest(`${API_BASE_URL}/validations/history`);
        // 兼容两种数据格式：{data: {histories: [...]}} 或 {data: [...]}
        const histories = Array.isArray(response.data) ? response.data : (response.data.histories || []);
        
        const tbody = document.getElementById('validations-table-body');
        
        if (histories.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="loading">暂无数据</td></tr>';
            return;
        }
        
        tbody.innerHTML = histories.map(history => `
            <tr>
                <td class="col-id">#${history.id}</td>
                <td class="col-name">
                    <span class="cell-truncate" title="${history.asset_name || '-'}">${history.asset_name || '-'}</span>
                </td>
                <td class="col-type">${history.total_rules || 0}</td>
                <td class="col-type">${(history.success_rate || 0).toFixed(1)}%</td>
                <td class="col-status">${getStatusBadge(history.status)}</td>
                <td class="col-date">${formatDate(history.created_at)}</td>
                <td class="col-actions">
                    <button class="btn btn-primary btn-sm" onclick="viewValidationDetail(${history.id})">详情</button>
                    <button class="btn btn-secondary btn-sm" onclick="exportJson(${history.id})" title="导出JSON结果">导出</button>
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
