const $=id=>document.getElementById(id),
esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let data=[];

function norm(v){
  return String(v??'')
    .normalize('NFD').replace(/[\u0300-\u036f]/g,'')
    .toUpperCase().replace(/[^A-Z0-9]+/g,' ').trim();
}
function normStatus(v){
  const s=norm(v);
  if(['CONCLUIDA','CONCLUIDO','FINALIZADA','FINALIZADO'].includes(s)) return 'CONCLUÍDA';
  if(['EM ANDAMENTO','ANDAMENTO'].includes(s)) return 'EM ANDAMENTO';
  return 'PENDENTE';
}
function fillCompany(){
  const map=new Map();
  data.forEach(x=>{
    const k=norm(x.company);
    if(k && !map.has(k)) map.set(k,String(x.company||'').trim());
  });
  $('gCompany').innerHTML='<option value="">Todas</option>'+
    [...map.entries()].sort((a,b)=>a[1].localeCompare(b[1],'pt-BR'))
      .map(([k,label])=>`<option value="${esc(k)}">${esc(label)}</option>`).join('');
}
function fillSimple(id,vals,label){
  $(id).innerHTML=`<option value="">${label}</option>`+
    [...new Set(vals.filter(Boolean).map(v=>String(v).trim()))]
      .sort((a,b)=>a.localeCompare(b,'pt-BR')).map(v=>`<option value="${esc(v)}">${esc(v)}</option>`).join('');
}
async function load(){
  const r=await fetch('/api/garage-chip-swaps',{cache:'no-store'});
  const j=await r.json();
  if(!r.ok || j.ok===false) throw new Error(j.error||`HTTP ${r.status}`);
  data=(j.rows||[]).map(x=>({...x,status:normStatus(x.status)}));
  fillCompany();
  fillSimple('gModel',data.map(x=>x.model),'Todos');
  render();
}
function render(){
  const companyKey=$('gCompany').value;
  const q=$('gTerminal').value.trim().toLowerCase();
  const model=$('gModel').value;
  const status=$('gStatus').value;

  const rows=data.filter(x =>
    (!companyKey || norm(x.company)===companyKey) &&
    (!q || String(x.terminal||'').toLowerCase().includes(q)) &&
    (!model || String(x.model||'')===model) &&
    (!status || normStatus(x.status)===status)
  );

  const total=rows.length;
  const done=rows.filter(x=>normStatus(x.status)==='CONCLUÍDA').length;
  const prog=rows.filter(x=>normStatus(x.status)==='EM ANDAMENTO').length;
  const pend=rows.filter(x=>normStatus(x.status)==='PENDENTE').length;
  const pct=total ? done*100/total : 0;

  $('gTotal').textContent=total;
  $('gDone').textContent=done;
  $('gProg').textContent=prog;
  $('gPend').textContent=pend;
  $('gPct').textContent=pct.toFixed(1)+'%';
  $('gDonutPct').textContent=pct.toFixed(1)+'%';
  $('gDonut').style.background=`conic-gradient(#238b57 0 ${pct}%, #c9413c ${pct}% 100%)`;
  $('gBar').style.width=Math.min(100,pct)+'%';

  $('gDoneBar').style.width=(total?done*100/total:0)+'%';
  $('gProgBar').style.width=(total?prog*100/total:0)+'%';
  $('gPendBar').style.width=(total?pend*100/total:0)+'%';

  // Clear, single-line ratios.
  $('gDoneRatio').textContent=`${done} de ${total}`;
  $('gProgRatio').textContent=`${prog} de ${total}`;
  $('gPendRatio').textContent=`${pend} de ${total}`;
  $('gSummary').textContent=`Concluídos: ${done} de ${total} · Pendentes: ${pend} · Progresso: ${pct.toFixed(1)}%`;

  $('gRows').innerHTML=rows.map(x=>`<article class="chipValidatorCard ${normStatus(x.status)==='CONCLUÍDA'?'done':''}">
    <div class="chipValidatorHead"><div><small>${esc(x.company)}</small><h3>Terminal ${esc(x.terminal)}</h3>
    <p>${esc(x.model||'Modelo não informado')}${x.technician?' · '+esc(x.technician):''}</p></div>
    <span class="tag">${esc(normStatus(x.status))}</span></div>
    <div class="chipEvidence">${(x.photos||[]).map(p=>`<figure class="chipEvidenceItem"><a href="${esc(p.url)}" target="_blank"><img src="${esc(p.thumb_url||p.url)}" loading="lazy"></a></figure>`).join('')}</div>
    <form class="gForm" data-id="${x.id}">
      <label>Resultado após troca *</label>
      <select name="test_result" required>
        <option value="">Selecione</option>
        <option value="TESTADO_OK" ${x.test_result==='TESTADO_OK'?'selected':''}>Testado - OK</option>
        <option value="TESTADO_COM_DEFEITO" ${x.test_result==='TESTADO_COM_DEFEITO'?'selected':''}>Testado - com defeito</option>
        <option value="NAO_FOI_POSSIVEL_TESTAR" ${x.test_result==='NAO_FOI_POSSIVEL_TESTAR'?'selected':''}>Não foi possível testar</option>
        <option value="EQUIPAMENTO_INOPERANTE" ${x.test_result==='EQUIPAMENTO_INOPERANTE'?'selected':''}>Equipamento inoperante</option>
        <option value="OUTRO" ${x.test_result==='OUTRO'?'selected':''}>Outro</option>
      </select>
      <label>Observação / pendência</label>
      <textarea name="notes" rows="2">${esc(x.notes||'')}</textarea>
      <label>Evidência opcional</label>
      <div class="fieldEvidenceActions">
        <label class="secondary fieldEvidenceBtn">📷 Tirar foto<input name="photos" type="file" accept="image/*" capture="environment" hidden></label>
        <label class="secondary fieldEvidenceBtn">🖼️ Escolher foto<input name="photos" type="file" accept="image/*" multiple hidden></label>
      </div>
      <button type="submit">Registrar troca e concluir</button><small class="chipMsg"></small>
    </form></article>`).join('') || '<p class="muted">Nenhum terminal neste filtro.</p>';

  document.querySelectorAll('.gForm').forEach(f=>f.onsubmit=save);
}
async function save(e){
  e.preventDefault();
  const f=e.currentTarget,msg=f.querySelector('.chipMsg'),fd=new FormData(f),btn=f.querySelector('button');
  if(!fd.get('test_result')){msg.textContent='Selecione o resultado.';return}
  btn.disabled=true;
  try{
    const r=await fetch('/api/garage-chip-swaps/'+f.dataset.id,{method:'POST',body:fd});
    const j=await r.json();
    if(!r.ok) throw Error(j.error||'Falha');
    msg.textContent='Troca registrada.';
    await load();
  }catch(e){msg.textContent=e.message}
  finally{btn.disabled=false}
}
['gCompany','gModel','gStatus'].forEach(id=>$(id).onchange=render);
$('gTerminal').oninput=render;
$('gClear').onclick=()=>{
  $('gCompany').value='';$('gTerminal').value='';$('gModel').value='';$('gStatus').value='';render()
};
load().catch(e=>{
  console.error(e);
  $('gRows').innerHTML=`<p class="muted">Falha ao carregar a base: ${esc(e.message)}</p>`;
});