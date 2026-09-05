const BASE = "https://mail.zoho.com";
const ACCOUNT = "3117999000000008002";
const TRASH = "3117999000000008026";
const CID = "1000.O7DJKTXGWR6BZK1OTXG3VB777TTUVX";
const CSEC = "e04387b26c5e39e879297d414c141a7f0c6ed10332";
const RT = "1000.981eab1d3e0cf080c9b9ef4372eec0d8.dc6f8cd4e19f37a6d8f1a6d197019df7";

async function getToken() {
  for (let i = 0; i < 3; i++) {
    try {
      const r = await fetch("https://accounts.zoho.com/oauth/v2/token", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ grant_type: "refresh_token", client_id: CID, client_secret: CSEC, refresh_token: RT }),
      });
      const d = await r.json();
      if (d.access_token) return d.access_token;
    } catch (e) {}
    if (i < 2) await new Promise(r => setTimeout(r, 10000));
  }
  return null;
}

async function main() {
  const token = await getToken();
  if (!token) { console.log("No token"); process.exit(1); }

  // Get all trash messages
  let allMsgs: any[] = [];
  let start = 0;
  while (true) {
    const r = await fetch(`${BASE}/api/accounts/${ACCOUNT}/messages/view?folderId=${TRASH}&limit=200&start=${start}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    const d = await r.json();
    const msgs = d.data?.data || [];
    allMsgs.push(...msgs);
    if (msgs.length < 200) break;
    start += 200;
  }

  console.log(`Found ${allMsgs.length} messages in trash`);

  if (allMsgs.length === 0) {
    console.log("Trash is already empty");
    process.exit(0);
  }

  // Move messages back to their original folders
  let restored = 0;
  let failed = 0;

  for (const m of allMsgs) {
    const msgId = m.messageId;
    const origFolder = m.folderId; // The folder it came from before being trashed

    // Zoho's move API: POST /api/accounts/{accountId}/messages/{messageId}/move?destFolderId={folderId}
    try {
      const r = await fetch(`${BASE}/api/accounts/${ACCOUNT}/messages/${msgId}/move?destFolderId=${origFolder}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      });
      const d = await r.json();
      if (d.status?.code === 200) {
        restored++;
      } else {
        failed++;
        console.log(`Failed: ${msgId} -> ${origFolder}: ${JSON.stringify(d)}`);
      }
    } catch (e: any) {
      failed++;
      console.log(`Error: ${msgId}: ${e.message}`);
    }

    if (restored % 50 === 0) {
      console.log(`Restored ${restored}, failed ${failed}...`);
    }
  }

  console.log(`Done: ${restored} restored, ${failed} failed`);
}

main();
