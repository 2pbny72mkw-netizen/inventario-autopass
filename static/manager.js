window.AUTOPASS_MANAGER_VERSION='dashboard-v36-0';
console.log('AUTOPASS Dashboard Executivo V25 carregado');
let locations=[];
let dashboardData=null;
const $=id=>document.getElementById(id);
const uniq=a=>[...new Set(a)].sort((x,y)=>x.localeCompare(y,'pt-BR'));
function st(s){return `<span class="status s${s.replaceAll(' ','')}">${s}</span>`}
function fmt(n){return new Intl.NumberFormat('pt-BR').format(Number(n||0))}
function esc(v){return String(v??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'","&#039;")}

const OFFICIAL_EXEC_TYPES=['ATM','VALIDADOR','POS','BLOQUEIO'];
const DASHBOARD_DISPLAY_TYPES=['ATM','VALIDADOR','POS','TDI','BLOQUEIO','OUTRO'];
function typeLabel(type){
  return type==='VALIDADOR'?'Recarga':type==='BLOQUEIO'?'Bloqueio':type==='OUTRO'?'Outro':type;
}
function technicalTdiExpected(){
  return Number(
    dashboardData?.technical_tdi?.expected ??
    dashboardData?.official_park?.technical_tdi ??
    (dashboardData?.by_type||[]).find(x=>x.type==='TDI')?.expected ??
    80
  );
}
function sumObjectValues(obj){return Object.values(obj||{}).reduce((a,b)=>a+Number(b||0),0)}
function filteredLocationMetrics(rows,type=''){
  const result={
    expected:0,inventoried:0,missing:0,inoperative:0,divergences:0,
    byType:{ATM:{e:0,i:0},VALIDADOR:{e:0,i:0},POS:{e:0,i:0},TDI:{e:0,i:0},BLOQUEIO:{e:0,i:0},OUTRO:{e:0,i:0}}
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
    // V36: TDI técnico tem uma única fonte executiva (80 por padrão),
    // independentemente de quantos TDI estejam distribuídos por localidade na base detalhada.
    if(type==='TDI' && !($('execCompany')?.value||'') && !($('execLine')?.value||'')){
      result.expected=technicalTdiExpected();
    }
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

// V35.1 — geometria de contingência para linhas que ainda não possuem referências
// geográficas suficientes cadastradas no banco. É usada somente para desenho da linha.
const railFallbackGeometry={
  '4':[
    [-23.5362,-46.6335],[-23.5441,-46.6422],[-23.5489,-46.6520],[-23.5553,-46.6620],
    [-23.5608,-46.6719],[-23.5662,-46.6840],[-23.5673,-46.6930],[-23.5669,-46.7012],
    [-23.5718,-46.7080],[-23.5864,-46.7230],[-23.5944,-46.7330]
  ],
  '17':[
    [-23.6217,-46.7012],[-23.6222,-46.6947],[-23.6209,-46.6878],[-23.6201,-46.6800],
    [-23.6210,-46.6732],[-23.6241,-46.6670],[-23.6288,-46.6633],[-23.6328,-46.6603]
  ]
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

  // V35 — controle nativo do Leaflet: permanece visível mesmo quando o cabeçalho do mapa é ocultado.
  const fullscreenControl=L.control({position:'topright'});
  fullscreenControl.onAdd=()=>{
    const wrap=L.DomUtil.create('div','leaflet-bar autopassMapFullscreenControl');
    const btn=L.DomUtil.create('button','autopassMapFullscreenBtn',wrap);
    btn.type='button'; btn.title='Abrir mapa em tela cheia'; btn.setAttribute('aria-label','Abrir mapa em tela cheia');
    btn.innerHTML='⛶ <span>Tela cheia</span>';
    L.DomEvent.disableClickPropagation(wrap);
    L.DomEvent.on(btn,'click',ev=>{L.DomEvent.stop(ev);setMapFullscreen(!$('gpsMap')?.classList.contains('gpsMapFullscreen'));});
    return wrap;
  };
  fullscreenControl.addTo(gpsMap);

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

  // Garante que 4-Amarela e 17-Ouro sejam desenhadas mesmo antes de todas as referências
  // oficiais dessas estações serem cadastradas no banco.
  ['4','17'].forEach(number=>{ if(!groups[number]) groups[number]=[]; });

  Object.entries(groups).forEach(([number,stations])=>{
    const sequence=stations.length>=2?buildRailSequence(stations):[];
    const fallback=railFallbackGeometry[number]||[];
    const coordinates=sequence.length>=2?sequence.map(x=>[
      Number(x.reference_latitude),Number(x.reference_longitude)
    ]):fallback;
    if(coordinates.length<2) return;
    const color=railColorsByNumber[number]||'#64748b';

    // Halo branco: aumenta contraste sobre o mapa-base.
    L.polyline(coordinates,{
      color:'#ffffff',weight:11,opacity:.96,lineCap:'round',lineJoin:'round',interactive:false
    }).addTo(railLineLayer);

    const polyline=L.polyline(coordinates,{
      color,weight:7,opacity:1,lineCap:'round',lineJoin:'round'
    }).addTo(railLineLayer);

    polyline.bindPopup(`<b>Linha ${esc(number)} — ${esc(railNamesByNumber[number]||'')}</b><br>${stations.length} estação(ões) com referência geográfica${sequence.length<2?' · traçado de contingência':''}`);

    // Número da linha nas duas pontas do traçado.
    const endpoints=sequence.length>=2
      ? [[Number(sequence[0].reference_latitude),Number(sequence[0].reference_longitude)],[Number(sequence[sequence.length-1].reference_latitude),Number(sequence[sequence.length-1].reference_longitude)]]
      : [coordinates[0],coordinates[coordinates.length-1]];
    endpoints.forEach(point=>{
      if(!point) return;
      const icon=L.divIcon({
        className:'rail-line-end-icon',
        html:`<div class="rail-line-number" style="background:${color}">${esc(number)}</div>`,
        iconSize:[30,30],iconAnchor:[15,15]
      });
      L.marker(point,{icon,interactive:false}).addTo(railLineLayer);
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
      html:`<div class="gpsTechAvatar" style="outline:3px solid ${color}">${x.technician_photo_url?`<img src="${esc(x.technician_photo_url)}" alt="">`:`<span>${esc(techInitials)}</span>`}</div>`,
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


async function setMapFullscreen(on){
  const mapEl=$('gpsMap'); if(!mapEl)return;
  const root=document.documentElement;
  if(on){
    mapEl.classList.add('gpsMapFullscreen');
    document.body.classList.add('mapFullscreenOpen');
    try{
      if(!document.fullscreenElement && !document.webkitFullscreenElement){
        if(root.requestFullscreen) await root.requestFullscreen();
        else if(root.webkitRequestFullscreen) await root.webkitRequestFullscreen();
      }
    }catch(_e){
      // O overlay fixo continua funcional mesmo se o navegador bloquear a Fullscreen API.
    }
  }else{
    try{
      if(document.fullscreenElement && document.exitFullscreen) await document.exitFullscreen();
      else if(document.webkitFullscreenElement && document.webkitExitFullscreen) await document.webkitExitFullscreen();
    }catch(_e){}
    mapEl.classList.remove('gpsMapFullscreen');
    document.body.classList.remove('mapFullscreenOpen');
  }
  const active=mapEl.classList.contains('gpsMapFullscreen');
  const text=active?'✕ Sair da tela cheia':'⛶ Tela cheia';
  if($('toggleMapFullscreenBtn')) $('toggleMapFullscreenBtn').textContent=text;
  const leafletBtn=document.querySelector('.autopassMapFullscreenBtn');
  if(leafletBtn) leafletBtn.innerHTML=active?'✕ <span>Sair da tela cheia</span>':'⛶ <span>Tela cheia</span>';
  requestAnimationFrame(()=>setTimeout(()=>{try{gpsMap?.invalidateSize()}catch(_e){}},80));
}

function syncMapFullscreenState(){
  const mapEl=$('gpsMap'); if(!mapEl)return;
  const nativeActive=!!(document.fullscreenElement||document.webkitFullscreenElement);
  if(!nativeActive && mapEl.classList.contains('gpsMapFullscreen')){
    mapEl.classList.remove('gpsMapFullscreen');
    document.body.classList.remove('mapFullscreenOpen');
  }
  const active=mapEl.classList.contains('gpsMapFullscreen');
  const leafletBtn=document.querySelector('.autopassMapFullscreenBtn');
  if(leafletBtn) leafletBtn.innerHTML=active?'✕ <span>Sair da tela cheia</span>':'⛶ <span>Tela cheia</span>';
  if($('toggleMapFullscreenBtn')) $('toggleMapFullscreenBtn').textContent=active?'✕ Sair da tela cheia':'⛶ Tela cheia';
  requestAnimationFrame(()=>setTimeout(()=>{try{gpsMap?.invalidateSize()}catch(_e){}},80));
}
document.addEventListener('fullscreenchange',syncMapFullscreenState);
document.addEventListener('webkitfullscreenchange',syncMapFullscreenState);

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
function renderTypeBigNumbers(rows){ rows.forEach(x=>{ const id=x.type; if($('type'+id)) $('type'+id).textContent=fmt(id==='OUTRO'?x.inventoried:x.expected); if($('type'+id+'Detail')) $('type'+id+'Detail').textContent=id==='OUTRO'?`${fmt(x.inventoried)} encontrado(s) fora da base`:`${fmt(x.inventoried)} levantados · ${fmt(x.missing)} faltam · ${x.coverage_pct}%`; }); const other=locations.reduce((n,x)=>n+Number((x.inventoried_by_type||{}).OUTRO||0),0); if($('typeOUTRO'))$('typeOUTRO').textContent=fmt(other); if($('typeOUTRODetail'))$('typeOUTRODetail').textContent=`${fmt(other)} encontrado(s) fora da base`; }
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
  const types=type?[type]:DASHBOARD_DISPLAY_TYPES;
  $('analyticsTypes').innerHTML=types.map(t=>{const z=m.byType[t]||{e:0,i:0};const p=z.e?Math.min(100,Math.round(z.i/z.e*100)):0;return `<div class="analyticsTypeRow"><b>${esc(typeLabel(t))}</b><div class="track"><i style="width:${p}%"></i></div><span>${p}%</span></div>`}).join('');
  const dynamicRows=DASHBOARD_DISPLAY_TYPES.map(t=>{const z=m.byType[t]||{e:0,i:0};return {type:t,expected:z.e,inventoried:z.i,missing:Math.max(0,z.e-z.i),coverage_pct:z.e?Math.round(z.i/z.e*1000)/10:0}});
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
  const types=type?[type]:DASHBOARD_DISPLAY_TYPES;
  $('v21TypeBars').innerHTML=types.map(t=>{
    const z=m.byType[t]||{e:0,i:0}, p=z.e?Math.min(100,Math.round(z.i/z.e*100)):0;
    return `<div class="v21BarRow"><div><b>${esc(typeLabel(t))}</b><span>${t==='OUTRO'?fmt(z.i)+' encontrado(s)':fmt(z.i)+'/'+fmt(z.e)}</span></div><div class="v21BarTrack"><i style="width:${t==='OUTRO'?(z.i?100:0):p}%"></i></div><strong>${t==='OUTRO'?(z.i?'fora base':'0'):p+'%'}</strong></div>`;
  }).join('');
  const priorities=rows.map(x=>{
    const exp=type?Number((x.expected_by_type||{})[type]||0):OFFICIAL_EXEC_TYPES.reduce((a,t)=>a+Number((x.expected_by_type||{})[t]||0),0);
    const inv=type?Number((x.inventoried_by_type||{})[type]||0):OFFICIAL_EXEC_TYPES.reduce((a,t)=>a+Number((x.inventoried_by_type||{})[t]||0),0);
    return {...x,_missing:Math.max(0,exp-inv)};
  }).filter(x=>x._missing>0).sort((a,b)=>b._missing-a._missing).slice(0,6);
  const max=Math.max(1,...priorities.map(x=>x._missing));
  $('v21PriorityBars').innerHTML=priorities.length?priorities.map((x,i)=>`<div class="v21PriorityRow"><span class="rank">${i+1}</span><div class="who"><b>${esc(x.location)}</b><small>${esc(x.company)} · ${esc(x.line)}</small><div class="v21PriorityTrack"><i style="width:${Math.round(x._missing/max*100)}%"></i></div></div><strong>${fmt(x._missing)}</strong></div>`).join(''):'<div class="muted">Nenhuma pendência no recorte atual.</div>';  const overviewTypes=document.getElementById('v344TypeBars'); if(overviewTypes) overviewTypes.innerHTML=$('v21TypeBars').innerHTML;
  const overviewPriorities=document.getElementById('v344PriorityBars'); if(overviewPriorities) overviewPriorities.innerHTML=$('v21PriorityBars').innerHTML;
}


function renderV22Cockpit(){
  if(!dashboardData||!$('v22ExecutiveCockpit')) return;
  const trend=dashboardData.trend_14d||[]; const max=Math.max(1,...trend.map(x=>Number(x.count||0)));
  $('v22Trend').innerHTML=trend.map(x=>{const h=Math.max(4,Math.round(Number(x.count||0)/max*100)); const d=new Date(x.date+'T12:00:00'); return `<div class="v22TrendCol"><b>${fmt(x.count||0)}</b><i style="height:${h}%"></i><small>${String(d.getDate()).padStart(2,'0')}/${String(d.getMonth()+1).padStart(2,'0')}</small></div>`}).join('');
  const tech=dashboardData.top_technicians_14d||[]; const tmax=Math.max(1,...tech.map(x=>Number(x.count||0)));
  $('v22Productivity').innerHTML=tech.length?tech.map((x,i)=>`<div class="v22ProdRow"><span>${i+1}</span><div><b>${esc(x.name)}</b><div class="v22ProdTrack"><i style="width:${Math.round(Number(x.count||0)/tmax*100)}%"></i></div></div><strong>${fmt(x.count||0)}</strong></div>`).join(''):'<div class="muted">Sem lançamentos nos últimos 14 dias.</div>';
  const e=dashboardData.evidence||{}; const total=Number(e.items||0), matched=Number(e.matched||0), review=Number(e.review||0), media=Number(e.media||0);
  const conf=total?Math.round(matched/total*100):0;
  $('v22EvidenceQuality').innerHTML=`<div class="v22EvidenceHero"><b>${conf}%</b><span>itens conciliados</span></div><div class="v22EvidenceRows"><span>Visitas <b>${fmt(e.visits||0)}</b></span><span>Itens <b>${fmt(total)}</b></span><span>Revisar <b>${fmt(review)}</b></span><span>Fotos/vídeos <b>${fmt(media)}</b></span></div>`;
}

function renderV36Productivity(){
  if(!dashboardData||!$('v36ProductivityStrip')) return;
  const trend=dashboardData.trend_14d||[];
  const total14=trend.reduce((a,x)=>a+Number(x.count||0),0);
  const last7=trend.slice(-7);
  const total7=last7.reduce((a,x)=>a+Number(x.count||0),0);
  const pace=last7.length?total7/last7.length:0;
  const tech=dashboardData.top_technicians_14d||[];
  const top=tech[0]||null;
  if($('v36Prod14')) $('v36Prod14').textContent=fmt(total14);
  if($('v36Pace7')) $('v36Pace7').textContent=`${pace.toFixed(1).replace('.',',')}/dia`;
  if($('v36ActiveTechs')) $('v36ActiveTechs').textContent=fmt(tech.length);
  if($('v36TopTech')) $('v36TopTech').textContent=top?top.name:'—';
  if($('v36TopTechDetail')) $('v36TopTechDetail').textContent=top?`${fmt(top.count)} lançamento(s) nos últimos 14 dias`:'sem produção recente';
}


function renderV25ExecutiveBI(){
  if(!dashboardData||!$('v25BiArena')) return;
  const trend=dashboardData.trend_14d||[], max=Math.max(1,...trend.map(x=>Number(x.count||0)));
  $('v25TrendChart').innerHTML=trend.map(x=>{const n=Number(x.count||0),h=Math.max(3,Math.round(n/max*100));const d=new Date(x.date+'T12:00:00');return `<i class="v25TrendBar" style="height:${h}%" data-tip="${String(d.getDate()).padStart(2,'0')}/${String(d.getMonth()+1).padStart(2,'0')} · ${fmt(n)}"></i>`}).join('');
  const prev=trend.slice(0,7).reduce((a,x)=>a+Number(x.count||0),0), now=trend.slice(7).reduce((a,x)=>a+Number(x.count||0),0);
  const delta=prev?Math.round((now-prev)/prev*100):(now?100:0); $('v25TrendDelta').textContent=(delta>=0?'▲ ':'▼ ')+Math.abs(delta)+'% vs 7d ant.';
  const exp=Number(dashboardData.totals?.expected||0), inv=Number(dashboardData.inventory?.official_inventoried||0), pct=exp?Math.min(100,Math.round(inv/exp*100)):0;
  $('v25MixPct').textContent=pct+'%'; $('v25MixDonut').style.setProperty('--pct',pct+'%');
  const types=(dashboardData.by_type||[]).filter(x=>x.type!=='TDI'); $('v25MixLegend').innerHTML=types.map(x=>`<span>${esc(typeLabel(x.type))}<b>${fmt(x.inventoried||0)}</b></span>`).join('');
  const companies=(dashboardData.by_company||[]).slice().sort((a,b)=>Number(b.completed||0)-Number(a.completed||0)).slice(0,7), cmax=Math.max(1,...companies.map(x=>Number(x.total||0)));
  $('v25CompanyCompare').innerHTML=companies.length?companies.map(x=>{const done=Number(x.completed||0),tot=Number(x.total||0),p=tot?Math.round(done/tot*100):0;return `<div class="v25CompanyRow"><span>${esc(x.company||'—')}</span><div class="v25CompanyTrack"><i style="width:${p}%"></i></div><b>${p}%</b></div>`}).join(''):'<span class="muted">Sem dados por empresa.</span>';
  const e=dashboardData.evidence||{}; $('v25Attention').innerHTML=`<article><b>${fmt(dashboardData.inventory?.divergences||0)}</b><span>Divergências</span></article><article><b>${fmt(dashboardData.inventory?.inoperative||0)}</b><span>Inoperantes</span></article><article><b>${fmt(e.review||0)}</b><span>Evidências a revisar</span></article><article><b>${fmt(e.unresolved_visits||0)}</b><span>Visitas sem vínculo</span></article>`;
  const comp=e.competition||{}; $('v25CompetitionTotal').textContent=fmt(e.competition_total||0); const entries=Object.entries(comp).sort((a,b)=>b[1]-a[1]), m=Math.max(1,...entries.map(x=>Number(x[1]||0)));
  $('v25CompetitionBars').innerHTML=entries.length?entries.map(([k,v])=>`<div class="v25CompanyRow"><span>${esc(k)}</span><div class="v25CompanyTrack"><i style="width:${Math.round(Number(v)/m*100)}%"></i></div><b>${fmt(v)}</b></div>`).join(''):'<div class="muted">Nenhuma quantidade estruturada de concorrência encontrada nas evidências importadas.</div>';
}

function updateExecutiveView(){
  if(!dashboardData) return;
  renderV25ExecutiveBI();
  renderV29CommandCenter();
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
  renderV22Cockpit();
  renderV36Productivity();
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

// V23 — navegação lateral e primeiro Modo TV
let v23ActiveView='overview';
let v23TvTimer=null;
const V23_TV_VIEWS=['overview','execution','competition','quality','map','evidence','ranking'];
function v23SetView(view){
  v23ActiveView=view||'overview';
  document.body.dataset.dashboardView=v23ActiveView;
  document.body.dataset.dashboardView=v23ActiveView;
  document.querySelectorAll('.v23Panel').forEach(el=>{
    const active=String(el.dataset.v23Panel||'').split(/\s+/).includes(v23ActiveView);
    el.classList.toggle('v23PanelActive',active);
    el.hidden=!active;
  });
  document.querySelectorAll('.v23Nav').forEach(btn=>btn.classList.toggle('active',btn.dataset.v23View===v23ActiveView));
  document.querySelectorAll('.executiveFilterBar.v23Shared').forEach(el=>{el.hidden=(v23ActiveView==='chips');});
  if(v23ActiveView==='map' && gpsMap) setTimeout(()=>gpsMap.invalidateSize(),140);
  window.scrollTo({top:0,behavior:document.body.classList.contains('v23TvMode')?'auto':'smooth'});
}
function v343SyncTv(){
  const txt=(id,fallback='—')=>document.getElementById(id)?.textContent?.trim()||fallback;
  const set=(id,val)=>{const e=document.getElementById(id);if(e)e.textContent=val;};
  set('tvExpected',txt('expected','0')); set('tvInventoried',txt('inventoried','0')); set('tvMissing',txt('missing','0'));
  set('tvCoverage',txt('assetCoverageTop','0%')); set('tvPace',txt('v29Pace','0/dia')); set('tvProjection',txt('v29Projection','—'));
  set('v343TvDonutPct',txt('assetCoverageTop','0%')); set('v343TvProgressText',txt('v29ProgressText',''));
  set('v343TvHeadline',txt('v29Headline','Monitoramento executivo do inventário.'));
  const pct=parseFloat((txt('assetCoverageTop','0').replace(',','.')))||0;
  const donut=document.getElementById('v343TvDonut'); if(donut)donut.style.setProperty('--tvpct',Math.max(0,Math.min(100,pct))+'%');
  const clone=(from,to)=>{const a=document.getElementById(from),b=document.getElementById(to);if(a&&b)b.innerHTML=a.innerHTML;};
  clone('v34Trend','v343TvTrend'); clone('v21TypeBars','v343TvTypes'); clone('v21PriorityBars','v343TvPriority');
  const t=document.getElementById('v343TvTime'); if(t)t.textContent=new Date().toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'});
  const u=document.getElementById('v343TvUpdated'); if(u)u.textContent='Atualizado '+new Date().toLocaleDateString('pt-BR')+' · '+new Date().toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'});
}
function v23StopTv(){
  if(v23TvTimer){clearInterval(v23TvTimer);v23TvTimer=null;}
  document.body.classList.remove('v23TvMode');
  const overlay=document.getElementById('v343TvOverlay'); if(overlay){overlay.classList.remove('active');overlay.setAttribute('aria-hidden','true');}
  const btn=$('v23TvBtn'); if(btn) btn.querySelector('span').textContent='Modo TV';
}
function v23StartTv(){
  const overlay=document.getElementById('v343TvOverlay'); if(!overlay)return;
  v343SyncTv();
  overlay.classList.add('active'); overlay.setAttribute('aria-hidden','false'); document.body.classList.add('v23TvMode');
  const btn=$('v23TvBtn'); if(btn) btn.querySelector('span').textContent='Sair da TV';
  const target=overlay;
  if(target.requestFullscreen && !document.fullscreenElement){target.requestFullscreen().catch(()=>{});}
  v23TvTimer=setInterval(v343SyncTv,5000);
}
function initV23DashboardNav(){
  document.querySelectorAll('.v23Nav').forEach(btn=>btn.addEventListener('click',()=>v23SetView(btn.dataset.v23View)));
  $('v23TvBtn')?.addEventListener('click',()=>{ window.open('/gerencial/tv','_blank','noopener'); });
  document.addEventListener('fullscreenchange',()=>{if(!document.fullscreenElement && document.body.classList.contains('v23TvMode'))v23StopTv();});
  v23SetView('overview');
}

initV23DashboardNav();
loadAll();
setInterval(loadAll,120000);
function renderV29CommandCenter(){
 if(!dashboardData)return;
 const t=dashboardData.totals||{}, inv=dashboardData.inventory||{};
 const expected=Number(t.expected||0), done=Number(inv.official_inventoried||0), missing=Math.max(0,expected-done), pct=expected?Math.min(100,done/expected*100):0;
 if($('v29Progress'))$('v29Progress').textContent=`${pct.toFixed(1)}%`;
 if($('v29ProgressBar'))$('v29ProgressBar').style.width=`${pct}%`;
 if($('v29ProgressText'))$('v29ProgressText').textContent=`${fmt(done)} de ${fmt(expected)} ativos oficiais conciliados`;
 const trend=dashboardData.trend_14d||[], prev=trend.slice(0,7).reduce((a,x)=>a+Number(x.count||0),0), now=trend.slice(7).reduce((a,x)=>a+Number(x.count||0),0), pace=now/7;
 if($('v29Pace'))$('v29Pace').textContent=`${pace.toFixed(1).replace('.',',')}/dia`;
 const delta=prev?((now-prev)/prev*100):null;
 if($('v29PaceDelta'))$('v29PaceDelta').textContent=delta===null?'Primeira janela comparável':`${delta>=0?'▲':'▼'} ${Math.abs(delta).toFixed(1).replace('.',',')}% vs. 7 dias anteriores`;
 if($('v29Trend'))$('v29Trend').textContent=delta===null?'—':delta>=5?'ACELERANDO':delta<=-5?'DESACELERANDO':'ESTÁVEL';
 if($('v29Projection'))$('v29Projection').textContent=pace>0?`${Math.ceil(missing/pace)} dias`:'—';
 if($('v29ProjectionSmall'))$('v29ProjectionSmall').textContent=pace>0?`${fmt(missing)} pendentes ao ritmo dos últimos 7 dias`:'Sem ritmo recente para projeção';
 const div=Number(inv.divergences||0), ino=Number(inv.inoperative||0);
 let headline=`Cobertura ${pct.toFixed(1).replace('.',',')}% · ${fmt(missing)} ativos oficiais ainda pendentes.`;
 if(div||ino) headline+=` Atenção: ${fmt(div)} divergência(s) e ${fmt(ino)} inoperante(s).`;
 if($('v29Headline'))$('v29Headline').textContent=headline;
}


// V30 — gestão contratual ATM
async function loadV30Contracts(){
  const box=document.getElementById('v30ContractBars'); if(!box) return;
  const company=document.getElementById('execCompany')?.value||'';
  const line=document.getElementById('execLine')?.value||'';
  const contract=document.getElementById('v30Contract')?.value||'';
  const horizon=document.getElementById('v30Horizon')?.value||'';
  try{
    const r=await fetch(`/api/v30/atm-contracts?company=${encodeURIComponent(company)}&line=${encodeURIComponent(line)}&contract=${encodeURIComponent(contract)}&horizon=${encodeURIComponent(horizon)}`,{cache:'no-store'});
    const d=await r.json(); if(!r.ok) throw new Error(d.error||'Falha');
    const sel=document.getElementById('v30Contract'); const before=sel.value;
    const opts=['<option value="">Todos</option>',...(d.contracts||[]).map(x=>`<option value="${esc(x)}">${esc(x)}</option>`)]; sel.innerHTML=opts.join(''); if([...sel.options].some(o=>o.value===before))sel.value=before;
    document.getElementById('v30ContractCount').textContent=fmt(d.count||0);
    const risk=(d.assets||[]).filter(x=>['VENCIDO','ATÉ 30 DIAS','31–60 DIAS','61–90 DIAS'].includes(x.contract_status)).length;
    document.getElementById('v30ContractRisk').textContent=fmt(risk);
    const groups={}; (d.assets||[]).forEach(x=>groups[x.contract_status]=(groups[x.contract_status]||0)+1); const max=Math.max(1,...Object.values(groups));
    box.innerHTML=Object.entries(groups).map(([k,v])=>`<div class="v30ContractRow"><span>${esc(k)}</span><div><i style="width:${Math.round(v/max*100)}%"></i></div><b>${fmt(v)}</b></div>`).join('')||'<span class="muted">Nenhum ATM no recorte.</span>';
  }catch(err){box.innerHTML='<span class="muted">Não foi possível carregar contratos ATM.</span>'}
}
['v30Contract','v30Horizon'].forEach(id=>document.getElementById(id)?.addEventListener('change',loadV30Contracts));
['execCompany','execLine'].forEach(id=>document.getElementById(id)?.addEventListener('change',()=>setTimeout(loadV30Contracts,50)));
document.getElementById('v30ContractExport')?.addEventListener('click',()=>{
 const p=new URLSearchParams({company:document.getElementById('execCompany')?.value||'',line:document.getElementById('execLine')?.value||'',contract:document.getElementById('v30Contract')?.value||'',horizon:document.getElementById('v30Horizon')?.value||''}); location.href='/api/v30/atm-contracts/export?'+p.toString();
});
setTimeout(loadV30Contracts,800);


// V35 — visão geral operacional filtrável
function renderV35Overview(){
  if(!dashboardData||!document.getElementById('v34Radial')) return;
  const rows=executiveFilteredLocations();
  const type=document.getElementById('execType')?.value||'';
  const company=document.getElementById('execCompany')?.value||'';
  const line=document.getElementById('execLine')?.value||'';
  const metrics=filteredLocationMetrics(rows,type);
  const noGeoFilters=!company&&!line;
  // V36: TDI técnico usa a fonte única exposta pela API do dashboard.
  if(noGeoFilters && type==='TDI'){
    const tdiExpected=technicalTdiExpected();
    const tdiInventoried=Number(dashboardData?.technical_tdi?.inventoried ?? (dashboardData.by_type||[]).find(x=>x.type==='TDI')?.inventoried ?? metrics.inventoried ?? 0);
    metrics.expected=tdiExpected;
    metrics.inventoried=tdiInventoried;
    metrics.missing=Math.max(0,tdiExpected-tdiInventoried);
    metrics.byType.TDI.e=tdiExpected;
    metrics.byType.TDI.i=tdiInventoried;
  }

  // Cobertura: usa exatamente o mesmo recorte dos Big Numbers.
  const exp=Number(metrics.expected||0), done=Number(metrics.inventoried||0);
  const pct=exp?Math.min(100,done/exp*100):0;
  document.getElementById('v34Radial').style.setProperty('--pct',pct.toFixed(1)+'%');
  document.getElementById('v34RadialPct').textContent=pct.toFixed(1).replace('.',',')+'%';
  document.getElementById('v34RadialText').textContent=`${fmt(done)} de ${fmt(exp)} ativos no recorte`;

  // Status das localidades — responde aos filtros Empresa/Linha/Tipo.
  const countStatus=status=>rows.filter(x=>String(x.survey_status||'').toUpperCase()===status).length;
  const completed=countStatus('CONCLUIDA'), progress=countStatus('EM ANDAMENTO'), pending=countStatus('PENDENTE');
  const total=rows.length||0, denominator=Math.max(1,total);
  const cp=completed/denominator*100, pp=progress/denominator*100, pendp=pending/denominator*100;
  const setText=(id,val)=>{const e=document.getElementById(id);if(e)e.textContent=val;};
  setText('v35Completed',fmt(completed)); setText('v35Progress',fmt(progress)); setText('v35Pending',fmt(pending));
  setText('v35CompletedPct',Math.round(cp)+'%'); setText('v35ProgressPct',Math.round(pp)+'%'); setText('v35PendingPct',Math.round(pendp)+'%');
  setText('v35LocationsTotal',`${fmt(total)} localidade(s) no recorte`);
  setText('v35StatusContext',[company||'Todas empresas',line||'Todas linhas',type?typeLabel(type):'Todos os tipos'].join(' · '));
  const doneBar=document.getElementById('v35StatusDone'), progBar=document.getElementById('v35StatusProgress'), pendBar=document.getElementById('v35StatusPending');
  if(doneBar)doneBar.style.width=cp+'%'; if(progBar)progBar.style.width=pp+'%'; if(pendBar)pendBar.style.width=pendp+'%';

  // Mix do parque — quando não há recorte geográfico usa os mesmos denominadores oficiais
  // dos Big Numbers. TDI e Outro não compõem o parque oficial de 3.801 ativos.
  const officialMap={}; (dashboardData.by_type||[]).forEach(x=>officialMap[x.type]=Number(x.expected||0));
  let mix=[];
  if(noGeoFilters){
    const officialTypes=['ATM','VALIDADOR','POS','BLOQUEIO'];
    if(type && officialTypes.includes(type)) mix=[{type,value:Number(officialMap[type]||0)}];
    else if(type==='TDI'){ mix=[{type,value:technicalTdiExpected(),outsideOfficial:true}]; }
    else if(type==='OUTRO'){ const z=metrics.byType.OUTRO||{i:0}; mix=[{type,value:Number(z.i||0),outsideOfficial:true}]; }
    else mix=officialTypes.map(t=>({type:t,value:Number(officialMap[t]||0)})).filter(x=>x.value>0);
  }else{
    const mixTypes=type?[type]:['ATM','VALIDADOR','POS','BLOQUEIO'];
    mix=mixTypes.map(t=>{const z=metrics.byType[t]||{e:0,i:0};return {type:t,value:Number(z.e||0)}}).filter(x=>x.value>0);
  }
  const mixTotal=mix.reduce((a,x)=>a+x.value,0);
  const colors={ATM:'#2878d8',VALIDADOR:'#16b98e',POS:'#ff9f2e',TDI:'#8a63d2',BLOQUEIO:'#16b8b0',OUTRO:'#f4c64d'};
  let cursor=0, stops=[];
  mix.forEach(x=>{const start=cursor;cursor+=mixTotal?x.value/mixTotal*100:0;stops.push(`${colors[x.type]} ${start.toFixed(2)}% ${cursor.toFixed(2)}%`)});
  const donut=document.getElementById('v35MixDonut'); if(donut)donut.style.background=mixTotal?`conic-gradient(${stops.join(',')})`:'#dfe8f1';
  setText('v35MixTotal',fmt(mixTotal));
  const mixLegend=document.getElementById('v35MixLegend');
  if(mixLegend)mixLegend.innerHTML=mix.length?mix.map(x=>`<div><i style="background:${colors[x.type]}"></i><span>${esc(typeLabel(x.type))}</span><b>${fmt(x.value)}</b><small>${mixTotal?Math.round(x.value/mixTotal*100):0}%</small></div>`).join(''):'<div class="muted">Sem ativos no recorte.</div>';

  // Evolução por empresa — distribuição de status, não apenas um percentual isolado.
  const groups={};
  rows.forEach(x=>{const key=x.company||'Não informado';const g=groups[key]||(groups[key]={total:0,completed:0,progress:0,pending:0});g.total++;const st=String(x.survey_status||'').toUpperCase();if(st==='CONCLUIDA')g.completed++;else if(st==='EM ANDAMENTO')g.progress++;else g.pending++;});
  const companies=Object.entries(groups).map(([name,g])=>({name,...g,pct:g.total?Math.round(g.completed/g.total*100):0})).sort((a,b)=>b.pct-a.pct||b.completed-a.completed||b.total-a.total).slice(0,8);
  const companyBox=document.getElementById('v35CompanyBars');
  if(companyBox)companyBox.innerHTML=companies.length?companies.map(g=>{const d=g.total?g.completed/g.total*100:0,pr=g.total?g.progress/g.total*100:0,p=g.total?g.pending/g.total*100:0;return `<div class="v35CompanyRow"><div class="v35CompanyTitle"><b>${esc(g.name)}</b><span>${g.pct}% concluído · ${fmt(g.completed)}/${fmt(g.total)}</span></div><div class="v35CompanyTrack"><i class="done" style="width:${d}%"></i><i class="progress" style="width:${pr}%"></i><i class="pending" style="width:${p}%"></i></div><div class="v35CompanyMeta"><span><i class="dot done"></i>${fmt(g.completed)} concluídas</span><span><i class="dot progress"></i>${fmt(g.progress)} andamento</span><span><i class="dot pending"></i>${fmt(g.pending)} pendentes</span></div></div>`}).join(''):'<div class="muted">Sem empresas no recorte atual.</div>';

  // Atenção continua gerencial, mas as localidades não iniciadas respeitam o recorte.
  const e=dashboardData.evidence||{}; const alerts=[
    [Number(e.review||0),'Evidências aguardando revisão','evidence'],
    [pending,'Localidades pendentes no recorte','ranking'],
    [progress,'Localidades em andamento','execution'],
    [Number(metrics.divergences||0),'Divergências com a base','quality'],
    [Number(metrics.inoperative||0),'Equipamentos inoperantes','quality']
  ].sort((a,b)=>b[0]-a[0]);
  const att=document.getElementById('v34Attention');
  if(att)att.innerHTML=alerts.map(([n,label,view],i)=>`<button type="button" onclick="v23SetView('${view}')"><em>${i+1}</em><span>${esc(label)}</span><b>${fmt(n)}</b></button>`).join('');
}

// Compatibilidade: módulos antigos chamam este nome.
function renderV34Intelligence(){ renderV35Overview(); }

const _v34UpdateExecutiveView=updateExecutiveView; updateExecutiveView=function(){_v34UpdateExecutiveView();renderV34Intelligence();};


// V35 — clique nos status da Visão Geral abre a execução já filtrada por situação.
document.querySelectorAll('.v35Status[data-status]').forEach(btn=>btn.addEventListener('click',()=>{
  const target=btn.dataset.status||'';
  if(document.getElementById('fs')) document.getElementById('fs').value=target;
  try{syncChips();renderLocations();}catch(_e){}
  v23SetView('execution');
}));

async function v39LoadTopdesk(){try{const r=await fetch('/api/topdesk/dashboard',{cache:'no-store'});if(!r.ok)return;const d=await r.json();if(!d.ok)return;const map={v39TdTotal:d.total,v39TdOpen:d.open,v39TdResolved:d.resolved,v39TdAssigned:d.assigned,v39TdUnassigned:d.unassigned};Object.entries(map).forEach(([id,v])=>{const e=document.getElementById(id);if(e)e.textContent=fmt(v)});const types=document.getElementById('v39TdTypes');if(types){const arr=Object.entries(d.by_type||{}).sort((a,b)=>b[1]-a[1]);const m=Math.max(1,...arr.map(x=>x[1]));types.innerHTML=arr.map(([k,v])=>`<div class="v25CompanyRow"><span>${esc(k)}</span><div class="v25CompanyTrack"><i style="width:${Math.round(v/m*100)}%"></i></div><b>${fmt(v)}</b></div>`).join('')||'<span class="muted">Sem chamados importados.</span>'}const loc=document.getElementById('v39TdLocations');if(loc){const arr=d.top_locations||[];const m=Math.max(1,...arr.map(x=>x.count));loc.innerHTML=arr.map(x=>`<div class="v25CompanyRow"><span>${esc(x.name)}</span><div class="v25CompanyTrack"><i style="width:${Math.round(x.count/m*100)}%"></i></div><b>${fmt(x.count)}</b></div>`).join('')||'<span class="muted">Sem localidades vinculadas.</span>'}}catch(e){console.warn('TopDesk dashboard',e)}}
document.addEventListener('DOMContentLoaded',v39LoadTopdesk);

// V40.1.3 — Visões panorâmicas com status, progresso e filtros no Dashboard.
let dashPanData=[];
const dashPanEsc=v=>String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));
function dashPanFiltered(includeStatus=true){
  const c=document.getElementById('dashPanCompany')?.value||'';
  const l=document.getElementById('dashPanLine')?.value||'';
  const st=document.getElementById('dashPanStatus')?.value||'';
  return dashPanData.filter(x=>(!c||x.company===c)&&(!l||x.line===l)&&(!includeStatus||!st||x.status===st));
}
function dashPanFill(id,vals,label){const e=document.getElementById(id);if(!e)return;const cur=e.value;e.innerHTML=`<option value="">${label}</option>`+[...new Set(vals.filter(Boolean))].sort((a,b)=>String(a).localeCompare(String(b),'pt-BR')).map(v=>`<option value="${dashPanEsc(v)}">${dashPanEsc(v)}</option>`).join('');if([...e.options].some(o=>o.value===cur))e.value=cur}
function dashPanRenderSummary(){
  const a=dashPanFiltered(true), total=a.length;
  const done=a.filter(x=>x.status==='CONCLUÍDA').length;
  const progress=a.filter(x=>x.status==='EM ANDAMENTO').length;
  const pending=a.filter(x=>x.status==='PENDENTE').length;
  const photos=a.reduce((n,x)=>n+Number(x.photo_count||0),0);
  const pct=n=>total?Math.round(n*1000/total)/10:0;
  const set=(id,v)=>{const e=document.getElementById(id);if(e)e.textContent=v};
  set('dashPanTotal',total);set('dashPanPending',pending);set('dashPanInProgress',progress);set('dashPanDone',done);set('dashPanPhotos',photos);
  set('dashPanPendingPct',pct(pending)+'%');set('dashPanInProgressPct',pct(progress)+'%');set('dashPanDonePct',pct(done)+'%');set('dashPanPct',pct(done)+'%');
  set('dashPanLegendDone',done);set('dashPanLegendProgress',progress);set('dashPanLegendPending',pending);
  set('dashPanProgressText',`${done} de ${total} localidades concluídas · ${photos} foto(s) registradas.`);
  const donut=document.getElementById('dashPanDonut');if(donut){const d=pct(done),p=pct(progress);donut.style.background=`conic-gradient(#20945b 0 ${d}%, #d58a12 ${d}% ${Math.min(100,d+p)}%, #c93c3c ${Math.min(100,d+p)}% 100%)`}
  const bd=document.getElementById('dashPanBarDone'),bp=document.getElementById('dashPanBarProgress'),bn=document.getElementById('dashPanBarPending');
  if(bd)bd.style.width=pct(done)+'%';if(bp)bp.style.width=pct(progress)+'%';if(bn)bn.style.width=pct(pending)+'%';
}
function dashPanLocations(){
  const a=dashPanFiltered(true),el=document.getElementById('dashPanLocation');if(!el)return;
  const cur=el.value;el.innerHTML='<option value="">Selecione</option>'+a.map(x=>`<option value="${x.id}">${dashPanEsc(x.location)} · ${dashPanEsc(x.status)}</option>`).join('');if([...el.options].some(o=>o.value===cur))el.value=cur;
  if(!el.value){const g=document.getElementById('dashPanGallery');if(g)g.innerHTML='<p class="muted">Selecione uma localidade para visualizar as fotos.</p>'}
  dashPanRenderSummary();
}
function dashPanShow(){const id=+document.getElementById('dashPanLocation')?.value,x=dashPanData.find(a=>a.id===id),g=document.getElementById('dashPanGallery');if(!g)return;if(!x){g.innerHTML='<p class="muted">Selecione uma localidade para visualizar as fotos.</p>';return}const photos=(x.points||[]).flatMap(p=>(p.photos||[]).map(ph=>`<figure><a href="${dashPanEsc(ph.url)}" target="_blank"><img loading="lazy" src="${dashPanEsc(ph.url)}"></a><figcaption><b>${dashPanEsc(p.name)}</b><br>${dashPanEsc(ph.uploaded_by)} · ${new Date(ph.created_at).toLocaleString('pt-BR')}</figcaption></figure>`));g.innerHTML=photos.join('')||`<div class="dashPanEmpty"><b>${dashPanEsc(x.location)}</b><span>${dashPanEsc(x.status)} · nenhuma foto registrada.</span></div>`}
async function dashPanLoad(){try{const r=await fetch('/api/panoramas',{cache:'no-store'});if(!r.ok)throw new Error('HTTP '+r.status);const d=await r.json();dashPanData=d.locations||[];dashPanFill('dashPanCompany',dashPanData.map(x=>x.company),'Todas');dashPanFill('dashPanLine',dashPanData.map(x=>x.line),'Todas');dashPanLocations()}catch(e){console.warn('panorama dashboard',e);const g=document.getElementById('dashPanGallery');if(g)g.innerHTML='<p class="muted">Não foi possível carregar o progresso das visões panorâmicas.</p>'}}
document.getElementById('dashPanCompany')?.addEventListener('change',()=>{const c=document.getElementById('dashPanCompany')?.value||'';dashPanFill('dashPanLine',dashPanData.filter(x=>!c||x.company===c).map(x=>x.line),'Todas');dashPanLocations()});
document.getElementById('dashPanLine')?.addEventListener('change',dashPanLocations);document.getElementById('dashPanStatus')?.addEventListener('change',dashPanLocations);document.getElementById('dashPanLocation')?.addEventListener('change',dashPanShow);dashPanLoad();

let chipDashData={locations:[],technicians:[],summary:{}};
function chipDashEsc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function chipDashOperation(company){const t=String(company||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toUpperCase();if(t.includes('CPTM'))return 'CPTM';if(t.includes('METRO'))return 'Metrô';if(t.includes('VIA MOBILIDADE'))return 'Via Mobilidade';if(t.includes('VIAQUATRO')||t.includes('VIA QUATRO'))return 'ViaQuatro';return company||'Outros'}
function chipDashFill(id,vals,label){const e=document.getElementById(id);if(!e)return;const cur=e.value;e.innerHTML=`<option value="">${label}</option>`+[...new Set(vals.filter(Boolean))].sort().map(v=>`<option>${chipDashEsc(v)}</option>`).join('');if([...e.options].some(o=>o.value===cur))e.value=cur}
function v413Norm(s){return String(s??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toUpperCase().replace(/\b(LINHA|METRO|CPTM|VIA|MOBILIDADE|QUATRO)\b/g,' ').replace(/[^A-Z0-9]+/g,' ').replace(/\s+/g,' ').trim()}
function v413LooseMatch(a,b){if(!a||!b)return true;const A=v413Norm(a),B=v413Norm(b);return A===B||A.includes(B)||B.includes(A)}
function chipDashFilteredRows(){
  const op=document.getElementById('chipDashOperation')?.value||'',c=document.getElementById('chipDashCompany')?.value||'',l=document.getElementById('chipDashLine')?.value||'',loc=document.getElementById('chipDashLocation')?.value||'',test=document.getElementById('chipDashTestResult')?.value||'';
  const gc=document.getElementById('execCompany')?.value||'',gl=document.getElementById('execLine')?.value||'',gs=document.getElementById('execStatus')?.value||'',gt=document.getElementById('execType')?.value||'';
  const base=(chipDashData.locations||[]).filter(x=>(!op||chipDashOperation(x.company)===op)&&(!gc||v413LooseMatch(x.company,gc))&&(!gl||v413LooseMatch(x.line,gl))&&(!gt||gt==='VALIDADOR'));
  let rows=base.filter(x=>(!c||x.company===c)&&(!l||x.line===l)&&(!loc||x.location===loc));
  if(gs){rows=rows.map(x=>{const validators=(x.validators||[]).filter(v=>gs==='CONCLUIDA'?v.status==='CONCLUÍDA':gs==='PENDENTE'?v.status==='PENDENTE':gs==='EM ANDAMENTO'?v.status==='EM ANDAMENTO':gs==='SEM REGISTRO'?!v.swap_id:true);return {...x,validators,total:validators.length,concluded:validators.filter(v=>v.status==='CONCLUÍDA').length,in_progress:validators.filter(v=>v.status==='EM ANDAMENTO').length,pending:validators.filter(v=>v.status==='PENDENTE').length,percent:validators.length?Math.round(validators.filter(v=>v.status==='CONCLUÍDA').length/validators.length*100):0}}).filter(x=>x.total)}
  if(test)rows=rows.map(x=>({...x,validators:(x.validators||[]).filter(v=>(v.test_result||'SEM_RESULTADO')===test)})).filter(x=>x.validators.length);
  return {op,c,l,loc,test,base,rows}
}
function chipDashRender(){const f=chipDashFilteredRows(),{c,l,base,rows}=f;chipDashFill('chipDashCompany',base.map(x=>x.company),'Todas');chipDashFill('chipDashLine',base.filter(x=>!c||x.company===c).map(x=>x.line),'Todas');chipDashFill('chipDashLocation',base.filter(x=>(!c||x.company===c)&&(!l||x.line===l)).map(x=>x.location),'Todas');const total=rows.reduce((a,x)=>a+x.total,0),done=rows.reduce((a,x)=>a+x.concluded,0),prog=rows.reduce((a,x)=>a+x.in_progress,0),pend=rows.reduce((a,x)=>a+x.pending,0),pct=total?Math.round(done/total*1000)/10:0;[['chipDashTotal',total],['chipDashDone',done],['chipDashProgressN',prog],['chipDashPending',pend],['chipDashPct',pct+'%'],['chipLegendDone',done],['chipLegendProgress',prog],['chipLegendPending',pend],['chipDonutPct',pct+'%'],['chipDonutTotal',total+' total']].forEach(([i,v])=>{const e=document.getElementById(i);if(e)e.textContent=v});const bar=document.getElementById('chipDashBar');if(bar)bar.style.width=Math.min(pct,100)+'%';[['chipChartDone',done],['chipChartProgress',prog],['chipChartPending',pend]].forEach(([id,n])=>{const e=document.getElementById(id);if(e)e.style.width=(total?(n/total*100):0)+'%'});const donut=document.getElementById('chipDashDonut');if(donut){const d=total?done/total*100:0,p=total?prog/total*100:0;donut.style.background=`conic-gradient(#16824b 0 ${d}%, #d98b00 ${d}% ${d+p}%, #c93b3b ${d+p}% 100%)`}const el=document.getElementById('chipDashLocations');if(el)el.innerHTML=`<table class="chipDashTable"><thead><tr><th>Localidade</th><th>Progresso</th><th>Concl.</th><th>And.</th><th>Pend.</th></tr></thead><tbody>${[...rows].sort((a,b)=>a.percent-b.percent).map(x=>`<tr><td>${chipDashEsc(x.line)} · ${chipDashEsc(x.location)}</td><td><b>${x.percent}%</b></td><td>${x.concluded}/${x.total}</td><td>${x.in_progress}</td><td>${x.pending}</td></tr>`).join('')||'<tr><td colspan="5">Sem dados.</td></tr>'}</tbody></table>`;const oe=document.getElementById('chipDashOperations');if(oe){const ops={};(chipDashData.locations||[]).forEach(x=>{const k=chipDashOperation(x.company),o=ops[k]??={total:0,done:0,prog:0,pend:0};o.total+=x.total;o.done+=x.concluded;o.prog+=x.in_progress;o.pend+=x.pending});oe.innerHTML=Object.entries(ops).sort((a,b)=>(b[1].done/(b[1].total||1))-(a[1].done/(a[1].total||1))).map(([k,o])=>{const pc=o.total?Math.round(o.done/o.total*1000)/10:0;return `<div class="chipOpRow"><b>${chipDashEsc(k)}</b><div class="chipOpTrack"><i style="width:${pc}%"></i></div><span>${pc}% · ${o.done}/${o.total}</span></div>`}).join('')}const tech={};rows.forEach(x=>(x.validators||[]).forEach(v=>{if(!v.technician)return;const t=tech[v.technician]??={name:v.technician,total:0,done:0};t.total++;if(v.status==='CONCLUÍDA')t.done++}));const te=document.getElementById('chipDashTechs');if(te)te.innerHTML=`<table class="chipDashTable"><thead><tr><th>Técnico</th><th>Concluídas</th><th>Atividades</th></tr></thead><tbody>${Object.values(tech).sort((a,b)=>b.done-a.done).map(t=>`<tr><td>${chipDashEsc(t.name)}</td><td><b>${t.done}</b></td><td>${t.total}</td></tr>`).join('')||'<tr><td colspan="3">Sem atividade registrada.</td></tr>'}</tbody></table>`;chipDashRenderTestResults(rows)}
function chipDashRenderTestResults(rows){const labels={TESTADO_OK:'Testado - OK',TESTADO_COM_DEFEITO:'Testado - com defeito',NAO_FOI_POSSIVEL_TESTAR:'Não foi possível testar',EQUIPAMENTO_INOPERANTE:'Equipamento inoperante',OUTRO:'Outro',SEM_RESULTADO:'Sem resultado'};const counts={};let total=0,pending=[];rows.forEach(x=>(x.validators||[]).forEach(v=>{if(!v.swap_id)return;const r=v.test_result||'SEM_RESULTADO';counts[r]=(counts[r]||0)+1;total++;if(r!=='TESTADO_OK')pending.push({x,v,r})}));const ok=counts.TESTADO_OK||0;const okEl=document.getElementById('chipTestOk'),pe=document.getElementById('chipTestPending');if(okEl)okEl.textContent=ok;if(pe)pe.textContent=pending.length;const chart=document.getElementById('chipTestResultChart');if(chart)chart.innerHTML=Object.entries(labels).map(([k,label])=>{const n=counts[k]||0,pct=total?Math.round(n/total*100):0;return `<div class="chipResultRow"><span>${chipDashEsc(label)}</span><div><i style="width:${pct}%"></i></div><b>${n}</b></div>`}).join('');const list=document.getElementById('chipTechnicalPendingList');if(list)list.innerHTML=pending.length?`<table class="chipDashTable"><thead><tr><th>Localidade</th><th>Terminal</th><th>Resultado</th><th>Técnico</th></tr></thead><tbody>${pending.slice(0,50).map(({x,v,r})=>`<tr><td>${chipDashEsc(x.line)} · ${chipDashEsc(x.location)}</td><td>${chipDashEsc(v.label||v.base_asset_id||'')}</td><td>${chipDashEsc(labels[r]||r)}</td><td>${chipDashEsc(v.technician||'—')}</td></tr>`).join('')}</tbody></table>`:'<p class="muted">Nenhuma pendência técnica registrada.</p>'}
function chipDashExportCsv(){const {rows,op,c,l,loc}=chipDashFilteredRows();const total=rows.reduce((a,x)=>a+x.total,0),done=rows.reduce((a,x)=>a+x.concluded,0),prog=rows.reduce((a,x)=>a+x.in_progress,0),pend=rows.reduce((a,x)=>a+x.pending,0),pct=total?Math.round(done/total*1000)/10:0;const q=v=>'"'+String(v??'').replace(/"/g,'""')+'"';const lines=[['RELATÓRIO TROCA DE CHIPS'],['Operação',op||'Todos'],['Empresa',c||'Todas'],['Linha',l||'Todas'],['Localidade',loc||'Todas'],[],['RESUMO'],['Total previsto','Concluídos','Em andamento','Pendentes','Progresso %'],[total,done,prog,pend,pct],[],['DETALHAMENTO'],['Operação','Empresa','Linha','Localidade','Terminal / ativo','Modelo','Status','Técnico']];rows.forEach(x=>(x.validators||[]).forEach(v=>lines.push([chipDashOperation(x.company),x.company,x.line,x.location,v.label||v.base_asset_id||'',v.model||'',v.status||'PENDENTE',v.technician||''])));const csv='\ufeff'+lines.map(r=>r.map(q).join(';')).join('\r\n');const blob=new Blob([csv],{type:'text/csv;charset=utf-8;'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='troca_chips_'+new Date().toISOString().slice(0,10)+'.csv';document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(url)}
async function loadChipDashboard(){try{const j=await fetch('/api/chip-swaps/dashboard',{cache:'no-store'}).then(r=>r.json());if(!j.ok)return;chipDashData=j;chipDashFill('chipDashOperation',j.locations.map(x=>chipDashOperation(x.company)),'Todos');chipDashFill('chipDashCompany',j.locations.map(x=>x.company),'Todas');chipDashFill('chipDashLine',j.locations.map(x=>x.line),'Todas');chipDashFill('chipDashLocation',j.locations.map(x=>x.location),'Todas');chipDashRender()}catch(e){console.warn('chip dashboard',e)}}
['chipDashOperation','chipDashCompany','chipDashLine','chipDashLocation','chipDashTestResult'].forEach(id=>document.getElementById(id)?.addEventListener('change',chipDashRender));document.getElementById('chipDashExport')?.addEventListener('click',()=>{const f=chipDashFilteredRows();const p=new URLSearchParams();if(f.op)p.set('operation',f.op);if(f.c)p.set('company',f.c);if(f.l)p.set('line',f.l);if(f.loc)p.set('location',f.loc);window.location.href='/api/chip-swaps/export.xlsx?'+p.toString()});loadChipDashboard();

document.getElementById('chipDashExportPending')?.addEventListener('click',()=>{const f=chipDashFilteredRows();const p=new URLSearchParams({pending_only:'1'});if(f.op)p.set('operation',f.op);if(f.c)p.set('company',f.c);if(f.l)p.set('line',f.l);if(f.loc)p.set('location',f.loc);if(f.test)p.set('test_result',f.test);window.location.href='/api/chip-swaps/export.xlsx?'+p.toString()});

// V41.3 — Dashboard EMV sincronizado com filtros executivos
let emvDashRows=[];
function emvDashFiltered(){const c=document.getElementById('execCompany')?.value||'',l=document.getElementById('execLine')?.value||'',st=document.getElementById('execStatus')?.value||'',t=document.getElementById('execType')?.value||'';if(t&&t!=='BLOQUEIO')return [];return emvDashRows.filter(x=>(!c||v413LooseMatch(x.company,c))&&(!l||v413LooseMatch(x.line,l))&&(!st||(st==='CONCLUIDA'?x.status==='CONCLUÍDA':st==='PENDENTE'?x.status==='PENDENTE':st==='EM ANDAMENTO'?x.status==='EM ANDAMENTO':st==='SEM REGISTRO'?!x.swap_id:true)))}
function renderEmvDashboard(){const rows=emvDashFiltered(),total=rows.length,done=rows.filter(x=>x.status==='CONCLUÍDA').length,progress=rows.filter(x=>x.status==='EM ANDAMENTO').length,pend=rows.filter(x=>x.status==='PENDENTE').length,pct=total?Math.round(done/total*1000)/10:0;const set=(id,v)=>{const e=document.getElementById(id);if(e)e.textContent=v};set('emvDashTotal',total);set('emvDashDone',done);set('emvDashPending',pend+progress);set('emvDashPct',pct+'%');set('emvDashDonePct',pct+'%');set('emvDashText',`${done} de ${total} bloqueios concluídos · ${progress} em andamento · ${pend} pendentes.`);const bd=document.getElementById('emvBarDone'),bp=document.getElementById('emvBarPending');if(bd)bd.style.width=pct+'%';if(bp)bp.style.width=(100-pct)+'%';const days={};rows.filter(x=>x.completed_at).forEach(x=>{const d=x.completed_at.slice(0,10);days[d]=(days[d]||0)+1});let cumulative=0;const data=Object.entries(days).sort().map(([d,n])=>({d,n,c:(cumulative+=n)})),el=document.getElementById('emvEvolution');if(el){if(!data.length){el.innerHTML='<p class="muted">Ainda não há histórico de conclusões para os filtros selecionados.</p>'}else{const max=Math.max(...data.map(x=>x.c),1);el.innerHTML=data.map(x=>`<div class="emvEvolutionRow"><span>${x.d.split('-').reverse().join('/')}</span><div><i style="width:${x.c/max*100}%"></i></div><b>${x.c}</b></div>`).join('')}}const link=document.querySelector('[data-v23-panel="emv"] a[href^="/api/emv-chip-swaps/export.xlsx"]');if(link){const p=new URLSearchParams();const c=document.getElementById('execCompany')?.value||'',l=document.getElementById('execLine')?.value||'',st=document.getElementById('execStatus')?.value||'';if(c)p.set('company',c);if(l)p.set('line',l);if(st)p.set('status',st==='CONCLUIDA'?'CONCLUÍDA':st);link.href='/api/emv-chip-swaps/export.xlsx?'+p.toString()}}
async function loadEmvDashboard(){const panel=document.querySelector('[data-v23-panel="emv"]');if(!panel)return;try{const j=await (await fetch('/api/emv-chip-swaps',{cache:'no-store'})).json();emvDashRows=j.rows||[];renderEmvDashboard()}catch(e){console.warn('EMV dashboard',e)}}
['execCompany','execLine','execStatus','execType'].forEach(id=>document.getElementById(id)?.addEventListener('change',()=>{chipDashRender();renderEmvDashboard()}));loadEmvDashboard();
