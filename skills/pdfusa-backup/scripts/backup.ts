import { Database } from "bun:sqlite";
import { $ } from "bun";

const APP_DIR = "/home/workspace/Projects/PDFUSAEDIT-zo";
const BACKUP_DIR = `${APP_DIR}/backups`;
const DB_PATH = `${APP_DIR}/data/pdfusa.db`;
const UPLOADS_DIR = `${APP_DIR}/data/uploads/serves`;

async function main() {
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
  const zipName = `pdfusa-backup-${timestamp}.zip`;
  const zipPath = `${BACKUP_DIR}/${zipName}`;

  await $`mkdir -p ${BACKUP_DIR}`;

  // Close DB if open (ensure WAL is checkpointed)
  try {
    const db = new Database(DB_PATH);
    db.exec("PRAGMA wal_checkpoint(TRUNCATE)");
    db.close();
  } catch {}

  // Create zip
  console.log(`Creating backup: ${zipName}`);
  await $`cd ${APP_DIR} && zip -r ${zipPath} data/pdfusa.db data/uploads/serves/`;

  const stats = await Bun.file(zipPath).size;
  console.log(`Backup created: ${zipPath} (${(stats / 1024 / 1024).toFixed(1)} MB)`);
  console.log(`ZIP_PATH=${zipPath}`);
  console.log(`ZIP_NAME=${zipName}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
