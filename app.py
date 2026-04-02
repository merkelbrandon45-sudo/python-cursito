from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for

# Dependencias opcionales y manejo de imports ausentes
try:
    import yt_dlp
except ImportError:
    yt_dlp = None

import os
import logging
from pathlib import Path
import threading
from functools import wraps
import json
import time
from datetime import datetime
from urllib.parse import quote_plus
import re
import subprocess

try:
    from textblob import TextBlob
except ImportError:
    TextBlob = None

try:
    import requests
except ImportError:
    requests = None

try:
    from youtubesearchpython import VideosSearch
except ImportError:
    VideosSearch = None

try:
    from pytubefix import YouTube
except ImportError:
    YouTube = None

from werkzeug.security import generate_password_hash, check_password_hash
import shutil
import sqlite3

try:
    from cryptography.fernet import Fernet
except ImportError:
    Fernet = None


# ngrok integration for unified link (remote + local)
try:
    from pyngrok import ngrok, conf
except ImportError:
    ngrok = None
    conf = None

app = Flask(__name__)
app.secret_key = os.environ.get('BRAUTI_SECRET_KEY', 'descargador_youtube_mp3_2024')
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=False  # En producción usar True con HTTPS y HTTPS completo
)

# Activar HTTPS con Flask-Talisman si está disponible (solo en producción)
if os.environ.get('FLASK_ENV') == 'production':
    try:
        from flask_talisman import Talisman
        csp = {
            'default-src': ['\'self\''],
            'script-src': ['\'self\'', '\'unsafe-inline\''],
            'style-src': ['\'self\'', '\'unsafe-inline\'', 'https://cdnjs.cloudflare.com']
        }
        Talisman(app, content_security_policy=csp, force_https=True, session_cookie_secure=True)
    except ImportError:
        print('Aviso: Flask-Talisman no instalado, correr: pip install flask-talisman para HTTPS reforzado')
else:
    print('Modo desarrollo: Talisman deshabilitado para evitar advertencias de seguridad en local')

# Opciones de configuración
USE_SQLITE = True
USE_DISK_ENCRYPTION = True
SANDBOX_ONLY = False  # True: no se pueden descargar de YouTube, solo subir MP3 propios

# Método para iniciar ngrok automáticamente (si está disponible)
def start_ngrok():
    if ngrok is None:
        print('pyngrok no instalado; no se inicia ngrok automáticamente. Ejecuta: pip install pyngrok')
        return None

    auth_token = os.environ.get('NGROK_AUTH_TOKEN', '')
    if not auth_token:
        print('NGROK_AUTH_TOKEN no configurado. Configura la variable de entorno para activar ngrok.')
        return None

    if conf:
        conf.get_default().auth_token = auth_token

    try:
        tunnel = ngrok.connect(5000)
        print(f'ngrok activo: {tunnel.public_url}')
        print('Abre ese enlace desde PC/celular para acceso unificado')
        return tunnel.public_url
    except Exception as e:
        print(f'Error al iniciar ngrok: {e}')
        return None


def maintain_ngrok():
    if ngrok is None:
        return

    while True:
        try:
            active_tunnels = ngrok.get_tunnels()
            if not active_tunnels:
                tunnel = start_ngrok()
                if tunnel:
                    print(f'Ngrok recreado: {tunnel}')
            else:
                current = active_tunnels[0].public_url
                print(f'ngrok sigue activo: {current}')
            time.sleep(20)
        except Exception as e:
            print(f'Error ngrok monitor: {e} - reintentando en 5s')
            time.sleep(5)


def set_safe_error_handlers(app):
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        try:
            app.logger.error('Error inesperado', exc_info=error)
        except Exception:
            logging.error('Error inesperado (no se pudo usar app.logger)', exc_info=True)

        response = jsonify({'success': False, 'message': 'Ha ocurrido un error interno. Reintentando...'} )
        response.status_code = 500
        return response


set_safe_error_handlers(app)

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'brauti.db')
USERS_FILE = os.path.join(os.path.dirname(__file__), 'users.json.enc')
PLAYLISTS_FILE = os.path.join(os.path.dirname(__file__), 'playlists.json.enc')
MUSIC_FOLDER = os.path.join(os.path.dirname(__file__), 'descargas')

# Clave de cifrado para datos en disco (debe guardarse segura en producción)
ENCRYPTION_KEY = os.environ.get('BRAUTI_ENC_KEY')
if not ENCRYPTION_KEY:
    # Fallback seguro: generar una clave Fernet válida cuando no se provee env var.
    ENCRYPTION_KEY = Fernet.generate_key().decode() if Fernet is not None else ''

