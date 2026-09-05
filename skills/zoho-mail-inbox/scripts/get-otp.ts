// Get the OTP from the inbox
const BASE = "https://mail.zoho.com";
const ACCOUNT = "3117999000000008002";
const INBOX = "3117999000000008014";

const r = await fetch("https://accounts.zoho.com/oauth/v2/token", {
  method: "POST",
  headers: { "Content-Type": "application/x-www-form-urlencoded" },
  body: new URLSearchParams({ grant_type: "refresh_token", client_id: "1000.O7DJKTXGWR6BZK1OTXG3VB777TTUVX", client_secret: "e04387b26c5e39e879297d414c141a7f0c6ed10332", refresh_token: "1000.981eab1d3e0cf080c9b9ef4372eec0d8.dc6f8cd4e19f37a6d8f1a6d197019df7" }),
});
const d = await r.json();
const h = { Authorization: `Bearer ${d.access_token}` };

// Get recent inbox messages
const resp = await fetch(`${BASE}/api/accounts/${ACCOUNT}/messages/view?folderId=${INBOX}&limit=5&includeto=false`, { headers: h });
const data = await resp.json();
console.log("Found", data.data?.length || 0, "messages");

for (const m of data.data || []) {
  console.log(`\n--- ${m.subject} ---`);
  console.log(`From: ${m.fromAddress}`);
  console.log(`Date: ${new Date(parseInt(m.receivedTime)).toLocaleString()}`);
  // Get message content
  const msgResp = await fetch(`${BASE}/api/accounts/${ACCOUNT}/messages/view/${INBOX}/${m.messageId}?includeto=false`, { headers: h });
  const msgData = await msgResp.json();
  if (msgData.data?.content) {
    // Extract OTP from content
    const otpMatch = msgData.data.content.match(/(\d{6})/);
    if (otpMatch) {
      console.log(`OTP found: ${otpMatch[1]}`);
      console.log(otpMatch[1]);
      process.exit(0);
    }
    // Also check text version
    if (msgData.data.textContent) {
      const otpMatch2 = msgData.data.textContent.match(/(\d{6})/);
      if (otpMatch2) {
        console.log(`OTP found in text: ${otpMatch2[1]}`);
        console.log(otpMatch2[1]);
        process.exit(0);
      }
    }
  }
}
console.log("No OTP found");
