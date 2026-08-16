window.AUTOPASS_MANAGER_VERSION='dashboard-v21';
console.log('AUTOPASS Dashboard Executivo V21 carregado');
let locations=[];
let dashboardData=null;
const $=id=>document.getElementById(id);
const uniq=a=>[...new Set(a)].sort((x,y)=>x.localeCompare(y,'pt-BR'));
function st(s){return `<span class="status s${s.replaceAll(' ','')}">${s}</span>`}
function fmt(n){return new Intl.NumberFormat('pt-BR').format(Number(n||0))}
function esc(v){return String(v??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'","&#039;")}

const OFFICIAL_EXEC_TYPES=['ATM','VALIDADOR','POS','BLOQUEIO'];
function typeLabel(type){
  return type==='VALIDADOR'?'Recarga':type==='BLOQUEIO'?'Bloqueio':type;
}
function sumObjectValues(obj){return Object.values(obj||{}).reduce((a,b)=>a+Number(b||0),0)}
function filteredLocationMetrics(rows,type=''){
  const result={
    expected:0,inventoried:0,missing:0,inoperative:0,divergences:0,
    byType:{ATM:{e:0,i:0},VALIDADOR:{e:0,i:0},POS:{e:0,i:0},TDI:{e:0,i:0},BLOQUEIO:{e:0,i:0}}
  };
  rows.forEach(x=>{
    const exp=x.expected_by_type||{};
    const inv=x.inventoried_by_type||{};
    Object.keys(result.byType).forEach(t=>{
      result.byType[t].e+=Number(exp[t]||0);
      result.byType[t].i+=Number(inv[t]||0);
    });
    result.inoperative+=Number(x.inoperative||0);
    result.divergences+=Number(x.divergences||0);
  });
  if(type){
    result.expected=result.byType[type]?.e||0;
    result.inventoried=result.byType[type]?.i||0;
  }else{
    result.expected=OFFICIAL_EXEC_TYPES.reduce((a,t)=>a+(result.byType[t]?.e||0),0);
    result.inventoried=OFFICIAL_EXEC_TYPES.reduce((a,t)=>a+(result.byType[t]?.i||0),0);
  }
  result.missing=Math.max(0,result.expected-result.inventoried);
  return result;
}

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

  // Inventário atual é da região de São Paulo.
  // Ignora referências incorretas ou antigas fora desta área.
  if(lat < -25 || lat > -22 || lon < -49 || lon > -45){
    return false;
  }

  return true;
}

let gpsMap=null;
let gpsPointLayer=null;
let gpsAccuracyLayer=null;
let referenceLayer=null;
let stationLabelLayer=null;
let referenceMode=false;
let referenceTempMarker=null;
let railLineLayer=null;
let mapLayersControl=null;
let railLegendControl=null;
let mapViewInitialized=false;


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

/* =========================================================
   MAPA METROFERROVIÁRIO
========================================================= */

const railColorsByNumber={
  '1':'#0054A6',
  '2':'#008C5A',
  '3':'#E6332A',
  '4':'#F4C300',
  '5':'#7A3E9D',
  '6':'#F28C18',
  '7':'#A60055',
  '8':'#8C8C8C',
  '9':'#00A092',
  '10':'#00A5B5',
  '11':'#F04B23',
  '12':'#164F9C',
  '13':'#009B62',
  '15':'#9B9DA0',
  '17':'#9A7A24'
};

const railNamesByNumber={
  '1':'Azul','2':'Verde','3':'Vermelha','4':'Amarela','5':'Lilás','6':'Laranja',
  '7':'Rubi','8':'Diamante','9':'Esmeralda','10':'Turquesa','11':'Coral',
  '12':'Safira','13':'Jade','15':'Prata','17':'Ouro'
};

function normalizeRailText(value){
  return String(value||'')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g,'')
    .toUpperCase()
    .trim();
}

function railNumber(line){
  const t=normalizeRailText(line);
  const m=t.match(/(?:^|\s)(0?1[0-7]|0?[1-9])(?:\s|\-|$)/);
  if(m) return String(Number(m[1]));

  const aliases={
    AZUL:'1',VERDE:'2',VERMELHA:'3',AMARELA:'4',LILAS:'5',LARANJA:'6',
    RUBI:'7',DIAMANTE:'8',ESMERALDA:'9',TURQUESA:'10',CORAL:'11',SAFIRA:'12',
    JADE:'13',PRATA:'15',OURO:'17'
  };
  return aliases[t]||Object.entries(aliases).find(([name])=>t.includes(name))?.[1]||'';
}

function railColor(line){
  return railColorsByNumber[railNumber(line)]||'#64748b';
}

function railDisplayName(line){
  const n=railNumber(line);
  return n ? `Linha ${n} — ${railNamesByNumber[n]||String(line||'')}` : String(line||'Linha');
}

