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
  if (!d.access_token) throw new Error("No token: " + t);
  return d.access_token;
}

async function main() {
  const token = await getToken();
  console.log("Got token");
  
  // Get trash messages using view API
  const viewUrl = `${BASE}/api/accounts/${ACCOUNT}/messages/view?folderId=${TRASH}&limit=200&start=0`;
  const viewResp = await fetch(viewUrl, {
    headers: { Authorization: `Zoho-oauthtoken ${token}` },
  });
  const viewData = await viewResp.json();
  console.log("View status:", JSON.stringify(viewData.status));
  
  let trashIds: any[] = [];
  if (viewData.data && Array.isArray(viewData.data)) {
    trashIds = viewData.data;
  }
  console.log(`Found ${trashIds.length} trash messages`);
  
  if (trashIds.length === 0) {
    console.log("Trash is empty");
    return;
  }
  
  // Show first few
  for (const m of trashIds.slice(0, 5)) {
    console.log(`  msgId: ${m.messageId || m.id}, subject: ${m.subject?.substring(0, 50)}, fromFolder: ${m.folderId}`);
  }
  
  // Try multiple move endpoint variations
  const batch = trashIds.slice(0, 5);
  const firstId = batch[0].messageId || batch[0].id;
  
  const tests = [
    // POST /messages/move with folderId and toFolderId
    { method: "POST", url: `${BASE}/api/accounts/${ACCOUNT}/messages/move?folderId=${TRASH}&toFolderId=${INBOX}&ids=${firstId}` },
    // POST /messages/{id}/move
    { method: "POST", url: `${BASE}/api/accounts/${ACCOUNT}/messages/${firstId}/move`, body: { toFolderId: INBOX } },
    // PUT /messages/{id}/move
    { method: "PUT", url: `${BASE}/api/accounts/${ACCOUNT}/messages/${firstId}/move`, body: { toFolderId: INBOX } },
    // POST /messages/changeFolder
    { method: "POST", url: `${BASE}/api/accounts/${ACCOUNT}/messages/changeFolder`, body: { messageIds: [firstId], toFolderId: INBOX } },
    // POST /messages/moveMessages
    { method: "POST", url: `${BASE}/api/accounts/${ACCOUNT}/messages/moveMessages`, body: { messageIds: [firstId], toFolderId: INBOX } },
    // POST /messages with action=move
    { method: "POST", url: `${BASE}/api/accounts/${ACCOUNT}/messages`, body: { action: "move", messageIds: [firstId], toFolderId: INBOX } },
  ];
  
  for (const test of tests) {
    console.log(`\nTesting ${test.method}: ${test.url.substring(0, 120)}...`);
    const r = await fetch(test.url, {
      method: test.method,
      headers: { Authorization: `Zoho-oauthtoken ${token}`, "Content-Type": "application/json" },
      body: test.body ? JSON.stringify(test.body) : undefined,
    });
    const txt = await r.text();
    console.log(`${r.status}: ${txt.substring(0, 300)}`);
  }
}

main().catch(e => console.error(e));
