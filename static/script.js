// Elementos del DOM
const urlInput = document.getElementById('urlInput');
const downloadBtn = document.getElementById('downloadBtn');
const statusMessage = document.getElementById('statusMessage');
const progressBar = document.getElementById('progressBar');
const songsList = document.getElementById('songsList');
const songCount = document.getElementById('songCount');
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const searchResults = document.getElementById('searchResults');
const playlistInput = document.getElementById('playlistInput');
const createPlaylistBtn = document.getElementById('createPlaylistBtn');
const playlistsContainer = document.getElementById('playlistsContainer');
const toastContainer = document.getElementById('toastContainer');
const installBtn = document.getElementById('installBtn');

let deferredPrompt = null;

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    if (installBtn) {
        installBtn.classList.remove('hidden');
    }
    showToast('Brauti está listo para instalarse como app (instala desde aquí).', 'success', 8000);
});

if (installBtn) {
    installBtn.addEventListener('click', async () => {
        if (!deferredPrompt) return;
        deferredPrompt.prompt();
        const choiceResult = await deferredPrompt.userChoice;
        if (choiceResult.outcome === 'accepted') {
            showToast('Instalación iniciada con éxito.', 'success', 5000);
        } else {
            showToast('Instalación cancelada.', 'error', 5000);
        }
        deferredPrompt = null;
        installBtn.classList.add('hidden');
    });
}

// Cargar canciones al iniciar
document.addEventListener('DOMContentLoaded', () => {
    loadSongs();
    loadPlaylists();
    
    // Eventos
    downloadBtn.addEventListener('click', handleDownload);
    urlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleDownload();
    });

    searchBtn.addEventListener('click', handleSearch);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSearch();
    });

    createPlaylistBtn.addEventListener('click', createPlaylist);

});

// Cargar lista de canciones
async function loadSongs() {
    try {
        const response = await fetch('/api/songs');
        const songs = await response.json();
        
        songCount.textContent = songs.length;
        
        if (songs.length === 0) {
            songsList.innerHTML = '<p class="empty-message">No hay canciones descargadas aún</p>';
            return;
        }
        
        songsList.innerHTML = songs.map(song => createSongCard(song)).join('');
        
        // Agregar event listeners a los botones
        document.querySelectorAll('.btn-delete').forEach(btn => {
            btn.addEventListener('click', (e) => deleteSong(e.target.dataset.filename));
        });
        
        document.querySelectorAll('.btn-play').forEach(btn => {
            btn.addEventListener('click', (e) => playSong(e.target.dataset.filename));
        });
        
        document.querySelectorAll('.btn-download').forEach(btn => {
            btn.addEventListener('click', (e) => downloadSong(e.target.dataset.filename));
        });

        document.querySelectorAll('.btn-add-playlist').forEach(btn => {
            btn.addEventListener('click', (e) => addSongToPlaylist(e.target.dataset.filename));
        });
    } catch (error) {
        showMessage('Error al cargar las canciones', 'error');
        console.error('Error:', error);
    }
}

// Crear tarjeta de canción
function createSongCard(song) {
    const fileName = song.name.replace(/\.mp3$/, '');
    return `
        <div class="song-card">
            <div class="song-title" title="${fileName}">
                <i class="fas fa-music"></i> ${fileName}
            </div>
            <div class="song-size">
                <i class="fas fa-database"></i> ${song.size}
            </div>
            <div class="song-actions">
                <button class="btn btn-success btn-play" data-filename="${song.name}" title="Reproducir">
                    <i class="fas fa-play"></i> Escuchar
                </button>
                <button class="btn btn-info btn-add-playlist" data-filename="${song.name}" title="Agregar a playlist">
                    <i class="fas fa-list"></i> Agregar a Playlist
                </button>
                <button class="btn btn-download btn-download" data-filename="${song.name}" title="Descargar">
                    <i class="fas fa-cloud-download-alt"></i> Descargar
                </button>
                <button class="btn btn-danger btn-delete" data-filename="${song.name}" title="Eliminar">
                    <i class="fas fa-trash"></i> Eliminar
                </button>
            </div>
        </div>
    `;
}

