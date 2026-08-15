window.AUTOPASS_TEAMS_VERSION='teams-v5-1';
console.log('AUTOPASS Central de Equipes V5.1 carregada');

const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

let teamMap=L.map('teamMap',{scrollWheelZoom:true}).setView([-23.5505,-46.6333],10);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{
  maxZoom:19, attribution:'&copy; OpenStreetMap contributors'
}).addTo(teamMap);

let markers=[];

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
    iconSize:[44,44], iconAnchor:[22,22]
  });
}
async function loadTeams(){
  try{
    const r=await fetch('/api/equipes/status',{cache:'no-store'});
    const d=await r.json();
    if(!r.ok || !d.ok) throw new Error(d.error||'Falha ao carregar equipes.');

    $('teamDate').textContent=d.date||'—';
    $('teamClock').textContent=`${d.date||''} ${d.time||''}`.trim();
    $('kScheduled').textContent=d.scheduled||0;

    let current=0, attention=0, noSignal=0;
    markers.forEach(m=>teamMap.removeLayer(m)); markers=[];

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

      if(t.latitude!=null && t.longitude!=null){
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
      </article>`).join('') || '<span class="muted">Sem equipe de apoio cadastrada.</span>';

    if(markers.length){
      teamMap.fitBounds(L.featureGroup(markers).getBounds().pad(.15),{maxZoom:16});
    }
    setTimeout(()=>teamMap.invalidateSize(),80);
  }catch(err){
    console.error(err);
    $('teamCards').innerHTML=`<div class="alert">Não foi possível carregar a Central de Equipes: ${esc(err.message)}</div>`;
  }
}

$('refreshTeams').addEventListener('click',loadTeams);
$('teamMapFull').addEventListener('click',()=>{
  const mapEl=$('teamMap');
  const on=!mapEl.classList.contains('teamMapFullscreen');
  mapEl.classList.toggle('teamMapFullscreen',on);
  document.body.classList.toggle('mapFullscreenOpen',on);
  $('teamMapFull').textContent=on?'Sair da tela cheia':'Expandir mapa';
  setTimeout(()=>teamMap.invalidateSize(),100);
});
document.addEventListener('keydown',e=>{
  if(e.key==='Escape' && $('teamMap').classList.contains('teamMapFullscreen')){
    $('teamMapFull').click();
  }
});

loadTeams();
setInterval(loadTeams,120000);