if Fernet is None:
    print('Aviso: cryptography no está instalado; se usará almacenamiento JSON sin cifrar. Instala pip install cryptography para cifrado.')
    FERNET = None
else:
    try:
        FERNET = Fernet(ENCRYPTION_KEY.encode())
    except Exception:
        print('Aviso: BRAUTI_ENC_KEY inválida; se generará una clave temporal para evitar caída en arranque.')
        ENCRYPTION_KEY = Fernet.generate_key().decode()
        FERNET = Fernet(ENCRYPTION_KEY.encode())

# Usuario principal (ya existe)
DEFAULT_USERS = {
    'bran': {
        'password': None,  # Se crea la primera vez
        'name': 'Bran',
        'downloads': [],
        'created': False,
        'secret_question': '¿cuando cumple años bauti?',
        'secret_answer': '21 de abril'
    },
    'bauti': {
        'password': None,  # Se crea la primera vez
        'name': 'Bauti',
        'downloads': [],
        'created': False,
        'secret_question': '¿cuando cumple años bran?',
        'secret_answer': '5 de junio'
    }
}

# Solo habilitar reset de Bran por variable de entorno en casos puntuales.
RESET_BRAN_PASSWORD_ON_START = os.environ.get('RESET_BRAN_PASSWORD_ON_START', 'false').lower() == 'true'


def is_password_hash(value):
    """Detecta hashes soportados por Werkzeug para evitar re-hashear hashes existentes."""
    if not value or not isinstance(value, str):
        return False
    return value.startswith('pbkdf2:') or value.startswith('scrypt:') or value.startswith('argon2:')

def encrypt_data(data):
    payload = json.dumps(data, ensure_ascii=False).encode('utf-8')
    if FERNET:
        return FERNET.encrypt(payload)
    return payload


def decrypt_data(bytes_data):
    if FERNET:
        return json.loads(FERNET.decrypt(bytes_data).decode('utf-8'))
    return json.loads(bytes_data.decode('utf-8'))


def save_encrypted_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(encrypt_data(data))


def load_encrypted_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, 'rb') as f:
            return decrypt_data(f.read())
    except Exception:
        return default


def init_db():
    if not USE_SQLITE:
        return
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT,
            password TEXT,
            created INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            filename TEXT,
            title TEXT,
            url TEXT,
            thumbnail TEXT,
            duration INTEGER,
            sentiment TEXT,
            sentiment_emoji TEXT,
            downloaded_at TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            name TEXT,
            songs TEXT
        )
    ''')
    conn.commit()
    conn.close()


def load_users():
    """Carga los usuarios desde el archivo cifrado o DB"""
    global RESET_BRAN_PASSWORD_ON_START
    if USE_SQLITE:
        init_db()
        conn = sqlite3.connect(DATABASE_PATH)
        cur = conn.cursor()
        cur.execute('SELECT id, name, password, created FROM users')
        rows = cur.fetchall()
        conn.close()
        if rows:
            users = {
                r[0]: {'name': r[1], 'password': r[2], 'created': bool(r[3]), 'downloads': []}
                for r in rows
            }
        else:
            users = DEFAULT_USERS.copy()
            save_users(users)
        # cargar descargas también
        conn = sqlite3.connect(DATABASE_PATH)
        cur = conn.cursor()
        cur.execute('SELECT user_id, filename, title, url, thumbnail, duration, sentiment, sentiment_emoji, downloaded_at FROM downloads')
        songs = cur.fetchall()
        conn.close()
        for row in songs:
            user_id = row[0]
            if user_id in users:
                users[user_id].setdefault('downloads', []).append({
                    'filename': row[1], 'title': row[2], 'url': row[3], 'thumbnail': row[4],
                    'duration': row[5], 'sentiment': row[6], 'sentiment_emoji': row[7], 'downloaded_at': row[8]
                })
    else:
        users = load_encrypted_json(USERS_FILE, DEFAULT_USERS.copy())

    # Añadir campos necesarios y migrar de versiones anteriores
    for uid, info in users.items():
        if 'secret_question' not in info or 'secret_answer' not in info:
            # en caso de perfiles antiguos, volver a cargar defaults
            info.setdefault('secret_question', DEFAULT_USERS[uid]['secret_question'])
            info.setdefault('secret_answer', DEFAULT_USERS[uid]['secret_answer'])

    # Reset a petición: elimina contraseña de bran para crear una nueva (solo una vez en arranque)
    if RESET_BRAN_PASSWORD_ON_START and 'bran' in users and users['bran'].get('created', False):
        users['bran']['password'] = None
        users['bran']['created'] = False
        # marcar que ya se aplicó el reset en esta ejecución
        RESET_BRAN_PASSWORD_ON_START = False

    # Hash de passwords solo para valores legacy en texto plano.
    migrated_passwords = False
    for uid, info in users.items():
        pw = info.get('password')
        if pw and not is_password_hash(pw):
            users[uid]['password'] = generate_password_hash(pw)
            migrated_passwords = True

    if USE_SQLITE and migrated_passwords:
        save_users(users)
    elif not USE_SQLITE:
        save_users(users)
    return users


def save_users(users):
    """Guarda los usuarios en DB/archivo cifrado"""
    if USE_SQLITE:
        init_db()
        conn = sqlite3.connect(DATABASE_PATH)
        cur = conn.cursor()
        for uid, info in users.items():
            cur.execute('INSERT OR REPLACE INTO users (id, name, password, created) VALUES (?, ?, ?, ?)',
                        (uid, info.get('name', ''), info.get('password', ''), int(info.get('created', False))))
        conn.commit()
        cur.execute('DELETE FROM downloads')
        for uid, info in users.items():
            for d in info.get('downloads', []):
                cur.execute('''INSERT INTO downloads (user_id, filename, title, url, thumbnail, duration, sentiment, sentiment_emoji, downloaded_at)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                            (uid, d.get('filename', ''), d.get('title', ''), d.get('url', ''), d.get('thumbnail', ''),
                             d.get('duration', 0), d.get('sentiment', ''), d.get('sentiment_emoji', ''), d.get('downloaded_at', '')))
        conn.commit()
        conn.close()
    else:
        save_encrypted_json(USERS_FILE, users)


