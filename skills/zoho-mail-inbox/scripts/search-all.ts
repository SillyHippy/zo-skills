const BASE = "https://mail.zoho.com";
const ACCT = "3117999000000008001";
const CID = "1000.O7DJKTXGWR6BZK1OTXG3VB777TTUVX";
const CSEC = "e04387b26c5e39e879297d414c141a7f0c6ed10332";
const RT = "1000.981eab1d3e0cf080c9b9ef4372eec0d8.dc6f8cd4e19f37a6d8f1a6d197019df7";

async function getToken() {
  const r = await fetch("https://accounts.zoho.com/oauth/v2/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ client_id: CID, client_secret: CSEC, refresh_token: RT, grant_type: "refresh_token" }),
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
];

(async () => {
  let token: string;
  for (let i = 0; i < 5; i++) {
    try { token = await getToken(); break; }
    catch (e) { if (i === 4) throw e; await new Promise(r => setTimeout(r, 120000)); }
  }

  for (const f of FOLDERS) {
    console.log(`\n=== ${f.name} (folderId=${f.id}) ===`);
    const url = `${BASE}/api/accounts/${ACCT}/view?folderId=${f.id}&start=0&limit=50`;
    const r = await fetch(url, { headers: { Authorization: `Zoho-oauthtoken ${token}` } });
    const d = await r.json();
    const msgs = d.data?.messages || d.data?.result?.messages || [];
    console.log(`  Found ${msgs.length} messages`);
    msgs.slice(0, 20).forEach((m: any, i: number) => {
      console.log(`  ${i+1}. ${m.subject || "(no subject)"} | From: ${m.fromAddress}`);
    });
    await new Promise(r => setTimeout(r, 3000));
  }
})();
