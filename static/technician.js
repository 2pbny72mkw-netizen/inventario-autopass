window.AUTOPASS_TECHNICIAN_VERSION = '1408-5';
console.log('AUTOPASS technician.js 1408-5 carregado');

let locations = [], current = null, assets = [];
let currentInventoryRows = [];
let allLocationAssets = [];
let editingInventoryId = null;
const $ = id => document.getElementById(id);
const uniq = a => [...new Set(a)].sort((x, y) => x.localeCompare(y, 'pt-BR'));
const fill = (el, a, label = 'Selecione') =>
  el.innerHTML = `<option value="">${label}</option>` + a.map(x => `<option>${x}</option>`).join('');


let lastGps = null;

function clearGpsFields() {
  ['latitude','longitude','gps_accuracy','gps_captured_at'].forEach(id => {
    const el = $(id); if (el) el.value = '';
  });
}

function setGpsMessage(text, ok = null) {
  const gpsText = $('gpsText');
  const box = $('gpsStatus');
  if (gpsText) gpsText.textContent = text;
  if (!box) return;
  if (ok === true) box.style.borderColor = '#b7dfc4';
  else if (ok === false) box.style.borderColor = '#f0c2c2';
  else box.style.borderColor = '';
}

function applyGpsPosition(position) {
  const c = position.coords;
  const capturedAt = new Date(position.timestamp || Date.now()).toISOString();

  lastGps = {
    latitude: c.latitude,
    longitude: c.longitude,
    accuracy: c.accuracy,
    captured_at: capturedAt
  };

  if ($('latitude')) $('latitude').value = String(c.latitude);
  if ($('longitude')) $('longitude').value = String(c.longitude);
  if ($('gps_accuracy')) $('gps_accuracy').value = String(c.accuracy);
  if ($('gps_captured_at')) $('gps_captured_at').value = capturedAt;

  const accuracy = Number.isFinite(c.accuracy) ? Math.round(c.accuracy) : null;
  setGpsMessage(
    accuracy !== null
      ? `Localização capturada • precisão aproximada ${accuracy} m`
      : 'Localização capturada.',
    true
  );

  return lastGps;
}

function captureGpsForSubmission() {
  clearGpsFields();

  if (!('geolocation' in navigator)) {
    setGpsMessage('GPS não disponível neste aparelho/navegador. O cadastro pode continuar.', false);
    return Promise.resolve(null);
  }

  setGpsMessage('Capturando localização...');

  return new Promise(resolve => {
    navigator.geolocation.getCurrentPosition(
      position => resolve(applyGpsPosition(position)),
      error => {
        const messages = {
          1: 'Permissão de localização não concedida.',
          2: 'Localização indisponível neste momento.',
          3: 'Tempo esgotado ao tentar obter a localização.'
        };
        setGpsMessage(`${messages[error.code] || 'Não foi possível obter o GPS.'} O cadastro pode continuar.`, false);
        resolve(null);
      },
      {
        enableHighAccuracy: true,
        timeout: 8000,
        maximumAge: 30000
      }
    );
  });
}

const DB_NAME = 'inventario-autopass-offline';
const DB_VERSION = 1;
const STORE_QUEUE = 'queue';
const STORE_CACHE = 'cache';
const LOCAL_MODE_KEY = 'inventario-autopass-local-mode';

function isLocalMode() {
  return localStorage.getItem(LOCAL_MODE_KEY) === '1';
}

function setLocalMode(enabled) {
  localStorage.setItem(LOCAL_MODE_KEY, enabled ? '1' : '0');
  $('localMode').checked = enabled;
  $('localModeHint').style.display = enabled ? 'block' : 'none';
  $('saveBtn').textContent = enabled ? 'Salvar no aparelho' : 'Salvar equipamento';
}

function openDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);

    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE_QUEUE)) {
        const q = db.createObjectStore(STORE_QUEUE, { keyPath: 'local_id' });
        q.createIndex('created_at', 'created_at');
        q.createIndex('location_id', 'location_id');
      }
      if (!db.objectStoreNames.contains(STORE_CACHE)) {
        db.createObjectStore(STORE_CACHE, { keyPath: 'key' });
      }
    };

    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function idbPut(storeName, value) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, 'readwrite');
    tx.objectStore(storeName).put(value);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

async function idbGet(storeName, key) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, 'readonly');
    const req = tx.objectStore(storeName).get(key);
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function idbGetAll(storeName) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, 'readonly');
    const req = tx.objectStore(storeName).getAll();
    req.onsuccess = () => resolve(req.result || []);
    req.onerror = () => reject(req.error);
  });
}

async function idbDelete(storeName, key) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, 'readwrite');
    tx.objectStore(storeName).delete(key);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

