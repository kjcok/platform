/**
 * 规则管理页面 - 查看资产与规则的对应关系
 */

let currentAssetId = null;
let assets = [];

// Great Expectations 内置 Expectations 定义（用于参数编辑）
// 注意：保持与 rule_config_v2.js 中的定义一致
const GE_EXPECTATIONS = {
    'column_values': {
        name: '列值校验',
        expectations: [
            {
                id: 'expect_column_values_to_not_be_null',
                name: '非空校验',
                params: [
                    { name: 'mostly', label: '最小通过率', type: 'number', default: 1.0, min: 0, max: 1, step: 0.01 }
                ]
            },
            {
                id: 'expect_column_values_to_be_unique',
                name: '唯一性校验',
                params: []
            },
            {
                id: 'expect_column_values_to_be_in_type_list',
                name: '数据类型校验',
                params: [
                    { name: 'type_list', label: '允许的类型', type: 'select', options: ['STRING', 'INTEGER', 'FLOAT', 'BOOLEAN', 'DATETIME'], default: 'STRING' }
                ]
            },
            {
                id: 'expect_column_values_to_match_regex',
                name: '正则匹配校验',
                params: [
                    { name: 'regex', label: '正则表达式', type: 'text', placeholder: '例如: ^1[3-9]\\d{9}$', required: true },
                    { name: 'mostly', label: '最小通过率', type: 'number', default: 1.0, min: 0, max: 1, step: 0.01 }
                ]
            },
            {
                id: 'expect_column_values_to_not_match_regex',
                name: '正则排除校验',
                params: [
                    { name: 'regex', label: '正则表达式', type: 'text', placeholder: '例如: password', required: true },
                    { name: 'mostly', label: '最小通过率', type: 'number', default: 1.0, min: 0, max: 1, step: 0.01 }
                ]
            },
            {
                id: 'expect_column_values_to_be_in_set',
                name: '枚举值校验',
                params: [
                    { name: 'value_set', label: '允许的取值（每行一个）', type: 'textarea', placeholder: '例如:\n男\n女\n其他', required: true },
                    { name: 'mostly', label: '最小通过率', type: 'number', default: 1.0, min: 0, max: 1, step: 0.01 }
                ]
            },
            {
                id: 'expect_column_values_to_not_be_in_set',
                name: '排除值校验',
                params: [
                    { name: 'value_set', label: '禁止的取值（每行一个）', type: 'textarea', placeholder: '例如:\nNULL\nN/A\n-', required: true },
                    { name: 'mostly', label: '最小通过率', type: 'number', default: 1.0, min: 0, max: 1, step: 0.01 }
                ]
            },
            {
                id: 'expect_column_values_to_be_between',
                name: '数值范围校验',
                params: [
                    { name: 'min_value', label: '最小值', type: 'number', placeholder: '留空表示不限制' },
                    { name: 'max_value', label: '最大值', type: 'number', placeholder: '留空表示不限制' },
                    { name: 'mostly', label: '最小通过率', type: 'number', default: 1.0, min: 0, max: 1, step: 0.01 }
                ]
            }
        ]
    },
    'datetime': {
        name: '日期时间校验',
        expectations: [
            {
                id: 'expect_column_values_to_be_dateutil_parseable',
                name: '日期可解析性校验',
                params: [
                    { name: 'mostly', label: '最小通过率', type: 'number', default: 1.0, min: 0, max: 1, step: 0.01 }
                ]
            },
            {
                id: 'expect_column_values_to_match_strftime_format',
                name: '日期格式匹配校验',
                params: [
                    { name: 'strftime_format', label: '日期格式(strftime)', type: 'text', placeholder: '例如: %Y-%m-%d', required: true },
                    { name: 'mostly', label: '最小通过率', type: 'number', default: 1.0, min: 0, max: 1, step: 0.01 }
                ]
            },
            {
                id: 'expect_column_values_to_be_increasing',
                name: '日期递增校验',
                params: [
                    { name: 'strictly', label: '严格递增', type: 'select', options: ['true', 'false'], default: 'false' },
                    { name: 'mostly', label: '最小通过率', type: 'number', default: 1.0, min: 0, max: 1, step: 0.01 }
                ]
            },
            {
                id: 'expect_column_values_to_be_decreasing',
                name: '日期递减校验',
                params: [
                    { name: 'strictly', label: '严格递减', type: 'select', options: ['true', 'false'], default: 'false' },
                    { name: 'mostly', label: '最小通过率', type: 'number', default: 1.0, min: 0, max: 1, step: 0.01 }
                ]
            },
            {
                id: 'expect_column_values_to_be_between',
                name: '日期范围校验（逐行校验）⭐',
                params: [
                    { name: 'min_value', label: '最小日期', type: 'text', placeholder: 'YYYY-MM-DD' },
                    { name: 'max_value', label: '最大日期', type: 'text', placeholder: 'YYYY-MM-DD' },
                    { name: 'mostly', label: '最小通过率', type: 'number', default: 1.0, min: 0, max: 1, step: 0.01 }
                ]
            },
            {
                id: 'expect_column_min_to_be_between',
                name: '最小日期范围校验（整列聚合）',
                params: [
                    { name: 'min_value', label: '最小值下限', type: 'text', placeholder: 'YYYY-MM-DD' },
                    { name: 'max_value', label: '最小值上限', type: 'text', placeholder: 'YYYY-MM-DD' }
                ]
            },
            {
                id: 'expect_column_max_to_be_between',
                name: '最大日期范围校验（整列聚合）',
                params: [
                    { name: 'min_value', label: '最大值下限', type: 'text', placeholder: 'YYYY-MM-DD' },
                    { name: 'max_value', label: '最大值上限', type: 'text', placeholder: 'YYYY-MM-DD' }
                ]
            }
        ]
    }
};

