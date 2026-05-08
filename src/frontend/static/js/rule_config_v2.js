// DataQ 数质宝 - 规则配置（GE Expectations版）

let selectedExpectation = null;
let assetId = null;
let availableColumns = [];
let selectedFields = [];

// Great Expectations 内置 Expectations 分类定义
const GE_EXPECTATIONS = {
    'column_values': {
        name: '列值校验',
        icon: '📊',
        description: '检查列中的值是否符合预期',
        expectations: [
            {
                id: 'expect_column_values_to_not_be_null',
                name: '非空校验',
                description: '检查列值不为空',
                params: [
                    { name: 'mostly', label: '最小通过率', type: 'number', default: 1.0, min: 0, max: 1, step: 0.01 }
                ],
                autoGenerateName: (column) => `${column}_非空校验`
            },
            {
                id: 'expect_column_values_to_be_unique',
                name: '唯一性校验',
                description: '检查列值无重复',
                params: [],
                autoGenerateName: (column) => `${column}_唯一性校验`
            },
            {
                id: 'expect_column_values_to_be_in_type_list',
                name: '数据类型校验',
                description: '检查列值的数据类型',
                params: [
                    { name: 'type_list', label: '允许的类型', type: 'select', options: ['STRING', 'INTEGER', 'FLOAT', 'BOOLEAN', 'DATETIME'], default: 'STRING' }
                ],
                autoGenerateName: (column) => `${column}_类型校验`
            },
            {
                id: 'expect_column_values_to_not_match_regex',
                name: '正则排除校验',
                description: '检查列值不匹配正则表达式',
                params: [
                    { name: 'regex', label: '正则表达式', type: 'text', placeholder: '例如: password', required: true },
                    { name: 'mostly', label: '最小通过率', type: 'number', default: 1.0, min: 0, max: 1, step: 0.01 }
                ],
                autoGenerateName: (column) => `${column}_排除校验`
            },
            {
                id: 'expect_column_values_to_match_regex',
                name: '正则匹配校验',
                description: '检查列值匹配正则表达式',
                params: [
                    { name: 'regex', label: '正则表达式', type: 'text', placeholder: '例如: ^1[3-9]\\d{9}$', required: true },
                    { name: 'mostly', label: '最小通过率', type: 'number', default: 1.0, min: 0, max: 1, step: 0.01 }
                ],
                autoGenerateName: (column) => `${column}_格式校验`
            },
            {
                id: 'expect_column_values_to_match_regex_list',
                name: '多正则匹配校验',
                description: '检查列值匹配多个正则表达式之一',
                params: [
                    { name: 'regex_list', label: '正则列表', type: 'textarea', placeholder: '每行一个正则表达式', required: true },
                    { name: 'mostly', label: '最小通过率', type: 'number', default: 1.0, min: 0, max: 1, step: 0.01 }
                ],
                autoGenerateName: (column) => `${column}_多正则匹配`
            },
            {
                id: 'expect_column_values_to_not_match_regex_list',
                name: '多正则排除校验',
                description: '检查列值不匹配任意正则表达式',
                params: [
                    { name: 'regex_list', label: '正则列表', type: 'textarea', placeholder: '每行一个正则表达式', required: true },
                    { name: 'mostly', label: '最小通过率', type: 'number', default: 1.0, min: 0, max: 1, step: 0.01 }
                ],
                autoGenerateName: (column) => `${column}_多正则排除`
            },
            {
                id: 'expect_column_values_to_be_in_set',
                name: '枚举值校验',
                description: '检查列值在指定集合中',
                params: [
                    { name: 'value_set', label: '允许的取值', type: 'textarea', placeholder: '每行一个值，例如:\n男\n女\n其他', required: true },
                    { name: 'mostly', label: '最小通过率', type: 'number', default: 1.0, min: 0, max: 1, step: 0.01 }
                ],
                autoGenerateName: (column) => `${column}_枚举值校验`
            },
            {
                id: 'expect_column_values_to_not_be_in_set',
                name: '排除值校验',
                description: '检查列值不在指定集合中',
                params: [
                    { name: 'value_set', label: '禁止的取值', type: 'textarea', placeholder: '每行一个值，例如:\nNULL\nN/A\n-', required: true },
                    { name: 'mostly', label: '最小通过率', type: 'number', default: 1.0, min: 0, max: 1, step: 0.01 }
                ],
                autoGenerateName: (column) => `${column}_排除值`
            },
            {
                id: 'expect_column_values_to_be_between',
                name: '数值范围校验',
                description: '检查列值在指定范围内',
                params: [
                    { name: 'min_value', label: '最小值', type: 'number', placeholder: '可选' },
                    { name: 'max_value', label: '最大值', type: 'number', placeholder: '可选' },
                    { name: 'mostly', label: '最小通过率', type: 'number', default: 1.0, min: 0, max: 1, step: 0.01 }
                ],
                autoGenerateName: (column) => `${column}_范围校验`
            },
            {
                id: 'expect_column_values_to_be_like',
                name: '模糊匹配校验',
                description: '检查列值匹配SQL LIKE模式',
                params: [
                    { name: 'pattern', label: 'LIKE模式', type: 'text', placeholder: '例如: www.%', required: true },
                    { name: 'mostly', label: '最小通过率', type: 'number', default: 1.0, min: 0, max: 1, step: 0.01 }
                ],
                autoGenerateName: (column) => `${column}_模糊匹配`
            },
            {
                id: 'expect_column_values_to_be_of_type',
                name: '数据类型校验(Spark)',
                description: '检查列值是指定Spark SQL类型',
                params: [
                    { name: 'type_', label: '类型名称', type: 'text', placeholder: '例如: IntegerType', required: true }
                ],
                autoGenerateName: (column) => `${column}_类型校验`
            },
            {
                id: 'expect_column_value_lengths_to_be_between',
                name: '字符串长度范围校验',
                description: '检查字符串长度在指定范围内',
                params: [
                    { name: 'min_value', label: '最小长度', type: 'number', required: true },
                    { name: 'max_value', label: '最大长度', type: 'number', required: true },
                    { name: 'mostly', label: '最小通过率', type: 'number', default: 1.0, min: 0, max: 1, step: 0.01 }
                ],
                autoGenerateName: (column) => `${column}_长度校验`
            },
            {
                id: 'expect_column_values_to_be_null',
                name: '为空校验',
                description: '检查列值为空',
                params: [
                    { name: 'mostly', label: '最小通过率', type: 'number', default: 1.0, min: 0, max: 1, step: 0.01 }
                ],
                autoGenerateName: (column) => `${column}_为空校验`
            }
        ]
    },
    'column_aggregates': {
        name: '列聚合校验',
        icon: '📈',
        description: '检查列的统计特征',
        expectations: [
            {
                id: 'expect_column_mean_to_be_between',
                name: '平均值范围校验',
                description: '检查列的平均值在范围内',
                params: [
                    { name: 'min_value', label: '最小平均值', type: 'number' },
                    { name: 'max_value', label: '最大平均值', type: 'number' }
                ],
                autoGenerateName: (column) => `${column}_平均值校验`
            },
            {
                id: 'expect_column_median_to_be_between',
                name: '中位数范围校验',
                description: '检查列的中位数在范围内',
                params: [
                    { name: 'min_value', label: '最小中位数', type: 'number' },
                    { name: 'max_value', label: '最大中位数', type: 'number' }
                ],
                autoGenerateName: (column) => `${column}_中位数校验`
            },
            {
                id: 'expect_column_stdev_to_be_between',
                name: '标准差范围校验',
                description: '检查列的标准差在范围内',
                params: [
                    { name: 'min_value', label: '最小标准差', type: 'number' },
                    { name: 'max_value', label: '最大标准差', type: 'number' }
                ],
                autoGenerateName: (column) => `${column}_标准差校验`
            },
            {
                id: 'expect_column_min_to_be_between',
                name: '最小值范围校验',
                description: '检查列的最小值在范围内',
                params: [
                    { name: 'min_value', label: '最小值下限', type: 'number' },
                    { name: 'max_value', label: '最小值上限', type: 'number' }
                ],
                autoGenerateName: (column) => `${column}_最小值校验`
            },
            {
                id: 'expect_column_max_to_be_between',
                name: '最大值范围校验',
                description: '检查列的最大值在范围内',
                params: [
                    { name: 'min_value', label: '最大值下限', type: 'number' },
                    { name: 'max_value', label: '最大值上限', type: 'number' }
                ],
                autoGenerateName: (column) => `${column}_最大值校验`
            },
            {
                id: 'expect_column_sum_to_be_between',
                name: '总和范围校验',
                description: '检查列的总和在范围内',
                params: [
                    { name: 'min_value', label: '最小总和', type: 'number' },
                    { name: 'max_value', label: '最大总和', type: 'number' }
                ],
                autoGenerateName: (column) => `${column}_总和校验`
            },
            {
                id: 'expect_column_unique_value_count_to_be_between',
                name: '唯一值数量校验',
                description: '检查列的唯一值数量在范围内',
                params: [
                    { name: 'min_value', label: '最小唯一值数量', type: 'integer' },
                    { name: 'max_value', label: '最大唯一值数量', type: 'integer' }
                ],
                autoGenerateName: (column) => `${column}_唯一值数量校验`
            },
            {
                id: 'expect_column_percentile_to_be_between',
                name: '百分位数校验',
                description: '检查列的指定百分位数在范围内',
                params: [
                    { name: 'percentile', label: '百分位数', type: 'number', step: 0.01, min: 0, max: 1, required: true },
                    { name: 'min_value', label: '最小值', type: 'number', required: true },
                    { name: 'max_value', label: '最大值', type: 'number', required: true }
                ],
                autoGenerateName: (column) => `${column}_百分位数校验`
            },
            {
                id: 'expect_column_quantile_values_to_be_between',
                name: '分位数校验',
                description: '检查列的多个分位数都在指定范围内',
                params: [
                    { name: 'quantiles', label: '分位数', type: 'text', placeholder: '0.25,0.5,0.75', required: true },
                    { name: 'ranges', label: '范围', type: 'textarea', placeholder: 'min,max\nmin,max\n...', required: true },
                ],
                autoGenerateName: (column) => `${column}_分位数校验`
            },
            {
                id: 'expect_column_unique_value_count_to_be_between',
                name: '唯一值数量校验',
                description: '检查列的唯一值数量在范围内',
                params: [
                    { name: 'min_value', label: '最小唯一值数量', type: 'integer' },
                    { name: 'max_value', label: '最大唯一值数量', type: 'integer' }
                ],
                autoGenerateName: (column) => `${column}_唯一值数量校验`
            },
            {
                id: 'expect_column_distinct_values_to_be_in_set',
                name: '唯一值集合校验',
                description: '检查所有唯一值都在指定集合中',
                params: [
                    { name: 'value_set', label: '允许的唯一值', type: 'textarea', placeholder: '每行一个值', required: true }
                ],
                autoGenerateName: (column) => `${column}_唯一值集合校验`
            },
            {
                id: 'expect_column_distinct_values_to_contain_set',
                name: '唯一值包含集合校验',
                description: '检查列包含所有指定的唯一值',
                params: [
                    { name: 'value_set', label: '必须包含的唯一值', type: 'textarea', placeholder: '每行一个值', required: true }
                ],
                autoGenerateName: (column) => `${column}_唯一值包含校验`
            },
            {
                id: 'expect_column_distinct_values_to_equal_set',
                name: '唯一值等于集合校验',
                description: '检查列的唯一值正好等于指定集合',
                params: [
                    { name: 'value_set', label: '期望的唯一值集合', type: 'textarea', placeholder: '每行一个值', required: true }
                ],
                autoGenerateName: (column) => `${column}_唯一值等于集合校验`
            }
        ]
    },
    'table': {
        name: '表级校验',
        icon: '🗄️',
        description: '检查整个表的特征',
        expectations: [
            {
                id: 'expect_table_row_count_to_be_between',
                name: '行数范围校验',
                description: '检查表的行数在范围内',
                params: [
                    { name: 'min_value', label: '最小行数', type: 'number' },
                    { name: 'max_value', label: '最大行数', type: 'number' }
                ],
                autoGenerateName: () => `表_行数校验`
            },
            {
                id: 'expect_table_columns_to_match_ordered_list',
                name: '列顺序校验',
                description: '检查表的列顺序符合预期',
                params: [
                    { name: 'column_list', label: '期望的列顺序', type: 'textarea', placeholder: '每行一个列名', required: true }
                ],
                autoGenerateName: () => `表_列顺序校验`
            },
            {
                id: 'expect_table_column_count_to_be_between',
                name: '列数量校验',
                description: '检查表的列数量在范围内',
                params: [
                    { name: 'min_value', label: '最小列数', type: 'number' },
                    { name: 'max_value', label: '最大列数', type: 'number' }
                ],
                autoGenerateName: () => `表_列数量校验`
            },
            {
                id: 'expect_table_columns_to_match_set',
                name: '列集合校验',
                description: '检查表的列集合符合预期',
                params: [
                    { name: 'column_set', label: '期望的列集合', type: 'textarea', placeholder: '每行一个列名', required: true },
                    { name: 'exact_match', label: '精确匹配', type: 'select', options: ['true', 'false'], default: 'true' }
                ],
                autoGenerateName: () => `表_列集合校验`
            }
        ]
    },
    'column_pairs': {
        name: '列对校验',
        icon: '🔗',
        description: '检查多列之间的关系',
        expectations: [
            {
                id: 'expect_column_pair_values_A_to_be_greater_than_B',
                name: 'A大于B校验',
                description: '检查A列值大于B列值',
                params: [
                    { name: 'column_B', label: '对比列(B)', type: 'select', required: true },
                    { name: 'mostly', label: '最小通过率', type: 'number', default: 1.0, min: 0, max: 1, step: 0.01 }
                ],
                autoGenerateName: (column, params) => `${column}>${params.column_B}_校验`
            },
            {
                id: 'expect_column_pair_values_to_be_equal',
                name: '两列相等校验',
                description: '检查两列值相等',
                params: [
                    { name: 'column_B', label: '对比列(B)', type: 'select', required: true },
                    { name: 'mostly', label: '最小通过率', type: 'number', default: 1.0, min: 0, max: 1, step: 0.01 }
                ],
                autoGenerateName: (column, params) => `${column}=${params.column_B}_校验`
            },
            {
                id: 'expect_column_pair_values_to_be_between',
                name: '差值范围校验',
                description: '检查A列减B列的差值在范围内',
                params: [
                    { name: 'column_B', label: '对比列(B)', type: 'select', required: true },
                    { name: 'min_value', label: '最小差值', type: 'number', required: true },
                    { name: 'max_value', label: '最大差值', type: 'number', required: true },
                    { name: 'mostly', label: '最小通过率', type: 'number', default: 1.0, min: 0, max: 1, step: 0.01 }
                ],
                autoGenerateName: (column, params) => `${column}-${params.column_B}_差值校验`
            },
            {
                id: 'expect_column_pair_values_to_not_be_null',
                name: '配对非空校验',
                description: '检查两列配对不为空',
                params: [
                    { name: 'column_B', label: '对比列(B)', type: 'select', required: true },
                    { name: 'mostly', label: '最小通过率', type: 'number', default: 1.0, min: 0, max: 1, step: 0.01 }
                ],
                autoGenerateName: (column, params) => `${column},${params.column_B}_配对非空`
            }
        ]
    },
    'multicolumn': {
        name: '多列联合校验',
        icon: '🧩',
        description: '检查多列组合的特征',
        expectations: [
            {
                id: 'expect_multicolumn_sum_to_equal',
                name: '多列和校验',
                description: '检查多列的和等于预期值',
                params: [
                    { name: 'columns_list', label: '参与计算的列', type: 'multiselect', required: true },
                    { name: 'sum_total', label: '期望的总和', type: 'number', required: true }
                ],
                autoGenerateName: () => `多列_总和校验`
            },
            {
                id: 'expect_multicolumn_values_to_be_unique',
                name: '多列组合唯一性校验',
                description: '检查多列组合没有重复',
                params: [
                    { name: 'columns_list', label: '参与组合的列', type: 'multiselect', required: true }
                ],
                autoGenerateName: () => `多列_组合唯一性校验`
            }
        ]
    },
    'datetime': {
        name: '日期时间校验',
        icon: '📅',
        description: '检查日期时间相关特征',
        expectations: [
            {
                id: 'expect_column_values_to_be_dateutil_parseable',
                name: '日期可解析性校验',
                description: '检查列值可以被 dateutil 解析为有效日期',
                params: [
                    { name: 'mostly', label: '最小通过率', type: 'number', default: 1.0, min: 0, max: 1, step: 0.01 }
                ],
                autoGenerateName: (column) => `${column}_日期可解析校验`
            },
            {
                id: 'expect_column_values_to_match_strftime_format',
                name: '日期格式匹配校验',
                description: '检查列值符合指定的 strftime 日期格式',
                params: [
                    { name: 'strftime_format', label: '日期格式(strftime)', type: 'text', placeholder: '例如: %Y-%m-%d, %Y/%m/%d %H:%M:%S', required: true },
                    { name: 'mostly', label: '最小通过率', type: 'number', default: 1.0, min: 0, max: 1, step: 0.01 }
                ],
                autoGenerateName: (column) => `${column}_日期格式校验`
            },
            {
                id: 'expect_column_values_to_be_increasing',
                name: '日期递增校验',
                description: '检查日期列值是逐行递增的',
                params: [
                    { name: 'strictly', label: '严格递增', type: 'select', options: ['true', 'false'], default: 'false' },
                    { name: 'mostly', label: '最小通过率', type: 'number', default: 1.0, min: 0, max: 1, step: 0.01 }
                ],
                autoGenerateName: (column) => `${column}_日期递增校验`
            },
            {
                id: 'expect_column_values_to_be_decreasing',
                name: '日期递减校验',
                description: '检查日期列值是逐行递减的',
                params: [
                    { name: 'strictly', label: '严格递减', type: 'select', options: ['true', 'false'], default: 'false' },
                    { name: 'mostly', label: '最小通过率', type: 'number', default: 1.0, min: 0, max: 1, step: 0.01 }
                ],
                autoGenerateName: (column) => `${column}_日期递减校验`
            },
            {
                id: 'expect_column_values_to_be_between',
                name: '日期范围校验（逐行）⭐',
                description: '检查每一行的日期值是否在指定范围内（推荐用于发现异常数据）',
                params: [
                    { name: 'min_value', label: '最小日期', type: 'text', placeholder: 'YYYY-MM-DD' },
                    { name: 'max_value', label: '最大日期', type: 'text', placeholder: 'YYYY-MM-DD' },
                    { name: 'mostly', label: '最小通过率', type: 'number', default: 1.0, min: 0, max: 1, step: 0.01 }
                ],
                autoGenerateName: (column) => `${column}_日期范围校验`
            },
            {
                id: 'expect_column_min_to_be_between',
                name: '最小日期范围校验（整列聚合）',
                description: '检查整列日期的最小值是否在范围内（仅检查1个聚合值）',
                params: [
                    { name: 'min_value', label: '最小值下限', type: 'text', placeholder: 'YYYY-MM-DD' },
                    { name: 'max_value', label: '最小值上限', type: 'text', placeholder: 'YYYY-MM-DD' }
                ],
                autoGenerateName: (column) => `${column}_最小日期校验`
            },
            {
                id: 'expect_column_max_to_be_between',
                name: '最大日期范围校验（整列聚合）',
                description: '检查整列日期的最大值是否在范围内（仅检查1个聚合值）',
                params: [
                    { name: 'min_value', label: '最大值下限', type: 'text', placeholder: 'YYYY-MM-DD' },
                    { name: 'max_value', label: '最大值上限', type: 'text', placeholder: 'YYYY-MM-DD' }
                ],
                autoGenerateName: (column) => `${column}_最大日期校验`
            }
        ]
    },
    'json': {
        name: 'JSON校验',
        icon: '🔍',
        description: '检查JSON数据相关特征',
        expectations: [
            {
                id: 'expect_json_values_to_have_keys',
                name: 'JSON包含指定键',
                description: '检查JSON对象包含所有指定的键',
                params: [
                    { name: 'expected_keys', label: '期望的键', type: 'textarea', placeholder: '每行一个键名', required: true }
                ],
                autoGenerateName: (column) => `${column}_包含键校验`
            },
            {
                id: 'expect_json_schema_to_match',
                name: 'JSON Schema校验',
                description: '检查JSON符合指定的Schema',
                params: [
                    { name: 'json_schema', label: 'JSON Schema', type: 'textarea', placeholder: '{...}', required: true }
                ],
                autoGenerateName: (column) => `${column}_Schema校验`
            }
        ]
    }
};

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    // 从 URL获取资产ID
    const urlParams = new URLSearchParams(window.location.search);
    assetId = urlParams.get('asset_id');
    
    // 加载期望分类列表
    loadExpectationCategories();
    
    // 如果有asset_id，直接加载资产信息和字段
    if (assetId) {
        loadAssetInfo(assetId);
        loadAssetColumns(assetId);
    } else {
        // 否则显示资产选择器
        document.getElementById('asset-selector-section').style.display = 'block';
        loadAssetsForSelection();
    }
});