// Descargar de YouTube
async function handleDownload() {
    const url = urlInput.value.trim();
    
    if (!url) {
        showMessage('Por favor ingresa una URL de YouTube', 'error');
        urlInput.focus();
        return;
    }
    
    downloadBtn.disabled = true;
    showMessage('Descargando... esto puede tomar un momento', 'loading');
    showProgressBar();
    
    try {
        const response = await fetch('/api/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url })
        });

        const data = await response.json().catch(() => ({ success: false, message: 'Respuesta inválida del servidor' }));
        
        if (data.success) {
            showMessage(`✓ ${data.message}`, 'success');
            urlInput.value = '';
            setTimeout(() => {
                loadSongs();
                hideProgressBar();
            }, 1000);
        } else {
            showMessage(`✗ ${data.message}`, 'error');
            hideProgressBar();
        }
    } catch (error) {
        showMessage(`✗ Error en la descarga: ${error.message}`, 'error');
        hideProgressBar();
        console.error('Error:', error);
    } finally {
        downloadBtn.disabled = false;
    }
}

// Eliminar canción
async function deleteSong(filename) {
    if (!confirm(`¿Estás seguro de que quieres eliminar "${filename.replace(/\.mp3$/, '')}"?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ filename })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('✓ Canción eliminada', 'success');
            setTimeout(() => loadSongs(), 500);
        } else {
            showMessage(`✗ ${data.message}`, 'error');
        }
    } catch (error) {
        showMessage(`✗ Error al eliminar: ${error.message}`, 'error');
        console.error('Error:', error);
    }
}

// Reproducir canción
async function playSong(filename) {
    try {
        // Obtener información de la canción
        const response = await fetch(`/api/song-info/${filename}`);
        const songData = await response.json();
        
        if (songData.error) {
            showMessage('Error al obtener información de la canción', 'error');
            return;
        }
        
        // Mostrar modal con información
        showSongModal(songData);
        
        // Reproducir la canción
        const audio = new Audio(`/api/play/${filename}`);
        audio.play().catch(error => {
            showMessage('✗ Error al reproducir la canción', 'error');
            console.error('Error:', error);
        });
        
    } catch (error) {
        showMessage('✗ Error al cargar información de la canción', 'error');
        console.error('Error:', error);
    }
}

// Descargar canción
function downloadSong(filename) {
    const link = document.createElement('a');
    link.href = `/api/download-file/${filename}`;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Mostrar mensaje
function showToast(message, type = 'success', duration = 4000) {
    if (!toastContainer) return;
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${message}</span><button aria-label='Cerrar'>×</button>`;

    const closeBtn = toast.querySelector('button');
    closeBtn.addEventListener('click', () => {
        toast.remove();
    });

    toastContainer.appendChild(toast);

    if (duration > 0) {
        setTimeout(() => {
            toast.remove();
        }, duration);
    }
}

function showMessage(message, type) {
    if (statusMessage) {
        statusMessage.textContent = message;
        statusMessage.className = `status-message ${type}`;
        statusMessage.classList.remove('hidden');
    }
    showToast(message, type, 5000);
}

// Mostrar/ocultar barra de progreso
function showProgressBar() {
    if (progressBar) {
        progressBar.classList.remove('hidden');
    }
}

function hideProgressBar() {
    if (progressBar) {
        progressBar.classList.add('hidden');
    }
}

// Descargar sugerencia
async function downloadSuggestion(title, url) {
    if (!confirm(`¿Quieres descargar "${title}"?`)) {
        return;
    }
    
    // Mostrar progreso
    showMessage('Descargando sugerencia...', 'loading');
    showProgressBar();
    
    try {
        const response = await fetch('/api/suggest-download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ title, url })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(`✓ ${data.message}`, 'success');
            setTimeout(() => {
                loadSongs();
                hideProgressBar();
                // Recargar la página para actualizar sugerencias
                location.reload();
            }, 1000);
        } else {
            showMessage(`✗ ${data.message}`, 'error');
            hideProgressBar();
        }
    } catch (error) {
        showMessage(`✗ Error al descargar sugerencia: ${error.message}`, 'error');
        hideProgressBar();
        console.error('Error:', error);
    }
}

async function handleSearch() {
    const query = searchInput.value.trim();
    if (!query) {
        showMessage('Escribe un término para buscar', 'error');
        return;
    }

    try {
        showMessage('Buscando canciones...', 'loading');
        const resp = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const data = await resp.json().catch(() => ({ success: false, message: 'Respuesta inválida del servidor' }));

        if (!resp.ok) {
            showMessage(data.message || 'Error en búsqueda', 'error');
            return;
        }

        if (!data.success) {
            showMessage(data.message || 'Error en búsqueda', 'error');
            return;
        }

        renderSearchResults(data.results);
        showMessage('Resultados actualizados', 'success');
    } catch (error) {
        showMessage('Error al buscar canciones. Reintenta en unos segundos.', 'error');
        console.error('Error:', error);
    }
}

function renderSearchResults(results) {
    if (!results.length) {
        searchResults.innerHTML = '<p class="empty-message">No se encontraron resultados</p>';
        return;
    }

    searchResults.innerHTML = results.map((r, idx) => `
        <div class="song-card">
            <div class="song-title" title="${r.title}"><i class="fas fa-search"></i> ${r.title}</div>
            <div class="song-size">Duración: ${r.duration ? `${Math.floor(r.duration/60)}:${(r.duration%60).toString().padStart(2,'0')}` : 'Desconocida'}</div>
            <div class="song-actions">
                <button class="btn btn-primary" onclick="downloadSuggestion('${r.title.replace(/'/g, "\\'")}', '${r.url}')">
                    <i class="fas fa-download"></i> Descargar
                </button>
            </div>
        </div>
    `).join('');

    animateCards('#searchResults .song-card');
}

async function createPlaylist() {
    const name = playlistInput.value.trim();
    if (!name) {
        showMessage('Ingresa el nombre de la playlist', 'error');
        return;
    }

    try {
        const resp = await fetch('/api/playlist', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name})
        });
        const data = await resp.json();

        if (!data.success) {
            showMessage(data.message, 'error');
            return;
        }

        playlistInput.value = '';
        showMessage('Playlist creada', 'success');
        loadPlaylists();
    } catch (error) {
        showMessage('Error al crear playlist', 'error');
        console.error('Error:', error);
    }
}