/**
 * 根据规则类型查找 Expectation 定义
 */
function findExpectationByRuleType(ruleType) {
    for (const categoryKey of Object.keys(GE_EXPECTATIONS)) {
        const category = GE_EXPECTATIONS[categoryKey];
        const expectation = category.expectations.find(exp => exp.id === ruleType);
        if (expectation) {
            return expectation;
        }
    }
    return null;
}

/**
 * 渲染规则参数表单 HTML
 */
function renderRuleParamsForm(expectation, ruleConfigJson) {
    if (!expectation || !expectation.params || expectation.params.length === 0) {
        return '';
    }
    
    // 解析 rule_config_json
    let configValues = {};
    if (ruleConfigJson) {
        try {
            configValues = typeof ruleConfigJson === 'string' ? JSON.parse(ruleConfigJson) : ruleConfigJson;
        } catch (e) {
            console.warn('解析 rule_config_json 失败:', e);
        }
    }
    
    let paramsHtml = `
        <div class="form-divider" style="margin: 1.5rem 0; border-top: 1px solid #e2e8f0;"></div>
        <div class="form-section-title" style="font-weight: 600; color: #374151; margin-bottom: 1rem;">⚙️ 规则参数</div>
    `;
    
    expectation.params.forEach(param => {
        const value = configValues[param.name] !== undefined ? configValues[param.name] : (param.default !== undefined ? param.default : '');
        
        let inputHtml = '';
        
        if (param.type === 'select') {
            inputHtml = `
                <select id="edit-param-${param.name}" class="form-input">
                    ${param.options.map(opt => `
                        <option value="${opt}" ${value === opt ? 'selected' : ''}>${opt}</option>
                    `).join('')}
                </select>
            `;
        } else if (param.type === 'textarea') {
            // 处理数组类型的 value_set，转为换行分隔字符串
            const displayValue = Array.isArray(value) ? value.join('\n') : value;
            inputHtml = `
                <textarea id="edit-param-${param.name}" class="form-textarea" rows="3"
                    placeholder="${param.placeholder || ''}">${displayValue || ''}</textarea>
            `;
        } else {
            inputHtml = `
                <input type="${param.type}" id="edit-param-${param.name}" class="form-input"
                    value="${value || ''}" placeholder="${param.placeholder || ''}"
                    ${param.min !== undefined ? `min="${param.min}"` : ''}
                    ${param.max !== undefined ? `max="${param.max}"` : ''}
                    ${param.step !== undefined ? `step="${param.step}"` : ''}>
            `;
        }
        
        paramsHtml += `
            <div class="form-group">
                <label class="form-label">${param.label}${param.required ? ' *' : ''}</label>
                ${inputHtml}
            </div>
        `;
    });
    
    return paramsHtml;
}

/**
 * 收集规则参数值
 */
