const BASE = "https://mail.zoho.com";
const ACCOUNT = "3117999000000008002";
const TRASH = "3117999000000008026";

async function getToken() {
  // Try multiple token endpoints (Zoho EU/IN/COM)
  for (const host of ["https://accounts.zoho.com", "https://accounts.zoho.eu"]) {
    try {
      const resp = await fetch(`${host}/oauth/v2/token`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
          grant_type: "refresh_token",
          client_id: "1000.O7DJKTXGWR6BZK1OTXG3VB777TTUVX",
          client_secret: "e04387b26c5e39e879297d414c141a7f0c6ed10332",
          refresh_token: "1000.981eab1d3e0cf080c9b9ef4372eec0d8.dc6f8cd4e19f37a6d8f1a6d197019df7",
        }),
      });
      const data = await resp.json();
      if (data.access_token) return data.access_token;
    } catch (e) {}
  }
  throw new Error("Could not get token");
}

async function main() {
  let token;
  for (let attempt = 0; attempt < 5; attempt++) {
    try {
      token = await getToken();
      break;
    } catch (e) {
      console.log(`Token attempt ${attempt + 1} failed, waiting...`);
      await new Promise(r => setTimeout(r, 5000));
    }
  }
  if (!token) { process.exit(1); }

  const headers = { Authorization: `Bearer ${token}` };

  // Search trash messages
  let trashMsgs: any[] = [];
  let start = 0;
  while (true) {
    const resp = await fetch(`${BASE}/api/accounts/${ACCOUNT}/messages/search?searchKey=folder:${TRASH}&limit=200&start=${start}&includeto=false`, { headers });
    const data = await resp.json();
    console.log("Search response status:", data.status?.code, JSON.stringify(data.data).substring(0, 200));
    if (Array.isArray(data.data) && data.data.length > 0) {
      trashMsgs.push(...data.data);
    }
    if (!Array.isArray(data.data) || data.data.length < 200) break;
    start += 200;
    await new Promise(r => setTimeout(r, 1000));
  }

  console.log(`Found ${trashMsgs.length} messages in trash`);

  if (trashMsgs.length === 0) {
    // Try messages/view endpoint for trash
    let startV = 1;
    while (true) {
      const resp = await fetch(`${BASE}/api/accounts/${ACCOUNT}/messages/view?folderId=${TRASH}&limit=200&start=${startV}&includeto=false`, { headers });
      const data = await resp.json();
      console.log("View response status:", data.status?.code, JSON.stringify(data.data).substring(0, 200));
      if (Array.isArray(data.data) && data.data.length > 0) {
        trashMsgs.push(...data.data);
      }
      if (!Array.isArray(data.data) || data.data.length < 200) break;
      startV += 200;
      await new Promise(r => setTimeout(r, 1000));
    }
    console.log(`Found ${trashMsgs.length} messages via view`);
  }

  if (trashMsgs.length === 0) {
    console.log("NO MESSAGES FOUND IN TRASH. Nothing to restore.");
    return;
  }

  console.log("Messages to restore:");
  for (const m of trashMsgs.slice(0, 20)) {
    console.log(`  msgId=${m.messageId}, folderId=${m.folderId}, subject=${m.subject?.substring(0, 60)}`);
  }

  // Move each message back to its original folder
  let restored = 0;
  let failed = 0;
  for (const msg of trashMsgs) {
    const origFolder = msg.folderId || "3117999000000008014"; // default to Inbox
    if (origFolder === TRASH) continue;
    
    try {
      const moveResp = await fetch(`${BASE}/api/accounts/${ACCOUNT}/messages/move`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({
          ids: [`${TRASH}:${msg.messageId}`],
          destination: { folderId: origFolder },
        }),
      });
      const moveData = await moveResp.json();
      if (moveData.status?.code === 200 || moveData.status?.code === 201) {
        restored++;
      } else {
        failed++;
        console.log(`Failed to move ${msg.messageId}: ${JSON.stringify(moveData)}`);
      }
    } catch (e) {
      failed++;
      console.log(`Error moving ${msg.messageId}: ${e}`);
    }
    await new Promise(r => setTimeout(r, 500));
  }

  console.log(`Done. Restored: ${restored}, Failed: ${failed}`);
}

main();
