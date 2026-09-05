const BASE_URL = "https://mail.zoho.com";
const ACCOUNT = "3117999000000008002";
const TRASH = "3117999000000008026";
const INBOX = "3117999000000008014";
const CLIENT_ID = "1000.O7DJKTXGWR6BZK1OTXG3VB777TTUVX";
const CLIENT_SECRET = "e04387b26c5e39e879297d414c141a7f0c6ed10332";
const REFRESH_TOKEN = "1000.981eab1d3e0cf080c9b9ef4372eec0d8.dc6f8cd4e19f37a6d8f1a6d197019df7";

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
  const data = await resp.json();
  if (data.error) {
    console.error("OAuth error:", data.error, data.error_description);
    process.exit(1);
  }
  return data.access_token;
}

async function api(path: string, opts: RequestInit = {}): Promise<any> {
  const token = await getToken();
  const resp = await fetch(`${BASE_URL}/api${path}`, {
    ...opts,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      ...opts.headers,
    },
  });
  const text = await resp.text();
  try {
    return JSON.parse(text);
  } catch {
    return { raw: text.substring(0, 500) };
  }
}

async function main() {
  // Get all trash messages
  let allTrash: any[] = [];
  let start = 1;
  
  while (true) {
    const resp = await api(`/accounts/${ACCOUNT}/messages/view?folderId=${TRASH}&limit=200&start=${start}`);
    const items = resp.data;
    if (!items || !Array.isArray(items) || items.length === 0) break;
    allTrash.push(...items);
    if (items.length < 200) break;
    start += 200;
  }
  
  console.log(`Total messages in Trash: ${allTrash.length}`);
  
  if (allTrash.length === 0) {
    console.log("Trash is empty - nothing to restore.");
    return;
  }
  
  // Show first few
  for (const m of allTrash.slice(0, 10)) {
    console.log(`  ${m.messageId} | From: ${m.fromAddress} | Subject: ${(m.subject || "").substring(0, 70)}`);
  }
  if (allTrash.length > 10) console.log(`  ... and ${allTrash.length - 10} more`);
  
  // Analyze senders to guess original folders
  const senderFolderMap: Record<string, string> = {
    "servetracker.tech": "3117999000000008014",  // Inbox
    "noreply@proofserve.com": "3117999000000008014",  // Inbox
    "donotreply@app.helcim.com": "3117999000000374023",  // Helcim
    "hello@buffermail.com": "3117999000000009011",  // Newsletter
    "noreply@zohoaccounts.com": "3117999000000009001",  // Notification
  };
  
  // Try restoring first message using different approaches
  const first = allTrash[0];
  console.log(`\nTrying restore on message ${first.messageId}...`);
  
  const tests = [
    {
      desc: "POST messages/{id}/move {destFolderId}",
      path: `/accounts/${ACCOUNT}/messages/${first.messageId}/move`,
      opts: { method: "POST", body: JSON.stringify({ destFolderId: INBOX }) }
    },
    {
      desc: "POST messages/{trash}/{id}/move {destFolderId}",
      path: `/accounts/${ACCOUNT}/messages/${TRASH}/${first.messageId}/move`,
      opts: { method: "POST", body: JSON.stringify({ destFolderId: INBOX }) }
    },
    {
      desc: "POST folders/{trash}/messages/{id}/move {destFolderId}",
      path: `/accounts/${ACCOUNT}/folders/${TRASH}/messages/${first.messageId}/move`,
      opts: { method: "POST", body: JSON.stringify({ destFolderId: INBOX }) }
    },
    {
      desc: "POST messages/undelete {messageIds}",
      path: `/accounts/${ACCOUNT}/messages/undelete`,
      opts: { method: "POST", body: JSON.stringify({ messageIds: [first.messageId] }) }
    },
  ];
  
  for (const t of tests) {
    const resp = await api(t.path, t.opts);
    console.log(`  ${t.desc} -> ${JSON.stringify(resp).substring(0, 300)}`);
  }
}

main().catch(console.error);
