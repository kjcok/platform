/**
 * 规则管理页面 - 查看资产与规则的对应关系
 */

let currentAssetId = null;
let assets = [];

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', () => {
    loadAssets();
});

/**
 * 加载所有资产列表
 */
async function loadAssets() {
    try {
        const response = await apiRequest(`${API_BASE_URL}/assets?page=1&per_page=100`);
        assets = Array.isArray(response.data) ? response.data : (response.data.assets || []);
        renderAssetList(assets);
        
    } catch (error) {
        console.error('加载资产列表失败:', error);
        showError('加载资产列表失败: ' + error.message);
    }
}

/**
 * 渲染资产列表
 */
function renderAssetList(assets) {
    const container = document.getElementById('asset-list');
    
    if (assets.length === 0) {
        container.innerHTML = `
            <div class="empty-state" style="padding: 2rem;">
                <div class="empty-icon">📊</div>
                <div class="empty-text">暂无资产</div>
                <button class="btn btn-primary" onclick="window.location.href='/assets'">创建资产</button>
            </div>
        `;
        return;
    }
    
    container.innerHTML = assets.map(asset => `
        <div class="asset-item" data-asset-id="${asset.id}" onclick="selectAsset(${asset.id})">
            <div class="asset-item-name">${asset.name}</div>
            <div class="asset-item-meta">
                <span>${asset.asset_type || '文件'}</span>
                <span class="rule-count-badge">${asset.rule_count || 0} 条规则</span>
            </div>
        </div>
    `).join('');
}

/**
 * 选择资产
 */
async function selectAsset(assetId) {
    currentAssetId = assetId;
    
    // 更新选中状态
    document.querySelectorAll('.asset-item').forEach(item => {
        item.classList.remove('active');
        if (parseInt(item.dataset.assetId) === assetId) {
            item.classList.add('active');
        }
    });
    
    // 更新标题
    const asset = assets.find(a => a.id === assetId);
    if (asset) {
        document.getElementById('rule-header-title').textContent = 
            `${asset.name} 的规则列表`;
        document.getElementById('rule-header-actions').style.display = 'flex';
    }
    
    // 加载规则列表
    await loadRules(assetId);
}

/**
 * 加载规则列表
 */
async function loadRules(assetId) {
    const container = document.getElementById('rule-list');
    container.innerHTML = `
        <div class="loading-spinner">
            <div class="spinner"></div>
        </div>
    `;
    
    try {
        const response = await apiRequest(`${API_BASE_URL}/assets/${assetId}/rules`);
        const rules = response.data.rules || [];
        renderRulesList(rules);
        
    } catch (error) {
        console.error('加载规则列表失败:', error);
        showError('加载规则列表失败: ' + error.message);
    }
}

/**
 * 渲染规则列表
 */
