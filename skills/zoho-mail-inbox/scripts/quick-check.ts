const CLIENT_ID = "1000.O7DJKTXGWR6BZK1OTXG3VB777TTUVX";
const CLIENT_SECRET = "e04387b26c5e39e879297d414c141a7f0c6ed10332";
const REFRESH_TOKEN = "1000.981eab1d3e0cf080c9b9ef4372eec0d8.dce955205787673d6086f82036457f48";

const tokenResp = await fetch("https://accounts.zoho.com/oauth/v2/token", {
  method: "POST",
  headers: { "Content-Type": "application/x-www-form-urlencoded" },
  body: `client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}&refresh_token=${REFRESH_TOKEN}&grant_type=refresh_token`
});
const tokenData = await tokenResp.json();
console.log("Token:", tokenData.access_token ? "GOT IT" : "FAILED", tokenData.error_description || "");

if (!tokenData.access_token) {
  console.log("Still rate limited, waiting 5 min...");
  await new Promise(r => setTimeout(r, 300000));
  const tokenResp2 = await fetch("https://accounts.zoho.com/oauth/v2/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: `client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}&refresh_token=${REFRESH_TOKEN}&grant_type=refresh_token`
  });
  const tokenData2 = await tokenResp2.json();
  console.log("Token retry:", tokenData2.access_token ? "GOT IT" : "STILL FAILED");
  if (!tokenData2.access_token) process.exit(1);
  tokenData.access_token = tokenData2.access_token;
}

const token = tokenData.access_token;
const apiDomain = tokenData.api_domain || "https://www.zohoapis.com";
const account = "3117999000000008002";

// Check trash
const trashResp = await fetch(`${apiDomain}/mail/v1/accounts/${account}/messages/view?folderId=3117999000000008026&limit=5&start=0`, {
  headers: { Authorization: `Zoho-oauthtoken ${token}` }
});
const trashData = await trashResp.json();
console.log("Trash messages:", trashData.data?.length || 0);

// Check inbox
const inboxResp = await fetch(`${apiDomain}/mail/v1/accounts/${account}/messages/view?folderId=3117999000000008014&limit=5&start=0`, {
  headers: { Authorization: `Zoho-oauthtoken ${token}` }
});
const inboxData = await inboxResp.json();
console.log("Inbox messages (first page):", inboxData.data?.length || 0);
