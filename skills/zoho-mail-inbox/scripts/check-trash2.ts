const ACCOUNT = "3117999000000008002";
const TRASH = "3117999000000008026";

async function getToken() {
  const CLIENT_ID = "1000.O7DJKTXGWR6BZK1OTXG3VB777TTUVX";
  const CLIENT_SECRET = "e04387b26c5e39e879297d414c141a7f0c6ed10332";
  const REFRESH_TOKEN = "1000.981eab1d3e0cf080c9b9ef4372eec0d8.dc6f8cd4e19f37a6d8f1a6d197019df7";
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
  return { token: data.access_token, apiDomain: data.api_domain || "https://www.zohoapis.com" };
}

async function main() {
  const { token, apiDomain } = await getToken();
  
  // Try with the correct API domain
  // Try listing trash messages
  const endpoints = [
    `https://mail.zoho.com/api/accounts/${ACCOUNT}/folders/${TRASH}/messages?limit=50&start=1`,
    `https://www.zohoapis.com/api/accounts/${ACCOUNT}/folders/${TRASH}/messages?limit=50&start=1`,
    `https://mail.zoho.com/api/accounts/${ACCOUNT}/messages?folderId=${TRASH}&limit=50&start=1`,
    `https://www.zohoapis.com/api/accounts/${ACCOUNT}/messages?folderId=${TRASH}&limit=50&start=1`,
    `https://mail.zoho.com/api/accounts/${ACCOUNT}/messages/view?folderId=${TRASH}&limit=50&start=1`,
  ];
  
  for (const url of endpoints) {
    const resp = await fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const text = await resp.text();
    console.log(`URL: ${url}`);
    console.log(`Status: ${resp.status}`);
    console.log(`Response: ${text.substring(0, 500)}`);
    console.log("---");
  }
}

main().catch(console.error);
