/* V87.6 REV76 — Padrão Autopass: tabelas ordenáveis (data-ap-table) e KPI clicável (data-ap-href).
   Opt-in: telas sem o atributo não mudam. Funciona com tbody preenchido depois do carregamento. */
(function(){
  "use strict";
  if(window.__apStd) return; window.__apStd=true;
  var collator=new Intl.Collator('pt-BR',{sensitivity:'base',numeric:true});

  function parseNum(s){
    var t=String(s==null?'':s).replace(/ /g,' ').trim();
    if(!t||t==='—'||t==='-'||t==='–') return null;
    t=t.replace(/^R\$\s*/,'').replace(/\s*(%|MB|GB|KB|ms|s|dias?|h)$/i,'').trim();
    if(!/^-?\d{1,3}(\.\d{3})*(,\d+)?$/.test(t) && !/^-?\d+(,\d+)?$/.test(t) && !/^-?\d+\.\d+$/.test(t)) return null;
    if(t.indexOf(',')>=0) t=t.replace(/\./g,'').replace(',','.');
    else if(/^-?\d{1,3}(\.\d{3})+$/.test(t)) t=t.replace(/\./g,'');
    var n=parseFloat(t); return isNaN(n)?null:n;
  }
  function parseDate(s){
    var t=String(s==null?'':s).trim(), m;
    if((m=/^(\d{2})\/(\d{2})\/(\d{4})(?:[ ,]+(\d{2}):(\d{2})(?::(\d{2}))?)?/.exec(t)))
      return Date.UTC(+m[3],+m[2]-1,+m[1],+(m[4]||0),+(m[5]||0),+(m[6]||0));
    if((m=/^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2})(?::(\d{2}))?)?/.exec(t)))
      return Date.UTC(+m[1],+m[2]-1,+m[3],+(m[4]||0),+(m[5]||0),+(m[6]||0));
    return null;
  }
  function cellRaw(td){
    if(!td) return '';
    if(td.dataset && td.dataset.sort!==undefined) return td.dataset.sort;
    return (td.textContent||'').replace(/\s+/g,' ').trim();
  }
  function bodyGroups(tbody){
    // grupos = linha de dados + linhas de detalhe (data-ap-detail) que a seguem
    var groups=[],cur=null;
    Array.prototype.forEach.call(tbody.rows,function(tr){
      if(tr.hasAttribute('data-ap-detail')&&cur){cur.rows.push(tr);return;}
      if(tr.__apo===undefined) tr.__apo=(window.__apSeq=(window.__apSeq||0)+1);
      cur={rows:[tr],idx:tr.__apo,main:tr};groups.push(cur);
    });
    return groups;
  }
  function colType(groups,col){
    var n=0,num=0,dt=0;
    groups.forEach(function(g){
      var r=cellRaw(g.main.cells[col]); if(r===''||r==='—'||r==='-') return; n++;
      if(parseNum(r)!==null) num++; else if(parseDate(r)!==null) dt++;
    });
    if(n&&num/n>=0.8) return 'num'; if(n&&dt/n>=0.8) return 'date'; return 'text';
  }

  function exportCsv(table,ths){
    function q(v){v=String(v==null?'':v).replace(/\s+/g,' ').trim();return '"'+v.replace(/"/g,'""')+'"';}
    var lines=[ths.map(function(th){return q(th.textContent.replace(/[⇅▲▼]/g,''));}).join(';')];
    Array.prototype.forEach.call(table.tBodies[0].rows,function(tr){
      if(tr.classList.contains('ap-hidden')||tr.hasAttribute('data-ap-detail')) return;
      lines.push(Array.prototype.map.call(tr.cells,function(td){return q(td.textContent);}).join(';'));
    });
    var blob=new Blob(['\ufeff'+lines.join('\r\n')],{type:'text/csv;charset=utf-8'});
    var a=document.createElement('a'); a.href=URL.createObjectURL(blob);
    a.download='tabela_'+new Date().toISOString().slice(0,10)+'.csv';
    document.body.appendChild(a); a.click(); setTimeout(function(){URL.revokeObjectURL(a.href);a.remove();},500);
  }
  function enhance(table){
    if(table.__ap) return; 
    var thead=table.tHead; if(!thead||thead.rows.length!==1) return;
    var ths=Array.prototype.slice.call(thead.rows[0].cells);
    if(ths.some(function(th){return th.colSpan>1;})) return;
    var tbody=table.tBodies[0]; if(!tbody) return;
    var st={col:-1,dir:0,busy:false,q:''};
    table.__ap=st;
    var opts=(table.getAttribute('data-ap-table')||'').split(/\s+/);

    ths.forEach(function(th,i){
      if(th.hasAttribute('data-ap-nosort')) return;
      if(!(th.textContent||'').replace(/[⇅▲▼\s]/g,'')) return;
      var btn=document.createElement('button'); btn.type='button'; btn.className='ap-th-btn';
      btn.title='Ordenar por esta coluna';
      while(th.firstChild) btn.appendChild(th.firstChild);
      // remove marcadores de ordenação antigos digitados no HTML (ex.: ⇅)
      btn.innerHTML=btn.innerHTML.replace(/\s*[⇅▲▼]\s*$/,'');
      var ind=document.createElement('span'); ind.className='ap-ind'; ind.setAttribute('aria-hidden','true'); ind.textContent='⇅';
      btn.appendChild(ind); th.appendChild(btn); th.setAttribute('aria-sort','none');
      btn.addEventListener('click',function(){
        if(st.col===i){ st.dir = st.dir===1 ? -1 : (st.dir===-1 ? 0 : 1); } else { st.col=i; st.dir=1; }
        if(st.dir===0) st.col=-1;
        apply();
      });
    });

    function mark(){
      ths.forEach(function(th,i){
        if(!th.hasAttribute('aria-sort')) return;
        var d=(i===st.col&&st.dir!==0)?(st.dir===1?'ascending':'descending'):'none';
        th.setAttribute('aria-sort',d);
        var ind=th.querySelector('.ap-ind'); if(ind) ind.textContent=d==='ascending'?'▲':(d==='descending'?'▼':'⇅');
      });
    }
    function apply(){
      st.busy=true;
      try{
        var groups=bodyGroups(tbody);
        groups.sort(function(a,b){return a.idx-b.idx;});
        if(st.col>=0&&st.dir!==0){
          var type=colType(groups,st.col), dir=st.dir;
          var keyOf=function(g){var r=cellRaw(g.main.cells[st.col]); if(r===''||r==='—'||r==='-') return {e:true};
            if(type==='num'){var n=parseNum(r); return n===null?{e:true}:{e:false,v:n};}
            if(type==='date'){var d=parseDate(r); return d===null?{e:true}:{e:false,v:d};}
            return {e:false,v:r};};
          groups.forEach(function(g){g.k=keyOf(g);});
          groups.sort(function(a,b){
            if(a.k.e&&b.k.e) return a.idx-b.idx; if(a.k.e) return 1; if(b.k.e) return -1;
            var c=(type==='text')?collator.compare(a.k.v,b.k.v):(a.k.v-b.k.v);
            return c? c*dir : a.idx-b.idx;
          });
        }
        var frag=document.createDocumentFragment();
        groups.forEach(function(g){g.rows.forEach(function(r){frag.appendChild(r);});});
        tbody.appendChild(frag);
        filter();
      } finally { st.busy=false; if(st.obs) st.obs.takeRecords(); }
      mark();
    }
    // busca opcional: data-ap-table="search"
    var counter=null;
    function filter(){
      if(!opts.includes('search')) return;
      var q=(st.q||'').toLowerCase(), total=0, shown=0;
      bodyGroups(tbody).forEach(function(g){
        var txt=g.rows.map(function(r){return r.textContent;}).join(' ').toLowerCase();
        var ok=!q||txt.indexOf(q)>=0; total++; if(ok) shown++;
        g.rows.forEach(function(r){ if(ok) r.classList.remove('ap-hidden'); else r.classList.add('ap-hidden'); });
      });
      if(counter) counter.textContent = total? (shown===0 ? ('Nenhum registro encontrado para “'+(st.q||'')+'”. Limpe a busca para ver os '+total.toLocaleString('pt-BR')+' registros.') : ('Mostrando '+shown.toLocaleString('pt-BR')+' de '+total.toLocaleString('pt-BR'))) : '';
    }
    if(opts.includes('search')){
      var tools=document.createElement('div'); tools.className='ap-tools';
      var inp=document.createElement('input'); inp.type='search'; inp.placeholder='Buscar na tabela'; inp.setAttribute('aria-label','Buscar na tabela');
      counter=document.createElement('span'); counter.className='ap-count'; counter.setAttribute('aria-live','polite');
      inp.addEventListener('input',function(){st.q=inp.value;filter();});
      tools.appendChild(inp); tools.appendChild(counter);
      if(opts.includes('export')){
        var ex=document.createElement('button'); ex.type='button'; ex.className='ap-export'; ex.textContent='Exportar CSV';
        ex.addEventListener('click',function(){exportCsv(table,ths);});
        tools.appendChild(ex);
      }
      var host=table.parentElement&&/(^|\s)(tableWrap|table-wrap)(\s|$)/.test(table.parentElement.className)?table.parentElement:table;
      host.parentNode.insertBefore(tools,host);
      filter();
    }
    // tbody preenchido/atualizado por JS depois do carregamento: reaplica ordem e busca
    var obs=new MutationObserver(function(){ if(st.busy) return; apply(); });
    obs.observe(tbody,{childList:true});
    st.obs=obs;
  }

  function enhanceKpi(el){
    if(el.__apk) return; el.__apk=true;
    var href=el.getAttribute('data-ap-href'); if(!href) return;
    if(el.tagName!=='A'&&el.tagName!=='BUTTON'){ el.setAttribute('role','link'); el.tabIndex=0; }
    el.title=el.title||'Abrir os registros';
    var go=function(){ window.location.href=href; };
    el.addEventListener('click',function(e){ if(e.target.closest('a,button')&&e.target.closest('a,button')!==el) return; go(); });
    el.addEventListener('keydown',function(e){ if(e.key==='Enter'||e.key===' '){ e.preventDefault(); go(); } });
  }

  function scan(root){
    (root.querySelectorAll?root.querySelectorAll('table[data-ap-table]'):[]).forEach(enhance);
    (root.querySelectorAll?root.querySelectorAll('[data-ap-href]'):[]).forEach(enhanceKpi);
    if(root.matches&&root.matches('table[data-ap-table]')) enhance(root);
    if(root.matches&&root.matches('[data-ap-href]')) enhanceKpi(root);
  }
  function start(){
    scan(document);
    new MutationObserver(function(muts){
      muts.forEach(function(m){ m.addedNodes.forEach(function(n){ if(n.nodeType===1) scan(n); }); });
    }).observe(document.body,{childList:true,subtree:true});
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',start); else start();
})();
/* V87.6 REV83 — pré-visualização do visual novo: só liga neste navegador (localStorage), nunca para os demais usuários. */
(function(){
  /* V87.6 REV84 — visual novo ligado por padrão; "0" no navegador desliga só nele. */
  try{ if(localStorage.getItem('ap_preview')!=='0') document.documentElement.classList.add('ap-new'); }catch(e){ document.documentElement.classList.add('ap-new'); }
  var RULES=[
    ['danger',/^(excluir|apagar|remover|deletar|descartar|arquivar|compactar|desativar|inativar|bloquear|encerrar)/],
    ['success',/^(aprovar|concluir|confirmar|receber|finalizar|liberar|autorizar|aceitar|iniciar|ativar|reativar)/],
    ['warn',/^(reabrir|pausar|reprocessar|devolver|reverter|desfazer|revisar|reenviar|recalcular)/],
    ['info',/^(importar|exportar|baixar|download|sincronizar|imprimir|anexar|upload|ver plano|simular)/],
    ['neutral',/^(voltar|cancelar|fechar|dispensar|ignorar)/],
    ['primary',/^(salvar|registrar|gerar|enviar|criar|novo|nova|adicionar|cadastrar|entrar|aplicar|publicar|solicitar|atribuir|alocar)/]
  ];
  var SKIP='.navDropBtn,.navInstall,.ap-th-btn,.navDropMenu,[role="tab"],[class*="tab"],.on,.active,th';
  function label(el){ var t=(el.value&&el.tagName==='INPUT'?el.value:el.textContent)||''; return t.normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/^[^a-zA-Z]+/,'').trim().toLowerCase(); }
  function tag(el){
    if(el.hasAttribute('data-ap-v')) return;
    if(el.matches(SKIP)||el.closest('.navDropMenu,.tabs,[role="tablist"]')) return;
    var st=el.getAttribute('style')||''; if(/background/i.test(st)) return;
    var t=label(el); if(!t) return;
    for(var i=0;i<RULES.length;i++){ if(RULES[i][1].test(t)){ el.setAttribute('data-ap-v',RULES[i][0]); return; } }
  }
  function scanButtons(root){
    if(!document.documentElement.classList.contains('ap-new')) return;
    var list=root.querySelectorAll?root.querySelectorAll('button,input[type="button"],input[type="submit"],a.btn'):[];
    Array.prototype.forEach.call(list,tag);
    if(root.matches&&root.matches('button,input[type="button"],input[type="submit"],a.btn')) tag(root);
  }
  function startBtns(){
    scanButtons(document);
    new MutationObserver(function(muts){ muts.forEach(function(m){ m.addedNodes.forEach(function(n){ if(n.nodeType===1) scanButtons(n); }); }); }).observe(document.body,{childList:true,subtree:true});
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',startBtns); else startBtns();
})();
