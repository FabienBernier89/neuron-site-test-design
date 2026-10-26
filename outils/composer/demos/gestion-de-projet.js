/* Démo Gestion de projet · tunnel en trois étapes, état réel reflété dans le stepper et les boutons.
   Textes lus dans le bloc data-textes (traduit avec la page) ; les langues cibles se lisent sur le libellé de leur case. */
(function(){
  var cx=document.getElementById('cx'); if(!cx){return;}
  var reduce=!!(window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  var $=function(id){return document.getElementById(id);};
  var each=function(list,fn){Array.prototype.forEach.call(list,fn);};
  var lire=function(s){var e=document.querySelector('script['+s+']');return e?JSON.parse(e.textContent):{};};
  var TX=lire('data-textes');
  /* Texte de la page ; {variable} remplacée par sa valeur */
  function t(k,v){return String(TX[k]||'').replace(/\{(\w+)\}/g,function(m,n){return v&&n in v?v[n]:m;});}
  var state={step:1,langs:[],file:false};

  /* Navigation entre étapes */
  var steps=[$('cxpStep1'),$('cxpStep2'),$('cxpStep3')];
  var items=cx.querySelectorAll('.cxp-stepper li');
  var prev=$('cxpPrev'),next=$('cxpNext');
  function render(focus){
    for(var i=0;i<3;i++){
      var n=i+1,on=n===state.step;
      steps[i].classList.toggle('on',on);
      items[i].classList.toggle('on',on);
      items[i].classList.toggle('done',n<state.step);
      if(on){items[i].setAttribute('aria-current','step');}else{items[i].removeAttribute('aria-current');}
    }
    prev.disabled=state.step===1;
    next.hidden=state.step===3;
    next.disabled=(state.step===1&&!state.langs.length)||(state.step===2&&!state.file);
    if(focus){var el=steps[state.step-1].querySelector('.cxp-title');if(el){el.focus();}}
  }
  prev.addEventListener('click',function(){if(state.step>1){state.step--;render(true);}});
  next.addEventListener('click',function(){if(state.step<3&&!next.disabled){state.step++;render(true);}});

  /* Étape 1 · nom du projet (nom par défaut : valeur d'origine du champ) */
  var nameIn=$('cxpName'),defBtn=$('cxpDefault');
  defBtn.addEventListener('click',function(){
    var off=defBtn.classList.toggle('off');
    defBtn.setAttribute('aria-pressed',off?'false':'true');
    nameIn.readOnly=!off;
    if(off){nameIn.focus();nameIn.select();}else{nameIn.value=nameIn.defaultValue;}
  });

  /* Étape 1 · confidentialité */
  var cards=cx.querySelectorAll('.cxp-card');
  each(cards,function(c){c.addEventListener('click',function(){
    each(cards,function(o){var on=o===c;o.classList.toggle('on',on);o.setAttribute('aria-checked',on?'true':'false');});
  });});

  /* Étape 1 · langues cibles : la valeur de chaque case est la clé de l'état, son libellé (traduit) est affiché */
  var langBtn=$('cxpLangBtn'),langPop=$('cxpLangPop'),langSearch=$('cxpLangSearch'),langList=$('cxpLangList'),chips=$('cxpLangChips');
  function openPop(open){langPop.hidden=!open;langBtn.setAttribute('aria-expanded',open?'true':'false');}
  langBtn.addEventListener('click',function(){var open=langPop.hidden;openPop(open);if(open){langSearch.focus();}});
  langSearch.addEventListener('input',function(){
    var q=langSearch.value.trim().toLowerCase();
    each(langList.querySelectorAll('li'),function(li){li.hidden=!!q&&li.textContent.toLowerCase().indexOf(q)<0;});
  });
  function caseDe(l){var r=null;each(langList.querySelectorAll('input[type="checkbox"]'),function(b){if(b.value===l){r=b;}});return r;}
  function libelle(l){var b=caseDe(l);return b?b.closest("label").textContent.trim():l;}
  function renderChips(){
    chips.innerHTML='';
    state.langs.forEach(function(l){
      var nom=libelle(l);
      var b=document.createElement('button');b.type='button';b.className='cx-chip on';
      b.setAttribute('aria-label',t('retirer',{langue:nom}));
      b.appendChild(document.createTextNode(nom+' '));
      var x=document.createElement('span');x.setAttribute('aria-hidden','true');x.textContent='×';b.appendChild(x);
      b.addEventListener('click',function(){setLang(l,false);});
      chips.appendChild(b);
    });
    chips.hidden=!state.langs.length;
  }
  function setLang(l,on){
    var box=caseDe(l);if(box){box.checked=on;}
    var i=state.langs.indexOf(l);
    if(on&&i<0){state.langs.push(l);}
    if(!on&&i>=0){state.langs.splice(i,1);}
    renderChips();render(false);
  }
  langList.addEventListener('change',function(e){if(e.target&&e.target.type==='checkbox'){setLang(e.target.value,e.target.checked);}});
  langPop.addEventListener('keydown',function(e){if(e.key==='Escape'){openPop(false);langBtn.focus();}});
  document.addEventListener('click',function(e){if(!langPop.hidden&&!langPop.contains(e.target)&&e.target!==langBtn&&!langBtn.contains(e.target)){openPop(false);}});

  /* Étape 2 · dépôt simulé */
  var drop=$('cxpDrop'),card=$('cxpFileCard'),bar=$('cxpFileBar'),sub=$('cxpFileSub'),meta=$('cxpFileMeta'),del=$('cxpFileDel'),tm;
  drop.addEventListener('click',function(){
    if(state.file||drop.disabled){return;}
    drop.disabled=true;card.hidden=false;meta.hidden=true;sub.hidden=false;sub.textContent=t('analyse');
    bar.style.transition='none';bar.style.transform='scaleX(0)';
    void bar.offsetWidth;
    bar.style.transition='';
    requestAnimationFrame(function(){bar.style.transform='scaleX(1)';});
    clearTimeout(tm);
    tm=setTimeout(function(){
      sub.hidden=true;
      meta.hidden=false;state.file=true;render(false);next.focus();
    },reduce?0:2400);
  });
  del.addEventListener('click',function(){
    clearTimeout(tm);
    card.hidden=true;state.file=false;drop.disabled=false;
    bar.style.transition='none';bar.style.transform='scaleX(0)';
    render(false);drop.focus();
  });

  /* Étape 3 · onglets Internal review / Custom workflow */
  var tabs=[$('cxpTabInt'),$('cxpTabCus')],pans=[$('cxpPanInt'),$('cxpPanCus')];
  function selTab(i){each(tabs,function(el,k){var on=k===i;el.classList.toggle('on',on);el.setAttribute('aria-selected',on?'true':'false');el.tabIndex=on?0:-1;pans[k].hidden=!on;});}
  each(tabs,function(el,i){
    el.addEventListener('click',function(){selTab(i);});
    el.addEventListener('keydown',function(e){if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();var n=(i+1)%2;selTab(n);tabs[n].focus();}});
  });
  $('cxpCreate').addEventListener('click',function(){$('cxpCreateMsg').hidden=false;});

  /* Étape 3 · Custom workflow : priorité, sélection, info, estimation */
  var yn=cx.querySelectorAll('.cxp-yn-btn');
  each(yn,function(b){b.addEventListener('click',function(){each(yn,function(o){var on=o===b;o.classList.toggle('on',on);o.setAttribute('aria-pressed',on?'true':'false');});});});
  var selAll=$('cxpSelAll'),rowBox=$('cxpRowBox');
  selAll.addEventListener('change',function(){rowBox.checked=selAll.checked;});
  rowBox.addEventListener('change',function(){selAll.checked=rowBox.checked;});
  var infoBtn=$('cxpInfoBtn'),info=$('cxpInfo');
  infoBtn.addEventListener('click',function(){var open=info.hidden;info.hidden=!open;infoBtn.setAttribute('aria-expanded',open?'true':'false');});

  var due=$('cxpDue'),rev=$('cxpRev'),level=$('cxpLevel'),quote=$('cxpQuote'),quoteMsg=$('cxpQuoteMsg'),estNote=$('cxpEstNote'),et;
  var dd={prep:$('cxpEstPrep'),inter:$('cxpEstInt'),ext:$('cxpEstExt'),tot:$('cxpEstTot')};
  function setEst(v){for(var k in dd){if(dd.hasOwnProperty(k)){dd[k].textContent=v[k];}}}
  function compute(){
    /* relecture externe : première option du sélecteur (son libellé suit la langue de la page) */
    var lvl=level.value,d=due.value,externe=rev.selectedIndex===0;
    quote.disabled=!(lvl&&d);
    quoteMsg.hidden=true;
    clearTimeout(et);
    if(!lvl){setEst({prep:'-',inter:'-',ext:'-',tot:'-'});estNote.hidden=true;return;}
    for(var k in dd){if(dd.hasOwnProperty(k)){dd[k].innerHTML='<span class="cx-shim"></span>';}}
    et=setTimeout(function(){
      if(externe&&lvl==='full'&&d==='2026-09-24'){
        setEst({prep:t('un_jour'),inter:t('zero_heure'),ext:t('un_jour'),tot:t('un_jour')});estNote.hidden=true;
      }else{
        var c=t('a_calculer');
        setEst({prep:c,inter:c,ext:c,tot:c});estNote.hidden=false;
      }
    },reduce?0:700);
  }
  due.addEventListener('change',compute);rev.addEventListener('change',compute);level.addEventListener('change',compute);
  quote.addEventListener('click',function(){if(!quote.disabled){quoteMsg.hidden=false;}});

  render(false);
  compute();
})();