function collectRuleParams(expectation) {
    if (!expectation || !expectation.params) {
        return {};
    }
    
    const params = {};
    
    expectation.params.forEach(param => {
        const element = document.getElementById(`edit-param-${param.name}`);
        if (element) {
            let value = element.value;
            
            // 类型转换
            if (param.type === 'number') {
                value = value === '' ? null : parseFloat(value);
            } else if (param.type === 'textarea' && param.name === 'value_set') {
                // 将换行分隔的文本转为数组
                value = value.split('\n').map(v => v.trim()).filter(v => v);
            }
            
            if (value !== null && value !== '') {
                params[param.name] = value;
            }
        }
    });
    
    return params;
}

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
        const ruleTypeDisplay = rule.expectation_type || rule.rule_type || 'unknown';
        html += `
            <div class="rule-card">
                <div class="rule-card-header">
                    <div class="rule-name" title="${rule.name}">${rule.name}</div>
                </div>
                <div class="rule-info">
                    <div class="rule-info-item">
                        <div class="rule-info-label">规则类型</div>
                        <div class="rule-info-value">${getRuleTypeLabel(ruleTypeDisplay)}</div>
                    </div>
                    <div class="rule-info-item">
                        <div class="rule-info-label">字段</div>
                        <div class="rule-info-value" title="${rule.column_name || '-'}">${rule.column_name || '-'}</div>
                    </div>
                    <div class="rule-info-item">
                        <div class="rule-info-label">状态</div>
                        <div class="rule-info-value">${rule.enabled ? '✅ 已启用' : '⏸️ 已禁用'}</div>
                    </div>
                </div>
                ${rule.description ? `<div class="rule-description" title="${rule.description}">${rule.description}</div>` : ''}
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
        
        // 查找对应的 expectation 定义
        const expectation = findExpectationByRuleType(rule.rule_type) || 
                           findExpectationByRuleType(rule.expectation_type);
        
        // 渲染参数表单
        const paramsFormHtml = renderRuleParamsForm(expectation, rule.rule_config_json);
        
        // 创建编辑模态框
        const modalHtml = `
            <div id="edit-rule-modal" class="modal show" style="display: flex;">
                <div class="modal-content" style="max-width: 600px; max-height: 85vh; overflow-y: auto;">
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
                            <label class="form-label">规则类型</label>
                            <div class="form-input" style="background-color: #f7fafc; color: #666;">
                                ${expectation ? expectation.name : (getRuleTypeLabel(rule.rule_type) || rule.rule_type)}
                            </div>
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
                        ${paramsFormHtml}
                        <div class="form-group">
                            <label class="form-label">规则描述</label>
                            <textarea id="edit-rule-description" class="form-textarea" 
                                placeholder="请输入规则描述（可选）" rows="3">${rule.description || ''}</textarea>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" onclick="closeEditModal()">取消</button>
                        <button class="btn btn-primary" onclick="saveRuleEdit(${rule.id}, ${expectation ? 'true' : 'false'})">保存修改</button>
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
async function saveRuleEdit(ruleId, hasExpectation) {
    const data = {
        name: document.getElementById('edit-rule-name').value.trim(),
        column_name: document.getElementById('edit-column-name').value.trim() || null,
        is_active: document.getElementById('edit-rule-active').value === 'true',
        description: document.getElementById('edit-rule-description').value.trim() || null
    };
    
    if (!data.name) {
        showWarning('请输入规则名称');
        return;
    }
    
    // 如果有 expectation，收集参数
    if (hasExpectation) {
        try {
            // 先获取规则详情，重新查找 expectation
            const response = await apiRequest(`${API_BASE_URL}/rules/${ruleId}`);
            const rule = response.data;
            const expectation = findExpectationByRuleType(rule.rule_type) ||
                               findExpectationByRuleType(rule.expectation_type);

            if (expectation) {
                const params = collectRuleParams(expectation);
                // 合并现有的 parameters（如果是字符串先解析）
                let existingConfig = {};
                if (rule.parameters) {
                    try {
                        existingConfig = typeof rule.parameters === 'string' ?
                            JSON.parse(rule.parameters) : rule.parameters;
                    } catch (e) {
                        console.warn('解析现有 parameters 失败:', e);
                    }
                }
                data.parameters = JSON.stringify({ ...existingConfig, ...params });
            }
        } catch (e) {
            console.error('收集参数时出错:', e);
        }
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
