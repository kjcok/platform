// DataQ 数质宝 - 规则配置向导

let currentStep = 1;
let selectedTemplate = null;
let assetId = null;

// 规则模板定义
const TEMPLATES = [
    {
        id: 'completeness',
        name: '完整性校验',
        icon: '✅',
        description: '检查字段是否为空或记录是否完整',
        type: 'completeness',
        ge_expectation: 'expect_column_values_to_not_be_null',
        strength_default: 'strong',
        params: [
            { name: 'column_name', label: '字段名', type: 'text', required: true, placeholder: '例如: user_id 或 user_id,email,phone', help: '单个字段或多个字段（用逗号分隔）' },
            { name: 'mostly', label: '通过率阈值', type: 'number', required: false, placeholder: '0.95', default: '0.95', min: '0', max: '1', step: '0.01', help: '允许的最小通过率（0-1之间）' }
        ],
        sql_template: "SELECT COUNT(*) as null_count\nFROM {table_name}\nWHERE {column_name} IS NULL;\n\n-- 期望: null_count = 0 或 null_count/total_count <= {mostly}"
    },
    {
        id: 'uniqueness',
        name: '唯一性校验',
        icon: '🔑',
        description: '检查字段值是否存在重复',
        type: 'uniqueness',
        ge_expectation: 'expect_column_values_to_be_unique',
        strength_default: 'strong',
        params: [
            { name: 'column_name', label: '字段名', type: 'text', required: true, placeholder: '例如: email 或 email,phone', help: '单个字段或多个字段组合（用逗号分隔）' }
        ],
        sql_template: "SELECT {column_name}, COUNT(*) as cnt\nFROM {table_name}\nGROUP BY {column_name}\nHAVING COUNT(*) > 1;\n\n-- 期望: 返回空结果集（无重复值）"
    },
    {
        id: 'validity',
        name: '有效性校验',
        icon: '✔️',
        description: '检查字段值是否符合特定格式或范围',
        type: 'validity',
        ge_expectation: 'expect_column_values_to_match_regex',
        strength_default: 'weak',
        params: [
            { name: 'column_name', label: '字段名', type: 'text', required: true, placeholder: '例如: phone', help: '选择需要校验格式的字段' },
            { name: 'regex', label: '正则表达式', type: 'text', required: true, placeholder: '例如: ^1[3-9]\\d{9}$', help: '匹配值的正则表达式' },
            { name: 'mostly', label: '通过率阈值', type: 'number', required: false, placeholder: '0.95', default: '0.95', min: '0', max: '1', step: '0.01', help: '允许的最小通过率（0-1之间）' }
        ],
        sql_template: "SELECT {column_name}\nFROM {table_name}\nWHERE {column_name} NOT REGEXP '{regex}';\n\n-- 期望: 返回空结果集（所有值都匹配正则）"
    },
    {
        id: 'range',
        name: '范围校验',
        icon: '📊',
        description: '检查数值字段是否在指定范围内',
        type: 'validity',
        ge_expectation: 'expect_column_values_to_be_between',
        strength_default: 'weak',
        params: [
            { name: 'column_name', label: '字段名', type: 'text', required: true, placeholder: '例如: age', help: '选择需要校验范围的字段' },
            { name: 'min_value', label: '最小值', type: 'number', required: false, placeholder: '例如: 0', help: '允许的最小值（留空表示无下限）' },
            { name: 'max_value', label: '最大值', type: 'number', required: false, placeholder: '例如: 150', help: '允许的最大值（留空表示无上限）' }
        ],
        sql_template: "SELECT {column_name}\nFROM {table_name}\nWHERE ({min_value} IS NOT NULL AND {column_name} < {min_value})\n   OR ({max_value} IS NOT NULL AND {column_name} > {max_value});\n\n-- 期望: 返回空结果集（所有值都在范围内）"
    },
    {
        id: 'timeliness',
        name: '及时性校验',
        icon: '⏰',
        description: '检查数据是否按时更新或记录数是否正常',
        type: 'timeliness',
        ge_expectation: 'expect_table_row_count_to_be_between',
        strength_default: 'weak',
        params: [
            { name: 'min_value', label: '最小行数', type: 'number', required: false, placeholder: '例如: 1000', help: '期望的最小记录数' },
            { name: 'max_value', label: '最大行数', type: 'number', required: false, placeholder: '例如: 1000000', help: '期望的最大记录数' }
        ],
        sql_template: "SELECT COUNT(*) as row_count\nFROM {table_name};\n\n-- 期望: row_count 在 [{min_value}, {max_value}] 范围内"
    },
    {
        id: 'consistency',
        name: '一致性校验',
        icon: '🔄',
        description: '检查字段值是否属于预期的值集合',
        type: 'consistency',
        ge_expectation: 'expect_column_values_to_be_in_set',
        strength_default: 'weak',
        params: [
            { name: 'column_name', label: '字段名', type: 'text', required: true, placeholder: '例如: gender', help: '选择需要校验的字段' },
            { name: 'value_set', label: '允许值集合', type: 'text', required: true, placeholder: '例如: ["男", "女", "未知"]', help: 'JSON格式的值集合，如: ["男", "女", "未知"]' }
        ],
        sql_template: "SELECT {column_name}\nFROM {table_name}\nWHERE {column_name} NOT IN {value_set};\n\n-- 期望: 返回空结果集（所有值都在集合中）"
    },
    {
        id: 'custom_sql',
        name: '自定义SQL',
        icon: '💻',
        description: '使用自定义SQL语句进行复杂校验',
        type: 'custom_sql',
        ge_expectation: 'expect_custom_sql',
        strength_default: 'weak',
        params: [
            { name: 'sql_query', label: 'SQL查询语句', type: 'textarea', required: true, placeholder: 'SELECT * FROM table WHERE condition', help: '返回异常数据的SQL查询，如果返回结果则表示校验失败' }
        ],
        sql_template: "{sql_query}"
    }
];

