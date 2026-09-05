import { Hono } from "hono";
import { cors } from "hono/cors";
import { serve } from "bun";
import { Database } from "bun:sqlite";
import { readFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const DB_PATH = join(__dirname, "..", "assets", "file-share.db");
const BASE_URL = process.env.FILE_SHARE_BASE_URL || "http://localhost:8765";
const PORT = parseInt(process.env.PORT || "8765");

// Initialize database
const db = new Database(DB_PATH);
db.run("PRAGMA journal_mode=WAL");

db.run(`CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE NOT NULL,
  confirmed INTEGER DEFAULT 0,
  confirmation_token TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)`);

db.run(`CREATE TABLE IF NOT EXISTS files (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  path TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)`);

db.run(`CREATE TABLE IF NOT EXISTS user_files (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  file_id INTEGER NOT NULL,
  access_token TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (file_id) REFERENCES files(id),
  UNIQUE(user_id, file_id)
)`);

function randomToken(): string {
  return crypto.randomUUID().replace(/-/g, "");
}

const app = new Hono();
app.use("*", cors());

// Health check
app.get("/health", (c) => c.json({ status: "ok" }));

// List files
app.get("/files", (c) => {
  const files = db.query("SELECT id, name FROM files ORDER BY created_at DESC").all();
  return c.json(files);
});

// Web UI
app.get("/", (c) => {
  const html = readFileSync(join(__dirname, "ui.html"), "utf-8");
  return c.html(html);
});

// Request access
app.post("/request-access", async (c) => {
  const body = await c.req.json();
  const { email, file_id } = body;

  if (!email || !file_id) {
    return c.json({ error: "email and file_id required" }, 400);
  }

  // Check file exists
  const file = db.query("SELECT * FROM files WHERE id = ?").get(file_id) as any;
  if (!file) return c.json({ error: "File not found" }, 404);

  // Upsert user
  let user = db.query("SELECT * FROM users WHERE email = ?").get(email) as any;
  if (!user) {
    const token = randomToken();
    db.run("INSERT INTO users (email, confirmation_token) VALUES (?, ?)", [email, token]);
    user = db.query("SELECT * FROM users WHERE email = ?").get(email) as any;
  }

  if (!user.confirmed) {
    const token = user.confirmation_token || randomToken();
    db.run("UPDATE users SET confirmation_token = ? WHERE id = ?", [token, user.id]);

    const confirmUrl = `${BASE_URL}/confirm/${token}`;
    // Send confirmation email via Zo API
    try {
      const resp = await fetch("https://api.zo.computer/zo/ask", {
        method: "POST",
        headers: {
          "authorization": process.env.ZO_CLIENT_IDENTITY_TOKEN || "",
          "content-type": "application/json",
        },
        body: JSON.stringify({
          input: `Send a file access confirmation email. Use the send_email_to_user tool with subject "Confirm your email for file access" and body:\n\nPlease confirm your email to access "${file.name}".\n\nClick here to confirm: ${confirmUrl}\n\nThis link will expire in 24 hours.`,
        }),
      });
    } catch (e) {
      console.error("Failed to send confirmation email:", e);
    }

    return c.json({ message: "Confirmation email sent. Please check your inbox.", status: "pending_confirmation" });
  }

  // User already confirmed — check or create access
  let access = db.query("SELECT * FROM user_files WHERE user_id = ? AND file_id = ?").get(user.id, file_id) as any;
  if (!access) {
    const accessToken = randomToken();
    db.run("INSERT INTO user_files (user_id, file_id, access_token) VALUES (?, ?, ?)", [user.id, file_id, accessToken]);
    access = db.query("SELECT * FROM user_files WHERE user_id = ? AND file_id = ?").get(user.id, file_id) as any;
  }

  const downloadUrl = `${BASE_URL}/file/${file_id}/${access.access_token}`;

  // Send download link email
  try {
    await fetch("https://api.zo.computer/zo/ask", {
      method: "POST",
      headers: {
        "authorization": process.env.ZO_CLIENT_IDENTITY_TOKEN || "",
        "content-type": "application/json",
      },
      body: JSON.stringify({
        input: `Send a file download email. Use the send_email_to_user tool with subject "Your download link for ${file.name}" and body:\n\nHere is your download link for "${file.name}":\n\n${downloadUrl}\n\nThis link is permanent. Do not share it.`,
      }),
    });
  } catch (e) {
    console.error("Failed to send download email:", e);
  }

  return c.json({ message: "Download link sent to your email.", status: "access_granted" });
});

// Confirm email
app.get("/confirm/:token", (c) => {
  const token = c.req.param("token");
  const user = db.query("SELECT * FROM users WHERE confirmation_token = ?").get(token) as any;
  if (!user) return c.html("<h1>Invalid or expired confirmation link.</h1>", 404);

  db.run("UPDATE users SET confirmed = 1 WHERE id = ?", [user.id]);

  return c.html(`
    <html><body style="font-family:sans-serif;text-align:center;padding:50px">
      <h1>✅ Email Confirmed!</h1>
      <p>You can now access your files. Check your email for download links.</p>
    </body></html>
  `);
});

// Download file
app.get("/file/:file_id/:token", (c) => {
  const fileId = c.req.param("file_id");
  const token = c.req.param("token");

  const access = db.query(
    "SELECT uf.*, f.path, f.name FROM user_files uf JOIN files f ON f.id = uf.file_id WHERE uf.file_id = ? AND uf.access_token = ?"
  ).get(fileId, token) as any;

  if (!access) return c.html("<h1>Access denied or link expired.</h1>", 403);

  if (!existsSync(access.path)) {
    return c.json({ error: "File not found on disk" }, 404);
  }

  const fileBuffer = readFileSync(access.path);
  return new Response(fileBuffer, {
    headers: {
      "Content-Type": "application/octet-stream",
      "Content-Disposition": `attachment; filename="${access.name}"`,
    },
  });
});

// Start server
console.log(`File Share server running on port ${PORT}`);
console.log(`Base URL: ${BASE_URL}`);

serve({
  fetch: app.fetch,
  port: PORT,
});
