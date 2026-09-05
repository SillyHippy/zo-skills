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
      const text = await r.text();
      const d = JSON.parse(text);
      if (d.access_token) return d.access_token;
      console.log(`Token attempt ${i+1}: ${text.substring(0, 100)}`);
    } catch (e: any) {
      console.log(`Token attempt ${i+1} error: ${e.message}`);
    }
    await new Promise(r => setTimeout(r, 15000));
  }
  return null;
}

async function main() {
  const token = await getToken();
  if (!token) { console.log("Could not get token"); process.exit(1); }

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
    console.log("Trash is empty - nothing to restore");
    process.exit(0);
  }

  let restored = 0;
  let failed = 0;

  for (const m of allMsgs) {
    const msgId = m.messageId;
    const origFolder = m.folderId;

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
      }
    } catch (e) {
      failed++;
    }
  }

  console.log(`Result: ${restored} restored, ${failed} failed out of ${allMsgs.length}`);
}

main();
