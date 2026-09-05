// Try recovery/undelete endpoints
const BASE = "https://mail.zoho.com";
const ACCOUNT = "3117999000000008002";
const TRASH = "3117999000000008026";

const r = await fetch("https://accounts.zoho.com/oauth/v2/token", {
  method: "POST",
  headers: { "Content-Type": "application/x-www-form-urlencoded" },
  body: new URLSearchParams({ grant_type: "refresh_token", client_id: "1000.O7DJKTXGWR6BZK1OTXG3VB777TTUVX", client_secret: "e04387b26c5e39e879297d414c141a7f0c6ed10332", refresh_token: "1000.981eab1d3e0cf080c9b9ef4372eec0d8.dc6f8cd4e19f37a6d8f1a6d197019df7" }),
});
const d = await r.json();
const h = { Authorization: `Bearer ${d.access_token}` };

const sr = await fetch(`${BASE}/api/accounts/${ACCOUNT}/messages/search?searchKey=folder:${TRASH}&limit=1&includeto=false`, { headers: h });
const sd = await sr.json();
if (!sd.data?.length) { console.log("No trash"); process.exit(0); }
const msgId = sd.data[0].messageId;

const endpoints = [
  // Different HTTP methods on /messages
  { m: "PATCH", p: `/api/accounts/${ACCOUNT}/messages/${msgId}`, b: { folderId: "3117999000000008014" } },
  { m: "DELETE", p: `/api/accounts/${ACCOUNT}/messages/${TRASH}:${msgId}`, b: undefined },
  // Undelete
  { m: "POST", p: `/api/accounts/${ACCOUNT}/messages/${msgId}/undelete`, b: {} },
  { m: "POST", p: `/api/accounts/${ACCOUNT}/messages/${msgId}/recover`, b: {} },
  // Zoho API v2 style
  { m: "POST", p: `/api/v2/accounts/${ACCOUNT}/messages/move`, b: { ids: msgId, folder: "3117999000000008014" } },
  // Using the view API with action param
  { m: "POST", p: `/api/accounts/${ACCOUNT}/view/${TRASH}/${msgId}?action=restore`, b: {} },
  { m: "GET", p: `/api/accounts/${ACCOUNT}/messages/${msgId}/restore`, b: undefined },
];

for (const ep of endpoints) {
  try {
    const opts: any = { method: ep.m, headers: h };
    if (ep.b) opts.headers["Content-Type"] = "application/json";
    if (ep.b) opts.body = JSON.stringify(ep.b);
    const resp = await fetch(`${BASE}${ep.p}`, opts);
    const txt = await resp.text();
    console.log(`${ep.m} ${ep.p} -> ${resp.status}: ${txt.substring(0, 120)}`);
  } catch (e: any) { console.log(`${ep.m} ${ep.p} -> ERR: ${e.message}`); }
  await new Promise(s => setTimeout(s, 300));
}
