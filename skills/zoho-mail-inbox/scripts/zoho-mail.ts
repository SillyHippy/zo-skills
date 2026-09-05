const BASE_URL = "https://mail.zoho.com";
const DEFAULT_ACCOUNT_ID = "3117999000000008002";

// OAuth credentials for auto-refresh
const CLIENT_ID = "1000.O7DJKTXGWR6BZK1OTXG3VB777TTUVX";
const CLIENT_SECRET = "e04387b26c5e39e879297d414c141a7f0c6ed10332";
const REFRESH_TOKEN = "1000.981eab1d3e0cf080c9b9ef4372eec0d8.dc6f8cd4e19f37a6d8f1a6d197019df7";

// Cached access token
let accessToken: string | null = null;
let tokenExpiry = 0;

async function getAccessToken(): Promise<string> {
  if (accessToken && Date.now() < tokenExpiry) return accessToken;

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
    console.error(`OAuth error: ${data.error}${data.error_description ? ` — ${data.error_description}` : ""}`);
    process.exit(1);
  }

  accessToken = data.access_token;
  tokenExpiry = Date.now() + (data.expires_in - 60) * 1000;
  return accessToken;
}

async function api(path: string, options: RequestInit = {}): Promise<any> {
  const token = await getAccessToken();
  const url = `${BASE_URL}/api${path}`;
  const resp = await fetch(url, {
    ...options,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  const text = await resp.text();
  let json: any;
  try {
    json = JSON.parse(text);
  } catch {
    console.error(`Failed to parse JSON from ${url}: ${text.substring(0, 200)}`);
    process.exit(1);
  }

  if (!resp.ok || json.status?.code >= 400) {
    console.error(`API error ${resp.status}: ${text.substring(0, 300)}`);
    process.exit(1);
  }
  return json;
}

// Collect ALL messages matching a search query (paginated)
async function collectMessagesAll(searchKey: string): Promise<string[]> {
  const account = DEFAULT_ACCOUNT_ID;
  let allIds: string[] = [];
  let start = 0;

  while (true) {
    const resp = await api(`/accounts/${account}/messages/search?searchKey=${encodeURIComponent(searchKey)}&limit=200&start=${start}&includeto=false`);
    const items = resp.data || [];
    for (const m of items) {
      allIds.push(`${m.folderId}:${m.messageId}`);
    }
    if (items.length < 200) break;
    start += 200;
  }
  return allIds;
}

// Get unread message IDs (using messages/view with status=unread)
async function getUnreadIds(): Promise<string[]> {
  const account = DEFAULT_ACCOUNT_ID;
  let allIds: string[] = [];
  let start = 1;

  while (true) {
    const resp = await api(`/accounts/${account}/messages/view?status=unread&limit=200&start=${start}&includeto=false`);
    const items = resp.data || [];
    for (const m of items) {
      allIds.push(`${m.folderId}:${m.messageId}`);
    }
    if (items.length < 200) break;
    start += 200;
  }
  return allIds;
}

// Delete a single message
async function deleteMessage(id: string): Promise<boolean> {
  const account = DEFAULT_ACCOUNT_ID;
  const [folderId, messageId] = id.split(":");
  const token = await getAccessToken();
  const resp = await fetch(`${BASE_URL}/api/accounts/${account}/folders/${folderId}/messages/${messageId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  return resp.ok;
}

// Batch delete
async function deleteBatch(ids: string[]): Promise<{ deleted: number; failed: number }> {
  let deleted = 0;
  let failed = 0;
  const concurrency = 50;

  for (let i = 0; i < ids.length; i += concurrency) {
    const batch = ids.slice(i, i + concurrency);
    const results = await Promise.all(batch.map((id) => deleteMessage(id)));
    deleted += results.filter(Boolean).length;
    failed += results.filter((r) => !r).length;
    process.stdout.write(`  Progress: ${Math.min(i + concurrency, ids.length)}/${ids.length}\n`);
  }
  return { deleted, failed };
}

// Mark a single message as read
async function markAsRead(id: string): Promise<boolean> {
  const account = DEFAULT_ACCOUNT_ID;
  const [folderId, messageId] = id.split(":");
  const token = await getAccessToken();
  const resp = await fetch(`${BASE_URL}/api/accounts/${account}/messages/${folderId}/${messageId}/read`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });
  return resp.ok;
}

// Batch mark as read
async function markBatchRead(ids: string[]): Promise<{ marked: number; failed: number }> {
  let marked = 0;
  let failed = 0;
  const concurrency = 50;

  for (let i = 0; i < ids.length; i += concurrency) {
    const batch = ids.slice(i, i + concurrency);
    const results = await Promise.all(batch.map((id) => markAsRead(id)));
    marked += results.filter(Boolean).length;
    failed += results.filter((r) => !r).length;
    process.stdout.write(`  Progress: ${Math.min(i + concurrency, ids.length)}/${ids.length}\n`);
  }
  return { marked, failed };
}

// Fetch message details
async function getMessageDetails(folderId: string, messageId: string): Promise<any> {
  const account = DEFAULT_ACCOUNT_ID;
  const resp = await api(`/accounts/${account}/messages/${folderId}/${messageId}`);
  return resp.data;
}

// Send email
async function sendEmail(params: {
  from: string;
  to: string;
  subject: string;
  body: string;
  cc?: string;
  bcc?: string;
}): Promise<boolean> {
  const account = DEFAULT_ACCOUNT_ID;
  const body: any = {
    fromAddress: params.from,
    toAddress: params.to,
    subject: params.subject,
    content: params.body,
    askReceipt: "no",
  };
  if (params.cc) body.ccAddress = params.cc;
  if (params.bcc) body.bccAddress = params.bcc;

  const resp = await api(`/accounts/${account}/messages`, {
    method: "POST",
    body: JSON.stringify(body),
  });
  return resp.status?.code === 200;
}

// Restore all messages from Trash folder
async function restoreTrash(): Promise<{ restored: number; failed: number }> {
  const account = DEFAULT_ACCOUNT_ID;
  const TRASH_FOLDER = "3117999000000008026";
  const ARCHIVE_FOLDER = "3117999000000009021";

  // Get all messages in Trash
  let allTrashIds: string[] = [];
  let start = 1;

  while (true) {
    const resp = await api(`/accounts/${account}/folders/${TRASH_FOLDER}/messages?limit=200&start=${start}`);
    const items = resp.data || [];
    for (const m of items) {
      allTrashIds.push(`${TRASH_FOLDER}:${m.messageId}`);
    }
    if (items.length < 200) break;
    start += 200;
  }

  if (allTrashIds.length === 0) {
    console.log("No emails in Trash to restore.");
    return { restored: 0, failed: 0 };
  }

  console.log(`Found ${allTrashIds.length} emails in Trash. Restoring to Archive...`);

  let restored = 0;
  let failed = 0;
  const concurrency = 50;

  for (let i = 0; i < allTrashIds.length; i += concurrency) {
    const batch = allTrashIds.slice(i, i + concurrency);
    const results = await Promise.all(batch.map(async (id) => {
      const [srcFolderId, messageId] = id.split(":");
      const token = await getAccessToken();
      const resp = await fetch(`${BASE_URL}/api/accounts/${account}/folders/${ARCHIVE_FOLDER}/messages/${messageId}/move`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ sourceFolderId: srcFolderId }),
      });
      return resp.ok;
    }));
    restored += results.filter(Boolean).length;
    failed += results.filter((r) => !r).length;
    process.stdout.write(`  Progress: ${Math.min(i + concurrency, allTrashIds.length)}/${allTrashIds.length}\n`);
  }

  return { restored, failed };
}

const FOLDER_NAMES: Record<string, string> = {
  "3117999000000008014": "Inbox",
  "3117999000000008016": "Drafts",
  "3117999000000008018": "Templates",
  "3117999000000008020": "Snoozed",
  "3117999000000008022": "Sent",
  "3117999000000008024": "Spam",
  "3117999000000008026": "Trash",
  "3117999000000008028": "Outbox",
  "3117999000000009001": "Notification",
  "3117999000000009011": "Newsletter",
  "3117999000000009021": "Archive",
  "3117999000000334001": "Wade Reeves",
  "3117999000000373002": "Spam stuff like Dutch bros",
  "3117999000000374023": "Helcim",
};

const ALIASES = [
  "info@justlegalsolutions.org",
  "joseph@justlegalsolutions.org",
  "11@justlegalsolutions.org",
  "12@justlegalsolutions.org",
  "123@justlegalsolutions.org",
  "1234@justlegalsolutions.org",
  "12345@justlegalsolutions.org",
  "123456@justlegalsolutions.org",
];

const command = process.argv[2];
const args = process.argv.slice(3);

(async () => {
  switch (command) {
    case "unread": {
      const ids = await getUnreadIds();
      if (ids.length === 0) {
        console.log("No unread emails.");
        break;
      }
      console.log(`${ids.length} unread email(s):`);
      for (const id of ids.slice(0, 20)) {
        const [folderId, messageId] = id.split(":");
        const m = await getMessageDetails(folderId, messageId);
        console.log(`  From: ${m.fromAddress} | Subject: ${m.subject.substring(0, 80)}`);
      }
      if (ids.length > 20) console.log(`  ... and ${ids.length - 20} more`);
      break;
    }

    case "markread": {
      const ids = await getUnreadIds();
      if (ids.length === 0) {
        console.log("No unread emails to mark as read.");
        break;
      }
      console.log(`Marking ${ids.length} emails as read...`);
      const result = await markBatchRead(ids);
      console.log(`Done. Marked: ${result.marked}, Failed: ${result.failed}`);
      break;
    }

    case "search": {
      const query = args.join(" ");
      if (!query) {
        console.error("Usage: bun zoho-mail.ts search <query>");
        process.exit(1);
      }
      const ids = await collectMessagesAll(query);
      if (ids.length === 0) {
        console.log(`No emails matching "${query}".`);
        break;
      }
      console.log(`Found ${ids.length} emails matching "${query}":`);
      for (const id of ids.slice(0, 20)) {
        const [folderId, messageId] = id.split(":");
        const m = await getMessageDetails(folderId, messageId);
        console.log(`  From: ${m.fromAddress} | Subject: ${m.subject.substring(0, 80)}`);
      }
      if (ids.length > 20) console.log(`  ... and ${ids.length - 20} more`);
      break;
    }

    case "delete": {
      const query = args.join(" ");
      if (!query) {
        console.error("Usage: bun zoho-mail.ts delete <searchQuery>");
        process.exit(1);
      }
      console.log(`Searching for "${query}"...`);
      const ids = await collectMessagesAll(query);
      if (ids.length === 0) {
        console.log("No emails found to delete.");
        break;
      }
      console.log(`Found ${ids.length}. Deleting...`);
      const result = await deleteBatch(ids);
      console.log(`Done. Deleted: ${result.deleted}, Failed: ${result.failed}`);
      break;
    }

    case "send": {
      if (args.length < 3) {
        console.error("Usage: bun zoho-mail.ts send <from-alias> <to> <subject> [body]");
        console.error(`Available aliases: ${ALIASES.join(", ")}`);
        process.exit(1);
      }
      const from = args[0];
      const to = args[1];
      const subject = args[2];
      const body = args.slice(3).join(" ");
      if (!ALIASES.includes(from)) {
        console.error(`Invalid alias "${from}". Available: ${ALIASES.join(", ")}`);
        process.exit(1);
      }
      console.log(`Sending from ${from} to ${to}...`);
      const ok = await sendEmail({ from, to, subject, body: body || "" });
      console.log(ok ? "Sent successfully." : "Failed to send.");
      break;
    }

    case "folders": {
      const resp = await api(`/accounts/${DEFAULT_ACCOUNT_ID}/folders`);
      console.log("Folders:");
      for (const f of resp.data) {
        const name = FOLDER_NAMES[f.folderId] || "";
        console.log(`  ${name ? name + " " : ""}(ID: ${f.folderId})`);
      }
      break;
    }

    case "aliases": {
      console.log("Available email aliases:");
      for (const a of ALIASES) {
        console.log(`  - ${a}`);
      }
      break;
    }

    case "restore": {
      const result = await restoreTrash();
      console.log(`Done. Restored: ${result.restored}, Failed: ${result.failed}`);
      break;
    }

    case "list": {
      const limit = parseInt(args[0]) || 10;
      const account = DEFAULT_ACCOUNT_ID;
      const resp = await api(`/accounts/${account}/messages/view?limit=${limit}&includeto=false`);
      console.log(`Latest ${limit} messages:`);
      for (const m of resp.data) {
        const folderName = FOLDER_NAMES[m.folderId] || `folder ${m.folderId}`;
        console.log(`  [${folderName}] From: ${m.fromAddress} | Subject: ${m.subject?.substring(0, 80)}`);
      }
      break;
    }

    default:
      console.error(`Unknown command: ${command}`);
      console.error("Commands: list, unread, markread, search, delete, send, folders, aliases");
      process.exit(1);
  }
})();