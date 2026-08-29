const $=id=>document.getElementById(id), esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));let panData=[],current=null,panGps=null,panNearbyOnly=false,panCollapsed=true;
async function loadPan(){const d=await fetch('/api/panoramas',{cache:'no-store'}).then(r=>r.json());panData=d.locations||[];fillFilters();render()}
function fillFilters(){const fill=(id,vals)=>{const el=$(id),keep=el.value;el.innerHTML='<option value="">Todas</option>'+[...new Set(vals.filter(Boolean))].sort().map(v=>`<option>${esc(v)}</option>`).join('');el.value=[...el.options].some(o=>o.value===keep)?keep:''};fill('panCompany',panData.map(x=>x.company));const c=$('panCompany').value;fill('panLine',panData.filter(x=>!c||x.company===c).map(x=>x.line))}
function distM(a,b,c,d){const R=6371000,r=x=>x*Math.PI/180,p1=r(a),p2=r(c),dp=r(c-a),dl=r(d-b),z=Math.sin(dp/2)**2+Math.cos(p1)*Math.cos(p2)*Math.sin(dl/2)**2;return 2*R*Math.asin(Math.sqrt(z))}function filtered(){const q=$('panSearch').value.toLowerCase(),c=$('panCompany').value,l=$('panLine').value,s=$('panStatus').value;let a=panData.filter(x=>(!q||x.location.toLowerCase().includes(q))&&(!c||x.company===c)&&(!l||x.line===l)&&(!s||x.status===s));if(panGps){a=a.map(x=>({...x,_distance:(Number.isFinite(+x.reference_latitude)&&Number.isFinite(+x.reference_longitude))?distM(panGps.lat,panGps.lon,+x.reference_latitude,+x.reference_longitude):Infinity}));if(panNearbyOnly)a=a.filter(x=>x._distance<=3000);a.sort((x,y)=>x._distance-y._distance)}return a}
function render(){const a=filtered(),pend=a.filter(x=>x.status==='PENDENTE').length,prog=a.filter(x=>x.status==='EM ANDAMENTO').length,done=a.filter(x=>x.status==='CONCLUÍDA').length,pct=a.length?Math.round(done/a.length*100):0;$('panTotal').textContent=a.length;$('panPending').textContent=pend;$('panProgress').textContent=prog;$('panDone').textContent=done;$('panProgTotal').textContent=a.length;$('panProgPending').textContent=pend;$('panProgIn').textContent=prog;$('panProgDone').textContent=done;$('panPct').textContent=pct+'%';$('panProgressBar').style.width=pct+'%';if($('panSegDone'))$('panSegDone').style.width=(a.length?done/a.length*100:0)+'%';if($('panSegIn'))$('panSegIn').style.width=(a.length?prog/a.length*100:0)+'%';if($('panSegPending'))$('panSegPending').style.width=(a.length?pend/a.length*100:0)+'%';$('panLocations').classList.toggle('hidden',panCollapsed);$('panCollapsedPicker')?.classList.toggle('hidden',!panCollapsed);if($('panLocationPicker')){$('panLocationPicker').innerHTML='<option value="">Selecione uma estação/localidade</option>'+a.map(x=>`<option value="${x.id}">${esc(x.line)} · ${esc(x.location)} · ${esc(x.status)}</option>`).join('')}$('panLocations').innerHTML=a.map(x=>`<button class="card panoramaLocation" data-id="${x.id}"><small>${esc(x.company)} · ${esc(x.line)}</small><b>${esc(x.location)}</b><span class="tag">${esc(x.status)}</span><small>${x.photo_count} foto(s) · ${x.points.length} ponto(s)${Number.isFinite(x._distance)?` · ${Math.round(x._distance)} m`:''}</small></button>`).join('')||(panNearbyOnly?'<p class="muted">Nenhuma localidade em até 3 km da posição atual.</p>':'');document.querySelectorAll('.panoramaLocation').forEach(b=>b.onclick=()=>openLoc(+b.dataset.id))}
function openLoc(id){current=panData.find(x=>x.id===id);if(!current)return;$('panLocationId')&&($('panLocationId').value=id);$('panModalTitle').textContent=current.location;$('panModalMeta').textContent=`${current.company} · ${current.line} · ${current.status}`;renderPoints();$('panModal').classList.remove('hidden')}
function renderPoints(){$('panPoints').innerHTML=(current.points||[]).map(p=>`<section class="panPoint"><div class="sectionHead"><div><h3>${esc(p.name)}</h3><small>${p.photos.length} foto(s) · ${esc(p.status)}</small></div></div><div class="panGallery">${p.photos.map(ph=>`<figure><a href="${esc(ph.url)}" target="_blank"><img loading="lazy" src="${esc(ph.url)}"></a><figcaption>${esc(ph.uploaded_by)} · ${new Date(ph.created_at).toLocaleString('pt-BR')}${window.PAN_ROLE==='manager'?`<button type="button" class="dangerGhost" data-del="${ph.id}">Excluir</button>`:''}</figcaption></figure>`).join('')||'<p class="muted">Nenhuma foto.</p>'}</div></section>`).join('')||'<p class="muted">Nenhum ponto panorâmico iniciado.</p>';document.querySelectorAll('[data-del]').forEach(b=>b.onclick=async()=>{if(!confirm('Excluir esta foto?'))return;const id=current?.id;const r=await fetch('/api/panoramas/photos/'+b.dataset.del,{method:'DELETE'}),d=await r.json().catch(()=>({}));if(!r.ok){alert(d.error||'Não foi possível excluir a foto.');return}panStatus(`Foto excluída. Status da localidade: ${d.status||'atualizado'}.`,true);await loadPan();if(id&&panData.some(x=>x.id===id))openLoc(id)})}

