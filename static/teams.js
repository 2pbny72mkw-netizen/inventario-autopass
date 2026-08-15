window.AUTOPASS_TEAMS_VERSION='teams-v5-2-1';
console.log('AUTOPASS Central de Equipes V5.2.1 carregada');

const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmtDate=s=>{
  if(!s) return '—';
  const [y,m,d]=String(s).split('-');
  return d&&m&&y?`${d}/${m}`:s;
};
const weekday=s=>{
  if(!s) return '';
  const d=new Date(`${s}T12:00:00`);
  return ['Dom','Seg','Ter','Qua','Qui','Sex','Sáb'][d.getDay()];
};

let teamMap=L.map('teamMap',{scrollWheelZoom:true}).setView([-23.5505,-46.6333],10);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{
  maxZoom:19,attribution:'&copy; OpenStreetMap contributors'
}).addTo(teamMap);

let markers=[];
let lastTeamData=null;
let profilesCache=[];
let usersCache=[];

function freshnessClass(value){
  return value==='ATUAL'?'current':
         value==='ATENÇÃO'?'attention':
         value==='ATRASADO'?'late':'noSignal';
}
function initials(name){
  return String(name||'?').trim().split(/\s+/).slice(0,2).map(x=>x[0]||'').join('').toUpperCase();
}
function avatarHtml(t){
  const cls=freshnessClass(t.freshness);
  if(t.photo_url){
    return `<div class="avatarRing ${cls}"><img src="${esc(t.photo_url)}" alt="${esc(t.name)}"></div>`;
  }
  return `<div class="avatarRing ${cls}"><div class="avatarFallback">${esc(initials(t.name))}</div></div>`;
}
function freshnessText(t){
  if(t.minutes_since==null) return 'Sem localização recebida';
  if(t.minutes_since===0) return 'Localização recebida agora';
  return `${t.minutes_since} min desde a última posição`;
}
function markerIcon(t){
  const cls=freshnessClass(t.freshness);
  const photo=t.photo_url
    ? `<img src="${esc(t.photo_url)}" alt="">`
    : `<span>${esc(initials(t.name))}</span>`;
  return L.divIcon({
    className:'',
    html:`<div class="teamMapAvatar ${cls}">${photo}</div>`,
    iconSize:[44,44],iconAnchor:[22,22]
  });
}
async function loadTeams(){
  try{
    const r=await fetch('/api/equipes/status',{cache:'no-store'});
    const d=await r.json();
    if(!r.ok||!d.ok) throw new Error(d.error||'Falha ao carregar equipes.');
    lastTeamData=d;

    $('teamDate').textContent=d.date||'—';
    $('teamClock').textContent=`${d.date||''} ${d.time||''}`.trim();
    $('kScheduled').textContent=d.scheduled||0;

    let current=0,attention=0,noSignal=0;
    markers.forEach(m=>teamMap.removeLayer(m));
    markers=[];

    $('teamCards').innerHTML='';
    for(const t of d.technicians||[]){
      if(t.freshness==='ATUAL') current++;
      else if(t.freshness==='ATENÇÃO'||t.freshness==='ATRASADO') attention++;
      else noSignal++;

      const card=document.createElement('article');
      card.className=`teamCard freshness-${freshnessClass(t.freshness)}`;
      card.innerHTML=`
        ${avatarHtml(t)}
        <div class="teamCardBody">
          <div class="teamNameRow"><b>${esc(t.name)}</b><span class="teamFreshness">${esc(t.freshness)}</span></div>
          <small>${esc(t.shift||'—')} · entrada ${esc(t.entry||'—')}</small>
          <small>Linhas ${esc((t.lines||[]).filter(Boolean).join(' / ')||'—')}</small>
          <small>${esc(t.supervision||'')}</small>
          <span class="lastPosition">${esc(freshnessText(t))}</span>
        </div>`;
      $('teamCards').appendChild(card);

      if(t.latitude!=null&&t.longitude!=null){
        const m=L.marker([Number(t.latitude),Number(t.longitude)],{icon:markerIcon(t)})
          .addTo(teamMap)
          .bindPopup(`<b>${esc(t.name)}</b><br>${esc(t.shift||'')}<br>${esc(freshnessText(t))}`);
        markers.push(m);
      }
    }

    $('kCurrent').textContent=current;
    $('kAttention').textContent=attention;
    $('kNoSignal').textContent=noSignal;

    $('supportCards').innerHTML=(d.support||[]).map(s=>`
      <article class="supportCard">
        <b>${esc(s.name||s.nome||'Apoio')}</b>
        <small>${esc(s.role||s.funcao||s.supervision||'')}</small>
      </article>`).join('')||'<span class="muted">Sem equipe de apoio cadastrada.</span>';

    if(markers.length){
      const bounds=L.featureGroup(markers).getBounds();
      if(bounds.isValid()) teamMap.fitBounds(bounds.pad(.15),{maxZoom:16});
    }
    invalidateTeamMap();
  }catch(err){
    console.error(err);
    $('teamCards').innerHTML=`<div class="alert">Não foi possível carregar a Central de Equipes: ${esc(err.message)}</div>`;
  }
}

function invalidateTeamMap(){
  [50,180,400].forEach(ms=>setTimeout(()=>teamMap.invalidateSize({pan:false}),ms));
}

