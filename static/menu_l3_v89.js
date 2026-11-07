/* V89 — menu com terceiro nível (variante 2: painel ao lado no computador; lista que abre e fecha no celular).
   Só roda com a chave "menu_terceiro_nivel" ligada. Nunca cria acesso: só enfeita links que o servidor já entregou ao usuário. */
(()=>{try{
 if(!(window.AP_FLAGS&&window.AP_FLAGS.menu_terceiro_nivel))return;
 const SECS=window.AP_DIAG_SECS||[];
 const OTHER={
  '/patrimonio':['Busca global','Filtros de Equipamentos','Central Executiva do Inventário','Saúde e confiabilidade do parque','Situação do parque por localidade'],
  '/documentos/acessos':['Gerar documento oficial','Motiva (APT)','Pendências de atualização','Revisões geradas'],
  '/visao-panoramica':['Importar ZIP do WhatsApp','Diagnóstico da Visão Panorâmica','Rastreamento das Evidências','Progresso das visões panorâmicas','Localidades'],
  '/documentos-materiais':['Meus documentos','Minhas APTs','Minha carga atual','Solicitação de material','Entrega de Materiais / Ferramentas','Dossiê dos colaboradores','Devolução de Materiais / Ferramentas','Cadastro de Materiais / Ferramentas / Consumíveis','Kits configuráveis'],
  '/equipes':['Filtros de equipes','Técnico mais próximo','Mapa operacional','Escala por dias','Operação por data','Gerenciar equipe e escala'],
  '/usuarios':['Novo usuário','Perfis de acesso','Usuários cadastrados','Usuários arquivados'],
  '/portal-cliente/gestao-agendamentos':['Solicitados hoje','Programados / recebimentos de hoje','Aguardando recebimento','Cancelados','Todos'],
  '/portal-cliente/cadastro-clientes':['Novo cliente / empresa','Empresas e garagens cadastradas','Acessos externos do Portal do Cliente'],
  '/engenharia/estoque':['Materiais da localidade','Novo material provisório','Detalhamento','Movimentações recentes'],
  '/troca-chips':['Atualizar base por planilha','Troca de Chip Recarga','Ativos da base'],
  '/troca-chips-emv':['Atualizar base por planilha','Bloqueio não encontrado na base','Bloqueios / pendências'],
  '/central-operacional':['Alertas operacionais','Distribuição da operação','Equipe operacional'],
  '/inteligencia-operacional':['Previsão de capacidade','Prioridade automática','Anomalias'],
  '/topdesk':['Filtros de análise','Evolução mensal','Central de Atenção','Principais falhas','Equipamentos crônicos','Chamados por linha','Localidades críticas','Mapa de calor','Produtividade técnica','Produtividade × reincidência','Importação TopDesk'],
  '/gestao-360':['O que precisa de atenção?','Ir direto para a ação','Atividade recente da plataforma'],
  '/gestao/rastreabilidade-jornada':['Histórico GPS por estações','Autorizações de jornada','Folgas e trocas de folga'],
  '/saude-plataforma':['Saúde do sistema','Resposta ao longo do tempo','Volume das principais bases','Capacidade e armazenamento','Índices críticos','Migrações de banco','Ciclo de vida T-Reports','Top 5 gargalos','Comparativo por versão','Auditoria de índices PostgreSQL','Raio-X das rotas'],
  '/financeiro/lancamentos':['Empresas / fornecedores','Pendências de cadastros','Lançamentos da competência','Novo lançamento mensal','Histórico de competências','Cadastro de fornecedor'],
  '/financeiro/coleta-valores':['Visão Geral / Custos','Programação de Coletas','Fila de Prioridades','Monitoramento'],
  '/financeiro/apuracao':['Importar bases','Legenda de conceitos','Comparativo entre coletas','Comparativo geral','Análise inteligente do período','Detalhamento da apuração'],
  '/atividades':['Dashboard','Minhas Atividades','Todas as Atividades','Concluídas / Histórico']
 };
 const MAP={'/diagnostico':SECS.map(s=>({label:s.label,href:'/diagnostico#sec-'+s.k}))};
 for(const [h,l] of Object.entries(OTHER))MAP[h]=l.map(t=>({label:t,href:h+'#ap-ir='+encodeURIComponent(t)}));
 // Vai até a seção pelo título (ou abre a aba com esse nome). Tenta por até ~4 s porque várias telas montam o conteúdo depois.
 const nz=t=>(t||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/\s+/g,' ').trim();
 const goto=()=>{const m=/#ap-ir=(.+)$/.exec(location.hash);if(!m)return;let want;try{want=nz(decodeURIComponent(m[1]))}catch(e){return}
  let tries=0;const run=()=>{tries++;const cand=[...document.querySelectorAll('main h1,main h2,main h3,main summary,main [role=tab],main button[data-tab],main .tabs button,main .tabBtn,main a[data-tab],main button[data-view]')];
   const el=cand.find(e=>nz(e.textContent).startsWith(want));
   if(el){if(/^(BUTTON|A)$/.test(el.tagName)||el.getAttribute('role')==='tab'){el.click()}
    const box=el.closest('details')||el.closest('section,.card')||el;if(box.tagName==='DETAILS')box.open=true;
    box.scrollIntoView({behavior:'smooth',block:'start'});const o=box.style.outline;box.style.outline='3px solid #2BA6A0';setTimeout(()=>{box.style.outline=o},1800);return}
   if(tries<16)setTimeout(run,250)};run()};
 window.addEventListener('hashchange',goto);if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',goto);else goto();
 const root=document.getElementById('mainNavV424');if(!root)return;
 const st=document.createElement('style');
 st.textContent='.apL3Item{position:relative;display:block}.apL3Item>a{display:block;padding-right:34px!important}'
 +'.apL3Toggle{position:absolute;right:4px;top:50%;transform:translateY(-50%);border:0!important;background:transparent!important;box-shadow:none!important;min-width:0!important;width:auto!important;height:auto!important;color:inherit;cursor:pointer;font-size:14px;padding:4px 8px!important;line-height:1;margin:0}'
 +'.apL3Panel{display:none;background:#F8FAFD;border-left:3px solid #2BA6A0}.apL3Panel a{display:block;padding:7px 14px;font-size:13px;white-space:nowrap}'
 +'.apL3Panel h4{margin:6px 14px 4px;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:#5A6478}'
 +'.apL3Item.open>.apL3Panel{display:block}'
 +'@media(min-width:761px){.apL3Panel{position:absolute;left:100%;top:0;min-width:270px;box-shadow:0 12px 28px #17345d33;border:1px solid #DDE3EE;border-left:3px solid #2BA6A0;z-index:90010;padding:6px 0}'
 +'.apL3Item:hover>.apL3Panel,.apL3Item:focus-within>.apL3Panel{display:block}.apL3Toggle{pointer-events:none}}'
 +'@media(max-width:760px){.apL3Panel{margin-left:14px}}';
 document.head.appendChild(st);
 for(const [href,items] of Object.entries(MAP)){
  for(const a of root.querySelectorAll('.navDropMenu a[href="'+href+'"]')){
   if(a.closest('.apL3Item'))continue;
   const wrap=document.createElement('div');wrap.className='apL3Item';a.parentNode.insertBefore(wrap,a);wrap.appendChild(a);
   const tg=document.createElement('button');tg.type='button';tg.className='apL3Toggle';tg.textContent='▸';tg.setAttribute('aria-label','Mostrar seções de '+(a.textContent||'').trim());tg.setAttribute('aria-expanded','false');
   const panel=document.createElement('div');panel.className='apL3Panel';
   const h=document.createElement('h4');h.textContent=(a.textContent||'').trim();panel.appendChild(h);
   for(const it of items){const l=document.createElement('a');l.href=it.href;l.textContent=it.label;panel.appendChild(l)}
   wrap.append(tg,panel);
   tg.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();const o=wrap.classList.toggle('open');tg.setAttribute('aria-expanded',o?'true':'false');tg.textContent=o?'▾':'▸'});
   a.addEventListener('keydown',e=>{if(e.key==='ArrowRight'){const f=panel.querySelector('a');if(f){e.preventDefault();wrap.classList.add('open');f.focus()}}});
   panel.addEventListener('keydown',e=>{if(e.key==='ArrowLeft'||e.key==='Escape'){e.preventDefault();wrap.classList.remove('open');a.focus()}});
  }
 }
}catch(e){console.error('MENU_L3_V89',e)}})();
