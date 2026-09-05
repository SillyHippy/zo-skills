const BASE = "https://mail.zoho.com";
const ACCOUNT = "3117999000000008002";
const TRASH = "3117999000000008026";
const CID = "1000.O7DJKTXGWR6BZK1OTXG3VB777TTUVX";
const CSEC = "e04387b26c5e39e879297d414c141a7f0c6ed10332";
const RT = "1000.981eab1d3e0cf080c9b9ef4372eec0d8.dc6f8cd4e19f37a6d8f1a6d197019df7";

async function getToken() {
  for (let i = 0; i < 5; i++) {
    try {
      const r = await fetch("https://accounts.zoho.com/oauth/v2/token", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ grant_type: "refresh_token", client_id: CID, client_secret: CSEC, refresh_token: RT }),
      });
      const d = await r.json();
      if (d.access_token) return d.access_token;
      console.log(`Token attempt ${i+1}: ${JSON.stringify(d).substring(0, 100)}`);
    } catch (e: any) { console.log(`Token attempt ${i+1} error: ${e.message}`); }
    await new Promise(r => setTimeout(r, 20000));
  }
  return null;
}

async function main() {
  const token = await getToken();
  if (!token) { console.log("No token"); process.exit(1); }

  // Check trash
  const r1 = await fetch(`${BASE}/api/accounts/${ACCOUNT}/messages/view?folderId=${TRASH}&limit=200`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  const d1 = await r1.json();
  const trashCount = (d1.data?.data || []).length;
  console.log(`Trash messages: ${trashCount}`);

  // Check inbox count
  const INBOX = "3117999000000008014";
  const r2 = await fetch(`${BASE}/api/accounts/${ACCOUNT}/messages/view?folderId=${INBOX}&limit=1`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  const d2 = await r2.json();
  const inboxTotal = d2.data?.count || 0;
  console.log(`Inbox messages: ${inboxTotal}`);

  // List all folders with counts
  const r3 = await fetch(`${BASE}/api/accounts/${ACCOUNT}/folders`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  const d3 = await r3.json();
  console.log("\nFolders:");
  if (d3.data?.data) {
    for (const f of d3.data.data) {
      console.log(`  ${f.folderName} (${f.folderId}): ${f.unreadCount || 0} unread, ${f.totalCount || 0} total`);
    }
  }
}

main();
