// Get the OTP from all folders
const BASE = "https://mail.zoho.com";
const ACCOUNT = "3117999000000008002";

const r = await fetch("https://accounts.zoho.com/oauth/v2/token", {
  method: "POST",
  headers: { "Content-Type": "application/x-www-form-urlencoded" },
  body: new URLSearchParams({ grant_type: "refresh_token", client_id: "1000.O7DJKTXGWR6BZK1OTXG3VB777TTUVX", client_secret: "e04387b26c5e39e879297d414c141a7f0c6ed10332", refresh_token: "1000.981eab1d3e0cf080c9b9ef4372eec0d8.dc6f8cd4e19f37a6d8f1a6d197019df7" }),
});
const d = await r.json();
const h = { Authorization: `Bearer ${d.access_token}` };

// Search for OTP email
const folders = ["3117999000000008014", "3117999000000009001", "3117999000000008026"];
for (const fid of folders) {
  const resp = await fetch(`${BASE}/api/accounts/${ACCOUNT}/messages/search?searchKey=folder:${fid}&limit=5&includeto=false`, { headers: h });
  const data = await resp.json();
  console.log(`Folder ${fid}: ${Array.isArray(data.data) ? data.data.length : 0} messages`);
  if (Array.isArray(data.data)) {
    for (const m of data.data) {
      console.log(`  ${m.subject?.substring(0, 80)} (${m.fromAddress})`);
    }
  }
}

// Also try searching for "OTP" or "Zoho" in subject
const otpSearch = await fetch(`${BASE}/api/accounts/${ACCOUNT}/messages/search?searchKey=subject:OTP&limit=3&includeto=false`, { headers: h });
const otpData = await otpSearch.json();
console.log("\nOTP subject search:", Array.isArray(otpData.data) ? otpData.data.length : 0, "results");

const zohoSearch = await fetch(`${BASE}/api/accounts/${ACCOUNT}/messages/search?searchKey=sender:zoho&limit=3&includeto=false`, { headers: h });
const zohoData = await zohoSearch.json();
console.log("Zoho sender search:", Array.isArray(zohoData.data) ? zohoData.data.length : 0, "results");