def load_playlists():
    if USE_SQLITE:
        init_db()
        conn = sqlite3.connect(DATABASE_PATH)
        cur = conn.cursor()
        cur.execute('SELECT user_id, name, songs FROM playlists')
        rows = cur.fetchall()
        conn.close()
        playlists = {'bran': [], 'bauti': []}
        for user_id, name, songs_text in rows:
            songs = json.loads(songs_text) if songs_text else []
            playlists.setdefault(user_id, []).append({'name': name, 'songs': songs})
        return playlists
    else:
        return load_encrypted_json(PLAYLISTS_FILE, {'bran': [], 'bauti': []})


def save_playlists(playlists):
    if USE_SQLITE:
        init_db()
        conn = sqlite3.connect(DATABASE_PATH)
        cur = conn.cursor()
        cur.execute('DELETE FROM playlists')
        for user_id, pl_list in playlists.items():
            for pl in pl_list:
                cur.execute('INSERT INTO playlists (user_id, name, songs) VALUES (?, ?, ?)',
                            (user_id, pl['name'], json.dumps(pl.get('songs', []), ensure_ascii=False)))
        conn.commit()
        conn.close()
    else:
        save_encrypted_json(PLAYLISTS_FILE, playlists)


def get_current_user():
    """Obtiene el usuario actual de la sesión"""
    if 'user_id' in session:
        users = load_users()
        return users.get(session['user_id'])
    return None


@app.context_processor
def inject_url_flags():
    endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}
    return {'forgot_password_route': 'forgot_password' in endpoints}


def get_security_question(user_id):
    users = load_users()
    user = users.get(user_id)
    return user.get('secret_question', '') if user else ''


def validate_security_answer(user_id, answer):
    users = load_users()
    user = users.get(user_id)
    if not user or not answer:
        return False
    expected = user.get('secret_answer', '').strip().lower()
    return answer.strip().lower() == expected


def get_suggestions_for_user(user_id):
    """Obtiene sugerencias de canciones del otro usuario"""
    users = load_users()
    suggestions = []

    # Si es bran, mostrar descargas de bauti
    if user_id == 'bran':
        bauti_downloads = users.get('bauti', {}).get('downloads', [])
        suggestions = bauti_downloads[-10:]  # Últimas 10 descargas
    
    # Si es bauti, mostrar descargas de bran
    elif user_id == 'bauti':
        bran_downloads = users.get('bran', {}).get('downloads', [])
        suggestions = bran_downloads[-10:]  # Últimas 10 descargas
    
    return suggestions

