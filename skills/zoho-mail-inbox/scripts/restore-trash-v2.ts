const BASE = "https://mail.zoho.com";
const ACCT = "3117999000000008002";
const CID = "1000.O7DJKTXGWR6BZK1OTXG3VB777TTUVX";
const CSEC = "e04387b26c5e39e879297d414c141a7f0c6ed10332";
const RT = "1000.981eab1d3e0cf080c9b9ef4372eec0d8.dc6f8cd4e19f37a6d8f1a6d197019df7";

async function tok() {
  const r = await fetch("https://accounts.zoho.com/oauth/v2/token",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:new URLSearchParams({grant_type:"refresh_token",client_id:CID,client_secret:CSEC,refresh_token:RT})});
  return (await r.json()).access_token;
}

async function main(){
  const t = await tok();
  const h = {Authorization:`Bearer ${t}`};

  // Try messages/view - get all recent and look for trash
  const r = await fetch(`${BASE}/api/accounts/${ACCT}/messages/view?limit=500&includeto=false`,{headers:h});
  const d:any = await r.json();
  const msgs = Array.isArray(d.data)?d.data:[];
  console.log(`Got ${msgs.length} messages from view`);
  for(const m of msgs.slice(0,20)){
    console.log(`  msgId:${m.messageId} folder:${m.folderId} subj:${(m.subject||"").substring(0,60)}`);
  }
}
main().catch(e=>console.error(e));
