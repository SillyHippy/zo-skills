// Test different Zoho API endpoints for moving/restoring messages
const BASE = "https://mail.zoho.com";
const ACCOUNT = "3117999000000008002";
const TRASH = "3117999000000008026";
const INBOX = "3117999000000008014";

const r = await fetch("https://accounts.zoho.com/oauth/v2/token", {
  method: "POST",
  headers: { "Content-Type": "application/x-www-form-urlencoded" },
  body: new URLSearchParams({ grant_type: "refresh_token", client_id: "1000.O7DJKTXGWR6BZK1OTXG3VB777TTUVX", client_secret: "e04387b26c5e39e879297d414c141a7f0c6ed10332", refresh_token: "1000.981eab1d3e0cf080c9b9ef4372eec0d8.dc6f8cd4e19f37a6d8f1a6d197019df7" }),
});
const d = await r.json();
const h = { Authorization: `Bearer ${d.access_token}` };

// Get a trash message to test with
const sr = await fetch(`${BASE}/api/accounts/${ACCOUNT}/messages/search?searchKey=folder:${TRASH}&limit=1&includeto=false`, { headers: h });
const sd = await sr.json();
if (!sd.data || !Array.isArray(sd.data) || sd.data.length === 0) { console.log("No trash msgs"); process.exit(0); }
const msg = sd.data[0];
const msgId = msg.messageId;
console.log(`Testing with msgId=${msgId}, folderId=${msg.folderId}`);

const endpoints = [
  { method: "POST", path: `/api/accounts/${ACCOUNT}/messages/move`, body: { messageIds: [`${TRASH}:${msgId}`], destFolderId: INBOX } },
  { method: "POST", path: `/api/accounts/${ACCOUNT}/messages/move`, body: { ids: [`${TRASH}:${msgId}`], destination: { folderId: INBOX } } },
  { method: "POST", path: `/api/accounts/${ACCOUNT}/messages/${TRASH}:${msgId}/move`, body: { destFolderId: INBOX } },
  { method: "POST", path: `/api/accounts/${ACCOUNT}/messages/${TRASH}:${msgId}/restore`, body: {} },
  { method: "POST", path: `/api/accounts/${ACCOUNT}/view/${TRASH}/${msgId}`, body: { action: "restore", destFolderId: INBOX } },
  { method: "PUT", path: `/api/accounts/${ACCOUNT}/messages/${TRASH}:${msgId}`, body: { folderId: INBOX } },
  { method: "POST", path: `/api/accounts/${ACCOUNT}/messages/restore`, body: { ids: [`${TRASH}:${msgId}`] } },
  { method: "POST", path: `/api/accounts/${ACCOUNT}/folders/${TRASH}/messages/move`, body: { messageIds: [`${TRASH}:${msgId}`], destFolderId: INBOX } },
];

for (const ep of endpoints) {
  try {
    const r = await fetch(`${BASE}${ep.path}`, {
      method: ep.method,
      headers: { ...h, "Content-Type": "application/json" },
      body: JSON.stringify(ep.body),
    });
    const t = await r.text();
    console.log(`${ep.method} ${ep.path} -> ${r.status}: ${t.substring(0, 150)}`);
  } catch (e: any) {
    console.log(`${ep.method} ${ep.path} -> ERROR: ${e.message}`);
  }
  await new Promise(s => setTimeout(s, 300));
}
