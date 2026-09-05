const BASE = "https://mail.zoho.com";
const ACCT = "3117999000000008002";
const CID = "1000.O7DJKTXGWR6BZK1OTXG3VB777TTUVX";
const CSEC = "e04387b26c5e39e879297d414c141a7f0c6ed10332";
const RT = "1000.981eab1d3e0cf080c9b9ef4372eec0d8.dc6f8cd4e19f37a6d8f1a6d197019df7";

const FOLDERS: Record<string,string> = {
  "3117999000000008014":"Inbox","3117999000000008022":"Sent","3117999000000009001":"Notification",
  "3117999000000009011":"Newsletter","3117999000000009021":"Archive",
  "3117999000000334001":"Wade Reeves","3117999000000373002":"Spam stuff like Dutch bros",
  "3117999000000374023":"Helcim"
};

async function tok() {
  const r = await fetch("https://accounts.zoho.com/oauth/v2/token",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:new URLSearchParams({grant_type:"refresh_token",client_id:CID,client_secret:CSEC,refresh_token:RT})});
  return (await r.json()).access_token;
}

async function main(){
  const t = await tok();
  const h = {Authorization:`Bearer ${t}`};
  const TRASH = "3117999000000008026";

  // Get trash messages with original folder info
  let msgs:any[]=[]; let start=0;
  while(true){
    const r = await fetch(`${BASE}/api/accounts/${ACCT}/messages/search?searchKey=folder:${TRASH}&limit=200&start=${start}&includeto=false`,{headers:h});
    const d:any = await r.json();
    const arr = Array.isArray(d.data)?d.data:[];
    msgs.push(...arr);
    if(arr.length<200)break;
    start+=200;
    await new Promise(s=>setTimeout(s,200));
  }
  console.log(`Found ${msgs.length} trash messages`);
  if(msgs.length===0){process.exit(0);}

  // Group by original folderId
  const byFolder:Record<string,string[]>={};
  for(const m of msgs){
    const fid=m.folderId||"3117999000000008014";
    byFolder[fid]=byFolder[fid]||[];
    byFolder[fid].push(m.messageId);
  }

  // Move each group back
  let restored=0,failed=0;
  for(const[fid,mids]of Object.entries(byFolder)){
    const name=FOLDERS[fid]||fid;
    // Zoho move: POST /accounts/{aid}/messages/move with messageIds and destFolderId
    // Batch in groups of 50
    for(let i=0;i<mids.length;i+=50){
      const batch=mids.slice(i,i+50);
      const body={messageIds:batch.map(id=>`${TRASH}:${id}`),destFolderId:fid};
      const r=await fetch(`${BASE}/api/accounts/${ACCT}/messages/move`,{method:"POST",headers:{"Content-Type":"application/json",...h},body:JSON.stringify(body)});
      const txt=await r.text();
      if(r.ok||r.status===200){restored+=batch.length;}
      else{failed+=batch.length;console.log(`FAIL move to ${name}: ${r.status} ${txt}`);}
      await new Promise(s=>setTimeout(s,300));
    }
  }
  console.log(`Restored: ${restored}, Failed: ${failed}`);
}
main().catch(e=>console.error(e));
