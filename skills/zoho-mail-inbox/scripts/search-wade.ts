const BASE_URL = "https://mail.zoho.com";
const ACCOUNT = "3117999000000008001";
const CLIENT_ID = "1000.O7DJKTXGWR6BZK1OTXG3VB777TTUVX";
const CLIENT_SECRET = "e04387b26c5e39e879297d414c141a7f0c6ed10332";
const REFRESH_TOKEN = "1000.981eab1d3e0cf080c9b9ef4372eec0d8.dc6f8cd4e19f37a6d8f1a6d197019df7";

async function getToken() {
  const r = await fetch("https://accounts.zoho.com/oauth/v2/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      client_id: CLIENT_ID,
      client_secret: CLIENT_SECRET,
      refresh_token: REFRESH_TOKEN,
      grant_type: "refresh_token",
    }),
  });
  const d = await r.json();
  if (!d.access_token) throw new Error(JSON.stringify(d));
  return d.access_token;
}

const FOLDERS = [
  { name: "Inbox", id: "3117999000000008014" },
  { name: "Trash", id: "3117999000000008026" },
  { name: "Spam", id: "3117999000000008024" },
  { name: "Sent", id: "3117999000000008022" },
  { name: "Wade Reeves", id: "3117999000000338018" },
  { name: "Drafts", id: "3117999000000008016" },
];

async function searchFolder(token: string, folderId: string, folderName: string) {
  const url = `${BASE_URL}/api/accounts/${ACCOUNT}/view?folderId=${folderId}&start=0&limit=200`;
  const r = await fetch(url, { headers: { Authorization: `Zoho-oauthtoken ${token}` } });
  const d = await r.json();
  const msgs = d.data?.messages || [];
  const found = msgs.filter((m: any) =>
    (m.subject && m.subject.toLowerCase().includes("wade")) ||
    (m.subject && m.subject.toLowerCase().includes("reeves")) ||
    (m.fromAddress && m.fromAddress.toLowerCase().includes("wade")) ||
    (m.fromAddress && m.fromAddress.toLowerCase().includes("reeves"))
  );
  if (found.length) {
    console.log(`\n=== ${folderName} (${folderId}) ===`);
    found.forEach((m: any) => {
      console.log(`  [${m.folderName || folderName}] ${m.subject || "(no subject)"} | From: ${m.fromAddress} | ID: ${m.messageId}`);
    });
  }
  return found.length;
}

(async () => {
  let token: string;
  for (let i = 0; i < 5; i++) {
    try { token = await getToken(); break; }
    catch (e) { if (i === 4) throw e; await new Promise(r => setTimeout(r, 60000)); }
  }
  let total = 0;
  for (const f of FOLDERS) {
    total += await searchFolder(token, f.id, f.name);
    await new Promise(r => setTimeout(r, 2000));
  }
  console.log(`\nTotal matches: ${total}`);
})();
