Write-Host "🔍 Testing Ollama Connection..." -ForegroundColor Cyan
Write-Host "="*50 -ForegroundColor Cyan

# Test 1: Check if Ollama process is running
Write-Host "1. Checking Ollama process..." -ForegroundColor Yellow
$ollamaProcess = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
if ($ollamaProcess) {
    Write-Host "   ✅ Ollama process is running (PID: $($ollamaProcess.Id))" -ForegroundColor Green
} else {
    Write-Host "   ❌ Ollama is NOT running" -ForegroundColor Red
    Write-Host "   💡 Start Ollama in a new window: ollama serve" -ForegroundColor Yellow
}

# Test 2: Check Ollama API
Write-Host "2. Testing Ollama API..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 5
    Write-Host "   ✅ Ollama API is responding" -ForegroundColor Green
    Write-Host "   📦 Models available:" -ForegroundColor Gray
    foreach ($model in $response.models) {
        Write-Host "     • $($model.name) ($([math]::Round($model.size/1GB, 2)) GB)" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ❌ Ollama API not responding: $_" -ForegroundColor Red
}

# Test 3: Check if deepseek-coder is available
Write-Host "3. Checking for deepseek-coder model..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 5
    $models = $response.models | Where-Object { $_.name -eq "deepseek-coder:6.7b" }
    if ($models) {
        Write-Host "   ✅ deepseek-coder:6.7b is available" -ForegroundColor Green
    } else {
        Write-Host "   ❌ deepseek-coder:6.7b is NOT available" -ForegroundColor Red
        Write-Host "   💡 Pull the model: ollama pull deepseek-coder:6.7b" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Could not check models" -ForegroundColor Red
}

# Test 4: Test Ollama generate endpoint
Write-Host "4. Testing Ollama generate endpoint..." -ForegroundColor Yellow
try {
    $body = @{
        model = "deepseek-coder:6.7b"
        prompt = "Write hello world in Python"
        stream = $false
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/generate" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 10
    Write-Host "   ✅ Ollama generate is working!" -ForegroundColor Green
    Write-Host "   📝 Response: $($response.response.Substring(0, [Math]::Min(100, $response.response.Length)))..." -ForegroundColor Gray
} catch {
    Write-Host "   ❌ Ollama generate failed: $_" -ForegroundColor Red
}

Write-Host "`n" + "="*50 -ForegroundColor Cyan
Write-Host "📋 SUMMARY" -ForegroundColor Cyan
Write-Host "="*50 -ForegroundColor Cyan

if ($ollamaProcess) {
    Write-Host "✅ Ollama is running" -ForegroundColor Green
} else {
    Write-Host "❌ Ollama is NOT running - START IT:" -ForegroundColor Red
    Write-Host "   Open a NEW PowerShell window and run:" -ForegroundColor Yellow
    Write-Host "   cd D:\ollama" -ForegroundColor White
    Write-Host "   ollama serve" -ForegroundColor White
}