function ensureRailMapStyles(){
  if(document.getElementById('autopassRailMapStyles')) return;
  const style=document.createElement('style');
  style.id='autopassRailMapStyles';
  style.textContent=`
    .rail-station-label{
      background:rgba(255,255,255,.88)!important;
      border:0!important;
      box-shadow:none!important;
      color:#152033!important;
      font-size:10px!important;
      font-weight:700!important;
      padding:1px 3px!important;
      white-space:nowrap!important;
      text-shadow:0 1px 0 #fff,1px 0 0 #fff,-1px 0 0 #fff,0 -1px 0 #fff;
    }
    .rail-station-label:before{display:none!important;}
    .rail-line-end-icon{background:transparent!important;border:0!important;}
    .rail-line-number{
      display:flex;align-items:center;justify-content:center;
      width:30px;height:30px;border-radius:5px;
      color:#fff;font:800 16px/1 Arial,sans-serif;
      border:2px solid rgba(255,255,255,.96);
      box-shadow:0 1px 5px rgba(0,0,0,.32);
    }
    .autopass-rail-legend{
      background:rgba(255,255,255,.95);padding:10px 12px;border-radius:8px;
      box-shadow:0 1px 6px rgba(15,23,42,.24);max-height:360px;overflow:auto;
      font:12px/1.35 Arial,sans-serif;color:#172033;
    }
    .autopass-rail-legend h4{margin:0 0 8px;font-size:13px;}
    .autopass-rail-legend .row{display:flex;align-items:center;gap:8px;margin:4px 0;}
    .autopass-rail-legend .swatch{display:inline-block;width:28px;height:6px;border-radius:4px;}
    .leaflet-control-layers-expanded{font-size:12px;border-radius:8px!important;}
  `;
  document.head.appendChild(style);
}

function buildRailSequence(stations){
  const pool=[...stations];
  if(pool.length<2) return pool;

  // Começa por um extremo aproximado: menor longitude + latitude.
  pool.sort((a,b)=>{
    const ax=Number(a.reference_longitude)+Number(a.reference_latitude)*.08;
    const bx=Number(b.reference_longitude)+Number(b.reference_latitude)*.08;
    return ax-bx;
  });

  const sequence=[pool.shift()];
  while(pool.length){
    const last=sequence[sequence.length-1];
    let bestIndex=0,bestDistance=Infinity;
    pool.forEach((candidate,index)=>{
      const d=haversineMeters(
        Number(last.reference_latitude),Number(last.reference_longitude),
        Number(candidate.reference_latitude),Number(candidate.reference_longitude)
      );
      if(d<bestDistance){bestDistance=d;bestIndex=index;}
    });
    sequence.push(pool.splice(bestIndex,1)[0]);
  }
  return sequence;
}

function addRailLegend(){
  if(!gpsMap||railLegendControl) return;
  railLegendControl=L.control({position:'topleft'});
  railLegendControl.onAdd=()=>{
    const div=L.DomUtil.create('div','autopass-rail-legend');
    const numbers=['1','2','3','4','5','6','7','8','9','10','11','12','13','15','17'];
    div.innerHTML='<h4>Linhas Metroferroviárias</h4>'+numbers.map(n=>`
      <div class="row">
        <span class="swatch" style="background:${railColorsByNumber[n]}"></span>
        <b>${n}</b><span>${railNamesByNumber[n]}</span>
      </div>`).join('');
    L.DomEvent.disableClickPropagation(div);
    L.DomEvent.disableScrollPropagation(div);
    return div;
  };
  railLegendControl.addTo(gpsMap);
}

function ensureGpsMap(){
  if(gpsMap || !window.L || !$('gpsMap')) return gpsMap;

  ensureRailMapStyles();
  gpsMap=L.map('gpsMap',{scrollWheelZoom:true}).setView([-23.5505,-46.6333],10);

  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{
    maxZoom:19,
    attribution:'&copy; OpenStreetMap contributors'
  }).addTo(gpsMap);

  railLineLayer=L.layerGroup().addTo(gpsMap);
  referenceLayer=L.layerGroup().addTo(gpsMap);
  stationLabelLayer=L.layerGroup();
  gpsPointLayer=L.layerGroup().addTo(gpsMap);
  gpsAccuracyLayer=L.layerGroup();

  addRailLegend();

  mapLayersControl=L.control.layers(null,{
    'Linhas':railLineLayer,
    'Estações':referenceLayer,
    'Nomes das estações':stationLabelLayer,
    'Técnicos (GPS)':gpsPointLayer,
    'Precisão GPS (auditoria)':gpsAccuracyLayer
  },{collapsed:false,position:'bottomright'}).addTo(gpsMap);

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
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({latitude:e.latlng.lat,longitude:e.latlng.lng,source:'Gestor - mapa'})
    });
    const j=await r.json().catch(()=>({ok:false,error:'Erro no servidor.'}));
    if(!r.ok){alert(j.error||'Não foi possível salvar a referência.');return;}

    referenceMode=false;
    $('setReferenceBtn').textContent='Definir referência no mapa';
    $('referenceStatus').textContent='Referência salva.';
    if(referenceTempMarker){referenceTempMarker.remove();referenceTempMarker=null;}
    await loadAll();