async function loadPlaylists() {
    try {
        const resp = await fetch('/api/playlists');
        const list = await resp.json();

        if (!list.length) {
            playlistsContainer.innerHTML = '<p class="empty-message">No hay playlists aún</p>';
            return;
        }

        playlistsContainer.innerHTML = list.map(pl => `
            <div class="playlist-card">
                <h3>${pl.name}</h3>
                <p>Songs: ${pl.songs.length}</p>
                <button class="trash" onclick="deletePlaylist('${pl.name}')">Eliminar Playlist</button>
                ${pl.songs.map(song => `<div class="song-item">${song} <button class='btn btn-success' onclick='playSong("${song}")'>Reproducir</button></div>`).join('')}
            </div>
        `).join('');
        animateCards('#playlistsContainer .playlist-card');
    } catch (error) {
        showMessage('Error al cargar playlists', 'error');
        console.error('Error:', error);
    }
}

async function deletePlaylist(name) {
    // no implementado en backend (puede agregarse), por ahora solo recarga.
    showMessage('Funcionalidad de eliminar playlist (próximamente)', 'loading');
}

async function addSongToPlaylist(filename) {
    const playlistName = prompt('Ingresa el nombre de la playlist donde agregar la canción:');
    if (!playlistName) {
        return;
    }

    try {
        const resp = await fetch('/api/playlist/add', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({playlist_name: playlistName, filename})
        });
        const data = await resp.json();

        if (!data.success) {
            showMessage(data.message, 'error');
            return;
        }

        showMessage('Canción agregada a playlist', 'success');
        loadPlaylists();
    } catch (err) {
        showMessage('Error al agregar a playlist', 'error');
    }
}

// Mostrar modal de canción
function showSongModal(songData) {
    document.getElementById('songTitle').textContent = songData.title;
    document.getElementById('songThumbnail').src = songData.thumbnail || '/static/default-album.png';
    document.getElementById('sentimentEmoji').textContent = songData.sentiment_emoji;
    document.getElementById('sentimentText').textContent = songData.sentiment;
    
    // Formatear duración
    const duration = songData.duration || 0;
    const minutes = Math.floor(duration / 60);
    const seconds = duration % 60;
    document.getElementById('songDuration').textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    
    // Formatear fecha
    if (songData.downloaded_at) {
        const date = new Date(songData.downloaded_at);
        document.getElementById('songDate').textContent = date.toLocaleDateString();
    }
    
    document.getElementById('songModal').classList.remove('hidden');
}

// Cerrar modal de canción
function closeSongModal() {
    document.getElementById('songModal').classList.add('hidden');
}

function animateCards(selector) {
    const cards = document.querySelectorAll(selector);
    cards.forEach((card, idx) => {
        card.style.animationDelay = `${Math.min(idx * 60, 420)}ms`;
        card.classList.add('reveal');
    });
}
