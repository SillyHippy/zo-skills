// Try Zoho APIs domain (www.zohoapis.com)
const BASE = "https://www.zohoapis.com";
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

// First test if this domain works for reading
const sr = await fetch(`${BASE}/mail/api/v1/accounts/${ACCOUNT}/messages/search?searchKey=folder:${TRASH}&limit=1`, { headers: h });
const sd = await sr.json();
console.log("Search on zohoapis.com:", sr.status, JSON.stringify(sd).substring(0, 150));

// If search works, try move
if (sd.data?.length) {
  const msgId = sd.data[0].messageId;
  const mr = await fetch(`${BASE}/mail/api/v1/accounts/${ACCOUNT}/messages/move`, {
    method: "POST",
    headers: { ...h, "Content-Type": "application/json" },
    body: JSON.stringify({ messageIds: [msgId], destFolderId: INBOX }),
  });
  const mt = await mr.text();
  console.log("Move on zohoapis.com:", mr.status, mt.substring(0, 200));
}
