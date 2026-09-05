// Try to get a web session cookie from the OAuth token
const BASE = "https://mail.zoho.com";
const ACCOUNT = "3117999000000008002";

const r = await fetch("https://accounts.zoho.com/oauth/v2/token", {
  method: "POST",
  headers: { "Content-Type": "application/x-www-form-urlencoded" },
  body: new URLSearchParams({ grant_type: "refresh_token", client_id: "1000.O7DJKTXGWR6BZK1OTXG3VB777TTUVX", client_secret: "e04387b26c5e39e879297d414c141a7f0c6ed10332", refresh_token: "1000.981eab1d3e0cf080c9b9ef4372eec0d8.dc6f8cd4e19f37a6d8f1a6d197019df7" }),
});
const d = await r.json();
const token = d.access_token;

// Try to use the token to access the web UI
// Method 1: Set Authorization header on web request
const resp = await fetch(`${BASE}/zm/`, {
  headers: { Authorization: `Bearer ${token}`, "X-ZOHO-API-KEY": token },
  redirect: "manual",
});
console.log("Web UI access:", resp.status, resp.headers.get("location") || resp.headers.get("set-cookie") || "no redirect/cookie");

// Method 2: Try to exchange token for cookie
const resp2 = await fetch("https://accounts.zoho.com/oauth/token/exchange", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ token, service: "VirtualOffice" }),
  redirect: "manual",
});
console.log("Token exchange:", resp2.status, resp2.headers.get("set-cookie") || "no cookie");

// Method 3: Try mail API with web-style auth
const resp3 = await fetch(`${BASE}/api/accounts/${ACCOUNT}/messages/search?searchKey=folder:3117999000000008026&limit=5`, {
  headers: { Authorization: `Zoho-oauthtoken ${token}` },
});
const d3 = await resp3.json();
console.log("Zoho-oauthtoken auth:", d3.status?.code, "count:", d3.data?.length || 0);