function panoramaFiles(){
  const all=[...($('panPhotos')?.files||[]),...($('panCameraInput')?.files||[])], seen=new Set();
  return all.filter(f=>{const k=`${f.name}|${f.size}|${f.lastModified}`;if(seen.has(k))return false;seen.add(k);return true});
}
function panStatus(msg,ok=false){const el=$('panSaveStatus');if(el){el.textContent=msg||'';el.classList.toggle('successText',!!ok)}}
function getGpsForUpload(fd){return new Promise(res=>{if(!navigator.geolocation)return res();navigator.geolocation.getCurrentPosition(p=>{fd.set('latitude',p.coords.latitude);fd.set('longitude',p.coords.longitude);res()},()=>res(),{enableHighAccuracy:false,timeout:2500,maximumAge:30000})})}

$('panLocationPicker')&&($('panLocationPicker').onchange=e=>{if(e.target.value)openLoc(+e.target.value)});$('panToggleLocations').onclick=()=>{panCollapsed=!panCollapsed;$('panToggleLocations').textContent=panCollapsed?'Mostrar estações':'Recolher estações';render()};$('panGpsBtn').onclick=()=>{if(panNearbyOnly){panNearbyOnly=false;$('panGpsInfo').textContent=panGps?'GPS mantido; exibindo todas as estações.':'';$('panGpsBtn').textContent='📍 Estações próximas';render();return}if(panGps){panNearbyOnly=true;$('panGpsInfo').textContent=`Mostrando estações em até 3 km · precisão ±${Math.round(panGps.acc||0)} m`;$('panGpsBtn').textContent='Mostrar todas';render();return}if(!navigator.geolocation){$('panGpsInfo').textContent='GPS indisponível neste navegador.';return}$('panGpsInfo').textContent='Obtendo localização...';navigator.geolocation.getCurrentPosition(p=>{panGps={lat:p.coords.latitude,lon:p.coords.longitude,acc:p.coords.accuracy};panNearbyOnly=true;$('panGpsInfo').textContent=`Mostrando estações em até 3 km · precisão ±${Math.round(p.coords.accuracy)} m`;$('panGpsBtn').textContent='Mostrar todas';render()},()=>{$('panGpsInfo').textContent='Não foi possível obter a localização. Verifique a permissão/GPS.'},{enableHighAccuracy:true,timeout:12000,maximumAge:10000})};
['panCompany','panLine','panStatus'].forEach(id=>$(id).onchange=()=>{if(id==='panCompany'){const c=$('panCompany').value,keep=$('panLine').value,vals=[...new Set(panData.filter(x=>!c||x.company===c).map(x=>x.line).filter(Boolean))].sort();$('panLine').innerHTML='<option value="">Todas</option>'+vals.map(v=>`<option>${esc(v)}</option>`).join('');$('panLine').value=vals.includes(keep)?keep:''}render()});$('panSearch').oninput=render;$('panClose').onclick=()=>$('panModal').classList.add('hidden');$('panCamera')&&($('panCamera').onclick=()=>$('panCameraInput').click());
$('panCameraInput')&&($('panCameraInput').onchange=()=>panStatus(`${panoramaFiles().length} foto(s) pronta(s) para salvar.`));
$('panPhotos')&&($('panPhotos').onchange=()=>panStatus(`${panoramaFiles().length} foto(s) pronta(s) para salvar.`));

