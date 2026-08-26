window.AUTOPASS_TEAMS_VERSION="teams-v39-7-3";

console.log('AUTOPASS Central Operacional V26 carregada');

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
  v391SetupTeamMap();

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
function photoUrl(t){
  if(!t?.photo_url) return '';
  const sep=String(t.photo_url).includes('?')?'&':'?';
  return `${t.photo_url}${sep}v=${encodeURIComponent(t.photo_version||t.captured_at||Date.now())}`;
}
function avatarHtml(t){
  const cls=freshnessClass(t.freshness);
  const url=photoUrl(t);
  if(url){
    return `<div class="avatarRing ${cls}"><img class="teamCardAvatarPhoto" src="${esc(url)}" alt="${esc(t.name)}" loading="lazy" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'"><div class="avatarFallback" style="display:none">${esc(initials(t.name))}</div></div>`;
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
  const url=photoUrl(t);
  const photo=url
    ? `<img class="teamMapAvatarPhoto" src="${esc(url)}" alt="${esc(t.name)}" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'"><span class="teamMapAvatarInitials" style="display:none">${esc(initials(t.name))}</span>`
    : `<span class="teamMapAvatarInitials">${esc(initials(t.name))}</span>`;
  return L.divIcon({
    className:'teamAvatarMarker',
    html:`<div class="teamMapAvatar ${cls} ${categoryClass(t.category)}">${photo}</div>`,
    iconSize:L.point(52,52), iconAnchor:L.point(26,26), popupAnchor:L.point(0,-28)
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
  markers.forEach(m=>{try{(v391TechLayer||teamMap).removeLayer(m)}catch(_e){}});
  markers=[];

  $('teamCards').innerHTML='';
  if($('todayTeamTable')) $('todayTeamTable').innerHTML='';
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
          <span class="categoryBadge ${categoryClass(t.category)}">${esc(t.job_title||t.category)}</span>
        </div>
        <small><b>${esc(t.schedule_type)}</b> · ${esc(t.shift||'—')} · entrada ${esc(t.entry||'—')}</small>
        ${t.lines?.length?`<small>Linhas ${esc(t.lines.join(' / '))}</small>`:''}
        ${t.supervision?`<small>${esc(t.supervision)}</small>`:''}
        <span class="lastPosition">${esc(freshnessText(t))}</span>
        <span class="linkBadge ${t.linked?'linked':'unlinked'}">${t.linked?'Usuário vinculado':'Sem vínculo com Usuários'}</span>
      </div>`;
    $('teamCards').appendChild(card);
    if($('todayTeamTable')){ const tr=document.createElement('tr'); tr.innerHTML=`<td><b>${esc(t.name)}</b></td><td>${esc(t.job_title||t.category)}</td><td>${esc(t.schedule_type||'—')}</td><td>${esc(t.shift||'—')}</td><td>${esc(t.entry||'—')}</td><td>${esc((t.lines||[]).join(' / ')||'—')}</td><td>${esc(t.operation_status||t.freshness||'SEM SINAL')}</td><td>${esc(t.current_location||'—')} · ${esc(freshnessText(t))}</td>`; $('todayTeamTable').appendChild(tr); }

    if(t.latitude!=null&&t.longitude!=null){
      const m=L.marker([Number(t.latitude),Number(t.longitude)],{icon:markerIcon(t)})
        .addTo(v391TechLayer||teamMap)
        .bindPopup(`
          <div class="teamMapPopup">
            <b>${esc(t.name)}</b><br>
            ${esc(t.category)} · ${esc(t.shift||'')}<br>
            Entrada: ${esc(t.entry||'—')}<br>
            ${t.accuracy!=null?`Precisão GPS: ${Math.round(Number(t.accuracy))} m<br>`:''}
            <b>Localidade/estação:</b> ${esc(t.current_location||'—')}${t.nearest_station?.distance_m!=null?` · ${esc(t.nearest_station.relation)} · ${Number(t.nearest_station.distance_m).toLocaleString('pt-BR')} m`:''}<br>
            <b>Status:</b> ${esc(t.operation_status||'—')}<br>
            Login: ${esc(t.first_login||'—')}${t.late_minutes?` · atraso ${t.late_minutes} min`:''}<br>
            GPS hoje: ${Number(t.gps_points_today||0).toLocaleString('pt-BR')} posição(ões)<br>
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
  if($('calendarCategory').value) params.set('cargo',$('calendarCategory').value);

  const r=await fetch(`/api/equipes/calendario?${params.toString()}`,{cache:'no-store',headers:{'Accept':'application/json'}});
  const contentType=String(r.headers.get('content-type')||'');
  let d;
  if(contentType.includes('application/json')) d=await r.json();
  else {
    const raw=await r.text();
    throw new Error(`Servidor retornou ${r.status} em vez de JSON${raw?': '+raw.replace(/<[^>]+>/g,' ').replace(/\s+/g,' ').trim().slice(0,160):''}`);
  }
  if(!r.ok||!d.ok) throw new Error(d.error||'Falha ao carregar escala.');
  const requestedDays=Number($('calendarDays').value||14);
  if((d.dates||[]).length!==requestedDays) throw new Error(`Período retornado inválido: esperado ${requestedDays}, recebido ${(d.dates||[]).length}.`);

  if($('calendarRangeSummary')){
    const first=d.dates?.[0], last=d.dates?.[d.dates.length-1];
    $('calendarRangeSummary').innerHTML=`<b>Exibindo ${d.dates.length} dia(s)</b> · ${first?fmtDate(first):'—'} a ${last?fmtDate(last):'—'} · ${(d.members||[]).length} integrante(s)`;
  }
  if($('calendarTable')) $('calendarTable').style.minWidth=`${Math.max(900,520+(d.dates?.length||0)*92)}px`;
  $('scaleHead').innerHTML=`
    <tr>
      <th class="stickyTechCol">Técnico</th>
      <th>Turno</th>
      <th>Entrada</th>
      ${d.dates.map(x=>`<th><b>${weekday(x)}</b><small>${fmtDate(x)}</small></th>`).join('')}
    </tr>`;

  $('scaleBody').innerHTML=(d.members||[]).map(t=>`
    <tr class="scale-${categoryClass(t.category)}">
      <td class="stickyTechCol">
        <b>${esc(t.name)}</b>
        <small>${t.linked?'✓ '+esc(t.linked_user_name):'Não vinculado'}${t.job_title?' · '+esc(t.job_title):''}</small>
      </td>
      <td>${esc(t.shift)}</td>
      <td>${esc(t.entry||'—')}</td>
      ${t.days.map(day=>`
        <td class="${day.scheduled?'scaleWork':'scaleOff'}">
          ${day.status_override?esc(String(day.status_override).replaceAll('_',' ')):(day.scheduled?esc(t.shift.replaceAll(':00','')):'Folga')}
        </td>`).join('')}
    </tr>`).join('');  if($('calendarTableWrap')) $('calendarTableWrap').scrollLeft=0;
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
  if($('calendarCategory').value) params.set('cargo',$('calendarCategory').value);
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

function refreshCargoFilter(){
  const sel=$('calendarCategory'); if(!sel) return;
  const keep=sel.value;
  const cargos=[...new Set(profilesCache.map(p=>String(p.job_title||'').trim()).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'pt-BR'));
  sel.innerHTML='<option value="">Todos os cargos</option>'+cargos.map(c=>`<option value="${esc(c)}">${esc(c)}</option>`).join('');
  if(cargos.includes(keep)) sel.value=keep;
}
async function refreshAll(){
  await Promise.allSettled([loadTeams(),loadCalendar(),loadProfiles()]);
}

$('refreshTeams').addEventListener('click',refreshAll);
$('exportScale').addEventListener('click',exportScale);
const reloadCalendarVisible=()=>{ if($('calendarRangeSummary')) $('calendarRangeSummary').textContent='Atualizando período...'; loadCalendar().catch(err=>{console.error(err); if($('calendarRangeSummary')) $('calendarRangeSummary').innerHTML=`<b>Erro:</b> ${esc(err.message)}`;}); };
$('reloadCalendar').addEventListener('click',reloadCalendarVisible);
$('calendarCategory').addEventListener('change',reloadCalendarVisible);
$('calendarDays').addEventListener('change',reloadCalendarVisible);
$('calendarStart').addEventListener('change',reloadCalendarVisible);

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


// V26 — seções operacionais sob demanda para reduzir poluição visual.
function bindTeamCollapsible(buttonId, contentId){
  const btn=$(buttonId), content=$(contentId); if(!btn||!content) return;
  btn.addEventListener('click',()=>{
    const opening=content.classList.contains('hidden');
    content.classList.toggle('hidden',!opening);
    btn.setAttribute('aria-expanded',opening?'true':'false');
    const span=btn.querySelector('span'); if(span) span.textContent=opening?'−':'＋';
  });
}
bindTeamCollapsible('toggleTodayOperational','todayOperationalContent');
bindTeamCollapsible('toggleExpectedTeam','expectedTeamContent');

// V39.6 — autocomplete de colaborador ligado ao cadastro de usuários.
async function v396LoadCollaborators(){try{const r=await fetch('/api/equipes/colaboradores',{cache:'no-store'});const d=await r.json();const dl=$('v396Collaborators');if(dl&&d.ok)dl.innerHTML=(d.users||[]).map(u=>`<option value="${esc(u.name)}"></option>`).join('')}catch(e){console.warn('autocomplete colaboradores',e)}}
v396LoadCollaborators();

// V38 — malha metroferroviária também no mapa de equipes
async function v38DrawRailNetwork(){try{const locs=await fetch('/api/locations',{cache:'no-store'}).then(r=>r.json());const colors={'1':'#005ca9','2':'#008c5a','3':'#ee3338','4':'#f4b800','5':'#7651a2','6':'#f28c00','7':'#9b0058','8':'#8b8b8b','9':'#008c7d','10':'#00a5b5','11':'#e94b24','12':'#1455a0','13':'#008b68','15':'#9a9a9a','17':'#8a7627'};const groups={};(locs||[]).forEach(x=>{if(x.reference_latitude==null||x.reference_longitude==null)return;const m=String(x.line||'').match(/(?:^|\D)(1[0-7]|[1-9])(?:\D|$)/);if(!m)return;(groups[m[1]]??=[]).push(x)});Object.entries(groups).forEach(([n,a])=>{if(a.length<2)return;const pts=a.map(x=>[Number(x.reference_latitude),Number(x.reference_longitude)]);L.polyline(pts,{color:colors[n]||'#64748b',weight:5,opacity:.85}).addTo(teamMap)})}catch(e){console.warn('V38 trilhos equipes',e)}}
function v38ApplyTeamFilter(){const q=String($('v38TeamSearch')?.value||'').toLowerCase(),cat=$('v38TeamCategory')?.value||'',gps=$('v38TeamGps')?.value||'';document.querySelectorAll('#todayTeamTable tr').forEach(tr=>{const txt=tr.textContent.toLowerCase();tr.style.display=(!q||txt.includes(q))&&(!cat||txt.includes(cat.toLowerCase()))&&(!gps||txt.includes(gps.toLowerCase()))?'':'none'});document.querySelectorAll('#teamCards > *').forEach(el=>{const txt=el.textContent.toLowerCase();el.style.display=(!q||txt.includes(q))&&(!cat||txt.includes(cat.toLowerCase()))&&(!gps||txt.includes(gps.toLowerCase()))?'':'none'})}
['v38TeamSearch','v38TeamCategory','v38TeamGps'].forEach(id=>$(id)?.addEventListener(id==='v38TeamSearch'?'input':'change',v38ApplyTeamFilter));$('v38ClearTeam')?.addEventListener('click',()=>{['v38TeamSearch','v38TeamCategory','v38TeamGps'].forEach(id=>$(id).value='');v38ApplyTeamFilter()});


// V39.1 substitui os controles V38.1 por controles nativos Leaflet.

// V39.1 — mapa de Equipes alinhado ao Dashboard: legenda + camadas clicáveis + menor uso de memória.
let v391RailLines=null,v391Stations=null,v391StationNames=null,v391TechLayer=null,v391Accuracy=null,v391LayerControl=null,v391Legend=null;
const V391_COLORS={'1':'#0054A6','2':'#008C5A','3':'#E6332A','4':'#F4C300','5':'#7A3E9D','6':'#F28C18','7':'#A60055','8':'#8C8C8C','9':'#00A092','10':'#00A5B5','11':'#F04B23','12':'#164F9C','13':'#009B62','15':'#9B9DA0','17':'#9A7A24'};
const V391_NAMES={'1':'Azul','2':'Verde','3':'Vermelha','4':'Amarela','5':'Lilás','6':'Laranja','7':'Rubi','8':'Diamante','9':'Esmeralda','10':'Turquesa','11':'Coral','12':'Safira','13':'Jade','15':'Prata','17':'Ouro'};
const V391_FALLBACK={
'1':[[-23.4799,-46.6024],[-23.4923,-46.6072],[-23.5091,-46.6245],[-23.5255,-46.6407],[-23.5441,-46.6358],[-23.5688,-46.6399],[-23.5983,-46.6369],[-23.6261,-46.6401],[-23.6592,-46.6388]],
'2':[[-23.5895,-46.6350],[-23.5812,-46.6458],[-23.5703,-46.6585],[-23.5632,-46.6548],[-23.5581,-46.6607],[-23.5508,-46.6719],[-23.5451,-46.6904],[-23.5444,-46.7066]],
'3':[[-23.5423,-46.4714],[-23.5364,-46.4903],[-23.5281,-46.5180],[-23.5262,-46.5558],[-23.5292,-46.5747],[-23.5356,-46.6072],[-23.5421,-46.6177],[-23.5453,-46.6388],[-23.5495,-46.6535],[-23.5487,-46.6875]],
'4':[[-23.5362,-46.6335],[-23.5441,-46.6422],[-23.5489,-46.6520],[-23.5553,-46.6620],[-23.5608,-46.6719],[-23.5662,-46.6840],[-23.5673,-46.6930],[-23.5669,-46.7012],[-23.5718,-46.7080],[-23.5864,-46.7230],[-23.5944,-46.7330]],
'5':[[-23.6491,-46.7588],[-23.6401,-46.7503],[-23.6262,-46.7418],[-23.6125,-46.7228],[-23.5977,-46.7191],[-23.5858,-46.7061],[-23.5730,-46.6936],[-23.5673,-46.6828],[-23.5663,-46.6520]],
'6':[[-23.5450,-46.6320],[-23.5480,-46.6200],[-23.5520,-46.6030],[-23.5560,-46.5850],[-23.5580,-46.5660],[-23.5600,-46.5480]],
'7':[[-23.5454,-46.6380],[-23.5327,-46.6550],[-23.5204,-46.7020],[-23.5110,-46.7480],[-23.5030,-46.7890],[-23.4940,-46.8330],[-23.4860,-46.8760],[-23.4690,-46.9400],[-23.4210,-46.9650],[-23.3020,-46.9870],[-23.1850,-46.8840]],
'8':[[-23.5250,-46.6680],[-23.5320,-46.7010],[-23.5420,-46.7280],[-23.5550,-46.7560],[-23.5700,-46.7870],[-23.5890,-46.8200],[-23.6040,-46.8400],[-23.6370,-46.8660],[-23.6840,-46.8930],[-23.7160,-46.9010]],
'9':[[-23.7630,-46.7100],[-23.7220,-46.7000],[-23.6860,-46.6930],[-23.6480,-46.6910],[-23.6180,-46.6900],[-23.5950,-46.6890],[-23.5750,-46.6900],[-23.5550,-46.6870],[-23.5360,-46.6810],[-23.5190,-46.6650]],
'10':[[-23.5450,-46.6380],[-23.5310,-46.6150],[-23.5220,-46.5920],[-23.5150,-46.5730],[-23.5070,-46.5480],[-23.5000,-46.5200],[-23.4950,-46.5000],[-23.4820,-46.4760],[-23.4710,-46.4480]],
'11':[[-23.5450,-46.6380],[-23.5430,-46.6160],[-23.5400,-46.5960],[-23.5370,-46.5760],[-23.5320,-46.5540],[-23.5250,-46.5300],[-23.5180,-46.5080],[-23.5070,-46.4770],[-23.4980,-46.4490]],
'12':[[-23.5450,-46.6380],[-23.5290,-46.6490],[-23.5120,-46.6640],[-23.4920,-46.6800],[-23.4740,-46.6980],[-23.4560,-46.7160],[-23.4370,-46.7290]],
'13':[[-23.4850,-46.4920],[-23.4630,-46.4930],[-23.4420,-46.5000],[-23.4230,-46.5070],[-23.4040,-46.5200],[-23.3830,-46.5360],[-23.3630,-46.5530]],
'15':[[-23.6460,-46.6420],[-23.6320,-46.6410],[-23.6170,-46.6400],[-23.6040,-46.6390],[-23.5900,-46.6380],[-23.5760,-46.6360]],
'17':[[-23.6217,-46.7012],[-23.6222,-46.6947],[-23.6209,-46.6878],[-23.6201,-46.6800],[-23.6210,-46.6732],[-23.6241,-46.6670],[-23.6288,-46.6633],[-23.6328,-46.6603]]
}
function v391LineNo(v){const t=String(v||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toUpperCase();const m=t.match(/(?:^|\D)(1[0-7]|[1-9])(?:\D|$)/);if(m)return String(Number(m[1]));const a={AZUL:'1',VERDE:'2',VERMELHA:'3',AMARELA:'4',LILAS:'5',LARANJA:'6',RUBI:'7',DIAMANTE:'8',ESMERALDA:'9',TURQUESA:'10',CORAL:'11',SAFIRA:'12',JADE:'13',PRATA:'15',OURO:'17'};return Object.entries(a).find(([k])=>t.includes(k))?.[1]||''}
function v391Dist(a,b){const R=6371000,p=x=>x*Math.PI/180,dlat=p(+b.reference_latitude-+a.reference_latitude),dlon=p(+b.reference_longitude-+a.reference_longitude),x=Math.sin(dlat/2)**2+Math.cos(p(+a.reference_latitude))*Math.cos(p(+b.reference_latitude))*Math.sin(dlon/2)**2;return 2*R*Math.asin(Math.sqrt(x))}
function v391Sequence(a){if(a.length<3)return [...a];const pool=[...a], seq=[pool.shift()];while(pool.length){const last=seq[seq.length-1];let bi=0,bd=Infinity;pool.forEach((c,i)=>{const d=v391Dist(last,c);if(d<bd){bd=d;bi=i}});seq.push(pool.splice(bi,1)[0])}return seq}
async function v391BuildRails(){
  if(!teamMap||!v391RailLines)return;
  v391RailLines.clearLayers();v391Stations.clearLayers();v391StationNames.clearLayers();
  try{
    const r=await fetch('/api/equipes/rail-network',{cache:'no-store'}); if(!r.ok)throw new Error('HTTP '+r.status); const locs=await r.json(); const groups={};
    (locs||[]).forEach(x=>{if(x.reference_latitude==null||x.reference_longitude==null)return;const n=v391LineNo(x.line);if(!n)return;(groups[n]??=[]).push(x);const pt=[+x.reference_latitude,+x.reference_longitude];L.circleMarker(pt,{pane:'railStationsPane',radius:5,color:'#fff',weight:2,fillColor:V391_COLORS[n]||'#64748b',fillOpacity:1}).bindTooltip(String(x.location||''),{direction:'top'}).addTo(v391Stations);L.marker(pt,{interactive:false,icon:L.divIcon({className:'stationLabelIcon',html:`<span>${esc(x.location||'')}</span>`,iconSize:null})}).addTo(v391StationNames)});
    Object.keys(V391_FALLBACK).forEach(n=>{if(!groups[n])groups[n]=[]});
    Object.entries(groups).forEach(([n,arr])=>{const seq=v391Sequence(arr);const pts=seq.length>=2?seq.map(x=>[+x.reference_latitude,+x.reference_longitude]):(V391_FALLBACK[n]||[]);if(pts.length<2)return;L.polyline(pts,{pane:'railLinesPane',color:'#fff',weight:11,opacity:.96,interactive:false}).addTo(v391RailLines);L.polyline(pts,{pane:'railLinesPane',color:V391_COLORS[n]||'#64748b',weight:6,opacity:1}).bindPopup(`<b>Linha ${n} — ${V391_NAMES[n]||''}</b>`).addTo(v391RailLines)});
  }catch(e){console.warn('V39.1 mapa equipes',e)}
}
function v391SetupTeamMap(){
  if(!teamMap||v391RailLines)return;
  if(!teamMap.getPane('railLinesPane'))teamMap.createPane('railLinesPane');teamMap.getPane('railLinesPane').style.zIndex=460;if(!teamMap.getPane('railStationsPane'))teamMap.createPane('railStationsPane');teamMap.getPane('railStationsPane').style.zIndex=470;v391RailLines=L.layerGroup().addTo(teamMap);v391Stations=L.layerGroup().addTo(teamMap);v391StationNames=L.layerGroup();v391TechLayer=L.layerGroup().addTo(teamMap);v391Accuracy=L.layerGroup();
  v391LayerControl=L.control.layers(null,{'Linhas':v391RailLines,'Estações':v391Stations,'Nomes das estações':v391StationNames,'Técnicos (GPS)':v391TechLayer,'Precisão GPS (auditoria)':v391Accuracy},{collapsed:false,position:'bottomright'}).addTo(teamMap);
  v391Legend=L.control({position:'topleft'});v391Legend.onAdd=()=>{const d=L.DomUtil.create('div','autopass-rail-legend');d.innerHTML='<h4>Linhas Metroferroviárias</h4>'+Object.keys(V391_COLORS).map(n=>`<div class="row"><span class="swatch" style="background:${V391_COLORS[n]}"></span><b>${n}</b><span>${V391_NAMES[n]}</span></div>`).join('');L.DomEvent.disableClickPropagation(d);L.DomEvent.disableScrollPropagation(d);return d};v391Legend.addTo(teamMap);
  v391BuildRails(); setTimeout(v391BuildRails,900);
}


// V39.6 — compatibilidade dos checkboxes visíveis com as camadas Leaflet.
function v396SyncRailChecks(){const map=teamMap;if(!map)return;[['teamShowLines',v391RailLines],['teamShowStations',v391Stations],['teamShowNames',v391StationNames],['teamShowTechs',v391TechLayer]].forEach(([id,layer])=>{const el=$(id);if(!el||!layer)return;const sync=()=>{if(el.checked&&!map.hasLayer(layer))map.addLayer(layer);if(!el.checked&&map.hasLayer(layer))map.removeLayer(layer)};el.addEventListener('change',sync);sync()});v391BuildRails()}
setTimeout(v396SyncRailChecks,500);
