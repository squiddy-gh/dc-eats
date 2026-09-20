const sources = [
  { file: 'data/best_of_loudoun.csv', label: 'Best of Loudoun', color: '#d1493f' },
  { file: 'data/washingtonian_best_cheap_eats_2026.csv', label: 'Washingtonian Cheap Eats', color: '#2479b3' },
  { file: 'data/washington_post_40_essential_dc_dishes_2026.csv', label: 'Washington Post 40 Essential Dishes', color: '#7953a7' },
];

// Handles quoted commas, doubled quotes, and line breaks inside quoted values.
export function parseCsv(text) {
  const rows = [];
  let row = [], field = '', quoted = false;
  text = text.replace(/^\uFEFF/, '');
  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    if (char === '"') {
      if (quoted && text[i + 1] === '"') { field += '"'; i++; }
      else quoted = !quoted;
    } else if (char === ',' && !quoted) {
      row.push(field); field = '';
    } else if ((char === '\n' || char === '\r') && !quoted) {
      if (char === '\r' && text[i + 1] === '\n') i++;
      row.push(field); field = '';
      if (row.some(value => value.trim())) rows.push(row);
      row = [];
    } else {
      field += char;
    }
  }
  row.push(field);
  if (row.some(value => value.trim())) rows.push(row);
  if (!rows.length) return [];
  const headers = rows.shift().map(value => value.trim().toLowerCase());
  return rows.map(values => Object.fromEntries(headers.map((header, i) => [header, (values[i] || '').trim()])));
}

export function normalizeRow(row, source) {
  const latitude = Number(row.latitude);
  const longitude = Number(row.longitude);
  if (!row.latitude || !row.longitude || !Number.isFinite(latitude) || !Number.isFinite(longitude) ||
      latitude < 38 || latitude > 40 || longitude < -79 || longitude > -76) return null;
  return {
    latitude, longitude, source: source.label,
    name: row.name || row.restaurant_name || row.restaurant || 'Unnamed place',
    category: row.category || row.dish || '',
    placement: row.place || '',
    address: row.address || '',
    website: row.website_address || row.website || '',
    narrative: row.review_text || row.short_description || '',
  };
}

function addDetail(parent, label, value, className = '') {
  if (!value) return;
  const p = document.createElement('p');
  if (className) p.className = className;
  if (label) {
    const strong = document.createElement('strong');
    strong.textContent = `${label}: `;
    p.append(strong);
  }
  p.append(document.createTextNode(value));
  parent.append(p);
}

function popup(place) {
  const root = document.createElement('div');
  root.className = 'popup';
  const title = document.createElement('h2');
  title.textContent = place.name;
  root.append(title);
  addDetail(root, '', place.source, 'source');
  addDetail(root, place.category && place.source.startsWith('Washington Post') ? 'Dish' : 'Category', place.category);
  addDetail(root, 'Placement', place.placement);
  addDetail(root, 'Address', place.address);
  if (place.website) {
    try {
      const url = new URL(place.website);
      if (url.protocol === 'http:' || url.protocol === 'https:') {
        const p = document.createElement('p');
        const link = document.createElement('a');
        link.href = url.href;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        link.textContent = 'Website ↗';
        p.append(link); root.append(p);
      }
    } catch { /* Ignore malformed website values. */ }
  }
  addDetail(root, '', place.narrative, 'review');
  return root;
}

async function loadMap() {
  const map = L.map('map', { scrollWheelZoom: false });
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);
  map.setView([38.92, -77.2], 10);

  const bounds = L.latLngBounds();
  const overlays = {};
  const summary = [];
  const legend = document.getElementById('legend');
  for (const source of sources) {
    const layer = L.layerGroup().addTo(map);
    overlays[source.label] = layer;
    let loaded = 0, skipped = 0;
    try {
      const response = await fetch(source.file);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const rows = parseCsv(await response.text());
      for (const row of rows) {
        const place = normalizeRow(row, source);
        if (!place) { skipped++; continue; }
        const position = [place.latitude, place.longitude];
        L.circleMarker(position, { radius: 7, color: '#fff', weight: 2, fillColor: source.color, fillOpacity: .9 })
          .bindPopup(popup(place), { maxWidth: 320 }).addTo(layer);
        bounds.extend(position);
        loaded++;
      }
      summary.push(`${source.label}: ${loaded} mapped${skipped ? `, ${skipped} skipped (invalid or out-of-area coordinates)` : ''}`);
    } catch (error) {
      summary.push(`${source.label}: could not load (${error.message})`);
    }
    const item = document.createElement('div');
    item.className = 'legend-item';
    const swatch = document.createElement('span');
    swatch.className = 'swatch';
    swatch.style.backgroundColor = source.color;
    const label = document.createElement('span');
    label.textContent = source.label;
    const count = document.createElement('span');
    count.className = 'count';
    count.textContent = `(${loaded})`;
    item.append(swatch, label, count);
    legend.append(item);
  }
  L.control.layers(null, overlays, { collapsed: false }).addTo(map);
  if (bounds.isValid()) map.fitBounds(bounds.pad(.05));
  document.getElementById('status').textContent = summary.join(' · ');
  console.info('DC Eats map:', ...summary);
}

if (typeof window !== 'undefined' && typeof L !== 'undefined') loadMap();

