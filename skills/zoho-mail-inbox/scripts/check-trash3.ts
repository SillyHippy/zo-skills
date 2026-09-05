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
  return data.access_token;
}

async function main() {
  const token = await getToken();
  
  // Get first page of trash messages
  const resp = await fetch(`${BASE_URL}/api/accounts/${ACCOUNT}/messages/view?folderId=${TRASH}&limit=200&start=1`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await resp.json();
  
  console.log("Response keys:", Object.keys(data));
  console.log("Status:", JSON.stringify(data.status));
  console.log("Is data array:", Array.isArray(data.data));
  
  if (Array.isArray(data.data)) {
    console.log("Trash messages count:", data.data.length);
    
    // Show first few
    for (const m of data.data.slice(0, 10)) {
      console.log(`  ${m.messageId} | From: ${m.fromAddress} | Subject: ${(m.subject || "").substring(0, 60)}`);
    }
    
    // Try move/undelete on first message - test different approaches
    if (data.data.length > 0) {
      const msg = data.data[0];
      console.log(`\nTesting restore approaches on message ${msg.messageId}...`);
      
      // Try POST to messages/{messageId}/move with destination folder in body
      const tests = [
        {
          desc: "POST messages/{id}/move {destFolderId}",
          url: `${BASE_URL}/api/accounts/${ACCOUNT}/messages/${msg.messageId}/move`,
          opts: { method: "POST", body: JSON.stringify({ destFolderId: INBOX }) }
        },
        {
          desc: "POST messages/{folderId}/{id}/move {destFolderId}",
          url: `${BASE_URL}/api/accounts/${ACCOUNT}/messages/${TRASH}/${msg.messageId}/move`,
          opts: { method: "POST", body: JSON.stringify({ destFolderId: INBOX }) }
        },
        {
          desc: "POST folders/{trash}/messages/{id}/move {destFolderId}",
          url: `${BASE_URL}/api/accounts/${ACCOUNT}/folders/${TRASH}/messages/${msg.messageId}/move`,
          opts: { method: "POST", body: JSON.stringify({ destFolderId: INBOX }) }
        },
        {
          desc: "PUT messages/{id}/move {destFolderId}",
          url: `${BASE_URL}/api/accounts/${ACCOUNT}/messages/${msg.messageId}/move`,
          opts: { method: "PUT", body: JSON.stringify({ destFolderId: INBOX }) }
        },
        {
          desc: "POST messages/undelete {messageIds}",
          url: `${BASE_URL}/api/accounts/${ACCOUNT}/messages/undelete`,
          opts: { method: "POST", body: JSON.stringify({ messageIds: [msg.messageId] }) }
        },
      ];
      
      for (const t of tests) {
        const resp2 = await fetch(t.url, {
          ...t.opts,
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        });
        const text = await resp2.text();
        console.log(`  ${t.desc} -> ${resp2.status}: ${text.substring(0, 300)}`);
      }
    }
  } else {
    console.log("Data:", JSON.stringify(data.data).substring(0, 500));
  }
}

main().catch(console.error);
