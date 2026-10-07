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
test('all seven current datasets load, and every published schedule is understood', () => {
  for (const source of sources) {
    const rows = parseCsv(readFileSync(new URL(`../${source.file}`,import.meta.url),'utf8'));
    assert.ok(rows.length > 0,source.label);
    const places = rows.map(r => normalizeRow(r,source)).filter(Boolean);
    assert.ok(places.length > 0,source.label);
    for (const p of places) for (const h of p.hours) if (h) assert.notEqual(parseHours(h),null,`${p.name}: ${h}`);
    if (source.id === 'michelin') { assert.equal(rows.length,110); assert.ok(places.some(p => p.name === 'The Inn at Little Washington' && p.stars === 2)); }
  }
});


test('Best of NoVA preserves all awards and supports category, placement, and open filters', () => {
 const source=sources.find(s=>s.id==='nova');
 const rows=parseCsv(readFileSync(new URL(`../${source.file}`,import.meta.url),'utf8'));
 assert.equal(rows.length,125);
 assert.equal(new Set(rows.map(r=>[r.category,r.place,r.restaurant_name].join('|'))).size,61);
 assert.equal(new Set(rows.map(r=>r.category)).size,31);
 assert.ok(rows.some(r=>r.restaurant_name==='Chloez Café'));
 const p=rows.map(r=>normalizeRow(r,source)).find(p=>p && p.category==='Bagels' && p.placement==='Winner' && p.hours.every(Boolean));
 assert.equal(matchesFilters(p,{...filters,list:'nova',category:'Bagels',placement:'Winner',open:true},new Date('2026-10-07T14:00:00Z')),true);
 assert.equal(matchesFilters(p,{...filters,placement:'Runner-up'}),false);
});


test('happy-hour list retains each venue and separate menu links', () => {
 const source=sources.find(s=>s.id==='happy');
 const rows=parseCsv(readFileSync(new URL(`../${source.file}`,import.meta.url),'utf8'));
 assert.equal(rows.length,58);assert.equal(new Set(rows.map(r=>r.restaurant_name)).size,58);
 assert.ok(rows.every(r=>r.hours_type==='happy_hour' && r.menu_url && r.narrative));
 const open=normalizeRow(rows.find(r=>r.restaurant_name==='Open Road'),source);
 const heirloom=normalizeRow(rows.find(r=>r.restaurant_name==='Heirloom'),source);
 assert.equal(open.hoursType,'happy_hour');assert.ok(open.menuUrl);
 assert.equal(openingStatus(open,new Date('2026-10-07T19:30:00Z')),'open');
 assert.equal(openingStatus(heirloom,new Date('2026-10-07T19:30:00Z')),'closed');
 assert.equal(openingStatus(open,new Date('2026-10-07T22:30:00Z')),'closed');
 assert.deepEqual(parseHours('Not offered'),[]);
 const lazy=normalizeRow(rows.find(r=>r.restaurant_name==='Lazy Dog'),source);
 assert.equal(openingStatus(lazy,new Date('2026-10-08T03:00:00Z')),'open');
 assert.equal(openingStatus(lazy,new Date('2026-10-08T04:00:00Z')),'closed');
 const ometeo={hours:days.map(()=> 'Not offered')};ometeo.hours[6]='11:00-21:30';
 assert.equal(openingStatus(ometeo,new Date('2026-10-11T12:00:00Z')),'closed');
});


test('NoVA Top 50 preserves ranks, branches, cuisine and dish recommendations', () => {
 const source=sources.find(s=>s.id==='top50');
 const rows=parseCsv(readFileSync(new URL(`../${source.file}`,import.meta.url),'utf8'));
 assert.equal(rows.length,53);assert.equal(new Set(rows.map(r=>r.restaurant_name)).size,50);
 assert.deepEqual(rows.filter(r=>r.position).map(r=>r.position),Array.from({length:10},(_,i)=>`No. ${i+1}`));
 assert.ok(rows.every(r=>r.eat_this && r.cuisine && r.narrative && r.hours_type==='opening'));
 const celebration=normalizeRow(rows.find(r=>r.restaurant_name==='Celebration by Rupa Vira'),source);
 assert.equal(celebration.cuisine,'Modern Indian');assert.equal(celebration.position,'No. 9');
 assert.ok(matchesFilters(celebration,{list:'top50',cuisine:'Modern Indian',category:'',placement:'',stars:'',open:false,search:'kale'}));
 for (const name of ['Alias','Carmello’s']) {
  const r=rows.find(r=>r.restaurant_name===name);
  const p=normalizeRow({...r,latitude:'38.8',longitude:'-77.5'},source);
  p.hours=days.map(()=> '24 hours');
  assert.equal(openingStatus(p,new Date('2026-10-07T23:00:00Z')),'closed');
 }
});
