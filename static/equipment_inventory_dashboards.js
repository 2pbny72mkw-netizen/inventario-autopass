
(()=>{ "use strict";
const cache=new Map();
const esc=s=>String(s??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]));
function params(panel){const q=new URLSearchParams();panel.querySelectorAll("[data-filter]").forEach(el=>{if(el.value)q.set(el.dataset.filter,el.value)});return q}
function fillSelect(el,values,keep){const cur=keep??el.value;el.innerHTML='<option value="">Todos</option>'+values.map(v=>`<option>${esc(v)}</option>`).join("");if(values.includes(cur))el.value=cur}
function bars(el,obj,limit=12,onClick){const entries=Object.entries(obj||{}).slice(0,limit),max=Math.max(1,...entries.map(x=>x[1]));el.innerHTML=entries.length?entries.map(([k,v])=>`<div class="invBarRow" data-key="${esc(k)}"><span title="${esc(k)}">${esc(k)}</span><div class="invTrack"><i style="width:${(v/max*100).toFixed(1)}%"></i></div><b>${v}</b></div>`).join(""):'<p class="muted">Sem dados no recorte.</p>';if(onClick)el.querySelectorAll(".invBarRow").forEach(r=>r.onclick=()=>onClick(r.dataset.key))}
function legend(el,obj,limit=8){const e=Object.entries(obj||{}).slice(0,limit);el.innerHTML=e.map(([k,v])=>`<div><span>${esc(k)}</span><b>${v}</b></div>`).join("")||'<p class="muted">Sem dados.</p>'}
function csvDownload(rows,family){const cols=["company","line","locality","type","asset","serial","model","supplier","version","status"];const lines=[cols.join(";"),...rows.map(r=>cols.map(c=>`"${String(r[c]??"").replace(/"/g,'""')}"`).join(";"))];const blob=new Blob(["\ufeff"+lines.join("\n")],{type:"text/csv;charset=utf-8"});const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download=`dashboard_${family}_inventario.csv`;a.click();URL.revokeObjectURL(a.href)}
async function load(panel){
 const family=panel.dataset.family,q=params(panel),url=`/api/dashboard/inventory-equipment/${family}?${q}`;
 panel.classList.add("loading");
 try{
   const res=await fetch(url,{cache:"no-store",headers:{Accept:"application/json"}});const d=await res.json();if(!res.ok||!d.ok)throw new Error(d.error||"Falha ao carregar");
   cache.set(panel,d);
   const set=(k,v)=>{const e=panel.querySelector(`[data-kpi="${k}"]`);if(e)e.textContent=v};
   set("total",d.total);set("totalDonut",d.total);set("locations",d.unique_locations);set("models",Object.keys(d.models||{}).length);set("inbase",d.in_base);set("divergences",d.divergences);set("rowsTag",`${d.total} registros`);
   const opts=d.options||{};
   [["company","companies"],["line","lines"],["locality","localities"],["model","models"],["status","statuses"],["subtype","subtypes"]].forEach(([f,o])=>{const el=panel.querySelector(`[data-filter="${f}"]`);if(el)fillSelect(el,opts[o]||[],el.value)});
   bars(panel.querySelector('[data-chart="companies"]'),d.companies,12,k=>{const e=panel.querySelector('[data-filter="company"]');if(e){e.value=k;load(panel)}});
   bars(panel.querySelector('[data-chart="locations"]'),d.locations,12,k=>{const e=panel.querySelector('[data-filter="locality"]');if(e){e.value=k;load(panel)}});
   bars(panel.querySelector('[data-chart="statuses"]'),d.statuses,10,k=>{const e=panel.querySelector('[data-filter="status"]');if(e){e.value=k;load(panel)}});
   bars(panel.querySelector('[data-chart="suppliers"]'),d.suppliers,10);
   const tech=panel.querySelector('[data-chart="versions"],[data-chart="installations"]'); if(tech) bars(tech,tech.dataset.chart==="installations"?d.installations:d.versions,10);
   const sub=panel.querySelector('[data-chart="subtypes"]'); if(sub) bars(sub,d.subtypes,6,k=>{const e=panel.querySelector('[data-filter="subtype"]');if(e){e.value=k;load(panel)}});
   legend(panel.querySelector('[data-chart="models"]'),d.models,8);
   const tbody=panel.querySelector('[data-table="assets"]');tbody.innerHTML=(d.assets||[]).slice(0,500).map(r=>`<tr><td>${esc(r.company)}</td><td>${esc(r.line)}</td><td>${esc(r.locality)}</td><td>${esc(r.type)}</td><td>${esc(r.asset)}</td><td>${esc(r.serial)}</td><td>${esc(r.model)}</td><td>${esc(r.supplier)}</td><td>${esc(r.version)}</td><td>${esc(r.status)}</td></tr>`).join("")||'<tr><td colspan="10">Sem registros no recorte.</td></tr>';
 }catch(err){panel.querySelectorAll(".invBars").forEach(e=>e.innerHTML=`<p class="muted">Falha ao carregar: ${esc(err.message)}</p>`)}
 finally{panel.classList.remove("loading")}
}
function init(panel){
 if(panel.dataset.ready)return;panel.dataset.ready="1";
 panel.querySelectorAll("[data-filter]").forEach(el=>el.addEventListener("change",()=>load(panel)));
 panel.querySelector(".invClear")?.addEventListener("click",()=>{panel.querySelectorAll("[data-filter]").forEach(e=>e.value="");load(panel)});
 panel.querySelector(".invExport")?.addEventListener("click",()=>{const d=cache.get(panel);if(d)csvDownload(d.assets||[],panel.dataset.family)});
}
function activate(view){document.querySelectorAll(`.invFamilyDash[data-v23-panel="${view}"]`).forEach(p=>{init(p);load(p)})}
document.addEventListener("click",e=>{const b=e.target.closest("[data-v23-view]");if(b)activate(b.dataset.v23View)});
window.addEventListener("DOMContentLoaded",()=>{document.querySelectorAll(".invFamilyDash").forEach(init);const v=new URLSearchParams(location.search).get("view");if(v)activate(v)});
})();
