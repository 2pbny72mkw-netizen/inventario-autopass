/* V88.0 REV2 — botão "Excluir POS (definitivo)" no diálogo da Troca POS Metrô (somente gestão; injetado pelo servidor). */
(function(){
  var cur={id:'',terminal:''};
  var orig=window.openPos;
  if(typeof orig==='function'){
    window.openPos=function(el){
      try{cur.id=el&&el.dataset?el.dataset.id:'';cur.terminal=el&&el.dataset?(el.dataset.terminal||''):'';}catch(e){}
      return orig.apply(this,arguments);
    };
  }
  function addButton(){
    var footer=document.querySelector('#posdialog footer');
    if(!footer||document.getElementById('posHardDelete'))return;
    var b=document.createElement('button');
    b.type='button';b.id='posHardDelete';b.textContent='Excluir POS (definitivo)';
    b.style.cssText='color:#fff;background:#b42318;border:1px solid #b42318;border-radius:8px;padding:8px 12px;font-weight:700;cursor:pointer';
    b.addEventListener('click',function(){
      if(!cur.id){alert('Abra o POS novamente para excluir.');return;}
      var msg='EXCLUIR DEFINITIVAMENTE o POS '+cur.terminal+'?\n\nO cadastro, o histórico de trocas e TODAS as fotografias deste POS serão apagados e não poderão ser recuperados pelo sistema (fica apenas um registro de auditoria).\n\nPara confirmar, digite a identificação do POS exatamente como aparece:\n'+cur.terminal;
      var typed=window.prompt(msg,'');
      if(typed===null)return;
      if(typed.trim().toLowerCase()!==cur.terminal.trim().toLowerCase()){alert('Identificação diferente. Nada foi excluído.');return;}
      b.disabled=true;
      var f=document.createElement('form');f.method='post';f.action='/field/troca-pos-metro/'+encodeURIComponent(cur.id)+'/excluir-pos';
      var i=document.createElement('input');i.type='hidden';i.name='confirmar';i.value=typed.trim();f.appendChild(i);
      document.body.appendChild(f);f.submit();
    });
    footer.insertBefore(b,footer.firstChild);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',addButton);else addButton();
})();