$('panForm')&&($('panForm').onsubmit=async e=>{
  e.preventDefault();
  const form=e.currentTarget, btn=$('panSaveBtn'), locationId=$('panLocationId')?.value, files=panoramaFiles(), pointName=$('panPointName')?.value||'';
  if(!locationId){panStatus('Localidade não identificada. Feche e abra a estação novamente.');return}
  if(!files.length){panStatus('Selecione ou tire pelo menos uma foto.');return}
  if(!form.reportValidity())return;
  const oldText=btn?.textContent||'Salvar fotos';
  try{
    if(btn){btn.disabled=true;btn.textContent='Salvando...'}
    panStatus(`Enviando ${files.length} foto(s)... não feche esta tela.`);
    const fd=new FormData(form);fd.delete('photos');files.forEach(f=>fd.append('photos',f,f.name));
    await getGpsForUpload(fd);
    const ctl=new AbortController(), timer=setTimeout(()=>ctl.abort(),90000);
    let r;
    try{r=await fetch(`/api/panoramas/${locationId}/points`,{method:'POST',body:fd,signal:ctl.signal})}finally{clearTimeout(timer)}
    const raw=await r.text();let d={};try{d=raw?JSON.parse(raw):{}}catch(_){d={error:raw?.slice(0,180)||`Resposta inválida do servidor (${r.status}).`}}
    if(!r.ok||d.ok===false)throw new Error(d.error||`Falha ao salvar (${r.status}).`);
    panStatus(d.message||`${d.photos_added||files.length} foto(s) salva(s) com sucesso.`,true);
    form.reset();if($('panPointName'))$('panPointName').value=pointName;if($('panCameraInput'))$('panCameraInput').value='';
    const id=+locationId;await loadPan();openLoc(id);
  }catch(err){
    console.error('Panorama upload',err);
    panStatus(err?.name==='AbortError'?'Tempo de envio excedido. Verifique a conexão e tente novamente.':(err?.message||'Não foi possível salvar as fotos.'));
  }finally{
    if(btn){btn.disabled=false;btn.textContent=oldText}
  }
});
if($('panToggleLocations'))$('panToggleLocations').textContent='Mostrar estações';
loadPan();

if($('panWhatsImport'))$('panWhatsImport').onclick=async()=>{const f=$('panWhatsZip')?.files?.[0];if(!f){alert('Selecione o ZIP do WhatsApp.');return}const fd=new FormData();fd.append('zip',f);$('panWhatsStatus').textContent='Importando e relacionando fotos...';const r=await fetch('/api/panoramas/import-whatsapp',{method:'POST',body:fd});const d=await r.json();if(!r.ok){$('panWhatsStatus').textContent=d.error||'Falha na importação.';return}$('panWhatsStatus').textContent=`${d.imported.length} importada(s) · ${d.unresolved.length} não identificada(s) · ${d.duplicates} duplicada(s)`;$('panWhatsResult').innerHTML=d.unresolved.length?`<details><summary>Conferir ${d.unresolved.length} arquivo(s) não identificado(s)</summary><div class="panUnresolved">${d.unresolved.map(x=>`<small>${esc(x)}</small>`).join('')}</div></details>`:'<p class="successText">Todas as fotos válidas foram associadas.</p>';await loadPan()};

function updatePanPptLink(){const b=$('panPptBtn');if(!b)return;const q=new URLSearchParams();if($('panCompany')?.value)q.set('company',$('panCompany').value);if($('panLine')?.value)q.set('line',$('panLine').value);if($('panStatus')?.value)q.set('status',$('panStatus').value);if($('panSearch')?.value)q.set('search',$('panSearch').value);b.href='/api/panoramas/export.pptx'+(q.toString()?'?'+q.toString():'')}
document.addEventListener('change',e=>{if(['panCompany','panLine','panStatus'].includes(e.target.id))updatePanPptLink()});document.addEventListener('input',e=>{if(e.target.id==='panSearch')updatePanPptLink()});document.addEventListener('DOMContentLoaded',updatePanPptLink);

// V50.1 — controle administrativo de status da Visão Panorâmica.
function panSyncAdminStatus(){
  const sel=$('panAdminStatus'),info=$('panAdminStatusInfo'); if(!sel||!current)return;
  sel.value=current.status_override?(current.status||'PENDENTE'):'AUTOMÁTICO';
  if(info)info.textContent=current.status_override?`Status manual: ${current.status}`:`Automático: ${current.auto_status||current.status}`;
}
$('panAdminStatusSave')&&($('panAdminStatusSave').onclick=async()=>{
  if(!current)return; const sel=$('panAdminStatus'),btn=$('panAdminStatusSave'); btn.disabled=true;
  try{const r=await fetch(`/api/panoramas/${current.id}/status`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({status:sel.value})});const d=await r.json().catch(()=>({}));if(!r.ok){alert(d.error||'Não foi possível alterar o status.');return}panStatus(`Status alterado para ${d.status}.`,true);const id=current.id;await loadPan();if(panData.some(x=>x.id===id))openLoc(id);}finally{btn.disabled=false}
});
const _panOpenLocV501=typeof openLoc==='function'?openLoc:null;
if(_panOpenLocV501){openLoc=function(id){_panOpenLocV501(id);setTimeout(panSyncAdminStatus,0)}}


