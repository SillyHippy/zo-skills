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

// Method 1: search
let s1: any[] = [];
let start = 0;
while (true) {
  const resp = await fetch(`${BASE}/api/accounts/${ACCOUNT}/messages/search?searchKey=folder:${TRASH}&limit=200&start=${start}&includeto=false`, { headers: h });
  const data = await resp.json();
  if (data.data && Array.isArray(data.data)) s1.push(...data.data);
  if (!data.data || !Array.isArray(data.data) || data.data.length < 200) break;
  start += 200;
}
console.log(`Search method found: ${s1.length}`);

// Method 2: messages/view with folderId
let s2: any[] = [];
start = 1;
while (true) {
  const resp = await fetch(`${BASE}/api/accounts/${ACCOUNT}/messages/view?folderId=${TRASH}&limit=200&start=${start}&includeto=false`, { headers: h });
  const data = await resp.json();
  if (data.data && Array.isArray(data.data)) s2.push(...data.data);
  if (!data.data || !Array.isArray(data.data) || data.data.length < 200) break;
  start += 200;
}
console.log(`View method found: ${s2.length}`);

// Method 3: Check inbox count
const inboxResp = await fetch(`${BASE}/api/accounts/${ACCOUNT}/messages/search?searchKey=folder:3117999000000008014&limit=5&includeto=false`, { headers: h });
const inboxData = await inboxResp.json();
console.log(`Inbox sample:`, inboxData.data?.length || 0, "messages");
if (inboxData.data?.length) {
  inboxData.data.forEach((m: any) => console.log(`  ${m.subject?.substring(0, 60)}`));
}
