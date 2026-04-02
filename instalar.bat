@echo off
REM Instalar dependencias para el Descargador de YouTube MP3

echo ========================================
echo Descargador YouTube a MP3 - Instalador
echo ========================================
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no está instalado o no está en PATH
    echo Por favor instala Python desde https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python detectado

REM Verificar si pip está instalado
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: pip no está disponible
    pause
    exit /b 1
)

echo [OK] pip detectado

REM Instalar librerías Python
echo.
echo Instalando librerías Python...
pip install yt-dlp flask

echo.
echo [OK] Librerías Python instaladas

REM Verificar FFmpeg
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ADVERTENCIA] FFmpeg no está instalado
    echo FFmpeg es necesario para convertir audio a MP3
    echo.
    echo Opciones para instalar FFmpeg:
    echo 1. Instalar con Chocolatey (si está instalado):
    echo    choco install ffmpeg
    echo.
    echo 2. O descargar manualmente de https://ffmpeg.org/download.html
    echo.
    echo Presiona ENTER después de instalar FFmpeg...
    pause
) else (
    echo [OK] FFmpeg detectado
)

echo.
echo ========================================
echo Instalación completada!
echo ========================================
echo.
echo Para ejecutar la app:
echo    python app.py
echo.
echo Luego abre en tu navegador:
echo    http://127.0.0.1:5000
echo.
pause
