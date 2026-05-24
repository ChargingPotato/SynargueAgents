# Synargue 一键启动脚本
# 三个服务：Worker / FastAPI / Vite Dev Server
# Ctrl+C 停止全部

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Synargue 一键启动" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$bgJobs = @()
$cleanupDone = $false

function Cleanup {
    if ($cleanupDone) { return }
    $cleanupDone = $true
    Write-Host "`n正在停止所有服务..." -ForegroundColor Yellow
    foreach ($job in $bgJobs) {
        if ($job -and $job.HasExited -eq $false) {
            Stop-Process -Id $job.Id -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Host "所有服务已停止" -ForegroundColor Green
}

$null = [Console]::TreatControlCAsInput
try {
    [Console]::CancelKeyPress += { Cleanup; exit 0 }
} catch {
}

# ---- Worker ----
Write-Host "`n[1/3] 启动 Worker..." -ForegroundColor Yellow
$workerJob = Start-Process -FilePath "uv" `
    -ArgumentList "run","python","-m","backend.worker" `
    -WorkingDirectory $root `
    -NoNewWindow `
    -PassThru
$bgJobs += $workerJob
Write-Host "  Worker PID: $($workerJob.Id)" -ForegroundColor DarkGray

# ---- FastAPI ----
Write-Host "`n[2/3] 启动 FastAPI (端口 8000)..." -ForegroundColor Yellow
$apiJob = Start-Process -FilePath "uv" `
    -ArgumentList "run","uvicorn","backend.main:app","--host","0.0.0.0","--port","8000" `
    -WorkingDirectory $root `
    -NoNewWindow `
    -PassThru
$bgJobs += $apiJob
Write-Host "  FastAPI PID: $($apiJob.Id)" -ForegroundColor DarkGray

# ---- Frontend Dev Server ----
Write-Host "`n[3/3] 启动 Vite Dev Server..." -ForegroundColor Yellow
Write-Host "  前端地址: http://localhost:5173" -ForegroundColor Green
Write-Host "  API 地址: http://localhost:8000" -ForegroundColor Green
Write-Host "`n按 Ctrl+C 停止所有服务`n" -ForegroundColor DarkGray

$frontendDir = Join-Path $root "frontend"
Push-Location $frontendDir
try {
    npm run dev
} finally {
    Pop-Location
    Cleanup
}
