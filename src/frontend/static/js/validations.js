// DataQ 数质宝 - 校验历史页面

document.addEventListener('DOMContentLoaded', function() {
    loadValidations();
});

async function loadValidations() {
    try {
        const response = await apiRequest(`${API_BASE_URL}/validations/history`);
        const histories = response.data.histories;
        
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
                <td>${(history.success_percent || 0).toFixed(1)}%</td>
                <td>${getStatusBadge(history.status)}</td>
                <td>${formatDate(history.created_at)}</td>
                <td>
                    <button class="btn btn-primary" onclick="viewDetail(${history.id})">详情</button>
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('加载校验历史失败:', error);
    }
}

function viewDetail(historyId) {
    // TODO: 显示校验详情
    alert('查看校验详情 #' + historyId);
}