async function cacheSet(key, data) {
  await idbPut(STORE_CACHE, { key, data, saved_at: Date.now() });
}

async function cacheGet(key) {
  const row = await idbGet(STORE_CACHE, key);
  return row ? row.data : null;
}

function connectionText() {
  return navigator.onLine ? '🟢 Online' : '🟠 Offline';
}

async function refreshConnectionUI() {
  const queue = await idbGetAll(STORE_QUEUE);
  $('connectionStatus').textContent = connectionText();
  $('syncSummary').textContent = queue.length
    ? `${queue.length} registro(s) aguardando sincronização.`
    : 'Tudo sincronizado neste aparelho.';
  $('pendingCount').textContent = `${queue.length} pendente(s)`;
  $('syncBtn').disabled = !navigator.onLine || queue.length === 0;
  setLocalMode(isLocalMode());
  renderPending(queue);
}

function renderPending(queue) {
  if (!queue.length) {
    $('pendingList').innerHTML = 'Nenhuma pendência.';
    return;
  }

  const ordered = [...queue].sort((a, b) => a.created_at - b.created_at);
  $('pendingList').innerHTML = ordered.map(x => {
    const dt = new Date(x.created_at).toLocaleString('pt-BR');
    const files = x.files?.length || 0;
    const gps = x.fields.latitude && x.fields.longitude
      ? ` • GPS ${Number(x.fields.gps_accuracy || 0).toFixed(0)} m`
      : ' • GPS indisponível';
    return `
      <div style="padding:10px 0;border-bottom:1px solid #e5e7eb">
        <b>${escapeHtml(x.fields.equipment_type || 'Equipamento')} • ${escapeHtml(x.fields.asset_identifier || '')}</b><br>
        <small>${escapeHtml(x.location_name || '')} • ${dt} • ${files} mídia(s)${gps}</small>
      </div>`;
  }).join('');
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

async function loadLocations() {
  if (navigator.onLine) {
    try {
      const r = await fetch('/api/locations', { cache: 'no-store' });
      if (!r.ok) throw new Error('Falha ao consultar localidades.');
      locations = await r.json();
      await cacheSet('locations', locations);
    } catch (err) {
      locations = (await cacheGet('locations')) || [];
    }
  } else {
    locations = (await cacheGet('locations')) || [];
  }

  fill($('company'), uniq(locations.map(x => x.company)));

  if (!locations.length) {
    showMsg('Sem internet e sem localidades armazenadas neste aparelho. Conecte-se uma vez antes de entrar em campo.', false);
  }
}

$('company').onchange = () => {
  fill(
    $('line'),
    uniq(locations.filter(x => x.company === $('company').value).map(x => x.line))
  );
  $('line').disabled = !$('company').value;
  fill($('location'), []);
  $('location').disabled = true;
  hideInfo();
};

$('line').onchange = () => {
  const arr = locations.filter(
    x => x.company === $('company').value && x.line === $('line').value
  );
  $('location').innerHTML = '<option value="">Selecione</option>' +
    arr.map(x => `<option value="${x.id}">${escapeHtml(x.location)}</option>`).join('');
  $('location').disabled = !$('line').value;
  hideInfo();
};

$('location').onchange = async () => {
  current = locations.find(x => x.id == +$('location').value);
  $('location_id').value = current?.id || '';

  if (current) {
    showInfo();
    await Promise.all([loadAlready(), loadAssets()]);
  } else {
    hideInfo();
  }
};

function hideInfo() {
  $('locInfo').classList.add('hidden');
  $('already').innerHTML = '<tr><td colspan="6">Selecione um local.</td></tr>';
  $('doneCount').textContent = '0 registros';
  currentInventoryRows = [];
  renderLocationPending();
}

function showInfo() {
  const expected = current.expected_atm + current.expected_validator + current.expected_pos;
  $('locInfo').classList.remove('hidden');
  $('locInfo').innerHTML = `
    <b>${escapeHtml(current.location)}</b> • ${escapeHtml(current.company)} • ${escapeHtml(current.line)}<br>
    Status: <span class="status s${String(current.survey_status).replaceAll(' ', '')}">${escapeHtml(current.survey_status)}</span> &nbsp;
    Base: ATM ${current.expected_atm} | Validadores ${current.expected_validator} | POS ${current.expected_pos} | Total ${expected}
  `;
}

async function queuedForLocation(locationId) {
  const queue = await idbGetAll(STORE_QUEUE);
  return queue.filter(x => Number(x.location_id) === Number(locationId));
}

async function loadAlready() {
  const cacheKey = `inventory:${current.id}`;
  let serverRows = [];
  if (navigator.onLine) {
    try {
      const r = await fetch(`/api/location/${current.id}/inventory`, { cache: 'no-store' });
      if (!r.ok) throw new Error('Falha ao consultar realizados.');
      serverRows = await r.json();
      await cacheSet(cacheKey, serverRows);
    } catch (err) { serverRows = (await cacheGet(cacheKey)) || []; }
  } else { serverRows = (await cacheGet(cacheKey)) || []; }

  const pending = await queuedForLocation(current.id);
  const pendingRows = pending.map(x => ({
    equipment_type:x.fields.equipment_type, asset_identifier:x.fields.asset_identifier,
    serial:x.fields.serial, model:x.fields.model, operational_status:'Pendente de sincronização',
    technician:'Neste aparelho', created_at:new Date(x.created_at).toISOString(), _pending:true
  }));
  const all=[...pendingRows,...serverRows];
  currentInventoryRows=all;
  $('doneCount').textContent=`${all.length} registro(s)`;
  $('already').innerHTML = all.length ? all.map(x=>`
    <tr>
      <td>${escapeHtml(x.equipment_type)}</td>
      <td><b>${escapeHtml(x.asset_identifier)}</b>${x.serial&&x.serial!==x.asset_identifier?'<br>'+escapeHtml(x.serial):''}</td>
      <td>${escapeHtml(x.model||'')}</td>
      <td>${x._pending?'<span class="tag">PENDENTE</span>':escapeHtml(x.operational_status)}</td>
      <td>${escapeHtml(x.technician)}</td>
      <td>${escapeHtml(String(x.created_at||'').replace('T',' ').slice(0,19))}</td>
      <td>${x._pending?'<span class="muted">Aguardando sincronização</span>':`
        <div style="display:flex;gap:6px;flex-wrap:wrap">
          <button type="button" class="secondary editInventoryBtn" data-id="${x.id}">Editar</button>
          <button type="button" class="secondary deleteInventoryBtn" data-id="${x.id}" style="color:#b42318;border-color:#f0b4b4">Excluir</button>
        </div>`}</td>
    </tr>`).join('') : '<tr><td colspan="7">Nenhum equipamento registrado ainda.</td></tr>';

  document.querySelectorAll('.deleteInventoryBtn').forEach(btn=>btn.onclick=async()=>{
    const inventoryId=Number(btn.dataset.id); if(!inventoryId) return;
    if(!confirm('Confirma a exclusão deste cadastro? Esta ação removerá o registro do inventário.')) return;
    try{
      btn.disabled=true; btn.textContent='Excluindo...';
      const r=await fetch(`/api/inventory/${inventoryId}`,{method:'DELETE'});
      const j=await r.json().catch(()=>({ok:false,error:'Resposta inválida do servidor.'}));
      if(!r.ok){showMsg(j.error||'Não foi possível excluir o cadastro.',false);btn.disabled=false;btn.textContent='Excluir';return;}
      showMsg('Cadastro excluído com sucesso.',true); await loadAlready(); await loadAssets();
    }catch(err){console.error(err);showMsg('Erro ao excluir o cadastro.',false);btn.disabled=false;btn.textContent='Excluir';}
  });

  document.querySelectorAll('.editInventoryBtn').forEach(btn=>btn.onclick=async()=>{
    const inventoryId=Number(btn.dataset.id);
    const row=currentInventoryRows.find(x=>Number(x.id)===inventoryId);
    if(!row) return showMsg('Não foi possível localizar este cadastro.',false);
    editingInventoryId=inventoryId;
    $('equipment_type').value=row.equipment_type||'';
    updateEquipmentTypeUI();
    await loadAssets();
    $('base_asset_id').value=row.base_asset_id||'';
    const values={asset_identifier:row.asset_identifier,serial:row.serial,supplier:row.supplier,model:row.model,
      mount:row.mount,application:row.application,bom_id:row.bom_id,bu_id:row.bu_id,
      validator_top_id:row.validator_top_id,software_version:row.software_version};
    Object.entries(values).forEach(([id,v])=>{if($(id)) $(id).value=v||'';});
    ['exact_position','operational_status','connectivity','network_id','label_status','in_base','divergence','notes'].forEach(name=>{
      const el=document.querySelector(`[name="${name}"]`); if(el) el.value=row[name]||'';
    });
    ['latitude','longitude','gps_accuracy','gps_captured_at'].forEach(id=>{if($(id)) $(id).value=row[id]??'';});
    $('saveBtn').textContent='Salvar alterações';
    showMsg('Modo edição ativo. Faça as alterações e clique em Salvar alterações.',true);
    $('invForm').scrollIntoView({behavior:'smooth',block:'start'});
  });
  renderLocationPending();
}

async function loadAssets() {
  const cacheKey=`assets:${current.id}:all`;
  if(navigator.onLine){
    try{
      const r=await fetch(`/api/location/${current.id}/assets`,{cache:'no-store'});
      if(!r.ok) throw new Error('Falha ao consultar ativos.');
      allLocationAssets=await r.json(); await cacheSet(cacheKey,allLocationAssets);
    }catch(err){allLocationAssets=(await cacheGet(cacheKey))||[];}
  }else{allLocationAssets=(await cacheGet(cacheKey))||[];}
  const selected=normalizedEquipmentType($('equipment_type').value||'');
  assets=selected ? allLocationAssets.filter(a=>normalizedEquipmentType(a.equipment_type||'ATM')===selected) : [];
  renderAssets(); renderLocationPending();
}

function renderAssets(){
  const sel=$('base_asset_id'); if(!sel) return;
  sel.innerHTML='<option value="">Novo / não selecionar</option>';
  assets.forEach(a=>{
    const id=a.terminal_number||a.top_id||a.qrcode_id||a.serial||a.asset_key;
    const o=document.createElement('option'); o.value=a.id; o.disabled=a.already_inventoried;
    o.textContent=`${a.already_inventoried?'✓ JÁ FEITO — ':''}${a.asset_key||id||'Ativo'} | ${a.model||'-'} | ${id||'-'}`;
    sel.appendChild(o);
  });
  const type=normalizedEquipmentType($('equipment_type').value||'');
  const typeLabel=type||'equipamento';
  $('assetHint').textContent=assets.length
    ? `${assets.filter(x=>x.already_inventoried).length} já feito(s) de ${assets.length} ativo(s) detalhado(s) de ${typeLabel}.`
    : navigator.onLine ? `Nenhum ativo detalhado de ${typeLabel} encontrado para este local.` : 'Nenhum ativo armazenado offline para este local.';
}

function normalizedEquipmentType(value) {
  const v = String(value || '').trim().toUpperCase();
  if (v === 'ATM') return 'ATM';
  if (v.includes('VALIDADOR')) return 'Validador de Recarga';
  if (v.includes('POS')) return 'POS de Bilheteria';
  if (v === 'TDI' || v.includes(' TDI')) return 'TDI';
  if (v.includes('BLOQUEIO')) return 'Bloqueio';
  if (v.includes('RACK')) return 'Rack de Comunicação';
  return value || 'Outro';
}

function countInventoryByType(type) {
  return currentInventoryRows.filter(x =>
    normalizedEquipmentType(x.equipment_type) === type &&
    String(x.operational_status || '').toUpperCase() !== 'NÃO ENCONTRADO'
  ).length;
}

function pendingDefinitions() {
  if (!current) return [];
  const defs = [
    { type: 'ATM', label: 'ATMs', configured: Number(current.expected_atm || 0) },
    { type: 'Validador de Recarga', label: 'Validadores de Recarga', configured: Number(current.expected_validator || 0) },
    { type: 'POS de Bilheteria', label: 'POS de Bilheteria', configured: Number(current.expected_pos || 0) },
    { type: 'TDI', label: 'TDI', configured: 0 },
    { type: 'Bloqueio', label: 'Bloqueios', configured: 0 }
  ];
  return defs.map(item => {
    const done = countInventoryByType(item.type);
    const detailed = allLocationAssets.filter(
      a => normalizedEquipmentType(a.equipment_type || 'ATM') === item.type
    ).length;
    const expected = Math.max(item.configured, detailed);
    return {...item, expected, done, detailed,
      remaining: Math.max(expected-done,0),
      extra: Math.max(done-expected,0)};
  }).filter(x => x.expected > 0 || x.done > 0);
}

function renderLocationPending() {
  const summary=$('locationPendingSummary'), list=$('locationPendingList'), badge=$('locationPendingCount');
  if (!summary || !list || !badge) return;
  if (!current) {
    badge.textContent='0 pendências';
    summary.textContent='Selecione uma localidade para consultar o que falta.';
    list.innerHTML=''; return;
  }
  const defs=pendingDefinitions();
  const totalExpected=defs.reduce((s,x)=>s+x.expected,0);
  const totalDone=defs.reduce((s,x)=>s+Math.min(x.done,x.expected),0);
  const totalRemaining=defs.reduce((s,x)=>s+x.remaining,0);
  badge.textContent=`${totalRemaining} pendência(s)`;
  summary.innerHTML=totalRemaining
    ? `<b>${totalDone} de ${totalExpected}</b> equipamento(s) previstos conferidos. Ainda faltam <b>${totalRemaining}</b>.`
    : totalExpected ? `<b>Previsão da base atendida.</b> ${totalDone} de ${totalExpected} equipamento(s) conferidos.`
    : 'Esta localidade não possui equipamentos previstos na base detalhada.';
  list.innerHTML=defs.map(x=>{
    const action=x.remaining>0 ? `<button type="button" class="secondary pendingStartBtn" data-type="${escapeHtml(x.type)}">Cadastrar ${escapeHtml(x.type)}</button>` : '';
    const extra=x.extra ? ` • ${x.extra} acima da previsão` : '';
    return `<div style="display:flex;justify-content:space-between;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid #e5e7eb;flex-wrap:wrap"><div><b>${escapeHtml(x.label)}</b><br><small>Previstos: ${x.expected} • Ativos detalhados: ${x.detailed} • Realizados: ${x.done} • Faltam: ${x.remaining}${extra}</small></div><div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap"><span class="tag">${x.remaining>0?'PENDENTE':'CONCLUÍDO'}</span>${action}</div></div>`;
  }).join('');
  document.querySelectorAll('.pendingStartBtn').forEach(btn=>btn.onclick=()=>{
    $('equipment_type').value=btn.dataset.type;
    $('equipment_type').dispatchEvent(new Event('change'));
    $('asset_identifier').focus();
    $('invForm').scrollIntoView({behavior:'smooth',block:'start'});
  });
}

$('showPendingBtn')?.addEventListener('click',()=>{
  if (!current) return showMsg('Selecione uma localidade para consultar as pendências.',false);
  renderLocationPending();
  $('locationPendingCard')?.scrollIntoView({behavior:'smooth',block:'start'});
});

function updateEquipmentTypeUI(){
  const type=$('equipment_type').value;
  const label=$('assetBaseLabel');
  if(label){
    if(type==='ATM') label.textContent='Ativo da base — ATM';
    else if(type==='Validador de Recarga') label.textContent='Ativo da base — Validador';
    else if(type==='POS de Bilheteria') label.textContent='Ativo da base — POS';
    else if(type==='TDI') label.textContent='Ativo da base — TDI';
    else if(type==='Bloqueio') label.textContent='Ativo da base — Bloqueio';
    else label.textContent='Ativo da base';
  }
  const showTechnical=['Validador de Recarga','TDI','Bloqueio'].includes(type);
  const vf=$('validatorFields'); if(vf) vf.style.display=showTechnical?'block':'none';
  const title=$('technicalFieldsTitle');
  if(title){
    if(type==='Validador de Recarga') title.textContent='Dados específicos do Validador de Recarga';
    else if(type==='TDI') title.textContent='Dados específicos do TDI';
    else if(type==='Bloqueio') title.textContent='Dados específicos do Bloqueio';
  }
  const isBlock=type==='Bloqueio';
  ['fieldBom','fieldBu','fieldTop'].forEach(id=>{if($(id)) $(id).style.display=isBlock?'none':'block';});
  if($('applicationLabel')) $('applicationLabel').textContent=isBlock?'Instalação':'Aplicação';
}


function formatBaseDate(value){
  if(!value) return '—';
  const s=String(value);
  const m=s.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  return m ? `${m[3]}/${m[2]}/${m[1]}` : s;
}

function renderSelectedBaseInfo(a){
  const panel=$('baseDetailsPanel');
  const body=$('baseDetailsBody');
  const title=$('baseDetailsTitle');
  if(!panel || !body) return;

  if(!a){
    panel.style.display='none';
    body.innerHTML='';
    return;
  }

  const type=normalizedEquipmentType(a.equipment_type||$('equipment_type').value);
  const rows=[];

  const add=(label,value)=>{
    const v=(value===null || value===undefined || String(value).trim()==='') ? '' : String(value).trim();
    if(v) rows.push(`<span><b>${escapeHtml(label)}:</b> ${escapeHtml(v)}</span>`);
  };

  add('Ativo',a.asset_key||a.description);
  add('Status da base',a.base_status);

  if(type==='ATM'){
    if(title) title.textContent='Dados da base — ATM';
    add('Produtos',a.products);
    add('Transaciona',a.transactions);
    add('PIX',a.pix);
    add('Fixação',a.mount);
    add('Leasing',a.leasing_status);
    add('Vencimento contrato',formatBaseDate(a.contract_end));
  }else if(type==='Validador de Recarga'){
    if(title) title.textContent='Dados da base — Validador';
    add('Aplicação',a.application);
    add('BOM',a.bom_id);
    add('BU',a.bu_id);
    add('TOP',a.top_id);
    add('Versão',a.software_version);
  }else if(type==='POS de Bilheteria'){
    if(title) title.textContent='Dados da base — POS';
    add('Terminal',a.terminal_number);
    add('Fornecedor',a.supplier);
    add('Modelo',a.model);
  }else if(type==='TDI'){
    if(title) title.textContent='Dados da base — TDI';
    add('Aplicação',a.application);
    add('BOM',a.bom_id);
    add('BU',a.bu_id);
    add('TOP',a.top_id);
    add('Versão',a.software_version);
    add('Série',a.serial);
  }else if(type==='Bloqueio'){
    if(title) title.textContent='Dados da base — Bloqueio';
    add('Bloqueio',a.terminal_number||a.top_id);
    add('Modelo',a.model);
    add('Versão',a.software_version);
    add('Instalação',a.installation_type||a.application);
    add('Data instalação',formatBaseDate(a.installation_date));
  }else{
    if(title) title.textContent='Dados encontrados na base';
    add('Modelo',a.model);
    add('Fornecedor',a.supplier);
  }

  if(a.already_inventoried) rows.push('<span><b>Situação:</b> já inventariado nesta localidade</span>');

  body.innerHTML=rows.length
    ? `<div style="display:flex;gap:14px;flex-wrap:wrap">${rows.join('')}</div>`
    : 'Ativo localizado na base, sem outros dados complementares.';
  panel.style.display='block';
}

$('equipment_type').onchange = async () => {
  updateEquipmentTypeUI();
  renderSelectedBaseInfo(null);
  $('base_asset_id').value='';
  if(current) await loadAssets(); else {assets=[];renderAssets();}
};

$('base_asset_id').onchange = () => {
  const a=assets.find(x=>x.id==+$('base_asset_id').value);
  if(!a){ renderSelectedBaseInfo(null); return; }
  $('asset_identifier').value=a.terminal_number||a.top_id||a.qrcode_id||a.serial||a.asset_key||'';
  $('serial').value=a.serial||''; $('supplier').value=a.supplier||''; $('model').value=a.model||'';
  if($('mount') && a.mount) $('mount').value=a.mount;
  if($('application')) $('application').value=a.application||a.installation_type||'';
  if($('bom_id')) $('bom_id').value=a.bom_id||'';
  if($('bu_id')) $('bu_id').value=a.bu_id||'';
  if($('validator_top_id')) $('validator_top_id').value=a.top_id||a.terminal_number||'';
  if($('software_version')) $('software_version').value=a.software_version||'';
  renderSelectedBaseInfo(a);
};

async function formToOfflineRecord(form) {
  const fd = new FormData(form);
  const fields = {};
  const files = [];

  for (const [key, value] of fd.entries()) {
    if (value instanceof File) {
      if (value.name) {
        files.push({
          field: key,
          name: value.name,
          type: value.type || 'application/octet-stream',
          blob: value
        });
      }
    } else {
      fields[key] = value;
    }
  }

  const localId = (crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`);
  return {
    local_id: localId,
    created_at: Date.now(),
    location_id: Number(fields.location_id),
    location_name: current?.location || '',
    fields,
    files,
    attempts: 0,
    last_error: null
  };
}

async function hasLocalDuplicate(record) {
  const queue = await idbGetAll(STORE_QUEUE);
  const type = String(record.fields.equipment_type || '').trim().toUpperCase();
  const identifier = String(record.fields.asset_identifier || '').trim().toUpperCase();

  return queue.some(x =>
    Number(x.location_id) === Number(record.location_id) &&
    String(x.fields.equipment_type || '').trim().toUpperCase() === type &&
    String(x.fields.asset_identifier || '').trim().toUpperCase() === identifier
  );
}

async function enqueueCurrentForm(form) {
  try{
    showMsg('Preparando salvamento local...',true);
    const record=await formToOfflineRecord(form);
    if(await hasLocalDuplicate(record)){showMsg('Este equipamento já está na fila de sincronização deste aparelho.',false);return false;}
    await idbPut(STORE_QUEUE,record);
    const savedGps=lastGps?{...lastGps}:null;
    form.reset(); $('location_id').value=current.id; clearGpsFields(); updateEquipmentTypeUI(); renderSelectedBaseInfo(null);
    if(savedGps){const a=Number.isFinite(savedGps.accuracy)?Math.round(savedGps.accuracy):null;setGpsMessage(a!==null?`Último registro salvo com GPS • precisão aproximada ${a} m`:'Último registro salvo com GPS.',true);}
    else setGpsMessage('Último registro salvo sem GPS disponível.',false);
    await refreshConnectionUI(); await loadAlready(); await loadAssets();
    showMsg('Equipamento salvo neste aparelho com sucesso. O formulário foi limpo e as pendências foram atualizadas.',true);
    return true;
  }catch(err){console.error('Erro ao salvar localmente:',err);showMsg(`Erro ao salvar neste aparelho: ${err?.message||String(err)}`,false);return false;}
}

async function sendRecord(record) {
  const fd = new FormData();
  Object.entries(record.fields).forEach(([key, value]) => fd.append(key, value ?? ''));

  (record.files || []).forEach(f => {
    fd.append(f.field || 'attachments', new File([f.blob], f.name, { type: f.type }));
  });

  const r = await fetch('/api/inventory', { method: 'POST', body: fd });
  const j = await r.json().catch(() => ({ ok: false, error: 'Resposta inválida do servidor.' }));

  if (r.ok) return { ok: true };

  // Se o servidor diz que já existe, consideramos a fila resolvida:
  // o objetivo é não duplicar o inventário.
  if (r.status === 409 && j.duplicate) {
    return { ok: true, duplicate: true, message: j.error || 'Duplicidade já existente no servidor.' };
  }

  return { ok: false, status: r.status, error: j.error || 'Não foi possível sincronizar.' };
}

async function syncQueue({ silent = false } = {}) {
  if (!navigator.onLine) {
    if (!silent) showMsg('Sem conexão. A sincronização será tentada quando o sinal voltar.', false);
    await refreshConnectionUI();
    return;
  }

  const queue = (await idbGetAll(STORE_QUEUE)).sort((a, b) => a.created_at - b.created_at);
  if (!queue.length) {
    await refreshConnectionUI();
    if (!silent) showMsg('Não há registros pendentes.', true);
    return;
  }

  $('syncBtn').disabled = true;
  $('connectionStatus').textContent = '🔵 Sincronizando...';

  let synced = 0;
  let duplicates = 0;

  for (const record of queue) {
    try {
      const result = await sendRecord(record);

      if (result.ok) {
        await idbDelete(STORE_QUEUE, record.local_id);
        synced++;
        if (result.duplicate) duplicates++;
      } else {
        record.attempts = (record.attempts || 0) + 1;
        record.last_error = result.error;
        await idbPut(STORE_QUEUE, record);

        // Em erros de validação, seguimos para os demais.
        // Em falhas de rede/servidor, interrompemos para não insistir em sequência.
        if (!result.status || result.status >= 500) break;
      }
    } catch (err) {
      record.attempts = (record.attempts || 0) + 1;
      record.last_error = String(err);
      await idbPut(STORE_QUEUE, record);
      break;
    }

    await refreshConnectionUI();
  }

  await refreshConnectionUI();

  if (current) {
    await loadAlready();
    await loadAssets();
  }

  if (navigator.onLine) {
    try {
      const r = await fetch('/api/locations', { cache: 'no-store' });
      if (r.ok) {
        locations = await r.json();
        await cacheSet('locations', locations);
        if (current) {
          current = locations.find(x => x.id === current.id) || current;
          showInfo();
        }
      }
    } catch (_) {}
  }

  if (!silent) {
    const remaining = (await idbGetAll(STORE_QUEUE)).length;
    if (!remaining) {
      showMsg(
        duplicates
          ? `Sincronização concluída. ${synced} registro(s) processado(s), incluindo ${duplicates} duplicidade(s) já existente(s) no servidor.`
          : `Sincronização concluída. ${synced} registro(s) enviado(s).`,
        true
      );
    } else {
      showMsg(`${synced} registro(s) sincronizado(s). ${remaining} ainda aguardam envio.`, false);
    }
  }
}

$('invForm').onsubmit = async e => {
  e.preventDefault();

  if(editingInventoryId){
    try{
      const fd=new FormData(e.target);
      const r=await fetch(`/api/inventory/${editingInventoryId}`,{method:'PATCH',body:fd});
      const j=await r.json().catch(()=>({ok:false,error:'Resposta inválida do servidor.'}));
      if(!r.ok){showMsg(j.error||'Não foi possível atualizar o cadastro.',false);return;}
      showMsg('Cadastro atualizado com sucesso.',true);
      editingInventoryId=null; e.target.reset(); $('location_id').value=current.id; clearGpsFields(); updateEquipmentTypeUI(); renderSelectedBaseInfo(null);
      $('saveBtn').textContent=isLocalMode()?'Salvar no aparelho':'Salvar equipamento';
      await loadAlready(); await loadAssets(); renderLocationPending(); return;
    }catch(err){console.error('Erro ao editar cadastro:',err);showMsg('Erro ao atualizar o cadastro.',false);return;}
  }

  if (!current) {
    showMsg('Selecione uma localidade.', false);
    return;
  }

  await captureGpsForSubmission();

  // Em modo coleta local, sempre guarda no aparelho, mesmo que haja internet.
  // Isso permite cadastrar vários equipamentos primeiro e sincronizar só no fim.
  if (isLocalMode()) {
    await enqueueCurrentForm(e.target);
    return;
  }

  // Sem internet: guarda localmente.
  if (!navigator.onLine) {
    await enqueueCurrentForm(e.target);
    return;
  }

  try {
    const fd = new FormData(e.target);
    const r = await fetch('/api/inventory', { method: 'POST', body: fd });
    const j = await r.json().catch(() => ({ ok: false, error: 'Erro no servidor.' }));

    if (!r.ok) {
      if (!navigator.onLine || r.status >= 500) {
        await enqueueCurrentForm(e.target);
        return;
      }
      showMsg(j.error || 'Não foi possível salvar.', false);
      return;
    }

    showMsg('Equipamento salvo no servidor.', true);
    const savedGps = lastGps ? {...lastGps} : null;
    e.target.reset();
    $('location_id').value = current.id;
    clearGpsFields();
    if (savedGps) {
      const a = Number.isFinite(savedGps.accuracy) ? Math.round(savedGps.accuracy) : null;
      setGpsMessage(a !== null
        ? `Último registro salvo com GPS • precisão aproximada ${a} m`
        : 'Último registro salvo com GPS.', true);
    } else {
      setGpsMessage('Último registro salvo sem GPS disponível.', false);
    }

    await loadAlready();
    await loadAssets();

    const rr = await fetch('/api/locations', { cache: 'no-store' });
    if (rr.ok) {
      locations = await rr.json();
      await cacheSet('locations', locations);
      current = locations.find(x => x.id === current.id);
      showInfo();
    }
  } catch (err) {
    await enqueueCurrentForm(e.target);
  }

  await refreshConnectionUI();
};

$('completeBtn').onclick = async () => {
  if (!current) return showMsg('Selecione uma localidade.', false);

  const localPending = await queuedForLocation(current.id);
  if (localPending.length) {
    return showMsg(
      `Esta localidade ainda tem ${localPending.length} registro(s) pendente(s) neste aparelho. Sincronize antes de concluir.`,
      false
    );
  }

  if (!navigator.onLine) {
    return showMsg('A conclusão da localidade exige conexão para evitar encerramento sem sincronizar os registros.', false);
  }

  const operationalPending = pendingDefinitions().reduce((s, x) => s + x.remaining, 0);
  if (operationalPending > 0) {
    const proceed = confirm(`A base ainda indica ${operationalPending} equipamento(s) pendente(s) nesta localidade. Deseja mesmo assim continuar para a confirmação final?`);
    if (!proceed) return;
  }

  if (!confirm('Confirma que o levantamento desta localidade foi finalizado? Ela aparecerá como CONCLUÍDA no painel gerencial.')) {
    return;
  }

  const r = await fetch(`/api/location/${current.id}/complete`, { method: 'POST' });

  if (r.ok) {
    showMsg('Localidade marcada como CONCLUÍDA.', true);
    const rr = await fetch('/api/locations', { cache: 'no-store' });
    if (rr.ok) {
      locations = await rr.json();
      await cacheSet('locations', locations);
      current = locations.find(x => x.id === current.id);
      showInfo();
    }
  } else {
    showMsg('Não foi possível concluir a localidade.', false);
  }
};

$('syncBtn').onclick = () => syncQueue({ silent: false });

window.addEventListener('online', async () => {
  await refreshConnectionUI();
  const queue = await idbGetAll(STORE_QUEUE);
  if (queue.length) {
    showMsg(`Conexão restabelecida. ${queue.length} registro(s) aguardam envio. Clique em "Sincronizar agora" quando desejar.`, true);
  }
});

window.addEventListener('offline', refreshConnectionUI);

$('localMode').addEventListener('change', async e => {
  setLocalMode(e.target.checked);
  await refreshConnectionUI();

  if (e.target.checked) {
    showMsg('Modo coleta local ativado. Os próximos registros ficarão neste aparelho até a sincronização manual.', true);
  } else {
    const queue = await idbGetAll(STORE_QUEUE);
    if (queue.length) {
      showMsg(`${queue.length} registro(s) continuam pendentes. Clique em "Sincronizar agora" quando desejar enviá-los.`, true);
    } else {
      showMsg('Modo coleta local desativado.', true);
    }
  }
});

function showMsg(t, ok) {
  $('msg').className = ok ? 'okmsg' : 'errmsg';
  $('msg').textContent = t;
}

(async function init() {
  try {
    await openDB();
    await loadLocations();
    await refreshConnectionUI();

    setLocalMode(isLocalMode());
  } catch (err) {
    console.error(err);
    showMsg('Não foi possível iniciar o armazenamento offline neste navegador.', false);
  }
})();
