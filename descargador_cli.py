#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Descargador de YouTube a MP3 - Versión CLI (Línea de Comandos)
Simple y rápido para descargar canciones desde YouTube
"""

import os
import sys
import json
import yt_dlp
from pathlib import Path
from datetime import datetime

# Colores para la terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header():
    """Mostrar encabezado"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*50}")
    print("🎵 DESCARGADOR DE YOUTUBE A MP3")
    print(f"{'='*50}{Colors.ENDC}\n")

def print_menu():
    """Mostrar menú principal"""
    print(f"{Colors.BOLD}Opciones:{Colors.ENDC}")
    print("1. Descargar una canción")
    print("2. Descarga en lote desde lista de URLs")
    print("3. Buscar en YouTube desde CLI")
    print("4. Editar metadatos de una canción")
    print("5. Crear/Ver playlists")
    print("6. Ver canciones descargadas")
    print("7. Sincronizar con teléfono (mostrar IP y modo móvil)")
    print("8. Eliminar una canción")
    print("9. Salir")
    print()

def setup_folders():
    """Crear carpetas necesarias"""
    music_folder = os.path.join(os.path.dirname(__file__), 'descargas')
    os.makedirs(music_folder, exist_ok=True)
    return music_folder

def get_music_files(music_folder):
    """Obtener lista de archivos MP3"""
    files = []
    if os.path.exists(music_folder):
        for i, file in enumerate(sorted(os.listdir(music_folder)), 1):
            if file.endswith('.mp3'):
                file_path = os.path.join(music_folder, file)
                size = os.path.getsize(file_path) / (1024 * 1024)
                files.append({
                    'id': i,
                    'name': file,
                    'size': size,
                    'path': file_path
                })
    return files

def download_youtube_mp3(url, music_folder):
    """Descargar video de YouTube como MP3"""
    try:
        print(f"\n{Colors.OKCYAN}Procesando URL...{Colors.ENDC}")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(music_folder, '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'progress_hooks': [progress_hook],
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"{Colors.OKCYAN}Descargando...{Colors.ENDC}")
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Desconocida')
            
            print(f"\n{Colors.OKGREEN}✓ Descarga completada!{Colors.ENDC}")
            print(f"{Colors.BOLD}Canción: {title}{Colors.ENDC}")
            return True
            
    except Exception as e:
        print(f"{Colors.FAIL}✗ Error: {str(e)}{Colors.ENDC}")
        return False

def progress_hook(d):
    """Hook para mostrar progreso de descarga"""
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', 'N/A')
        speed = d.get('_speed_str', 'N/A')
        eta = d.get('_eta_str', 'N/A')
        print(f"\r{Colors.OKCYAN}{percent} a {speed} (ETA: {eta}){Colors.ENDC}", end='', flush=True)
    elif d['status'] == 'finished':
        print(f"\r{Colors.OKGREEN}Descarga finalizada - Convirtiendo a MP3...{Colors.ENDC}")

def show_songs(music_folder):
    """Mostrar lista de canciones descargadas"""
    files = get_music_files(music_folder)
    
    if not files:
        print(f"\n{Colors.WARNING}No hay canciones descargadas aún.{Colors.ENDC}\n")
        return
    
    print(f"\n{Colors.BOLD}Canciones descargadas ({len(files)}):{Colors.ENDC}\n")
    
    total_size = 0
    for file in files:
        total_size += file['size']
        print(f"{Colors.OKCYAN}{file['id']:2d}.{Colors.ENDC} {file['name']:<50} {Colors.OKBLUE}{file['size']:>8.2f} MB{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}Tamaño total: {total_size:.2f} MB{Colors.ENDC}\n")

def batch_download(music_folder):
    """Descarga en lote desde un archivo con URLs"""
    file_path = input(f"{Colors.BOLD}Ruta del archivo de URLs (una por línea): {Colors.ENDC}").strip()
    if not os.path.exists(file_path):
        print(f"{Colors.FAIL}Archivo no encontrado.{Colors.ENDC}\n")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        urls = [l.strip() for l in f if l.strip()]

    total = len(urls)
    print(f"{Colors.OKGREEN}Iniciando descarga de {total} URLs...{Colors.ENDC}")
    for i, url in enumerate(urls, 1):
        print(f"{Colors.OKBLUE}[{i}/{total}] Descargando: {url}{Colors.ENDC}")
        download_youtube_mp3(url, music_folder)
    print(f"{Colors.OKGREEN}Descarga en lote completada.{Colors.ENDC}\n")


