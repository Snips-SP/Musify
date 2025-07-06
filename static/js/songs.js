import { socket } from './socket.js';
import { flashMessage } from './animations.js';
import { queuePlaylist } from './playlists.js';

const songNameIpt = document.getElementById('songNameIpt');
const artistNameIpt = document.getElementById('artistNameIpt');
const songFileIpt = document.getElementById('songFileIpt');
const playlistSelectIpt = document.getElementById('playlistSelectIpt');
const addSongToPlaylistModel = document.getElementById('addSongModal')
const addSongToPlaylistBtn = document.getElementById('addSongToPlaylistBtn')


// Public function to manually create a post-request to create song-endpoint
window.createSong = async function createSong() {
    const song_name = songNameIpt.value.trim();
    const artist_name = artistNameIpt.value.trim();
    const file = songFileIpt.files[0];

    if (!song_name) {
        flashMessage('Song name cannot be empty.', 'error');
        return;
    }
    if (!artist_name) {
        flashMessage('Artist name cannot be empty.', 'error');
        return;
    }
    if (!file) {
        flashMessage('Please select a song file.', 'error');
        return;
    }

    // Prepare FormData for file upload
    const formData = new FormData();
    formData.append('song_name', song_name);
    formData.append('artist', artist_name);
    formData.append('song_file', file);

    try {
        const response = await fetch('/songs/create_song', {
            method: 'POST',
            body: formData,
        });

        if (response.ok) {
            // Parse JSON from the response
            const data = await response.json();
            const song = data.song;

            // Clone the template
            const template = document.getElementById('song-template');
            const new_song = template.content.cloneNode(true);

            // Update the article class to "song"
            const article = new_song.querySelector('article');
            article.dataset.id = song.id;

            // Fill in the placeholder and onchange handlers
            // Song Title
            const song_title_text_ipt = new_song.querySelector('#songTitleTextIpt');
            song_title_text_ipt.value = song.name;
            song_title_text_ipt.onchange = function() {
                updateSongName(song.id, this.value);
            };
            // Song Artist
            const song_artist_text_ipt = new_song.querySelector('#artistNameTextIpt');
            song_artist_text_ipt.value = song.artist;
            song_artist_text_ipt.onchange = function() {
                updateArtistName(song.id, this.value);
            };

            // File input
            const song_file_ipt = new_song.querySelector('#songFileIpt');
            // TODO: CHANGE SONG FILE UPLOAD
            //song_file_ipt.onchange = () =>

            // Add onclick handler to buttons
            new_song.querySelector('#addToPlaylistBtn').onclick = () => openAddToPlaylist(song.id);
            new_song.querySelector('#deleteSongBtn').onclick = () => deleteSong(song.id);

            // Append to the ul within the user_songs section
            const userSongsDiv = document.getElementById('user_songs');
            userSongsDiv.appendChild(new_song);

            // Clear the input fields
            songNameIpt.value = '';
            artistNameIpt.value = '';
            songFileIpt.value = '';

            flashMessage(data.message, 'success');
        } else {
            const data = await response.json();
            flashMessage(data.message, 'error');
        }
    } catch (err) {
        console.error(err);
        flashMessage('An error occurred. Please try again.', 'error');
    }
}


window.deleteSong = function deleteSong(song_id) {
    // Send to backend via socket and wait for backend success code
    socket.emit('delete_song', {song_id}, (response) => {
        flashMessage(response.message, response.success ? 'success' : 'error');
    });
}

// Remove song from DOM when it is removed from the database
socket.on('song_removed', song => {
    // Removes ALL instances of the song in library menu
    document.querySelectorAll(`article.song[data-id="${song.id}"]`).forEach(el => el.remove());
    // Removes ALL instances of the song from any playlist (library and homepage)
    document.querySelectorAll(`article.song_in_playlist[data-id="${song.id}"]`).forEach(el => el.remove());
});


window.removeSongFromPlaylist = function removeSongFromPlaylist(playlist_id, song_id) {
    socket.emit('delete_song_from_playlist', {playlist_id, song_id}, (response) => {
        flashMessage(response.message, response.success ? 'success' : 'error');
    });
}

socket.on('song_removed_from_playlist', payload => {
    // Remove the song from a specific playlist (library and homepage)
    document.querySelectorAll(`article.playlist[data-id="${payload.playlist_id}"]`).forEach(playlist => {
        const song = playlist.querySelector(`article.song_in_playlist[data-id="${payload.song_id}"]`);
        if (song) song.remove();
    });
});



window.addSongToPlaylist = function addSongToPlaylist() {
    const playlist_id = playlistSelectIpt.value;
    const song_id = addSongToPlaylistBtn.dataset.song_id;

    socket.emit('add_song_to_playlist', {song_id: song_id, playlist_id: playlist_id}, (response) => {
            if (!response.success){
                flashMessage(response.message, 'error');
            }
            else{
                closeAddToPlaylist();
                flashMessage(response.message, 'info');
            }
        }
    );
}

