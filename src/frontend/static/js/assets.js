// DataQ 数质宝 - 资产管理页面

let currentPage = 1;
const perPage = 20;

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    loadAssets();
    
    // 绑定表单提交事件
    document.getElementById('asset-form').addEventListener('submit', handleAssetSubmit);
    
    // 绑定搜索和过滤事件
    document.getElementById('search-input').addEventListener('input', debounce(loadAssets, 500));
    document.getElementById('status-filter').addEventListener('change', () => {
        currentPage = 1;
        loadAssets();
    });
});

// 加载资产列表
async function loadAssets() {
    try {
        const searchQuery = document.getElementById('search-input').value;
        const statusFilter = document.getElementById('status-filter').value;
        
        let url = `${API_BASE_URL}/assets?page=${currentPage}&per_page=${perPage}`;
        
        if (statusFilter) {
            url += `&is_active=${statusFilter === 'active'}`;
        }
        
        const response = await apiRequest(url);
        const assets = response.data.assets;
        
        renderAssetsTable(assets);
        
    } catch (error) {
        console.error('加载资产列表失败:', error);
    }
}

// 渲染资产表格
function renderAssetsTable(assets) {
    const tbody = document.getElementById('assets-table-body');
    
    if (assets.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="loading">暂无数据</td></tr>';
        return;
    }
    
    tbody.innerHTML = assets.map(asset => `
        <tr>
            <td>${asset.id}</td>
            <td>${asset.name}</td>
            <td>${asset.data_source}</td>
            <td>${asset.asset_type}</td>
            <td>${asset.owner || '-'}</td>
            <td>${asset.rule_count || 0}</td>
            <td>${getStatusBadge(asset.is_active ? 'active' : 'inactive')}</td>
            <td>${formatDate(asset.created_at)}</td>
            <td>
                <button class="btn btn-primary" onclick="editAsset(${asset.id})">编辑</button>
                <button class="btn btn-danger" onclick="deleteAsset(${asset.id})">删除</button>
            </td>
        </tr>
    `).join('');
}

// 显示创建资产模态框
function showCreateAssetModal() {
    document.getElementById('modal-title').textContent = '新建资产';
    document.getElementById('asset-form').reset();
    document.getElementById('asset-id').value = '';
    document.getElementById('asset-modal').style.display = 'flex';
}

// 编辑资产
async function editAsset(assetId) {
    try {
        const response = await apiRequest(`${API_BASE_URL}/assets/${assetId}`);
        const asset = response.data;
        
        document.getElementById('modal-title').textContent = '编辑资产';
        document.getElementById('asset-id').value = asset.id;
        document.getElementById('asset-name').value = asset.name;
        document.getElementById('data-source').value = asset.data_source;
        document.getElementById('asset-type').value = asset.asset_type;
        document.getElementById('owner').value = asset.owner || '';
        document.getElementById('description').value = asset.description || '';
        
        document.getElementById('asset-modal').style.display = 'flex';
        
    } catch (error) {
        console.error('加载资产详情失败:', error);
    }
}

// 关闭模态框
function closeAssetModal() {
    document.getElementById('asset-modal').style.display = 'none';
}

// 处理表单提交
async function handleAssetSubmit(event) {
    event.preventDefault();
    
    const assetId = document.getElementById('asset-id').value;
    const data = {
        name: document.getElementById('asset-name').value,
        data_source: document.getElementById('data-source').value,
        asset_type: document.getElementById('asset-type').value,
        owner: document.getElementById('owner').value,
        description: document.getElementById('description').value
    };
    
    try {
        if (assetId) {
            // 更新资产
            await apiRequest(`${API_BASE_URL}/assets/${assetId}`, 'PUT', data);
            showSuccess('资产更新成功');
        } else {
            // 创建资产
            await apiRequest(`${API_BASE_URL}/assets`, 'POST', data);
            showSuccess('资产创建成功');
        }
        
        closeAssetModal();
        loadAssets();
        
    } catch (error) {
        console.error('保存资产失败:', error);
    }
}

// 删除资产
async function deleteAsset(assetId) {
    if (!confirmAction('确定要删除这个资产吗？此操作不可恢复！')) {
        return;
    }
    
    try {
        await apiRequest(`${API_BASE_URL}/assets/${assetId}`, 'DELETE');
        showSuccess('资产删除成功');
        loadAssets();
        
    } catch (error) {
        console.error('删除资产失败:', error);
    }
}

// 防抖函数
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
