const BASE = "https://mail.zoho.com";
const ACCOUNT = "3117999000000008002";
const CLIENT_ID = "1000.O7DJKTXGWR6BZK1OTXG3VB777TTUVX";
const CLIENT_SECRET = "e04387b26c5e39e879297d414c141a7f0c6ed10332";
const REFRESH_TOKEN = "1000.981eab1d3e0cf080c9b9ef4372eec0d8.dc6f8cd4e19f37a6d8f1a6d197019df7";

let cachedToken: string | null = null;

async function getToken(): Promise<string> {
  if (cachedToken) return cachedToken;
  for (let attempt = 1; attempt <= 3; attempt++) {
    const r = await fetch("https://accounts.zoho.com/oauth/v2/token", {
      method: "POST",
      headers: { "content-type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        grant_type: "refresh_token",
        client_id: CLIENT_ID,
        client_secret: CLIENT_SECRET,
        refresh_token: REFRESH_TOKEN,
      }),
    });
    const d = await r.json();
    if (d.access_token) {
      cachedToken = d.access_token;
      return d.access_token;
    }
    console.log(`Token attempt ${attempt}: ${JSON.stringify(d)}`);
    await new Promise(r => setTimeout(r, attempt * 30000));
  }
  throw new Error("Failed to get token");
}

async function checkFolder(folderId: string, folderName: string, token: string) {
  const r = await fetch(`${BASE}/api/accounts/${ACCOUNT}/messages/view?folderId=${folderId}&limit=200`, {
    headers: { Authorization: `Zoho-oauthtoken ${token}` },
  });
  const d = await r.json();
  const msgs = d.data?.messages || [];
  console.log(`${folderName}: ${msgs.length} messages`);
  
  const wadeMsgs = msgs.filter((m: any) => {
    const from = (m.fromAddress || m.from || "").toLowerCase();
    const subj = (m.subject || "").toLowerCase();
    return from.includes("wade") || from.includes("reeves") || subj.includes("wade") || subj.includes("reeves");
  });
  
  if (wadeMsgs.length > 0) {
    console.log(`  *** WADE REEVES FOUND: ${wadeMsgs.length} messages ***`);
    wadeMsgs.forEach((m: any) => {
      console.log(`    From: ${m.fromAddress || m.from}, Subject: ${m.subject}`);
    });
  }
  return wadeMsgs.length;
}

(async () => {
  try {
    const token = await getToken();
    console.log("Searching all folders for Wade Reeves...\n");
    
    const folders = [
      { id: "3117999000000008014", name: "Inbox" },
      { id: "3117999000000008016", name: "Drafts" },
      { id: "3117999000000008020", name: "Snoozed" },
      { id: "3117999000000008022", name: "Sent" },
      { id: "3117999000000008024", name: "Spam" },
      { id: "3117999000000008026", name: "Trash" },
      { id: "3117999000000009001", name: "Notification" },
    ];
    
    let total = 0;
    for (const f of folders) {
      total += await checkFolder(f.id, f.name, token);
      await new Promise(r => setTimeout(r, 2000));
    }
    console.log(`\nTotal Wade Reeves emails found: ${total}`);
  } catch (e: any) {
    console.error("Error:", e.message);
  }
})();
