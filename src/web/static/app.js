async function fetchJson(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error('Network error');
  return res.json();
}

function el(tag, attrs={}, ...children) {
  const e = document.createElement(tag);
  Object.entries(attrs).forEach(([k,v]) => { if (k === 'class') e.className = v; else e.setAttribute(k,v); });
  children.forEach(c => { if (typeof c === 'string') e.appendChild(document.createTextNode(c)); else e.appendChild(c); });
  return e;
}

let state = {
  mode: 'image', // 'image' | 'carousel'
  images: [],
  convertedImages: [],
  currentIndex: -1,
  autoplay: false,
  intervalSec: 30,
  timer: null,
  orientation: 'portrait'
};

function enableNav(enabled) {
  const prevBtn = document.getElementById('prevBtn');
  const nextBtn = document.getElementById('nextBtn');
  const autoplayToggle = document.getElementById('autoplayToggle');
  [prevBtn, nextBtn, autoplayToggle].forEach(b => b.disabled = !enabled);
  autoplayToggle.disabled = state.mode !== 'carousel';
}

function setMode(mode) {
  if (state.mode === mode) return;
  state.mode = mode;
  document.getElementById('modeImageBtn').setAttribute('aria-pressed', mode==='image');
  document.getElementById('modeCarouselBtn').setAttribute('aria-pressed', mode==='carousel');
  if (mode === 'image') {
    stopAutoplay();
    enableNav(false);
  } else {
    enableNav(true);
  }
}

function showByIndex(idx) {
  if (!state.convertedImages.length) return;
  if (idx < 0) idx = state.convertedImages.length - 1;
  if (idx >= state.convertedImages.length) idx = 0;
  state.currentIndex = idx;
  const item = state.convertedImages[idx];
  // Reuse same logic used on thumb click
  displayImage(item.path, false);
}

function nextImage() { showByIndex(state.currentIndex + 1); }
function prevImage() { showByIndex(state.currentIndex - 1); }

function startAutoplay() {
  if (state.autoplay) return;
  state.autoplay = true;
  const btn = document.getElementById('autoplayToggle');
  btn.textContent = 'Autoplay: On';
  btn.dataset.playing = 'true';
  scheduleNext();
}

function stopAutoplay() {
  state.autoplay = false;
  const btn = document.getElementById('autoplayToggle');
  btn.textContent = 'Autoplay: Off';
  btn.dataset.playing = 'false';
  if (state.timer) { clearTimeout(state.timer); state.timer = null; }
}

function scheduleNext() {
  if (!state.autoplay) return;
  if (state.timer) clearTimeout(state.timer);
  state.timer = setTimeout(() => {
    nextImage();
    scheduleNext();
  }, state.intervalSec * 1000);
}

async function displayImage(path, showOverlay=true) {
  const overlay = document.getElementById('previewOverlay');
  const statusEl = document.getElementById('previewStatus');
  if (showOverlay) {
    overlay.style.display = '';
    statusEl.textContent = 'Applying image...';
  }
  try {
    const res = await fetch('/api/display/image', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({image_path: path})});
    if (!res.ok) throw new Error('display failed');
    await res.json().catch(()=>null);
  } catch (e) {
    console.error(e);
  } finally {
    if (showOverlay) {
      overlay.style.display = 'none';
      statusEl.textContent = '';
    }
    setTimeout(refresh, 300);
  }
}