def search_youtube_cli(music_folder):
    query = input(f"{Colors.BOLD}Consulta para buscar en YouTube: {Colors.ENDC}").strip()
    if not query:
        return

    try:
        ydl_opts = {'quiet': True, 'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(f"ytsearch10:{query}", download=False)
            entries = result.get('entries', []) if result else []
            for idx, entry in enumerate(entries, 1):
                url = entry.get('webpage_url')
                title = entry.get('title')
                duration = entry.get('duration', 0)
                print(f"[{idx}] {title} ({duration//60}:{str(duration%60).zfill(2)}) - {url}")

            choice = input(f"{Colors.BOLD}Ingresa el número para descargar (0 cancelar): {Colors.ENDC}").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(entries):
                selected = entries[int(choice)-1]
                download_youtube_mp3(selected.get('webpage_url'), music_folder)
    except Exception as e:
        print(f"{Colors.FAIL}Error en búsqueda: {str(e)}{Colors.ENDC}\n")


def edit_metadata(music_folder):
    files = get_music_files(music_folder)
    if not files:
        print(f"{Colors.WARNING}No hay canciones para editar.{Colors.ENDC}\n")
        return

    for i, file in enumerate(files, 1):
        print(f"{i}. {file['name']}")

    choice = input(f"{Colors.BOLD}Número de canción a editar (0 cancelar): {Colors.ENDC}").strip()
    if not choice.isdigit() or int(choice) < 1 or int(choice) > len(files):
        return

    selected = files[int(choice) - 1]
    title = input(f"{Colors.BOLD}Nuevo título (deja vacío para no cambiar): {Colors.ENDC}").strip()
    artist = input(f"{Colors.BOLD}Artista (deja vacío para no cambiar): {Colors.ENDC}").strip()
    album = input(f"{Colors.BOLD}Álbum (deja vacío para no cambiar): {Colors.ENDC}").strip()

    # Simular guardado local en archivo metadata
    meta_file = os.path.join(music_folder, 'metadata.json')
    metadata = {}
    if os.path.exists(meta_file):
        with open(meta_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

    meta_data = metadata.get(selected['name'], {})
    if title: meta_data['title'] = title
    if artist: meta_data['artist'] = artist
    if album: meta_data['album'] = album
    metadata[selected['name']] = meta_data

    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)

    print(f"{Colors.OKGREEN}Metadatos actualizados para {selected['name']}{Colors.ENDC}\n")


def loadPlaylists(music_folder):
    playlist_file = os.path.join(music_folder, 'playlists.json')
    playlists = {}
    if os.path.exists(playlist_file):
        with open(playlist_file, 'r', encoding='utf-8') as f:
            playlists = json.load(f)

    if not playlists:
        print(f"{Colors.WARNING}No hay playlists creadas aún.{Colors.ENDC}\n")
        return

    print(f"\n{Colors.BOLD}Playlists:{Colors.ENDC}")
    for name, songs in playlists.items():
        print(f"- {name} (canciones: {len(songs)})")
    print('')

    action = input(f"{Colors.BOLD}Escribe el nombre de la playlist para agregar canción o ENTER para salir: {Colors.ENDC}").strip()
    if not action or action not in playlists:
        return

    file = input(f"{Colors.BOLD}Nombre de archivo MP3 para agregar en playlist '{action}': {Colors.ENDC}").strip()
    if not file:
        return

    if file not in playlists[action]:
        playlists[action].append(file)
        with open(playlist_file, 'w', encoding='utf-8') as f:
            json.dump(playlists, f, indent=4, ensure_ascii=False)
        print(f"{Colors.OKGREEN}Añadido a playlist{Colors.ENDC}\n")
    else:
        print(f"{Colors.WARNING}La canción ya está en la playlist.{Colors.ENDC}\n")


def sync_info():
    import socket
    host = socket.gethostname()
    ip = socket.gethostbyname(host)
    print(f"{Colors.OKGREEN}Tu app brauti está disponible en: http://{ip}:5000{Colors.ENDC}")
    print(f"Abre esta dirección en tu teléfono con la misma red Wi-Fi.")


def delete_song(music_folder):
    """Eliminar una canción"""
    files = get_music_files(music_folder)
    
    if not files:
        print(f"\n{Colors.WARNING}No hay canciones para eliminar.{Colors.ENDC}\n")
        return
    
    show_songs(music_folder)
    
    try:
        choice = input(f"{Colors.BOLD}Ingresa el número de la canción a eliminar (0 para cancelar): {Colors.ENDC}")
        choice = int(choice)
        
        if choice == 0:
            print(f"{Colors.OKBLUE}Cancelado.{Colors.ENDC}\n")
            return
        
        if 1 <= choice <= len(files):
            file = files[choice - 1]
            confirm = input(f"{Colors.WARNING}¿Estás seguro de que quieres eliminar '{file['name']}'? (s/n): {Colors.ENDC}")
            
            if confirm.lower() == 's':
                os.remove(file['path'])
                print(f"{Colors.OKGREEN}✓ Canción eliminada.{Colors.ENDC}\n")
            else:
                print(f"{Colors.OKBLUE}Cancelado.{Colors.ENDC}\n")
        else:
            print(f"{Colors.FAIL}✗ Opción inválida.{Colors.ENDC}\n")
    
    except ValueError:
        print(f"{Colors.FAIL}✗ Por favor ingresa un número válido.{Colors.ENDC}\n")

def main():
    """Función principal"""
    print_header()
    music_folder = setup_folders()
    
    print(f"{Colors.OKGREEN}✓ Carpeta de descargas: {music_folder}{Colors.ENDC}\n")
    
    while True:
        print_menu()
        choice = input(f"{Colors.BOLD}Elige una opción (1-4): {Colors.ENDC}").strip()
        
        if choice == '1':
            url = input(f"\n{Colors.BOLD}Pega el enlace de YouTube: {Colors.ENDC}").strip()
            if url:
                download_youtube_mp3(url, music_folder)
            else:
                print(f"{Colors.FAIL}✗ URL vacía.{Colors.ENDC}\n")

        elif choice == '2':
            batch_download(music_folder)

        elif choice == '3':
            search_youtube_cli(music_folder)

        elif choice == '4':
            edit_metadata(music_folder)

        elif choice == '5':
            print(f"{Colors.OKCYAN}Cargando playlists...{Colors.ENDC}\n")
            loadPlaylists(music_folder)

        elif choice == '6':
            show_songs(music_folder)

        elif choice == '7':
            sync_info()

        elif choice == '8':
            delete_song(music_folder)

        elif choice == '9':
            print(f"{Colors.WARNING}¡Hasta luego!{Colors.ENDC}\n")
            sys.exit(0)
        
        else:
            print(f"{Colors.FAIL}✗ Opción inválida. Por favor intenta de nuevo.{Colors.ENDC}\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Programa interrumpido.{Colors.ENDC}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.FAIL}Error inesperado: {str(e)}{Colors.ENDC}\n")
        sys.exit(1)
