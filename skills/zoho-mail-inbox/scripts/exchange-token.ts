// Get a fresh token and try to exchange for web session cookies
const r = await fetch("https://accounts.zoho.com/oauth/v2/token", {
  method: "POST",
  headers: { "Content-Type": "application/x-www-form-urlencoded" },
  body: new URLSearchParams({ grant_type: "refresh_token", client_id: "1000.O7DJKTXGWR6BZK1OTXG3VB777TTUVX", client_secret: "e04387b26c5e39e879297d414c141a7f0c6ed10332", refresh_token: "1000.981eab1d3e0cf080c9b9ef4372eec0d8.dc6f8cd4e19f37a6d8f1a6d197019df7" }),
});
const d = await r.json();
const token = d.access_token;

// Try various exchange endpoints
const endpoints = [
  "https://accounts.zoho.com/oauth/token/exchange?service=VirtualOffice&token=" + token,
  "https://accounts.zoho.com/oauth/v2/token/exchange?service=VirtualOffice&token=" + token,
  "https://accounts.zoho.com/oa/oauth/v2/token/exchange?service=VirtualOffice&token=" + token,
];

for (const url of endpoints) {
  try {
    const resp = await fetch(url, { method: "GET", redirect: "manual" });
    const cookies = resp.headers.get("set-cookie");
    console.log(`GET ${url.substring(0, 60)} -> ${resp.status}`);
    if (cookies) console.log(`  Cookies: ${cookies.substring(0, 200)}`);
    if (resp.status === 302) console.log(`  Location: ${resp.headers.get("location")}`);
  } catch (e: any) { console.log(`  ERR: ${e.message}`); }
}

// Also try POST with proper params
const resp = await fetch("https://accounts.zoho.com/oauth/token/exchange", {
  method: "POST",
  headers: { "Content-Type": "application/x-www-form-urlencoded" },
  body: new URLSearchParams({ service: "VirtualOffice", token }),
  redirect: "manual",
});
const cookies = resp.headers.get("set-cookie");
console.log(`POST exchange -> ${resp.status}`);
if (cookies) console.log(`  Cookies: ${cookies.substring(0, 300)}`);
if (resp.status === 302) console.log(`  Location: ${resp.headers.get("location")}`);
