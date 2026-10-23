/* Osteo-Fit CMF catalog — view toggle, theme toggle, zoom modal, search.
   Product image URLs come from window.CAT (built from the image manifest). */
(function(){
  var body=document.body, root=document.documentElement;
  var P=(window.CAT&&window.CAT.p)||{};
  /* single-file export: product <img> carry only data-img; fill src from the map */
  document.querySelectorAll('img[data-img]:not([src])').forEach(function(im){var e=P[im.dataset.img]; if(e){im.src=e.m}});

  /* ---- view: shape / sku ------------------------------------------------- */
  var VK='osteofit.view';
  function setView(v){
    body.classList.toggle('shape',v==='shape');
    document.getElementById('v-shape').setAttribute('aria-pressed',v==='shape');
    document.getElementById('v-sku').setAttribute('aria-pressed',v!=='shape');
    try{localStorage.setItem(VK,v)}catch(e){}
  }
  var v='shape';
  try{v=localStorage.getItem(VK)||localStorage.getItem('view_bw')||localStorage.getItem('view_w')||'shape'}catch(e){}
  setView(v);
  document.getElementById('v-shape').onclick=function(){setView('shape')};
  document.getElementById('v-sku').onclick=function(){setView('sku')};

  /* ---- theme: dark / light ----------------------------------------------- */
  var TK='osteofit.theme', tb=document.getElementById('t-dark'),
      mq=window.matchMedia?matchMedia('(prefers-color-scheme:light)'):null;
  function stored(){try{return localStorage.getItem(TK)}catch(e){return null}}
  function applyTheme(t,save,animate){
    if(animate){root.classList.add('theming');setTimeout(function(){root.classList.remove('theming')},300)}
    root.dataset.theme=t;
    if(tb){tb.setAttribute('aria-pressed',t==='dark');tb.setAttribute('aria-label',t==='dark'?'다크 모드 (켜짐)':'다크 모드 (꺼짐)')}
    if(save){try{localStorage.setItem(TK,t)}catch(e){}}
  }
  applyTheme(root.dataset.theme==='light'?'light':'dark',false,false);
  if(tb)tb.onclick=function(){applyTheme(root.dataset.theme==='dark'?'light':'dark',true,true)};
  if(mq&&mq.addEventListener)mq.addEventListener('change',function(){if(!stored())applyTheme(mq.matches?'light':'dark',false,true)});

  /* ---- zoom modal ---------------------------------------------------------- */
  var modal=document.getElementById('modal'),mi=document.getElementById('mi'),
      mx=document.getElementById('mx'),main=document.querySelector('main'),last=null;
  function openM(el){
    var k=el.dataset.img,e=P[k]; if(!e)return;
    mi.removeAttribute('srcset'); mi.removeAttribute('sizes');
    mi.width=e.w; mi.height=e.h; mi.src=e.m;
    if(e.f&&e.f!==e.m){mi.srcset=e.m+' '+e.mw+'w, '+e.f+' '+e.fw+'w'; mi.sizes='min(1000px, 100vw)';}
    var t=el.dataset.title||'', s=el.dataset.sub||'';
    mi.alt=(t+' '+s).trim();
    document.getElementById('mt').textContent=t; document.getElementById('ms').textContent=s;
    last=document.activeElement; modal.classList.add('open'); if(main)main.inert=true; mx.focus();
  }
  function closeM(){
    if(!modal.classList.contains('open'))return;
    modal.classList.remove('open'); if(main)main.inert=false;
    if(last&&last.focus){if(main)main.getBoundingClientRect();last.focus()} last=null;
  }
  document.addEventListener('click',function(e){
    if(modal.classList.contains('open')){ if(e.target===modal||e.target.id==='mx') closeM(); return; }
    var z=e.target.closest('.card[data-img], .zoom[data-img]'); if(z&&!e.target.closest('.var')) openM(z);
  });
  document.addEventListener('keydown',function(e){if(e.key==='Escape')closeM()});
})();

(function(){
  var q=document.getElementById('q'),hits=document.getElementById('hits'),items=[].slice.call(document.querySelectorAll('.item'));
  function esc(s){return s.replace(/[&<>]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c]})}
  function hl(el,text,term){
    if(!el)return; if(!term){el.textContent=text;return}
    var i=text.toLowerCase().indexOf(term);
    el.innerHTML= i<0?esc(text):esc(text.slice(0,i))+'<mark>'+esc(text.slice(i,i+term.length))+'</mark>'+esc(text.slice(i+term.length));
  }
  items.forEach(function(it){
    it._dEl=it.querySelector('.desc')||it.querySelector('.vd')||(it.cells&&it.cells[0]); it._pEl=it.querySelector('.card>.pn')||it.querySelector('.vp')||(it.cells&&it.cells[1]);
    it._d=it.dataset.d; it._p=it.dataset.p; it._dText=it._dEl?it._dEl.textContent:'';
    it._pText=it.tagName==='TR'?it.cells[1].firstChild.textContent:(it._pEl?it._pEl.textContent:'');
  });
  function run(){
    var term=q.value.trim().toLowerCase().replace(/\s+/g,' ');
    document.body.classList.toggle('q',!!term);
    var n=0;
    items.forEach(function(it){
      var ok=!term||it._d.indexOf(term)>=0||it._p.indexOf(term)>=0;
      it.classList.toggle('hit',ok); if(ok&&!it.classList.contains('var'))n++;
      hl(it._dEl,it._dText,ok&&term?term:'');
      if(it.tagName==='TR'){var tn=it.cells[1].firstChild; if(tn&&tn.nodeType===3){var s=document.createElement('span');it.cells[1].replaceChild(s,tn);} hl(it.cells[1].firstChild,it._pText,ok&&term?term:'');}
      else if(it._pEl) hl(it._pEl,it._pText,ok&&term?term:'');
    });
    document.querySelectorAll('.card.shape').forEach(function(c){c.classList.toggle('has',c.querySelectorAll('.item.hit').length>0)});
    document.querySelectorAll('.group').forEach(function(g){
      var c=g.querySelectorAll('.v-sku .item.hit, tr.item.hit').length; g.classList.toggle('has',c>0);
      var b=g.querySelector('.count'); if(b)b.textContent=term?c+' / '+b.dataset.n:b.dataset.n;
    });
    document.querySelectorAll('.family').forEach(function(f){f.classList.toggle('has',f.querySelectorAll('.group.has').length>0)});
    document.body.classList.toggle('none',!!term&&n===0);
    hits.textContent=term?n+'건':'';
  }
  q.addEventListener('input',run);
  var h=location.hash.replace('#','');
  if(h&&/^[a-z]+$/.test(h)&&document.getElementById(h)){setTimeout(function(){document.getElementById(h).scrollIntoView()},0)}
  run();
})();
