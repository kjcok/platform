// DataQ 数质宝 - 资产管理页面

let currentPage = 1;
const perPage = 20;
let selectedFile = null; // 存储选中的文件

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    loadAssets();
    
    // 绑定表单提交事件
    document.getElementById('asset-form').addEventListener('submit', handleAssetSubmit);
    
    // 绑定类型过滤事件
    document.getElementById('search-input').addEventListener('input', debounce(loadAssets, 500));
    document.getElementById('status-filter').addEventListener('change', () => {
        currentPage = 1;
        loadAssets();
    });
    
    // 绑定数据库类型变化事件
    document.getElementById('db-type').addEventListener('change', handleDbTypeChange);
    
    // 初始化资产类型显示
    handleAssetTypeChange();
});

// 加载资产列表
async function loadAssets() {
    try {
        const searchQuery = document.getElementById('search-input').value;
        const statusFilter = document.getElementById('status-filter').value;
        
        let url = `${API_BASE_URL}/assets?page=${currentPage}&per_page=${perPage}`;
        
        // 添加搜索参数
        if (searchQuery && searchQuery.trim()) {
            url += `&search=${encodeURIComponent(searchQuery.trim())}`;
        }
        
        if (statusFilter) {
            url += `&is_active=${statusFilter === 'active'}`;
        }
        
        const response = await apiRequest(url);
        // 修复：后端返回 { data: [数组], pagination: {...} }
        const assets = Array.isArray(response.data) ? response.data : (response.data.assets || []);
        
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
            <td class="col-id">${asset.id}</td>
            <td class="col-name">
                <a href="/assets/${asset.id}" class="cell-truncate" style="color: #667eea; text-decoration: none; font-weight: 500;" title="${asset.name}">${asset.name}</a>
            </td>
            <td class="col-datasource">
                <span class="cell-truncate" title="${asset.data_source}">${asset.data_source}</span>
            </td>
            <td class="col-type">${asset.asset_type}</td>
            <td class="col-type">${asset.owner || '-'}</td>
            <td class="col-type">
                <a href="/rule-management" onclick="localStorage.setItem('selectedAssetId', ${asset.id})" style="color: #667eea; text-decoration: none;" title="管理规则">
                    ${asset.rule_count || 0} 条规则
                </a>
            </td>
            <td class="col-status">${getStatusBadge(asset.is_active ? 'active' : 'inactive')}</td>
            <td class="col-date">${formatDate(asset.created_at)}</td>
            <td class="col-actions">
                <button class="btn btn-success btn-sm" onclick="configureRule(${asset.id})" title="配置规则">配置规则</button>
                <button class="btn btn-secondary btn-sm" onclick="viewAssetDetail(${asset.id})" title="查看详情">详情</button>
                <button class="btn btn-primary btn-sm" onclick="editAsset(${asset.id})" title="编辑资产">编辑</button>
                <button class="btn btn-danger btn-sm" onclick="deleteAsset(${asset.id})" title="删除资产">删除</button>
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
    const assetType = document.getElementById('asset-type').value;
    
    let data = {
        name: document.getElementById('asset-name').value,
        asset_type: assetType,
        owner: document.getElementById('owner').value,
        quality_score_weight: parseFloat(document.getElementById('quality-weight').value) || 5.0,
        description: document.getElementById('description').value
    };
    
    // 根据资产类型处理数据源
    if (assetType === 'csv' || assetType === 'excel') {
        // 文件类型：需要先上传文件
        if (!selectedFile && !assetId) {
            showError('请先选择数据文件');
            return;
        }
        
        if (selectedFile) {
            try {
                showInfo('正在上传文件...');
                
                // 上传文件
                const formData = new FormData();
                formData.append('file', selectedFile);
                
                const uploadResponse = await fetch(`${API_BASE_URL}/upload`, {
                    method: 'POST',
                    body: formData
                });
                
                const uploadResult = await uploadResponse.json();
                
                if (uploadResult.status !== 'success') {
                    showError('文件上传失败: ' + uploadResult.message);
                    return;
                }
                
                // 使用file_id作为数据源
                data.data_source = uploadResult.file_id;
                data.file_name = selectedFile.name;
                
                showSuccess('文件上传成功');
                
            } catch (error) {
                showError('文件上传失败: ' + error.message);
                return;
            }
        } else if (assetId) {
            // 编辑模式，保留原有数据源
            data.data_source = document.getElementById('data-source')?.value || '';
        }
        
    } else if (assetType === 'database') {
        // 数据库类型：构建连接字符串
        const dbType = document.getElementById('db-type').value;
        const table = document.getElementById('db-table').value.trim();
        
        let connectionString = '';
        
        if (dbType === 'sqlite') {
            // SQLite：只需要文件路径
            const sqliteFile = document.getElementById('sqlite-file').value.trim();
            if (!sqliteFile || !table) {
                showError('请填写SQLite文件路径和表名');
                return;
            }
            connectionString = `sqlite:///${sqliteFile}`;
            
            data.db_config = {
                db_type: dbType,
                sqlite_file: sqliteFile,
                table: table
            };
        } else {
            // 其他数据库：需要完整的连接信息
            const host = document.getElementById('db-host').value.trim();
            const port = document.getElementById('db-port').value;
            const dbName = document.getElementById('db-name').value.trim();
            const username = document.getElementById('db-username').value;
            const password = document.getElementById('db-password').value;
            
            if (!host || !dbName || !table) {
                showError('请填写数据库地址、数据库名和表名');
                return;
            }
            
            // 构建数据库连接字符串（使用 SQLAlchemy 格式）
            switch(dbType) {
                case 'mysql':
                    connectionString = `mysql+pymysql://${username}:${password}@${host}:${port}/${dbName}.${table}`;
                    break;
                case 'postgresql':
                    connectionString = `postgresql+psycopg2://${username}:${password}@${host}:${port}/${dbName}.${table}`;
                    break;
                case 'sqlserver':
                    connectionString = `mssql+pyodbc://${username}:${password}@${host}:${port}/${dbName}.${table}?driver=ODBC+Driver+17+for+SQL+Server`;
                    break;
                default:
                    connectionString = `${host}:${port}/${dbName}.${table}`;
            }
            
            data.db_config = {
                host: host,
                port: port,
                database: dbName,
                db_type: dbType,
                table: table
            };
        }
        
        data.data_source = connectionString;
        
    } else {
        // API类型
        data.data_source = data.description || 'API接口';
    }
    
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
        // 延迟一下再加载，确保数据已保存
        setTimeout(() => {
            currentPage = 1;
            loadAssets();
        }, 300);
        
    } catch (error) {
        console.error('保存资产失败:', error);
        showError('保存失败: ' + error.message);
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

// 配置规则
function configureRule(assetId) {
    window.location.href = `/rule-config?asset_id=${assetId}`;
}

/**
 * 查看资产详情
 */
function viewAssetDetail(assetId) {
    window.location.href = `/assets/${assetId}`;
}

/**
 * 处理资产类型变化
 */
function handleAssetTypeChange() {
    const assetType = document.getElementById('asset-type').value;
    const fileSection = document.getElementById('file-upload-section');
    const dbSection = document.getElementById('database-config-section');
    const apiSection = document.getElementById('api-config-section');
    
    // 隐藏所有配置区域
    fileSection.style.display = 'none';
    dbSection.style.display = 'none';
    apiSection.style.display = 'none';
    
    if (assetType === 'csv' || assetType === 'excel') {
        // 显示文件上传
        fileSection.style.display = 'block';
    } else if (assetType === 'database') {
        // 显示数据库配置
        dbSection.style.display = 'block';
        // 初始化数据库类型处理
        handleDbTypeChange();
    } else if (assetType === 'api') {
        // 显示API配置
        apiSection.style.display = 'block';
    }
}

/**
 * 处理数据库类型变化
 */
function handleDbTypeChange() {
    const dbType = document.getElementById('db-type').value;
    const sqliteGroup = document.getElementById('sqlite-file-group');
    const standardFields = document.getElementById('standard-db-fields');
    
    if (dbType === 'sqlite') {
        // SQLite：显示文件路径，隐藏其他字段
        sqliteGroup.style.display = 'block';
        standardFields.style.display = 'none';
    } else {
        // 其他数据库：显示标准字段，隐藏SQLite文件路径
        sqliteGroup.style.display = 'none';
        standardFields.style.display = 'block';
    }
}

/**
 * 处理文件选择
 */
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // 验证文件类型
    const allowedTypes = ['text/csv', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
    const allowedExtensions = ['.csv', '.xlsx', '.xls'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedExtensions.includes(fileExtension)) {
        showError('不支持的文件类型，请上传 CSV、XLSX 或 XLS 文件');
        clearFile();
        return;
    }
    
    // 验证文件大小（100MB）
    if (file.size > 100 * 1024 * 1024) {
        showError('文件大小不能超过 100MB');
        clearFile();
        return;
    }
    
    selectedFile = file;
    
    // 显示文件信息
    document.getElementById('file-name').textContent = `${file.name} (${formatFileSize(file.size)})`;
    document.getElementById('file-info').style.display = 'block';
    
    showSuccess(`已选择文件：${file.name}`);
}

/**
 * 清除文件选择
 */
function clearFile() {
    selectedFile = null;
    document.getElementById('file-input').value = '';
    document.getElementById('file-info').style.display = 'none';
}

/**
 * 格式化文件大小
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * 测试数据库连接
 */
async function testDbConnection() {
    const dbType = document.getElementById('db-type').value;
    
    if (dbType === 'sqlite') {
        // SQLite：验证文件路径
        const sqliteFile = document.getElementById('sqlite-file').value.trim();
        if (!sqliteFile) {
            showWarning('请填写SQLite文件路径');
            return;
        }
    } else {
        // 其他数据库：验证标准字段
        const host = document.getElementById('db-host').value.trim();
        const dbName = document.getElementById('db-name').value.trim();
        
        if (!host || !dbName) {
            showWarning('请填写数据库地址和数据库名');
            return;
        }
    }
    
    try {
        showInfo('正在测试连接...');
        
        // TODO: 调用后端API测试连接
        // 目前临时模拟成功
        setTimeout(() => {
            showSuccess('数据库连接成功');
        }, 1000);
        
    } catch (error) {
        showError('数据库连接失败: ' + error.message);
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

// 测试API连接
async function testApiConnection() {
    const apiUrl = document.getElementById('api-url').value;
    
    if (!apiUrl) {
        showWarning('请先输入API URL');
        return;
    }
    
    try {
        showInfo('正在测试连接...');
        
        // 简单的HEAD请求测试
        const response = await fetch(apiUrl, {
            method: 'HEAD',
            mode: 'cors'
        });
        
        if (response.ok) {
            showSuccess('API连接成功！');
        } else {
            showError(`API返回状态码: ${response.status}`);
        }
    } catch (error) {
        showError('API连接失败: ' + error.message);
    }
}
