(()=>{
  'use strict';
  let timer=null, stopped=false, running=false, intervalMs=300000, lastSent=0;
  const now=()=>Date.now();
  async function sendPosition(force=false){
    if(stopped||running||!navigator.geolocation||!navigator.onLine) return;
    if(!force && now()-lastSent < Math.max(60000,intervalMs-5000)) return;
    running=true;
    navigator.geolocation.getCurrentPosition(async pos=>{
      try{
        const r=await fetch('/api/tecnico/position',{method:'POST',headers:{'Content-Type':'application/json','Accept':'application/json'},cache:'no-store',body:JSON.stringify({latitude:pos.coords.latitude,longitude:pos.coords.longitude,accuracy:pos.coords.accuracy})});
        if(r.ok) lastSent=now();
      }catch(_e){} finally{running=false}
    },()=>{running=false},{enableHighAccuracy:false,maximumAge:60000,timeout:10000});
  }
  async function start(){
    try{
      const r=await fetch('/api/v38/gps-config',{cache:'no-store',headers:{'Accept':'application/json'}});
      if(!r.ok) return; const cfg=await r.json(); if(!cfg.enabled) return;
      intervalMs=Math.max(60000,Number(cfg.interval_seconds||300)*1000);
    }catch(_e){}
    await sendPosition(true);
    timer=setInterval(()=>sendPosition(false),intervalMs);
  }
  function stop(){stopped=true;if(timer){clearInterval(timer);timer=null}}
  window.addEventListener('pagehide',stop,{once:true});
  window.addEventListener('beforeunload',stop,{once:true});
  document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')sendPosition(false)});
  start();
})();