async function refresh() {
  try {
    const status = await fetchJson('/api/status');
    // Current image
    const current = status.current_image || null;
    const imgEl = document.getElementById('currentImage');
    const placeholder = document.getElementById('placeholder');
    if (current) {
      imgEl.src = '/static_image?path=' + encodeURIComponent(current);
      imgEl.style.display = '';
      placeholder.style.display = 'none';
    } else {
      imgEl.src = '';
      imgEl.style.display = 'none';
      placeholder.style.display = '';
    }

    // Images list
    const images = await fetchJson('/api/images');
    const list = document.getElementById('thumbList');
    list.innerHTML = '';
    // Only show converted images for now
    const all = images.converted_images || [];
    state.convertedImages = all;
    // Update current index if we have a known current image
    if (status.current_image) {
      const idx = all.findIndex(i => i.path === status.current_image);
      if (idx !== -1) state.currentIndex = idx; else state.currentIndex = -1;
    }
    enableNav(state.mode === 'carousel' && all.length>0);
    all.forEach((item, idx) => {
      const thumb = el('div', {class:'thumb'});
      const img = el('img', {src:'/static_image?path=' + encodeURIComponent(item.path)});
      const name = el('div', {class:'name'}, item.name);
      const meta = el('div', {class:'meta'}, item.type);
      const text = el('div', {}, name, meta);
      thumb.appendChild(img);
      thumb.appendChild(text);
      thumb.addEventListener('click', async () => {
        if (thumb.classList.contains('disabled')) return;
        // Disable all thumbs while updating
        document.querySelectorAll('.thumb').forEach(t => t.classList.add('disabled'));
        // Show spinner overlay and status
        const overlay = document.getElementById('previewOverlay');
        const statusEl = document.getElementById('previewStatus');
        overlay.style.display = '';
        statusEl.textContent = 'Applying image...';

        try {
          await displayImage(item.path, false);
          state.currentIndex = idx;
        } catch (e) {
          alert('Failed to display image');
        } finally {
          // Re-enable inputs and hide overlay
          document.querySelectorAll('.thumb').forEach(t => t.classList.remove('disabled'));
          overlay.style.display = 'none';
          statusEl.textContent = '';
          setTimeout(refresh, 500);
        }
      });
      list.appendChild(thumb);
    });
  } catch (e) {
    console.error(e);
  }
}

window.addEventListener('load', () => {
  refresh();
  setInterval(() => { if (!state.autoplay) refresh(); }, 5000);

  document.getElementById('clearBtn').addEventListener('click', async () => {
    const overlay = document.getElementById('previewOverlay');
    const statusEl = document.getElementById('previewStatus');
    overlay.style.display = '';
    statusEl.textContent = 'Clearing display...';
    try {
      const r = await fetch('/api/display/clear', {method:'POST'});
      if (!r.ok) throw new Error('clear failed');
    } catch (e) {
      alert('Failed to clear display');
    } finally {
      overlay.style.display = 'none';
      statusEl.textContent = '';
      setTimeout(refresh, 300);
    }
  });

  // Mode buttons
  document.getElementById('modeImageBtn').addEventListener('click', () => {
    setMode('image');
  });
  document.getElementById('modeCarouselBtn').addEventListener('click', () => {
    setMode('carousel');
    if (state.currentIndex === -1 && state.convertedImages.length) {
      showByIndex(0);
    }
  });

  // Navigation
  document.getElementById('nextBtn').addEventListener('click', () => nextImage());
  document.getElementById('prevBtn').addEventListener('click', () => prevImage());

  // Autoplay
  document.getElementById('autoplayToggle').addEventListener('click', () => {
    if (state.autoplay) {
      stopAutoplay();
    } else {
      startAutoplay();
    }
  });

  // Interval change
  document.getElementById('intervalInput').addEventListener('change', (e) => {
    const v = parseInt(e.target.value, 10);
    if (!isNaN(v) && v >= 5) {
      state.intervalSec = v;
      if (state.autoplay) scheduleNext();
    }
  });

  // Orientation (stub - requires backend endpoint to actually change display orientation)
  document.getElementById('orientationSelect').addEventListener('change', async (e) => {
    state.orientation = e.target.value;
    try {
      // Attempt call (may 404 until implemented server-side)
      await fetch('/api/display/orientation', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({orientation: state.orientation})});
    } catch (err) {
      console.warn('Orientation endpoint not implemented yet.');
    }
  });
});