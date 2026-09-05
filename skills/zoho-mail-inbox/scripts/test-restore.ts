const BASE_URL = "https://mail.zoho.com";
const ACCOUNT = "3117999000000008002";
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
  const TRASH = "3117999000000008026";
  
  // List messages in Trash
  const resp = await fetch(`${BASE_URL}/api/accounts/${ACCOUNT}/folders/${TRASH}/messages?limit=10&start=1`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const text = await resp.text();
  console.log("Trash list response:", text.substring(0, 2000));
}

main().catch(console.error);
