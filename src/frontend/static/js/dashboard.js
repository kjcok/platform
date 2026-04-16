// DataQ 数质宝 - 质量大盘页面

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
});

// 加载大盘数据
async function loadDashboardData() {
    try {
        // 获取统计概览
        const statsResponse = await apiRequest(`${API_BASE_URL}/statistics/overview`);
        updateStatsCards(statsResponse.data);
        
        // 加载最近问题
        await loadRecentIssues();
        
        // 绘制图表
        drawCharts(statsResponse.data);
        
    } catch (error) {
        console.error('加载大盘数据失败:', error);
    }
}

// 更新统计卡片
function updateStatsCards(data) {
    document.getElementById('total-assets').textContent = data.assets.total;
    document.getElementById('total-rules').textContent = data.rules.total;
    document.getElementById('pending-issues').textContent = data.issues.pending;
    
    // 计算成功率
    const totalValidations = data.validations.total;
    const successfulValidations = data.validations.successful;
    const successRate = totalValidations > 0 
        ? ((successfulValidations / totalValidations) * 100).toFixed(1)
        : 0;
    document.getElementById('success-rate').textContent = successRate + '%';
}

// 加载最近问题
async function loadRecentIssues() {
    try {
        const response = await apiRequest(`${API_BASE_URL}/issues?per_page=10`);
        const issues = response.data.issues;
        
        const tbody = document.getElementById('recent-issues-table');
        
        if (issues.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="loading">暂无问题</td></tr>';
            return;
        }
        
        tbody.innerHTML = issues.map(issue => `
            <tr>
                <td>#${issue.id}</td>
                <td>${issue.asset_name || '-'}</td>
                <td>${issue.rule_name || '-'}</td>
                <td>${getPriorityBadge(issue.priority)}</td>
                <td>${getStatusBadge(issue.status)}</td>
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

// 绘制图表
function drawCharts(data) {
    drawValidationTrendChart();
    drawIssueDistributionChart(data.issues);
}

// 绘制校验趋势图
async function drawValidationTrendChart() {
    try {
        // TODO: 从 API 获取趋势数据
        // 这里使用模拟数据
        const labels = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
        const successData = [85, 90, 88, 92, 95, 87, 93];
        const failedData = [15, 10, 12, 8, 5, 13, 7];
        
        const ctx = document.getElementById('validation-trend-chart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '成功',
                    data: successData,
                    borderColor: '#48bb78',
                    backgroundColor: 'rgba(72, 187, 120, 0.1)',
                    tension: 0.4
                }, {
                    label: '失败',
                    data: failedData,
                    borderColor: '#fc8181',
                    backgroundColor: 'rgba(252, 129, 129, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
        
    } catch (error) {
        console.error('绘制趋势图失败:', error);
    }
}

// 绘制问题分布图
function drawIssueDistributionChart(issuesData) {
    const ctx = document.getElementById('issue-distribution-chart').getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['待处理', '处理中', '已解决'],
            datasets: [{
                data: [
                    issuesData.pending,
                    issuesData.processing,
                    issuesData.resolved
                ],
                backgroundColor: [
                    '#ed8936',
                    '#4299e1',
                    '#48bb78'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// 查看问题详情
function viewIssue(issueId) {
    window.location.href = `/issues/${issueId}`;
}
