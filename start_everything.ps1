# Start Everything Script

Write-Host "🚀 Starting LLM Platform..." -ForegroundColor Green

# 1. Check if server is already running
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 2
    Write-Host "✅ Server is already running" -ForegroundColor Green
} catch {
    Write-Host "🔄 Starting server..." -ForegroundColor Yellow
    
    # Start server in background
    $serverJob = Start-Job -ScriptBlock {
        cd "D:\ollama\local-llm-platform"
        python run.py
    }
    
    Write-Host "⏳ Waiting for server to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
}

# 2. Test the API
Write-Host "`n🧪 Testing API..." -ForegroundColor Cyan

# Health check
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
    Write-Host "✅ Health: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "❌ Server not responding" -ForegroundColor Red
    exit 1
}

# Chat test
Write-Host "`n💬 Testing chat..." -ForegroundColor Cyan
$headers = @{
    "Authorization" = "Bearer default-api-key"
    "Content-Type" = "application/json"
}
$body = @{
    message = "Hello, are you working?"
    model_name = "deepseek-coder:6.7b"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/chat" -Method Post -Headers $headers -Body $body
    Write-Host "✅ Chat successful!" -ForegroundColor Green
    Write-Host "📝 Response: $($response.message.Substring(0, [Math]::Min(100, $response.message.Length)))..." -ForegroundColor Gray
} catch {
    Write-Host "❌ Chat failed: $_" -ForegroundColor Red
}

Write-Host "`n" + "="*50 -ForegroundColor Cyan
Write-Host "🎉 LLM Platform is running!" -ForegroundColor Green
Write-Host "="*50 -ForegroundColor Cyan
Write-Host "`n📊 Access URLs:" -ForegroundColor White
Write-Host "  • API: http://localhost:8000" -ForegroundColor Gray
Write-Host "  • Docs: http://localhost:8000/docs" -ForegroundColor Gray
Write-Host "  • Health: http://localhost:8000/health" -ForegroundColor Gray
Write-Host "`n🔑 API Key: default-api-key" -ForegroundColor White
Write-Host "`n💡 Run: python chat_interface.py for interactive chat" -ForegroundColor Yellow