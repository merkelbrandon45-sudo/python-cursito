from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
import yt_dlp
import os
from pathlib import Path
import threading
from functools import wraps

import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'descargador_youtube_mp3_2024'

# Configuración de usuarios
USERS_FILE = os.path.join(os.path.dirname(__file__), 'users.json')

# Usuario principal (ya existe)
DEFAULT_USERS = {
    'usuario_principal': {
        'password': '48695973Bm',
        'name': 'Usuario Principal',
        'downloads': [],
        'created': True
    },
    'usuario_amigo': {
        'password': None,  # Se crea la primera vez
        'name': 'Usuario Amigo',
        'downloads': [],
        'created': False
    }
}

def load_users():
    """Carga los usuarios desde el archivo JSON"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return DEFAULT_USERS.copy()

def save_users(users):
    """Guarda los usuarios en el archivo JSON"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

def get_current_user():
    """Obtiene el usuario actual de la sesión"""
    if 'user_id' in session:
        users = load_users()
        return users.get(session['user_id'])
    return None

def get_suggestions_for_user(user_id):
    """Obtiene sugerencias de canciones del otro usuario"""
    users = load_users()
    suggestions = []
    
    # Si es usuario_amigo, mostrar descargas del usuario_principal
    if user_id == 'usuario_amigo':
        principal_downloads = users.get('usuario_principal', {}).get('downloads', [])
        suggestions = principal_downloads[-10:]  # Últimas 10 descargas
    
    # Si es usuario_principal, mostrar descargas del usuario_amigo (si tiene)
    elif user_id == 'usuario_principal':
        amigo_downloads = users.get('usuario_amigo', {}).get('downloads', [])
        suggestions = amigo_downloads[-10:]  # Últimas 10 descargas
    
    return suggestions

# Carpeta donde se guardarán las canciones
MUSIC_FOLDER = os.path.join(os.path.dirname(__file__), 'descargas')
os.makedirs(MUSIC_FOLDER, exist_ok=True)

# Decorador para proteger rutas
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'authenticated' not in session or not session['authenticated']:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

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

def download_youtube_to_mp3(url, progress_callback=None):
    """Descarga un video de YouTube como MP3"""
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
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return {
                'success': True,
                'filename': os.path.basename(filename.replace('.webm', '.mp3').replace('.m4a', '.mp3')),
                'message': f"Canción descargada: {info.get('title', 'Desconocida')}"
            }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error al descargar: {str(e)}'
        }

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if request.method == 'POST':
        password = request.form.get('password', '')
        
        if password == APP_PASSWORD:
            session['authenticated'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Contraseña incorrecta', password_entered=password)
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Cerrar sesión"""
    session.pop('authenticated', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Página principal"""
    songs = get_music_files()
    return render_template('index.html', songs=songs)

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
    
    if not url:
        return jsonify({'success': False, 'message': 'URL vacía'}), 400
    
    result = download_youtube_to_mp3(url)
    return jsonify(result)

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

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
