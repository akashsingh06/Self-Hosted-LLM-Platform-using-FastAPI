# Test API Script for PowerShell

Write-Host "🧪 Testing LLM Platform API" -ForegroundColor Cyan
Write-Host "="*50 -ForegroundColor Cyan

# Test 1: Health Check
Write-Host "1. Testing Health Check..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
    Write-Host "   ✅ Health: $($response.status)" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Health check failed: $_" -ForegroundColor Red
    exit 1
}

# Test 2: Get Models
Write-Host "2. Testing Models Endpoint..." -ForegroundColor Yellow
try {
    $headers = @{
        "Authorization" = "Bearer default-api-key"
    }
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/models" -Method Get -Headers $headers
    Write-Host "   ✅ Models found: $($response.Count)" -ForegroundColor Green
    foreach ($model in $response[0..2]) {
        Write-Host "     • $($model.name)" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ❌ Models endpoint failed: $_" -ForegroundColor Red
}

# Test 3: Chat Test
Write-Host "3. Testing Chat Endpoint..." -ForegroundColor Yellow
try {
    $headers = @{
        "Authorization" = "Bearer default-api-key"
        "Content-Type" = "application/json"
    }
    
    $body = @{
        message = "Write a Python function to calculate factorial"
        model_name = "deepseek-coder:6.7b"
        stream = $false
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/chat" -Method Post -Headers $headers -Body $body
    Write-Host "   ✅ Chat successful!" -ForegroundColor Green
    Write-Host "   📝 Response preview: $($response.message.Substring(0, [Math]::Min(100, $response.message.Length)))..." -ForegroundColor Gray
    
    if ($response.code_blocks) {
        Write-Host "   📦 Code blocks found: $($response.code_blocks.Count)" -ForegroundColor Green
    }
    
} catch {
    Write-Host "   ❌ Chat endpoint failed: $_" -ForegroundColor Red
}

Write-Host "`n" + "="*50 -ForegroundColor Cyan
Write-Host "🎉 API Tests Complete!" -ForegroundColor Green
Write-Host "="*50 -ForegroundColor Cyan