document.addEventListener('DOMContentLoaded', function() {
    // 从URL获取资产ID（可选）
    const urlParams = new URLSearchParams(window.location.search);
    assetId = urlParams.get('asset_id');
    
    if (assetId) {
        // 有asset_id：直接进入配置流程
        showSuccess(`正在为资产 #${assetId} 配置规则`);
    } else {
        // 无asset_id：显示资产选择器
        document.getElementById('asset-selector-section').style.display = 'block';
        showInfo('请先选择要配置规则的资产，或从资产管理页面进入');
    }
    
    loadTemplates();
    
    // 只在无asset_id时加载资产列表
    if (!assetId) {
        loadAssetsForSelection();
    }
});

/**
 * 加载资产列表供选择
 */
async function loadAssetsForSelection() {
    try {
        const response = await apiRequest(`${API_BASE_URL}/assets?page=1&per_page=100`);
        const assets = response.data.assets || [];
        
        const selector = document.getElementById('asset-selector');
        assets.forEach(asset => {
            const option = document.createElement('option');
            option.value = asset.id;
            option.textContent = `${asset.name} (${asset.asset_type})`;
            selector.appendChild(option);
        });
        
    } catch (error) {
        console.error('加载资产列表失败:', error);
        showError('加载资产列表失败，请刷新页面重试');
    }
}

/**
 * 加载模板列表
 */
function loadTemplates() {
    const templateGrid = document.getElementById('template-grid');
    
    templateGrid.innerHTML = TEMPLATES.map(template => `
        <div class="template-card" data-template-id="${template.id}" onclick="selectTemplate('${template.id}')">
            <div class="template-check">✓</div>
            <div class="template-icon">${template.icon}</div>
            <div class="template-name">${template.name}</div>
            <div class="template-desc">${template.description}</div>
            <div class="template-type">${template.type}</div>
        </div>
    `).join('');
}

/**
 * 选择模板
 */
function selectTemplate(templateId) {
    selectedTemplate = TEMPLATES.find(t => t.id === templateId);
    
    // 更新卡片选中状态
    document.querySelectorAll('.template-card').forEach(card => {
        card.classList.remove('selected');
    });
    document.querySelector(`[data-template-id="${templateId}"]`).classList.add('selected');
}

/**
 * 下一步
 */
function nextStep() {
    if (currentStep === 1) {
        if (!selectedTemplate) {
            showWarning('请先选择一个规则模板');
            return;
        }
        renderTemplateParams();
    } else if (currentStep === 2) {
        if (!validateStep2()) {
            return;
        }
        generatePreview();
    } else if (currentStep === 3) {
        createRule();
        return;
    }
    
    if (currentStep < 3) {
        currentStep++;
        updateWizard();
    }
}

/**
 * 上一步
 */
function prevStep() {
    if (currentStep > 1) {
        currentStep--;
        updateWizard();
    }
}

/**
 * 更新向导状态
 */
function updateWizard() {
    // 更新步骤条
    document.querySelectorAll('.step').forEach((step, index) => {
        const stepNum = index + 1;
        step.classList.remove('active', 'completed');
        
        if (stepNum === currentStep) {
            step.classList.add('active');
        } else if (stepNum < currentStep) {
            step.classList.add('completed');
            step.querySelector('.step-circle').textContent = '✓';
        }
    });
    
    // 更新内容区域
    document.querySelectorAll('.wizard-step').forEach((step, index) => {
        step.classList.remove('active');
        if (index + 1 === currentStep) {
            step.classList.add('active');
        }
    });
    
    // 更新按钮
    document.getElementById('btn-prev').style.display = currentStep === 1 ? 'none' : 'inline-block';
    
    const btnNext = document.getElementById('btn-next');
    if (currentStep === 3) {
        btnNext.textContent = '创建规则';
    } else {
        btnNext.textContent = '下一步';
    }
}

