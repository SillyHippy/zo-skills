// Try folder-based move and action-based endpoints
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

const sr = await fetch(`${BASE}/api/accounts/${ACCOUNT}/messages/search?searchKey=folder:${TRASH}&limit=1&includeto=false`, { headers: h });
const sd = await sr.json();
if (!sd.data?.length) { console.log("No trash msgs"); process.exit(0); }
const msgId = sd.data[0].messageId;

const endpoints = [
  // Folder operations
  { m: "POST", p: `/api/accounts/${ACCOUNT}/folders/moveMessages`, b: { sourceFolderId: TRASH, destinationFolderId: INBOX, messageIds: [msgId] } },
  { m: "POST", p: `/api/accounts/${ACCOUNT}/folders/${TRASH}/messages`, b: { action: "move", destFolderId: INBOX, ids: [msgId] } },
  // Message actions
  { m: "POST", p: `/api/accounts/${ACCOUNT}/messages/${msgId}`, b: { action: "move", folderId: INBOX } },
  // Change folder
  { m: "POST", p: `/api/accounts/${ACCOUNT}/messages/changeFolder`, b: { messageIds: [`${TRASH}:${msgId}`], destFolderId: INBOX } },
  // Bulk operations
  { m: "POST", p: `/api/accounts/${ACCOUNT}/messages/bulkMove`, b: { ids: [msgId], toFolder: INBOX, fromFolder: TRASH } },
  // Restore from trash specifically
  { m: "POST", p: `/api/accounts/${ACCOUNT}/trash/restore`, b: { messageIds: [msgId] } },
  { m: "POST", p: `/api/accounts/${ACCOUNT}/messages/emptyTrash`, b: {} }, // maybe has restore option
];

for (const ep of endpoints) {
  try {
    const resp = await fetch(`${BASE}${ep.p}`, { method: ep.m, headers: { ...h, "Content-Type": "application/json" }, body: JSON.stringify(ep.b) });
    const txt = await resp.text();
    console.log(`${ep.m} ${ep.p} -> ${resp.status}: ${txt.substring(0, 120)}`);
  } catch (e: any) { console.log(`${ep.m} ${ep.p} -> ERR: ${e.message}`); }
  await new Promise(s => setTimeout(s, 300));
}