// Add a song to the playlist object
socket.on('new_song_in_playlist', payload => {
    const song = payload.song;

     // Get the template and container
    const template = document.getElementById('song-in-playlist-template');
    const library_playlists = document.getElementById('library-playlists');
    const index_playlists = document.getElementById('index-playlists');

    // Clone the template only once and fill out content
    const fragment = template.content.cloneNode(true);
    const new_song = fragment.querySelector('article.song_in_playlist');
    new_song.dataset.id = song.id;
    new_song.querySelector('.song-title').textContent = song.name;
    new_song.querySelector('.song-artist').textContent = song.artist;

    // For library_playlist
    if (library_playlists) {
        const library_playlist = library_playlists.querySelector(`.playlist[data-id="${payload.playlist_id}"]`)
        const new_song_for_library = new_song.cloneNode(true);
        const addToPlaylistBtn = new_song_for_library.querySelector('button.addToPlaylistBtn');
        const removeFromPlaylistBtn = new_song_for_library.querySelector('button.removeFromPlaylistBtn');

        addToPlaylistBtn.onclick = () => openAddToPlaylist(song.id);
        removeFromPlaylistBtn.onclick = () => removeSongFromPlaylist(payload.playlist_id, song.id);
        library_playlist.querySelector('ul').appendChild(new_song_for_library);
    }

    // For index_playlist
    if (index_playlists) {
        const index_playlist = index_playlists.querySelector(`.playlist[data-id="${payload.playlist_id}"]`)
        const new_song_for_index = new_song.cloneNode(true);
        const playSongBtn = new_song_for_index.querySelector('button.playSongBtn');
        const addToPlaylistBtn = new_song_for_index.querySelector('button.addToPlaylistBtn');

        playSongBtn.onclick = () => queuePlaylist(payload.playlist_id, song.id);
        addToPlaylistBtn.onclick = () => openAddToPlaylist(song.id);
        index_playlist.querySelector('ul').appendChild(new_song_for_index);
    }
});

window.openAddToPlaylist = function openAddToPlaylist(song_id) {
    // Remove the 'hidden' class to show the modal
    addSongToPlaylistModel.classList.remove('hidden');

    // Store the song id in the dataset of the submit button
    addSongToPlaylistBtn.dataset.song_id = song_id;
    // Clear the select element
    playlistSelectIpt.innerHTML = '';
    // Add loading text to the select element
    playlistSelectIpt.innerHTML = '<option value="">Loading playlists...</option>';

    socket.emit('get_playlists', (payload) => {
        playlistSelectIpt.innerHTML = '';

        const playlists = payload.playlists;
        if (playlists.length > 0) {
            playlists.forEach(playlist => {
                const option = document.createElement('option');
                option.value = playlist.id;
                option.textContent = playlist.name;
                playlistSelectIpt.appendChild(option);
            });
        } else {
            // Handle case where user has no playlists
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'No playlists available';
            playlistSelectIpt.appendChild(option);
        }
    });
}

window.closeAddToPlaylist = function closeAddToPlaylist() {
    // Add the 'hidden' class to hide the modal
    addSongToPlaylistModel.classList.add('hidden');
}


// Close modal when clicking outside
document.addEventListener('click', (event) => {
    if (event.target === addSongToPlaylistModel) {
        closeAddToPlaylist();
    }
});

window.updateSongName = function updateSongName(song_id, new_name) {
    socket.emit('update_song_name', {song_id, new_name}, (response) => {
        if (response.success){
            flashMessage(response.message, 'success');
        } else {
            flashMessage(response.message, 'error');
        }
    });
}

// Add a song to the playlist object
socket.on('song_name_updated', payload => {
    // Update the song name in the library and homepage
    document.querySelectorAll(`article.song_in_playlist[data-id="${payload.song_id}"]`).forEach(song => {
        song.querySelector('.song-title').textContent = payload.new_name;
    });
    // Update the song name in the textfield if we need to change it back to the original name
    document.querySelectorAll(`article.song[data-id="${payload.song_id}"]`).forEach(song => {
        song.querySelector('.song-title-input').value = payload.new_name;
    });
});

window.updateArtistName = function updateArtistName(song_id, new_artist){
    socket.emit('update_song_artist', {song_id, new_artist}, (response) => {
        if (response.success){
            flashMessage(response.message, 'success');
        } else {
            flashMessage(response.message, 'error');
        }
    });
}

// Add a song to the playlist object
socket.on('song_artist_updated', payload => {
    // Update the song artist in the library and homepage
    document.querySelectorAll(`article.song_in_playlist[data-id="${payload.song_id}"]`).forEach(song => {
        song.querySelector('.song-artist').textContent = payload.new_artist;
    });
    // Update the song name in the textfield if we need to change it back to the original artist
    document.querySelectorAll(`article.song[data-id="${payload.song_id}"]`).forEach(song => {
        song.querySelector('.song-artist-input').value = payload.new_artist;
    });
});