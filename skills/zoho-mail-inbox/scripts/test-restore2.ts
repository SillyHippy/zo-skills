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
  const headers = { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };

  // Try different approaches to list trash messages
  const endpoints = [
    `/api/accounts/${ACCOUNT}/messages/search?searchKey=folder:${TRASH}&limit=5&start=0&includeto=false`,
    `/api/accounts/${ACCOUNT}/messages/view?folderId=${TRASH}&limit=5&start=1&includeto=false`,
    `/api/accounts/${ACCOUNT}/messages/search?searchKey=status:trash&limit=5&start=0&includeto=false`,
  ];

  for (const ep of endpoints) {
    console.log(`\nTesting: ${ep}`);
    const resp = await fetch(`${BASE_URL}${ep}`, { headers: { Authorization: `Bearer ${token}` } });
    const text = await resp.text();
    console.log(`Status: ${resp.status}, Body: ${text.substring(0, 500)}`);
  }
}

test().catch(console.error);
