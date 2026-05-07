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

// 消息历史存储
window.toastHistory = [];
let toastTimer = null;

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    initToastSystem();
    console.log('DataQ 页面已加载');
});

function initToastSystem() {
    // 创建历史消息按钮
    const historyBtn = document.createElement('button');
    historyBtn.className = 'toast-history-btn';
    historyBtn.innerHTML = `
        <span>🔔</span>
        <span class="badge" id="toast-badge" style="display: none;">0</span>
    `;
    historyBtn.onclick = toggleToastHistory;
    document.body.appendChild(historyBtn);
    
    // 创建历史面板
    const historyPanel = document.createElement('div');
    historyPanel.className = 'toast-history-panel';
    historyPanel.id = 'toast-history-panel';
    historyPanel.innerHTML = `
        <div class="toast-history-header">
            <span class="toast-history-title">📜 消息历史</span>
            <button class="toast-history-clear" onclick="clearToastHistory()">清空</button>
        </div>
        <div class="toast-history-list" id="toast-history-list">
            <div class="toast-history-empty">
                <div class="toast-history-empty-icon">📭</div>
                <div>暂无消息</div>
            </div>
        </div>
    `;
    document.body.appendChild(historyPanel);
    
    // 点击外部关闭面板
    document.addEventListener('click', function(e) {
        const panel = document.getElementById('toast-history-panel');
        const btn = document.querySelector('.toast-history-btn');
        if (panel && panel.classList.contains('show') && 
            !panel.contains(e.target) && !btn.contains(e.target)) {
            panel.classList.remove('show');
        }
    });
}

// 显示成功消息
function showSuccess(message) {
    showMessage(message, 'success');
}

// 显示错误消息
function showError(message) {
    showMessage(message, 'error');
}

// 显示警告消息
function showWarning(message) {
    showMessage(message, 'warning');
}

// 显示信息消息
function showInfo(message) {
    showMessage(message, 'info');
}

// 统一消息显示函数
function showMessage(message, type = 'info') {
    // 移除已存在的消息
    const existingMessage = document.getElementById('toast-message');
    if (existingMessage) {
        existingMessage.remove();
    }
    
    // 保存到历史
    addToHistory(message, type);
    
    // 创建消息元素
    const toast = document.createElement('div');
    toast.id = 'toast-message';
    toast.className = `toast-message toast-${type}`;
    
    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };
    
    toast.innerHTML = `
        <span class="toast-icon">${icons[type]}</span>
        <span class="toast-text">${message}</span>
        <button class="toast-close" onclick="closeToast(this)">&times;</button>
    `;
    
    // 添加到DOM
    document.body.appendChild(toast);
    
    // 强制浏览器重绘以触发动画
    toast.offsetHeight;
    
    // 3秒后自动隐藏
    if (toastTimer) {
        clearTimeout(toastTimer);
    }
    toastTimer = setTimeout(() => {
        closeToast(toast);
    }, 3000);
}

// 关闭Toast消息
function closeToast(elementOrButton) {
    const toast = elementOrButton.classList.contains('toast-message') 
        ? elementOrButton 
        : elementOrButton.closest('.toast-message');
    
    if (toast) {
        toast.classList.add('toast-hide');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 300);
    }
}

function addToHistory(message, type) {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('zh-CN');
    
    window.toastHistory.unshift({
        message: message,
        type: type,
        time: timeStr
    });
    
    // 最多保留50条
    if (window.toastHistory.length > 50) {
        window.toastHistory = window.toastHistory.slice(0, 50);
    }
    
    updateBadge();
    renderHistory();
}

function toggleToastHistory() {
    const panel = document.getElementById('toast-history-panel');
    if (panel.classList.contains('show')) {
        panel.classList.remove('show');
    } else {
        panel.classList.add('show');
        // 清空徽章
        const badge = document.getElementById('toast-badge');
        badge.style.display = 'none';
        badge.textContent = '0';
    }
}

function renderHistory() {
    const list = document.getElementById('toast-history-list');
    if (!list) return;
    
    if (window.toastHistory.length === 0) {
        list.innerHTML = `
            <div class="toast-history-empty">
                <div class="toast-history-empty-icon">📭</div>
                <div>暂无消息</div>
            </div>
        `;
        return;
    }
    
    list.innerHTML = window.toastHistory.map((item, index) => `
        <div class="toast-history-item ${item.type}" onclick="replayToast(${index})">
            <div>
                <div>${item.message}</div>
                <div class="toast-history-time">${item.time}</div>
            </div>
        </div>
    `).join('');
}

function replayToast(index) {
    const item = window.toastHistory[index];
    if (item) {
        showMessage(item.message, item.type);
    }
}

function clearToastHistory() {
    if (confirm('确定要清空所有消息历史吗？')) {
        window.toastHistory = [];
        renderHistory();
        updateBadge();
    }
}

function updateBadge() {
    const badge = document.getElementById('toast-badge');
    if (badge) {
        const panel = document.getElementById('toast-history-panel');
        if (!panel.classList.contains('show') && window.toastHistory.length > 0) {
            badge.textContent = Math.min(window.toastHistory.length, 99);
            badge.style.display = 'block';
        }
    }
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
