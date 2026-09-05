const BASE = "https://mail.zoho.com";
const ACCOUNT = "3117999000000008002";
const INBOX = "3117999000000008014";
const TRASH = "3117999000000008026";
const CLIENT_ID = "1000.O7DJKTXGWR6BZK1OTXG3VB777TTUVX";
const CLIENT_SECRET = "e04387b26c5e39e879297d414c141a7f0c6ed10332";
const REFRESH_TOKEN = "1000.981eab1d3e0cf080c9b9ef4372eec0d8.dc6f8cd4e19f37a6d8f1a6d197019df7";

async function getToken() {
  for (let attempt = 0; attempt < 10; attempt++) {
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
    try {
      const d = JSON.parse(t);
      if (d.access_token) {
        console.log(`Got token on attempt ${attempt + 1}`);
        return d.access_token;
      }
      console.log(`Attempt ${attempt + 1} failed: ${d.error_description || t.substring(0, 100)}`);
    } catch {}
    if (attempt < 9) await new Promise(r => setTimeout(r, 30000));
  }
  throw new Error("Could not get token");
}

async function main() {
  const token = await getToken();
  console.log("Token acquired, getting trash messages...");
  
  // Get all trash messages using view API with pagination
  let allTrashIds: string[] = [];
  let start = 0;
  
  while (true) {
    const viewUrl = `${BASE}/api/accounts/${ACCOUNT}/messages/view?folderId=${TRASH}&limit=200&start=${start}`;
    const viewResp = await fetch(viewUrl, {
      headers: { Authorization: `Zoho-oauthtoken ${token}` },
    });
    const viewData = await viewResp.json();
    
    if (!viewData.data || !Array.isArray(viewData.data) || viewData.data.length === 0) break;
    
    for (const m of viewData.data) {
      allTrashIds.push(String(m.messageId || m.id));
    }
    start += viewData.data.length;
    if (viewData.data.length < 200) break;
  }
  
  console.log(`Found ${allTrashIds.length} trash messages`);
  
  if (allTrashIds.length === 0) {
    console.log("Trash is empty");
    return;
  }
  
  // Restore all messages using the correct Zoho API
  // Based on testing, the endpoint that works is:
  // POST /api/accounts/{accountId}/messages/move?folderId={fromFolderId}&toFolderId={toFolderId}&ids={id1}&ids={id2}...
  const batchSize = 10;
  let restored = 0, failed = 0;
  
  for (let i = 0; i < allTrashIds.length; i += batchSize) {
    const batch = allTrashIds.slice(i, i + batchSize);
    const idsParam = batch.map(id => `ids=${encodeURIComponent(id)}`).join("&");
    const moveUrl = `${BASE}/api/accounts/${ACCOUNT}/messages/move?folderId=${TRASH}&toFolderId=${INBOX}&${idsParam}`;
    
    const r = await fetch(moveUrl, {
      method: "POST",
      headers: { Authorization: `Zoho-oauthtoken ${token}`, "Content-Type": "application/json" },
    });
    const txt = await r.text();
    
    if (r.ok) {
      restored += batch.length;
      console.log(`Restored batch of ${batch.length} (${i + batch.length}/${allTrashIds.length})`);
    } else {
      failed += batch.length;
      console.log(`Failed batch ${i / batchSize + 1}: ${r.status} ${txt.substring(0, 200)}`);
    }
    
    // Rate limit protection
    await new Promise(r => setTimeout(r, 2000));
  }
  
  console.log(`\nDONE: Restored: ${restored}, Failed: ${failed}`);
}

main().catch(e => console.error(e));
