// Use browser cookies to authenticate with Zoho API
import { execSync } from "child_process";

const ACCOUNT = "3117999000000008002";
const INBOX = "3117999000000008014";
const TRASH = "3117999000000008026";
const BASE = "https://mail.zoho.com";

async function main() {
  // First, navigate to Zoho Mail to get cookies
  execSync('agent-browser open "https://mail.zoho.com/zm/"', { stdio: "inherit" });
  
  // Wait for page to load
  await new Promise(r => setTimeout(r, 5000));
  
  // Get cookies
  const cookiesOutput = execSync('agent-browser cookies 2>&1', { encoding: "utf8" });
  console.log("Cookies:", cookiesOutput.substring(0, 500));
}

main().catch(console.error);