/* Native Fullscreen API fixes the scattered Leaflet tiles seen in V5.1. */
async function enterMapFullscreen(){
  const wrap=$('teamMapWrap');
  try{
    if(wrap.requestFullscreen){
      await wrap.requestFullscreen();
    }else{
      wrap.classList.add('teamMapFullscreenFallback');
    }
  }catch(_e){
    wrap.classList.add('teamMapFullscreenFallback');
  }
  invalidateTeamMap();
}
async function exitMapFullscreen(){
  const wrap=$('teamMapWrap');
  if(document.fullscreenElement){
    await document.exitFullscreen();
  }
  wrap.classList.remove('teamMapFullscreenFallback');
  invalidateTeamMap();
}
function syncFullscreenButtons(){
  const on=!!document.fullscreenElement||$('teamMapWrap').classList.contains('teamMapFullscreenFallback');
  $('teamMapExit').style.display=on?'block':'none';
  $('teamMapFull').textContent=on?'Sair da tela cheia':'Expandir mapa';
  invalidateTeamMap();
}
document.addEventListener('fullscreenchange',syncFullscreenButtons);

async function loadCalendar(){
  const start=$('calendarStart').value;
  const days=$('calendarDays').value;
  const r=await fetch(`/api/equipes/calendario?start=${encodeURIComponent(start)}&days=${encodeURIComponent(days)}`,{cache:'no-store'});
  const d=await r.json();
  if(!r.ok||!d.ok) throw new Error(d.error||'Falha ao carregar escala.');

  $('scaleHead').innerHTML=`
    <tr>
      <th class="stickyTechCol">Técnico</th>
      <th>Turno</th>
      <th>Entrada</th>
      ${d.dates.map(x=>`<th><b>${weekday(x)}</b><small>${fmtDate(x)}</small></th>`).join('')}
    </tr>`;

  $('scaleBody').innerHTML=d.technicians.map(t=>`
    <tr>
      <td class="stickyTechCol"><b>${esc(t.name)}</b><small>${esc(t.supervision||'')}</small></td>
      <td>${esc(t.shift)}</td>
      <td>${esc(t.entry||'—')}</td>
      ${t.days.map(day=>`
        <td class="${day.scheduled?'scaleWork':'scaleOff'}">
          ${day.scheduled?esc(t.shift.replace(':00','').replace(':00','')):'Folga'}
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

  $('scheduleUser').innerHTML='<option value="">Nome manual</option>'+
    usersCache.map(u=>`<option value="${u.id}">${esc(u.name)} · ${esc(u.role)}</option>`).join('');
  renderProfiles();
}
function renderProfiles(){
  const q=String($('scheduleSearch')?.value||'').toUpperCase();
  const rows=profilesCache.filter(p=>!q||String(p.name).toUpperCase().includes(q));
  $('scheduleProfiles').innerHTML=rows.map(p=>`
    <article class="scheduleProfile ${p.active?'':'profileInactive'}">
      <div>
        <b>${esc(p.name)}</b>
        <small>${esc(p.shift)} · ${esc(p.entry||'—')} · linhas ${esc((p.lines||[]).join('/'))}</small>
        <small>Início ciclo: ${esc(p.anchor_date||'—')} · ${esc(p.supervision||'')}</small>
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
function resetScheduleForm(){
  $('scheduleProfileId').value='';
  $('scheduleUser').value='';
  $('scheduleUser').disabled=false;
  $('scheduleName').value='';
  $('scheduleName').disabled=false;
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
  $('scheduleUser').disabled=true;
  $('scheduleName').value=p.name||'';
  $('scheduleName').disabled=true;
  $('scheduleShift').value=p.shift;
  $('scheduleAnchor').value=p.anchor_date;
  $('scheduleEntry').value=p.entry||'';
  $('scheduleLines').value=(p.lines||[]).join(', ');
  $('scheduleSupervision').value=p.supervision||'';
  $('scheduleSave').textContent='Salvar alterações';
  $('scheduleCancelEdit').classList.remove('hidden');
  $('scheduleForm').scrollIntoView({behavior:'smooth',block:'center'});
}
async function removeProfile(id){
  const p=profilesCache.find(x=>x.profile_id===id);
  if(!p||!confirm(`Remover ${p.name} da escala operacional? O usuário do sistema não será excluído.`)) return;
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
async function refreshAll(){
  await Promise.allSettled([loadTeams(),loadCalendar(),loadProfiles()]);
}


$('toggleTeamMap').addEventListener('click',()=>{
  const wrap=$('teamMapWrap');
  const collapsed=wrap.classList.toggle('teamMapCollapsed');
  $('toggleTeamMap').textContent=collapsed?'Mostrar mapa':'Ocultar mapa';
  if(!collapsed) invalidateTeamMap();
});

$('refreshTeams').addEventListener('click',refreshAll);
$('teamMapFull').addEventListener('click',()=>{
  if(document.fullscreenElement||$('teamMapWrap').classList.contains('teamMapFullscreenFallback')) exitMapFullscreen();
  else enterMapFullscreen();
});
$('teamMapExit').addEventListener('click',exitMapFullscreen);
$('reloadCalendar').addEventListener('click',()=>loadCalendar().catch(console.error));

if($('openScheduleAdmin')){
  $('openScheduleAdmin').addEventListener('click',()=>{
    $('scheduleAdminModal').classList.remove('hidden');
    loadProfiles().catch(err=>alert(err.message));
  });
  $('closeScheduleAdmin').addEventListener('click',()=>$('scheduleAdminModal').classList.add('hidden'));
  $('scheduleCancelEdit').addEventListener('click',resetScheduleForm);
  $('scheduleForm').addEventListener('submit',saveScheduleForm);
  $('scheduleSearch').addEventListener('input',renderProfiles);
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
