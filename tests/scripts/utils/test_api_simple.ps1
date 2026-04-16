# DataQ API PowerShell Test Script
# Usage: .\tests\scripts\test_api_simple.ps1

$baseUrl = "http://localhost:5000/api/v1"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DataQ API Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set UTF-8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

try {
    # Test 1: Get statistics
    Write-Host "[Test 1] Get statistics overview..." -ForegroundColor Yellow
    $result = Invoke-RestMethod -Uri "$baseUrl/statistics/overview" -Method GET
    Write-Host "  Status: $($result.status)" -ForegroundColor Green
    Write-Host "  Assets: $($result.data.assets.total)" -ForegroundColor Green
    Write-Host "  Rules: $($result.data.rules.total)" -ForegroundColor Green
    Write-Host ""

    # Test 2: Create asset
    Write-Host "[Test 2] Create asset..." -ForegroundColor Yellow
    $assetBody = @{
        name = "Test Asset PS"
        data_source = "test_ps.csv"
        asset_type = "csv"
        owner = "Test User"
        quality_score_weight = 8.0
    } | ConvertTo-Json
    
    $result = Invoke-RestMethod -Uri "$baseUrl/assets" -Method POST -Body $assetBody -ContentType "application/json; charset=utf-8"
    Write-Host "  Status: $($result.status)" -ForegroundColor Green
    Write-Host "  Asset ID: $($result.data.id)" -ForegroundColor Green
    Write-Host "  Asset Name: $($result.data.name)" -ForegroundColor Green
    $assetId = $result.data.id
    Write-Host ""

    # Test 3: Get asset list
    Write-Host "[Test 3] Get asset list..." -ForegroundColor Yellow
    $result = Invoke-RestMethod -Uri "$baseUrl/assets" -Method GET
    Write-Host "  Status: $($result.status)" -ForegroundColor Green
    Write-Host "  Asset Count: $($result.data.Count)" -ForegroundColor Green
    Write-Host ""

    # Test 4: Create rule
    Write-Host "[Test 4] Create rule..." -ForegroundColor Yellow
    $ruleBody = @{
        name = "Email Uniqueness Check"
        rule_type = "uniqueness"
        rule_template = "Field Uniqueness Check"
        ge_expectation = "ExpectColumnValuesToBeUnique"
        column_name = "email"
        strength = "strong"
    } | ConvertTo-Json
    
    $result = Invoke-RestMethod -Uri "$baseUrl/assets/$assetId/rules" -Method POST -Body $ruleBody -ContentType "application/json; charset=utf-8"
    Write-Host "  Status: $($result.status)" -ForegroundColor Green
    Write-Host "  Rule ID: $($result.data.id)" -ForegroundColor Green
    Write-Host "  Rule Name: $($result.data.name)" -ForegroundColor Green
    $ruleId = $result.data.id
    Write-Host ""

    # Test 5: Get rules
    Write-Host "[Test 5] Get rules..." -ForegroundColor Yellow
    $result = Invoke-RestMethod -Uri "$baseUrl/assets/$assetId/rules" -Method GET
    Write-Host "  Status: $($result.status)" -ForegroundColor Green
    Write-Host "  Rule Count: $($result.count)" -ForegroundColor Green
    Write-Host ""

    # Test 6: Update rule
    Write-Host "[Test 6] Update rule (change to weak)..." -ForegroundColor Yellow
    $updateBody = @{
        strength = "weak"
    } | ConvertTo-Json
    
    $result = Invoke-RestMethod -Uri "$baseUrl/rules/$ruleId" -Method PUT -Body $updateBody -ContentType "application/json; charset=utf-8"
    Write-Host "  Status: $($result.status)" -ForegroundColor Green
    Write-Host ""

    # Test 7: Delete asset (cleanup)
    Write-Host "[Test 7] Delete test asset..." -ForegroundColor Yellow
    $result = Invoke-RestMethod -Uri "$baseUrl/assets/$assetId" -Method DELETE
    Write-Host "  Status: $($result.status)" -ForegroundColor Green
    Write-Host "  Message: $($result.message)" -ForegroundColor Green
    Write-Host ""

    # Final statistics
    Write-Host "[Final] Check statistics after cleanup..." -ForegroundColor Yellow
    $result = Invoke-RestMethod -Uri "$baseUrl/statistics/overview" -Method GET
    Write-Host "  Assets: $($result.data.assets.total)" -ForegroundColor Green
    Write-Host "  Rules: $($result.data.rules.total)" -ForegroundColor Green
    Write-Host ""

    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "All tests completed successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

} catch {
    Write-Host ""
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    if ($_.ErrorDetails) {
        Write-Host "Details:" -ForegroundColor Red
        Write-Host $_.ErrorDetails.Message -ForegroundColor Red
    }
}
