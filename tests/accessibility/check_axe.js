/**
 * Accessibility check (architecture §15 testing matrix "Accessibility: keyboard, focus, labels,
 * alt text and contrast" — the one row of that matrix that had never had a dedicated automated
 * pass before Stage 15, only informal manual browser verification during earlier stages).
 *
 * Runs axe-core (https://github.com/dequelabs/axe-core) against the running frontend's main
 * states: idle homepage, /browse, /basket, and the post-search results grid.
 *
 * Not wired into pytest or CI (it's a Node script needing a real browser download, not a
 * hermetic unit test) -- run it by hand when frontend markup changes meaningfully:
 *
 *   npm install --no-save playwright axe-core   (from this directory, or anywhere with npm)
 *   npx playwright install chromium
 *   node tests/accessibility/check_axe.js
 *
 * Requires the frontend dev server running locally (npm run dev in frontend/, port 3000).
 */

const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const axeSource = fs.readFileSync(
  require.resolve("axe-core/axe.min.js", { paths: [__dirname, process.cwd()] }),
  "utf-8"
);

const BASE_URL = process.env.FRONTEND_URL || "http://127.0.0.1:3000";

const pages = [
  { name: "homepage-idle", url: `${BASE_URL}/` },
  { name: "browse", url: `${BASE_URL}/browse` },
  { name: "basket", url: `${BASE_URL}/basket` },
];

async function scanPage(browser, name, url) {
  const page = await browser.newPage();
  await page.goto(url, { waitUntil: "networkidle" });
  await page.addScriptTag({ content: axeSource });
  const results = await page.evaluate(async () => await axe.run());
  await page.close();
  return { name, url, violations: results.violations };
}

async function scanSearchResults(browser) {
  const page = await browser.newPage();
  await page.goto(`${BASE_URL}/`, { waitUntil: "networkidle" });
  const input = page.locator("input[type='search'], input[type='text'], input[role='searchbox']").first();
  await input.fill("black adidas trainers");
  await input.press("Enter");
  await page.waitForTimeout(2000);
  await page.addScriptTag({ content: axeSource });
  const results = await page.evaluate(async () => await axe.run());
  await page.close();
  return { name: "homepage-search-results", url: `${BASE_URL}/ (after search)`, violations: results.violations };
}

(async () => {
  const browser = await chromium.launch();
  const reports = [];
  for (const p of pages) {
    reports.push(await scanPage(browser, p.name, p.url));
  }
  reports.push(await scanSearchResults(browser));
  await browser.close();

  let anyViolations = false;
  for (const r of reports) {
    console.log(`\n=== ${r.name} (${r.url}) ===`);
    if (r.violations.length === 0) {
      console.log("No axe-core violations.");
      continue;
    }
    anyViolations = true;
    for (const v of r.violations) {
      console.log(`[${v.impact}] ${v.id}: ${v.help} (${v.nodes.length} node(s))`);
      for (const node of v.nodes.slice(0, 3)) {
        console.log(`    ${node.target.join(" ")}`);
      }
    }
  }
  process.exit(anyViolations ? 1 : 0);
})();