# Carpeta donde se guardarán las canciones (mantener solo la inicialización) 
os.makedirs(MUSIC_FOLDER, exist_ok=True)


# Crear playlists si no existen
if not os.path.exists(PLAYLISTS_FILE):
    with open(PLAYLISTS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'bran': [], 'bauti': []}, f, indent=4, ensure_ascii=False)

# Decorador para proteger rutas
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'authenticated' not in session or not session['authenticated']:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def check_runtime_dependencies():
    """Comprueba si las dependencias necesarias están disponibles"""
    if not shutil.which('ffmpeg'):
        return False, 'FFmpeg no está disponible. Instale FFmpeg o ejecute la versión ejecutable de brauti.'
    return True, ''


@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    if request.is_secure:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response


def get_music_files():
    """Obtiene la lista de archivos MP3 descargados"""
    if not os.path.exists(MUSIC_FOLDER):
        return []

    files = []
    for file in os.listdir(MUSIC_FOLDER):
        if file.endswith('.mp3'):
            file_path = os.path.join(MUSIC_FOLDER, file)
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # Convertir a MB
            files.append({
                'name': file,
                'size': f'{file_size:.2f} MB',
                'path': file_path
            })
    return sorted(files, key=lambda x: x['name'], reverse=True)

def analyze_sentiment(text):
    """Analiza el sentimiento de un texto"""
    if TextBlob is None:
        return "neutral", "😐"

    try:
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        
        if polarity > 0.1:
            return "positivo", "😊"
        elif polarity < -0.1:
            return "negativo", "😢"
        else:
            return "neutral", "😐"
    except:
        return "neutral", "😐"


def sanitize_filename(name):
    clean = re.sub(r'[\\/:*?"<>|]+', '', (name or '').strip())
    clean = re.sub(r'\s+', ' ', clean)
    return clean[:120] if clean else f'song_{int(time.time())}'


def unique_path_with_extension(base_name, extension):
    base_path = os.path.join(MUSIC_FOLDER, f'{base_name}.{extension}')
    if not os.path.exists(base_path):
        return base_path

    idx = 1
    while True:
        candidate = os.path.join(MUSIC_FOLDER, f'{base_name}_{idx}.{extension}')
        if not os.path.exists(candidate):
            return candidate
        idx += 1


def save_download_for_user(user_id, title, filename, url, thumbnail, duration):
    sentiment, emoji = analyze_sentiment(title)
    users = load_users()
    if user_id in users:
        users[user_id]['downloads'].append({
            'title': title,
            'filename': filename,
            'url': url,
            'thumbnail': thumbnail,
            'duration': duration,
            'sentiment': sentiment,
            'sentiment_emoji': emoji,
            'downloaded_at': datetime.now().isoformat(),
            'user_id': user_id
        })
        save_users(users)
    return sentiment, emoji


