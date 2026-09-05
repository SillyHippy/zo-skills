const BASE_URL = "https://mail.zoho.com";
const CLIENT_ID = "1000.O7DJKTXGWR6BZK1OTXG3VB777TTUVX";
const CLIENT_SECRET = "e04387b26c5e39e879297d414c141a7f0c6ed10332";
const REFRESH_TOKEN = "1000.981eab1d3e0cf080c9b9ef4372eec0d8.dc6f8cd4e19f37a6d8f1a6d197019df7";
const ACCOUNT_ID = "3117999000000008002";

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
  const d = await resp.json();
  if (d.access_token) return d.access_token;
  console.log("Token failed:", JSON.stringify(d));
  process.exit(1);
}

async function checkFolder(folderId: string, name: string) {
  const token = await getToken();
  const resp = await fetch(
    `${BASE_URL}/api/accounts/${ACCOUNT_ID}/view?folderId=${folderId}&limit=200&start=0`,
    { headers: { "Authorization": `Zoho-oauthtoken ${token}` } }
  );
  const d = await resp.json();
  const msgs = d.data?.data || d.data?.list || [];
  console.log(`${name}: ${msgs.length} messages`);
  if (msgs.length > 0) {
    msgs.slice(0, 5).forEach((m: any) => {
      console.log(`  - ${m.subject?.substring(0, 80) || "(no subject)"} (ID: ${m.messageId})`);
    });
  }
}

(async () => {
  await checkFolder("3117999000000334001", "Wade Reeves");
  await checkFolder("3117999000000008014", "Inbox");
  await checkFolder("3117999000000009021", "Archive");
  await checkFolder("3117999000000008026", "Trash");
})();
