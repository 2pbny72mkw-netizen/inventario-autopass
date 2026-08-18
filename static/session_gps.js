(()=>{
  'use strict';
  if(window.__SUPORTE_CAMPO_GPS_V392__) return;
  const ctl=window.__SUPORTE_CAMPO_GPS_V392__={stopped:false,timer:null,running:false,intervalMs:300000,lastSent:0};
  const now=()=>Date.now();
  function clearTimer(){ if(ctl.timer){clearTimeout(ctl.timer);ctl.timer=null;} }
  function schedule(){
    clearTimer();
    if(ctl.stopped) return;
    ctl.timer=setTimeout(async()=>{
      if(document.visibilityState==='visible') await sendPosition(false);
      schedule();
    },ctl.intervalMs);
  }
  async function sendPosition(force=false){
    if(ctl.stopped||ctl.running||!navigator.geolocation||!navigator.onLine||document.visibilityState!=='visible') return;
    if(!force && now()-ctl.lastSent < Math.max(60000,ctl.intervalMs-5000)) return;
    ctl.running=true;
    navigator.geolocation.getCurrentPosition(async pos=>{
      try{
        const r=await fetch('/api/tecnico/position',{method:'POST',headers:{'Content-Type':'application/json','Accept':'application/json'},cache:'no-store',keepalive:false,body:JSON.stringify({latitude:pos.coords.latitude,longitude:pos.coords.longitude,accuracy:pos.coords.accuracy})});
        if(r.ok) ctl.lastSent=now();
      }catch(_e){} finally{ctl.running=false;}
    },()=>{ctl.running=false;},{enableHighAccuracy:false,maximumAge:120000,timeout:8000});
  }
  async function start(){
    try{
      const r=await fetch('/api/v38/gps-config',{cache:'no-store',headers:{'Accept':'application/json'}});
      if(!r.ok) return;
      const cfg=await r.json();
      if(!cfg.enabled) return;
      ctl.intervalMs=Math.max(60000,Number(cfg.interval_seconds||300)*1000);
    }catch(_e){return;}
    await sendPosition(true);
    schedule();
  }
  function stop(){ctl.stopped=true;clearTimer();ctl.running=false;}
  window.addEventListener('pagehide',stop,{once:true});
  window.addEventListener('beforeunload',stop,{once:true});
  document.addEventListener('visibilitychange',()=>{
    if(document.visibilityState==='hidden') clearTimer();
    else if(!ctl.stopped){sendPosition(false);schedule();}
  });
  start();
})();