def download_with_pytubefix(url, user_id):
    if YouTube is None:
        return {'success': False, 'message': 'No se pudo descargar en este momento. Reintenta en unos minutos.'}

    try:
        yt = YouTube(url)
        stream = yt.streams.filter(only_audio=True, file_extension='mp4').order_by('abr').desc().first()
        if stream is None:
            stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
        if stream is None:
            return {'success': False, 'message': 'No se encontró un stream de audio compatible.'}

        title = yt.title or 'Desconocida'
        safe_title = sanitize_filename(title)
        temp_m4a_path = unique_path_with_extension(safe_title, 'm4a')
        final_mp3_path = unique_path_with_extension(safe_title, 'mp3')

        stream.download(output_path=MUSIC_FOLDER, filename=os.path.basename(temp_m4a_path))

        cmd = [
            'ffmpeg', '-y', '-i', temp_m4a_path,
            '-vn', '-acodec', 'libmp3lame', '-ab', '192k',
            final_mp3_path
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if os.path.exists(temp_m4a_path):
            os.remove(temp_m4a_path)

        thumbnail = getattr(yt, 'thumbnail_url', '') or ''
        duration = int(getattr(yt, 'length', 0) or 0)
        filename = os.path.basename(final_mp3_path)
        sentiment, emoji = save_download_for_user(user_id, title, filename, url, thumbnail, duration)

        return {
            'success': True,
            'filename': filename,
            'message': f'Canción descargada: {title}',
            'thumbnail': thumbnail,
            'sentiment': sentiment,
            'sentiment_emoji': emoji
        }
    except Exception as e:
        return {'success': False, 'message': f'Error al descargar (fallback): {str(e)}'}


def duration_to_seconds(duration_text):
    if not duration_text:
        return 0
    try:
        parts = [int(p) for p in duration_text.split(':')]
    except Exception:
        return 0

    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 1:
        return parts[0]
    return 0


def collect_video_renderers(node, bucket):
    if isinstance(node, dict):
        renderer = node.get('videoRenderer')
        if isinstance(renderer, dict):
            bucket.append(renderer)
        for value in node.values():
            collect_video_renderers(value, bucket)
    elif isinstance(node, list):
        for item in node:
            collect_video_renderers(item, bucket)


def search_youtube_html(query, limit=10):
    if requests is None:
        return []

    url = f"https://www.youtube.com/results?search_query={quote_plus(query)}&hl=es&gl=US"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8'
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)
    except Exception:
        return []

    if response.status_code != 200:
        return []

    html = response.text
    marker = 'var ytInitialData = '
    start = html.find(marker)
    if start == -1:
        marker = 'ytInitialData = '
        start = html.find(marker)
        if start == -1:
            return []

    json_start = start + len(marker)
    json_end = html.find(';</script>', json_start)
    if json_end == -1:
        return []

    raw_json = html[json_start:json_end].strip()
    if raw_json.endswith(';'):
        raw_json = raw_json[:-1]

    try:
        data = json.loads(raw_json)
    except Exception:
        return []

    renderers = []
    collect_video_renderers(data, renderers)

    results = []
    for vr in renderers:
        video_id = vr.get('videoId', '')
        if not video_id:
            continue

        title_obj = vr.get('title', {})
        title = title_obj.get('simpleText', '')
        if not title and isinstance(title_obj.get('runs'), list):
            title = ''.join(run.get('text', '') for run in title_obj.get('runs', []))

        if not title:
            continue

        duration_text = (vr.get('lengthText') or {}).get('simpleText', '')
        thumb_list = (vr.get('thumbnail') or {}).get('thumbnails', [])
        thumbnail = thumb_list[-1].get('url', '') if thumb_list else ''

        results.append({
            'id': video_id,
            'title': title,
            'url': f'https://www.youtube.com/watch?v={video_id}',
            'duration': duration_to_seconds(duration_text),
            'thumbnail': thumbnail
        })

        if len(results) >= limit:
            break

    return results

def download_youtube_to_mp3(url, user_id, progress_callback=None):
    """Descarga un video de YouTube como MP3"""
    if yt_dlp is None:
        return {'success': False, 'message': 'Dependencia yt_dlp no instalada. Ejecuta pip install yt-dlp'}

    dep_ok, dep_msg = check_runtime_dependencies()
    if not dep_ok:
        return {'success': False, 'message': dep_msg}

    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(MUSIC_FOLDER, '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'socket_timeout': 30,
            'retries': 5,
            'fragment_retries': 5,
            'extractor_retries': 3,
            'noplaylist': True,
            'geo_bypass': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            },
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web', 'ios'],
                }
            },
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            title = info.get('title', 'Desconocida')
            thumbnail = info.get('thumbnail', '')
            duration = info.get('duration', 0)
            
            out_filename = os.path.basename(filename.replace('.webm', '.mp3').replace('.m4a', '.mp3'))
            sentiment, emoji = save_download_for_user(user_id, title, out_filename, url, thumbnail, duration)

            return {
                'success': True,
                'filename': out_filename,
                'message': f"Canción descargada: {title}",
                'thumbnail': thumbnail,
                'sentiment': sentiment,
                'sentiment_emoji': emoji
            }
    except Exception as e:
        err = str(e)
        err_l = err.lower()

        # YouTube cambia este mensaje con frecuencia (you're / you’re / variantes).
        is_bot_check = ('sign in to confirm' in err_l and 'not a bot' in err_l) or ('use --cookies' in err_l)

        # Intentar siempre fallback para enlaces de YouTube antes de fallar.
        if 'youtube.com' in url or 'youtu.be' in url:
            fallback = download_with_pytubefix(url, user_id)
            if fallback.get('success'):
                return fallback

        if is_bot_check:
            return {
                'success': False,
                'message': 'No se pudo descargar esta canción ahora. Prueba otra opción.'
            }
        return {
            'success': False,
            'message': f'Error al descargar: {err}'
        }

# Rutas principales
@app.route('/')
def index():
    """Página de selección de usuario"""
    return render_template('select_user.html')

@app.route('/login')
def login_root():
    return redirect(url_for('index'))


@app.route('/forgot-password')
def forgot_password_root():
    return redirect(url_for('index'))


