// DataQ 数质宝 - 问题管理页面

document.addEventListener('DOMContentLoaded', function() {
    loadIssues();
});

async function loadIssues() {
    try {
        const response = await apiRequest(`${API_BASE_URL}/issues`);
        const issues = response.data.issues;
        
        const tbody = document.getElementById('issues-table-body');
        
        if (issues.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="loading">暂无数据</td></tr>';
            return;
        }
        
        tbody.innerHTML = issues.map(issue => `
            <tr>
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
        
    } catch (error) {
        console.error('加载问题列表失败:', error);
    }
}

function viewIssue(issueId) {
    window.location.href = `/issues/${issueId}`;
}
