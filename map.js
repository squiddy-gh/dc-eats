export const sources = [
  { id: 'loudoun', file: 'data/best_of_loudoun.csv', label: 'Best of Loudoun', color: '#bb4939', icon: '🏆' },
  { id: 'cheap', file: 'data/washingtonian_best_cheap_eats_2026.csv', label: 'Washingtonian Cheap Eats', color: '#236b91', icon: '🍴' },
  { id: 'post', file: 'data/washington_post_40_essential_dc_dishes_2026.csv', label: 'Washington Post Essential Dishes', color: '#7852a0', icon: '◉' },
  { id: 'michelin', file: 'data/michelin_dc_area_2026.csv', label: 'Michelin Guide', color: '#b12e53', icon: 'M' },
];
export const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
export function parseCsv(text) {
  const rows = []; let row = [], field = '', quoted = false;
  text = text.replace(/^\uFEFF/, '');
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (c === '"') { if (quoted && text[i + 1] === '"') { field += '"'; i++; } else quoted = !quoted; }
    else if (c === ',' && !quoted) { row.push(field); field = ''; }
    else if ((c === '\n' || c === '\r') && !quoted) {
      if (c === '\r' && text[i + 1] === '\n') i++;
      row.push(field); field = ''; if (row.some(v => v.trim())) rows.push(row); row = [];
    } else field += c;
  }
  row.push(field); if (row.some(v => v.trim())) rows.push(row);
  if (!rows.length) return [];
  const headers = rows.shift().map(v => v.trim().toLowerCase());
  return rows.map(values => Object.fromEntries(headers.map((h, i) => [h, (values[i] || '').trim()])));
}
export function normalizeRow(row, source) {
  const latitude = Number(row.latitude), longitude = Number(row.longitude);
  if (!row.latitude || !row.longitude || !Number.isFinite(latitude) || !Number.isFinite(longitude) || latitude < 38 || latitude > 40 || longitude < -79 || longitude > -76) return null;
  return { latitude, longitude, source: source.label, sourceId: source.id,
    name: row.restaurant_name || row.name || row.restaurant || 'Unnamed restaurant',
    category: row.category || '', dish: row.dish || '', placement: row.place || '',
    address: row.address || '', website: row.website || row.website_address || '',
    cuisine: row.cuisine || '', cuisines: (row.cuisine || '').split(',').map(s => s.trim()).filter(Boolean),
    stars: /^[0-3]$/.test(String(row.michelin_stars ?? '').trim()) ? Number(row.michelin_stars) : null,
    phone: row.phone || row.telephone || '', narrative: row.narrative || row.review_text || row.short_description || '',
    hours: days.map(day => row[`${day}_hours`] || ''), hoursNotes: row.hours_notes || '' };
}
export function parseHours(value) {
  if (!value?.trim()) return null;
  const text = value.trim().replace(/[–—]/g, '-');
  if (/^closed$/i.test(text)) return [];
  if (/^(?:open\s*)?24\s*(?:hours?|hrs?)$/i.test(text)) return [[0, 1440]];
  const clock = token => {
    const m = token.trim().match(/^(\d{1,2})(?::(\d{2}))?\s*(AM|PM)?$/i);
    if (!m) return null;
    let h = Number(m[1]); const minute = Number(m[2] || 0), period = m[3]?.toUpperCase();
    if (minute > 59 || h > (period ? 12 : 23) || (period && h < 1)) return null;
    if (period) h = h % 12 + (period === 'PM' ? 12 : 0);
    return h * 60 + minute;
  };
  const intervals = [];
  for (const part of text.split(/\s*[;,\n]\s*/)) {
    const halves = part.replace(/\s*\(\+1 day\)/i, '').split('-');
    if (halves.length !== 2) return null;
    const start = clock(halves[0]), finish = clock(halves[1]);
    if (start === null || finish === null || start === finish) return null;
    intervals.push([start, finish + (finish < start || /\(\+1 day\)/i.test(part) ? 1440 : 0)]);
  }
  return intervals;
}
export function localTime(date = new Date()) {
  const p = Object.fromEntries(new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York', weekday: 'long', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).formatToParts(date).map(p => [p.type, p.value]));
  return { day: days.indexOf(p.weekday.toLowerCase()), minute: Number(p.hour) * 60 + Number(p.minute) };
}
export function openingStatus(place, date = new Date()) {
  const { day, minute } = localTime(date), today = parseHours(place.hours[day]), previous = parseHours(place.hours[(day + 6) % 7]);
  if (today?.some(([a, b]) => minute >= a && minute < b) || previous?.some(([a, b]) => b > 1440 && minute + 1440 >= a && minute + 1440 < b)) return 'open';
  if (today === null || (minute < 720 && previous === null)) return 'unknown';
  return 'closed';
}
export function matchesFilters(p, f, date = new Date()) {
  return (f.list === 'all' || p.sourceId === f.list) && (!f.cuisine || p.cuisines.includes(f.cuisine)) &&
    (!f.category || p.category === f.category) && (!f.placement || p.placement === f.placement) &&
    (f.stars === '' || String(p.stars) === f.stars) && (!f.open || openingStatus(p, date) === 'open') &&
    (!f.search || `${p.name} ${p.address} ${p.dish}`.toLowerCase().includes(f.search.toLowerCase()));
}
export function groupPlaces(places) {
  const groups = new Map();
  for (const p of places) {
    const key = `${p.name.toLowerCase().replace(/[^\p{L}\p{N}]/gu, '')}|${p.latitude.toFixed(4)}|${p.longitude.toFixed(4)}`;
    if (!groups.has(key)) groups.set(key, { ...p, entries: [] });
    const g = groups.get(key); if (!g.entries.some(e => JSON.stringify(e) === JSON.stringify(p))) g.entries.push(p);
  }
  return [...groups.values()];
}
export function googleMapsUrl(p) {
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${p.name}, ${p.address || `${p.latitude},${p.longitude}`}`)}`;
}
function detail(parent, label, text, className = '') {
  if (!text) return;
  const p = document.createElement('p'); p.className = className;
  if (label) { const b = document.createElement('strong'); b.textContent = `${label}: `; p.append(b); }
  p.append(document.createTextNode(text)); parent.append(p);
}
function link(parent, label, href) {
  try {
    const url = new URL(href); if (!['https:', 'http:'].includes(url.protocol)) return;
    const a = document.createElement('a'); a.href = url.href; a.textContent = label; a.target = '_blank'; a.rel = 'noopener noreferrer'; parent.append(a);
  } catch { /* CSV text never becomes HTML; invalid links are omitted. */ }
}
export function popup(group) {
  const root = document.createElement('div'); root.className = 'popup';
  const title = document.createElement('h2'); title.textContent = group.name; root.append(title);
  const address = document.createElement('p'); link(address, group.address || 'Google Maps ↗', googleMapsUrl(group)); root.append(address);
  for (const p of group.entries) {
    const section = document.createElement('section'); section.className = 'popup-entry'; detail(section, '', p.source, 'source');
    detail(section, 'Cuisine', p.cuisine);
    if (p.sourceId === 'michelin') detail(section, 'Michelin', p.stars === null ? 'Rating unavailable' : p.stars === 0 ? 'Selected · 0 stars' : `${p.stars} star${p.stars === 1 ? '' : 's'}`);
    detail(section, 'Category', p.category); detail(section, 'Award', p.placement); detail(section, 'Dish', p.dish); detail(section, '', p.narrative, 'review');
    const status = openingStatus(p); detail(section, '', status === 'unknown' ? 'Hours unavailable for this time' : status === 'open' ? 'Open now · Eastern time' : 'Closed now · Eastern time', `hours-state ${status}`);
    detail(section, 'Today', p.hours[localTime().day] || 'Not published');
    const hours = document.createElement('details'), summary = document.createElement('summary'); summary.textContent = 'Weekly hours'; hours.append(summary);
    const dl = document.createElement('dl'); dl.className = 'weekly-hours';
    days.forEach((day, i) => { const dt = document.createElement('dt'), dd = document.createElement('dd'); dt.textContent = day[0].toUpperCase() + day.slice(1); dd.textContent = p.hours[i] || 'Not published'; dl.append(dt, dd); });
    hours.append(dl); detail(hours, '', p.hoursNotes, 'hours-note'); section.append(hours);
    const links = document.createElement('p'); links.className = 'popup-links'; if (p.website) link(links, 'Website ↗', p.website);
    if (p.phone && /^\+?[\d\s().-]+$/.test(p.phone)) { const a = document.createElement('a'); a.href = `tel:${p.phone.replace(/[^+\d]/g, '')}`; a.textContent = p.phone; links.append(a); }
    section.append(links); root.append(section);
  }
  return root;
}
function markerIcon(g) {
  const starred = g.entries.find(e => e.sourceId === 'michelin' && e.stars > 0), p = starred || g.entries[0], s = sources.find(s => s.id === p.sourceId);
  return L.divIcon({ className: 'restaurant-icon', iconSize: [34, 40], iconAnchor: [17, 38], popupAnchor: [0, -32],
    html: `<span class="map-pin${new Set(g.entries.map(e => e.sourceId)).size > 1 ? ' multiple' : ''}" style="--pin-color:${s.color}"><span>${starred ? '★' : s.icon}</span>${starred ? `<b class="star-count">${starred.stars}</b>` : ''}</span>` });
}
export async function loadMap() {
  const status = document.getElementById('status'), notice = document.getElementById('notice');
  if (typeof L === 'undefined') { status.textContent = 'The map could not load. Check your connection and reload.'; return; }
  const map = L.map('map', { scrollWheelZoom: true }).setView([38.92, -77.2], 10);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' }).addTo(map);
  const layer = L.layerGroup().addTo(map), errors = []; let skipped = 0;
  const loadRecords = () => Promise.all(sources.map(async source => {
    try { const response = await fetch(source.file, { cache: 'no-store' }); if (!response.ok) throw new Error(); return parseCsv(await response.text()).map(row => { const p = normalizeRow(row, source); if (!p) skipped++; return p; }).filter(Boolean); }
    catch { errors.push(source.label); return []; }
  }));
  let places = (await loadRecords()).flat();
  const fields = Object.fromEntries(['cuisine', 'category', 'placement', 'stars', 'search', 'open'].map(id => [id, document.getElementById(id)]));
  let selected = 'all', locating = false, userLocation;
  const filters = () => ({ list: selected, ...Object.fromEntries(Object.entries(fields).map(([k, input]) => [k, k === 'open' ? input.checked : input.value])) });
  const render = (fit = false) => {
    const now = new Date(), groups = groupPlaces(places.filter(p => matchesFilters(p, filters(), now))); layer.clearLayers(); const bounds = L.latLngBounds();
    groups.forEach(g => { const m = L.marker([g.latitude, g.longitude], { icon: markerIcon(g), title: g.name, alt: g.name, keyboard: true }); m.bindPopup(() => popup(g), { maxWidth: 370, maxHeight: 420 }).addTo(layer); bounds.extend(m.getLatLng()); });
    if (fit && bounds.isValid()) map.fitBounds(bounds.pad(.08), { maxZoom: 14 });
    const time = new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York', hour: 'numeric', minute: '2-digit', timeZoneName: 'short' }).format(now);
    const unknown = places.filter(p => (selected === 'all' || p.sourceId === selected) && openingStatus(p, now) === 'unknown').length;
    status.textContent = `${groups.length} restaurant location${groups.length === 1 ? '' : 's'} shown · ${time}`;
    notice.textContent = [!groups.length ? 'No matches. Change or clear your filters.' : '', unknown ? `${unknown} entries have unknown hours and are excluded from Open now.` : '', selected === 'loudoun' && !places.some(p => p.sourceId === 'loudoun' && p.hours.some(Boolean)) ? 'Best of Loudoun has no published hours in this dataset.' : '', skipped ? `${skipped} entries have missing or out-of-area coordinates.` : '', errors.length ? `Could not load: ${errors.join(', ')}. Reload to try again.` : ''].filter(Boolean).join(' ');
    document.getElementById('legend').replaceChildren(...sources.filter(s => selected === 'all' || s.id === selected).map(s => { const item = document.createElement('div'); item.className = 'legend-item'; const dot = document.createElement('span'); dot.className = 'swatch'; dot.style.backgroundColor = s.color; item.append(dot, document.createTextNode(`${s.icon} ${s.label}`)); return item; }));
  };
  const populate = () => {
    const scope = places.filter(p => selected === 'all' || p.sourceId === selected), choices = { cuisine: scope.flatMap(p => p.cuisines), category: scope.map(p => p.category), placement: scope.map(p => p.placement), stars: scope.filter(p => p.stars !== null).map(p => String(p.stars)) };
    for (const key of ['cuisine', 'category', 'placement', 'stars']) {
      const options = [...new Set(choices[key].filter(Boolean))].sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
      fields[key].replaceChildren(new Option('Any', ''), ...options.map(v => new Option(key === 'stars' ? v === '0' ? '0 · Michelin selected' : `${v} star${v === '1' ? '' : 's'}` : v, v)));
      document.getElementById(`${key}-field`).hidden = !options.length || (key === 'stars' && selected !== 'michelin') || (['placement', 'category'].includes(key) && selected !== 'loudoun'); fields[key].value = '';
    }
  };
  const menu = document.getElementById('list-menu'), button = document.getElementById('list-button');
  menu.replaceChildren(...[{ id: 'all', label: 'All lists' }, ...sources].map(s => {
    const label = document.createElement('label'); label.className = 'list-choice'; const radio = document.createElement('input'); radio.type = 'radio'; radio.name = 'list'; radio.value = s.id; radio.checked = s.id === 'all'; label.append(radio, document.createTextNode(s.label));
    radio.addEventListener('change', () => { selected = s.id; button.textContent = `List · ${s.label} ▾`; menu.hidden = true; button.setAttribute('aria-expanded', 'false'); populate(); render(true); button.focus(); }); return label;
  }));
  button.addEventListener('click', () => { menu.hidden = !menu.hidden; button.setAttribute('aria-expanded', String(!menu.hidden)); });
  menu.addEventListener('keydown', e => { if (e.key === 'Escape') { menu.hidden = true; button.setAttribute('aria-expanded', 'false'); button.focus(); } });
  let refreshing = false;
  const refresh = async () => {
    if (refreshing) return;
    refreshing = true;
    try { skipped = 0; errors.length = 0; places = (await loadRecords()).flat(); render(); }
    finally { refreshing = false; }
  };
  Object.values(fields).forEach(f => f.addEventListener(f.id === 'search' ? 'input' : 'change', () => {
    render(); if (f.id === 'open' && f.checked) refresh();
  }));
  document.getElementById('reset').addEventListener('click', () => { Object.values(fields).forEach(f => f.type === 'checkbox' ? f.checked = false : f.value = ''); render(true); });
  document.getElementById('fit').addEventListener('click', () => render(true));
  const locate = document.getElementById('locate'), locationStatus = document.getElementById('location-status');
  locate.addEventListener('click', () => {
    if (locating) return;
    if (!navigator.geolocation || !window.isSecureContext) { locationStatus.textContent = 'Location requires HTTPS or localhost and a browser that supports location.'; return; }
    locating = true; locate.disabled = true; locate.textContent = '◎ Locating…'; locationStatus.textContent = 'Your browser may ask to use your location.';
    const done = () => { locating = false; locate.disabled = false; locate.textContent = '◎ Locate me'; };
    navigator.geolocation.getCurrentPosition(position => {
      done(); if (userLocation) map.removeLayer(userLocation); const point = [position.coords.latitude, position.coords.longitude];
      userLocation = L.layerGroup([L.circle(point, { radius: position.coords.accuracy, color: '#2563eb', weight: 1, fillOpacity: .08 }), L.circleMarker(point, { radius: 8, color: '#fff', weight: 3, fillColor: '#2563eb', fillOpacity: 1 }).bindPopup('You are here')]).addTo(map); map.setView(point, 14);
      locationStatus.textContent = `Location found · accuracy about ${Math.round(position.coords.accuracy)} metres. Your location is not stored.`;
    }, error => { done(); locationStatus.textContent = error.code === 1 ? 'Location permission was denied. Allow location in browser settings to try again.' : error.code === 3 ? 'Location timed out. Try again.' : 'Your location is unavailable. Try again.'; }, { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 });
  });
  populate(); render(true); setInterval(() => render(), 60000); setInterval(refresh, 300000);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) refresh(); });
}
if (typeof window !== 'undefined') loadMap().catch(() => { document.getElementById('status').textContent = 'The map could not start. Reload to try again.'; });