/**
 * 渲染模板参数表单
 */
function renderTemplateParams() {
    const paramsContainer = document.getElementById('template-params');
    
    let html = '';
    selectedTemplate.params.forEach(param => {
        html += `
            <div class="form-group">
                <label class="form-label">
                    ${param.label} ${param.required ? '<span class="required">*</span>' : ''}
                </label>
        `;
        
        if (param.type === 'textarea') {
            html += `<textarea id="param-${param.name}" class="form-textarea" 
                ${param.required ? 'required' : ''}
                placeholder="${param.placeholder || ''}">${param.default || ''}</textarea>`;
        } else if (param.name === 'column_name') {
            // 字段名特殊处理：支持多字段选择
            html += `<input type="text" id="param-${param.name}" class="form-input" 
                ${param.required ? 'required' : ''}
                placeholder="${param.placeholder || ''}" 
                value="${param.default || ''}">
                <div class="form-hint">💡 提示：可以输入多个字段，用逗号分隔，例如：user_id,email,phone</div>
                <div class="multi-field-selector" style="margin-top: 0.5rem;">
                    <button type="button" class="btn btn-sm btn-secondary" onclick="showFieldSelector()">📋 从资产字段中选择</button>
                </div>`;
        } else {
            html += `<input type="${param.type}" id="param-${param.name}" class="form-input" 
                ${param.required ? 'required' : ''}
                ${param.min ? `min="${param.min}"` : ''}
                ${param.max ? `max="${param.max}"` : ''}
                ${param.step ? `step="${param.step}"` : ''}
                placeholder="${param.placeholder || ''}" 
                value="${param.default || ''}">`;
        }
        
        if (param.help && param.name !== 'column_name') {
            html += `<div class="form-hint">${param.help}</div>`;
        }
        
        html += `</div>`;
    });
    
    paramsContainer.innerHTML = html;
}

/**
 * 验证步骤2
 */
function validateStep2() {
    // 如果没有asset_id，验证资产选择器
    if (!assetId) {
        const selectedAssetId = document.getElementById('asset-selector').value;
        if (!selectedAssetId) {
            showWarning('请先选择目标资产');
            document.getElementById('asset-selector').focus();
            return false;
        }
        // 保存选中的资产ID
        assetId = selectedAssetId;
    }
    
    const ruleName = document.getElementById('rule-name').value.trim();
    if (!ruleName) {
        showWarning('请输入规则名称');
        document.getElementById('rule-name').focus();
        return false;
    }
    
    // 验证动态参数
    for (let param of selectedTemplate.params) {
        if (param.required) {
            const value = document.getElementById(`param-${param.name}`).value.trim();
            if (!value) {
                showWarning(`请填写${param.label}`);
                document.getElementById(`param-${param.name}`).focus();
                return false;
            }
        }
    }
    
    return true;
}

/**
 * 生成预览
 */
function generatePreview() {
    // 生成SQL
    let sql = selectedTemplate.sql_template;
    
    // 替换模板变量
    selectedTemplate.params.forEach(param => {
        const value = document.getElementById(`param-${param.name}`)?.value || `{${param.name}}`;
        const regex = new RegExp(`\\{${param.name}\\}`, 'g');
        sql = sql.replace(regex, value);
    });
    
    // 替换表名占位符
    sql = sql.replace(/\{table_name\}/g, 'your_table_name');
    
    document.getElementById('sql-preview').value = sql;
    
    // 生成摘要
    const previewSummary = document.getElementById('preview-summary');
    const ruleName = document.getElementById('rule-name').value;
    const strength = document.getElementById('rule-strength').value;
    const description = document.getElementById('rule-description').value || '无';
    
    let paramsHtml = '';
    selectedTemplate.params.forEach(param => {
        const value = document.getElementById(`param-${param.name}`)?.value || '-';
        paramsHtml += `
            <div class="preview-item">
                <div class="preview-label">${param.label}</div>
                <div class="preview-value">${value}</div>
            </div>
        `;
    });
    
    previewSummary.innerHTML = `
        <div class="preview-item">
            <div class="preview-label">规则名称</div>
            <div class="preview-value">${ruleName}</div>
        </div>
        <div class="preview-item">
            <div class="preview-label">规则模板</div>
            <div class="preview-value">${selectedTemplate.icon} ${selectedTemplate.name}</div>
        </div>
        <div class="preview-item">
            <div class="preview-label">规则强度</div>
            <div class="preview-value">${strength === 'strong' ? '🔴 强规则' : '🟡 弱规则'}</div>
        </div>
        <div class="preview-item">
            <div class="preview-label">规则类型</div>
            <div class="preview-value">${selectedTemplate.type}</div>
        </div>
        <div class="preview-item" style="grid-column: span 2;">
            <div class="preview-label">规则描述</div>
            <div class="preview-value">${description}</div>
        </div>
        ${paramsHtml}
    `;
}