/**
 * 加载GE Expectations分类列表（二级菜单）
 */
function loadExpectationCategories() {
    const templateList = document.getElementById('template-list');
    let html = '';
    
    Object.keys(GE_EXPECTATIONS).forEach(categoryKey => {
        const category = GE_EXPECTATIONS[categoryKey];
        html += `
            <div class="category-item">
                <div class="category-header" onclick="toggleCategory('${categoryKey}')">
                    <span class="category-icon">${category.icon}</span>
                    <span class="category-name">${category.name}</span>
                    <span class="category-arrow">▼</span>
                </div>
                <div class="expectation-list" id="category-${categoryKey}" style="display: none;">
                    ${category.expectations.map(exp => `
                        <div class="expectation-item" data-expectation-id="${exp.id}" onclick="selectExpectation('${categoryKey}', '${exp.id}')">
                            <div class="expectation-name">${exp.name}</div>
                            <div class="expectation-desc">${exp.description}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    });
    
    templateList.innerHTML = html;
}

/**
 * 切换分类展开/收起
 */
function toggleCategory(categoryKey) {
    const list = document.getElementById(`category-${categoryKey}`);
    const isHidden = list.style.display === 'none';
    
    // 关闭所有其他分类
    document.querySelectorAll('.expectation-list').forEach(el => {
        el.style.display = 'none';
    });
    
    // 切换当前分类
    list.style.display = isHidden ? 'block' : 'none';
}