loadFieldEvidenceSummary();
  });

  setTimeout(()=>gpsMap.invalidateSize(),100);
  return gpsMap;
}

function renderRailLines(){
  if(!railLineLayer) return;
  railLineLayer.clearLayers();

  const groups={};
  locations.filter(hasReference).forEach(loc=>{
    const n=railNumber(loc.line);
    if(!n) return;
    (groups[n]??=[]).push(loc);
  });

  Object.entries(groups).forEach(([number,stations])=>{
    if(stations.length<2) return;

    const sequence=buildRailSequence(stations);
    const coordinates=sequence.map(x=>[
      Number(x.reference_latitude),Number(x.reference_longitude)
    ]);
    const color=railColorsByNumber[number]||'#64748b';

    // Halo branco: aumenta contraste sobre o mapa-base.
    L.polyline(coordinates,{
      color:'#ffffff',weight:11,opacity:.96,lineCap:'round',lineJoin:'round',interactive:false
    }).addTo(railLineLayer);

    const polyline=L.polyline(coordinates,{
      color,weight:7,opacity:1,lineCap:'round',lineJoin:'round'
    }).addTo(railLineLayer);

    polyline.bindPopup(`<b>${esc(railDisplayName(sequence[0]?.line))}</b><br>${stations.length} estação(ões) com referência geográfica`);

    // Número da linha nas duas pontas do traçado.
    [sequence[0],sequence[sequence.length-1]].forEach(endpoint=>{
      if(!endpoint) return;
      const icon=L.divIcon({
        className:'rail-line-end-icon',
        html:`<div class="rail-line-number" style="background:${color}">${esc(number)}</div>`,
        iconSize:[30,30],iconAnchor:[15,15]
      });
      L.marker([Number(endpoint.reference_latitude),Number(endpoint.reference_longitude)],{icon,interactive:false})
        .addTo(railLineLayer);
    });
  });
}

function renderStations(){
  if(!referenceLayer) return;
  referenceLayer.clearLayers();
  if(stationLabelLayer) stationLabelLayer.clearLayers();

  locations.filter(hasReference).forEach(x=>{
    const lat=Number(x.reference_latitude),lon=Number(x.reference_longitude);
    const color=railColor(x.line);

    const ref=L.circleMarker([lat,lon],{
      radius:5,color:'#ffffff',weight:2,fillColor:color,fillOpacity:1,opacity:1
    }).addTo(referenceLayer);

    ref.bindPopup(`<div style="min-width:210px"><b>${esc(x.location)}</b><br><small>${esc(x.company)} · ${esc(x.line)}</small><br><small>Fonte: ${esc(x.reference_source||'não informada')}</small></div>`);

    ref.bindTooltip(esc(x.location),{
      permanent:false,direction:'top',offset:[0,-6],className:'rail-station-hover',opacity:.96
    });
    if(stationLabelLayer){
      const label=L.marker([lat,lon],{interactive:false,icon:L.divIcon({className:'stationLabelIcon',html:`<span>${esc(x.location)}</span>`,iconSize:null})});
      label.addTo(stationLabelLayer);
    }
  });
}

function renderGpsMap(items){
  const map=ensureGpsMap();
  if(!map) return;

  gpsPointLayer.clearLayers();
  gpsAccuracyLayer.clearLayers();
  railLineLayer.clearLayers();
  referenceLayer.clearLayers();

  renderRailLines();
  renderStations();

  const valid=(items||[]).filter(x=>
    Number.isFinite(Number(x.latitude)) && Number.isFinite(Number(x.longitude))
  );

  valid.forEach(x=>{
    const lat=Number(x.latitude),lon=Number(x.longitude);
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

    // V10: círculo de precisão disponível apenas na camada opcional de auditoria.
    if(Number.isFinite(accuracy)&&accuracy>0&&accuracy<=500){
      L.circle([lat,lon],{radius:accuracy,color,weight:1,opacity:.45,fillColor:color,fillOpacity:.05}).addTo(gpsAccuracyLayer);
    }

    const techInitials=String(x.technician||'?').trim().split(/\s+/).slice(0,2).map(v=>v[0]||'').join('').toUpperCase();
    const markerIcon=L.divIcon({
      className:'',
      html:`<div class="gpsTechAvatar" style="outline:3px solid ${color}">${x.technician_photo_url?`<img src="${esc(x.technician_photo_url)}?v=${encodeURIComponent(x.gps_captured_at||x.created_at||'v10')}" alt="">`:`<span>${esc(techInitials)}</span>`}</div>`,
      iconSize:[40,40],iconAnchor:[20,20]
    });
    const marker=L.marker([lat,lon],{icon:markerIcon}).addTo(gpsPointLayer);

    marker.bindPopup(`
      <div style="min-width:220px">
        <b>${esc(x._team_current?'Posição atual do técnico':(x.location_name||'Localidade'))}</b><br>
        <small>${esc(x.company||'')} · ${esc(x.line||'')}</small>
        <hr style="border:0;border-top:1px solid #e5e7eb;margin:8px 0">
        ${x._team_current?'':`<b>${esc(x.equipment_type||'Equipamento')} ${esc(x.asset_identifier||'')}</b><br>`}
        Técnico: ${esc(x.technician||'—')}<br>
        Coleta: ${esc(when)}<br>
        Precisão GPS: <b>${esc(accuracyText)}</b><br>
        ${esc(distanceText)}<br>
        <small>${lat.toFixed(5)}, ${lon.toFixed(5)}</small>
      </div>`);
  });

  // Enquadra a rede inteira apenas na primeira carga. Depois preserva zoom/pan do gestor.
  if(!mapViewInitialized){
    const refCoords=locations.filter(hasReference).map(x=>[
      Number(x.reference_latitude),Number(x.reference_longitude)
    ]);
    if(refCoords.length>1){
      map.fitBounds(refCoords,{padding:[45,45],maxZoom:11});
    }else if(refCoords.length===1){
      map.setView(refCoords[0],14);
    }else{
      map.setView([-23.5505,-46.6333],10);
    }
    mapViewInitialized=true;
  }

  setTimeout(()=>map.invalidateSize(),50);
}


