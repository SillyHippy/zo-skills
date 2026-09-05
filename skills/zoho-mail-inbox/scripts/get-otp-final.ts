const BASE = "https://mail.zoho.com";
const ACCOUNT = "3117999000000008002";

const r = await fetch("https://accounts.zoho.com/oauth/v2/token", {
  method: "POST",
  headers: { "Content-Type": "application/x-www-form-urlencoded" },
  body: new URLSearchParams({ grant_type: "refresh_token", client_id: "1000.O7DJKTXGWR6BZK1OTXG3VB777TTUVX", client_secret: "e04387b26c5e39e879297d414c141a7f0c6ed10332", refresh_token: "1000.981eab1d3e0cf080c9b9ef4372eec0d8.dc6f8cd4e19f37a6d8f1a6d197019df7" }),
});
const d = await r.json();
if (!d.access_token) { console.error("Token failed"); process.exit(1); }
const h = { Authorization: `Bearer ${d.access_token}` };

// Search all folders for recent Zoho OTP emails
const resp = await fetch(`${BASE}/api/accounts/${ACCOUNT}/messages/view?limit=10&includeto=false`, { headers: h });
const data = await resp.json();
console.log("Latest messages:", data.data?.length || 0);

for (const m of (data.data || []).slice(0, 10)) {
  console.log(`[${m.folderId}] ${m.subject?.substring(0, 60)} from ${m.fromAddress}`);
  // Get content
  try {
    const msgResp = await fetch(`${BASE}/api/accounts/${ACCOUNT}/messages/view/${m.folderId}/${m.messageId}?includeto=false`, { headers: h });
    const msgData = await msgResp.json();
    const content = msgData.data?.content || msgData.data?.textContent || "";
    const otpMatch = content.match(/(\d{6})/);
    if (otpMatch) {
      console.log(`*** OTP: ${otpMatch[1]} ***`);
      console.log(otpMatch[1]);
      process.exit(0);
    }
  } catch(e) {}
}
console.log("No OTP found");
