let locations=[];
const $=id=>document.getElementById(id);
const uniq=a=>[...new Set(a)].sort((x,y)=>x.localeCompare(y,'pt-BR'));
function st(s){return `<span class="status s${s.replaceAll(' ','')}">${s}</span>`}
function fmt(n){return new Intl.NumberFormat('pt-BR').format(Number(n||0))}
function esc(v){return String(v??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'","&#039;")}

function hasReference(loc){
  if(!loc) return false;

  const lat = Number(loc.reference_latitude);
  const lon = Number(loc.reference_longitude);

  if(
    loc.reference_latitude === null ||
    loc.reference_latitude === undefined ||
    loc.reference_latitude === '' ||
    loc.reference_longitude === null ||
    loc.reference_longitude === undefined ||
    loc.reference_longitude === ''
  ){
    return false;
  }

  if(!Number.isFinite(lat) || !Number.isFinite(lon)){
    return false;
  }

  // 0,0 não é uma referência válida para nossas localidades.
  if(lat === 0 && lon === 0){
    return false;
  }

  return true;
}

let gpsMap=null;
let gpsPointLayer=null;
let gpsAccuracyLayer=null;
let referenceLayer=null;
let referenceMode=false;
let referenceTempMarker=null;

function haversineMeters(lat1,lon1,lat2,lon2){
  const R=6371000;
  const toRad=v=>v*Math.PI/180;
  const p1=toRad(lat1), p2=toRad(lat2);
  const dP=toRad(lat2-lat1), dL=toRad(lon2-lon1);
  const a=Math.sin(dP/2)**2 + Math.cos(p1)*Math.cos(p2)*Math.sin(dL/2)**2;
  return 2*R*Math.asin(Math.sqrt(a));
}

function gpsPointColor(accuracy){
  const a=Number(accuracy);
  if(!Number.isFinite(a)) return '#64748b';
  if(a<=30) return '#16824b';
  if(a<=80) return '#c47a12';
  return '#c23b32';
}

function ensureGpsMap(){
  if(gpsMap || !window.L || !$('gpsMap')) return gpsMap;

  gpsMap=L.map('gpsMap',{scrollWheelZoom:true}).setView([-23.5505,-46.6333],11);

  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{
    maxZoom:19,
    attribution:'&copy; OpenStreetMap contributors'
  }).addTo(gpsMap);

  gpsAccuracyLayer=L.layerGroup().addTo(gpsMap);
  referenceLayer=L.layerGroup().addTo(gpsMap);
  gpsPointLayer=L.layerGroup().addTo(gpsMap);

  gpsMap.on('click', async e=>{
    if(!referenceMode) return;
    const locationId=Number($('mapLocationSelect').value);
    if(!locationId) return;

    if(referenceTempMarker) referenceTempMarker.remove();
    referenceTempMarker=L.marker(e.latlng).addTo(gpsMap);

    if(!confirm(`Salvar este ponto como referência da localidade?\n${e.latlng.lat.toFixed(6)}, ${e.latlng.lng.toFixed(6)}`)){
      referenceTempMarker.remove(); referenceTempMarker=null; return;
    }

    const r=await fetch(`/api/location/${locationId}/reference-position`,{
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({latitude:e.latlng.lat, longitude:e.latlng.lng, source:'Gestor - mapa'})
    });
    const j=await r.json().catch(()=>({ok:false,error:'Erro no servidor.'}));
    if(!r.ok){ alert(j.error||'Não foi possível salvar a referência.'); return; }

    referenceMode=false;
    $('setReferenceBtn').textContent='Definir referência no mapa';
    $('referenceStatus').textContent='Referência salva.';
    if(referenceTempMarker){ referenceTempMarker.remove(); referenceTempMarker=null; }
    await loadAll();
  });

  setTimeout(()=>gpsMap.invalidateSize(),100);
  return gpsMap;
}

function renderGpsMap(items){
  const map=ensureGpsMap();
  if(!map) return;

  gpsPointLayer.clearLayers();
  gpsAccuracyLayer.clearLayers();
  referenceLayer.clearLayers();

locations.filter(x=>hasReference(x)).forEach(x=>{
    
    const lat=Number(x.reference_latitude), lon=Number(x.reference_longitude);
    const ref=L.marker([lat,lon],{title:`Referência: ${x.location}`}).addTo(referenceLayer);
    ref.bindPopup(`<div style="min-width:210px"><b>◆ Referência da localidade</b><br><b>${esc(x.location)}</b><br><small>${esc(x.company)} · ${esc(x.line)}</small><br><small>Fonte: ${esc(x.reference_source||'não informada')}</small></div>`);
  });

  const valid=(items||[]).filter(x=>
    Number.isFinite(Number(x.latitude)) &&
    Number.isFinite(Number(x.longitude))
  );

  if(!valid.length){
    map.setView([-23.5505,-46.6333],11);
    return;
  }

  const bounds=[];

  valid.forEach(x=>{
    const lat=Number(x.latitude), lon=Number(x.longitude);
    const accuracy=Number(x.gps_accuracy);
    const color=gpsPointColor(accuracy);
    const when=new Date(x.gps_captured_at||x.created_at).toLocaleString('pt-BR');
    const accuracyText=Number.isFinite(accuracy)?`${Math.round(accuracy)} m`:'não informada';
    const loc=locations.find(l=>Number(l.id)===Number(x.location_id));
    let distanceText='Referência da localidade ainda não cadastrada';
    if(hasReference(loc)){
      const d=haversineMeters(lat,lon,Number(loc.reference_latitude),Number(loc.reference_longitude));
      distanceText=`Distância até referência: ${Math.round(d)} m`;
    }

    if(Number.isFinite(accuracy) && accuracy>0){
      L.circle([lat,lon],{
        radius:accuracy,
        color,
        weight:1,
        opacity:.55,
        fillColor:color,
        fillOpacity:.08
      }).addTo(gpsAccuracyLayer);
    }

    const marker=L.circleMarker([lat,lon],{
      radius:8,
      color:'#ffffff',
      weight:2,
      fillColor:color,
      fillOpacity:1
    }).addTo(gpsPointLayer);

    marker.bindPopup(`
      <div style="min-width:220px">
        <b>${esc(x.location_name||'Localidade')}</b><br>
        <small>${esc(x.company||'')} · ${esc(x.line||'')}</small>
        <hr style="border:0;border-top:1px solid #e5e7eb;margin:8px 0">
        <b>${esc(x.equipment_type||'Equipamento')} ${esc(x.asset_identifier||'')}</b><br>
        Técnico: ${esc(x.technician||'—')}<br>
        Coleta: ${esc(when)}<br>
        Precisão GPS: <b>${esc(accuracyText)}</b><br>
        ${esc(distanceText)}<br>
        <small>${lat.toFixed(5)}, ${lon.toFixed(5)}</small>
      </div>
    `);

    bounds.push([lat,lon]);
  });

  if(bounds.length===1){
    map.setView(bounds[0],16);
  }else{
    map.fitBounds(bounds,{padding:[35,35],maxZoom:16});
  }

  setTimeout(()=>map.invalidateSize(),50);
}

async function loadAll(){
  const [d,l,g]=await Promise.all([
    fetch('/api/dashboard').then(r=>r.json()),
    fetch('/api/locations').then(r=>r.json()),
    fetch('/api/gps/recent?limit=100').then(r=>r.json())
  ]);
  locations=l;
  renderMapLocationSelect();

  $('total').textContent=fmt(d.totals.total);
  $('pending').textContent=fmt(d.totals.pending);
  $('progress').textContent=fmt(d.totals.progress);
  $('completed').textContent=fmt(d.totals.completed);
  $('expected').textContent=fmt(d.totals.expected);
  $('inventoried').textContent=fmt(d.inventory.inventoried);
  $('inoperative').textContent=fmt(d.inventory.inoperative);
  $('divergences').textContent=fmt(d.inventory.divergences);

  const total=Number(d.totals.total||0), done=Number(d.totals.completed||0),
        prog=Number(d.totals.progress||0), pend=Number(d.totals.pending||0),
        expected=Number(d.totals.expected||0), inventoried=Number(d.inventory.inventoried||0);
  const pct=total?Math.round(done/total*100):0;
  const coverage=expected?Math.min(100,Math.round(inventoried/expected*100)):0;

  $('overallPct').textContent=pct+'%';
  $('donutText').textContent=pct+'%';
  $('legendDone').textContent=done;
  $('legendProgress').textContent=prog;
  $('legendPending').textContent=pend;
  $('openLocations').textContent=pend+prog;
  $('assetCoverage').textContent=coverage+'%';

  const dDone=total?(done/total*360):0;
  const dProg=total?(prog/total*360):0;
  $('donut').style.background=`conic-gradient(
    var(--green) 0deg ${dDone}deg,
    var(--amber) ${dDone}deg ${dDone+dProg}deg,
    #e1e6ed ${dDone+dProg}deg 360deg
  )`;

  if(!$('fc').dataset.loaded){
    $('fc').innerHTML='<option value="">Todas</option>'+uniq(l.map(x=>x.company)).map(x=>`<option>${x}</option>`).join('');
    $('fc').dataset.loaded='1';
  }

  renderGps(g);
  renderCompany(d.by_company);
  renderCompanyBars(d.by_company);
  renderLocations();
  $('lastUpdate').textContent='Atualizado em '+new Date().toLocaleString('pt-BR');
}

function renderGps(g){
  const s=g.summary||{};
  const items=g.items||[];
  const pct=Number(s.coverage_pct||0);

  $('gpsWith').textContent=fmt(s.with_gps||0);
  $('gpsWithout').textContent=fmt(s.without_gps||0);
  $('gpsCoverage').textContent=pct.toLocaleString('pt-BR',{maximumFractionDigits:1})+'%';
  $('gpsCoverageTag').textContent='GPS '+pct.toLocaleString('pt-BR',{maximumFractionDigits:1})+'%';

  const first=items[0];
  $('gpsLast').textContent=first
    ? new Date(first.gps_captured_at||first.created_at).toLocaleString('pt-BR')
    : '—';

  renderGpsMap(items);

  $('gpsRows').innerHTML=items.length?items.map(x=>{
    const when=new Date(x.gps_captured_at||x.created_at).toLocaleString('pt-BR');
    const accuracy=x.gps_accuracy!=null?`${Math.round(Number(x.gps_accuracy))} m`:'—';
    const coords=`${Number(x.latitude).toFixed(5)}, ${Number(x.longitude).toFixed(5)}`;
    return `<tr>
      <td>${esc(when)}</td>
      <td><b>${esc(x.technician||'')}</b>${x.technician_code?`<br><small>${esc(x.technician_code)}</small>`:''}</td>
      <td><b>${esc(x.location_name||'')}</b><br><small>${esc(x.company||'')} · ${esc(x.line||'')}</small></td>
      <td>${esc(x.equipment_type||'')}<br><b>${esc(x.asset_identifier||'')}</b></td>
      <td>${esc(accuracy)}</td>
      <td><code>${esc(coords)}</code></td>
    </tr>`;
  }).join(''):'<tr><td colspan="6">Ainda não há registros com GPS capturado.</td></tr>';
}

function renderMapLocationSelect(){
  const sel=$('mapLocationSelect'); if(!sel) return;
  const currentValue=sel.value;
  const sorted=[...locations].sort((a,b)=>`${a.company} ${a.line} ${a.location}`.localeCompare(`${b.company} ${b.line} ${b.location}`,'pt-BR'));
  sel.innerHTML='<option value="">Selecione</option>'+sorted.map(x=>`<option value="${x.id}">${esc(x.company)} · ${esc(x.line)} · ${esc(x.location)}</option>`).join('');
  if(sorted.some(x=>String(x.id)===String(currentValue))) sel.value=currentValue;
  updateReferenceStatus();
}

function updateReferenceStatus(){
  const id=Number($('mapLocationSelect')?.value||0); const loc=locations.find(x=>Number(x.id)===id);
  if(!loc){ $('referenceStatus').textContent='Nenhuma localidade selecionada.'; return; }
  if(hasReference(loc)){
    $('referenceStatus').textContent=`Referência: ${Number(loc.reference_latitude).toFixed(5)}, ${Number(loc.reference_longitude).toFixed(5)}`;
  }else $('referenceStatus').textContent='Sem referência cadastrada.';
}

if($('mapLocationSelect')) $('mapLocationSelect').addEventListener('change',()=>{
  updateReferenceStatus();
  const id=Number($('mapLocationSelect').value||0); const loc=locations.find(x=>Number(x.id)===id);
  if(loc && Number.isFinite(Number(loc.reference_latitude)) && Number.isFinite(Number(loc.reference_longitude))) ensureGpsMap()?.setView([Number(loc.reference_latitude),Number(loc.reference_longitude)],16);
});

if($('setReferenceBtn')) $('setReferenceBtn').addEventListener('click',()=>{
  if(!$('mapLocationSelect').value){ alert('Selecione primeiro uma localidade.'); return; }
  referenceMode=!referenceMode;
  $('setReferenceBtn').textContent=referenceMode?'Clique no ponto do mapa…':'Definir referência no mapa';
  $('referenceStatus').textContent=referenceMode?'Modo de definição ativo: clique no ponto correto da localidade.':'Definição cancelada.';
});

function renderCompany(a){
  $('companyRows').innerHTML=a.map(x=>{
    let p=x.total?Math.round(x.completed/x.total*100):0;
    return `<tr><td><b>${x.company}</b></td><td>${x.total}</td><td>${x.pending||0}</td><td>${x.progress||0}</td><td>${x.completed||0}</td><td>${p}%</td></tr>`
  }).join('');
}

function renderCompanyBars(a){
  const ranked=[...a].sort((x,y)=>{
    const px=x.total?x.completed/x.total:0, py=y.total?y.completed/y.total:0;
    return py-px || y.total-x.total
  });
  $('companyBars').innerHTML=ranked.map(x=>{
    let p=x.total?Math.round(x.completed/x.total*100):0;
    return `<div class="companyBar">
      <div class="companyBarTop"><span><b>${x.company}</b> · ${x.completed||0}/${x.total}</span><strong>${p}%</strong></div>
      <div class="companyTrack"><i style="width:${p}%"></i></div>
    </div>`;
  }).join('');
}

function renderLocations(){
  let fs=$('fs').value,fc=$('fc').value,fl=$('fl').value,q=$('fq').value.toUpperCase();
  let a=locations.filter(x=>
    (!fs||x.survey_status===fs)&&
    (!fc||x.company===fc)&&
    (!fl||x.line===fl)&&
    (!q||(`${x.location} ${x.line} ${x.company}`).toUpperCase().includes(q))
  );
  $('visibleCount').textContent=`${a.length} localidade(s)`;

  $('locRows').innerHTML=a.length?a.map(x=>{
    let exp=x.expected_atm+x.expected_validator+x.expected_pos,
        inv=x.inventoried||0,
        p=exp?Math.min(100,Math.round(inv/exp*100)):0;
    return `<tr>
      <td>${st(x.survey_status)}</td>
      <td>${x.company}</td>
      <td>${x.line}</td>
      <td><b>${x.location}</b></td>
      <td>${exp}<br><small>ATM ${x.expected_atm} · VAL ${x.expected_validator} · POS ${x.expected_pos}</small></td>
      <td><b>${inv}</b></td>
      <td><div class="bar"><i style="width:${p}%"></i></div><small>${p}% do parque-base</small></td>
      <td>${x.inoperative||0}</td>
      <td>${x.survey_status==='CONCLUIDA'?`<button class="secondary" onclick="reopen(${x.id})">Reabrir</button>`:'—'}</td>
    </tr>`;
  }).join(''):`<tr><td colspan="9">Nenhuma localidade encontrada com os filtros selecionados.</td></tr>`;
}

$('fs').onchange=()=>{syncChips();renderLocations()};
$('fc').onchange=()=>{
  $('fl').innerHTML='<option value="">Todas</option>'+uniq(locations.filter(x=>!$('fc').value||x.company===$('fc').value).map(x=>x.line)).map(x=>`<option>${x}</option>`).join('');
  renderLocations();
};
$('fl').onchange=renderLocations;
$('fq').oninput=renderLocations;

document.querySelectorAll('.filterChip').forEach(b=>b.onclick=()=>{
  $('fs').value=b.dataset.status;
  syncChips();
  renderLocations();
});
function syncChips(){
  document.querySelectorAll('.filterChip').forEach(b=>b.classList.toggle('active',b.dataset.status===$('fs').value));
}
async function reopen(id){
  if(!confirm('Reabrir esta localidade para novos lançamentos?'))return;
  await fetch(`/api/location/${id}/reopen`,{method:'POST'});
  await loadAll();
}

loadAll();
setInterval(loadAll,60000);
