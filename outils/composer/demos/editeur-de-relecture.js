/* Démo Éditeur de relecture · segments éditables, confirmation, filtres et panneau latéral à quatre onglets.
   Contrat fictif ; les extraits CHnell reprennent des résultats réels déjà publiés sur le site.
   Textes lus dans le bloc data-textes (traduit avec la page), données dans le bloc data-donnees (jamais traduit : la
   source française et la traduction allemande du contrat restent celles de la démo dans toutes les langues). */
(function(){
  var cx=document.getElementById('cx'); if(!cx){return;}
  var reduce=!!(window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  var $=function(id){return document.getElementById(id);};
  var each=function(list,fn){Array.prototype.forEach.call(list,fn);};
  var lire=function(s){var e=document.querySelector('script['+s+']');return e?JSON.parse(e.textContent):{};};
  var TX=lire('data-textes'),D=lire('data-donnees');
  /* Texte de la page ; {variable} remplacée par sa valeur */
  function t(k,v){return String(TX[k]||'').replace(/\{(\w+)\}/g,function(m,n){return v&&n in v?v[n]:m;});}
  /* Langue d'un passage (WCAG 3.1.2) : posée si elle diffère de celle de la page */
  var PL=(document.documentElement.getAttribute('lang')||'fr').slice(0,2);
  function lg(c){return c===PL?'':' lang="'+c+'"';}
  function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
  function norm(s){return String(s).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'');}
  var liveEl=$('cxeLive'),lt;
  function say(t){clearTimeout(lt);liveEl.textContent='';lt=setTimeout(function(){liveEl.textContent=t;},40);}

  /* ---------- Données de démonstration ---------- */
  var ALT=D.alt;
  ALT[5]=ALT[0];
  var MEM=D.mem;
  var NOTE={1:t('memoire_note_1'),2:t('memoire_note_2'),3:t('memoire_note_3')};
  var REPH=D.reph;
  var LK=D.lk;
  var R=D.recherche;
  var REP={0:5,5:0};

  /* ---------- Segments ---------- */
  var rows=cx.querySelectorAll('.cxe-tab tbody tr[data-i]');
  var tg=[],src=[],box=[],sel=2;
  var last=[];
  each(rows,function(r,i){tg[i]=r.querySelector('.cxe-tgt');src[i]=r.querySelector('.cxe-src').textContent;box[i]=r.querySelector('.cxe-chk');last[i]=tg[i].textContent;});

  function select(i){
    if(i===sel){return;}
    sel=i;
    each(rows,function(r,k){r.classList.toggle('sel',k===i);});
    renderMem();renderAlt();renderReph(false);
  }
  each(rows,function(r,i){
    r.addEventListener('click',function(e){
      if(e.target.closest('input,button')){return;}
      select(i);
    });
    tg[i].addEventListener('focus',function(){select(i);});
  });

  /* Progression : une case par segment, case générale en tête */
  var all=$('cxeAll'),pbar=$('cxePBar'),pnum=$('cxePNum');
  function progress(){
    var n=0;box.forEach(function(b){if(b.checked){n++;}});
    var p=Math.round(n*100/box.length);
    pbar.style.transform='scaleX('+(p/100)+')';pnum.textContent=p+'%';
    all.checked=n===box.length;all.indeterminate=n>0&&n<box.length;
  }
  box.forEach(function(b,i){b.addEventListener('change',function(){progress();say(b.checked?t('segment_confirme',{n:i}):t('segment_a_relire',{n:i}));});});
  all.addEventListener('change',function(){var v=all.checked;box.forEach(function(b){b.checked=v;});progress();say(v?t('tous_confirmes'):t('aucun_confirme'));});

  /* Filtres source et traduction */
  var fs=$('cxeFs'),ft=$('cxeFt'),none=$('cxeNone');
  function filter(){
    var a=norm(fs.value.trim()),b=norm(ft.value.trim()),vis=0;
    each(rows,function(r,i){var ok=(!a||norm(src[i]).indexOf(a)>=0)&&(!b||norm(tg[i].textContent).indexOf(b)>=0);r.hidden=!ok;if(ok){vis++;}});
    none.hidden=vis>0;
  }
  fs.addEventListener('input',filter);ft.addEventListener('input',filter);
  each(cx.querySelectorAll('.cxe-clr[data-for]'),function(btn){btn.addEventListener('click',function(){var inp=$(btn.getAttribute('data-for'));inp.value='';filter();inp.focus();});});

  /* Mise à jour d'une traduction (mémoire, reformulation, Sync, copie de la source) */
  function setT(i,text,msg,noProp){
    tg[i].textContent=text;last[i]=text;
    if(box[i].checked){box[i].checked=false;progress();}
    var td=tg[i].parentNode;td.classList.remove('cxe-upd');void td.offsetWidth;td.classList.add('cxe-upd');
    if(msg){say(msg);}
    if(!noProp){checkProp(i);}
    filter();
  }
  $('cxeCopy').addEventListener('click',function(){setT(sel,src[sel],t('source_copiee',{n:sel}));});

  /* Saisie directe : texte brut, pas de retour à la ligne, la case de confirmation se décoche */
  var editT={};
  tg.forEach(function(el,i){
    el.addEventListener('input',function(){
      if(box[i].checked){box[i].checked=false;progress();}
      clearTimeout(editT[i]);editT[i]=setTimeout(function(){edited(i);},900);
    });
    el.addEventListener('blur',function(){clearTimeout(editT[i]);edited(i);});
    el.addEventListener('keydown',function(e){if(e.key==='Enter'){e.preventDefault();}});
    el.addEventListener('paste',function(e){
      e.preventDefault();
      var txt=((e.clipboardData||window.clipboardData).getData('text')||'').replace(/\s+/g,' ');
      var s=window.getSelection();if(!s.rangeCount){return;}
      var rg=s.getRangeAt(0);rg.deleteContents();var node=document.createTextNode(txt);rg.insertNode(node);
      rg.setStartAfter(node);rg.collapse(true);s.removeAllRanges();s.addRange(rg);
    });
  });

  /* ---------- Panneau latéral ---------- */
  var app=$('cxeApp'),fold=$('cxeFold'),title=$('cxeTitle');
  var rbs=cx.querySelectorAll('.cxe-rb'),pans=[$('cxeP0'),$('cxeP1'),$('cxeP2'),$('cxeP3')];
  function setFold(on){
    app.classList.toggle('fold',on);
    fold.setAttribute('aria-expanded',on?'false':'true');
    fold.setAttribute('aria-label',on?t('deplier'):t('replier'));
  }
  fold.addEventListener('click',function(){setFold(!app.classList.contains('fold'));});
  function tab(k,focus){
    each(rbs,function(b,j){var on=j===k;b.setAttribute('aria-selected',on?'true':'false');b.tabIndex=on?0:-1;pans[j].hidden=!on;});
    title.textContent=rbs[k].getAttribute('data-title');
    if(app.classList.contains('fold')){setFold(false);}
    if(focus){rbs[k].focus();}
  }
  each(rbs,function(b,j){
    b.addEventListener('click',function(){tab(j);});
    b.addEventListener('keydown',function(e){
      var n=null,L=rbs.length;
      if(e.key==='ArrowDown'||e.key==='ArrowRight'){n=(j+1)%L;}
      else if(e.key==='ArrowUp'||e.key==='ArrowLeft'){n=(j+L-1)%L;}
      else if(e.key==='Home'){n=0;}else if(e.key==='End'){n=L-1;}
      if(n!==null){e.preventDefault();tab(n,true);}
    });
  });

  /* Onglet Translation memories */
  var memBox=$('cxeMem');
  function renderMem(){
    var m=MEM[sel];
    if(!m){memBox.innerHTML='<p class="cxe-empty">'+esc(t('memoire_vide',{n:sel}))+'</p>';return;}
    memBox.innerHTML='<div class="cxe-match"><p class="cxe-ml">From this project\'s TM</p><p class="cxe-ms"'+lg('fr')+'>'+esc(m.s)+'</p><p class="cxe-mt" lang="de">'+esc(m.t)+'</p><div class="cxe-ma"><button type="button" class="cx-btn cxe-sm" id="cxeMemOk">Apply</button></div></div><p class="cx-note">'+esc(NOTE[sel])+'</p>';
    $('cxeMemOk').addEventListener('click',function(){setT(sel,m.t,t('memoire_appliquee',{n:sel}));});
  }

  /* Onglet Fast Lookup : mémoires et CHnell, côté source ou cible */
  var lk=$('cxeLk'),q=$('cxeQ'),liveSw=$('cxeLiveSw'),side='src',lkT;
  var sideBtns=cx.querySelectorAll('.cxe-seg button');
  var RX={src:/int[ée]r[êe]ts?\s+moratoires?/gi,tgt:/Verzugszins\w*/g};
  function mark(text,rx){return esc(text).replace(rx,function(x){return '<mark>'+x+'</mark>';});}
  function block(list){
    return '<div class="cxe-res"><div class="cxe-rh"><span>Source</span><span>Target</span></div>'+list.map(function(r){
      return '<div class="cxe-rr"><p'+lg('fr')+'>'+mark(r.s,RX.src)+'</p><p lang="de">'+mark(r.t,RX.tgt)+'</p><p class="doc">'+esc(r.d)+'</p></div>';
    }).join('')+'</div>';
  }
  function lookup(announce){
    var v=norm(q.value.trim()),hit=false;
    if(v){hit=side==='src'?(v.indexOf('moratoire')>=0||v.indexOf('interet')>=0):(v.indexOf('verzug')>=0);}
    var h='<p class="cxe-h">Translation memories</p>'+(hit?block(LK.tm):'<p class="cxe-nr">No result</p>');
    h+='<p class="cxe-h">CHnell</p>'+(hit?block(LK.ch):'<p class="cxe-nr">No result</p>');
    if(!hit&&v){h+='<p class="cx-note">'+esc(t('recherche_essai',{source:R.source,cible:R.cible}))+'</p>';}
    lk.innerHTML=h;
    if(announce){say(hit?t('recherche_trouvee'):t('recherche_vide'));}
  }
  $('cxeQForm').addEventListener('submit',function(e){e.preventDefault();lookup(true);});
  q.addEventListener('input',function(){if(liveSw.getAttribute('aria-pressed')==='true'){clearTimeout(lkT);lkT=setTimeout(function(){lookup(true);},400);}});
  $('cxeQClr').addEventListener('click',function(){q.value='';lookup(false);q.focus();});
  liveSw.addEventListener('click',function(){var on=liveSw.getAttribute('aria-pressed')!=='true';liveSw.setAttribute('aria-pressed',on?'true':'false');liveSw.classList.toggle('off',!on);});
  each(sideBtns,function(b){b.addEventListener('click',function(){
    side=b.getAttribute('data-side');
    each(sideBtns,function(o){var on=o===b;o.classList.toggle('on',on);o.setAttribute('aria-pressed',on?'true':'false');});
    /* terme de la source française (côté Source) ou de la traduction allemande (côté Target), dans sa langue */
    q.value=side==='src'?R.source:R.cible;
    q.setAttribute('lang',side==='src'?'fr':'de');
    lookup(true);
  });});

  /* Onglet AI Assistant : Alternatives et Rephrasing */
  var aiT=[$('cxeAiA'),$('cxeAiR')],aiP=[$('cxeAiAP'),$('cxeAiRP')];
  function aiTab(k,focus){
    aiT.forEach(function(b,j){var on=j===k;b.classList.toggle('on',on);b.setAttribute('aria-selected',on?'true':'false');b.tabIndex=on?0:-1;aiP[j].hidden=!on;});
    if(focus){aiT[k].focus();}
  }
  aiT.forEach(function(b,j){
    b.addEventListener('click',function(){aiTab(j);});
    b.addEventListener('keydown',function(e){if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();aiTab(1-j,true);}});
  });
  var altBox=$('cxeAlt'),more=$('cxeMore'),shown=2,gt;
  function renderAlt(){
    altBox.innerHTML=ALT[sel].slice(0,shown).map(function(x){return '<p class="cxe-alt"><span lang="de">'+esc(x.t)+'</span> <span class="e">- '+esc(x.e)+'</span></p>';}).join('');
    more.disabled=shown>=ALT[sel].length;
  }
  more.addEventListener('click',function(){
    if(more.disabled){return;}
    more.disabled=true;
    altBox.insertAdjacentHTML('beforeend','<p class="cxe-alt"><span class="cx-shim" style="display:block"></span><span class="cx-shim" style="display:block;width:60%"></span></p>');
    clearTimeout(gt);
    gt=setTimeout(function(){shown=3;renderAlt();say(t('alternative_ajoutee',{moteur:ALT[sel][2].e}));},reduce?0:700);
  });

  var style=null,shorten=false,pStyle=null,pShort=false,rt;
  var rWrap=$('cxeRWrap'),rNote=$('cxeRNote'),rOut=$('cxeROut'),setB=$('cxeSet'),pop=$('cxePop');
  var chips=pop.querySelectorAll('[data-style]'),shortChip=$('cxeShort');
  function rephHTML(){var d=REPH[sel];return shorten?d.short:d[style||'none'];}
  function renderReph(anim){
    var d=REPH[sel];
    rWrap.hidden=!d;rNote.hidden=!!d;
    if(!d){return;}
    clearTimeout(rt);
    if(anim&&!reduce){
      rOut.innerHTML='<span class="cx-shim" style="display:block"></span><span class="cx-shim" style="display:block;width:70%"></span>';
      rt=setTimeout(function(){rOut.innerHTML=rephHTML();},650);
    }else{rOut.innerHTML=rephHTML();}
  }
  function syncChips(){
    each(chips,function(c){var on=c.getAttribute('data-style')===pStyle;c.classList.toggle('on',on);c.setAttribute('aria-pressed',on?'true':'false');});
    shortChip.classList.toggle('on',pShort);shortChip.setAttribute('aria-pressed',pShort?'true':'false');
  }
  function openPop(open){
    pop.classList.toggle('on',open);setB.setAttribute('aria-expanded',open?'true':'false');
    if(open){pStyle=style;pShort=shorten;syncChips();chips[0].focus();}
  }
  setB.addEventListener('click',function(){openPop(!pop.classList.contains('on'));});
  pop.addEventListener('keydown',function(e){if(e.key==='Escape'){openPop(false);setB.focus();}});
  each(chips,function(c){c.addEventListener('click',function(){var s=c.getAttribute('data-style');pStyle=pStyle===s?null:s;syncChips();});});
  shortChip.addEventListener('click',function(){pShort=!pShort;syncChips();});
  $('cxeReset').addEventListener('click',function(){pStyle=null;pShort=false;syncChips();});
  $('cxeSetOk').addEventListener('click',function(){style=pStyle;shorten=pShort;openPop(false);setB.focus();renderReph(true);say(t('reformulation_regeneree'));});
  $('cxeRegen').addEventListener('click',function(){renderReph(true);});
  $('cxeRApply').addEventListener('click',function(){if(REPH[sel]){setT(sel,rOut.textContent,t('reformulation_appliquee',{n:sel}));}});
  $('cxeGo4').addEventListener('click',function(){select(4);rows[4].scrollIntoView({block:'nearest',behavior:reduce?'auto':'smooth'});setB.focus();});

  /* Onglet Sync : conflits, modifications entrantes, propagation */
  var syncBox=$('cxeSync'),dot=$('cxeDot'),dotTxt=$('cxeDotTxt');
  var S=D.sync;
  var OK='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>';
  /* Une saisie réelle (texte différent du dernier connu) déclenche le contrôle des répétitions */
  function edited(i){var x=tg[i].textContent;if(x===last[i]){return;}last[i]=x;checkProp(i);filter();}
  function checkProp(i){
    if(!(i in REP)){return;}
    var j=REP[i];
    if(tg[i].textContent!==tg[j].textContent){
      S.prop={from:i,to:j,text:tg[i].textContent};renderSync();
      say(t('propagation_attente',{n:j}));
    }else if(S.prop){S.prop=null;renderSync();}
  }
  function renderSync(focusSel){
    var h='<div class="cxe-sblock"><p class="cxe-sh" id="cxeSh1" tabindex="-1">Conflicting changes</p>';
    if(S.conflict){
      var c=S.conflict;
      h+='<div class="cxe-sync"><p class="cxe-sl">Segment '+c.seg+'</p><div class="cxe-ver"><b>My Edit · AM</b><span lang="de">'+esc(c.mine)+'</span></div><div class="cxe-ver"><b>Last Edit · LM</b><span lang="de">'+esc(c.last)+'</span></div><div class="cxe-sact"><button type="button" class="cx-btn ghost cxe-sm" data-act="keep">Keep all My Edits</button><button type="button" class="cx-btn cxe-sm" data-act="applyall">Apply all Last Edits</button></div></div>';
    }else{h+='<p class="cxe-okst">No conflicting change to resolve.'+OK+'</p>';}
    h+='</div><div class="cxe-sblock"><p class="cxe-sh" id="cxeSh2" tabindex="-1">Incoming changes</p>';
    if(S.incoming){
      var n=S.incoming;
      h+='<div class="cxe-sync"><p class="cxe-sl">Segment '+n.seg+' · LM</p><div class="cxe-ver one"><span lang="de">'+esc(n.text)+'</span></div><div class="cxe-sact"><button type="button" class="cx-btn cxe-sm" data-act="incoming">Apply</button></div></div>';
    }else{h+='<p class="cxe-okst">No incoming change to apply.'+OK+'</p>';}
    h+='</div><div class="cxe-sblock"><p class="cxe-sh" id="cxeSh3" tabindex="-1">Propagation decisions</p>';
    if(S.prop){
      var p=S.prop;
      h+='<div class="cxe-sync"><p class="cxe-sl">Segment '+p.from+' · repeated</p><div class="cxe-ver one"><span lang="de">'+esc(p.text)+'</span></div><label class="cxe-pchk"><input type="checkbox" class="cxe-chk" id="cxePropBox" checked> Segment '+p.to+'</label><div class="cxe-sact"><button type="button" class="cx-btn ghost cxe-sm" data-act="asis">Keep as is</button><button type="button" class="cx-btn cxe-sm" data-act="prop">Apply</button></div></div>';
    }else{h+='<p class="cxe-okst">No propagation decision required.'+OK+'</p>';}
    h+='</div>';
    syncBox.innerHTML=h;
    var pend=(S.conflict?1:0)+(S.incoming?1:0)+(S.prop?1:0);
    dot.hidden=!pend;dotTxt.textContent=pend?', '+t(pend>1?'attente_plusieurs':'attente_un',{n:pend}):'';
    if(focusSel){var f=$(focusSel);if(f){f.focus();}}
  }
  syncBox.addEventListener('click',function(e){
    var b=e.target.closest('button[data-act]');if(!b){return;}
    var a=b.getAttribute('data-act');
    if(a==='keep'){S.conflict=null;renderSync('cxeSh1');say(t('conflit_garde'));}
    else if(a==='applyall'){var c=S.conflict;S.conflict=null;setT(c.seg,c.last,t('conflit_applique',{n:c.seg}),true);renderSync('cxeSh1');}
    else if(a==='incoming'){var n=S.incoming;S.incoming=null;setT(n.seg,n.text,t('entrante_appliquee',{n:n.seg}),true);renderSync('cxeSh2');}
    else if(a==='prop'){var p=S.prop,go=$('cxePropBox').checked;S.prop=null;if(go){setT(p.to,p.text,t('correction_propagee',{n:p.to}),true);}renderSync('cxeSh3');}
    else if(a==='asis'){S.prop=null;renderSync('cxeSh3');say(t('tel_quel'));}
  });

  /* État initial */
  progress();renderMem();renderAlt();renderReph(false);lookup(false);renderSync();
})();