/**
 * 复制SQL
 */
function copySQL() {
    const sqlPreview = document.getElementById('sql-preview');
    sqlPreview.select();
    document.execCommand('copy');
    showSuccess('SQL已复制到剪贴板');
}

/**
 * 创建规则
 */
async function createRule() {
    const ruleName = document.getElementById('rule-name').value.trim();
    const strength = document.getElementById('rule-strength').value;
    const description = document.getElementById('rule-description').value.trim();
    
    // 收集参数
    const parameters = {};
    selectedTemplate.params.forEach(param => {
        const value = document.getElementById(`param-${param.name}`)?.value;
        if (value) {
            parameters[param.name] = value;
        }
    });
    
    const data = {
        name: ruleName,
        rule_type: selectedTemplate.type,
        rule_template: selectedTemplate.id,
        ge_expectation: selectedTemplate.ge_expectation,
        strength: strength,
        description: description,
        parameters: JSON.stringify(parameters)
    };
    
    // 如果有column_name参数，添加到顶层
    if (parameters.column_name) {
        data.column_name = parameters.column_name;
    }
    
    // 显示加载状态
    document.getElementById('loading-overlay').classList.add('show');
    
    try {
        const response = await apiRequest(`${API_BASE_URL}/assets/${assetId}/rules`, 'POST', data);
        
        document.getElementById('loading-overlay').classList.remove('show');
        showSuccess('规则创建成功！');
        
        // 跳转到资产详情页
        setTimeout(() => {
            window.location.href = `/assets/${assetId}`;
        }, 1500);
        
    } catch (error) {
        document.getElementById('loading-overlay').classList.remove('show');
        console.error('创建规则失败:', error);
        showError('创建规则失败: ' + error.message);
    }
}

/**
 * 显示字段选择器
 */
function showFieldSelector() {
    // 创建一个简单的字段输入对话框
    const currentFields = document.getElementById('param-column_name')?.value || '';
    
    const modalHtml = `
        <div id="field-selector-modal" class="modal show" style="display: flex;">
            <div class="modal-content" style="max-width: 600px;">
                <div class="modal-header">
                    <h3>📋 选择字段</h3>
                    <button class="close-btn" onclick="closeFieldSelector()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label class="form-label">可用字段（每行一个）</label>
                        <textarea id="available-fields" class="form-textarea" rows="10" placeholder="例如：\nuser_id\nusername\nemail\nphone\ncreated_at">${currentFields.split(',').map(f => f.trim()).filter(f => f).join('\n')}</textarea>
                        <div class="form-hint">💡 提示：勾选需要的字段，或直接在文本框中编辑</div>
                    </div>
                    <div class="form-group">
                        <label class="form-label">已选字段（用逗号分隔）</label>
                        <input type="text" id="selected-fields-output" class="form-input" value="${currentFields}" readonly>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="closeFieldSelector()">取消</button>
                    <button class="btn btn-primary" onclick="confirmFieldSelection()">确认选择</button>
                </div>
            </div>
        </div>
    `;
    
    // 移除已存在的模态框
    const existingModal = document.getElementById('field-selector-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // 添加新模态框
    document.body.insertAdjacentHTML('beforeend', modalHtml);
}

/**
 * 关闭字段选择器
 */
function closeFieldSelector() {
    const modal = document.getElementById('field-selector-modal');
    if (modal) {
        modal.remove();
    }
}

/**
 * 确认字段选择
 */
function confirmFieldSelection() {
    const availableFieldsText = document.getElementById('available-fields').value;
    const selectedFields = availableFieldsText
        .split('\n')
        .map(f => f.trim())
        .filter(f => f)
        .join(',');
    
    // 更新字段输入框
    const columnInput = document.getElementById('param-column_name');
    if (columnInput) {
        columnInput.value = selectedFields;
    }
    
    // 关闭模态框
    closeFieldSelector();
    
    showSuccess(`已选择 ${selectedFields.split(',').length} 个字段`);
}

/**
 * 取消向导
 */
function cancelWizard() {
    if (confirm('确定要取消规则配置吗？未保存的更改将会丢失。')) {
        window.history.back();
    }
}
