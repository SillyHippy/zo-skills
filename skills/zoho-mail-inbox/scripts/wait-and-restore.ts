const BASE = "https://mail.zoho.com";
const ACCOUNT = "3117999000000008002";
const INBOX = "3117999000000008014";
const TRASH = "3117999000000008026";
const CLIENT_ID = "1000.O7DJKTXGWR6BZK1OTXG3VB777TTUVX";
const CLIENT_SECRET = "e04387b26c5e39e879297d414c141a7f0c6ed10332";
const REFRESH_TOKEN = "1000.981eab1d3e0cf080c9b9ef4372eec0d8.dc6f8cd4e19f37a6d8f1a6d197019df7";

async function getToken() {
  const r = await fetch("https://accounts.zoho.com/oauth/v2/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "refresh_token",
      client_id: CLIENT_ID,
      client_secret: CLIENT_SECRET,
      refresh_token: REFRESH_TOKEN,
    }),
  });
  const t = await r.text();
  const d = JSON.parse(t);
  if (!d.access_token) throw new Error(t);
  return d.access_token;
}

async function tryGetToken(maxAttempts = 20, delayMs = 30000) {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const token = await getToken();
      console.log(`Got token on attempt ${i + 1}`);
      return token;
    } catch (e: any) {
      console.log(`Attempt ${i + 1} failed: ${e.message.substring(0, 100)}`);
      if (i < maxAttempts - 1) {
        console.log(`Waiting ${delayMs / 1000}s...`);
        await new Promise(r => setTimeout(r, delayMs));
      }
    }
  }
  throw new Error("Could not get token after all attempts");
}

async function main() {
  console.log("Waiting for OAuth rate limit to clear...");
  const token = await tryGetToken(20, 30000);
  
  // Get trash messages
  let allTrashIds: any[] = [];
  let start = 0;
  
  while (true) {
    const viewUrl = `${BASE}/api/accounts/${ACCOUNT}/messages/view?folderId=${TRASH}&limit=200&start=${start}`;
    const viewResp = await fetch(viewUrl, {
      headers: { Authorization: `Zoho-oauthtoken ${token}` },
    });
    const viewData = await viewResp.json();
    
    if (!viewData.data || !Array.isArray(viewData.data) || viewData.data.length === 0) break;
    
    allTrashIds.push(...viewData.data);
    start += viewData.data.length;
    if (viewData.data.length < 200) break;
  }
  
  console.log(`Found ${allTrashIds.length} messages in trash`);
  
  if (allTrashIds.length === 0) {
    console.log("Trash is empty");
    return;
  }
  
  // Restore all messages
  const batchSize = 10;
  let restored = 0;
  
  for (let i = 0; i < allTrashIds.length; i += batchSize) {
    const batch = allTrashIds.slice(i, i + batchSize);
    const idsParam = batch.map((m: any) => `ids=${encodeURIComponent(String(m.messageId || m.id))}`).join("&");
    const moveUrl = `${BASE}/api/accounts/${ACCOUNT}/messages/move?folderId=${TRASH}&toFolderId=${INBOX}&${idsParam}`;
    
    const r = await fetch(moveUrl, {
      method: "POST",
      headers: { Authorization: `Zoho-oauthtoken ${token}` },
    });
    const txt = await r.text();
    
    if (r.ok) {
      restored += batch.length;
      console.log(`Restored ${restored}/${allTrashIds.length}`);
    } else {
      console.log(`Failed: ${r.status} ${txt.substring(0, 200)}`);
    }
    
    await new Promise(r => setTimeout(r, 2000));
  }
  
  console.log(`DONE: Restored ${restored}/${allTrashIds.length} messages`);
}

main().catch(e => console.error(e));
