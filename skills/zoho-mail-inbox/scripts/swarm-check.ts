const BASE_URL = "https://mail.zoho.com";
const ACCOUNT_ID = "3117999000000008002";
const CLIENT_ID = "1000.O7DJKTXGWR6BZK1OTXG3VB777TTUVX";
const CLIENT_SECRET = "e04387b26c5e39e879297d414c141a7f0c6ed10332";
const REFRESH_TOKEN = "1000.981eab1d3e0cf080c9b9ef4372eec0d8.dc6f8cd4e19f37a6d8f1a6d197019df7";

async function getAccessToken(): Promise<string> {
  for (let attempt = 1; attempt <= 10; attempt++) {
    try {
      const r = await fetch("https://accounts.zoho.com/oauth/v2/token", {
        method: "POST",
        headers: { "content-type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ grant_type: "refresh_token", client_id: CLIENT_ID, client_secret: CLIENT_SECRET, refresh_token: REFRESH_TOKEN }),
      });
      const d = await r.json();
      if (d.access_token) return d.access_token;
      console.log(`Token attempt ${attempt} failed: ${JSON.stringify(d)}`);
    } catch (e: any) {
      console.log(`Token attempt ${attempt} error: ${e.message}`);
    }
    if (attempt < 10) {
      const wait = 60 * 1000;
      console.log(`Waiting ${wait/1000}s before retry...`);
      await new Promise(r => setTimeout(r, wait));
    }
  }
  throw new Error("Could not get token after 10 attempts");
}

async function searchInFolder(token: string, folderId: string, folderName: string, keyword: string) {
  const results: any[] = [];
  let start = 0;
  while (true) {
    const url = `${BASE_URL}/api/accounts/${ACCOUNT_ID}/view?folderId=${folderId}&searchKey=${encodeURIComponent(keyword)}&limit=200&start=${start}&includeto=false`;
    const resp = await fetch(url, { headers: { "Authorization": `Zoho-oauthtoken ${token}` } });
    const data = await resp.json();
    const msgs = data?.data?.messages || [];
    for (const m of msgs) {
      results.push({ folder: folderName, subject: m.subject, from: m.fromAddress, date: m.receivedTime, id: m.messageId });
    }
    if (msgs.length < 200) break;
    start += 200;
    await new Promise(r => setTimeout(r, 12000));
  }
  return results;
}

(async () => {
  console.log("Starting search across all folders for Wade Reeves...");
  const token = await getAccessToken();
  console.log("Got token, searching folders...");
  
  const folders = [
    { id: "3117999000000008014", name: "Inbox" },
    { id: "3117999000000008016", name: "Drafts" },
    { id: "3117999000000008022", name: "Sent" },
    { id: "3117999000000008024", name: "Spam" },
    { id: "3117999000000008026", name: "Trash" },
    { id: "3117999000000008028", name: "Outbox" },
    { id: "3117999000000009001", name: "Notification" },
  ];
  
  const keywords = ["Wade Reeves", "Wade", "Reeves"];
  const allResults: any[] = [];
  
  for (const folder of folders) {
    for (const keyword of keywords) {
      console.log(`Searching ${folder.name} for "${keyword}"...`);
      await new Promise(r => setTimeout(r, 15000));
      const found = await searchInFolder(token, folder.id, folder.name, keyword);
      for (const r of found) {
        allResults.push(r);
      }
    }
  }
  
  // Deduplicate by message ID
  const seen = new Map<string, any>();
  for (const r of allResults) {
    if (!seen.has(r.id)) seen.set(r.id, r);
  }
  const unique = Array.from(seen.values());
  
  console.log(`\n=== Wade Reeves emails found: ${unique.length} ===`);
  for (const r of unique.sort((a,b) => (b.date||"").localeCompare(a.date||""))) {
    console.log(`[${r.folder}] From: ${r.from} | Subject: ${r.subject} | Date: ${r.date}`);
  }
  if (unique.length === 0) {
    console.log("No Wade Reeves emails found in any folder.");
  }
})();