function setMapFullscreen(on){
  const mapEl=$('gpsMap');
  const btn=$('toggleMapFullscreenBtn');
  if(!mapEl) return;

  mapEl.classList.toggle('gpsMapFullscreen',!!on);
  document.body.classList.toggle('mapFullscreenOpen',!!on);
  if(btn) btn.textContent=on?'Sair da tela cheia':'Expandir mapa';

  setTimeout(()=>{
    try{ gpsMap?.invalidateSize(); }catch(_e){}
  },80);
}

if($('toggleMapFullscreenBtn')){
  $('toggleMapFullscreenBtn').addEventListener('click',()=>{
    setMapFullscreen(!$('gpsMap')?.classList.contains('gpsMapFullscreen'));
  });
}

document.addEventListener('keydown',e=>{
  if(e.key==='Escape' && $('gpsMap')?.classList.contains('gpsMapFullscreen')){
    setMapFullscreen(false);
  }
});

async function loadAll(){
  const started=performance.now();
  if($('lastUpdate')) $('lastUpdate').textContent='Atualizando indicadores...';
  try{
    // Fase 1: /api/dashboard é leve e exibe imediatamente os KPIs oficiais.
    const d=await fetch('/api/dashboard',{cache:'no-store'}).then(r=>{
      if(!r.ok) throw new Error('Dashboard '+r.status);
      return r.json();
    });
    dashboardData=d;
    renderGlobalDashboard(d);
    if($('lastUpdate')) $('lastUpdate').textContent='KPIs em '+((performance.now()-started)/1000).toFixed(1)+'s · carregando localidades...';

    // Fase 2: localidades/base detalhada é mais pesada, mas não bloqueia os Big Numbers.
    const l=await fetch('/api/locations',{cache:'no-store'}).then(r=>{
      if(!r.ok) throw new Error('Localidades '+r.status);
      return r.json();
    });
    locations=l;
    renderMapLocationSelect();
    renderExecutiveFilters();

    if(!$('fc').dataset.loaded){
      $('fc').innerHTML='<option value="">Todas</option>'+uniq(l.map(x=>x.company)).map(x=>`<option>${esc(x)}</option>`).join('');
      $('fc').dataset.loaded='1';
    }

    renderCompany(d.by_company||[]);
    renderCompanyBars(d.by_company||[]);
    renderLocations();
    renderCriticalLocations();
    updateExecutiveView();

    if($('lastUpdate')) $('lastUpdate').textContent='Atualizado em '+new Date().toLocaleString('pt-BR')+` · ${((performance.now()-started)/1000).toFixed(1)}s`;
    setTimeout(loadGpsDeferred,120);
  }catch(err){
    console.error('Falha ao carregar dashboard',err);
    if($('lastUpdate')) $('lastUpdate').textContent='Falha ao atualizar — clique em Atualizar agora';
  }
}