@app.route('/reset-bran')
def reset_bran():
    users = load_users()
    if 'bran' in users:
        users['bran']['password'] = None
        users['bran']['created'] = False
        save_users(users)
    return redirect(url_for('login', user_id='bran', msg='Contraseña de Bran eliminada. Crea una nueva.'))


@app.route('/login/<user_id>', methods=['GET', 'POST'])
def login(user_id):
    """Página de login para usuario específico"""
    users = load_users()

    if user_id not in users:
        return redirect(url_for('index'))

    user = users[user_id]

    if request.method == 'POST':
        password = request.form.get('password', '').strip()

        # Si el usuario no tiene contraseña creada
        if not user['created']:
            if not password:
                return render_template('login.html',
                                     user=user,
                                     user_id=user_id,
                                     error='Debes crear una contraseña',
                                     creating=True)

            # Crear contraseña segura para el usuario
            user['password'] = generate_password_hash(password)
            user['created'] = True
            save_users(users)
            session['user_id'] = user_id
            session['authenticated'] = True
            return redirect(url_for('dashboard'))

        # Verificar contraseña normal
        if check_password_hash(user['password'], password):
            session['user_id'] = user_id
            session['authenticated'] = True
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html',
                                 user=user,
                                 user_id=user_id,
                                 error='Contraseña incorrecta',
                                 creating=False)

    creating = not user['created']
    message = request.args.get('msg', '')
    return render_template('login.html', user=user, user_id=user_id, creating=creating, message=message)


@app.route('/forgot-password/<user_id>', methods=['GET', 'POST'])
def forgot_password(user_id):
    users = load_users()
    if user_id not in users:
        return redirect(url_for('index'))

    question = get_security_question(user_id)
    error = ''
    message = ''

    if request.method == 'POST':
        answer = request.form.get('secret_answer', '').strip()
        if validate_security_answer(user_id, answer):
            users[user_id]['password'] = None
            users[user_id]['created'] = False
            save_users(users)
            message = 'Respuesta correcta. Ya puedes crear una nueva contraseña en el login.'
        else:
            error = 'Respuesta de recuperación incorrecta. Intenta de nuevo.'

    return render_template('forgot_password.html', user_id=user_id, question=question, error=error, message=message)


@app.route('/logout')
def logout():
    """Cerrar sesión"""
    session.pop('authenticated', None)
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal del usuario"""
    user = get_current_user()
    songs = get_music_files()
    suggestions = get_suggestions_for_user(session['user_id'])
    playlists = load_playlists().get(session['user_id'], [])

    return render_template('index.html',
                         songs=songs,
                         user=user,
                         suggestions=suggestions,
                         playlists=playlists)

# APIs
@app.route('/api/songs')
@login_required
def get_songs():
    """API para obtener lista de canciones"""
    songs = get_music_files()
    return jsonify(songs)

@app.route('/api/download', methods=['POST'])
@login_required
def download():
    """API para descargar desde YouTube"""
    data = request.get_json()
    url = data.get('url', '').strip()
    legal_confirm = data.get('confirm_license', False)

    if SANDBOX_ONLY:
        return jsonify({'success': False, 'message': 'Modo sandbox activo: descargas de YouTube deshabilitadas.'}), 403

    if not url:
        return jsonify({'success': False, 'message': 'URL vacía'}), 400

    # Validación de licencia removida: usuario asume responsabilidad al usar la app
    # if not legal_confirm:
    #     return jsonify({'success': False, 'message': '...'}), 400

    dep_ok, dep_msg = check_runtime_dependencies()
    if not dep_ok:
        return jsonify({'success': False, 'message': dep_msg}), 500

    user_id = session.get('user_id')
    result = download_youtube_to_mp3(url, user_id)
    return jsonify(result)


@app.route('/api/upload', methods=['POST'])
@login_required
def upload_song():
    """Upload de MP3 local para modo sandbox y colección propia"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No se proporcionó archivo.'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Archivo inválido.'}), 400

    if not file.filename.lower().endswith('.mp3'):
        return jsonify({'success': False, 'message': 'Solo se permiten archivos MP3.'}), 400

    safe_name = os.path.basename(file.filename)
    destination = os.path.join(MUSIC_FOLDER, safe_name)

    if not os.path.abspath(destination).startswith(os.path.abspath(MUSIC_FOLDER)):
        return jsonify({'success': False, 'message': 'Acceso denegado'}), 403

    file.save(destination)

    users = load_users()
    user_id = session.get('user_id')
    if user_id in users:
        users[user_id]['downloads'].append({
            'title': os.path.splitext(safe_name)[0],
            'filename': safe_name,
            'url': 'local upload',
            'thumbnail': '',
            'duration': 0,
            'sentiment': 'neutral',
            'sentiment_emoji': '😐',
            'downloaded_at': datetime.now().isoformat(),
            'user_id': user_id
        })
        save_users(users)

    return jsonify({'success': True, 'message': 'Archivo subido correctamente.'})

