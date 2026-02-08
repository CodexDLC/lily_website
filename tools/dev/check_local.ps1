Clear-Host
$ErrorActionPreference = "Stop"
Write-Host "🚀 Starting Local Quality Check..." -ForegroundColor Cyan

# 1. Code Style: Ruff
Write-Host "`n🔍 Checking Style (Ruff)..." -ForegroundColor Yellow
try {
    # Проверяем всю папку src
    ruff check src/ --fix
    if ($LASTEXITCODE -ne 0) { throw "Ruff found errors" }
    Write-Host "✅ Ruff passed!" -ForegroundColor Green
} catch {
    Write-Host "❌ Ruff failed!" -ForegroundColor Red
    exit 1
}

# 2. Type Checking: Mypy
Write-Host "`n🧠 Checking Types (Mypy)..." -ForegroundColor Yellow
try {
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