function renderGlobalDashboard(d){
  $('total').textContent=fmt(d.totals.total);
  $('pending').textContent=fmt(d.totals.pending);
  $('progress').textContent=fmt(d.totals.progress);
  $('completed').textContent=fmt(d.totals.completed);
  $('expected').textContent=fmt(d.totals.expected);
  $('inventoried').textContent=fmt(d.inventory.official_inventoried ?? d.inventory.inventoried);
  if($('missing')) $('missing').textContent=fmt(d.totals.missing||0);
  $('inoperative').textContent=fmt(d.inventory.inoperative);
  $('divergences').textContent=fmt(d.inventory.divergences);
  if($('inoperativeQuality')) $('inoperativeQuality').textContent=fmt(d.inventory.inoperative);
  if($('divergencesQuality')) $('divergencesQuality').textContent=fmt(d.inventory.divergences);
  if($('unclassified')) $('unclassified').textContent=fmt(d.inventory.unclassified||0);

  const total=Number(d.totals.total||0), done=Number(d.totals.completed||0),
        prog=Number(d.totals.progress||0), pend=Number(d.totals.pending||0),
        expected=Number(d.totals.expected||0), inventoried=Number((d.inventory.official_inventoried ?? d.inventory.inventoried) || 0);
  const pct=total?Math.round(done/total*100):0;
  const coverage=expected?Math.min(100,Math.round(inventoried/expected*100)):0;

  $('overallPct').textContent=pct+'%';
  $('donutText').textContent=pct+'%';
  $('legendDone').textContent=done;
  $('legendProgress').textContent=prog;
  $('legendPending').textContent=pend;
  $('assetCoverage').textContent=coverage+'%';
  if($('assetCoverageTop')) $('assetCoverageTop').textContent=coverage+'%';
  if($('inventoryCoverageSmall')) $('inventoryCoverageSmall').textContent=coverage+'% do parque';
  renderTypeBigNumbers(d.by_type||[]);
  renderTypeProgress(d.by_type||[]);

  const dDone=total?(done/total*360):0;
  const dProg=total?(prog/total*360):0;
  $('donut').style.background=`conic-gradient(var(--green) 0deg ${dDone}deg,var(--amber) ${dDone}deg ${dDone+dProg}deg,#e1e6ed ${dDone+dProg}deg 360deg)`;
}

let gpsLoading=false;
async function loadGpsDeferred(){
  if(gpsLoading) return; gpsLoading=true;
  try{
    const [gpsR,teamR]=await Promise.all([fetch('/api/gps/recent?limit=100',{cache:'no-store'}),fetch('/api/equipes/status',{cache:'no-store'})]);
    if(!gpsR.ok) throw new Error('GPS '+gpsR.status);
    const gps=await gpsR.json(); renderGps(gps);
    if(teamR.ok){ const team=await teamR.json(); renderTeamPositionsOnDashboard(team.technicians||team.rows||team.items||[]); }
  }catch(err){console.warn('GPS não carregado',err)} finally{gpsLoading=false}
}

