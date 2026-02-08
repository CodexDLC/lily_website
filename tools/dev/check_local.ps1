$ErrorActionPreference = "Stop"
Write-Host "🚀 Starting Local Quality Check..." -ForegroundColor Cyan

# 1. Backend & Tests: Ruff
Write-Host "`n🔍 Checking Style (Ruff)..." -ForegroundColor Yellow
try {
    # Проверяем и backend, и tests
    ruff check backend/ tests/ --fix
    if ($LASTEXITCODE -ne 0) { throw "Ruff found errors" }
    Write-Host "✅ Ruff passed!" -ForegroundColor Green
} catch {
    Write-Host "❌ Ruff failed!" -ForegroundColor Red
    exit 1
}

# 2. Backend: Mypy
Write-Host "`n🧠 Checking Backend Types (Mypy)..." -ForegroundColor Yellow
try {
    mypy backend/
    if ($LASTEXITCODE -ne 0) { throw "Mypy found errors" }
    Write-Host "✅ Mypy passed!" -ForegroundColor Green
} catch {
    Write-Host "❌ Mypy failed!" -ForegroundColor Red
    exit 1
}

# 3. Backend: Pytest (Unit Tests Only)
# Запускаем только unit-тесты, так как для integration нужна живая БД.
# Если хочешь запускать всё, убедись, что БД поднята, и убери "tests/unit"
Write-Host "`n🧪 Running Unit Tests (Pytest)..." -ForegroundColor Yellow
try {
    # Устанавливаем фейковый ключ, если его нет в .env, чтобы тесты не падали при старте
    $env:SECRET_KEY = "local_test_key"

    pytest tests/unit
    if ($LASTEXITCODE -ne 0) { throw "Tests failed" }
    Write-Host "✅ Tests passed!" -ForegroundColor Green
} catch {
    Write-Host "❌ Tests failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n🎉 ALL CHECKS PASSED! You are ready to push." -ForegroundColor Cyan