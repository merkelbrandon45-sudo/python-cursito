$ErrorActionPreference = 'Stop'

Write-Host "=== Brauti AutoDeploy Web ===" -ForegroundColor Cyan

function Assert-Command {
    param([string]$Name, [string]$InstallHint)
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $cmd) {
        Write-Host "Falta comando: $Name" -ForegroundColor Yellow
        Write-Host $InstallHint -ForegroundColor Yellow
        return $false
    }
    return $true
}

$hasGit = Assert-Command -Name "git" -InstallHint "Instala Git desde https://git-scm.com/download/win"
$hasGh = Assert-Command -Name "gh" -InstallHint "Instala GitHub CLI desde https://cli.github.com/"

if (-not $hasGit -or -not $hasGh) {
    Write-Host "No se puede continuar sin git y gh." -ForegroundColor Red
    exit 1
}

Set-Location $PSScriptRoot

if (-not (Test-Path ".git")) {
    git init
}

git add .

$status = git status --porcelain
if ($status) {
    git commit -m "chore: prepare production deploy and uptime automation"
} else {
    Write-Host "No hay cambios nuevos para commit." -ForegroundColor Yellow
}

$branch = (git rev-parse --abbrev-ref HEAD)
if ($branch -ne "main") {
    git branch -M main
}

Write-Host "Verificando autenticacion con GitHub..." -ForegroundColor Cyan
gh auth status 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    gh auth login
}

$repoUrl = git remote get-url origin 2>$null
if (-not $repoUrl) {
    Write-Host "Creando repo en GitHub y configurando origin..." -ForegroundColor Cyan
    gh repo create brauti --public --source . --remote origin --push
} else {
    git push -u origin main
}

Write-Host "" 
Write-Host "Listo: el codigo ya esta en GitHub." -ForegroundColor Green
Write-Host "Siguiente: desplegar en Render con un click." -ForegroundColor Green
Write-Host "1) Abre https://dashboard.render.com/new?type=web" -ForegroundColor White
Write-Host "2) Conecta el repo brauti" -ForegroundColor White
Write-Host "3) Runtime: Docker" -ForegroundColor White
Write-Host "4) Auto Deploy: ON" -ForegroundColor White
Write-Host "5) Health Check Path: /health" -ForegroundColor White
Write-Host "" 
Write-Host "Luego crea el Deploy Hook en Render y guardalo como secret en GitHub:" -ForegroundColor White
Write-Host "Nombre secret: RENDER_DEPLOY_HOOK_URL" -ForegroundColor White
Write-Host "" 
Write-Host "Cada push a main quedara desplegado automaticamente." -ForegroundColor Green