// V66 REV1 — PowerPoint vinculado aos filtros atuais, com cancelamento cooperativo.
let panV66Timer=null, panV66Job=null, panV66JobKey=null;
function panV66Filters(){const f=new URLSearchParams();if($('panCompany')?.value)f.set('company',$('panCompany').value);if($('panLine')?.value)f.set('line',$('panLine').value);if($('panStatus')?.value)f.set('status',$('panStatus').value);if($('panSearch')?.value)f.set('search',$('panSearch').value.trim().toLowerCase());return f}
function panV66FilterKey(){const f=panV66Filters();const o={company:f.get('company')||'',line:f.get('line')||'',status:f.get('status')||'',search:f.get('search')||''};return JSON.stringify(o,Object.keys(o).sort())}
function panV66Button(text,href='#',state='idle'){const b=$('panPptNavBtn');if(!b)return;b.textContent=text;b.href=href;b.dataset.state=state}
function panV66Reset(){clearTimeout(panV66Timer);panV66Timer=null;panV66Job=null;panV66JobKey=null;panV66Button('PowerPoint','#','idle')}
async function panV66Poll(id){clearTimeout(panV66Timer);try{const r=await fetch(`/api/panoramas/export.pptx/jobs/${id}?_=${Date.now()}`,{cache:'no-store'}),d=await r.json();if(!r.ok)throw new Error(d.error||'Falha ao consultar PowerPoint');if(d.filter_key&&d.filter_key!==panV66FilterKey()){panV66Reset();return}panV66JobKey=d.filter_key||panV66JobKey;if(d.status==='PRONTO'){panV66Button('Baixar PowerPoint',d.download_url,'ready');return}if(['ERRO','CANCELADO'].includes(d.status)){panV66Reset();return}panV66Button(`Gerando... ${Math.max(0,Math.min(100,+d.progress||0))}%`,'#','running');panV66Timer=setTimeout(()=>panV66Poll(id),2500)}catch(_){panV66Timer=setTimeout(()=>panV66Poll(id),8000)}}
async function panV66Recover(){try{const key=panV66FilterKey(),d=await fetch('/api/processamentos',{cache:'no-store'}).then(r=>r.json()),jobs=(d.jobs||[]).filter(x=>x.type==='POWERPOINT_PANORAMA'&&x.filter_key===key&&['FILA','PROCESSANDO','PRONTO'].includes(x.status));const j=jobs[0];if(!j){panV66Reset();return}panV66Job=j.id;panV66JobKey=j.filter_key;if(j.status==='PRONTO'&&j.download_url){panV66Button('Baixar PowerPoint',j.download_url,'ready');return}panV66Button(`Gerando... ${Math.max(0,Math.min(100,+j.progress||0))}%`,'#','running');if(j.id)panV66Poll(j.id)}catch(_){panV66Reset()}}
async function panV66Cancel(){if(!panV66Job)return;const id=panV66Job;panV66Button('Cancelando...','#','cancelling');try{await fetch(`/api/panoramas/export.pptx/jobs/${id}/cancel`,{method:'POST',cache:'no-store'})}finally{setTimeout(()=>panV66Poll(id),500)}}
$('panPptNavBtn')?.addEventListener('click',async e=>{const b=$('panPptNavBtn');if(b.dataset.state==='ready'&&b.href&&b.href!=='#')return;e.preventDefault();if(b.dataset.state==='running'||b.dataset.state==='cancelling'){if(b.dataset.state==='running'&&confirm('Cancelar a geração deste PowerPoint?'))await panV66Cancel();return}try{const key=panV66FilterKey();panV66Button('Iniciando...','#','running');const r=await fetch('/api/panoramas/export.pptx/jobs',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded;charset=UTF-8'},body:panV66Filters().toString(),cache:'no-store'}),d=await r.json();if(!r.ok||!d.job_id)throw new Error(d.error||'Falha ao iniciar PowerPoint');panV66Job=d.job_id;panV66JobKey=d.filter_key||key;panV66Poll(panV66Job)}catch(err){panV66Reset();if(typeof panStatus==='function')panStatus(err.message||'Falha ao gerar PowerPoint')}});
['panCompany','panLine','panStatus'].forEach(id=>$(id)?.addEventListener('change',()=>{if(panV66JobKey&&panV66JobKey!==panV66FilterKey())panV66Reset();setTimeout(panV66Recover,80)}));
$('panSearch')?.addEventListener('input',()=>{if(panV66JobKey&&panV66JobKey!==panV66FilterKey())panV66Reset()});
$('panSearch')?.addEventListener('change',()=>setTimeout(panV66Recover,80));
window.addEventListener('load',()=>setTimeout(panV66Recover,250),{once:true});

