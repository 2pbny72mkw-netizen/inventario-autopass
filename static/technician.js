
let locations=[], current=null, assets=[];
const $=id=>document.getElementById(id);
const uniq=a=>[...new Set(a)].sort((x,y)=>x.localeCompare(y,'pt-BR'));
const fill=(el,a,label='Selecione')=>el.innerHTML=`<option value="">${label}</option>`+a.map(x=>`<option>${x}</option>`).join('');

async function loadLocations(){locations=await fetch('/api/locations').then(r=>r.json());fill($('company'),uniq(locations.map(x=>x.company)));}

$('company').onchange=()=>{fill($('line'),uniq(locations.filter(x=>x.company===$('company').value).map(x=>x.line)));$('line').disabled=!$('company').value;fill($('location'),[]);$('location').disabled=true;hideInfo()}
$('line').onchange=()=>{let arr=locations.filter(x=>x.company===$('company').value&&x.line===$('line').value);$('location').innerHTML='<option value="">Selecione</option>'+arr.map(x=>`<option value="${x.id}">${x.location}</option>`).join('');$('location').disabled=!$('line').value;hideInfo()}
$('location').onchange=async()=>{current=locations.find(x=>x.id==+$('location').value);$('location_id').value=current?.id||'';if(current){showInfo();await Promise.all([loadAlready(),loadAssets()])}else hideInfo()}

function hideInfo(){$('locInfo').classList.add('hidden');$('already').innerHTML='<tr><td colspan="6">Selecione um local.</td></tr>'}
function showInfo(){
 let expected=current.expected_atm+current.expected_validator+current.expected_pos;
 $('locInfo').classList.remove('hidden');
 $('locInfo').innerHTML=`<b>${current.location}</b> • ${current.company} • ${current.line}<br>
 Status: <span class="status s${current.survey_status.replaceAll(' ','')}">${current.survey_status}</span> &nbsp;
 Base: ATM ${current.expected_atm} | Validadores ${current.expected_validator} | POS ${current.expected_pos} | Total ${expected}`;
}
async function loadAlready(){
 let a=await fetch(`/api/location/${current.id}/inventory`).then(r=>r.json());
 $('doneCount').textContent=`${a.length} registro(s)`;
 $('already').innerHTML=a.length?a.map(x=>`<tr><td>${x.equipment_type}</td><td><b>${x.asset_identifier}</b>${x.serial&&x.serial!==x.asset_identifier?'<br>'+x.serial:''}</td><td>${x.model||''}</td><td>${x.operational_status}</td><td>${x.technician}</td><td>${x.created_at.replace('T',' ')}</td></tr>`).join(''):'<tr><td colspan="6">Nenhum equipamento registrado ainda.</td></tr>';
}
async function loadAssets(){
 assets=await fetch(`/api/location/${current.id}/assets`).then(r=>r.json()); renderAssets()
}
function renderAssets(){
 let sel=$('base_asset_id'); sel.innerHTML='<option value="">Novo / não selecionar</option>';
 assets.forEach(a=>{let id=a.top_id||a.qrcode_id||a.serial||a.asset_key;let o=document.createElement('option');o.value=a.id;o.disabled=a.already_inventoried;o.textContent=`${a.already_inventoried?'✓ JÁ FEITO — ':''}${a.asset_key} | ${a.model||'-'} | ${id}`;sel.appendChild(o)})
 $('assetHint').textContent=assets.length?`${assets.filter(x=>x.already_inventoried).length} já feitos de ${assets.length} ATM(s) encontrados na base detalhada.`:'Nenhum ATM detalhado casado automaticamente para este local.';
}
$('equipment_type').onchange=()=>{if($('equipment_type').value!=='ATM')$('base_asset_id').value=''}
$('base_asset_id').onchange=()=>{
 let a=assets.find(x=>x.id==+$('base_asset_id').value);if(!a)return;
 $('asset_identifier').value=a.top_id||a.qrcode_id||a.serial||a.asset_key;
 $('serial').value=a.serial||'';$('supplier').value=a.supplier||'';$('model').value=a.model||'';$('mount').value=a.mount||'';
}
$('invForm').onsubmit=async e=>{
 e.preventDefault();if(!current){showMsg('Selecione uma localidade.',false);return}
 let fd=new FormData(e.target);
 let r=await fetch('/api/inventory',{method:'POST',body:fd});
 let j=await r.json().catch(()=>({ok:false,error:'Erro no servidor.'}));
 if(!r.ok){showMsg(j.error||'Não foi possível salvar.',false);return}
 showMsg('Equipamento salvo. A lista de realizados foi atualizada.',true);
 e.target.reset();$('location_id').value=current.id;await loadAlready();await loadAssets();locations=await fetch('/api/locations').then(r=>r.json());current=locations.find(x=>x.id===current.id);showInfo();
}
$('completeBtn').onclick=async()=>{
 if(!current)return showMsg('Selecione uma localidade.',false);
 if(!confirm('Confirma que o levantamento desta localidade foi finalizado? Ela aparecerá como CONCLUÍDA no painel gerencial.'))return;
 let r=await fetch(`/api/location/${current.id}/complete`,{method:'POST'}); if(r.ok){showMsg('Localidade marcada como CONCLUÍDA.',true);locations=await fetch('/api/locations').then(r=>r.json());current=locations.find(x=>x.id===current.id);showInfo()}
}
function showMsg(t,ok){$('msg').className=ok?'okmsg':'errmsg';$('msg').textContent=t}
loadLocations();
