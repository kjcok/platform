// DataQ 数质宝 - 通用 JavaScript 函数

// API 基础 URL
const API_BASE_URL = '/api/v1';

// 通用 AJAX 请求函数
async function apiRequest(url, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (data && (method === 'POST' || method === 'PUT')) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, options);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.message || '请求失败');
        }
        
        return result;
    } catch (error) {
        console.error('API 请求错误:', error);
        showError(error.message);
        throw error;
    }
}

// 显示成功消息
function showSuccess(message) {
    alert('✅ ' + message);
}

// 显示错误消息
function showError(message) {
    alert('❌ ' + message);
}

// 格式化日期
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
}

// 获取状态标签 HTML
function getStatusBadge(status) {
    const statusMap = {
        'pending': '<span class="badge badge-warning">待处理</span>',
        'processing': '<span class="badge badge-info">处理中</span>',
        'resolved': '<span class="badge badge-success">已解决</span>',
        'closed': '<span class="badge badge-secondary">已关闭</span>',
        'active': '<span class="badge badge-success">已启用</span>',
        'inactive': '<span class="badge badge-danger">已禁用</span>'
    };
    return statusMap[status] || `<span class="badge">${status}</span>`;
}

// 获取优先级标签 HTML
function getPriorityBadge(priority) {
    const priorityMap = {
        'high': '<span class="badge badge-danger">高</span>',
        'medium': '<span class="badge badge-warning">中</span>',
        'low': '<span class="badge badge-info">低</span>'
    };
    return priorityMap[priority] || `<span class="badge">${priority}</span>`;
}

// 确认对话框
function confirmAction(message) {
    return confirm(message);
}

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('DataQ 页面已加载');
});
