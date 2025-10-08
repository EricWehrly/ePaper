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
    all.forEach(item => {
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
          const res = await fetch('/api/display/image', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({image_path: item.path})});
          if (!res.ok) throw new Error('display failed');
          // Optionally get any returned status
          const body = await res.json().catch(()=>null);
          if (body && body.status) statusEl.textContent = body.status;
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
});