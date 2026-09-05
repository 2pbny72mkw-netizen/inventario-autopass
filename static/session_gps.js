(()=>{
'use strict'; if(window.__AUTOPASS_GPS_V762__)return;
const S=window.__AUTOPASS_GPS_V762__={stop:false,timer:null,busy:false,ms:60000,required:false,validated:false,key:null,history:false,watchId:null,lastGeo:null,lastGeoAt:0,lastOperationalAt:0,historySec:10,minMove:20,lastPostOkAt:0,lastGeofenceOkAt:0,lastResumeAt:0};
const Q='autopassGpsQueueV73';
function modal(show,msg){let x=document.getElementById('gpsRequiredV73');if(!x){x=document.createElement('div');x.id='gpsRequiredV73';x.style.cssText='position:fixed;inset:0;z-index:30000;background:rgba(15,23,42,.88);display:flex;align-items:center;justify-content:center;padding:20px';x.innerHTML='<div style="max-width:520px;background:#fff;border-radius:16px;padding:24px;text-align:center"><h2>Localização obrigatória</h2><p id="gpsReqMsg">Ative a localização para iniciar a atividade operacional.</p><button id="gpsReqBtn" class="primary" type="button">Ativar localização</button></div>';document.body.appendChild(x);x.querySelector('#gpsReqBtn').onclick=()=>capture(true,'manual')}x.querySelector('#gpsReqMsg').textContent=msg||'Ative a localização para iniciar a atividade operacional.';x.style.display=show?'flex':'none'}
function queued(){try{return JSON.parse(localStorage.getItem(Q)||'[]')}catch(_){return[]}}
function queue(v){const q=queued();q.push(v);localStorage.setItem(Q,JSON.stringify(q.slice(-60)))}
async function post(v){const r=await fetch('/api/tecnico/position',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(v),cache:'no-store'});if(!r.ok)throw new Error('gps post '+r.status);const j=await r.json();S.lastPostOkAt=Date.now();if(S.history){try{const g=await fetch('/api/tecnico/geofence-ping',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(v),cache:'no-store'});if(g.ok)S.lastGeofenceOkAt=Date.now()}catch(_){}}return j}
async function flush(){if(!navigator.onLine)return;const q=queued();if(!q.length)return;const left=[];let failed=false;for(const v of q){if(failed){left.push(v);continue}try{await post(v)}catch(_){left.push(v);failed=true}}localStorage.setItem(Q,JSON.stringify(left))}
function distM(a,b){if(!a||!b)return 1e9;const R=6371000,toRad=x=>x*Math.PI/180,dlat=toRad(b.latitude-a.latitude),dlon=toRad(b.longitude-a.longitude),la1=toRad(a.latitude),la2=toRad(b.latitude);const h=Math.sin(dlat/2)**2+Math.cos(la1)*Math.cos(la2)*Math.sin(dlon/2)**2;return 2*R*Math.asin(Math.sqrt(h))}
async function watchedPosition(p){if(S.stop)return;const now=Date.now(),v={latitude:p.coords.latitude,longitude:p.coords.longitude,accuracy:p.coords.accuracy,client_captured_at:new Date(p.timestamp||now).toISOString()};const moved=distM(S.lastGeo,v);if(now-S.lastGeoAt<S.historySec*1000 && moved<S.minMove)return;S.lastGeo=v;S.lastGeoAt=now;
  // Movimento relevante pode antecipar o heartbeat operacional.
  if(now-S.lastOperationalAt>=Math.min(S.ms,S.historySec*1000) || moved>=S.minMove){try{await post({...v,source:'session_watch',app_visibility:document.visibilityState});S.lastOperationalAt=now}catch(_){queue({...v,source:'session_watch',app_visibility:document.visibilityState})}}
}
function startWatch(){if(S.watchId!==null||!navigator.geolocation)return;S.watchId=navigator.geolocation.watchPosition(watchedPosition,()=>{}, {enableHighAccuracy:true,maximumAge:10000,timeout:20000})}
function schedule(delay=S.ms){clearTimeout(S.timer);if(!S.stop)S.timer=setTimeout(async()=>{if(document.visibilityState==='visible')await heartbeat('foreground_timer');schedule(S.ms)},Math.max(1000,delay))}
function markValidated(){S.validated=true;if(S.key)sessionStorage.setItem(S.key,'1');modal(false)}
function payloadFromPosition(p,source){const now=Date.now();const v={latitude:p.coords.latitude,longitude:p.coords.longitude,accuracy:p.coords.accuracy,source,client_captured_at:new Date(p.timestamp||now).toISOString(),app_visibility:document.visibilityState};S.lastGeo={latitude:v.latitude,longitude:v.longitude,accuracy:v.accuracy,client_captured_at:v.client_captured_at};S.lastGeoAt=now;return v}
function capture(initial=false,source){if(S.stop||S.busy)return Promise.resolve(false);if(!navigator.geolocation){if(initial&&S.required&&!S.validated)modal(true,'Este dispositivo/navegador não disponibilizou localização.');return Promise.resolve(false)}S.busy=true;return new Promise(resolve=>navigator.geolocation.getCurrentPosition(async p=>{const v=payloadFromPosition(p,source||(initial?'session_initial':'session_periodic'));try{if(navigator.onLine){await flush();await post(v);S.lastOperationalAt=Date.now();markValidated()}else{queue(v)}resolve(true)}catch(_){queue(v);if(initial&&S.required&&!S.validated)modal(true,'Localização obtida, mas não foi possível validar o envio.');resolve(false)}finally{S.busy=false}},()=>{S.busy=false;if(initial&&S.required&&!S.validated)modal(true,'Habilite o GPS e permita o acesso do navegador.');resolve(false)},{enableHighAccuracy:true,maximumAge:initial?0:Math.min(60000,S.ms),timeout:15000}))}
async function heartbeat(source='heartbeat'){
  if(S.stop||document.visibilityState!=='visible')return false;
  // Heartbeat independente de cliques/navegação. Tenta leitura atual; se o navegador não
  // fornecer uma nova leitura, reutiliza a última coordenada válida apenas como contato operacional.
  const ok=await capture(false,source);
  if(ok)return true;
  if(S.lastGeo && navigator.onLine && Date.now()-S.lastOperationalAt>=S.ms){
    const v={...S.lastGeo,source:source+'_last_known',heartbeat_only:true,heartbeat_at:new Date().toISOString(),app_visibility:document.visibilityState};
    try{await flush();await post(v);S.lastOperationalAt=Date.now();return true}catch(_){queue(v)}
  }
  return false;
}
async function resume(reason){if(S.stop||document.visibilityState!=='visible')return;const now=Date.now();if(now-S.lastResumeAt<3000)return;S.lastResumeAt=now;startWatch();await heartbeat('resume_'+reason);schedule(S.ms)}
async function start(){try{const c=await fetch('/api/v38/gps-config',{cache:'no-store'}).then(r=>r.json());if(!c.enabled)return;S.required=!!c.required;S.ms=Math.max(60000,(+c.interval_seconds||60)*1000);S.history=!!c.history_enabled;S.historySec=Math.max(10,+c.history_ping_seconds||10);S.minMove=Math.max(20,+c.history_min_movement_m||20);S.key='autopassGpsValidatedV73:'+String(c.session_token||'session');S.validated=sessionStorage.getItem(S.key)==='1';if(S.required&&!S.validated)modal(true);await capture(!S.validated,S.validated?'session_start':'session_initial');schedule(S.ms);startWatch()}catch(e){console.warn('GPS V76.2 indisponível',e)}}
function stop(clearValidation=false){S.stop=true;clearTimeout(S.timer);if(S.watchId!==null&&navigator.geolocation){navigator.geolocation.clearWatch(S.watchId);S.watchId=null}if(clearValidation&&S.key)sessionStorage.removeItem(S.key)}
window.AutopassGpsDebug=()=>({release:'V76.2',enabled:!S.stop,required:S.required,history:S.history,visibility:document.visibilityState,interval_ms:S.ms,history_sec:S.historySec,min_movement_m:S.minMove,last_post_ok_at:S.lastPostOkAt?new Date(S.lastPostOkAt).toISOString():null,last_geofence_ok_at:S.lastGeofenceOkAt?new Date(S.lastGeofenceOkAt).toISOString():null,last_operational_at:S.lastOperationalAt?new Date(S.lastOperationalAt).toISOString():null,queue:queued().length,last_geo:S.lastGeo});
window.addEventListener('online',()=>{flush();resume('online')});
document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')resume('visibility')});
window.addEventListener('focus',()=>resume('focus'));
window.addEventListener('pageshow',()=>resume('pageshow'));
document.querySelectorAll('a[href="/logout"]').forEach(a=>a.addEventListener('click',()=>stop(true),{capture:true}));
start();
})();
