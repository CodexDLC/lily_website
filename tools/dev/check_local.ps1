Clear-Host
$ErrorActionPreference = "Stop"
Write-Host "🚀 Starting Local Quality Check..." -ForegroundColor Cyan

# Check for pre-commit installation
Write-Host "`n⚙️ Checking for pre-commit installation..." -ForegroundColor Yellow
try {
    pre-commit --version | Out-Null
    Write-Host "✅ pre-commit is installed." -ForegroundColor Green
} catch {
    Write-Host "❌ pre-commit is not installed. Please install it: pip install pre-commit" -ForegroundColor Red
    exit 1
}

# Helper function to run pre-commit hooks
function Run-PreCommitHook {
    param (
        [string]$HookName,
        [string]$Message
    )
    Write-Host "`n🔍 $Message..." -ForegroundColor Yellow
    try {
        pre-commit run $HookName --all-files
        if ($LASTEXITCODE -ne 0) { throw "$HookName failed" }
        Write-Host "✅ $HookName passed!" -ForegroundColor Green
    } catch {
        Write-Host "❌ $HookName failed!" -ForegroundColor Red
        exit 1
    }
}

# 1. Code Style & Formatting (using pre-commit hooks)
Run-PreCommitHook -HookName "trailing-whitespace" -Message "Checking for trailing whitespace"
Run-PreCommitHook -HookName "end-of-file-fixer" -Message "Fixing end of files"
Run-PreCommitHook -HookName "check-yaml" -Message "Checking YAML syntax"
Run-PreCommitHook -HookName "ruff-format" -Message "Formatting code (Ruff Format)"
Run-PreCommitHook -HookName "ruff" -Message "Linting code (Ruff)"

# 2. Type Checking: Mypy
Write-Host "`n🧠 Checking Types (Mypy)..." -ForegroundColor Yellow
try {
    # Очищаем кэш для свежей проверки
    if (Test-Path ".mypy_cache") {
        Write-Host "   Clearing mypy cache..." -ForegroundColor Gray
        Remove-Item -Recurse -Force .mypy_cache
    }
    mypy src/
    if ($LASTEXITCODE -ne 0) { throw "Mypy found errors" }
    Write-Host "✅ Mypy passed!" -ForegroundColor Green
} catch {
    Write-Host "❌ Mypy failed!" -ForegroundColor Red
    exit 1
}

# 3. Unit Tests: Pytest
# Запускаем только unit-тесты, исключая интеграционные (требующие БД)
Write-Host "`n🧪 Running Unit Tests (Pytest)..." -ForegroundColor Yellow
try {
    # Устанавливаем фейковый ключ, если его нет в .env
    $env:SECRET_KEY = "local_test_key"

    # Ищем тесты в src, но игнорируем любые папки integration
    pytest src --ignore-glob="**/integration/**"
    if ($LASTEXITCODE -ne 0) { throw "Tests failed" }
    Write-Host "✅ Tests passed!" -ForegroundColor Green
} catch {
    Write-Host "❌ Tests failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n🎉 ALL CHECKS PASSED! You are ready to push." -ForegroundColor Cyan
