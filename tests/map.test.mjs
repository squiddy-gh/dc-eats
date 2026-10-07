import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { sources, days, parseCsv, normalizeRow, parseHours, localTime, openingStatus, matchesFilters, groupPlaces, googleMapsUrl } from '../map.js';
const base = { restaurant_name: 'Café José', latitude: '38.9', longitude: '-77.1', narrative: 'Chef’s full story…', address: '1 Main St' };
const filters = { list: 'all', cuisine: '', stars: '', category: '', placement: '', search: '', open: false };
test('CSV preserves UTF-8, quoted commas, quotes, and full multiline narratives', () => {
  assert.deepEqual(parseCsv('\uFEFFname,narrative\r\n"Café, José","Chef’s \\"story\\"\ncontinues…"'.replaceAll('\\"', '""')), [{ name: 'Café, José', narrative: 'Chef’s "story"\ncontinues…' }]);
});
test('normalization uses the narrative and never infers Michelin stars', () => {
  const p = normalizeRow(base, sources[3]); assert.equal(p.stars, null); assert.equal(p.narrative, base.narrative);
  assert.equal(normalizeRow({ ...base, michelin_stars: '0' }, sources[3]).stars, 0);
  assert.equal(normalizeRow({ ...base, latitude: '' }, sources[0]), null);
  assert.equal(normalizeRow({ ...base, longitude: 'Infinity' }, sources[0]), null);
});
test('hours accept split service, 12-hour clocks and overnight schedules', () => {
  assert.deepEqual(parseHours('11:30-14:00; 17:00-22:00'), [[690,840],[1020,1320]]);
  assert.deepEqual(parseHours('4 PM–12:45 AM'), [[960,1485]]);
  assert.deepEqual(parseHours('18:00-01:00 (+1 day)'), [[1080,1500]]);
  assert.deepEqual(parseHours('12 AM-12 PM'), [[0,720]]);
  assert.deepEqual(parseHours('Closed'), []); assert.equal(parseHours('By appointment'), null);
  assert.equal(parseHours('25:00-26:00'), null); assert.equal(parseHours(''), null);
});
test('Eastern time includes DST regardless of the device timezone', () => {
  assert.equal(localTime(new Date('2026-01-05T17:00:00Z')).minute,720);
  assert.equal(localTime(new Date('2026-07-06T16:00:00Z')).minute,720);
});
test('opening status handles midnight rollover, split closures and exclusive closing', () => {
  const p = { hours: days.map(() => 'Closed') }; p.hours[6] = '18:00-02:00 (+1 day)';
  assert.equal(openingStatus(p,new Date('2026-10-05T05:00:00Z')), 'open');
  assert.equal(openingStatus(p,new Date('2026-10-05T06:00:00Z')), 'closed');
  p.hours[0] = '11:00-14:00; 17:00-22:00';
  assert.equal(openingStatus(p,new Date('2026-10-05T19:00:00Z')), 'closed');
  assert.equal(openingStatus(p,new Date('2026-10-05T21:00:00Z')), 'open');
  p.hours[0] = ''; assert.equal(openingStatus(p,new Date('2026-10-05T21:00:00Z')), 'unknown');
});
test('filters distinguish zero-star, cuisine, award and unknown hours', () => {
  const p = normalizeRow({ ...base, michelin_stars:'0', cuisine:'Mexican, Contemporary', place:'Winner', category:'Restaurant' },sources[3]);
  assert.equal(matchesFilters(p,{ ...filters, list:'michelin', stars:'0', cuisine:'Mexican' }),true);
  assert.equal(matchesFilters(p,{ ...filters, stars:'1' }),false);
  assert.equal(matchesFilters(p,{ ...filters, placement:'Finalist' }),false);
  assert.equal(matchesFilters(p,{ ...filters, open:true }),false);
});
test('same-location groups retain dishes and suppress only exact duplicates', () => {
  const p = normalizeRow(base,sources[2]); const groups = groupPlaces([p,p,{ ...p,dish:'Another dish' }]);
  assert.equal(groups.length,1); assert.equal(groups[0].entries.length,2);
  assert.match(googleMapsUrl(p),/Caf%C3%A9/);
});
test('all four current datasets load, and every published schedule is understood', () => {
  for (const source of sources) {
    const rows = parseCsv(readFileSync(new URL(`../${source.file}`,import.meta.url),'utf8'));
    assert.ok(rows.length > 0,source.label);
    const places = rows.map(r => normalizeRow(r,source)).filter(Boolean);
    assert.ok(places.length > 0,source.label);
    for (const p of places) for (const h of p.hours) if (h) assert.notEqual(parseHours(h),null,`${p.name}: ${h}`);
    if (source.id === 'michelin') { assert.equal(rows.length,110); assert.ok(places.some(p => p.name === 'The Inn at Little Washington' && p.stars === 2)); }
  }
});
