$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$ScriptPath = Join-Path $ProjectRoot "tools\dev\graphify_wiki.py"
$ToolPython = Join-Path $env:APPDATA "uv\tools\graphifyy\Scripts\python.exe"
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (Test-Path $ToolPython) {
    & $ToolPython $ScriptPath $ProjectRoot @args
    exit $LASTEXITCODE
}

if (Test-Path $VenvPython) {
    & $VenvPython $ScriptPath $ProjectRoot @args
    exit $LASTEXITCODE
}

throw "Python executable not found. Expected one of:`n- $ToolPython`n- $VenvPython"
