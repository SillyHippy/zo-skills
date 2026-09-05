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
  if (data.error) {
    console.error("OAuth error:", data.error, data.error_description);
    process.exit(1);
  }
  return data.access_token;
}

async function api(path: string, opts: RequestInit = {}): Promise<any> {
  const token = await getToken();
  const resp = await fetch(`${BASE_URL}/api${path}`, {
    ...opts,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      ...opts.headers,
    },
  });
  const text = await resp.text();
  try { return JSON.parse(text); } catch { return { raw: text.substring(0, 500) }; }
}

async function countMessages(folderId: string): Promise<number> {
  let count = 0;
  let start = 1;
  while (true) {
    const resp = await api(`/accounts/${ACCOUNT}/messages/view?folderId=${folderId}&limit=200&start=${start}`);
    const items = resp.data;
    if (!items || !Array.isArray(items) || items.length === 0) break;
    count += items.length;
    if (items.length < 200) break;
    start += 200;
  }
  return count;
}

async function main() {
  const folders = [
    { id: "3117999000000008014", name: "Inbox" },
    { id: "3117999000000008016", name: "Drafts" },
    { id: "3117999000000008018", name: "Templates" },
    { id: "3117999000000008020", name: "Snoozed" },
    { id: "3117999000000008022", name: "Sent" },
    { id: "3117999000000008024", name: "Spam" },
    { id: "3117999000000008026", name: "Trash" },
    { id: "3117999000000008028", name: "Outbox" },
    { id: "3117999000000009001", name: "Notification" },
    { id: "3117999000000009011", name: "Newsletter" },
    { id: "3117999000000009021", name: "Archive" },
    { id: "3117999000000334001", name: "Wade Reeves" },
    { id: "3117999000000373002", name: "Spam stuff like Dutch bros" },
    { id: "3117999000000374023", name: "Helcim" },
  ];
  
  for (const f of folders) {
    const count = await countMessages(f.id);
    console.log(`${f.name} (${f.id}): ${count} messages`);
  }
}

main().catch(console.error);
