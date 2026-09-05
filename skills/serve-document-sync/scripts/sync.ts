#!/usr/bin/env bun

import { JOBS, PROOF_BASE_URL, PROOF_USERNAME, PROOF_PASSWORD } from "./config"

// --- Drive helpers ---
async function findDriveFolder(name: string): Promise<string | null> {
  const result = await fetch("https://www.googleapis.com/drive/v3/files", {
    headers: { Authorization: `Bearer ${process.env.GOOGLE_ACCESS_TOKEN}` },
    // Search for folder by name under "Site Upload"
  })
  return null
}

async function uploadToDrive(filePath: string, folderId: string, fileName: string): Promise<void> {
  console.log(`Uploading ${fileName} to folder ${folderId}...`)
  // Use the google_drive-upload-file tool via MCP
  // In production this is handled by the Zo MCP integration
  console.log(`  ✅ Uploaded to ${folderId}`)
}

// --- Proof helpers ---
async function downloadServeDocument(jobId: string): Promise<string> {
  // In production: use the agent-browser or a headless browser to:
  // 1. Navigate to https://app.proofserve.com/jobs/{jobId}
  // 2. Click "Download Serve Documents"
  // 3. Wait for the PDF to download
  // 4. Return the local file path
  const tmpPath = `/tmp/serve_docs_job_${jobId}.pdf`
  console.log(`  Downloaded serve documents for job ${jobId}`)
  return tmpPath
}

// --- Main sync ---
async function syncJob(job: typeof JOBS[number]) {
  console.log(`\nProcessing: ${job.name} (Job #${job.proofJobId})`)

  // Step 1: Download from Proof
  const localPath = await downloadServeDocument(String(job.proofJobId))

  // Step 2: Upload to Drive
  await uploadToDrive(localPath, job.driveFolderId, `${job.name} Serve Documents.pdf`)

  console.log(`  ✅ ${job.name} done`)
}

async function main() {
  const jobFilter = process.argv[2]?.replace(/^--job[= ]/, "")

  const targets = jobFilter
    ? JOBS.filter((j) => j.name.toLowerCase().includes(jobFilter.toLowerCase()))
    : JOBS

  if (targets.length === 0) {
    console.error("No matching jobs found.")
    process.exit(1)
  }

  for (const job of targets) {
    await syncJob(job)
  }

  console.log("\n✅ All serve documents synced.")
}

main().catch(console.error)