import { Hono } from "hono";
import { serve } from "bun";
import { exec } from "child_process";

const app = new Hono();
const ZO_API_KEY = process.env.ZO_API_KEY;

// Keep track of processed IDs to prevent duplicates
const processedEvents = new Set<string>();

const getZoApiKey = () => {
    // Try the direct env var first
    if (process.env.ZO_API_KEY && process.env.ZO_API_KEY !== "$ZO_ACCESS_TOKEN") {
        return process.env.ZO_API_KEY;
    }
    
    // Fall back to reading from .zo_secrets or master-credentials if needed,
    try {
        const secrets = require('fs').readFileSync('/root/.zo_secrets', 'utf8');
        const match = secrets.match(/export ZO_CLIENT_IDENTITY_TOKEN="([^"]+)"/);
        if (match) return match[1];
    } catch(e) {}
    
    try {
        const credentials = require('fs').readFileSync('/home/workspace/credentials/master-credentials.json', 'utf8');
        const creds = JSON.parse(credentials);
        if (creds.zo_api_key) return creds.zo_api_key;
        if (creds.ZO_API_KEY) return creds.ZO_API_KEY;
    } catch(e) {}
    
    // Use the ambient token that Zo injects for internal calls
    if (process.env.ZO_CLIENT_IDENTITY_TOKEN) {
       return process.env.ZO_CLIENT_IDENTITY_TOKEN;
    }

    return null;
};

async function sendSmsNotification(message: string) {
  const apiKey = getZoApiKey();
  if (!apiKey) {
      console.error("ZO_API_KEY environment variable is not set. Cannot send SMS.");
      return false;
  }
  try {
    const res = await fetch("https://api.zo.computer/tools/sms/send", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        message: message
      })
    });
    if (!res.ok) {
      console.error("Zo API returned error:", await res.text());
      return false;
    }
    return true;
  } catch (err: any) {
    console.error("Fetch error in sendSmsNotification:", err.message);
    return false;
  }
}

app.post("/", async (c) => {
  try {
    const body = await c.req.json();
    
    // Quick acknowledge to Helcim
    console.log("Received Helcim webhook:", JSON.stringify(body, null, 2));

    const invoiceId = body?.invoiceId || body?.id;
    if (invoiceId) {
       if (processedEvents.has(invoiceId)) {
          console.log(`Skipping already processed invoice: ${invoiceId}`);
          return c.json({ status: "skipped" });
       }
       processedEvents.add(invoiceId);
    }
    
    // Only proceed if it looks like an invoice was paid
    const status = body?.status || body?.invoiceStatus;
    if (status === "PAID") {
       // Format a nice message
       const amount = body.amountPaid || body.amount || "?";
       const invoiceNum = body.invoiceNumber || "?";
       let client = body.billingAddress?.name || body.customerName || "a client";
       
       const message = `💰 Helcim payment received: $${amount} for Invoice #${invoiceNum} from ${client}.`;
       
       console.log("Triggering Zo SMS notification...");
       
       const apiKey = getZoApiKey();
       if (apiKey) {
           const prompt = `The user's Helcim invoice #${invoiceNum} just got paid for $${amount} by ${client}. 
Please use your send_telegram_message tool to message the user (Joe) on Telegram and let them know. 
Format the message something like: "💰 Helcim payment received: $${amount} for Invoice #${invoiceNum} from ${client}."
Send the message immediately and then finish your turn.`;

           const resp = await fetch("https://api.zo.computer/zo/ask", {
              method: "POST",
              headers: {
                 "Authorization": apiKey,
                 "Content-Type": "application/json"
              },
              body: JSON.stringify({
                 input: prompt,
                 model_name: "byok:9261050d-bb46-4bb8-9f38-92e63324327e"
              })
           });
           
           if (!resp.ok) {
              console.error("Zo API returned error:", await resp.text());
           } else {
              console.log("Zo API notified successfully.");
           }
       } else {
           console.log("ZO_API_KEY missing - cannot send SMS.");
       }
    }

    return c.json({ status: "success" });
  } catch (err: any) {
    console.error("Webhook error:", err.message);
    return c.json({ error: err.message }, 500);
  }
});

serve({
  fetch: app.fetch,
  port: 4242
});

console.log("Helcim webhook listener running on port 4242...");