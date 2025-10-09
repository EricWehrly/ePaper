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
  busy: false,
  carouselActive: false
};

function setBusyState(busy, incomingImagePath = null, statusText = '') {
  const displayBox = document.getElementById('displayBox');
  const overlay = document.getElementById('previewOverlay');
  const statusEl = document.getElementById('previewStatus');
  const currentImage = document.getElementById('currentImage');
  
  if (busy) {
    displayBox.classList.add('display-busy');
    overlay.style.display = 'block';
    statusEl.textContent = statusText;
    
    // Show incoming image if provided
    if (incomingImagePath) {
      currentImage.src = '/static_image?path=' + encodeURIComponent(incomingImagePath);
      currentImage.style.display = '';
      document.getElementById('placeholder').style.display = 'none';
    }
    
    // Disable busy-sensitive controls
    document.querySelectorAll('.busy-sensitive').forEach(el => {
      el.disabled = true;
    });
    document.querySelectorAll('.thumb').forEach(el => {
      el.classList.add('disabled');
    });
  } else {
    displayBox.classList.remove('display-busy');
    overlay.style.display = 'none';
    statusEl.textContent = '';
    
    // Re-enable controls (but respect their individual disabled states)
    document.querySelectorAll('.busy-sensitive').forEach(el => {
      // Only re-enable if not disabled for other reasons
      if (!el.hasAttribute('data-originally-disabled')) {
        el.disabled = false;
      }
    });
    document.querySelectorAll('.thumb').forEach(el => {
      el.classList.remove('disabled');
    });
  }
}

async function displayImage(path, statusText = 'Applying image...') {
  setBusyState(true, path, statusText);
  try {
    const res = await fetch('/api/display/image', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({image_path: path})});
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      if (res.status === 409) {
        // Display is busy, don't change UI state
        return;
      }
      throw new Error(errorData.error || 'display failed');
    }
  } catch (e) {
    console.error(e);
    alert('Failed to display image: ' + e.message);
  } finally {
    setBusyState(false);
    setTimeout(refresh, 300);
  }
}

async function clearDisplay() {
  setBusyState(true, null, 'Clearing display...');
  try {
    const res = await fetch('/api/display/clear', {method:'POST'});
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      if (res.status === 409) return; // Already busy
      throw new Error(errorData.error || 'clear failed');
    }
  } catch (e) {
    console.error(e);
    alert('Failed to clear display: ' + e.message);
  } finally {
    setBusyState(false);
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
    state.carouselActive = status.carousel_active || false;
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
        
        try {
          await displayImage(item.path, `Applying ${item.name}...`);
        } catch (e) {
          console.error(e);
        } finally {
          // Re-enable thumbs
          document.querySelectorAll('.thumb').forEach(t => t.classList.remove('disabled'));
        }
      });
      list.appendChild(thumb);
    });
  } catch (e) {
    console.error(e);
  }
  return Promise.resolve(); // Ensure it returns a promise
}

function updateControlsFromStatus(status) {
  const mode = (status.settings && status.settings.mode) || 'image';
  const autoplay = !!(status.settings && status.settings.autoplay);
  const intervalSec = (status.settings && status.settings.interval_sec) || 30;
  const orientation = (status.settings && status.settings.orientation) || 'portrait';
  const carouselActive = status.carousel_active || false;
  
  document.getElementById('modeImageBtn').setAttribute('aria-pressed', mode==='image');
  document.getElementById('modeCarouselBtn').setAttribute('aria-pressed', mode==='carousel');
  const autoplayBtn = document.getElementById('autoplayToggle');
  autoplayBtn.textContent = 'Autoplay: ' + (autoplay ? 'On':'Off');
  autoplayBtn.dataset.playing = autoplay ? 'true':'false';
  document.getElementById('intervalInput').value = intervalSec;
  document.getElementById('orientationSelect').value = orientation;
  
  // Enable/disable navigation - prev/next work in any mode when images exist
  const navEnabled = state.convertedImages.length > 0;
  const autoplayEnabled = mode === 'carousel' && state.convertedImages.length > 0;
  
  ['prevBtn','nextBtn'].forEach(id => {
    const elRef = document.getElementById(id);
    if (!navEnabled) {
      elRef.setAttribute('data-originally-disabled', 'true');
      elRef.disabled = true;
    } else {
      elRef.removeAttribute('data-originally-disabled');
      if (!status.busy) elRef.disabled = false;
    }
  });
  
  // Autoplay toggle only enabled in carousel mode
  const autoplayToggle = document.getElementById('autoplayToggle');
  if (!autoplayEnabled) {
    autoplayToggle.setAttribute('data-originally-disabled', 'true');
    autoplayToggle.disabled = true;
  } else {
    autoplayToggle.removeAttribute('data-originally-disabled');
    if (!status.busy) autoplayToggle.disabled = false;
  }
  
  // Handle busy state from server
  const shouldShowBusy = status.busy;
  const statusText = carouselActive && status.busy ? 'Carousel cycling...' : 
                     status.busy ? 'Display busy...' : '';
  
  if (shouldShowBusy !== state.busy) {
    state.busy = shouldShowBusy;
    // Show current image with overlay when carousel is cycling
    if (carouselActive && status.busy && status.current_image) {
      setBusyState(shouldShowBusy, status.current_image, statusText);
    } else if (status.busy) {
      setBusyState(shouldShowBusy, null, statusText);
    } else {
      setBusyState(false);
    }
  }
}

let refreshTimer = null;

function scheduleNextRefresh() {
  if (refreshTimer) clearTimeout(refreshTimer);
  const isCarouselActive = (state.settings.mode === 'carousel' && state.settings.autoplay) || state.carouselActive;
  const interval = isCarouselActive ? 800 : 5000; // Very frequent when carousel is running
  refreshTimer = setTimeout(() => {
    refresh().then(() => scheduleNextRefresh());
  }, interval);
}

window.addEventListener('load', () => {
  refresh().then(() => scheduleNextRefresh());

  document.getElementById('clearBtn').addEventListener('click', () => {
    clearDisplay();
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
  document.getElementById('nextBtn').addEventListener('click', async (e) => {
    // Don't do anything if button is disabled
    if (e.target.disabled) return;
    
    setBusyState(true, null, 'Loading next image...');
    try {
      const res = await fetch('/api/display/next', {method:'POST'});
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        if (res.status === 409) return; // Already busy
        throw new Error(errorData.error || 'next failed');
      }
    } catch (e) {
      console.error(e);
      alert('Failed to go to next image: ' + e.message);
    } finally {
      setBusyState(false);
      setTimeout(refresh, 300);
    }
  });
  document.getElementById('prevBtn').addEventListener('click', async (e) => {
    // Don't do anything if button is disabled
    if (e.target.disabled) return;
    
    setBusyState(true, null, 'Loading previous image...');
    try {
      const res = await fetch('/api/display/prev', {method:'POST'});
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        if (res.status === 409) return; // Already busy
        throw new Error(errorData.error || 'prev failed');
      }
    } catch (e) {
      console.error(e);
      alert('Failed to go to previous image: ' + e.message);
    } finally {
      setBusyState(false);
      setTimeout(refresh, 300);
    }
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