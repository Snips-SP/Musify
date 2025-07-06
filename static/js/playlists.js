import { flashMessage } from './animations.js'
import { socket } from './socket.js';

const playlistNameIpt = document.getElementById('playlistNameIpt')
const audioPlayer = document.getElementById('audio-player');
const song_name = document.getElementById('song-name');
const artist_name = document.getElementById('artist-name');
const playlist_name = document.getElementById('playlist-name');

// Public function to create playlist
window.createPlaylist = function createPlaylist() {
    const playlist_name = playlistNameIpt.value.trim();

    if (!playlist_name) {
        flashMessage('Playlist name cannot be empty.', category='error');
        return;
    }

    // Send to backend via socket and wait for backend success code
    socket.emit('add_playlist', {playlist_name}, (response) => {
        flashMessage(response.message, response.success ? 'success' : 'error');
    });
    playlistNameIpt.value = '';
}

// Public function for all buttons to remove a specific playlist
window.removePlaylist = function removePlaylist(playlist_id) {
    // Send to backend via socket and wait for backend success code
    socket.emit('remove_playlist', {playlist_id}, (response) => {
        flashMessage(response.message, response.success ? 'success' : 'error');
    });
}

socket.on('new_playlist', playlist => {
    const library_playlists = document.getElementById('library-playlists');
    const index_playlists = document.getElementById('index-playlists');
    const template = document.getElementById('playlist-template');

    // Handle for the library page
    if (library_playlists) {
        // Create a fresh clone from the template for the library
        const new_playlist_node_for_library = template.content.cloneNode(true);

        const article = new_playlist_node_for_library.querySelector('article.playlist');
        const inputElement = new_playlist_node_for_library.querySelector('input.playlist-name-input');
        const deletePlaylistBtn = new_playlist_node_for_library.querySelector('button.deletePlaylistBtn');

        article.dataset.id = playlist.id;

        inputElement.value = playlist.name;
        inputElement.onchange = function() {
            updatePlaylistName(playlist.id, this.value);
        };

        deletePlaylistBtn.onclick = () => removePlaylist(playlist.id);

        library_playlists.appendChild(new_playlist_node_for_library);
    }

    // Handle for the index page
    if (index_playlists) {
        // Create a fresh clone from the template for the index page
        const new_playlist_node_for_index = template.content.cloneNode(true);
        const article = new_playlist_node_for_index.querySelector('article.playlist');
        const playPlaylistBtn = new_playlist_node_for_index.querySelector('button.playPlaylistBtn');
        const h3 = new_playlist_node_for_index.querySelector('h3.playlistNameH3');

        article.dataset.id = playlist.id;
        h3.textContent = playlist.name;
        playPlaylistBtn.onclick = () => queuePlaylist(playlist.id, -1);

        index_playlists.appendChild(new_playlist_node_for_index);
    }
});


// Remove the playlist from any page
socket.on('playlist_removed', playlist => {
    // Select the single matching playlist article in the document
    const playlistElement = document.querySelector(`article.playlist[data-id="${playlist.id}"]`);

    // Check if the element was found on the page
    if (playlistElement) {
        playlistElement.remove();
    }
});

window.updatePlaylistName = function updatePlaylistName(playlist_id, new_name) {
    socket.emit('update_playlist_name', {playlist_id, new_name}, (response) => {
        if (response.success){
            flashMessage(response.message, 'success');
        } else {
            flashMessage(response.message, 'error');

        }
    });
}

// Remove the playlist from any page
socket.on('playlist_name_updated', playlist => {
    // Select the single matching playlist article in the document
    const playlistElement = document.querySelector(`article.playlist[data-id="${playlist.id}"]`);

    // Check if the element was found on the page
    if (playlistElement) {
        const input = playlistElement.querySelector('input');
        if (input) {
            // Update the input value if it's in the library
            input.value = playlist.new_name;
        } else {
            // If no input, try to find and update an h3
            const h3 = playlistElement.querySelector('h3');
            if (h3) {
                // Update the h3 if it's in the homepage
                h3.textContent = playlist.new_name;
            }
        }
    }
});


window.skipSong = function skipSong() { }

function queuePlaylist(playlist_id, song_id) {
    const data = {
        playlist_id: playlist_id,
        shuffle: true  // For now, we just shuffle the playlist
    };

    // If we click a song directly, we add the song id to the reqeust
    if (song_id !== -1) {
        data.song_id = song_id;
    }

    fetch('/playlists/queue_playlist', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Replace skipSong function with the new one
            window.skipSong = playSongsInQueue(data.song_queue, data.playlist); // Start playing songs
        } else {
            flashMessage(data.message, 'error');
        }
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}
// Make the function available to the global scope
window.queuePlaylist = queuePlaylist;
// Make the function available to other js files
export { queuePlaylist };


function playSongsInQueue(songQueue, playlist) {
    let currentSongIndex = 0; // Start with the first song
    // Function to play the next song in the queue
    function playNextSong() {
        // loop the queue if we finish
        if (currentSongIndex >= songQueue.length) {
            console.log('All songs played.');
            currentSongIndex = 0;
        }

        audioPlayer.src = songQueue[currentSongIndex]['file_path']; // Set the source of the audio player
        audioPlayer.play(); // Play the song

        song_name.textContent = songQueue[currentSongIndex]['name'];
        artist_name.textContent = songQueue[currentSongIndex]['artist'];
        playlist_name.textContent = playlist;

        currentSongIndex++; // Move to the next song
    }

    // When a song ends, play the next one
    audioPlayer.addEventListener('ended', playNextSong);

    // Start the first song
    playNextSong();

    return playNextSong;
}