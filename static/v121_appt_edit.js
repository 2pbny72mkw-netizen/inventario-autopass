/* V88.0 REV49 — Editar e excluir agendamento do Portal (usado no Portal do Cliente e na Gestão de Agendamentos). */
(function () {
  if (window.apEdit) return;
  const css = `
.apx{position:fixed;inset:0;background:rgba(10,20,40,.55);display:flex;align-items:flex-start;justify-content:center;z-index:9999;padding:24px 12px;overflow:auto}
.apx[hidden],.apx [hidden]{display:none!important}
.apx .apxBox{background:#fff;border-radius:18px;width:min(980px,100%);padding:20px 22px;box-shadow:0 20px 50px rgba(0,0,0,.25);font-family:inherit;color:#16283d}
.apx h2{margin:0;font-size:20px}.apx .apxSub{color:#4a5b70;font-size:13px;margin:4px 0 14px}
.apx .apxGrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px}
.apx label{display:flex;flex-direction:column;gap:4px;font-size:12px;font-weight:700;color:#334861}
.apx input,.apx textarea,.apx select{font:inherit;font-weight:400;font-size:14px;border:1px solid #b9c7d8;border-radius:10px;padding:9px 10px;color:#16283d;background:#fff;width:100%;box-sizing:border-box}
.apx .apxEq{border:1px solid #dbe4ef;border-radius:14px;padding:12px;margin-top:10px;background:#f8fafd}
.apx .apxEq.rec{background:#f1f8f4;border-color:#bfe3cf}
.apx .apxEqTop{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;gap:8px}
.apx .apxEqF{display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:8px}.apx .apxEqF .w{grid-column:1/-1}@media(max-width:700px){.apx .apxEqF{grid-template-columns:1fr 1fr}.apx .apxEqF label:first-child{grid-column:1/-1}}
html .apx textarea{min-height:0;height:auto;resize:vertical}
.apx .apxFoot{display:flex;gap:8px;justify-content:flex-end;flex-wrap:wrap;margin-top:16px;position:sticky;bottom:-20px;background:#fff;padding:10px 0}
html .apx button.apxBtn{height:40px;min-height:40px;padding:0 16px;border-radius:10px;border:1px solid #0f1e3d;background:#fff;color:#0f1e3d;font:inherit;font-weight:700;font-size:13px;cursor:pointer}
html .apx button.apxBtn:hover{background:#eef3fa}
html .apx button.apxBtn.p{background:#0f5e5a;border-color:#0f5e5a;color:#fff}html .apx button.apxBtn.p:hover{background:#0b4a47}
html .apx button.apxBtn.d{border-color:#b42318;color:#b42318}html .apx button.apxBtn.d:hover{background:#fdecea}
html .apx button.apxBtn[disabled]{opacity:.55;cursor:wait}
.apx .apxTag{font-size:12px;font-weight:700;color:#1f7a5c;background:#dcfce7;border-radius:999px;padding:2px 10px}
.apx .apxErr{color:#b42318;font-weight:700;font-size:13px;margin-top:8px}
.apx .apxWarn{background:#fff7e0;border:1px solid #f3d38a;border-radius:12px;padding:10px 12px;font-size:13px;margin:8px 0}
`;
  const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
  const esc = s => String(s ?? '').replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));
  let box = null;
  function modal() {
    if (box) return box;
    box = document.createElement('div'); box.className = 'apx'; box.hidden = true;
    box.setAttribute('role', 'dialog'); box.setAttribute('aria-modal', 'true');
    box.innerHTML = '<div class="apxBox"></div>';
    box.addEventListener('click', e => { if (e.target === box) box.hidden = true });
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && box && !box.hidden) box.hidden = true });
    document.body.appendChild(box); return box;
  }
  function eqHtml(x, n) {
    const rec = !!x.received;
    return `<div class="apxEq${rec ? ' rec' : ''}" data-id="${x.id || ''}">
      <div class="apxEqTop"><b>Equipamento <span data-n>${n}</span></b>${rec ? '<span class="apxTag">Já recebido</span>' : '<button type="button" class="apxBtn d" data-rm>Retirar</button>'}</div>
      <div class="apxEqF">
        <label>Nº de série *<input data-k="serial" value="${esc(x.serial)}" maxlength="120"></label>
        <label>Modelo<input data-k="equipment" value="${esc(x.equipment)}" maxlength="120" list="apxModels"></label>
        <label>Versão<input data-k="version" value="${esc(x.version)}" maxlength="80"></label>
        <label>EOD<input data-k="eod" value="${esc(x.eod)}" maxlength="120"></label>
        <label class="w">Defeito informado *<input data-k="defect" value="${esc(x.defect)}" maxlength="500"></label>
        <label class="w">Informações adicionais<textarea data-k="notes" rows="2">${esc(x.notes)}</textarea></label>
      </div></div>`;
  }
  function renum() { box.querySelectorAll('.apxEq [data-n]').forEach((s, i) => s.textContent = i + 1) }

  window.apEdit = async function (id, onDone) {
    const m = modal(), b = m.querySelector('.apxBox');
    b.innerHTML = '<p>Carregando…</p>'; m.hidden = false;
    let d;
    try { const r = await fetch(`/api/portal/appointments/${id}/editar`, { credentials: 'same-origin' }); d = await r.json(); if (!r.ok) throw new Error(d.error || 'Falha ao abrir.') }
    catch (e) { b.innerHTML = `<p class="apxErr">${esc(e.message)}</p><div class="apxFoot"><button type="button" class="apxBtn" data-x>Fechar</button></div>`; b.querySelector('[data-x]').onclick = () => m.hidden = true; return }
    const a = d.appointment; let models = []; try { models = (typeof PC_MODELS !== 'undefined' && Array.isArray(PC_MODELS)) ? PC_MODELS : [] } catch (e) { }
    if (!d.pode_editar) { b.innerHTML = `<h2>${esc(a.code)}</h2><div class="apxWarn">${esc(d.motivo)}</div><div class="apxFoot"><button type="button" class="apxBtn" data-x>Fechar</button></div>`; b.querySelector('[data-x]').onclick = () => m.hidden = true; return }
    b.innerHTML = `<div style="display:flex;justify-content:space-between;gap:10px;align-items:flex-start"><div><h2>Editar agendamento ${esc(a.code)}</h2><div class="apxSub">${esc(a.company)} · notas fiscais, XML e fotos continuam como foram enviados.</div></div><button type="button" class="apxBtn" data-x>Fechar</button></div>
      <div class="apxGrid">
        <label>Responsável<input id="apxResp" value="${esc(a.responsible)}" maxlength="180"></label>
        <label>E-mail<input id="apxMail" type="email" value="${esc(a.email)}" maxlength="180"></label>
        <label>Telefone<input id="apxTel" value="${esc(a.phone)}" maxlength="40"></label>
        <label>Precisa de outra data?<select id="apxAlt"><option value="0">Não</option><option value="1"${a.alternate ? ' selected' : ''}>Sim</option></select></label>
        <label id="apxAltW"${a.alternate ? '' : ' hidden'}>Motivo da outra data<input id="apxAltR" value="${esc(a.alternate_reason)}" maxlength="300"></label>
        <label style="grid-column:1/-1">Observações gerais<textarea id="apxObs" rows="2">${esc(a.notes)}</textarea></label>
      </div>
      <datalist id="apxModels">${models.map(x => `<option value="${esc(x)}">`).join('')}</datalist>
      <div id="apxEqs">${d.items.map((x, i) => eqHtml(x, i + 1)).join('')}</div>
      <button type="button" class="apxBtn" id="apxAdd" style="margin-top:10px">+ Adicionar equipamento</button>
      <div class="apxErr" id="apxErr" role="alert"></div>
      <div class="apxFoot"><button type="button" class="apxBtn" data-x>Cancelar</button><button type="button" class="apxBtn p" id="apxSave">Salvar alterações</button></div>`;
    b.querySelectorAll('[data-x]').forEach(x => x.onclick = () => m.hidden = true);
    b.querySelector('#apxAlt').onchange = e => b.querySelector('#apxAltW').hidden = e.target.value !== '1';
    b.querySelector('#apxAdd').onclick = () => { const w = b.querySelector('#apxEqs'); w.insertAdjacentHTML('beforeend', eqHtml({}, w.children.length + 1)); w.lastElementChild.querySelector('[data-k=serial]').focus() };
    b.querySelector('#apxEqs').onclick = e => { const rm = e.target.closest('[data-rm]'); if (rm) { rm.closest('.apxEq').remove(); renum() } };
    b.querySelector('#apxSave').onclick = async ev => {
      const btn = ev.currentTarget, err = b.querySelector('#apxErr'); err.textContent = '';
      const items = [...b.querySelectorAll('.apxEq')].map(e => ({ id: e.dataset.id || null, ...Object.fromEntries([...e.querySelectorAll('[data-k]')].map(i => [i.dataset.k, i.value.trim()])) }));
      if (!items.length) { err.textContent = 'O agendamento precisa ter pelo menos um equipamento.'; return }
      const bad = items.findIndex(x => !x.serial || !x.defect); if (bad >= 0) { err.textContent = `Equipamento ${bad + 1}: preencha número de série e defeito.`; return }
      btn.disabled = true; btn.textContent = 'Salvando…';
      try {
        const r = await fetch(`/api/portal/appointments/${id}/editar`, { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ responsible: b.querySelector('#apxResp').value, email: b.querySelector('#apxMail').value, phone: b.querySelector('#apxTel').value, notes: b.querySelector('#apxObs').value, alternate: b.querySelector('#apxAlt').value === '1', alternate_reason: b.querySelector('#apxAltR').value, items }) });
        const j = await r.json().catch(() => ({})); if (!r.ok) throw new Error(j.error || 'Falha ao salvar.');
        m.hidden = true; if (onDone) onDone();
      } catch (e) { err.textContent = e.message; btn.disabled = false; btn.textContent = 'Salvar alterações' }
    };
  };

  /* recebidos > 0 só acontece para quem administra o Portal: exige motivo e o protocolo digitado. */
  window.apDelete = async function (id, code, recebidos, onDone) {
    recebidos = Number(recebidos || 0); let reason = '';
    if (recebidos) {
      if (!confirm(`ATENÇÃO: ${code} tem ${recebidos} equipamento(s) já recebido(s).\n\nA exclusão apaga o agendamento, os equipamentos e o histórico de recebimento e devolução. Não pode ser desfeita.\n\nContinuar?`)) return;
      reason = (prompt('Motivo da exclusão (ex.: agendamento de teste):') || '').trim(); if (!reason) return alert('Exclusão cancelada: informe o motivo.');
      if (prompt(`Para confirmar, digite o protocolo ${code}:`) !== code) return alert('Protocolo diferente. Exclusão cancelada.');
    } else if (!confirm(`Excluir o agendamento ${code}?\n\nEle será apagado e não poderá ser recuperado.`)) return;
    const r = await fetch(`/api/portal/appointments/${id}`, { method: 'DELETE', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ reason }) });
    const j = await r.json().catch(() => ({})); if (!r.ok) return alert(j.error || 'Falha ao excluir.');
    if (onDone) onDone();
  };
})();
