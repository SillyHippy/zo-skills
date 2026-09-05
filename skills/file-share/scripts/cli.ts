import { Database } from "bun:sqlite";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { existsSync } from "fs";
import { randomUUID } from "crypto";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const DB_PATH = join(__dirname, "..", "assets", "file-share.db");

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

function printTable(rows: any[]) {
  if (rows.length === 0) { console.log("(empty)"); return; }
  console.table(rows);
}

function printHelp() {
  console.log(`
File Share CLI

Commands:
  list-files                    Show all registered files
  list-users                    Show all users and confirmation status
  add-file <path> [name]        Register a file for sharing
  remove-file <file_id>         Remove a file from sharing
  add-user <email> <file_id>    Pre-register a user with file access
  remove-user <user_id>         Remove a user completely
  revoke-access <user_id> <file_id>  Revoke specific file access
  confirm-user <user_id>        Manually confirm a user
  file-users <file_id>          List users with access to a file
`);
}

const args = process.argv.slice(2);
const cmd = args[0];

switch (cmd) {
  case "list-files": {
    const files = db.query("SELECT id, name, path, created_at FROM files ORDER BY created_at DESC").all();
    printTable(files);
    break;
  }

  case "list-users": {
    const users = db.query("SELECT id, email, confirmed, created_at FROM users ORDER BY created_at DESC").all();
    printTable(users);
    break;
  }

  case "add-file": {
    const filePath = args[1];
    const name = args[2] || filePath.split("/").pop() || "unnamed";
    if (!filePath) { console.error("Usage: add-file <path> [name]"); process.exit(1); }
    if (!existsSync(filePath)) { console.error(`File not found: ${filePath}`); process.exit(1); }
    const absPath = filePath.startsWith("/") ? filePath : join(process.cwd(), filePath);
    db.run("INSERT INTO files (name, path) VALUES (?, ?)", [name, absPath]);
    const file = db.query("SELECT * FROM files WHERE path = ?").get(absPath) as any;
    console.log(`Added file "${name}" (id: ${file.id}) from ${absPath}`);
    break;
  }

  case "remove-file": {
    const fileId = parseInt(args[1] || "");
    if (!fileId) { console.error("Usage: remove-file <file_id>"); process.exit(1); }
    db.run("DELETE FROM user_files WHERE file_id = ?", [fileId]);
    db.run("DELETE FROM files WHERE id = ?", [fileId]);
    console.log(`Removed file ${fileId}`);
    break;
  }

  case "add-user": {
    const email = args[1];
    const fileId = parseInt(args[2] || "");
    if (!email || !fileId) { console.error("Usage: add-user <email> <file_id>"); process.exit(1); }
    const accessToken = randomUUID().replace(/-/g, "");
    // Upsert user
    let user = db.query("SELECT * FROM users WHERE email = ?").get(email) as any;
    if (!user) {
      db.run("INSERT INTO users (email, confirmed) VALUES (?, 1)", [email]);
      user = db.query("SELECT * FROM users WHERE email = ?").get(email) as any;
    } else if (!user.confirmed) {
      db.run("UPDATE users SET confirmed = 1 WHERE id = ?", [user.id]);
    }
    db.run("INSERT OR IGNORE INTO user_files (user_id, file_id, access_token) VALUES (?, ?, ?)", [user.id, fileId, accessToken]);
    console.log(`User ${email} pre-registered for file ${fileId} (confirmed, token: ${accessToken})`);
    break;
  }

  case "remove-user": {
    const userId = parseInt(args[1] || "");
    if (!userId) { console.error("Usage: remove-user <user_id>"); process.exit(1); }
    db.run("DELETE FROM user_files WHERE user_id = ?", [userId]);
    db.run("DELETE FROM users WHERE id = ?", [userId]);
    console.log(`Removed user ${userId}`);
    break;
  }

  case "revoke-access": {
    const userId = parseInt(args[1] || "");
    const fileId = parseInt(args[2] || "");
    if (!userId || !fileId) { console.error("Usage: revoke-access <user_id> <file_id>"); process.exit(1); }
    db.run("DELETE FROM user_files WHERE user_id = ? AND file_id = ?", [userId, fileId]);
    console.log(`Revoked access for user ${userId} to file ${fileId}`);
    break;
  }

  case "confirm-user": {
    const userId = parseInt(args[1] || "");
    if (!userId) { console.error("Usage: confirm-user <user_id>"); process.exit(1); }
    db.run("UPDATE users SET confirmed = 1 WHERE id = ?", [userId]);
    console.log(`Confirmed user ${userId}`);
    break;
  }

  case "file-users": {
    const fileId = parseInt(args[1] || "");
    if (!fileId) { console.error("Usage: file-users <file_id>"); process.exit(1); }
    const users = db.query(`
      SELECT u.id, u.email, u.confirmed, uf.access_token
      FROM users u JOIN user_files uf ON u.id = uf.user_id
      WHERE uf.file_id = ?
    `).all(fileId);
    printTable(users);
    break;
  }

  default:
    printHelp();
}
