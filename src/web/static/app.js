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
  convertedImages: [],
  settings: {},
  busy: false
};

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
    state.settings = status.settings || state.settings;
    state.busy = status.busy;
    updateControlsFromStatus(status);
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

function updateControlsFromStatus(status) {
  const mode = (status.settings && status.settings.mode) || 'image';
  const autoplay = !!(status.settings && status.settings.autoplay);
  const intervalSec = (status.settings && status.settings.interval_sec) || 30;
  const orientation = (status.settings && status.settings.orientation) || 'portrait';
  document.getElementById('modeImageBtn').setAttribute('aria-pressed', mode==='image');
  document.getElementById('modeCarouselBtn').setAttribute('aria-pressed', mode==='carousel');
  const autoplayBtn = document.getElementById('autoplayToggle');
  autoplayBtn.textContent = 'Autoplay: ' + (autoplay ? 'On':'Off');
  autoplayBtn.dataset.playing = autoplay ? 'true':'false';
  document.getElementById('intervalInput').value = intervalSec;
  document.getElementById('orientationSelect').value = orientation;
  // Enable/disable navigation based on mode & images
  const navEnabled = mode === 'carousel' && state.convertedImages.length>0;
  ['prevBtn','nextBtn','autoplayToggle'].forEach(id => {
    const elRef = document.getElementById(id);
    elRef.disabled = !navEnabled;
  });
  // Busy state styling
  const displayBox = document.getElementById('displayBox');
  if (status.busy) displayBox.classList.add('display-busy'); else displayBox.classList.remove('display-busy');
}

window.addEventListener('load', () => {
  refresh();
  setInterval(refresh, 5000);

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
  document.getElementById('modeImageBtn').addEventListener('click', async () => {
    await fetch('/api/settings', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({mode:'image'})});
    refresh();
  });
  document.getElementById('modeCarouselBtn').addEventListener('click', async () => {
    await fetch('/api/settings', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({mode:'carousel'})});
    refresh();
  });

  // Navigation
  document.getElementById('nextBtn').addEventListener('click', async () => {
    await fetch('/api/display/next', {method:'POST'});
    setTimeout(refresh, 300);
  });
  document.getElementById('prevBtn').addEventListener('click', async () => {
    await fetch('/api/display/prev', {method:'POST'});
    setTimeout(refresh, 300);
  });

  // Autoplay
  document.getElementById('autoplayToggle').addEventListener('click', async () => {
    const playing = document.getElementById('autoplayToggle').dataset.playing === 'true';
    await fetch('/api/settings', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({autoplay: !playing})});
    setTimeout(refresh, 300);
  });

  // Interval change
  document.getElementById('intervalInput').addEventListener('change', async (e) => {
    const v = parseInt(e.target.value, 10);
    if (!isNaN(v) && v >= 5) {
      await fetch('/api/settings', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({interval_sec: v})});
      setTimeout(refresh, 200);
    }
  });

  // Orientation (stub - requires backend endpoint to actually change display orientation)
  document.getElementById('orientationSelect').addEventListener('change', async (e) => {
    const orientation = e.target.value;
    await fetch('/api/display/orientation', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({orientation})});
    setTimeout(refresh, 500);
  });
});