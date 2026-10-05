const $=x=>document.getElementById(x);
let savedItems=[], envs=[];

function pretty(v){try{return JSON.stringify(JSON.parse(v),null,2)}catch{return v}}
function formatAll(){$("headers").value=pretty($("headers").value);if($("body").value.trim())$("body").value=pretty($("body").value)}
function parseHeaders(){let x=$("headers").value.trim();if(!x)return{};let h=JSON.parse(x);if(!h||Array.isArray(h)||typeof h!=="object")throw Error("Headers must be a JSON object");return h}
function activeEnv(){let x=envs.find(e=>e.name===$("envSelect").value);return x?JSON.parse(x.variables||"{}"):{}}
function sizeOf(x){try{return new Blob([typeof x==="string"?x:JSON.stringify(x)]).size}catch{return 0}}

async function send(){
 let url=$("url").value.trim();if(!url)return alert("Enter a URL");
 let headers,body=null;try{headers=parseHeaders();let b=$("body").value.trim();if(b){try{body=JSON.parse(b)}catch{body=b}}}catch(e){return alert(e.message)}
 $("meta").textContent="TRANSMITTING";$("pretty").textContent="Sending request…";
 try{
  let r=await fetch("/api/send",{method:"POST",headers:{"Content-Type":"application/json"},
   body:JSON.stringify({method:$("method").value,url,headers,body,environment:activeEnv()})});
  let d=await r.json();
  if(!d.success){$("meta").textContent="REQUEST ERROR";$("status").textContent="ERR";$("pretty").textContent=JSON.stringify(d,null,2);return}
  $("meta").textContent="COMPLETE";$("status").textContent=d.status_code+" "+d.reason;$("status").className=d.status_code<400?"ok":"bad";
  $("time").textContent=d.response_time_ms+" ms";$("rtype").textContent=d.response_type.toUpperCase();
  $("size").textContent=sizeOf(d.body)+" B";let txt=typeof d.body==="string"?d.body:JSON.stringify(d.body,null,2);
  $("pretty").textContent=txt;$("raw").textContent=typeof d.body==="string"?d.body:JSON.stringify(d.body);
  $("rh").textContent=JSON.stringify(d.headers,null,2);loadHistory();
 }catch(e){$("meta").textContent="CLIENT ERROR";$("pretty").textContent=e.toString()}
}
async function save(){
 let name=prompt("Collection name");if(!name)return;
 try{let d=await (await fetch("/api/saved",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({
  name,method:$("method").value,url:$("url").value,headers:parseHeaders(),body:$("body").value
 })})).json();if(d.success){loadSaved();alert("Saved to collection")}}catch(e){alert(e.message)}
}
async function loadSaved(){
 savedItems=await (await fetch("/api/saved")).json();$("savedCount").textContent=savedItems.length;
 if(!$("savedList"))return;$("savedList").innerHTML=savedItems.length?savedItems.map(x=>`<div class="listitem"><div class="li-main"><b>${esc(x.name)}</b><small>${x.method} · ${esc(x.url)}</small></div><div class="li-actions"><button onclick="useSaved(${x.id})">USE</button><button onclick="delSaved(${x.id})">×</button></div></div>`).join(""):"<div class=empty>No saved requests.</div>"
}
function useSaved(id){let x=savedItems.find(v=>v.id===id);if(!x)return;$("method").value=x.method;$("url").value=x.url;$("headers").value=pretty(x.headers||"{}");$("body").value=x.body||"";view("tester",document.querySelector(".nav"));window.scrollTo({top:0,behavior:"smooth"})}
async function delSaved(id){await fetch("/api/saved/"+id,{method:"DELETE"});loadSaved()}
async function loadHistory(){
 let a=await (await fetch("/api/history")).json();$("historyCount").textContent=a.length;
 $("historyList").innerHTML=a.length?a.map(x=>`<div class="listitem"><div class="li-main"><b>${x.method} · ${x.status}</b><small>${esc(x.url)}</small></div><div>${x.ms} ms</div></div>`).join(""):"<div class=empty>No request history.</div>"
}
async function clearHistory(){await fetch("/api/history",{method:"DELETE"});loadHistory()}
async function loadEnv(){
 envs=await (await fetch("/api/env")).json();$("envSelect").innerHTML='<option value="">No environment</option>'+envs.map(x=>`<option>${esc(x.name)}</option>`).join("");
 $("envList").innerHTML=envs.map(x=>{let v=JSON.parse(x.variables||"{}");return `<div class="envrow"><b>${esc(x.name)}</b> · ${Object.keys(v).join(", ")}</div>`}).join("")||"<div class=empty>No environments yet.</div>"
}
async function saveEnv(){
 let n=$("envName").value.trim();if(!n)return alert("Environment name required");
 try{let v=JSON.parse($("envVars").value||"{}");await fetch("/api/env",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:n,variables:v})});$("envName").value="";$("envVars").value="";loadEnv()}catch(e){alert("Invalid JSON")}
}
function copyCurl(){
 let u=$("url").value,h={};try{h=parseHeaders()}catch(e){return alert(e.message)}
 let c=`curl -X ${$("method").value} ${JSON.stringify(u)}`;Object.entries(h).forEach(([k,v])=>c+=` -H ${JSON.stringify(k+": "+v)}`);let b=$("body").value.trim();if(b)c+=` --data ${JSON.stringify(b)}`;navigator.clipboard?.writeText(c);alert(c)
}
function generateCurl(){copyCurl()}
function decodeResponse(){view("tester",document.querySelector(".nav"));$("pretty").focus()}
function resetReq(){$("url").value="";$("headers").value="{}";$("body").value="";$("pretty").textContent="Fire a request to inspect the response.";$("status").textContent="—";$("time").textContent="—";$("rtype").textContent="—";$("size").textContent="—";$("meta").textContent="STANDBY"}
function tab(id,b){["pretty","raw","rh"].forEach(x=>$(x).classList.add("hidden"));$(id).classList.remove("hidden");document.querySelectorAll(".tab").forEach(x=>x.classList.remove("active"));b.classList.add("active")}
function view(id,b){document.querySelectorAll(".screen").forEach(x=>x.classList.remove("active"));$(id).classList.add("active");document.querySelectorAll(".nav").forEach(x=>x.classList.remove("active"));if(b)b.classList.add("active");if(id==="history")loadHistory();if(id==="saved")loadSaved();if(id==="env")loadEnv()}
function esc(s){return String(s).replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]))}
loadSaved();loadHistory();loadEnv();
