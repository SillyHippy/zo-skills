#!/usr/bin/env node
/**
 * Browser check: reverse-proxy /omniroute/login must hydrate a password form.
 * Catches the "Loading..." forever failure that curl HTTP 200 misses.
 */
import { createRequire } from "node:module";

const require = createRequire("/home/workspace/Projects/omniroute/package.json");
const { chromium } = require("playwright");

const URL =
  process.env.OMNIROUTE_LOGIN_URL ||
  "https://zo-reverse-proxy-sillyhippy.zocomputer.io/omniroute/login";

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));
try {
  await page.goto(URL, { waitUntil: "networkidle", timeout: 45000 });
} catch (e) {
  // networkidle can flake; continue to DOM check
  errors.push(`goto: ${e.message}`);
}
await page.waitForTimeout(5000);
const passwordCount = await page.locator('input[type="password"]').count();
const body = (await page.locator("body").innerText()).slice(0, 240);
await browser.close();

if (passwordCount < 1) {
  console.error(`FAIL login hydrate: no password input at ${URL}`);
  console.error(`body: ${JSON.stringify(body)}`);
  if (errors.length) console.error(`errors: ${errors.slice(0, 5).join(" | ")}`);
  process.exit(1);
}
if (/^Skip to content\s*Loading\.\.\.\s*$/i.test(body.trim()) || body.trim() === "Loading...") {
  console.error(`FAIL login stuck on Loading... at ${URL}`);
  process.exit(1);
}
console.log(`PASS login hydrate: password form visible at ${URL}`);
process.exit(0);
