/* Autopass V73.6.3 — correção dedicada da Dashboard ATM.
   Motivo: garantir atualização do painel ATM sem depender do carregador legado.
   Fonte: /api/dashboard/inventory-atm (base oficial ATM 08/2026). */
(() => {
  'use strict';

  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? '')
    .replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;')
    .replaceAll('"','&quot;').replaceAll("'",'&#039;');
  const fmt = n => new Intl.NumberFormat('pt-BR').format(Number(n || 0));
  const norm = s => String(s || '').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toUpperCase().trim();
  const familyRoot = () => document.querySelector('[data-v23-panel="atm-inventory"]');
  const hasAtmDom = () => !!($('atmKTotal') && familyRoot());
  let lastPayload = null;
  let loading = false;
  let loadSeq = 0;

  function filterState(){
    return {
      company: $('atmFCompany')?.value || '',
      line: $('atmFLine')?.value || '',
      locality: $('atmFLocation')?.value || '',
      model: $('atmFModel')?.value || '',
      contract: $('atmFContract')?.value || '',
      ownership: $('atmFOwnership')?.value || '',
      status: $('atmFStatus')?.value || ''
    };
  }

  function setText(id, value){ const el=$(id); if(el) el.textContent=value; }
  function setHtml(id, value){ const el=$(id); if(el) el.innerHTML=value; }

  function fillSelect(id, values, label){
    const el=$(id); if(!el) return;
    const old=el.value;
    const list=[...new Set((values||[]).filter(Boolean).map(String))].sort((a,b)=>a.localeCompare(b,'pt-BR'));
    el.innerHTML=`<option value="">${esc(label)}</option>`+list.map(v=>`<option value="${esc(v)}">${esc(v)}</option>`).join('');
    if([...el.options].some(o=>o.value===old)) el.value=old;
  }

  function renderOptions(d){
    const o=d.options||{};
    fillSelect('atmFCompany',o.companies,'Todas operadoras');
    fillSelect('atmFLine',o.lines,'Todas linhas');
    fillSelect('atmFLocation',o.localities,'Todas localidades');
    fillSelect('atmFModel',o.models,'Todos modelos');
    fillSelect('atmFContract',o.contracts,'Todos contratos');
    fillSelect('atmFOwnership',o.ownership,'Todo tipo de posse');
    fillSelect('atmFStatus',o.statuses,'Todos status');
  }

  function entries(obj){
    return Object.entries(obj||{}).sort((a,b)=>Number(b[1]||0)-Number(a[1]||0) || String(a[0]).localeCompare(String(b[0]),'pt-BR'));
  }

  function renderOperatorBars(d){
    const rows=entries(d.operators), max=Math.max(1,...rows.map(x=>Number(x[1]||0)));
    setHtml('atmColumnOperator', rows.length ? rows.map(([name,count])=>{
      const h=Math.max(7,Math.round(Number(count)/max*100));
      return `<button type="button" class="v430Column" data-atm-company="${esc(name)}" title="${esc(name)} · ${fmt(count)} ATM(s)"><b>${fmt(count)}</b><i style="height:${h}%"></i><span>${esc(name)}</span></button>`;
    }).join('') : '<span class="muted">Sem dados no recorte.</span>');
    document.querySelectorAll('[data-atm-company]').forEach(btn=>btn.addEventListener('click',()=>{
      if($('atmFCompany')) $('atmFCompany').value=btn.dataset.atmCompany||'';
      loadAtmDashboard();
    }));
  }

  const palette=['#1f6feb','#16a085','#7c3aed','#d97706','#dc2626','#0891b2','#64748b','#4f46e5'];
  function renderDonut(d){
    const rows=entries(d.models), total=rows.reduce((s,x)=>s+Number(x[1]||0),0);
    setText('atmDonutTotal',fmt(total));
    let cursor=0; const stops=[];
    rows.forEach(([_,count],i)=>{ const start=cursor; cursor += total?Number(count)/total*100:0; stops.push(`${palette[i%palette.length]} ${start}% ${cursor}%`); });
    const donut=$('atmModelDonut'); if(donut) donut.style.background=rows.length?`conic-gradient(${stops.join(',')})`:'conic-gradient(#e5e7eb 0 100%)';
    setHtml('atmModelLegend',rows.map(([name,count],i)=>`<span><i style="background:${palette[i%palette.length]}"></i>${esc(name)} <b>${fmt(count)}</b></span>`).join(''));
  }

  function renderAllocation(d){
    const total=Number(d.total||0), allocated=Number(d.allocated||0), stock=Number(d.stock||0);
    const pct=total?Math.round(allocated/total*100):0;
    setText('atmAllocationPct',pct+'%'); setText('atmAllocationA',fmt(allocated)); setText('atmAllocationS',fmt(stock));
    const ring=$('atmAllocationRing'); if(ring) ring.style.background=`conic-gradient(#16a085 0 ${pct}%,#f0b429 ${pct}% 100%)`;
  }

  function renderLocations(d){
    const rows=entries(d.locations).slice(0,10), max=Math.max(1,...rows.map(x=>Number(x[1]||0)));
    setHtml('atmLocationRanking',rows.length?rows.map(([name,count])=>`<button type="button" class="statusBarRow" data-atm-location="${esc(name)}"><span>${esc(name)}</span><div class="bar"><i style="width:${Math.round(Number(count)/max*100)}%"></i></div><b>${fmt(count)}</b></button>`).join(''):'<span class="muted">Sem localidades no recorte.</span>');
    document.querySelectorAll('[data-atm-location]').forEach(btn=>btn.addEventListener('click',()=>{
      if($('atmFLocation')) $('atmFLocation').value=btn.dataset.atmLocation||'';
      loadAtmDashboard();
    }));
  }

  function renderOwnership(d){
    const rows=entries(d.ownership), total=rows.reduce((s,x)=>s+Number(x[1]||0),0);
    const leasing=rows.filter(([k])=>norm(k).includes('LEAS')).reduce((s,x)=>s+Number(x[1]||0),0);
    setText('atmLeasingCount',fmt(leasing));
    const pct=total?leasing/total*100:0;
    const donut=$('atmOwnershipDonut'); if(donut) donut.style.background=`conic-gradient(#4f46e5 0 ${pct}%,#dfe7f1 ${pct}% 100%)`;
    setHtml('atmOwnershipLegend',rows.map(([name,count])=>`<span>${esc(name)} <b>${fmt(count)}</b></span>`).join(''));
  }

  function renderLines(d){
    const rows=entries(d.lines).slice(0,12), max=Math.max(1,...rows.map(x=>Number(x[1]||0)));
    setHtml('atmLineHeatmap',rows.length?rows.map(([name,count])=>`<button type="button" data-atm-line="${esc(name)}" style="--heat:${Math.max(.12,Number(count)/max)}"><b>${fmt(count)}</b><span>${esc(name)}</span></button>`).join(''):'<span class="muted">Sem linhas no recorte.</span>');
    document.querySelectorAll('[data-atm-line]').forEach(btn=>btn.addEventListener('click',()=>{
      if($('atmFLine')) $('atmFLine').value=btn.dataset.atmLine||'';
      loadAtmDashboard();
    }));
  }

  function renderContracts(d){
    const assets=d.assets||[]; const grouped={};
    assets.forEach(a=>{ const c=String(a.contract||'Sem contrato').trim()||'Sem contrato'; const o=String(a.ownership||'Não informado').trim()||'Não informado'; const g=grouped[c]??={total:0,own:{}}; g.total++; g.own[o]=(g.own[o]||0)+1; });
    const rows=Object.entries(grouped).sort((a,b)=>b[1].total-a[1].total);
    const max=Math.max(1,...rows.map(x=>x[1].total));
    setHtml('atmContractStack',rows.length?rows.map(([name,g])=>`<button type="button" class="v430StackRow" data-atm-contract="${esc(name)}"><span>${esc(name)}</span><div class="v430StackTrack">${Object.entries(g.own).map(([own,n],i)=>`<i title="${esc(own)} · ${fmt(n)}" style="width:${n/g.total*100}%;background:${palette[i%palette.length]}"></i>`).join('')}</div><b>${fmt(g.total)}</b></button>`).join(''):'<span class="muted">Sem contratos no recorte.</span>');
    document.querySelectorAll('[data-atm-contract]').forEach(btn=>btn.addEventListener('click',()=>{
      if($('atmFContract')) $('atmFContract').value=btn.dataset.atmContract||'';
      loadAtmDashboard();
    }));
  }

  function renderCoverage(d){
    const assets=d.assets||[]; const groups={};
    assets.forEach(a=>{ const c=String(a.company||'Não informado').trim()||'Não informado'; const loc=String(a.locality||'').trim(); if(!loc)return; (groups[c]??=new Set()).add(loc); });
    const rows=Object.entries(groups).map(([name,set])=>[name,set.size]).sort((a,b)=>b[1]-a[1]);
    setHtml('atmCoverageTiles',rows.length?rows.map(([name,count])=>`<article><span>${esc(name)}</span><b>${fmt(count)}</b><small>localidades</small></article>`).join(''):'<span class="muted">Sem cobertura no recorte.</span>');
  }

  function assetId(a){ return a.asset_key || a.id_top || a.terminal_number || a.terminal || a.asset || a.id || '—'; }
  function renderAssets(d){
    const rows=d.assets||[];
    setText('atmRowsTag',`${fmt(rows.length)} ATMs`);
    const tbody=$('atmRows');
    if(tbody) tbody.innerHTML=rows.length?rows.map(a=>`<tr><td>${esc(a.company||'')}</td><td>${esc(a.line||'')}</td><td>${esc(a.locality||'')}</td><td><b>${esc(assetId(a))}</b></td><td>${esc(a.model||'')}</td><td>${esc(a.contract||'Sem contrato')}</td><td>${esc(a.ownership||'')}</td><td>${String(a.teamviewer_id||'').trim()?'Sim':'Não'}</td><td>${esc(a.teamviewer_id||'')}</td><td>${esc(a.ip||a.ip_address||'')}</td><td>${esc(a.status||'')}</td></tr>`).join(''):'<tr><td colspan="11">Nenhum ATM encontrado no recorte.</td></tr>';
    setHtml('atmDrillCards',`<article><span>Recorte atual</span><b>${fmt(rows.length)}</b><small>ATMs</small></article><article><span>Operações</span><b>${fmt(Object.keys(d.operators||{}).length)}</b><small>operadoras</small></article><article><span>Localidades</span><b>${fmt(Object.keys(d.locations||{}).length)}</b><small>com ATM</small></article><article><span>Modelos</span><b>${fmt(Object.keys(d.models||{}).length)}</b><small>no recorte</small></article>`);
  }

  function renderKpis(d){
    setText('atmKTotal',fmt(d.total));
    setText('atmKAllocated',fmt(d.allocated));
    setText('atmKStock',fmt(d.stock));
    setText('atmKCptmStations',fmt(d.cptm_stations));
    setText('atmKMetroStations',fmt(d.metro_stations));
    setText('atmKTeamviewer',fmt(d.teamviewer_count));
  }

  function renderAll(d){
    lastPayload=d;
    renderKpis(d); renderOptions(d); renderOperatorBars(d); renderDonut(d); renderAllocation(d);
    renderLocations(d); renderOwnership(d); renderLines(d); renderContracts(d); renderCoverage(d); renderAssets(d);
    const hint=$('atmDrillHint'); if(hint) hint.textContent=`Base ATM atualizada · ${fmt(d.total)} equipamento(s) no recorte · fonte oficial 08/2026.`;
  }

  function showError(err){
    console.error('V73.6.3 Dashboard ATM',err);
    const hint=$('atmDrillHint'); if(hint) hint.textContent='Falha ao atualizar a Dashboard ATM. Verifique Network → /api/dashboard/inventory-atm.';
    const tag=$('atmRowsTag'); if(tag) tag.textContent='ERRO DE CARGA';
  }

  async function loadAtmDashboard(){
    if(!hasAtmDom() || loading) return;
    const seq=++loadSeq; loading=true;
    try{
      const p=new URLSearchParams(filterState());
      if(new URLSearchParams(location.search).get('teamviewer_missing')==='1') p.set('teamviewer_missing','1');
      p.set('_v','7363'); p.set('_ts',String(Date.now()));
      const r=await fetch('/api/dashboard/inventory-atm?'+p.toString(),{cache:'no-store',headers:{'X-Autopass-Dashboard':'ATM-V73.6.3'}});
      const d=await r.json().catch(()=>({ok:false,error:'Resposta inválida do servidor'}));
      if(!r.ok || !d.ok) throw new Error(d.error||`HTTP ${r.status}`);
      if(seq!==loadSeq) return;
      renderAll(d);
    }catch(err){ showError(err); }
    finally{ loading=false; }
  }

  function exportCsv(){
    const d=lastPayload; if(!d) return;
    const q=v=>'"'+String(v??'').replaceAll('"','""')+'"';
    const lines=[['Operadora','Linha','Localidade','ATM','Modelo','Contrato','Posse','TeamViewer','IP','Status']];
    (d.assets||[]).forEach(a=>lines.push([a.company,a.line,a.locality,assetId(a),a.model,a.contract,a.ownership,a.teamviewer_id,a.ip||a.ip_address,a.status]));
    const csv='\ufeff'+lines.map(row=>row.map(q).join(';')).join('\r\n');
    const blob=new Blob([csv],{type:'text/csv;charset=utf-8'}), url=URL.createObjectURL(blob), a=document.createElement('a');
    a.href=url; a.download='dashboard_atm_'+new Date().toISOString().slice(0,10)+'.csv'; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
  }

  function bind(){
    if(!hasAtmDom()) return;
    ['atmFCompany','atmFLine','atmFLocation','atmFModel','atmFContract','atmFOwnership','atmFStatus'].forEach(id=>$(id)?.addEventListener('change',loadAtmDashboard));
    $('atmClear')?.addEventListener('click',()=>{ ['atmFCompany','atmFLine','atmFLocation','atmFModel','atmFContract','atmFOwnership','atmFStatus'].forEach(id=>{if($(id))$(id).value='';}); loadAtmDashboard(); });
    $('atmDashRefresh')?.addEventListener('click',loadAtmDashboard);
    $('atmDashExport')?.addEventListener('click',exportCsv);
    $('atmShowLocations')?.addEventListener('click',()=>{ const details=$('atmAssetDetails'); if(details){details.open=true;details.scrollIntoView({behavior:'smooth',block:'start'});} });
    window.AutopassATM7363={reload:loadAtmDashboard,getData:()=>lastPayload};
    setTimeout(loadAtmDashboard,80);
    setTimeout(loadAtmDashboard,900);

    const root=familyRoot();
    if(root && window.MutationObserver){
      new MutationObserver(()=>{ if(root.classList.contains('is-active') || getComputedStyle(root).display!=='none') loadAtmDashboard(); })
        .observe(root,{attributes:true,attributeFilter:['class','style']});
    }
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',bind,{once:true}); else bind();
})();
