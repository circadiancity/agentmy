# Tau2-Bench Clinical Evaluation - Quick Test Script
# 快速测试脚本 - 验证环境和配置

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Tau2-Bench Clinical Evaluation Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Python 环境
Write-Host "[1/5] Checking Python environment..." -ForegroundColor White
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Python not found" -ForegroundColor Red
    exit 1
}

# 检查虚拟环境
Write-Host "[2/5] Checking virtual environment..." -ForegroundColor White
if (Test-Path ".venv\Scripts\activate.ps1") {
    Write-Host "  Virtual environment: Found" -ForegroundColor Green
} else {
    Write-Host "  [WARNING] Virtual environment not found" -ForegroundColor Yellow
    Write-Host "  Run: python -m venv .venv" -ForegroundColor Yellow
}

# 检查依赖
Write-Host "[3/5] Checking dependencies..." -ForegroundColor White
try {
    $imports = python -c "import sys; sys.path.insert(0, 'src'); from tau2.registry import registry; print('OK')" 2>&1
    if ($imports -match "OK") {
        Write-Host "  Tau2 dependencies: OK" -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] Tau2 dependencies not installed" -ForegroundColor Red
    }
} catch {
    Write-Host "  [ERROR] Tau2 dependencies not installed" -ForegroundColor Red
    Write-Host "  Run: pip install -e ." -ForegroundColor Yellow
}

# 检查数据
Write-Host "[4/5] Checking clinical data..." -ForegroundColor White
$dataExists = Test-Path "data\tau2\domains\clinical"
if ($dataExists) {
    Write-Host "  Clinical data: Found" -ForegroundColor Green

    # 统计任务数
    $taskCount = python -c "import sys, json; sys.path.insert(0, 'src'); from pathlib import Path; data_dir = Path('data/tau2/domains/clinical'); total = sum(len(json.load(open(f/'tasks.json', 'r', encoding='utf-8'))) for f in data_dir.iterdir() if f.is_dir() and (f/'tasks.json').exists()); print(total)" 2>&1
    Write-Host "  Total tasks: $taskCount" -ForegroundColor Cyan
} else {
    Write-Host "  [ERROR] Clinical data not found" -ForegroundColor Red
}

# 检查 API 密钥
Write-Host "[5/5] Checking API key configuration..." -ForegroundColor White
if (Test-Path ".env") {
    Write-Host "  .env file: Found" -ForegroundColor Green

    # 检查是否配置了密钥
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "sk-") {
        Write-Host "  API key: Configured" -ForegroundColor Green
    } else {
        Write-Host "  [WARNING] API key not configured" -ForegroundColor Yellow
        Write-Host "  Edit .env and add your API key" -ForegroundColor Yellow
    }
} else {
    Write-Host "  [WARNING] .env file not found" -ForegroundColor Yellow
    Write-Host "  Copy .env.example to .env and configure" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Test Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Configure API key in .env file" -ForegroundColor White
Write-Host "  2. Run: python run_clinical_benchmark.py --list" -ForegroundColor White
Write-Host "  3. Run: python run_clinical_benchmark.py --domain clinical_neurology --max-tasks 1" -ForegroundColor White
Write-Host ""
Write-Host "For full guide, see: CLINICAL_BENCHMARK_GUIDE.md" -ForegroundColor White
Write-Host ""
