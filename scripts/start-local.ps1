param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("model", "backend", "frontend")]
    [string]$Service
)
$ErrorActionPreference = "Stop"
$cvaiRoot = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $cvaiRoot
if ($Service -eq "frontend") {
    Set-Location -LiteralPath (Join-Path $cvaiRoot "frontend")
    & npm run dev
    exit $LASTEXITCODE
}
$cvaiConfigPath = Join-Path $cvaiRoot "backend/src/FutureCV.Api/appsettings.Development.json"
$cvaiConfig = Get-Content -LiteralPath $cvaiConfigPath -Raw | ConvertFrom-Json
$cvaiKey = [string]$cvaiConfig.EvidenceAi.ApiKey
if ($cvaiKey.Length -lt 32 -or !$cvaiConfig.EvidenceAi.Enabled) {
    throw "Cấu hình EvidenceAi trong appsettings.Development.json: Enabled=true, BaseUrl và ApiKey ít nhất 32 ký tự."
}
if ($Service -eq "model") {
    $cvaiUrl = [uri]$cvaiConfig.EvidenceAi.BaseUrl
    if ($cvaiUrl.Host -notin @("localhost", "127.0.0.1")) { throw "Lệnh chạy local yêu cầu BaseUrl trên localhost." }
    $env:INTERNAL_API_KEY = $cvaiKey
    $env:CVAI_ARTIFACT_DIR = (Resolve-Path (Join-Path $cvaiRoot "models/evidence-r1")).Path
    $cvaiPython = if ($env:VIRTUAL_ENV) { Join-Path $env:VIRTUAL_ENV "Scripts/python.exe" } elseif (Test-Path ".venv/Scripts/python.exe") { ".venv/Scripts/python.exe" } else { "python" }
    & $cvaiPython -m uvicorn server:app --app-dir training/lightweight_cv --host 127.0.0.1 --port $cvaiUrl.Port --workers 1
} else {
    # Set explicitly so an old terminal variable cannot override the shared key.
    $env:EvidenceAi__Enabled = "true"
    $env:EvidenceAi__BaseUrl = [string]$cvaiConfig.EvidenceAi.BaseUrl
    $env:EvidenceAi__ApiKey = $cvaiKey
    & dotnet run --project backend/src/FutureCV.Api
}
exit $LASTEXITCODE
