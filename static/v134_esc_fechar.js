/* V88.0 REV62 — padrão do sistema: janela aberta por big number/indicador fecha com ESC (além do botão Fechar).
   Fecha só a janela de cima; se a própria tela já tratar o ESC, não faz nada. */
(()=>{
 const SEL='.modal,[role="dialog"],[aria-modal="true"],.exM,.fpM,[id$="Modal"],[id$="modal"],.modalBack,.overlay';
 const vis=e=>{if(!e||e.hidden)return false;const s=getComputedStyle(e);return s.display!=='none'&&s.visibility!=='hidden'&&e.getClientRects().length>0};
 const topo=()=>{let best=null,bz=-1;document.querySelectorAll(SEL).forEach((e,i)=>{if(!vis(e))return;if(e.parentElement&&e.parentElement.closest(SEL)&&vis(e.parentElement.closest(SEL)))return;
   const z=parseInt(getComputedStyle(e).zIndex)||0,k=z*100000+i;if(k>=bz){bz=k;best=e}});return best};
 const fechar=e=>{const bts=[...e.querySelectorAll('button,a,[role="button"]')];
   const b=bts.find(x=>/^(fechar|×|✕|x|voltar)$/i.test((x.textContent||'').trim()))||bts.find(x=>/fechar|close/i.test((x.getAttribute('aria-label')||'')+' '+(x.className||'')))||null;
   if(b){b.click();return}
   e.hidden=true};
 document.addEventListener('keydown',ev=>{if(ev.key!=='Escape'||ev.defaultPrevented)return;
   const t=ev.target;if(t&&t.tagName==='SELECT')return;
   const alvo=topo();if(!alvo)return;
   setTimeout(()=>{if(vis(alvo))fechar(alvo)},0)},true);
})();