function renderTeamPositionsOnDashboard(rows){
  const items=(rows||[]).filter(x=>Number.isFinite(Number(x.latitude))&&Number.isFinite(Number(x.longitude))).map(x=>({
    latitude:x.latitude,longitude:x.longitude,gps_accuracy:x.accuracy,gps_captured_at:x.captured_at,created_at:x.captured_at,
    technician:x.name||x.technician||'Técnico',technician_code:x.user_code||'',technician_photo_url:x.photo_url||'',
    location_name:'Posição atual',company:'Equipe de campo',line:x.shift||'',equipment_type:'Última posição autorizada',asset_identifier:'',_team_current:true
  }));
  renderGpsMap(items);
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

  const id = Number($('mapLocationSelect').value || 0);
  const loc = locations.find(x => Number(x.id) === id);

  if(hasReference(loc)){
    ensureGpsMap()?.setView(
      [Number(loc.reference_latitude), Number(loc.reference_longitude)],
      16
    );
  }
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

function expectedBreakdown(x){
  const e=x.expected_by_type||{};
  if(Object.keys(e).length) return `ATM ${e.ATM||0} · VAL ${e.VALIDADOR||0} · POS ${e.POS||0} · TDI ${e.TDI||0} · BLOQ ${e.BLOQUEIO||0}`;
  return `ATM ${x.expected_atm||0} · VAL ${x.expected_validator||0} · POS ${x.expected_pos||0}`;
}
function renderTypeBigNumbers(rows){ rows.forEach(x=>{ const id=x.type; if($('type'+id)) $('type'+id).textContent=fmt(x.expected); if($('type'+id+'Detail')) $('type'+id+'Detail').textContent=`${fmt(x.inventoried)} levantados · ${fmt(x.missing)} faltam · ${x.coverage_pct}%`; }); }
function renderTypeProgress(rows){ const box=$('typeProgressList'); if(!box)return; box.innerHTML=rows.map(x=>`<div class="typeProgressRow"><b>${esc(x.type==='VALIDADOR'?'Validador':x.type==='BLOQUEIO'?'Bloqueio':x.type)}</b><div class="companyTrack"><i style="width:${Math.min(100,Number(x.coverage_pct||0))}%"></i></div><small>${x.coverage_pct}%</small></div>`).join(''); }
function renderExecutiveFilters(){
  const c=$('execCompany'),line=$('execLine');
  if(!c||!line)return;
  const oldC=c.value,oldL=line.value;
  c.innerHTML='<option value="">Todas</option>'+uniq(locations.map(x=>x.company)).map(x=>`<option>${esc(x)}</option>`).join('');
  if([...c.options].some(o=>o.value===oldC))c.value=oldC;
  const avail=locations.filter(x=>!c.value||x.company===c.value);
  line.innerHTML='<option value="">Todas</option>'+uniq(avail.map(x=>x.line)).map(x=>`<option>${esc(x)}</option>`).join('');
  if([...line.options].some(o=>o.value===oldL))line.value=oldL;
}
function executiveFilteredLocations(){
  const c=$('execCompany')?.value||'',line=$('execLine')?.value||'',type=$('execType')?.value||'';
  return locations.filter(x=>
    (!c||x.company===c)&&
    (!line||x.line===line)&&
    (!type||Number((x.expected_by_type||{})[type]||0)>0||Number((x.inventoried_by_type||{})[type]||0)>0)
  );
}

function renderExecutiveAnalytics(rows,type){
  if(!$('executiveAnalytics')) return;
  const m=filteredLocationMetrics(rows,type);
  const pct=m.expected?Math.min(100,Math.round(m.inventoried/m.expected*100)):0;
  $('analyticsCoverage').textContent=pct+'%';
  $('analyticsCoverageBar').style.width=pct+'%';
  $('analyticsCoverageText').textContent=`${fmt(m.inventoried)} de ${fmt(m.expected)} inventariados`;
  $('analyticsDivergences').textContent=fmt(m.divergences);
  $('analyticsInoperative').textContent=fmt(m.inoperative);
  const c=$('execCompany')?.value||'',l=$('execLine')?.value||'';
  $('analyticsContext').textContent=[c||'Todas empresas',l||'Todas linhas',type?typeLabel(type):'Todos os tipos'].join(' · ');
  const types=type?[type]:OFFICIAL_EXEC_TYPES;
  $('analyticsTypes').innerHTML=types.map(t=>{const z=m.byType[t]||{e:0,i:0};const p=z.e?Math.min(100,Math.round(z.i/z.e*100)):0;return `<div class="analyticsTypeRow"><b>${esc(typeLabel(t))}</b><div class="track"><i style="width:${p}%"></i></div><span>${p}%</span></div>`}).join('');
  const dynamicRows=OFFICIAL_EXEC_TYPES.map(t=>{const z=m.byType[t]||{e:0,i:0};return {type:t,expected:z.e,inventoried:z.i,missing:Math.max(0,z.e-z.i),coverage_pct:z.e?Math.round(z.i/z.e*1000)/10:0}});
  renderTypeProgress(type?dynamicRows.filter(x=>x.type===type):dynamicRows);
}

function renderV21ExecutiveCharts(rows,type){
  if(!$('v21ExecutiveCharts')) return;
  const m=filteredLocationMetrics(rows,type);
  const pct=m.expected?Math.min(100,Math.round(m.inventoried/m.expected*100)):0;
  $('v21ExecPct').textContent=pct+'%';
  $('v21Done').textContent=fmt(m.inventoried);
  $('v21Left').textContent=fmt(m.missing);
  $('v21StackedExecution').innerHTML=`<i class="done" style="width:${pct}%"></i><i class="missing" style="width:${Math.max(0,100-pct)}%"></i>`;
  const types=type?[type]:OFFICIAL_EXEC_TYPES;
  $('v21TypeBars').innerHTML=types.map(t=>{
    const z=m.byType[t]||{e:0,i:0}, p=z.e?Math.min(100,Math.round(z.i/z.e*100)):0;
    return `<div class="v21BarRow"><div><b>${esc(typeLabel(t))}</b><span>${fmt(z.i)}/${fmt(z.e)}</span></div><div class="v21BarTrack"><i style="width:${p}%"></i></div><strong>${p}%</strong></div>`;
  }).join('');
  const priorities=rows.map(x=>{
    const exp=type?Number((x.expected_by_type||{})[type]||0):OFFICIAL_EXEC_TYPES.reduce((a,t)=>a+Number((x.expected_by_type||{})[t]||0),0);
    const inv=type?Number((x.inventoried_by_type||{})[type]||0):OFFICIAL_EXEC_TYPES.reduce((a,t)=>a+Number((x.inventoried_by_type||{})[t]||0),0);
    return {...x,_missing:Math.max(0,exp-inv)};
  }).filter(x=>x._missing>0).sort((a,b)=>b._missing-a._missing).slice(0,6);
  const max=Math.max(1,...priorities.map(x=>x._missing));
  $('v21PriorityBars').innerHTML=priorities.length?priorities.map((x,i)=>`<div class="v21PriorityRow"><span class="rank">${i+1}</span><div class="who"><b>${esc(x.location)}</b><small>${esc(x.company)} · ${esc(x.line)}</small><div class="v21PriorityTrack"><i style="width:${Math.round(x._missing/max*100)}%"></i></div></div><strong>${fmt(x._missing)}</strong></div>`).join(''):'<div class="muted">Nenhuma pendência no recorte atual.</div>';
}
function updateExecutiveView(){
  if(!dashboardData) return;
  const c=$('execCompany')?.value||'', line=$('execLine')?.value||'', type=$('execType')?.value||'';
  const noGeoFilters=!c&&!line;
  const rows=executiveFilteredLocations();

  // Sem Empresa/Linha usamos os denominadores oficiais para os Big Numbers.
  if(noGeoFilters){
    const officialRows=(dashboardData.by_type||[]);
    if(type){
      const row=officialRows.find(x=>x.type===type);
      const exp=Number(row?.expected||0), inv=Number(row?.inventoried||0);
      $('expected').textContent=fmt(exp);
      $('inventoried').textContent=fmt(inv);
      $('missing').textContent=fmt(Math.max(0,exp-inv));
      const coverage=exp?Math.min(100,Math.round(inv/exp*100)):0;
      $('assetCoverageTop').textContent=coverage+'%';
      $('inventoryCoverageSmall').textContent=coverage+'% do parque';
    }else{
      $('expected').textContent=fmt(dashboardData.totals.expected);
      $('inventoried').textContent=fmt(dashboardData.inventory.official_inventoried ?? dashboardData.inventory.inventoried);
      $('missing').textContent=fmt(dashboardData.totals.missing);
      const coverage=dashboardData.totals.expected?Math.min(100,Math.round((dashboardData.inventory.official_inventoried ?? dashboardData.inventory.inventoried)/dashboardData.totals.expected*100)):0;
      $('assetCoverageTop').textContent=coverage+'%';
      $('inventoryCoverageSmall').textContent=coverage+'% do parque';
    }
    renderTypeBigNumbers(officialRows);
  }else{
    const m=filteredLocationMetrics(rows,type);
    $('expected').textContent=fmt(m.expected);
    $('inventoried').textContent=fmt(m.inventoried);
    $('missing').textContent=fmt(m.missing);
    const coverage=m.expected?Math.min(100,Math.round(m.inventoried/m.expected*100)):0;
    $('assetCoverageTop').textContent=coverage+'%';
    $('inventoryCoverageSmall').textContent=coverage+'% do recorte';

    const dynamicRows=['ATM','VALIDADOR','POS','TDI','BLOQUEIO'].map(t=>{
      const exp=m.byType[t].e,inv=m.byType[t].i;
      return {type:t,expected:exp,inventoried:inv,missing:Math.max(0,exp-inv),coverage_pct:exp?Math.round(inv/exp*1000)/10:0};
    });
    renderTypeBigNumbers(dynamicRows);
  }

  if(c||line||type){
    const fm=filteredLocationMetrics(rows,type);
    $('inoperative').textContent=fmt(fm.inoperative);
    $('divergences').textContent=fmt(fm.divergences);
    if($('inoperativeQuality')) $('inoperativeQuality').textContent=fmt(fm.inoperative);
    if($('divergencesQuality')) $('divergencesQuality').textContent=fmt(fm.divergences);
  }else{
    $('inoperative').textContent=fmt(dashboardData.inventory.inoperative);
    $('divergences').textContent=fmt(dashboardData.inventory.divergences);
    if($('inoperativeQuality')) $('inoperativeQuality').textContent=fmt(dashboardData.inventory.inoperative);
    if($('divergencesQuality')) $('divergencesQuality').textContent=fmt(dashboardData.inventory.divergences);
  }

  if($('filterContext')){
    const parts=[c||'Todas empresas',line||'Todas linhas',type?typeLabel(type):'Todos os tipos'];
    $('filterContext').textContent=parts.join(' · ');
  }
  renderExecutiveAnalytics(rows,type);
  renderV21ExecutiveCharts(rows,type);
  const bm=filteredLocationMetrics(rows,type);
  const bc=bm.expected?Math.min(100,Math.round(bm.inventoried/bm.expected*100)):0;
  if($('biCoverage')) $('biCoverage').textContent=bc+'%';
  if($('biMissing')) $('biMissing').textContent=fmt(bm.missing);
  const qBase=Math.max(1,bm.inventoried);
  const q=Math.max(0,Math.round(100-((bm.divergences+bm.inoperative)/qBase*100)));
  if($('biQuality')) $('biQuality').textContent=q+'%';
  if($('biCritical')) { const c=(bm.missing>0&&bc<50)?'Crítico':(bm.missing>0||bm.divergences>0||bm.inoperative>0)?'Atenção':'Normal'; $('biCritical').textContent=c; $('biCritical').dataset.state=c; }
  renderCriticalLocations();
  renderLocations();
}

function renderCriticalLocations(){
  const box=$('criticalLocations');if(!box)return;
  const type=$('execType')?.value||'';
  const rows=executiveFilteredLocations().map(x=>{
    const exp=type?Number((x.expected_by_type||{})[type]||0):OFFICIAL_EXEC_TYPES.reduce((a,t)=>a+Number((x.expected_by_type||{})[t]||0),0);
    const inv=type?Number((x.inventoried_by_type||{})[type]||0):OFFICIAL_EXEC_TYPES.reduce((a,t)=>a+Number((x.inventoried_by_type||{})[t]||0),0);
    return {...x,_expected:exp,_inventoried:inv,_missing:Math.max(0,exp-inv)};
  }).filter(x=>x._missing>0).sort((a,b)=>b._missing-a._missing).slice(0,8);
  box.innerHTML=rows.length?rows.map(x=>`<div class="criticalItem"><div><b>${esc(x.location)}</b><small>${esc(x.company)} · ${esc(x.line)}</small></div><strong>${fmt(x._missing)} faltam</strong></div>`).join(''):'<div class="muted">Nenhuma pendência para os filtros atuais.</div>';
}
function applyExecutiveFilterToTable(){
  const c=$('execCompany')?.value||'',line=$('execLine')?.value||'';
  if($('fc'))$('fc').value=c;
  if($('fl')){
    $('fl').innerHTML='<option value="">Todas</option>'+uniq(locations.filter(x=>!c||x.company===c).map(x=>x.line)).map(x=>`<option>${esc(x)}</option>`).join('');
    $('fl').value=line;
  }
  updateExecutiveView();
}

function renderLocations(){
  if(!$('locRows')) return;
  let fs=$('fs').value,fc=$('fc').value,fl=$('fl').value,q=$('fq').value.toUpperCase();
  const execC=$('execCompany')?.value||'',execL=$('execLine')?.value||'',execType=$('execType')?.value||'';
  let a=locations.filter(x=>
    (!fs||x.survey_status===fs)&&
    (!fc||x.company===fc)&&
    (!fl||x.line===fl)&&
    (!execC||x.company===execC)&&
    (!execL||x.line===execL)&&
    (!execType||Number((x.expected_by_type||{})[execType]||0)>0||Number((x.inventoried_by_type||{})[execType]||0)>0)&&
    (!q||(`${x.location} ${x.line} ${x.company}`).toUpperCase().includes(q))
  );
  $('visibleCount').textContent=`${a.length} localidade(s)`;

  $('locRows').innerHTML=a.length?a.map(x=>{
    const exp=execType?Number((x.expected_by_type||{})[execType]||0):OFFICIAL_EXEC_TYPES.reduce((s,t)=>s+Number((x.expected_by_type||{})[t]||0),0);
    const inv=execType?Number((x.inventoried_by_type||{})[execType]||0):OFFICIAL_EXEC_TYPES.reduce((s,t)=>s+Number((x.inventoried_by_type||{})[t]||0),0);
    const p=exp?Math.min(100,Math.round(inv/exp*100)):0;
    return `<tr>
      <td>${st(x.survey_status)}</td>
      <td>${esc(x.company)}</td>
      <td>${esc(x.line)}</td>
      <td><b>${esc(x.location)}</b></td>
      <td>${fmt(exp)}<br><small>${execType?typeLabel(execType):expectedBreakdown(x)}</small></td>
      <td><b>${fmt(inv)}</b></td>
      <td><div class="bar"><i style="width:${p}%"></i></div><small>${p}% do parque-base</small></td>
      <td>${fmt(x.divergences||0)}</td>
      <td>${fmt(x.inoperative||0)}</td>
      <td>${x.survey_status==='CONCLUIDA'?`<button class="secondary" onclick="reopen(${x.id})">Reabrir</button>`:'—'}</td>
    </tr>`;
  }).join(''):`<tr><td colspan="10">Nenhuma localidade encontrada com os filtros selecionados.</td></tr>`;
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

if($('execCompany')) $('execCompany').onchange=()=>{
  renderExecutiveFilters();
  applyExecutiveFilterToTable();
};
if($('execLine')) $('execLine').onchange=applyExecutiveFilterToTable;
if($('execType')) $('execType').onchange=()=>{
  document.querySelectorAll('.equipmentBig').forEach(x=>x.classList.toggle('active',x.dataset.type===$('execType').value));
  updateExecutiveView();
};
if($('execReset')) $('execReset').onclick=()=>{
  $('execCompany').value='';
  renderExecutiveFilters();
  $('execLine').value='';
  $('execType').value='';
  document.querySelectorAll('.equipmentBig').forEach(x=>x.classList.remove('active'));
  applyExecutiveFilterToTable();
};
document.querySelectorAll('.equipmentBig').forEach(card=>card.onclick=()=>{
  const type=card.dataset.type;
  $('execType').value=$('execType').value===type?'':type;
  document.querySelectorAll('.equipmentBig').forEach(x=>x.classList.toggle('active',x.dataset.type===$('execType').value));
  updateExecutiveView();
});

function exportExecutiveExcel(){
  const params=new URLSearchParams();
  const company=$('execCompany')?.value||'';
  const line=$('execLine')?.value||'';
  const type=$('execType')?.value||'';
  if(company) params.set('company',company);
  if(line) params.set('line',line);
  if(type) params.set('type',type);
  window.location.href='/api/export/excel'+(params.toString()?'?'+params.toString():'');
}
if($('exportExecutive')) $('exportExecutive').onclick=exportExecutiveExcel;


async function loadFieldEvidenceSummary(){
  try{
    const r=await fetch('/api/evidencias-campo/resumo',{cache:'no-store'});
    if(!r.ok) return;
    const d=await r.json();
    if($('evVisits')) $('evVisits').textContent=fmt(d.visits||0);
    if($('evItems')) $('evItems').textContent=fmt(d.items||0);
    if($('evMatched')) $('evMatched').textContent=fmt(d.matched||0);
    if($('evReview')) $('evReview').textContent=fmt(d.review||0);
    if($('evMedia')) $('evMedia').textContent=fmt(d.media||0);
  }catch(_err){}
}

loadAll();
setInterval(loadAll,120000);