/**
 * 选择Expectation
 */
async function selectExpectation(categoryKey, expectationId) {
    // 更新选中状态
    document.querySelectorAll('.expectation-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    const selectedItem = document.querySelector(`[data-expectation-id="${expectationId}"]`);
    if (selectedItem) {
        selectedItem.classList.add('selected');
    }
    
    // 保存选中的expectation
    selectedExpectation = GE_EXPECTATIONS[categoryKey].expectations.find(e => e.id === expectationId);
    
    // 更新配置标题
    const category = GE_EXPECTATIONS[categoryKey];
    document.getElementById('config-title').textContent = `${category.icon} ${selectedExpectation.name}`;
    document.getElementById('config-subtitle').textContent = selectedExpectation.description;
    
    // 如果已选择资产，自动生成规则名称
    if (assetId && availableColumns.length > 0) {
        generateRuleName();
    }
    
    // 判断是否需要字段选择
    // column_values、column_aggregates分类下的所有expectations都需要字段
    // column_pairs需要主字段和对比列
    // table和multicolumn不需要单独选择字段（通过参数配置）
    const needsColumn = ['column_values', 'column_aggregates', 'column_pairs', 'datetime'].includes(categoryKey);
    const needsColumnB = selectedExpectation.params.some(p => p.name === 'column_B');
    
    // 显示/隐藏字段选择区域
    document.getElementById('field-selection-section').style.display = needsColumn ? 'block' : 'none';
    
    // 显示/隐藏对比列选择区域
    document.getElementById('column-b-section').style.display = needsColumnB ? 'block' : 'none';
    
    // 渲染参数表单
    renderExpectationParams();
    
    // 启用创建按钮
    updateCreateButtonState();
}

/**
 * 加载资产列表供选择
 */
async function loadAssetsForSelection() {
    try {
        const response = await apiRequest(`${API_BASE_URL}/assets?page=1&per_page=100`);
        const assets = Array.isArray(response.data) ? response.data : (response.data.assets || []);
        
        const selector = document.getElementById('asset-selector');
        assets.forEach(asset => {
            const option = document.createElement('option');
            option.value = asset.id;
            option.textContent = `${asset.name} (${asset.asset_type})`;
            selector.appendChild(option);
        });
        
    } catch (error) {
        console.error('加载资产列表失败:', error);
        showError('加载资产列表失败');
    }
}

/**
 * 资产选择变化
 */
async function onAssetChange() {
    const selector = document.getElementById('asset-selector');
    assetId = selector.value;
    
    if (assetId) {
        await loadAssetInfo(assetId);
        await loadAssetColumns(assetId);
    } else {
        // 清空字段选择
        availableColumns = [];
        selectedFields = [];
        document.getElementById('field-selector').innerHTML = '';
        updateConfigUI();
    }
}

/**
 * 加载资产信息
 */
async function loadAssetInfo(assetId) {
    try {
        const response = await apiRequest(`${API_BASE_URL}/assets/${assetId}`);
        const asset = response.data;
        
        // 更新标题
        document.getElementById('config-title').textContent = `为 "${asset.name}" 配置规则`;
        document.getElementById('config-subtitle').textContent = `资产类型: ${asset.asset_type} | 数据源: ${asset.data_source}`;
        
    } catch (error) {
        console.error('加载资产信息失败:', error);
    }
}

/**
 * 加载资产字段列表
 */
async function loadAssetColumns(assetId) {
    try {
        const response = await apiRequest(`${API_BASE_URL}/assets/${assetId}/columns`);
        availableColumns = response.data.columns || [];
        
        renderFieldSelector();
        
    } catch (error) {
        console.error('加载字段列表失败:', error);
        showError('加载字段列表失败: ' + error.message);
    }
}

/**
 * 渲染字段选择器
 */
function renderFieldSelector() {
    const container = document.getElementById('field-selector');
    
    if (availableColumns.length === 0) {
        container.innerHTML = '<div style="color: #999; text-align: center; padding: 2rem;">暂无可用字段</div>';
        return;
    }
    
    container.innerHTML = availableColumns.map(col => `
        <label class="field-checkbox">
            <input type="checkbox" 
                   value="${col.name}" 
                   onchange="onFieldChange('${col.name}', this.checked)"
                   ${selectedFields.includes(col.name) ? 'checked' : ''}>
            <span>${col.name}</span>
            <span class="field-type">${col.type || 'string'}</span>
        </label>
    `).join('');
    
    // 同时更新对比列选择器
    updateColumnBSelector();
}

/**
 * 更新对比列选择器
 */
function updateColumnBSelector() {
    const selector = document.getElementById('param-column_B');
    if (!selector) return;
    
    // 保存当前选中值
    const currentValue = selector.value;
    
    // 清空并重新填充
    selector.innerHTML = '<option value="">-- 请选择对比列 --</option>';
    availableColumns.forEach(col => {
        const option = document.createElement('option');
        option.value = col.name;
        option.textContent = `${col.name} (${col.type || 'string'})`;
        selector.appendChild(option);
    });
    
    // 恢复选中值
    if (currentValue) {
        selector.value = currentValue;
    }
    
    // 添加变化监听器，重新生成规则名称
    selector.onchange = function() {
        generateRuleName();
        updateCreateButtonState();
    };
}

/**
 * 字段选择变化
 */
function onFieldChange(fieldName, checked) {
    if (checked) {
        if (!selectedFields.includes(fieldName)) {
            selectedFields.push(fieldName);
        }
    } else {
        selectedFields = selectedFields.filter(f => f !== fieldName);
    }
    
    // 自动生成规则名称
    generateRuleName();
    updateCreateButtonState();
}

/**
 * 自动生成规则名称
 */
function generateRuleName() {
    if (!selectedExpectation || !assetId) return;
    
    // 如果已手动输入，不覆盖
    const nameInput = document.getElementById('rule-name');
    if (nameInput.value && nameInput.dataset.manual === 'true') return;
    
    let generatedName = '';
    
    // 判断分类
    const categoryKey = Object.keys(GE_EXPECTATIONS).find(key => 
        GE_EXPECTATIONS[key].expectations.some(e => e.id === selectedExpectation.id)
    );
    
    if (['column_values', 'column_aggregates'].includes(categoryKey)) {
        // 列级校验：需要字段
        if (selectedFields.length > 0) {
            generatedName = selectedExpectation.autoGenerateName(selectedFields[0]);
        } else {
            generatedName = selectedExpectation.autoGenerateName('[未选择字段]');
        }
    } else if (categoryKey === 'column_pairs') {
        // 列对校验：需要主字段和对比列
        const columnB = document.getElementById('param-column_B')?.value;
        if (selectedFields.length > 0 && columnB) {
            generatedName = selectedExpectation.autoGenerateName(selectedFields[0], { column_B: columnB });
        } else if (selectedFields.length > 0) {
            generatedName = selectedExpectation.autoGenerateName(selectedFields[0], { column_B: '[未选择]' });
        } else {
            generatedName = selectedExpectation.autoGenerateName('[未选择字段]', { column_B: '[未选择]' });
        }
    } else {
        // 表级或多列校验
        generatedName = selectedExpectation.autoGenerateName();
    }
    
    nameInput.value = generatedName;
    nameInput.dataset.manual = 'false';
}

/**
 * 监听规则名称手动输入
 */
document.addEventListener('DOMContentLoaded', function() {
    const nameInput = document.getElementById('rule-name');
    nameInput.addEventListener('input', function() {
        this.dataset.manual = 'true';
        updateCreateButtonState();
    });
});

/**
 * 渲染Expectation参数表单
 */
function renderExpectationParams() {
    const container = document.getElementById('other-params');
    const section = document.getElementById('other-params-section');
    
    if (!selectedExpectation || selectedExpectation.params.length === 0) {
        section.style.display = 'none';
        return;
    }
    
    // 过滤掉已经单独处理的参数
    const paramsToShow = selectedExpectation.params.filter(p => 
        p.name !== 'column_name' && p.name !== 'column_B'
    );
    
    if (paramsToShow.length === 0) {
        section.style.display = 'none';
        return;
    }
    
    section.style.display = 'block';
    
    container.innerHTML = paramsToShow.map(param => {
        
        let inputHtml = '';
        
        if (param.type === 'select') {
            // 下拉选择框
            inputHtml = `
                <select id="param-${param.name}" class="form-input" onchange="updateCreateButtonState()">
                    ${param.options.map(opt => `
                        <option value="${opt}" ${param.default === opt ? 'selected' : ''}>${opt}</option>
                    `).join('')}
                </select>
            `;
        } else if (param.type === 'multiselect') {
            // 多选字段
            inputHtml = `
                <div class="field-selector" style="max-height: 200px;">
                    ${availableColumns.map(col => `
                        <label class="field-checkbox">
                            <input type="checkbox" 
                                   name="param-${param.name}" 
                                   value="${col.name}"
                                   onchange="updateCreateButtonState()">
                            <span>${col.name}</span>
                        </label>
                    `).join('')}
                </div>
            `;
        } else if (param.type === 'textarea') {
            inputHtml = `
                <textarea id="param-${param.name}" class="form-textarea" rows="3" 
                    ${param.required ? 'required' : ''}
                    placeholder="${param.placeholder || ''}" 
                    onchange="updateCreateButtonState()">${param.default || ''}</textarea>
            `;
        } else {
            inputHtml = `
                <input type="${param.type}" id="param-${param.name}" class="form-input" 
                    ${param.required ? 'required' : ''}
                    ${param.min !== undefined ? `min="${param.min}"` : ''}
                    ${param.max !== undefined ? `max="${param.max}"` : ''}
                    ${param.step ? `step="${param.step}"` : ''}
                    placeholder="${param.placeholder || ''}" 
                    value="${param.default || ''}"
                    onchange="updateCreateButtonState()">
            `;
        }
        
        return `
            <div class="form-group">
                <label class="form-label">
                    ${param.label} ${param.required ? '<span class="required">*</span>' : ''}
                </label>
                ${inputHtml}
            </div>
        `;
    }).join('');
}

/**
 * 更新创建按钮状态
 */
function updateCreateButtonState() {
    const btn = document.getElementById('create-btn');
    
    if (!selectedExpectation) {
        btn.disabled = true;
        return;
    }
    
    const hasAsset = assetId !== null;
    const hasName = document.getElementById('rule-name').value.trim().length > 0;
    
    // 判断是否需要字段（根据分类）
    const categoryKey = Object.keys(GE_EXPECTATIONS).find(key => 
        GE_EXPECTATIONS[key].expectations.some(e => e.id === selectedExpectation.id)
    );
    
    const needsColumn = ['column_values', 'column_aggregates', 'column_pairs', 'datetime'].includes(categoryKey);
    const hasColumn = !needsColumn || selectedFields.length > 0;
    
    // 检查是否需要对比列
    const needsColumnB = selectedExpectation.params.some(p => p.name === 'column_B');
    const hasColumnB = !needsColumnB || document.getElementById('param-column_B')?.value;
    
    btn.disabled = !(hasAsset && hasName && hasColumn && hasColumnB);
}

/**
 * 创建规则
 */
async function createRule() {
    const ruleName = document.getElementById('rule-name').value.trim();
    const strength = document.querySelector('input[name="strength"]:checked').value;
    const description = document.getElementById('rule-description').value.trim();
    
    if (!selectedExpectation || !assetId || !ruleName) {
        showWarning('请填写完整信息');
        return;
    }
    
    // 收集参数
    const parameters = {};
    
    // 添加字段名（如果需要）
    if (selectedFields.length > 0) {
        parameters.column_name = selectedFields[0]; // 暂时只支持单字段
    }
    
    // 收集其他参数
    selectedExpectation.params.forEach(param => {
        if (param.name === 'column_name' || param.name === 'column_B') return;
        
        if (param.type === 'multiselect') {
            // 多选字段
            const checkboxes = document.querySelectorAll(`input[name="param-${param.name}"]:checked`);
            if (checkboxes.length > 0) {
                parameters[param.name] = Array.from(checkboxes).map(cb => cb.value);
            }
        } else if (param.type === 'select') {
            // 下拉选择
            const select = document.getElementById(`param-${param.name}`);
            if (select && select.value) {
                parameters[param.name] = select.value;
            }
        } else {
            // 普通输入框
            const input = document.getElementById(`param-${param.name}`);
            if (input && input.value) {
                // 数字类型转换
                if (param.type === 'number') {
                    parameters[param.name] = parseFloat(input.value);
                } else {
                    parameters[param.name] = input.value;
                }
            }
        }
    });
    
    // 处理列对校验的特殊情况
    if (selectedExpectation.params.some(p => p.name === 'column_B')) {
        const columnBSelect = document.getElementById('param-column_B');
        if (columnBSelect && columnBSelect.value) {
            parameters.column_B = columnBSelect.value;
        }
    }
    
    // 显示加载状态
    document.getElementById('loading-overlay').classList.add('show');
    
    try {
        const data = {
            name: ruleName,
            rule_type: selectedExpectation.id.split('_')[2] || 'custom', // 从expectation ID提取类型
            rule_template: selectedExpectation.id,
            ge_expectation: selectedExpectation.id,
            strength: strength,
            description: description,
            parameters: JSON.stringify(parameters)
        };
        
        // 如果有字段，添加到顶层
        if (parameters.column_name) {
            data.column_name = parameters.column_name;
        }
        
        await apiRequest(`${API_BASE_URL}/assets/${assetId}/rules`, 'POST', data);
        
        document.getElementById('loading-overlay').classList.remove('show');
        showSuccess(`规则创建成功！`);
        
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
 * 取消配置
 */
function cancelConfig() {
    if (confirm('确定要取消规则配置吗？未保存的更改将会丢失。')) {
        if (assetId) {
            window.location.href = `/assets/${assetId}`;
        } else {
            window.location.href = '/assets';
        }
    }
}

/**
 * 更新配置UI
 */
function updateConfigUI() {
    updateSQLPreview();
    updateCreateButton();
}

