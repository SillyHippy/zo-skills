import { $ } from "bun";

const BASE = "https://mail.zoho.com";
const ACCOUNT = "3117999000000008002";
const TRASH = "3117999000000008026";
const CID = "1000.O7DJKTXGWR6BZK1OTXG3VB777TTUVX";
const CSEC = "e04387b26c5e39e879297d414c141a7f0c6ed10332";
const RT = "1000.981eab1d3e0cf080c9b9ef4372eec0d8.dc6f8cd4e19f37a6d8f1a6d197019df7";

// Get OAuth token
const tokResp = await fetch("https://accounts.zoho.com/oauth/v2/token", {
  method: "POST",
  headers: { "Content-Type": "application/x-www-form-urlencoded" },
  body: new URLSearchParams({ grant_type: "refresh_token", client_id: CID, client_secret: CSEC, refresh_token: RT }),
});
const tokData = await tokResp.json();
if (!tokData.access_token) { console.error("No token:", JSON.stringify(tokData)); Deno.exit(1); }
const h = { Authorization: `Bearer ${tokData.access_token}` };

// Search trash
let msgs: any[] = [];
let start = 0;
while (true) {
  const r = await fetch(`${BASE}/api/accounts/${ACCOUNT}/messages/search?searchKey=folder:${TRASH}&limit=200&start=${start}&includeto=false`, { headers: h });
  const d = await r.json();
  if (d.data && Array.isArray(d.data)) msgs.push(...d.data);
  if (!d.data || !Array.isArray(d.data) || d.data.length < 200) break;
  start += 200;
  await new Promise(r => setTimeout(r, 500));
}
console.log(`Found ${msgs.length} in trash`);
if (msgs.length === 0) { console.log("Empty trash. Done."); Deno.exit(0); }

// Group by original folder
const groups: Record<string, string[]> = {};
for (const m of msgs) {
  const fid = m.folderId || "3117999000000008014";
  (groups[fid] ||= []).push(m.messageId);
}

// Move back
let restored = 0, failed = 0;
for (const [fid, mids] of Object.entries(groups)) {
  for (let i = 0; i < mids.length; i += 50) {
    const batch = mids.slice(i, i + 50);
    const body = { messageIds: batch.map(id => `${TRASH}:${id}`), destFolderId: fid };
    const mr = await fetch(`${BASE}/api/accounts/${ACCOUNT}/messages/move`, {
      method: "POST",
      headers: { ...h, "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const mt = await mr.text();
    if (mr.ok || mr.status === 200) { restored += batch.length; }
    else { failed += batch.length; console.log(`FAIL: ${mr.status} ${mt}`); }
    await new Promise(r => setTimeout(r, 400));
  }
}
console.log(`Restored: ${restored}, Failed: ${failed}`);
