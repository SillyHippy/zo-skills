const BASE_URL = "https://mail.zoho.com";
const ACCOUNT = "3117999000000008002";
const CLIENT_ID = "1000.O7DJKTXGWR6BZK1OTXG3VB777TTUVX";
const CLIENT_SECRET = "e04387b26c5e39e879297d414c141a7f0c6ed10332";
const REFRESH_TOKEN = "1000.981eab1d3e0cf080c9b9ef4372eec0d8.dc6f8cd4e19f37a6d8f1a6d197019df7";
const TRASH = "3117999000000008026";

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
  
  // Use messages/view to find trash messages - paginate through all
  let trashMessages: Array<{messageId: string, subject: string, fromAddress: string}> = [];
  let vStart = 1;
  
  while (true) {
    const resp = await fetch(`${BASE_URL}/api/accounts/${ACCOUNT}/messages/view?limit=200&start=${vStart}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const text = await resp.text();
    const data = JSON.parse(text);
    
    if (!data.data || data.data.length === 0) break;
    
    for (const m of data.data) {
      if (m.folderId === TRASH) {
        trashMessages.push({
          messageId: m.messageId,
          subject: m.subject || "(no subject)",
          fromAddress: m.fromAddress || "(unknown)",
        });
      }
    }
    
    if (data.data.length < 200) break;
    vStart += 200;
    if (vStart > 5000) {
      console.log("Stopping at 5000 to avoid too many requests");
      break;
    }
  }
  
  console.log(`Found ${trashMessages.length} messages in Trash:`);
  for (const m of trashMessages.slice(0, 20)) {
    console.log(`  ${m.messageId} | From: ${m.fromAddress} | ${m.subject.substring(0, 80)}`);
  }
  if (trashMessages.length > 20) {
    console.log(`  ... and ${trashMessages.length - 20} more`);
  }
}

main().catch(console.error);
