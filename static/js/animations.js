const toggleBtn = document.getElementById('menu-toggle');
const mobileNav = document.getElementById('mobile-nav');
const audio = document.getElementById('audio-player');
const playPauseBtn = document.getElementById('play-pause');
const progress = document.getElementById('progress');
const timeDisplay = document.getElementById('time-display');
const volumeBtn = document.getElementById('volume-btn');
const volumeSliderWrapper = document.getElementById('volume-slider-wrapper');
const volumeSlider = document.getElementById('volume-slider');

// Toggle slider visibility
if (volumeBtn) {
    volumeBtn.addEventListener('click', () => {
        volumeSliderWrapper.classList.toggle('hidden');
    });
}

// Adjust volume
if (volumeSlider) {
    volumeSlider.addEventListener('input', () => {
        audio.volume = volumeSlider.value;
    });
}

document.addEventListener('click', (e) => {
    if (volumeBtn && volumeSliderWrapper) {
        if (!volumeBtn.contains(e.target) && !volumeSliderWrapper.contains(e.target)) {
            volumeSliderWrapper.classList.add('hidden');
          }
    }
});

let isOpen = false;

if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
        isOpen = !isOpen;
        if (isOpen) {
            mobileNav.classList.remove('max-h-0', 'opacity-0');
            mobileNav.classList.add('max-h-96', 'opacity-100');
        } else {
            mobileNav.classList.add('max-h-0', 'opacity-0');
            mobileNav.classList.remove('max-h-96', 'opacity-100');
        }
    });
}

if (playPauseBtn) {
    playPauseBtn.addEventListener('click', () => {
        const playIcon = `
    <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round" d="M14.752 11.168l-6.518-3.758A1 1 0 007 8.29v7.418a1 1 0 001.234.97l6.518-3.758a1 1 0 000-1.742z" />
    </svg>`;

        const pauseIcon = `
    <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
      <rect x="6" y="4" width="4" height="16" rx="1" ry="1" />
      <rect x="14" y="4" width="4" height="16" rx="1" ry="1" />
    </svg>`;

        if (audio.paused) {
            audio.play();
            playPauseBtn.innerHTML = pauseIcon;
        } else {
            audio.pause();
            playPauseBtn.innerHTML = playIcon;
        }
    });
}

if (audio) {
    audio.addEventListener('timeupdate', () => {
        const current = audio.currentTime;
        const duration = audio.duration;
        if (!isNaN(duration)) {
            const percent = (current / duration) * 100;
            progress.value = percent;

            // Format time mm:ss
            const formatTime = (t) => {
                const m = Math.floor(t / 60) || 0;
                const s = Math.floor(t % 60) || 0;
                return `${m}:${s < 10 ? '0' : ''}${s}`;
            };

            timeDisplay.textContent = `${formatTime(current)} / ${formatTime(duration)}`;
        }
    });
}

if (progress) {
    progress.addEventListener('input', () => {
        if (!isNaN(audio.duration)) {
            audio.currentTime = (progress.value / 100) * audio.duration;
        }
    });
}

// Function for custom flash messages from websockets
export function flashMessage(message, category = 'info', duration = 3000) {
    const container = document.getElementById('custom-flash-popup');

    const alertDiv = document.createElement('div');

    // Add Tailwind classes for the white transparent background, black text, padding, and shadow
    alertDiv.className = `custom-flash-message ${category} rounded-lg bg-white/90 p-4 text-black shadow-lg backdrop-blur-sm text-center`;
    alertDiv.textContent = message;

    // Add a transition for a smooth fade-out effect
    alertDiv.style.transition = 'opacity 0.5s ease-in-out';

    container.appendChild(alertDiv);

    setTimeout(() => {
        alertDiv.style.opacity = 0;
        setTimeout(() => alertDiv.remove(), 500); // Remove after fade out
    }, duration);
}

