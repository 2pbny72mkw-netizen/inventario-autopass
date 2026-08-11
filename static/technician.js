let locations = [], current = null, assets = [];
const $ = id => document.getElementById(id);
const uniq = a => [...new Set(a)].sort((x, y) => x.localeCompare(y, 'pt-BR'));
const fill = (el, a, label = 'Selecione') =>
  el.innerHTML = `<option value="">${label}</option>` + a.map(x => `<option>${x}</option>`).join('');


let lastGps = null;

function clearGpsFields() {
  $('latitude').value = '';
  $('longitude').value = '';
  $('gps_accuracy').value = '';
  $('gps_captured_at').value = '';
}

function setGpsMessage(text, ok = null) {
  $('gpsText').textContent = text;
  const box = $('gpsStatus');
  if (ok === true) {
    box.style.borderColor = '#b7dfc4';
  } else if (ok === false) {
    box.style.borderColor = '#f0c2c2';
  } else {
    box.style.borderColor = '';
  }
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

  $('latitude').value = String(c.latitude);
  $('longitude').value = String(c.longitude);
  $('gps_accuracy').value = String(c.accuracy);
  $('gps_captured_at').value = capturedAt;

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
    } catch (err) {
      serverRows = (await cacheGet(cacheKey)) || [];
    }
  } else {
    serverRows = (await cacheGet(cacheKey)) || [];
  }

  const pending = await queuedForLocation(current.id);
  const pendingRows = pending.map(x => ({
    equipment_type: x.fields.equipment_type,
    asset_identifier: x.fields.asset_identifier,
    serial: x.fields.serial,
    model: x.fields.model,
    operational_status: 'Pendente de sincronização',
    technician: 'Neste aparelho',
    created_at: new Date(x.created_at).toISOString(),
    _pending: true
  }));

  const all = [...pendingRows, ...serverRows];
  $('doneCount').textContent = `${all.length} registro(s)`;

  $('already').innerHTML = all.length
    ? all.map(x => `
      <tr>
        <td>${escapeHtml(x.equipment_type)}</td>
        <td><b>${escapeHtml(x.asset_identifier)}</b>${x.serial && x.serial !== x.asset_identifier ? '<br>' + escapeHtml(x.serial) : ''}</td>
        <td>${escapeHtml(x.model || '')}</td>
        <td>${x._pending ? '<span class="tag">PENDENTE</span>' : escapeHtml(x.operational_status)}</td>
        <td>${escapeHtml(x.technician)}</td>
        <td>${escapeHtml(String(x.created_at || '').replace('T', ' ').slice(0, 19))}</td>
      </tr>`).join('')
    : '<tr><td colspan="6">Nenhum equipamento registrado ainda.</td></tr>';
}

async function loadAssets() {
  const cacheKey = `assets:${current.id}`;

  if (navigator.onLine) {
    try {
      const r = await fetch(`/api/location/${current.id}/assets`, { cache: 'no-store' });
      if (!r.ok) throw new Error('Falha ao consultar ativos.');
      assets = await r.json();
      await cacheSet(cacheKey, assets);
    } catch (err) {
      assets = (await cacheGet(cacheKey)) || [];
    }
  } else {
    assets = (await cacheGet(cacheKey)) || [];
  }

  renderAssets();
}

function renderAssets() {
  const sel = $('base_asset_id');
  sel.innerHTML = '<option value="">Novo / não selecionar</option>';

  assets.forEach(a => {
    const id = a.top_id || a.qrcode_id || a.serial || a.asset_key;
    const o = document.createElement('option');
    o.value = a.id;
    o.disabled = a.already_inventoried;
    o.textContent = `${a.already_inventoried ? '✓ JÁ FEITO — ' : ''}${a.asset_key} | ${a.model || '-'} | ${id}`;
    sel.appendChild(o);
  });

  $('assetHint').textContent = assets.length
    ? `${assets.filter(x => x.already_inventoried).length} já feitos de ${assets.length} ATM(s) encontrados na base detalhada.`
    : navigator.onLine
      ? 'Nenhum ATM detalhado casado automaticamente para este local.'
      : 'Nenhum ativo armazenado offline para este local.';
}

$('equipment_type').onchange = () => {
  if ($('equipment_type').value !== 'ATM') $('base_asset_id').value = '';
};

$('base_asset_id').onchange = () => {
  const a = assets.find(x => x.id == +$('base_asset_id').value);
  if (!a) return;

  $('asset_identifier').value = a.top_id || a.qrcode_id || a.serial || a.asset_key;
  $('serial').value = a.serial || '';
  $('supplier').value = a.supplier || '';
  $('model').value = a.model || '';
  $('mount').value = a.mount || '';
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
  const record = await formToOfflineRecord(form);

  if (await hasLocalDuplicate(record)) {
    showMsg('Este equipamento já está na fila de sincronização deste aparelho.', false);
    return false;
  }

  await idbPut(STORE_QUEUE, record);
  showMsg('Equipamento salvo neste aparelho. Você pode continuar cadastrando outros antes de sincronizar.', true);

  const savedGps = lastGps ? {...lastGps} : null;
  form.reset();
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

  await refreshConnectionUI();
  await loadAlready();
  return true;
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
