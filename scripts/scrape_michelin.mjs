/** Browser collector. Install Playwright separately; no credentials are stored. */
import { chromium } from 'playwright';
import { mkdir, writeFile } from 'node:fs/promises';
import { dirname } from 'node:path';
import { createInterface } from 'node:readline/promises';
import { stdin, stdout } from 'node:process';
import { extractRestaurant } from './michelin_extract.mjs';

const start = 'https://guide.michelin.com/us/en/area-united-states-washington-dc-area/restaurants';
const args = process.argv.slice(2);
const output = args.find(a => !a.startsWith('--')) || 'work/michelin_snapshot.json';
const browser = await chromium.launch({ headless: !args.includes('--login') });
const page = await browser.newPage();
const snapshot = { captured_at: new Date().toISOString(), listing_url: start,
  expected_count: null, listing_pages: [], allLinks: [], records: [] };
try {
  await page.goto(start, { waitUntil: 'networkidle' });
  if (args.includes('--login')) {
    const input = createInterface({ input: stdin, output: stdout });
    await input.question('Sign in through the browser if needed, then press Enter here. ');
    input.close();
    await page.goto(start, { waitUntil: 'networkidle' });
  }
  const pending = [start];
  const visited = new Set();
  while (pending.length) {
    const url = pending.shift();
    if (visited.has(url)) continue;
    if (url !== await page.url()) await page.goto(url, { waitUntil: 'networkidle' });
    await page.locator('h1').waitFor();
    const listing = await page.evaluate(() => {
      const title = document.querySelector('h1')?.textContent || '';
      const match = title.match(/(\d+)\s*[-–]\s*(\d+)\s+of\s+([\d,]+)\s+restaurants/i);
      if (!match) throw new Error('Listing count not found; page may be blocked');
      const count = Number(match[2]) - Number(match[1]) + 1;
      // The cards after the advertised range are recommendations, not results.
      const links = [...document.querySelectorAll('h3 a')]
        .filter(a => a.href.includes('/restaurant/')).slice(0, count)
        .map(a => ({ name: a.textContent.trim(), url: a.href }));
      if (links.length !== count) throw new Error('Incomplete listing page');
      const pages = [...document.querySelectorAll('a')].map(a => a.href)
        .filter(u => /^https:\/\/guide\.michelin\.com\/us\/en\/area-united-states-washington-dc-area\/restaurants\/page\/\d+$/.test(u));
      return { links, pages, count, total: Number(match[3].replaceAll(',', '')) };
    });
    if (snapshot.expected_count !== null && snapshot.expected_count !== listing.total)
      throw new Error('Listing changed during harvest; rerun');
    snapshot.expected_count = listing.total;
    snapshot.listing_pages.push({ url, count: listing.count });
    snapshot.allLinks.push(...listing.links);
    pending.push(...listing.pages.filter(u => !visited.has(u)));
    visited.add(url);
  }
  if (new Set(snapshot.allLinks.map(r => r.url)).size !== snapshot.expected_count ||
      snapshot.allLinks.length !== snapshot.expected_count)
    throw new Error('Listing total or uniqueness check failed');
  for (const [i, link] of snapshot.allLinks.entries()) {
    await page.goto(link.url, { waitUntil: 'networkidle' });
    await page.locator('h1.data-sheet__title').first().waitFor();
    const row = await page.evaluate(extractRestaurant);
    if (row.restaurant_name !== link.name) throw new Error(`Unexpected page for ${link.name}`);
    const words = row.narrative.split(/\s+/).filter(Boolean);
    row.narrative = words.slice(0, 20).join(' ') + (words.length > 20 ? ' …' : '');
    snapshot.records.push({ ...row, michelin_url: link.url });
    console.log(`${i + 1}/${snapshot.expected_count}: ${row.restaurant_name}`);
    await page.waitForTimeout(1000); // Polite sequential requests, never concurrent.
  }
  await mkdir(dirname(output), { recursive: true });
  await writeFile(output, JSON.stringify(snapshot, null, 2) + '\n', 'utf8');
  console.log(`Saved ${output}. Run import_michelin.py to validate and export CSV.`);
} finally {
  await browser.close();
}
