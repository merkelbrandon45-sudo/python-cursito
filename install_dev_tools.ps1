$ErrorActionPreference = 'Stop'

Write-Host "=== Instalador de herramientas (Git + GitHub CLI) ===" -ForegroundColor Cyan

$hasWinget = Get-Command winget -ErrorAction SilentlyContinue
if (-not $hasWinget) {
    Write-Host "No se encontro winget. Instala Git y GitHub CLI manualmente:" -ForegroundColor Yellow
    Write-Host "- Git: https://git-scm.com/download/win" -ForegroundColor Yellow
    Write-Host "- GitHub CLI: https://cli.github.com/" -ForegroundColor Yellow
    exit 1
}

Write-Host "Instalando Git..." -ForegroundColor Cyan
winget install --id Git.Git --source winget --accept-package-agreements --accept-source-agreements

Write-Host "Instalando GitHub CLI..." -ForegroundColor Cyan
winget install --id GitHub.cli --source winget --accept-package-agreements --accept-source-agreements

Write-Host "Instalacion finalizada. Cierra y abre PowerShell nuevamente." -ForegroundColor Green
