# DataQ API PowerShell 测试脚本
# 使用方法: .\tests\scripts\test_api.ps1

$baseUrl = "http://localhost:5000/api/v1"

Write-Host "=" -NoNewline
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "DataQ API PowerShell 测试" -ForegroundColor Cyan
Write-Host "=" -NoNewline
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host ""

# 设置 UTF-8 编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

try {
    # 1. 获取统计概览
    Write-Host "[测试 1] 获取统计概览..." -ForegroundColor Yellow
    $result = Invoke-RestMethod -Uri "$baseUrl/statistics/overview" -Method GET
    Write-Host "  状态: $($result.status)" -ForegroundColor Green
    Write-Host "  资产数: $($result.data.assets.total)" -ForegroundColor Green
    Write-Host "  规则数: $($result.data.rules.total)" -ForegroundColor Green
    Write-Host ""

    # 2. 创建资产
    Write-Host "[测试 2] 创建资产..." -ForegroundColor Yellow
    $assetBody = @{
        name = "PowerShell测试资产"
        data_source = "test_ps.csv"
        asset_type = "csv"
        owner = "测试用户"
        quality_score_weight = 8.0
        description = "通过PowerShell创建的测试资产"
    } | ConvertTo-Json
    
    $result = Invoke-RestMethod -Uri "$baseUrl/assets" -Method POST -Body $assetBody -ContentType "application/json; charset=utf-8"
    Write-Host "  状态: $($result.status)" -ForegroundColor Green
    Write-Host "  资产ID: $($result.data.id)" -ForegroundColor Green
    Write-Host "  资产名称: $($result.data.name)" -ForegroundColor Green
    $assetId = $result.data.id
    Write-Host ""

    # 3. 获取资产列表
    Write-Host "[测试 3] 获取资产列表..." -ForegroundColor Yellow
    $result = Invoke-RestMethod -Uri "$baseUrl/assets" -Method GET
    Write-Host "  状态: $($result.status)" -ForegroundColor Green
    Write-Host "  资产数量: $($result.data.Count)" -ForegroundColor Green
    foreach ($asset in $result.data) {
        Write-Host "    - ID:$($asset.id) 名称:$($asset.name)" -ForegroundColor Gray
    }
    Write-Host ""

    # 4. 获取单个资产
    Write-Host "[测试 4] 获取单个资产 (ID=$assetId)..." -ForegroundColor Yellow
    $result = Invoke-RestMethod -Uri "$baseUrl/assets/$assetId" -Method GET
    Write-Host "  状态: $($result.status)" -ForegroundColor Green
    Write-Host "  资产名称: $($result.data.name)" -ForegroundColor Green
    Write-Host "  负责人: $($result.data.owner)" -ForegroundColor Green
    Write-Host ""

    # 5. 创建规则
    Write-Host "[测试 5] 创建规则..." -ForegroundColor Yellow
    $ruleBody = @{
        name = "邮箱唯一性校验"
        rule_type = "uniqueness"
        rule_template = "字段唯一性校验"
        ge_expectation = "ExpectColumnValuesToBeUnique"
        column_name = "email"
        strength = "strong"
        description = "确保邮箱地址唯一"
    } | ConvertTo-Json
    
    $result = Invoke-RestMethod -Uri "$baseUrl/assets/$assetId/rules" -Method POST -Body $ruleBody -ContentType "application/json; charset=utf-8"
    Write-Host "  状态: $($result.status)" -ForegroundColor Green
    Write-Host "  规则ID: $($result.data.id)" -ForegroundColor Green
    Write-Host "  规则名称: $($result.data.name)" -ForegroundColor Green
    Write-Host "  强度: $($result.data.strength)" -ForegroundColor Green
    $ruleId = $result.data.id
    Write-Host ""

    # 6. 获取规则列表
    Write-Host "[测试 6] 获取规则列表..." -ForegroundColor Yellow
    $result = Invoke-RestMethod -Uri "$baseUrl/assets/$assetId/rules" -Method GET
    Write-Host "  状态: $($result.status)" -ForegroundColor Green
    Write-Host "  规则数量: $($result.count)" -ForegroundColor Green
    foreach ($rule in $result.data) {
        Write-Host "    - ID:$($rule.id) 名称:$($rule.name) 强度:$($rule.strength)" -ForegroundColor Gray
    }
    Write-Host ""

    # 7. 更新规则
    Write-Host "[测试 7] 更新规则 (改为弱规则)..." -ForegroundColor Yellow
    $updateBody = @{
        strength = "weak"
        description = "更新为弱规则"
    } | ConvertTo-Json
    
    $result = Invoke-RestMethod -Uri "$baseUrl/rules/$ruleId" -Method PUT -Body $updateBody -ContentType "application/json; charset=utf-8"
    Write-Host "  状态: $($result.status)" -ForegroundColor Green
    Write-Host "  规则ID: $($result.data.id)" -ForegroundColor Green
    Write-Host ""

    # 8. 获取问题列表
    Write-Host "[测试 8] 获取问题列表..." -ForegroundColor Yellow
    $result = Invoke-RestMethod -Uri "$baseUrl/issues" -Method GET
    Write-Host "  状态: $($result.status)" -ForegroundColor Green
    Write-Host "  问题数量: $($result.data.Count)" -ForegroundColor Green
    Write-Host ""

    # 9. 获取校验历史
    Write-Host "[测试 9] 获取校验历史..." -ForegroundColor Yellow
    $result = Invoke-RestMethod -Uri "$baseUrl/validations/history" -Method GET
    Write-Host "  状态: $($result.status)" -ForegroundColor Green
    Write-Host "  历史记录数: $($result.data.Count)" -ForegroundColor Green
    Write-Host ""

    # 10. 删除资产（清理测试数据）
    Write-Host "[测试 10] 删除测试资产..." -ForegroundColor Yellow
    $result = Invoke-RestMethod -Uri "$baseUrl/assets/$assetId" -Method DELETE
    Write-Host "  状态: $($result.status)" -ForegroundColor Green
    Write-Host "  消息: $($result.message)" -ForegroundColor Green
    Write-Host ""

    # 最终统计
    Write-Host "[最终统计] 查看清理后的统计数据..." -ForegroundColor Yellow
    $result = Invoke-RestMethod -Uri "$baseUrl/statistics/overview" -Method GET
    Write-Host "  资产数: $($result.data.assets.total)" -ForegroundColor Green
    Write-Host "  规则数: $($result.data.rules.total)" -ForegroundColor Green
    Write-Host ""

    Write-Host "=" -NoNewline
    Write-Host ("=" * 79) -ForegroundColor Cyan
    Write-Host "所有测试完成！✅" -ForegroundColor Green
    Write-Host "=" -NoNewline
    Write-Host ("=" * 79) -ForegroundColor Cyan

} catch {
    Write-Host ""
    Write-Host "❌ 错误: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "详细信息:" -ForegroundColor Red
    Write-Host $_.Exception.Response.StatusCode -ForegroundColor Red
    if ($_.ErrorDetails) {
        Write-Host $_.ErrorDetails.Message -ForegroundColor Red
    }
}
