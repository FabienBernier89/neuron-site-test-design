/* Démo Corrext · Traduction texte et document : données réelles récoltées dans l'application le 14 septembre 2026 (moteurs nommables uniquement).
   Partagé par la page d'accueil et la page Traduction texte et document. Une seule instance de cadre #cx par page. */
(function(){
  var EX={
    co:{label:"Contrat · art. 104 CO",
      src:"Le débiteur en demeure doit des intérêts moratoires au taux de 5% l'an, conformément à l'art. 104 al. 1 CO, sans qu'une mise en demeure formelle soit nécessaire lorsqu'un terme a été convenu.",
      def:"en",
      out:{
        en:{main:"The debtor in default shall owe default interest at the rate of 5% per annum in accordance with CO Art. 104 para. 1, without the need for formal notice when a term has been agreed.",
            alt:[{e:"DeepL Pro",t:"A debtor who is in default shall be liable to pay default interest at the rate of 5 per cent per annum, in accordance with Article 104(1) of the Swiss Code of Obligations, without the need for a formal notice of default where a payment deadline has been agreed."},
                 {e:"Azure OpenAI - GPT",t:"The debtor in default owes default interest at the rate of 5% per annum, in accordance with Art. 104 para. 1 CO, without a formal notice of default being necessary when a due date has been agreed."}]},
        it:{main:"Il debitore in mora deve interessi di mora al tasso annuo del 5 per cento conformemente all'art. 104 cpv. 1 CO, senza che sia necessaria una messa in mora formale se è stato pattuito un termine.",
            alt:[{e:"DeepL Pro",t:"Il debitore inadempiente è tenuto a corrispondere interessi di mora al tasso del 5% annuo, ai sensi dell'art. 104, comma 1, CO, senza che sia necessaria una formale messa in mora qualora sia stato concordato un termine."},
                 {e:"Azure OpenAI - GPT",t:"Il debitore in mora deve interessi moratori al tasso del 5% annuo, conformemente all'art. 104 cpv. 1 CO, senza che sia necessaria una costituzione in mora formale quando è stato convenuto un termine."}]}
      },
      lookup:{q:"Verzugszins",l1:"German",l2:"French",count:"324 results",rows:[
        {a:"Kann die Zahlstelle den fehlenden Betrag zuzüglich Verzugszins nicht mehr der betroffenen Person nachbelasten, zum Beispiel weil diese nicht mehr ihre Kundin ist, so ist die Zahlstelle zur Leistung des fehlenden Betrages zuzüglich Verzugszins verpflichtet.",b:"Si l'agent payeur ne peut plus prélever ultérieurement le montant manquant avec l'intérêt moratoire, notamment parce que la personne concernée n'est plus cliente de son établissement, il reste tenu de verser le montant correspondant.",dom:"OTHER",src:"Feuille Fédérale/Bundesblatt - Source: Feuille Fédérale/Bundesblatt - Data Set: Neur.on"},
        {a:"Art. 24 Verzugszins Auf Einmalzahlungen, abgeltenden Steuern und Abgeltungszahlungen, die der ESTV verspätet überwiesen werden, ist ohne Mahnung ein Verzugszins nach Ablauf der in diesem Gesetz festgelegten Fristen bis zum Datum des Eingangs geschuldet.",b:"5373 Art. 24 Intérêt moratoire Un intérêt moratoire est dû sans sommation dès l'échéance des délais fixés dans la présente loi sur les paiements uniques, les impôts libératoires et les paiements libératoires virés en retard à l'AFC et jusqu'à réception des sommes dues.",dom:"TAX LAW & CUSTOMS",src:"SIF FF20125365 Bundesgesetz-über-die-internationale-Quellenbesteuerung-IQG - Source: fedlex.admin.ch - Data Set: Neur.on"}],
        mark:["Verzugszins","intérêt moratoire","Intérêt moratoire"]},
      reph:{def:"Le débiteur en <u>retard</u> doit <u>verser</u> des intérêts moratoires au taux de 5 % <u>par</u> an, conformément à l’art. 104 al. 1 CO, sans qu’une mise en demeure formelle soit nécessaire <u>dès lors qu’</u>un terme a été <u>fixé</u>.",
            simp:"<u>Celui qui ne paie pas à temps</u> doit <u>verser</u> des intérêts <u>de retard de</u> 5% <u>par</u> an, <u>d'après</u> l'art. 104 al. 1 CO. <u>Une demande de paiement officielle n'est pas obligatoire si</u> une <u>date limite</u> a été <u>fixée</u>."}
    },
    lb:{label:"Banque · art. 47 LB",
      src:"L'établissement assujetti veille au respect du secret bancaire au sens de l'art. 47 LB et met en œuvre les exigences de la FINMA en matière de lutte contre le blanchiment d'argent.",
      def:"de",
      out:{
        de:{main:"Das beaufsichtigte Institut sorgt für die Einhaltung des Bankgeheimnisses nach Artikel 47 BankG und setzt die Anforderungen der FINMA zur Bekämpfung der Geldwäscherei um.",
            alt:[{e:"DeepL Pro",t:"Das unterstellte Institut sorgt für die Einhaltung des Bankgeheimnisses im Sinne von Art. 47 BankG und setzt die Anforderungen der FINMA zur Bekämpfung der Geldwäscherei um."},
                 {e:"Azure OpenAI - GPT",t:"Das unterstellte Institut achtet auf die Einhaltung des Bankgeheimnisses im Sinne von Art. 47 BankG und setzt die Anforderungen der FINMA zur Bekämpfung der Geldwäscherei um."}]},
        en:{main:"The supervised institution shall ensure compliance with banking secrecy in accordance with Article 47 BankA and implement FINMA's anti-money laundering requirements.",
            alt:[{e:"DeepL Pro",t:"The regulated institution ensures compliance with banking secrecy as defined in Article 47 of the Banking Act and implements FINMA's anti-money laundering requirements."},
                 {e:"Azure OpenAI - GPT",t:"The supervised institution ensures compliance with banking secrecy as defined in Art. 47 of the Banking Act and implements FINMA's requirements regarding anti-money laundering."}]},
        it:{main:"L'istituto assoggettato vigila sul rispetto del segreto bancario ai sensi dell'art. 47 LBCR e rispetta i requisiti della FINMA in materia di lotta contro il riciclaggio di denaro.",
            alt:[{e:"DeepL Pro",t:"L'istituto soggetto a vigilanza garantisce il rispetto del segreto bancario ai sensi dell'art. 47 LB e attua i requisiti della FINMA in materia di lotta contro il riciclaggio di denaro."},
                 {e:"Azure OpenAI - GPT",t:"L'ente soggetto garantisce il rispetto del segreto bancario ai sensi dell'art. 47 LB e attua i requisiti della FINMA in materia di lotta contro il riciclaggio di denaro."}]}
      },
      lookup:{q:"Bankgeheimnis",l1:"German",l2:"French",count:"425 results",rows:[
        {a:"Anlässlich dieses Treffens wurde der Kundenberater misstrauisch, da die Kundin auffällige Fragen über das Schweizer Bankgeheimnis und das Geldwäschereigesetz stellte.",b:"Lors de l'entretien, le conseiller à la clientèle est devenu méfiant parce que la cliente posait des questions suspectes sur le secret bancaire suisse et sur la loi sur le blanchiment d'argent.",dom:"BANKING & FINANCE",src:"MROS - Source: fedpol.admin.ch - Data Set: Neur.on"},
        {a:"Obwohl der Begriff Bankgeheimnis im Initiativtext nicht und im Argumentarium nur sparsam verwendet wird, beabsichtigt die Initiative insbesondere die Verankerung des steuerlichen Bankgeheimnisses im Inland auf Verfassungsstufe.",b:"Bien que le terme ne figure pas dans le texte de l'initiative et que l'argumentaire du comité d'initiative n'en fasse qu'un usage parcimonieux, un des buts principaux de l'initiative est d'inscrire la notion de secret bancaire dans la Constitution.",dom:"TAX LAW & CUSTOMS",src:"ESTV FF20156429 Botschaft-zur-Volksinitiative-Ja-zum-Schutz-der-Privatsphäre- - Source: fedlex.admin.ch - Data Set: Neur.on"}],
        mark:["Bankgeheimnis","secret bancaire"]}
    },
    ldip:{label:"Arbitrage · art. 186 LDIP",
      src:"Le tribunal arbitral statue sur sa propre compétence conformément à l'art. 186 LDIP, et la sentence peut faire l'objet d'un recours au Tribunal fédéral.",
      def:"en",
      out:{
        en:{main:"The arbitral tribunal shall decide on its own jurisdiction in accordance with art. 186 PILA, and the award may be appealed to the Federal Tribunal.",
            alt:[{e:"DeepL Pro",t:"The arbitral tribunal shall rule on its own jurisdiction in accordance with Article 186 of the LDIP, and the award may be appealed to the Federal Supreme Court."},
                 {e:"Azure OpenAI - GPT",t:"The arbitral tribunal rules on its own jurisdiction in accordance with Art. 186 PILA, and the award may be subject to an appeal before the Federal Supreme Court."}]},
        it:{main:"Il tribunale arbitrale decide in merito alla propria competenza conformemente all'articolo 186 LDIP e il lodo può essere impugnato dinanzi al Tribunale federale.",
            alt:[{e:"DeepL Pro",t:"Il tribunale arbitrale si pronuncia sulla propria competenza ai sensi dell'art. 186 LDIP e il lodo può essere impugnato dinanzi al Tribunale federale."},
                 {e:"Azure OpenAI - GPT",t:"Il tribunale arbitrale decide sulla propria competenza conformemente all'art. 186 LDIP, e il lodo può essere impugnato dinanzi al Tribunale federale."}]}
      }
    }
  };
  var LANGS={de:"German",en:"English",it:"Italian"};
  // notes de la démo dans la langue de la page (les libellés de l'interface Corrext restent en anglais)
  var TX={
    fr:{bientot:" (démo : bientôt)",lookup:"Démo : Fast Lookup est disponible sur les extraits « Contrat » et « Banque ».",
        reph:"Démo : choisissez l'extrait « Contrat · art. 104 CO » pour la réécriture.",
        style:"Démo : le style « {0} » n'est pas disponible sur cet extrait ; réglage par défaut appliqué. Styles réels de Corrext : Formal legal, Financial, Simplified, Formal, Informal, Shorten.",
        rnote:"Démo : réécriture disponible sur l'extrait « Contrat · art. 104 CO », avec le réglage par défaut et le style Simplified."},
    de:{bientot:" (Demo: bald verfügbar)",lookup:"Demo: Fast Lookup ist bei den Auszügen «Vertrag» und «Bank» verfügbar.",
        reph:"Demo: Wählen Sie für die Umformulierung den Auszug «Vertrag · Art. 104 OR».",
        style:"Demo: Der Stil «{0}» ist bei diesem Auszug nicht verfügbar, es gilt die Standardeinstellung. Stile in Corrext: Formal legal, Financial, Simplified, Formal, Informal, Shorten.",
        rnote:"Demo: Umformulierung beim Auszug «Vertrag · Art. 104 OR» verfügbar, mit der Standardeinstellung und dem Stil Simplified."},
    it:{bientot:" (demo: presto disponibile)",lookup:"Demo: Fast Lookup è disponibile per gli estratti «Contratto» e «Banca».",
        reph:"Demo: per la riformulazione scegliete l'estratto «Contratto · art. 104 CO».",
        style:"Demo: lo stile «{0}» non è disponibile per questo estratto; si applica l'impostazione predefinita. Stili reali di Corrext: Formal legal, Financial, Simplified, Formal, Informal, Shorten.",
        rnote:"Demo: riformulazione disponibile per l'estratto «Contratto · art. 104 CO», con l'impostazione predefinita e lo stile Simplified."},
    en:{bientot:" (demo: coming soon)",lookup:"Demo: Fast Lookup is available on the ‘Contract’ and ‘Banking’ excerpts.",
        reph:"Demo: choose the ‘Contract · Art. 104 CO’ excerpt for rephrasing.",
        style:"Demo: the ‘{0}’ style is not available on this excerpt, so the default setting applies. Actual Corrext styles: Formal legal, Financial, Simplified, Formal, Informal, Shorten.",
        rnote:"Demo: rephrasing is available on the ‘Contract · Art. 104 CO’ excerpt, with the default setting and the Simplified style."}
  };
  var tx=TX[(document.documentElement.lang||"fr").slice(0,2)]||TX.fr;
  var $=function(id){return document.getElementById(id);};
  var cx=$("cx"); if(!cx) return;
  var reduce=window.matchMedia&&window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var st={ex:"co",tgt:"en",eng:"LexMachina",alts:[],ai:0,timer:null};
  var src=$("cxSrc"),out=$("cxOut"),cnt=$("cxCnt"),tgt=$("cxTgt"),eng=$("cxEng"),srcLang=$("cxSrcLang"),
      alts=$("cxAlts"),altT=$("cxAltT"),pg=$("cxPg"),notice=$("cxNotice"),lookupBtn=$("cxLookupBtn"),modal=$("cxModal");

  function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
  function setTargets(ex){
    var d=EX[ex]; [].forEach.call(tgt.options,function(o){var ok=!!d.out[o.value]; o.disabled=!ok; o.textContent=LANGS[o.value]+(ok?"":tx.bientot);});
    if(!d.out[st.tgt]) st.tgt=d.def; tgt.value=st.tgt;
  }
  function loadExample(ex){
    st.ex=ex; var d=EX[ex];
    [].forEach.call(document.querySelectorAll("#cxEx button"),function(b){b.classList.toggle("on",b.getAttribute("data-ex")===ex);});
    src.value=d.src; cnt.textContent=d.src.length+" / 10000"; srcLang.selectedIndex=1;
    setTargets(ex); closeAlts(); translate(); loadReph();
  }
  function currentText(){
    var d=EX[st.ex].out[st.tgt]; if(!d) return null;
    if(st.eng==="LexMachina") return d.main;
    for(var i=0;i<d.alt.length;i++) if(d.alt[i].e===st.eng) return d.alt[i].t;
    return null;
  }
  function translate(){
    if(st.timer){clearTimeout(st.timer);st.timer=null;}
    closeAlts();
    if(!src.value){out.innerHTML='';return;}
    out.innerHTML='<div class="cx-shim" style="width:92%"></div><div class="cx-shim" style="width:78%"></div><div class="cx-shim" style="width:86%"></div>';
    st.timer=setTimeout(function(){var t=currentText(); out.textContent=t||""; st.timer=null;},reduce?0:900);
  }
  function buildAlts(){
    var d=EX[st.ex].out[st.tgt]; if(!d) return [];
    var list=[{e:"LexMachina",t:d.main}].concat(d.alt);
    return list.filter(function(a){return a.e!==st.eng;});
  }
  function showAlt(){
    if(!st.alts.length) return;
    var a=st.alts[st.ai];
    altT.innerHTML=esc(a.t)+' <em>- '+esc(a.e)+'</em>';
    pg.textContent=(st.ai+1)+" / "+st.alts.length;
  }
  function openAlts(){
    if(!src.value||st.timer) return;
    st.alts=buildAlts(); st.ai=0; if(!st.alts.length) return;
    alts.classList.add("on");
    altT.innerHTML='<span class="ph">Generating alternatives…</span>'; pg.textContent="";
    setTimeout(showAlt,reduce?0:700);
  }
  function closeAlts(){alts.classList.remove("on");}

  /* Extraits */
  [].forEach.call(document.querySelectorAll("#cxEx button"),function(b){b.addEventListener("click",function(){loadExample(b.getAttribute("data-ex"));});});
  tgt.addEventListener("change",function(){st.tgt=tgt.value; translate();});
  eng.addEventListener("change",function(){st.eng=eng.value; notice.classList.toggle("show",st.eng!=="LexMachina"); $("cxFEng").value=st.eng; translate();});
  $("cxFEng").addEventListener("change",function(){eng.value=$("cxFEng").value; st.eng=eng.value; notice.classList.toggle("show",st.eng!=="LexMachina"); translate();});
  $("cxClear").addEventListener("click",function(){src.value=""; cnt.textContent="0 / 10000"; srcLang.selectedIndex=0; out.innerHTML=""; closeAlts(); lookupBtn.classList.remove("show"); [].forEach.call(document.querySelectorAll("#cxEx button"),function(b){b.classList.remove("on");});});
  $("cxSpark").addEventListener("click",openAlts);
  $("cxAltX").addEventListener("click",closeAlts);
  $("cxUp").addEventListener("click",function(){if(!st.alts.length)return; st.ai=(st.ai-1+st.alts.length)%st.alts.length; showAlt();});
  $("cxDn").addEventListener("click",function(){if(!st.alts.length)return; st.ai=(st.ai+1)%st.alts.length; showAlt();});
  $("cxCopy").addEventListener("click",function(){var t=out.textContent; if(!t) return; try{navigator.clipboard&&navigator.clipboard.writeText(t);}catch(e){}});

  /* Interrupteur Highly sensitive content */
  var sw=$("cxSwitch");
  sw.addEventListener("click",function(){var on=sw.classList.toggle("off"); sw.setAttribute("aria-pressed",on?"false":"true");});

  /* Onglets */
  var tabs=[].slice.call(document.querySelectorAll(".cx-tab"));
  tabs.forEach(function(t){t.addEventListener("click",function(){
    tabs.forEach(function(x){var on=x===t; x.classList.toggle("on",on); x.setAttribute("aria-selected",on?"true":"false");});
    ["text","file","pdf","reph"].forEach(function(k){$("cxp-"+k).classList.toggle("on",k===t.getAttribute("data-tab"));});
    sw.classList.toggle("dis",t.getAttribute("data-tab")==="pdf");
    lookupBtn.classList.remove("show");
    syncH();
  });});

  /* Hauteur constante : chaque onglet garde la hauteur de Text translation, le plus haut */
  var pText=$("cxp-text"),pOthers=["file","pdf","reph"].map(function(k){return $("cxp-"+k);});
  function textH(){
    if(pText.classList.contains("on")) return pText.offsetHeight;
    var s=pText.style; s.display="block"; s.visibility="hidden"; s.position="absolute"; s.width=cx.clientWidth+"px";
    var h=pText.offsetHeight; s.display=s.visibility=s.position=s.width=""; return h;
  }
  function syncH(){var h=textH(); if(h) pOthers.forEach(function(p){p.style.minHeight=h+"px";});}
  var rz; window.addEventListener("resize",function(){clearTimeout(rz); rz=setTimeout(syncH,150);});
  if(document.fonts&&document.fonts.ready) document.fonts.ready.then(syncH);
  syncH();

  /* Fast Lookup : surligner un mot dans la source ouvre CHnell */
  function selectionInSrc(){var s=window.getSelection?String(window.getSelection()):""; return s&&s.trim().length>1;}
  src.addEventListener("mouseup",function(){setTimeout(function(){lookupBtn.classList.toggle("show",selectionInSrc());},10);});
  src.addEventListener("keyup",function(){lookupBtn.classList.toggle("show",selectionInSrc());});
  document.addEventListener("mousedown",function(e){if(!lookupBtn.contains(e.target)&&e.target!==src) lookupBtn.classList.remove("show");});
  function mark(text,terms){var h=esc(text); terms.forEach(function(t){h=h.split(esc(t)).join('<mark>'+esc(t)+'</mark>');}); return h;}
  function openLookup(){
    var d=EX[st.ex]; var cols=$("cxLkCols");
    if(!d.lookup){cols.innerHTML='<div class="cell" style="grid-column:1 / -1">'+esc(tx.lookup)+'</div>'; modal.classList.add("on"); return;}
    $("cxLkQ").textContent=d.lookup.q; $("cxLkL1").textContent=d.lookup.l1; $("cxLkL2").textContent=d.lookup.l2;
    var h='<div class="colh"><i>'+esc(d.lookup.q)+'</i> in <b>'+esc(d.lookup.l1)+'</b><small>'+esc(d.lookup.count)+'</small></div><div class="colh r"><i>'+esc(d.lookup.q)+'</i> in <b>'+esc(d.lookup.l2)+'</b></div>';
    d.lookup.rows.forEach(function(r){h+='<div class="cell">'+mark(r.a,d.lookup.mark)+'</div><div class="cell r">'+mark(r.b,d.lookup.mark)+'</div><div class="meta"><span><span class="dom">'+esc(r.dom)+'</span>'+esc(r.src)+'</span><a>Show in context</a></div>';});
    cols.innerHTML=h; modal.classList.add("on"); lookupBtn.classList.remove("show");
  }
  lookupBtn.addEventListener("click",openLookup);
  $("cxLkClose").addEventListener("click",function(){modal.classList.remove("on");});
  modal.addEventListener("click",function(e){if(e.target===modal) modal.classList.remove("on");});

  /* File translation et PDF to Word : dépôt simulé */
  function simulate(drop,row,bar,stEl,done){
    drop.addEventListener("click",function(){
      row.classList.add("show"); bar.style.transform="scaleX(0)"; stEl.textContent=stEl.getAttribute("data-run")||stEl.textContent;
      setTimeout(function(){bar.style.transform="scaleX(1)";},60);
      setTimeout(function(){stEl.textContent=done;},reduce?50:2600);
    });
  }
  $("cxFileSt").setAttribute("data-run","Translating…"); $("cxPdfSt").setAttribute("data-run","Converting…");
  simulate($("cxFileDrop"),$("cxFileRow"),$("cxFileBar"),$("cxFileSt"),"Download");
  simulate($("cxPdfDrop"),$("cxPdfRow"),$("cxPdfBar"),$("cxPdfSt"),"Download .docx");
  $("cxFTgt").addEventListener("change",function(){$("cxFileSub").textContent="248 KB · 14 pages · German → "+$("cxFTgt").value;});

  /* Rephrasing */
  var rsrc=$("cxRSrc"),rout=$("cxROut"),rcnt=$("cxRCnt"),pop=$("cxSetPop"),dot=$("cxSetDot"),rstyle=null,rTimer=null;
  function loadReph(){
    var d=EX[st.ex];
    if(!d.reph){rsrc.value=""; rcnt.textContent="0 / 5000"; rout.innerHTML='<span class="ph">'+esc(tx.reph)+'</span>'; return;}
    rsrc.value=d.src; rcnt.textContent=d.src.length+" / 5000"; rephrase();
  }
  function rephrase(){
    var d=EX[st.ex]; if(!d.reph) return;
    if(rTimer){clearTimeout(rTimer);}
    rout.innerHTML='<div class="cx-shim" style="width:90%"></div><div class="cx-shim" style="width:82%"></div><div class="cx-shim" style="width:70%"></div>';
    rTimer=setTimeout(function(){rout.innerHTML=(rstyle==="Simplified")?d.reph.simp:d.reph.def; rTimer=null;},reduce?0:900);
  }
  $("cxSetBtn").addEventListener("mousedown",function(e){e.preventDefault(); pop.classList.toggle("on");});
  $("cxSetBtn").addEventListener("keydown",function(e){if(e.key==="Enter"||e.key===" "){e.preventDefault(); pop.classList.toggle("on");}});
  [].forEach.call(document.querySelectorAll("#cxSetPop .cx-chip"),function(c){c.addEventListener("click",function(){
    var was=c.classList.contains("on"); [].forEach.call(document.querySelectorAll("#cxSetPop .cx-chip"),function(x){x.classList.remove("on");}); if(!was) c.classList.add("on");
  });});
  $("cxSetApply").addEventListener("click",function(){
    var on=document.querySelector("#cxSetPop .cx-chip.on"); rstyle=on?on.getAttribute("data-style"):null;
    dot.classList.toggle("on",!!rstyle); pop.classList.remove("on");
    if(rstyle&&rstyle!=="Simplified"){$("cxRNote").textContent=tx.style.replace("{0}",rstyle); rstyle=null; dot.classList.remove("on");}
    else{$("cxRNote").textContent=tx.rnote;}
    rephrase();
  });
  $("cxSetReset").addEventListener("click",function(){[].forEach.call(document.querySelectorAll("#cxSetPop .cx-chip"),function(x){x.classList.remove("on");}); rstyle=null; dot.classList.remove("on"); pop.classList.remove("on"); rephrase();});
  document.addEventListener("mousedown",function(e){if(pop.classList.contains("on")&&!pop.contains(e.target)&&e.target!==$("cxSetBtn")) pop.classList.remove("on");});

  /* Démarrage : premier extrait, dès que le cadre approche du viewport (240px avant) */
  var started=false;
  function start(){if(started)return; started=true; loadExample("co"); syncH(); setTimeout(syncH,1000);}
  if("IntersectionObserver" in window){
    var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){start(); io.disconnect();}});},{threshold:0,rootMargin:"0px 0px 240px 0px"});
    io.observe(cx);
  } else start();
})();
