const BASE_URL = "https://mail.zoho.com";
const ACCOUNT = "3117999000000008002";
const CLIENT_ID = "1000.O7DJKTXGWR6BZK1OTXG3VB777TTUVX";
const CLIENT_SECRET = "e04387b26c5e39e879297d414c141a7f0c6ed10332";
const REFRESH_TOKEN = "1000.981eab1d3e0cf080c9b9ef4372eec0d8.dc6f8cd4e19f37a6d8f1a6d197019df7";
const TRASH = "3117999000000008026";
const INBOX = "3117999000000008014";

async function getToken() {
  const resp = await fetch("https://accounts.zoho.com/oauth/v2/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "refresh_token",
      client_id: CLIENT_ID,
      client_secret: CLIENT_SECRET,
      refresh_token: REFRESH_TOKEN,
    }),
  });
  return (await resp.json()).access_token;
}

async function test() {
  const token = await getToken();
  const authHeaders = { Authorization: `Bearer ${token}` };

  // Get all trash message IDs using the search approach that worked
  let allMessages: any[] = [];
  let start = 0;
  while (true) {
    const resp = await fetch(`${BASE_URL}/api/accounts/${ACCOUNT}/messages/search?searchKey=folder:${TRASH}&limit=200&start=${start}&includeto=false`, { headers: authHeaders });
    const data = await resp.json();
    const items = Array.isArray(data.data) ? data.data : [];
    for (const m of items) allMessages.push(m);
    if (items.length < 200) break;
    start += 200;
  }

  console.log(`Found ${allMessages.length} messages in trash`);
  if (allMessages.length === 0) { console.log("Nothing to restore"); return; }

  for (const m of allMessages) {
    console.log(`  msgId: ${m.messageId}, original folderId: ${m.folderId}, subject: ${(m.subject || "").substring(0,60)}`);
  }

  const testMsg = allMessages[0];
  const msgId = testMsg.messageId;
  const originalFolderId = testMsg.folderId;

  // Test various move endpoints
  const tests = [
    { method: "POST", url: `${BASE_URL}/api/accounts/${ACCOUNT}/messages/${TRASH}/${msgId}/move`, body: JSON.stringify({ destFolderId: originalFolderId }) },
    { method: "POST", url: `${BASE_URL}/api/accounts/${ACCOUNT}/messages/${TRASH}/${msgId}/move`, body: JSON.stringify({ folderId: originalFolderId }) },
    { method: "POST", url: `${BASE_URL}/api/accounts/${ACCOUNT}/folders/${TRASH}/messages/${msgId}/move`, body: JSON.stringify({ destFolderId: originalFolderId }) },
    { method: "PUT", url: `${BASE_URL}/api/accounts/${ACCOUNT}/messages/${TRASH}/${msgId}`, body: JSON.stringify({ folderId: originalFolderId }) },
  ];

  for (const t of tests) {
    console.log(`\nTesting: ${t.method} ${t.url.replace(BASE_URL, '')}`);
    const resp = await fetch(t.url, { method: t.method as any, headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }, body: t.body });
    console.log(`Status: ${resp.status}, Body: ${(await resp.text()).substring(0, 400)}`);
  }
}

test().catch(console.error);