@app.route('/api/delete', methods=['POST'])
@login_required
def delete_song():
    """API para eliminar una canción"""
    data = request.get_json()
    filename = data.get('filename', '')

    file_path = os.path.join(MUSIC_FOLDER, filename)

    # Validación de seguridad
    if not os.path.abspath(file_path).startswith(os.path.abspath(MUSIC_FOLDER)):
        return jsonify({'success': False, 'message': 'Acceso denegado'}), 403

    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({'success': True, 'message': 'Canción eliminada'})
        else:
            return jsonify({'success': False, 'message': 'Archivo no encontrado'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error al eliminar: {str(e)}'}), 500

@app.route('/api/play/<filename>')
@login_required
def play_song(filename):
    """Reproduce una canción"""
    file_path = os.path.join(MUSIC_FOLDER, filename)

    # Validación de seguridad
    if not os.path.abspath(file_path).startswith(os.path.abspath(MUSIC_FOLDER)):
        return 'Acceso denegado', 403

    if os.path.exists(file_path):
        return send_file(file_path, mimetype='audio/mpeg')
    return 'Archivo no encontrado', 404

@app.route('/api/download-file/<filename>')
@login_required
def download_file(filename):
    """Descarga una canción al PC"""
    file_path = os.path.join(MUSIC_FOLDER, filename)

    # Validación de seguridad
    if not os.path.abspath(file_path).startswith(os.path.abspath(MUSIC_FOLDER)):
        return 'Acceso denegado', 403

    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=filename)
    return 'Archivo no encontrado', 404

@app.route('/api/song-info/<filename>')
@login_required
def get_song_info(filename):
    """API para obtener información detallada de una canción"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    # Buscar la canción en las descargas del usuario
    for download in user['downloads']:
        if download['filename'] == filename:
            return jsonify({
                'title': download['title'],
                'thumbnail': download.get('thumbnail', ''),
                'sentiment': download.get('sentiment', 'neutral'),
                'sentiment_emoji': download.get('sentiment_emoji', '😐'),
                'duration': download.get('duration', 0),
                'downloaded_at': download.get('downloaded_at', ''),
                'url': download.get('url', '')
            })
    
    return jsonify({'error': 'Canción no encontrada'}), 404

@app.route('/api/update-metadata', methods=['POST'])
@login_required
def update_metadata():
    """API para editar metadatos d euna canción"""
    data = request.get_json()
    filename = data.get('filename', '')
    title = data.get('title', '')
    artist = data.get('artist', '')
    album = data.get('album', '')

    if not filename:
        return jsonify({'success': False, 'message': 'Nombre de archivo requerido'}), 400

    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404

    # actualizar en la lista de descargas del usuario
    users = load_users()
    current = users.get(session['user_id'], {})
    updated = False
    for download in current.get('downloads', []):
        if download['filename'] == filename:
            if title:
                download['title'] = title
            if artist:
                download['artist'] = artist
            if album:
                download['album'] = album
            updated = True
            break

    if not updated:
        return jsonify({'success': False, 'message': 'Canción no encontrada'}), 404

    save_users(users)
    return jsonify({'success': True, 'message': 'Metadatos actualizados'})

@app.route('/api/playlists')
@login_required
def get_playlists():
    """Devuelve las playlists del usuario actual"""
    user_id = session.get('user_id')
    playlists = load_playlists().get(user_id, [])
    return jsonify(playlists)

@app.route('/api/playlist', methods=['POST'])
@login_required
def create_playlist():
    data = request.get_json()
    name = data.get('name', '').strip()
    user_id = session.get('user_id')

    if not name:
        return jsonify({'success': False, 'message': 'Nombre de playlist requerido'}), 400

    playlists = load_playlists()
    user_playlists = playlists.get(user_id, [])
    if any(pl['name'] == name for pl in user_playlists):
        return jsonify({'success': False, 'message': 'Playlist ya existe'}), 400

    user_playlists.append({'name': name, 'songs': []})
    playlists[user_id] = user_playlists
    save_playlists(playlists)
    return jsonify({'success': True, 'message': 'Playlist creada'})

@app.route('/api/playlist/add', methods=['POST'])
@login_required
def add_to_playlist():
    data = request.get_json()
    playlist_name = data.get('playlist_name', '').strip()
    filename = data.get('filename', '').strip()
    user_id = session.get('user_id')

    if not playlist_name or not filename:
        return jsonify({'success': False, 'message': 'Datos incompletos'}), 400

    playlists = load_playlists()
    user_playlists = playlists.get(user_id, [])
    for pl in user_playlists:
        if pl['name'] == playlist_name:
            if filename not in pl['songs']:
                pl['songs'].append(filename)
                save_playlists(playlists)
                return jsonify({'success': True, 'message': 'Canción agregada'})
            else:
                return jsonify({'success': False, 'message': 'Canción ya en playlist'}), 400
    return jsonify({'success': False, 'message': 'Playlist no encontrada'}), 404

@app.route('/api/search', methods=['GET'])
@login_required
def search_youtube():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'success': False, 'message': 'Consulta vacía'}), 400

    results = []

    # Busqueda principal: mas estable que yt-dlp para consultas de texto.
    if VideosSearch is not None:
        try:
            search = VideosSearch(query, limit=10)
            for item in search.result().get('result', []):
                duration_text = item.get('duration') or ''
                duration = duration_to_seconds(duration_text)

                video_id = item.get('id', '')
                results.append({
                    'id': video_id,
                    'title': item.get('title'),
                    'url': f"https://www.youtube.com/watch?v={video_id}" if video_id else item.get('link', ''),
                    'duration': duration,
                    'thumbnail': (item.get('thumbnails') or [{}])[0].get('url', '')
                })

            if results:
                return jsonify({'success': True, 'results': results})
        except Exception as e:
            app.logger.warning(f'Fallback a yt-dlp para search: {e}')

    # Fallback: yt-dlp si la libreria principal no esta disponible.
    if yt_dlp is None:
        return jsonify({'success': False, 'message': 'No se pudo buscar en este momento. Reintenta en unos segundos.'}), 500

    try:
        query_url = f"ytsearch10:{query}"
        ydl_opts = {
            'quiet': True,
            'simulate': True,
            'skip_download': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            },
            'socket_timeout': 30,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query_url, download=False)
            for entry in info.get('entries', []):
                results.append({
                    'id': entry.get('id'),
                    'title': entry.get('title'),
                    'url': entry.get('webpage_url'),
                    'duration': entry.get('duration'),
                    'thumbnail': entry.get('thumbnail')
                })

        if results:
            return jsonify({'success': True, 'results': results})
    except Exception as e:
        app.logger.warning(f'Fallback a parser HTML para search: {e}')

    html_results = search_youtube_html(query, limit=10)
    if html_results:
        return jsonify({'success': True, 'results': html_results})

    return jsonify({'success': False, 'message': 'Error al buscar en YouTube. Intenta con otra palabra clave.'}), 502

@app.route('/api/suggest-download', methods=['POST'])
@login_required
def suggest_download():
    """API para descargar una sugerencia"""
    data = request.get_json()
    suggestion_title = data.get('title', '')
    suggestion_url = data.get('url', '')

    if not suggestion_url:
        return jsonify({'success': False, 'message': 'URL de sugerencia vacía'}), 400

    user_id = session.get('user_id')
    result = download_youtube_to_mp3(suggestion_url, user_id)
    return jsonify(result)


@app.route('/health')
def health():
    """Health endpoint for uptime checks and hosting probes."""
    return jsonify({'status': 'ok'}), 200


@app.route('/download-apk')
def download_apk():
    """Descarga el APK de Brauti (si existe en /static)"""
    apk_path = os.path.join(os.path.dirname(__file__), 'static', 'brauti.apk')
    if os.path.exists(apk_path):
        return send_file(apk_path, as_attachment=True, download_name='brauti.apk')
    return jsonify({'success': False, 'message': 'APK no disponible'}), 404


def run_app():
    if ngrok is not None and os.environ.get('FLASK_ENV') != 'production':
        thread = threading.Thread(target=maintain_ngrok, daemon=True)
        thread.start()

    app.run(
        debug=os.environ.get('FLASK_ENV') != 'production',
        host='0.0.0.0',
        port=int(os.environ.get('PORT', '5000')),
        use_reloader=False
    )


if __name__ == '__main__':
    run_app()