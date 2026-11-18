(()=>{
"use strict";
if(window.__V72_JOURNEY_GUARD__)return;window.__V72_JOURNEY_GUARD__=1;
let timer=null,lastWarnKey="";
function banner(msg){let e=document.getElementById("v72JourneyWarn");if(!e){e=document.createElement("div");e.id="v72JourneyWarn";e.style.cssText="position:fixed;right:16px;bottom:16px;z-index:25000;max-width:380px;background:#fff7df;border:1px solid #e5b84a;color:#563d00;padding:12px 14px;border-radius:12px;box-shadow:0 8px 30px #0002;font-weight:700";document.body.appendChild(e)}e.textContent=msg}
async function check(){
 try{
  const r=await fetch("/api/v72/session-status",{cache:"no-store",headers:{Accept:"application/json"}});
  if(r.status===401){const d=await r.json().catch(()=>({}));location.href=d.redirect||"/acesso-fora-jornada";return}
  const d=await r.json();if(!d.ok||!d.controlled)return;
  if(!d.allowed){location.href="/acesso-fora-jornada";return}
  if(d.valid_until){
    const end=new Date(d.valid_until),ms=end-Date.now(),warn=(+d.warning_minutes||30)*60000;
    if(ms<=0){location.href="/acesso-fora-jornada";return}
    if(ms<=warn){
      const min=Math.max(1,Math.ceil(ms/60000)),key=d.valid_until+":"+min;
      if(key!==lastWarnKey){lastWarnKey=key;banner(`Sua jornada autorizada termina em aproximadamente ${min} minuto(s). Se precisar continuar, solicite extensão ao gestor.`)}
    }
    clearTimeout(timer);timer=setTimeout(check,Math.min(60000,Math.max(1000,ms+250)));
  }
 }catch(_){}
}
async function badge(){
 const e=document.getElementById("workAuthPending");if(!e)return;
 try{const d=await fetch("/api/gestao/autorizacoes-jornada/count",{cache:"no-store"}).then(r=>r.json());if(d.ok&&d.count){e.hidden=false;e.textContent=d.count;e.className="tag"}else e.hidden=true}catch(_){}
}
// REV17: jornada a cada 60 s (antes 20 s) e pausada com a aba oculta; confere na hora ao voltar para a aba. Contador a cada 2 min.
setInterval(()=>{if(document.visibilityState==='visible')check()},60000);setInterval(()=>{if(document.visibilityState==='visible')badge()},120000);document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')check()});check();badge();
})();