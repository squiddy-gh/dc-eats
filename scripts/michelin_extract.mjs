// Runs inside the restaurant detail page; reads DOM content only.
export const extractRestaurant = () => {
  const clean = e => e?.textContent.replace(/\s+/g, ' ').trim() || '';
  const h = document.querySelector('h1.data-sheet__title');
  const info = document.querySelector('.data-sheet__detail-info');
  if (!h || !info) throw Error('Restaurant detail layout missing');
  const fields = {};
  for (const r of info.querySelectorAll('.data-sheet__block--row')) {
    const c = r.querySelectorAll('.data-sheet__block--text');
    if (c.length === 2) fields[clean(c[0])] = clean(c[1]);
  }
  // Responsive duplicates must agree. Never sum the mobile and desktop badges.
  const badges = [...document.querySelectorAll('.data-sheet__badge-container')]
    .map(e => [...e.querySelectorAll('img')].map(i => i.getAttribute('src') || ''));
  if (!badges.length) throw Error('Award container missing; stars unknown');
  const counts = badges.map(b => b.filter(s => /\/michelin-star_/.test(s)).length);
  if (new Set(counts).size !== 1 || counts[0] > 3) throw Error('Inconsistent awards');
  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const hours = {};
  for (const card of document.querySelectorAll('.card-borderline__content')) {
    const day = clean(card.querySelector('.card--title'));
    if (days.includes(day)) {
      hours[day.toLowerCase() + '_hours'] = [...card.querySelectorAll('.card--content')]
        .map(clean).join('; ');
    }
  }
  return {
    restaurant_name: clean(h), michelin_stars: counts[0],
    address: clean(info.querySelector('.data-sheet__block--text')),
    latitude: '', longitude: '',
    cuisine: fields['Cuisine:'] || '', price: fields['Price:'] || '',
    phone: clean(document.querySelector('a[href^="tel:"]')),
    website: [...document.querySelectorAll('a')].find(a => clean(a) === 'Visit Website')?.href || '',
    badges, narrative: clean(document.querySelector('.data-sheet__description')),
    ...Object.fromEntries(days.map(d => [d.toLowerCase() + '_hours', hours[d.toLowerCase() + '_hours'] || ''])),
  };
};