function renderRulesList(rules) {
    const container = document.getElementById('rule-list');
    
    if (!rules || rules.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📋</div>
                <div class="empty-text">该资产暂无规则</div>
                <button class="btn btn-primary" onclick="configureRule()">添加第一个规则</button>
            </div>
        `;
        return;
    }
    
    let html = '';
    rules.forEach(rule => {
        html += `
            <div class="rule-card">
                <div class="rule-card-header">
                    <div class="rule-name">${rule.name}</div>
                    <span class="rule-badge ${rule.strength === 'strong' ? 'badge-strong' : 'badge-weak'}">
                        ${rule.strength === 'strong' ? '强规则' : '弱规则'}
                    </span>
                </div>
                <div class="rule-info">
                    <div class="rule-info-item">
                        <div class="rule-info-label">规则类型</div>
                        <div class="rule-info-value">${getRuleTypeLabel(rule.rule_type)}</div>
                    </div>
                    <div class="rule-info-item">
                        <div class="rule-info-label">字段</div>
                        <div class="rule-info-value">${rule.column_name || '-'}</div>
                    </div>
                    <div class="rule-info-item">
                        <div class="rule-info-label">状态</div>
                        <div class="rule-info-value">${rule.enabled ? '✅ 已启用' : '⏸️ 已禁用'}</div>
                    </div>
                </div>
                ${rule.description ? `<div class="rule-description">${rule.description}</div>` : ''}
                <div class="rule-actions">
                    <button class="btn btn-secondary btn-small" onclick="editRule(${rule.id})">编辑</button>
                    <button class="btn btn-danger btn-small" onclick="deleteRule(${rule.id})">删除</button>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

/**
 * 配置规则
 */
function configureRule() {
    if (currentAssetId) {
        window.location.href = `/rule-config?asset_id=${currentAssetId}`;
    } else {
        window.location.href = `/rule-config`;
    }
}

/**
 * 编辑规则
 */
function editRule(ruleId) {
    openEditModal(ruleId);
}

/**
 * 打开编辑模态框
 */
async function openEditModal(ruleId) {
    try {
        const response = await apiRequest(`${API_BASE_URL}/rules/${ruleId}`);
        const rule = response.data;
        
        // 创建编辑模态框
        const modalHtml = `
            <div id="edit-rule-modal" class="modal show" style="display: flex;">
                <div class="modal-content" style="max-width: 600px;">
                    <div class="modal-header">
                        <h3>✏️ 编辑规则</h3>
                        <button class="close-btn" onclick="closeEditModal()">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label class="form-label">规则名称 *</label>
                            <input type="text" id="edit-rule-name" class="form-input" 
                                value="${rule.name}" placeholder="请输入规则名称">
                        </div>
                        <div class="form-group">
                            <label class="form-label">规则强度</label>
                            <select id="edit-rule-strength" class="form-input">
                                <option value="strong" ${rule.strength === 'strong' ? 'selected' : ''}>🔴 强规则（失败即中断）</option>
                                <option value="weak" ${rule.strength === 'weak' ? 'selected' : ''}>🟡 弱规则（仅记录）</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">字段名</label>
                            <input type="text" id="edit-column-name" class="form-input" 
                                value="${rule.column_name || ''}" placeholder="例如: user_id">
                            <div class="form-hint">留空表示全表级别规则</div>
                        </div>
                        <div class="form-group">
                            <label class="form-label">规则状态</label>
                            <select id="edit-rule-active" class="form-input">
                                <option value="true" ${rule.is_active ? 'selected' : ''}>✅ 启用</option>
                                <option value="false" ${!rule.is_active ? 'selected' : ''}>⏸️ 禁用</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">规则描述</label>
                            <textarea id="edit-rule-description" class="form-textarea" 
                                placeholder="请输入规则描述（可选）" rows="3">${rule.description || ''}</textarea>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" onclick="closeEditModal()">取消</button>
                        <button class="btn btn-primary" onclick="saveRuleEdit(${rule.id})">保存修改</button>
                    </div>
                </div>
            </div>
        `;
        
        // 移除已存在的模态框
        const existingModal = document.getElementById('edit-rule-modal');
        if (existingModal) {
            existingModal.remove();
        }
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
    } catch (error) {
        console.error('加载规则详情失败:', error);
        showError('加载规则详情失败: ' + error.message);
    }
}

/**
 * 关闭编辑模态框
 */
function closeEditModal() {
    const modal = document.getElementById('edit-rule-modal');
    if (modal) {
        modal.remove();
    }
}

/**
 * 保存规则修改
 */
async function saveRuleEdit(ruleId) {
    const data = {
        name: document.getElementById('edit-rule-name').value.trim(),
        strength: document.getElementById('edit-rule-strength').value,
        column_name: document.getElementById('edit-column-name').value.trim() || null,
        is_active: document.getElementById('edit-rule-active').value === 'true',
        description: document.getElementById('edit-rule-description').value.trim() || null
    };
    
    if (!data.name) {
        showWarning('请输入规则名称');
        return;
    }
    
    try {
        await apiRequest(`${API_BASE_URL}/rules/${ruleId}`, 'PUT', data);
        showSuccess('规则修改成功');
        closeEditModal();
        // 重新加载规则列表
        if (currentAssetId) {
            await loadRules(currentAssetId);
        }
    } catch (error) {
        console.error('保存规则修改失败:', error);
        showError('保存规则修改失败: ' + error.message);
    }
}

/**
 * 删除规则
 */
async function deleteRule(ruleId) {
    if (!confirm('确定要删除这个规则吗？此操作不可恢复。')) {
        return;
    }
    
    try {
        await apiRequest(`${API_BASE_URL}/rules/${ruleId}`, 'DELETE');
        showSuccess('规则删除成功');
        // 重新加载规则列表
        if (currentAssetId) {
            await loadRules(currentAssetId);
        }
        
    } catch (error) {
        showError('删除规则失败: ' + error.message);
    }
}

/**
 * 辅助函数：获取规则类型标签
 */
function getRuleTypeLabel(type) {
    const typeMap = {
        'completeness': '完整性校验',
        'uniqueness': '唯一性校验',
        'validity': '有效性校验',
        'range': '范围校验',
        'timeliness': '及时性校验',
        'consistency': '一致性校验',
        'custom_sql': '自定义SQL'
    };
    return typeMap[type] || type;
}

/**
 * API请求封装
 */
async function apiRequest(url, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
    }
    
    const response = await fetch(url, options);
    const result = await response.json();
    
    if (!response.ok) {
        throw new Error(result.message || '请求失败');
    }
    
    return result;
}
