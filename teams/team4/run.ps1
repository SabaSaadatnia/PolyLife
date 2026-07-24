$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created teams/team4/.env from .env.example"
}

docker network inspect polylife_net *> $null

if ($LASTEXITCODE -ne 0) {
    Write-Host "The shared network polylife_net does not exist."
    Write-Host "Start the root Core service first:"
    Write-Host "  docker compose -f docker-compose.yml up -d core"
    exit 1
}

docker compose up --build
