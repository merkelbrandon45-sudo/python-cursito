# 🎵 brauti - Descargador de YouTube a MP3

App funcional para descargar y almacenar canciones de YouTube en formato MP3 con **múltiples usuarios** y **sistema de sugerencias**.

## ✨ Características

- ✅ **Múltiples Usuarios**: Usuario Principal + Usuario Amigo
- ✅ **Sistema de Sugerencias**: Las descargas aparecen como burbujas para otros usuarios
- ✅ Descarga canciones desde YouTube
- ✅ Almacenamiento local en carpeta `descargas/`
- ✅ Interfaz web moderna y fácil de usar
- ✅ Reproducir canciones en el navegador
- ✅ Descargar archivos MP3 a tu PC
- ✅ Eliminar canciones del almacenamiento
- ✅ Ver lista de todas tus descargas
- ✅ Información de tamaño de archivo
- ✅ Seguridad mejorada: cookies seguras, headers de seguridad y contraseñas con hash

## 📋 Requisitos Previos

Antes de ejecutar la aplicación, debes tener instalado:

1. **Python 3.8+** - [Descargar](https://www.python.org/downloads/)
2. **FFmpeg** - Necesario para la conversión de audio

### Instalar FFmpeg en Windows

#### Opción 1: Usar Chocolatey (Recomendado)
```powershell
choco install ffmpeg
```

#### Opción 2: Descargar manualmente
1. Ve a [ffmpeg.org](https://ffmpeg.org/download.html)
2. Descarga la versión "Full" para Windows
3. Extrae los archivos
4. Agrega la carpeta `bin` a tu PATH de Windows

Para verificar que FFmpeg está instalado:
```powershell
ffmpeg -version
```

## 🚀 Instalación y Ejecución

1. **Abre PowerShell o Cmd** en la carpeta del proyecto

2. **Instala las dependencias Python** (si no lo hiciste aún):
```powershell
pip install yt-dlp flask textblob requests
```

3. **Ejecuta la aplicación web**:
```powershell
python app.py
```

4. Verifica en consola que se ejecuta en:
```
* Running on http://0.0.0.0:5000
```

### Enlace unificado para PC y celular
- El link *único* recomendado es usar **ngrok** (igual en PC y celular, en cualquier WiFi):
  1. Instala y configura ngrok: `ngrok config add-authtoken TU_TOKEN`
  2. Lanza: `ngrok http 5000 --basic-auth usuario:password`
  3. Copia el enlace HTTPS (ej: `https://abc123.ngrok.io`).
  4. Ingresa desde PC o celular con ese mismo enlace.

- Si quieres LAN local (sin ngrok):
  - PC: `http://127.0.0.1:5000` o `http://localhost:5000`
  - Celular (misma red): `http://[IP-PC]:5000` (no uses `127.0.0.1` desde el celular).

**Importante**: `127.0.0.1` en celular apunta al propio teléfono, por eso te redirige a otro sitio. Usa el IP real del PC o el enlace ngrok.

**Permitir puerto en Firewall (Windows)**:
Ejecuta como Administrador:
```powershell
netsh advfirewall firewall add rule name="brauti" dir=in action=allow protocol=TCP localport=5000
```
Esto permite el puerto 5000 para acceso en LAN.

### Instalación automática (sin ejecutar Python manualmente)
Ejecuta `install.bat` para instalar dependencias, generar iconos PWA y crear un ejecutable independiente:
```cmd
install.bat
```
Esto instala todo, genera iconos `icon-192.png` y `icon-512.png` en `static/`, crea `dist\brauti.exe`, y copia las carpetas necesarias. Luego, ejecuta `dist\brauti.exe` sin necesidad de Python instalado.

### ¿Descarga para PC o para celular?
Al inicio de la app de brauti puedes elegir directamente:
- Si es para **PC**: abre con el enlace local (`http://127.0.0.1:5000`) o ngrok.
- Si es para **celular**: usa el mismo enlace *ngrok* (recomendado), que funciona desde cualquier WiFi y aparece igual.

Tanto en PC como en móvil, al abrir brauti con el mismo enlace tendrás la misma experiencia y no hace falta buscar por IP.

### Acceso desde cualquier WiFi (remoto)
Para usar la app desde cualquier lugar (diferentes WiFi), usa ngrok para crear un túnel público seguro:
1. Descarga ngrok desde https://ngrok.com/download
2. Regístrate en ngrok y obtén un auth token: `ngrok config add-authtoken TU_TOKEN`
3. Ejecuta: `ngrok http 5000 --basic-auth usuario:password` (agrega autenticación básica)
4. Copia el enlace HTTPS generado (ej: https://abc123.ngrok.io)
5. Comparte ese enlace para acceso remoto desde PC o celular.

**Nota de seguridad**: Usa autenticación básica con ngrok para proteger el acceso. No uses sin auth en redes públicas. Alternativa: Despliega en un VPS con HTTPS para producción. Cierra ngrok cuando no uses.

### Ejecutar la versión CLI (brauti CLI)

1. En la misma carpeta, ejecuta:
```powershell
python descargador_cli.py
```

2. Usa el menú para:
- Descargar una canción
- Descarga en lote con archivo de URLs
- Buscar en YouTube por texto
- Editar metadatos
- Crear y gestionar playlists
- Sincronizar con teléfono (mostrar IP)


## � Ejecución sin instalar Python (opcional)

Si quieres que quien use la app no tenga que instalar Python ni dependencias, crea un ejecutable con `PyInstaller`:

```powershell
pip install pyinstaller
pyinstaller --onefile --name brauti app.py
```

- El ejecutable se genera en `dist\brauti.exe`.
- Copia la carpeta `descargas` y `templates`/`static` junto al ejecutable.
- Asegura que FFmpeg esté disponible en el `PATH`; si no, recibes un mensaje claro.


## �💡 Cómo Usar

### 0. Nombre de la app
- Esta app se llama **brauti**

### 1. Seleccionar Usuario
- Abre la app en tu navegador
- Elige entre "Bran" o "Bauti"

### 2. Configuración Inicial
- **Bran**: Ingresa la contraseña `48695973Bm`
- **Bauti**: Crea tu contraseña personal la primera vez

### 3. Descargar una canción:
1. Pega el enlace de un video de YouTube
2. Haz clic en "Descargar"
3. ¡Espera a que termine la descarga!

### 4. Sistema de Sugerencias (Usuario Amigo):
- Verás burbujas con canciones descargadas por el Usuario Principal
- Haz clic en una burbuja para descargar automáticamente
- Las sugerencias se actualizan automáticamente

### 5. Gestionar canciones:
- **Reproducir**: Haz clic en "Escuchar"
- **Descargar**: Haz clic en "Descargar" para guardar en tu PC
- **Eliminar**: Haz clic en "Eliminar" para borrar de la biblioteca

## � Sistema de Usuarios

### Bran (Usuario Principal)
- **Contraseña**: `48695973Bm` (predefinida)
- Tiene acceso completo a todas las funciones
- Sus descargas aparecen como sugerencias para Baut

### Bauti (Usuario Amigo)
- **Contraseña**: Se crea la primera vez que accede
- Puede crear/cambiar su contraseña
- Recibe sugerencias de música de Bran
- Tiene su propia biblioteca de canciones

### Sistema de Sugerencias Bidireccional
- **Bran** ve las últimas 10 descargas de **Bauti**
- **Bauti** ve las últimas 10 descargas de **Bran**
- Clic en burbuja = descarga automática
- Cada usuario mantiene su historial separado

### 🎵 Reproducción con Información
- Al reproducir una canción, se muestra un modal con:
  - **Portada del video** (thumbnail de YouTube)
  - **Análisis de sentimiento** del título (😊 positivo, 😢 negativo, 😐 neutral)
  - **Duración** de la canción
  - **Fecha de descarga**

```
python cursito/
├── app.py                 # Servidor Flask (lógica principal)
├── templates/
│   └── index.html         # Interfaz web
├── static/
│   ├── style.css          # Estilos
│   └── script.js          # JavaScript del cliente
├── descargas/             # Carpeta donde se guardan los MP3
└── README.md              # Este archivo
```

## 🔧 Requisitos de Sistema

- **RAM**: Mínimo 2GB (recomendado 4GB+)
- **Disco**: 100MB libres (+ espacio para canciones)
- **Conexión**: Internet para descargar de YouTube (deshabilitable con modo sandbox)
- **Windows 10 o superior** o Linux/Mac

## 🛡️ Opciones de seguridad avanzadas

- Da de alta `BRAUTI_ENC_KEY` para cifrado de configuración y usuarios.
- Usa `Flask-Talisman` en producción para forzar HTTPS y CSP: `pip install flask-talisman`.
- Con `USE_SQLITE=true`, las tablas deben guardarse en `brauti.db`; las contraseñas se guardan en hash.
- En modo `SANDBOX_ONLY` (cambiar en `app.py`) no se permite descarga desde YouTube, solo archivos MP3 locales.

## 🌐 Despliegue seguro con NGINX y HTTPS

Se recomienda este flujo para producción:
1. Ejecuta la app en localhost con `gunicorn` o `waitress`, p.ej.: `gunicorn -b 127.0.0.1:5000 app:app`.
2. Configura NGINX como proxy inverso en HTTPS con certificados (`Let's Encrypt`)
3. Forzar `https` en NGINX y en Flask-Talisman para evitar tráfico no seguro.
4. Firewall y red confiable: solo accesible desde la LAN o IPs aprobadas.
5. Guarda `BRAUTI_ENC_KEY` en variable de entorno del sistema, no en código o repositorio.

Ejemplo de configuración NGINX (`/etc/nginx/sites-available/brauti`):
```
server {
    listen 80;
    server_name tu-dominio.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name tu-dominio.com;

    ssl_certificate /etc/letsencrypt/live/tu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tu-dominio.com/privkey.pem;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🌍 Dominio y HTTPS (`brauti.com` definitivo)

Para tener `https://brauti.com` necesitas:
1. Comprar/registrar el dominio `brauti.com` con un proveedor (GoDaddy, Namecheap, Cloudflare, etc.).
2. Apuntar DNS A/AAAA a la IP pública de tu servidor (o usar CNAME a un servicio de despliegue).
3. Crear el sitio en un servidor con NGINX/Apache/Traefik y configurar SSL (ej. Let's Encrypt):
   - `sudo certbot --nginx -d brauti.com -d www.brauti.com`
4. Forzar HTTPS y redirigir tráfico (código arriba). 
5. En Flask, activa en producción:
   - `FLASK_ENV=production`
   - `SESSION_COOKIE_SECURE=True`
   - `Talisman(app, force_https=True, content_security_policy=...)`

> Resultado: URL limpia y oficial, lista para SEO y aplicación de Google.

## 📲 Play Store / APK (android)

### 1) Empaquetar como PWA local (ya hecho):
- `manifest.json` con `display: standalone`.
- `sw.js` cachea recursos.
- Botón de instalación (`beforeinstallprompt`).
- Ruta `/download-apk` y descarga de `static/brauti.apk`.

### 2) Generar AAB/APK (recomendado para Play Store):
- Usar Capacitor/Ionic o TWA:
  - `npm install -g @ionic/cli` (opcional)
  - `npm init @capacitor/app` / `npx cap init brauti com.brauti.app`
  - `npx cap add android`
  - Copiar `www` con tu app (si la transformas a web files). 
- Otra opción rápida: `bubblewrap` para TWA.
- Abrir proyecto Android en Android Studio, compilar AAB.

### 3) Publicar en Google Play:
1. Crear cuenta de desarrollador: pagar $25.
2. Crear nueva app > subir AAB.
3. Añadir capturas, descripción, políticas de privacidad.
4. Pedir revisión y publicar.

## 🧹 Solución de problemas de “import no resuelto”

1. Asegúrate de usar el mismo intérprete Python que tu VSCode: `Ctrl+Shift+P` -> `Python: Select Interpreter`.
2. Ejecuta:
```powershell
pip install -r requirements.txt
```
3. Si sigues viendo warnings en VSCode, recarga ventana (`Ctrl+Shift+P` -> `Developer: Reload Window`).
4. Comprueba librerías opcionales desde el código:
   - `yt-dlp`, `flask`, `textblob`, `requests`, `python-dotenv`, `cryptography`, `pyngrok`, `flask-talisman`.

## 🛠️ Ajustes de código ejecutados ahora

- Importaciones con `try/except` para `yt_dlp`, `textblob`, `requests`, `cryptography`, y fallback funcional.
- `download_youtube_to_mp3` y `search_youtube` devuelven error detallado si `yt_dlp` falta.
- `analyze_sentiment` devuelve `neutral` si TextBlob no está instalado.
- `encrypt_data` y `decrypt_data` usan fallback sin cifrado si `cryptography` no está disponible.

---

Con esto, el proyecto ya es robusto, PWA + APK/local instalable + documentación completa para dominio/Play Store, y no depende de un entorno ya precargado. Si querés, ahora paso a añadir un script opcional `deploy.sh` para automatizar: 1) nginx, 2) certbot, 3) reinicio de servicio.
server {
    listen 80;
    server_name tu-dominio.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name tu-dominio.com;

    ssl_certificate /etc/letsencrypt/live/tu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tu-dominio.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 📱 Acceso directo y PWA (App-like)

### En Computadora (Windows)
Crea un acceso directo para que aparezca como app normal:
1. Abre el navegador y ve a `http://127.0.0.1:5000` (local) o el enlace ngrok (remoto, mismo para todos).
2. En Chrome/Edge: Menú → Más herramientas → Crear acceso directo.
3. Marca "Abrir como ventana" y crea el shortcut en el escritorio.

### En Teléfono/Celular (PWA)
La app se instala como app nativa:
1. Abre en Chrome/Safari móvil: `http://tu-ip:5000` (LAN) o el enlace ngrok (cualquier WiFi, mismo enlace).
2. En Chrome: Menú → Agregar a pantalla de inicio.
3. En Safari: Compartir → Agregar a pantalla de inicio.
4. Ahora aparece en el menú de apps y se abre directamente sin navegador.

### Modo Offline
- Las canciones descargadas se reproducen sin internet (modo offline).
- La interfaz se cachea para acceso rápido sin conexión.

## ⚖️ Legal y uso responsable

- Esta aplicación está pensada para uso personal con contenido que tengas derecho a descargar (tus propios videos, material libre de derechos o con las licencias adecuadas).
- Está prohibido descargar material con derechos sin permiso; no es legal ni correcto hacerlo.
- La descarga desde YouTube está bloqueada si no confirmas la licencia con `confirm_license=true` en cada petición.
- No se almacena ni comparte información personal del usuario; solo se guarda el nombre de usuario (`bran` o `bauti`) y el historial de descargas.
- Usa redes privadas seguras y mantén el software actualizado.


Si quieres cambiar la configuración, edita `app.py`:

```python
# Cambiar puerto (línea al final)
app.run(debug=True, host='127.0.0.1', port=5000)
# Cambio a: port=8000 (para usar puerto 8000)
```

## 📝 Solución de Problemas

### "ffmpeg not found"
- Instala FFmpeg siguiendo las instrucciones arriba
- Reinicia PowerShell/Cmd después de instalar

### "Permission denied" en descargas/
- Asegúrate de que la carpeta tiene permisos de escritura
- Intenta ejecutar PowerShell como Administrador

### El navegador no carga la página
- Verifica que el puerto 5000 esté libre
- Intenta acceder a `http://localhost:5000`

### La descarga es muy lenta
- Depende de tu velocidad de internet y el tamaño del video
- YouTube to MP3 puede tardar 1-5 minutos

## 🎯 Características Implementadas en brauti

- [x] Interfaz de línea de comandos (CLI)
- [x] Descargas en lote
- [x] Editar metadatos de canciones
- [x] Crear playlists
- [x] Buscar canciones en YouTube
- [x] Sincronizar con teléfono (acceso móvil + descarga remota)


## 📄 Licencia

Código libre para uso personal. Asegúrate de respetar los derechos de autor al descargar canciones.

## ⚖️ Legal y uso responsable

- Esta aplicación está pensada para uso personal con contenido que tengas derecho a descargar (tus propios videos, material libre de derechos, o con las licencias adecuadas).
- No utilices brauti para infringir derechos de autor de terceros o políticas de plataformas de video.
- No se almacena ni comparte información personal de los usuarios. El único dato guardado es el identificador del usuario en el dispositivo (`bran` o `bauti`) y su historial de descargas para la funcionalidad de sugerencias.
- Se recomienda usar siempre con conexión a redes seguras y mantener el software actualizado. En caso de publicar en Internet, hazlo bajo HTTPS y con control de acceso.
- La app no puede garantizar 0% riesgo legal automáticamente, ya que no verifica licencias de videos de YouTube sin API oficial. El sistema obliga a confirmar explícitamente para evitar descargas sin autorización.
- Con HTTPS, cifrado de datos y confirmación legal, es mucho más segura para uso personal.

## 🔧 Solución específica: ERR_NGROK_3200 (offline)
1. Este error significa que el túnel ngrok expiró o se cerró.
2. Si usaste el enlace `abc123.ngrok.io`, abre terminal y ejecuta de nuevo:
   - `ngrok http 5000 --basic-auth usuario:password`
3. Copia el nuevo enlace y úsalo de inmediato.
4. Para evitar esto de forma definitiva:
   - Ejecuta `python app.py` y usa LAN local con IP PC (`http://[IP-PC]:5000`), o
   - suscribe ngrok a una cuenta con dominio fijo (opción paga), o
   - usa NGINX con dominio/HTTPS propio.

---

¿Dudas o problemas? Revisa los logs en la terminal para más información.

¡Disfruta tu música! 🎵
