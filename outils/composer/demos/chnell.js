/* Démo CHnell : deux requêtes réelles (segments, domaines, sources et compteurs observés dans Corrext le 14 septembre 2026). Aucune donnée inventée.
   Textes lus dans le bloc data-textes (traduit avec la page), données dans le bloc data-donnees (jamais traduit). */
(function(){
  var $=function(id){return document.getElementById(id);};
  var cx=$("cx"); if(!cx) return;
  var lire=function(s){var e=document.querySelector("script["+s+"]");return e?JSON.parse(e.textContent):{};};
  var T=lire("data-textes"),DATA=lire("data-donnees");
  /* Texte de la page ; {variable} remplacée par sa valeur */
  function t(k,v){return String(T[k]||"").replace(/\{(\w+)\}/g,function(m,n){return v&&n in v?v[n]:m;});}
  /* Langue d'un passage (WCAG 3.1.2) : posée si elle diffère de celle de la page */
  var PL=(document.documentElement.getAttribute("lang")||"fr").slice(0,2);
  function lg(c){return c===PL?"":' lang="'+c+'"';}
  var reduce=window.matchMedia&&window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var q=$("cxlQ"),go=$("cxlGo"),l1=$("cxlL1"),l2=$("cxlL2"),swap=$("cxlSwap"),advBtn=$("cxlAdvBtn"),adv=$("cxlAdv"),
      doms=$("cxlDoms"),srcSel=$("cxlSrc"),cols=$("cxlCols"),moreWrap=$("cxlMoreWrap"),more=$("cxlMore"),note=$("cxlNote"),ex=$("cxEx");
  var st={key:"verzugszins",live:true,shown:0,timer:null};

  function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
  function escRe(s){return s.replace(/[.*+?^${}()|[\]\\]/g,"\\$&");}
  /* Surlignage : une seule expression combinée, insensible à la casse, pour ne jamais imbriquer deux <mark> */
  function hl(text,marks){var re=new RegExp(marks.map(escRe).join("|"),"gi");return esc(text).replace(re,function(m){return "<mark>"+m+"</mark>";});}
  function setNote(t){note.textContent=t;note.hidden=!t;}
  function empty(label,noteText){cols.innerHTML='<div class="cxl-empty">'+esc(label)+'</div>';moreWrap.hidden=true;setNote(noteText||"");}
  function setPill(key){[].forEach.call(ex.querySelectorAll("[data-ex]"),function(b){b.classList.toggle("on",b.getAttribute("data-ex")===key);});}

  /* Filtres du panneau Advanced search */
  function activeDoms(){return [].map.call(doms.querySelectorAll('[aria-pressed="true"]'),function(b){return b.getAttribute("data-dom");});}
  function resType(){var r=cx.querySelector('input[name="cxlRes"]:checked');return r?r.value:"all";}
  function filterRows(d){
    var ds=activeDoms(),sv=srcSel.value,rt=resType();
    return d.rows.filter(function(r){
      if(rt==="own") return false; /* les segments de la démo appartiennent tous aux jeux de données partagés */
      if(ds.length&&ds.indexOf(r.dom)<0) return false;
      if(sv&&sv!=="all"&&r.src.indexOf(sv)<0) return false;
      return true;
    });
  }
  function pairOk(){var a=l1.value,b=l2.value;return (a==="German"&&b==="French")||(a==="French"&&b==="German");}

  function render(){
    var d=DATA[st.key];
    if(!l1.value||!l2.value){empty("No results",t("note_langues"));return;}
    if(!pairOk()){empty("No results",t("note_paire",{langue_1:"German",langue_2:"French"}));return;}
    var rows=filterRows(d);
    if(!rows.length){empty("No results for these filters",t("note_filtres"));return;}
    var flip=(l1.value==="French");
    var h='<div class="colh"><i>'+esc(d.q)+'</i> in '+esc(l1.value)+'<small>'+d.count+' results</small></div><div class="colh r"><i>'+esc(d.q)+'</i> in '+esc(l2.value)+'</div>';
    rows.forEach(function(r,i){
      var left=flip?r.b:r.a,right=flip?r.a:r.b;
      /* résultats réels de CHnell, dans leur langue sur toutes les versions du site (allemand à gauche, sauf inversion) */
      h+='<div class="cell"'+lg(flip?"fr":"de")+'>'+hl(left,d.mark)+'</div><div class="cell r"'+lg(flip?"de":"fr")+'>'+hl(right,d.mark)+'</div>';
      h+='<div class="meta"><span><span class="dom">'+esc(r.dom)+'</span>'+esc(r.src)+'</span><button type="button" class="cxl-ctx" aria-expanded="false" aria-controls="cxlCtx'+i+'">Show in context</button></div>';
      h+='<div class="cxl-ctxline" id="cxlCtx'+i+'" hidden>'+esc(t("contexte"))+'</div>';
    });
    cols.innerHTML=h;moreWrap.hidden=false;setNote("");st.shown=rows.length;
  }

  function search(){
    var v=q.value.trim().toLowerCase(),key=DATA[v]?v:null;
    clearTimeout(st.timer);setPill(key);
    if(!key){st.live=false;empty("No results",t("note_requetes",{requete_1:DATA.verzugszins.q,requete_2:DATA.bankgeheimnis.q}));return;}
    st.key=key;st.live=true;
    if(reduce){render();return;}
    cols.innerHTML='<div class="cxl-shim"><div class="cx-shim"></div><div class="cx-shim" style="width:72%"></div><div class="cx-shim" style="width:86%"></div></div>';
    moreWrap.hidden=true;setNote("");
    st.timer=setTimeout(render,420);
  }
  function refresh(){if(st.live){clearTimeout(st.timer);render();}}

  go.addEventListener("click",search);
  q.addEventListener("keydown",function(e){if(e.key==="Enter"){e.preventDefault();search();}});
  ex.addEventListener("click",function(e){var b=e.target.closest("[data-ex]");if(!b) return;q.value=DATA[b.getAttribute("data-ex")].q;search();});
  swap.addEventListener("click",function(){var a=l1.value;l1.value=l2.value;l2.value=a;refresh();});
  l1.addEventListener("change",refresh);l2.addEventListener("change",refresh);
  $("cxlL1X").addEventListener("click",function(){l1.value="";refresh();});
  $("cxlL2X").addEventListener("click",function(){l2.value="";refresh();});
  advBtn.addEventListener("click",function(){var open=advBtn.getAttribute("aria-expanded")==="true";advBtn.setAttribute("aria-expanded",String(!open));adv.hidden=open;});
  doms.addEventListener("click",function(e){var b=e.target.closest(".cx-chip");if(!b) return;var on=b.getAttribute("aria-pressed")==="true";b.setAttribute("aria-pressed",String(!on));b.classList.toggle("on",!on);refresh();});
  srcSel.addEventListener("change",refresh);
  [].forEach.call(cx.querySelectorAll('input[name="cxlRes"]'),function(r){r.addEventListener("change",refresh);});
  cols.addEventListener("click",function(e){var b=e.target.closest(".cxl-ctx");if(!b) return;var line=$(b.getAttribute("aria-controls"));var open=b.getAttribute("aria-expanded")==="true";b.setAttribute("aria-expanded",String(!open));line.hidden=open;});
  more.addEventListener("click",function(){var d=DATA[st.key];setNote(t("note_plus",{affiches:st.shown,total:d.count}));});

  /* Démarrage : résultats de Verzugszins affichés sans attente */
  render();
})();
