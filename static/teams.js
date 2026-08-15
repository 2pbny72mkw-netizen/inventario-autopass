window.AUTOPASS_TEAMS_VERSION='teams-v9-2';
console.log('AUTOPASS Central Operacional V9.2 carregada');

const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmtDate=s=>{
  if(!s) return '—';
  const [y,m,d]=String(s).split('-');
  return d&&m&&y?`${d}/${m}`:s;
};
const weekday=s=>{
  const d=new Date(`${s}T12:00:00`);
  return ['Dom','Seg','Ter','Qua','Qui','Sex','Sáb'][d.getDay()];
};

let teamMap=null;
let tileLayer=null;
let markers=[];
let profilesCache=[];
let usersCache=[];

function createTeamMap(){
  if(teamMap) return;
  teamMap=L.map('teamMap',{
    scrollWheelZoom:true,
    preferCanvas:true,
    zoomControl:true
  }).setView([-23.5505,-46.6333],10);

  tileLayer=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{
    maxZoom:19,
    tileSize:256,
    zoomOffset:0,
    updateWhenIdle:false,
    keepBuffer:4,
    attribution:'&copy; OpenStreetMap contributors'
  }).addTo(teamMap);

  const container=$('teamMap');
  if('ResizeObserver' in window){
    const observer=new ResizeObserver(()=>{
      if(teamMap) requestAnimationFrame(()=>teamMap.invalidateSize({pan:false}));
    });
    observer.observe(container);
  }
}
function rebuildMapIfNeeded(){
  createTeamMap();
  requestAnimationFrame(()=>{
    teamMap.invalidateSize({pan:false});
    setTimeout(()=>teamMap.invalidateSize({pan:false}),120);
    setTimeout(()=>teamMap.invalidateSize({pan:false}),350);
  });
}
function freshnessClass(value){
  return value==='ATUAL'?'current':
         value==='ATENÇÃO'?'attention':
         value==='ATRASADO'?'late':'noSignal';
}
function categoryClass(value){
  return value==='SUPERVISOR'?'supervisor':
         value==='APOIO'?'support':'technician';
}
function initials(name){
  return String(name||'?').trim().split(/\s+/).slice(0,2).map(x=>x[0]||'').join('').toUpperCase();
}
function avatarHtml(t){
  const cls=freshnessClass(t.freshness);
  if(t.photo_url){
    // Background-image avoids global/Leaflet <img> rules stretching profile photos.
    const safeUrl=String(t.photo_url).replace(/[\"'()]/g, encodeURIComponent);
    return `<div class="avatarRing ${cls}"><div class="teamCardAvatarPhoto" style="background-image:url(&quot;${esc(safeUrl)}&quot;)" role="img" aria-label="${esc(t.name)}"></div></div>`;
  }
  return `<div class="avatarRing ${cls}"><div class="avatarFallback">${esc(initials(t.name))}</div></div>`;
}
function freshnessText(t){
  if(!t.linked) return 'Não vinculado a um usuário';
  if(t.minutes_since==null) return 'Sem localização recebida';
  if(t.minutes_since===0) return 'Localização recebida agora';
  return `${t.minutes_since} min desde a última posição`;
}
function markerIcon(t){
  const cls=freshnessClass(t.freshness);
  const photo=t.photo_url
    ? `<span class="teamMapAvatarPhoto" style="background-image:url(&quot;${esc(String(t.photo_url).replace(/[\"'()]/g, encodeURIComponent))}&quot;)"></span>`
    : `<span class="teamMapAvatarInitials">${esc(initials(t.name))}</span>`;
  return L.divIcon({
    className:'teamAvatarMarker',
    html:`<div class="teamMapAvatar ${cls} ${categoryClass(t.category)}">${photo}</div>`,
    iconSize:L.point(52,52),
    iconAnchor:L.point(26,26),
    popupAnchor:L.point(0,-28)
  });
}
async function loadTeams(){
  createTeamMap();
  const r=await fetch('/api/equipes/status',{cache:'no-store'});
  const d=await r.json();
  if(!r.ok||!d.ok) throw new Error(d.error||'Falha ao carregar equipes.');

  $('teamDate').textContent=d.date||'—';
  $('teamClock').textContent=`${d.date||''} ${d.time||''}`.trim();
  $('kScheduled').textContent=d.scheduled||0;
  $('kSupervisors').textContent=d.counts_by_category?.SUPERVISOR||0;
  $('kSupport').textContent=d.counts_by_category?.APOIO||0;

  let current=0,attention=0,noSignal=0;
  markers.forEach(m=>teamMap.removeLayer(m));
  markers=[];

  $('teamCards').innerHTML='';
  for(const t of d.technicians||[]){
    if(t.freshness==='ATUAL') current++;
    else if(t.freshness==='ATENÇÃO'||t.freshness==='ATRASADO') attention++;
    else noSignal++;

    const card=document.createElement('article');
    card.className=`teamCard freshness-${freshnessClass(t.freshness)} category-${categoryClass(t.category)}`;
    card.innerHTML=`
      ${avatarHtml(t)}
      <div class="teamCardBody">
        <div class="teamNameRow">
          <b>${esc(t.name)}</b>
          <span class="categoryBadge ${categoryClass(t.category)}">${esc(t.category)}</span>
        </div>
        <small><b>${esc(t.schedule_type)}</b> · ${esc(t.shift||'—')} · entrada ${esc(t.entry||'—')}</small>
        ${t.lines?.length?`<small>Linhas ${esc(t.lines.join(' / '))}</small>`:''}
        ${t.supervision?`<small>${esc(t.supervision)}</small>`:''}
        <span class="lastPosition">${esc(freshnessText(t))}</span>
        <span class="linkBadge ${t.linked?'linked':'unlinked'}">${t.linked?'Usuário vinculado':'Sem vínculo com Usuários'}</span>
      </div>`;
    $('teamCards').appendChild(card);

    if(t.latitude!=null&&t.longitude!=null){
      const m=L.marker([Number(t.latitude),Number(t.longitude)],{icon:markerIcon(t)})
        .addTo(teamMap)
        .bindPopup(`
          <div class="teamMapPopup">
            <b>${esc(t.name)}</b><br>
            ${esc(t.category)} · ${esc(t.shift||'')}<br>
            Entrada: ${esc(t.entry||'—')}<br>
            ${t.accuracy!=null?`Precisão GPS: ${Math.round(Number(t.accuracy))} m<br>`:''}
            ${esc(freshnessText(t))}
          </div>
        `,{maxWidth:260,closeButton:true});
      markers.push(m);
    }
  }

  $('kCurrent').textContent=current;
  $('kAttention').textContent=attention;
  $('kNoSignal').textContent=noSignal;

  if(markers.length){
    const bounds=L.featureGroup(markers).getBounds();
    if(bounds.isValid()) teamMap.fitBounds(bounds.pad(.18),{maxZoom:15});
  }else{
    teamMap.setView([-23.5505,-46.6333],10);
  }
  rebuildMapIfNeeded();
}

async function loadCalendar(){
  const params=new URLSearchParams({
    start:$('calendarStart').value,
    days:$('calendarDays').value
  });
  if($('calendarCategory').value) params.set('category',$('calendarCategory').value);

  const r=await fetch(`/api/equipes/calendario?${params.toString()}`,{cache:'no-store'});
  const d=await r.json();
  if(!r.ok||!d.ok) throw new Error(d.error||'Falha ao carregar escala.');

  $('scaleHead').innerHTML=`
    <tr>
      <th class="stickyTechCol">Nome</th>
      <th>Categoria</th>
      <th>Escala</th>
      <th>Turno</th>
      <th>Entrada</th>
      ${d.dates.map(x=>`<th><b>${weekday(x)}</b><small>${fmtDate(x)}</small></th>`).join('')}
    </tr>`;

  $('scaleBody').innerHTML=(d.members||[]).map(t=>`
    <tr class="scale-${categoryClass(t.category)}">
      <td class="stickyTechCol">
        <b>${esc(t.name)}</b>
        <small>${t.linked?'✓ '+esc(t.linked_user_name):'Não vinculado'}</small>
      </td>
      <td><span class="categoryBadge ${categoryClass(t.category)}">${esc(t.category)}</span></td>
      <td>${esc(t.schedule_type)}</td>
      <td>${esc(t.shift)}</td>
      <td>${esc(t.entry||'—')}</td>
      ${t.days.map(day=>`
        <td class="${day.scheduled?'scaleWork':'scaleOff'}">
          ${day.scheduled?esc(t.shift.replaceAll(':00','')):'Folga'}
        </td>`).join('')}
    </tr>`).join('');
}

async function loadProfiles(){
  if(!$('scheduleProfiles')) return;
  const r=await fetch('/api/equipes/perfis',{cache:'no-store'});
  const d=await r.json();
  if(!r.ok||!d.ok) throw new Error(d.error||'Falha ao carregar perfis.');

  profilesCache=d.profiles||[];
  usersCache=d.users||[];
  $('scheduleUser').innerHTML='<option value="">Não vinculado / nome manual</option>'+
    usersCache.map(u=>`<option value="${u.id}">${esc(u.name)}${u.user_code?' · '+esc(u.user_code):''} · ${esc(u.role)}</option>`).join('');

  const linked=profilesCache.filter(p=>p.active&&p.linked).length;
  const active=profilesCache.filter(p=>p.active).length;
  $('linkSummary').textContent=`${linked}/${active} com usuário vinculado`;
  renderProfiles();
}
function renderProfiles(){
  const q=String($('scheduleSearch')?.value||'').toUpperCase();
  const rows=profilesCache.filter(p=>{
    const hay=[p.name,p.entry,p.linked_user_name,p.category,p.shift,p.schedule_type].join(' ').toUpperCase();
    return !q||hay.includes(q);
  });

  $('scheduleProfiles').innerHTML=rows.map(p=>`
    <article class="scheduleProfile ${p.active?'':'profileInactive'} category-${categoryClass(p.category)}">
      <div>
        <div class="profileTitle">
          <b>${esc(p.name)}</b>
          <span class="categoryBadge ${categoryClass(p.category)}">${esc(p.category)}</span>
          <span class="linkBadge ${p.linked?'linked':'unlinked'}">${p.linked?'Vinculado':'Não vinculado'}</span>
        </div>
        <small>${esc(p.schedule_type)} · ${esc(p.shift)} · entrada <b>${esc(p.entry||'—')}</b></small>
        <small>${p.lines?.length?'Linhas '+esc(p.lines.join('/'))+' · ':''}${esc(p.supervision||'')}</small>
        ${p.linked?`<small>Usuário: ${esc(p.linked_user_name)}</small>`:''}
      </div>
      <div class="scheduleProfileActions">
        ${p.active?`
          <button type="button" class="secondary" data-edit-profile="${p.profile_id}">Editar / mudar escala</button>
          <button type="button" class="dangerGhost" data-remove-profile="${p.profile_id}">Remover da escala</button>
        `:`<span class="muted">Fora da escala</span>`}
      </div>
    </article>`).join('');

  document.querySelectorAll('[data-edit-profile]').forEach(btn=>{
    btn.addEventListener('click',()=>editProfile(Number(btn.dataset.editProfile)));
  });
  document.querySelectorAll('[data-remove-profile]').forEach(btn=>{
    btn.addEventListener('click',()=>removeProfile(Number(btn.dataset.removeProfile)));
  });
}
function syncScheduleDefaults(){
  const category=$('scheduleCategory').value;
  const type=$('scheduleType').value;
  if(category==='APOIO'){
    $('scheduleType').value='5x2';
    $('scheduleShift').value='08:00-18:00';
  }else if(type==='5x2'&&category!=='APOIO'){
    $('scheduleType').value='12x36';
  }
}
function resetScheduleForm(){
  $('scheduleProfileId').value='';
  $('scheduleUser').value='';
  $('scheduleName').value='';
  $('scheduleName').disabled=false;
  $('scheduleCategory').value='TECNICO';
  $('scheduleType').value='12x36';
  $('scheduleShift').value='05:00-17:00';
  $('scheduleAnchor').value=new Date().toISOString().slice(0,10);
  $('scheduleEntry').value='';
  $('scheduleLines').value='';
  $('scheduleSupervision').value='';
  $('scheduleSave').textContent='Adicionar à escala';
  $('scheduleCancelEdit').classList.add('hidden');
}
function editProfile(id){
  const p=profilesCache.find(x=>x.profile_id===id);
  if(!p) return;
  $('scheduleProfileId').value=p.profile_id;
  $('scheduleUser').value=p.user_id||'';
  $('scheduleName').value=p.name||'';
  $('scheduleCategory').value=p.category||'TECNICO';
  $('scheduleType').value=p.schedule_type||'12x36';
  $('scheduleShift').value=p.shift;
  $('scheduleAnchor').value=p.anchor_date||new Date().toISOString().slice(0,10);
  $('scheduleEntry').value=p.entry||'';
  $('scheduleLines').value=(p.lines||[]).join(', ');
  $('scheduleSupervision').value=p.supervision||'';
  $('scheduleSave').textContent='Salvar alterações';
  $('scheduleCancelEdit').classList.remove('hidden');
  $('scheduleForm').scrollIntoView({behavior:'smooth',block:'center'});
}
async function removeProfile(id){
  const p=profilesCache.find(x=>x.profile_id===id);
  if(!p||!confirm(`Remover ${p.name} da escala operacional? O usuário do sistema e o histórico NÃO serão excluídos.`)) return;
  const r=await fetch(`/api/equipes/perfis/${id}`,{method:'DELETE'});
  const j=await r.json().catch(()=>({ok:false}));
  if(!r.ok||!j.ok){alert(j.error||'Não foi possível remover.');return;}
  await refreshAll();
}
async function saveScheduleForm(e){
  e.preventDefault();
  const id=Number($('scheduleProfileId').value)||null;
  const payload={
    user_id:$('scheduleUser').value||null,
    name:$('scheduleName').value.trim(),
    category:$('scheduleCategory').value,
    schedule_type:$('scheduleType').value,
    shift:$('scheduleShift').value,
    anchor_date:$('scheduleAnchor').value,
    entry:$('scheduleEntry').value.trim(),
    lines:$('scheduleLines').value,
    supervision:$('scheduleSupervision').value.trim()
  };
  const r=await fetch(id?`/api/equipes/perfis/${id}`:'/api/equipes/perfis',{
    method:id?'PUT':'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify(payload)
  });
  const j=await r.json().catch(()=>({ok:false}));
  if(!r.ok||!j.ok){alert(j.error||'Não foi possível salvar a escala.');return;}
  resetScheduleForm();
  await refreshAll();
}
function exportScale(){
  const params=new URLSearchParams({
    start:$('calendarStart').value,
    days:$('calendarDays').value
  });
  if($('calendarCategory').value) params.set('category',$('calendarCategory').value);
  window.location.href=`/api/equipes/export/excel?${params.toString()}`;
}

async function enterMapFullscreen(){
  createTeamMap();
  const wrap=$('teamMapWrap');
  try{
    if(wrap.requestFullscreen) await wrap.requestFullscreen();
    else wrap.classList.add('teamMapFullscreenFallback');
  }catch(_e){
    wrap.classList.add('teamMapFullscreenFallback');
  }
  rebuildMapIfNeeded();
}
async function exitMapFullscreen(){
  const wrap=$('teamMapWrap');
  if(document.fullscreenElement) await document.exitFullscreen();
  wrap.classList.remove('teamMapFullscreenFallback');
  rebuildMapIfNeeded();
}
function syncFullscreenButtons(){
  const on=!!document.fullscreenElement||$('teamMapWrap').classList.contains('teamMapFullscreenFallback');
  $('teamMapExit').style.display=on?'block':'none';
  $('teamMapFull').textContent=on?'Sair da tela cheia':'Expandir mapa';
  rebuildMapIfNeeded();
}
document.addEventListener('fullscreenchange',syncFullscreenButtons);

async function refreshAll(){
  await Promise.allSettled([loadTeams(),loadCalendar(),loadProfiles()]);
}

$('refreshTeams').addEventListener('click',refreshAll);
$('exportScale').addEventListener('click',exportScale);
$('reloadCalendar').addEventListener('click',()=>loadCalendar().catch(console.error));
$('calendarCategory').addEventListener('change',()=>loadCalendar().catch(console.error));

$('toggleTeamMap').addEventListener('click',()=>{
  const wrap=$('teamMapWrap');
  const collapsed=wrap.classList.toggle('teamMapCollapsed');
  $('toggleTeamMap').textContent=collapsed?'Mostrar mapa':'Ocultar mapa';
  if(!collapsed) rebuildMapIfNeeded();
});
$('teamMapFull').addEventListener('click',()=>{
  if(document.fullscreenElement||$('teamMapWrap').classList.contains('teamMapFullscreenFallback')) exitMapFullscreen();
  else enterMapFullscreen();
});
$('teamMapExit').addEventListener('click',exitMapFullscreen);

if($('openScheduleAdmin')){
  $('openScheduleAdmin').addEventListener('click',()=>{
    $('scheduleAdminModal').classList.remove('hidden');
    loadProfiles().catch(err=>alert(err.message));
  });
  $('closeScheduleAdmin').addEventListener('click',()=>$('scheduleAdminModal').classList.add('hidden'));
  $('scheduleCancelEdit').addEventListener('click',resetScheduleForm);
  $('scheduleForm').addEventListener('submit',saveScheduleForm);
  $('scheduleSearch').addEventListener('input',renderProfiles);
  $('scheduleCategory').addEventListener('change',syncScheduleDefaults);
  $('scheduleType').addEventListener('change',()=>{
    if($('scheduleType').value==='5x2') $('scheduleShift').value='08:00-18:00';
  });
  $('scheduleUser').addEventListener('change',()=>{
    const u=usersCache.find(x=>String(x.id)===$('scheduleUser').value);
    if(u) $('scheduleName').value=u.name;
  });
}

const today=new Date();
$('calendarStart').value=today.toISOString().slice(0,10);
resetScheduleForm();
refreshAll();
setInterval(loadTeams,120000);
