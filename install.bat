@echo off
echo Instalando dependencias para brauti...
pip install yt-dlp flask textblob requests cryptography flask-talisman pillow
echo Generando iconos PWA...
python generate_icons.py
echo Creando ejecutable con PyInstaller...
pip install pyinstaller
pyinstaller --onefile --name brauti app.py
echo Ejecutable creado en dist\brauti.exe
echo Copiando carpetas necesarias...
xcopy /E /I templates dist\templates\
xcopy /E /I static dist\static\
mkdir dist\descargas
echo Listo! Ejecuta dist\brauti.exe para usar la app sin Python.