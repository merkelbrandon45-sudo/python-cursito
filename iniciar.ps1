# Script para iniciar el Descargador de YouTube a MP3

Write-Host "╔════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Descargador de YouTube a MP3            ║" -ForegroundColor Cyan
Write-Host "║   v1.0                                    ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Verificar si FFmpeg existe
$ffmpegExists = $null -ne (Get-Command ffmpeg -ErrorAction SilentlyContinue)

if (-not $ffmpegExists) {
    Write-Host "⚠️  ADVERTENCIA: FFmpeg no está instalado" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "FFmpeg es necesario para convertir audio a MP3."
    Write-Host ""
    Write-Host "Para instalar FFmpeg en Windows:"
    Write-Host "1. Opción A (Recomendado - requiere Chocolatey):"
    Write-Host "   choco install ffmpeg -y"
    Write-Host ""
    Write-Host "2. Opción B (Manual):"
    Write-Host "   - Ve a https://ffmpeg.org/download.html"
    Write-Host "   - Descarga la versión Full para Windows"
    Write-Host "   - Extrae y agrega a C:\ffmpeg"
    Write-Host "   - Agrega C:\ffmpeg\bin al PATH"
    Write-Host ""
    $response = Read-Host "¿Deseas continuar sin FFmpeg? (s/n)"
    if ($response -ne 's') {
        Write-Host "Instalación cancelada." -ForegroundColor Red
        exit
    }
}

Write-Host ""
Write-Host "✓ Iniciando servidor..." -ForegroundColor Green
Write-Host ""

# Crear carpeta descargas si no existe
$carpeta = Join-Path $PSScriptRoot "descargas"
if (!(Test-Path $carpeta)) {
    New-Item -ItemType Directory -Path $carpeta | Out-Null
    Write-Host "✓ Carpeta 'descargas/' creada" -ForegroundColor Green
}

# Ejecutar Flask
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "Servidor corriendo en: http://127.0.0.1:5000" -ForegroundColor Green
Write-Host ""
Write-Host "Presiona CTRL+C para detener el servidor" -ForegroundColor Yellow
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# Ejecutar la app
python app.py

Write-Host ""
Write-Host "Servidor detenido." -ForegroundColor Yellow
