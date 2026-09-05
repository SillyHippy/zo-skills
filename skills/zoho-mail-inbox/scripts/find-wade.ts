const ACCOUNT = "3117999000000008002";
const CLIENT_ID = "1000.O7DJKTXGWR6BZK1OTXG3VB777TTUVX";
const CLIENT_SECRET = "e04387b26c5e39e879297d414c141a7f0c6ed10332";
const REFRESH_TOKEN = process.env.ZOHO_MAIL_REFRESH_TOKEN || "";

async function getToken(): Promise<string> {
  const r = await fetch("https://accounts.zoho.com/oauth/v2/token", {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "refresh_token",
      client_id: CLIENT_ID,
      client_secret: CLIENT_SECRET,
      refresh_token: REFRESH_TOKEN,
    }),
  });
  const d = await r.json();
  if (!d.access_token) throw new Error(JSON.stringify(d));
  return d.access_token;
}

async function searchFolder(folderId: string, folderName: string, token: string) {
  const r = await fetch(`https://mail.zoho.com/api/accounts/${ACCOUNT}/messages/view?folderId=${folderId}&search=Reeves&limit=200`, {
    headers: { "Authorization": `Zoho-oauthtoken ${token}` },
  });
  const d = await r.json();
  const msgs = d.data?.messages || [];
  if (msgs.length > 0) {
    console.log(`${folderName}: ${msgs.length} messages found`);
    msgs.forEach((m: any) => {
      console.log(`  From: ${m.fromAddress || m.from}, Subject: ${m.subject || "(none)"}`);
    });
  }
}

(async () => {
  try {
    const token = await getToken();
    console.log("Searching all folders for Wade Reeves...\n");
    
    const folders = [
      { id: "3117999000000008014", name: "Inbox" },
      { id: "3117999000000008016", name: "Drafts" },
      { id: "3117999000000008018", name: "Templates" },
      { id: "3117999000000008020", name: "Snoozed" },
      { id: "3117999000000008022", name: "Sent" },
      { id: "3117999000000008024", name: "Spam" },
      { id: "3117999000000008026", name: "Trash" },
      { id: "3117999000000009001", name: "Notification" },
    ];
    
    for (const f of folders) {
      await searchFolder(f.id, f.name, token);
      await new Promise(r => setTimeout(r, 1000));
    }
    console.log("\nSearch complete.");
  } catch (e: any) {
    console.error("Error:", e.message);
  }
})();
