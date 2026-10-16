const escapeHTML = value => String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const data = window.MAP_EXPERIMENTS;
const query = new URLSearchParams(location.search);
let datasetKey = ['fragonard','delacroix','cezanne','boundary'].includes(query.get('artist')) ? query.get('artist') : 'delacroix';
let mode = ['step','all','panel'].includes(query.get('mode')) ? query.get('mode') : 'step';
let artist;
let shown = {incoming:5,outgoing:5};
const titles = {incoming:'Teachers & influences',outgoing:'Influence & legacy'};
const relationLabels = {teacher_of:'Teacher',influenced:'Influence',documented_admiration:'Admiration'};
const levelLabels = {documented:'Documented',scholarly_consensus:'Scholarly consensus',scholarly_interpretation:'Scholarly interpretation',editorial_inference:'Editorial inference'};
const descriptions = {step:'Five visible per side. Show more adds up to five people to that side; Show less returns it to five.',all:'Five visible per side. Show more reveals every remaining person on that side; Show less returns it to five.',panel:'Five visible per side. Show more opens a searchable side panel while keeping the map compact.'};
const e=escapeHTML;
const supported=c=>['documented','scholarly_consensus','scholarly_interpretation'].includes(c.evidence_level);
const level=c=>`<span class="evidence-level ${supported(c)?'supported':''}">${e(levelLabels[c.evidence_level]||c.evidence_level.replaceAll('_',' '))}</span>`;
const relation=(c,direction)=>c.relationship_type==='teacher_of'?(direction==='outgoing'?'Student':'Teacher'):(relationLabels[c.relationship_type]||c.relationship_type.replaceAll('_',' '));
const node=(row,index,direction,panel=false)=>`<button class="node" data-row="${index}" data-direction="${direction}" ${panel?'data-panel-row':''} aria-label="Read evidence for ${e(row.name)}"><span><span class="name">${e(row.name)}</span>${row.claims.map(c=>`<span class="claim-label"><span>${e(relation(c,direction))}</span><span aria-hidden="true">·</span>${level(c)}</span>`).join('')}</span><span class="chevron" aria-hidden="true">›</span></button>`;
const directionCount=direction=>Math.min(shown[direction],artist[direction].length);
function updateURL(){history.replaceState(null,'',`?mode=${mode}&artist=${datasetKey}`);}
function load(){
 const base=data[datasetKey==='boundary'?'delacroix':datasetKey];
 artist=datasetKey==='boundary'?{...base,incoming:base.incoming.slice(0,5),outgoing:base.outgoing.slice(0,6)}:base;
 shown={incoming:5,outgoing:5};
 document.querySelector('#dataset').value=datasetKey;
 document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===mode)));
 document.querySelector('#experiment-note').textContent=descriptions[mode];
 document.querySelector('#boundary-note').textContent=datasetKey==='boundary'?'Boundary test: a 5 / 6 subset of Delacroix’s saved connections, not his complete counts.':'';
 document.querySelector('#artist-name').textContent=artist.name;
 document.querySelector('#artist-dates').textContent=artist.dates;
 document.querySelector('#artist-link').href=`https://artlines.org/artists/${artist.slug}`;
 document.querySelector('#map-center h3').textContent=artist.name;
 document.querySelector('#map-center>span').textContent=artist.dates;
 renderSide('incoming');renderSide('outgoing');updateURL();scheduleDraw();
}
function renderSide(direction){
 const total=artist[direction].length,n=directionCount(direction),remaining=total-n;
 document.querySelector(`#${direction}`).innerHTML=`<header class="side-heading"><h3 id="${direction}-heading">${titles[direction]}</h3><span class="side-count">${n===total?`${total} ${total===1?'person':'people'}`:`${n} of ${total}`}</span></header><div class="nodes" id="${direction}-nodes">${artist[direction].slice(0,n).map((r,i)=>node(r,i,direction)).join('')||'<p class="side-empty">No connections recorded in this sample.</p>'}</div>${total>5?`<div class="side-actions">${remaining>0?`<button class="more-button" data-more="${direction}" aria-controls="${mode==='panel'?'detail-dialog':direction+'-nodes'}" ${mode==='panel'?'aria-haspopup="dialog"':`aria-expanded="${n>5}"`}><span>Show more</span><span class="remaining">${remaining} remaining <span aria-hidden="true">+</span></span></button>`:''}${n>5?`<button class="less-button" data-less="${direction}" aria-controls="${direction}-nodes">Show less</button>`:''}</div>`:''}`;
}
let frame;
function scheduleDraw(){cancelAnimationFrame(frame);frame=requestAnimationFrame(draw);}
function draw(){
 const grid=document.querySelector('#map-grid'),svg=document.querySelector('#connectors');
 if(innerWidth<=760){svg.innerHTML='';document.querySelector('#map-center').style.marginTop='';return;}
 const rect=grid.getBoundingClientRect();
 const firstFive=[...document.querySelectorAll('#incoming-nodes .node')].slice(0,5).concat([...document.querySelectorAll('#outgoing-nodes .node')].slice(0,5));
 if(!firstFive.length){svg.innerHTML='';return;}
 const top=Math.min(...firstFive.map(n=>n.getBoundingClientRect().top)),bottom=Math.max(...firstFive.map(n=>n.getBoundingClientRect().bottom));
 const center=document.querySelector('#map-center');
 const y=(top+bottom)/2-rect.top;
 grid.style.setProperty('--center-y',`${y}px`);
 center.style.marginTop=`${Math.max(40,y-center.offsetHeight/2)}px`;
 const c=center.getBoundingClientRect(),cx1=c.left-rect.left,cx2=c.right-rect.left,cy=c.top-rect.top+c.height/2;
 const path=(x1,y1,x2,y2,isSupported)=>`<path d="M${x1},${y1} C${(x1+x2)/2},${y1} ${(x1+x2)/2},${y2} ${x2},${y2}" fill="none" stroke="${isSupported?'#345c46':'#a09789'}" stroke-width="1.2" ${isSupported?'':'stroke-dasharray="4 4"'} marker-end="url(#arrow-${isSupported?'solid':'dashed'})"/>`;
 let paths='<defs><marker id="arrow-solid" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0 0L7 3.5L0 7" fill="none" stroke="#345c46"/></marker><marker id="arrow-dashed" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0 0L7 3.5L0 7" fill="none" stroke="#a09789"/></marker></defs>';
 for(const direction of ['incoming','outgoing']){
  document.querySelectorAll(`#${direction}-nodes .node`).forEach((n,index)=>{
   const r=n.getBoundingClientRect(),row=artist[direction][index];
   const kinds=[...new Set(row.claims.map(supported))];
   kinds.forEach((kind,i)=>{const offset=(i-(kinds.length-1)/2)*8;const ey=r.top-rect.top+r.height/2+offset;paths+=direction==='incoming'?path(r.right-rect.left,ey,cx1,cy+offset,kind):path(cx2,cy+offset,r.left-rect.left,ey,kind);});
  });
 }
 svg.innerHTML=paths;svg.setAttribute('viewBox',`0 0 ${rect.width} ${rect.height}`);
}
const dialog=document.querySelector('#detail-dialog');
let panelState=null,lastTrigger=null;
function claimDetail(c,direction){return `<section class="claim-detail"><h3>${e(relation(c,direction))}</h3>${level(c)}<p>${e(c.evidence_note)}</p><div class="sources">${c.sources.map(s=>`<a href="${e(s.url)}" target="_blank" rel="noopener">${e(s.label)} ↗</a>`).join('')}</div></section>`;}
function showEvidence(direction,index,fromPanel=false){
 const row=artist[direction][index];
 if(!fromPanel){panelState=null;lastTrigger=document.activeElement;dialog.className='';}
 else{panelState.lastIndex=index;panelState.scroll=dialog.scrollTop;}
 document.querySelector('#back-to-list').hidden=!fromPanel;
 document.querySelector('#dialog-label').hidden=fromPanel;
 document.querySelector('#dialog-body').innerHTML=`<h2 id="dialog-title">${e(row.name)}</h2><p class="dialog-subtitle">${direction==='incoming'?`${e(row.name)} → ${e(artist.name)}`:`${e(artist.name)} → ${e(row.name)}`}<br>${row.claims.length} ${row.claims.length===1?'claim':'separate claims'}</p>${row.claims.map(c=>claimDetail(c,direction)).join('')}${row.slug?`<a class="profile-link" href="https://artlines.org/artists/${e(row.slug)}" target="_blank" rel="noopener">Explore ${e(row.name)} ↗</a>`:''}`;
 if(!dialog.open)dialog.showModal();
 dialog.scrollTop=0;
 document.querySelector(fromPanel?'#back-to-list':'#close-dialog').focus({preventScroll:true});
}
function openPanel(direction){
 panelState={direction,search:'',limit:20,lastIndex:null,scroll:0};lastTrigger=document.activeElement;dialog.className='panel';
 showPanel();dialog.showModal();document.querySelector('#panel-search').focus({preventScroll:true});
}
function showPanel(){
 document.querySelector('#back-to-list').hidden=true;document.querySelector('#dialog-label').hidden=false;
 document.querySelector('#dialog-body').innerHTML=`<h2 id="dialog-title">${titles[panelState.direction]}</h2><p class="dialog-subtitle">${e(artist.name)} · ${artist[panelState.direction].length} people</p><label class="search-label">Find a person<input type="search" id="panel-search" placeholder="Search names" value="${e(panelState.search)}"></label><p class="panel-count" id="panel-count" role="status"></p><div class="panel-list" id="panel-list"></div><div id="panel-actions"></div>`;
 renderPanelList();
 document.querySelector('#panel-search').addEventListener('input',event=>{panelState.search=event.target.value;panelState.limit=20;renderPanelList();});
}
function renderPanelList(){
 const matches=artist[panelState.direction].map((row,index)=>({row,index})).filter(({row})=>row.name.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().includes(panelState.search.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase()));
 const n=Math.min(panelState.limit,matches.length);
 document.querySelector('#panel-count').textContent=`${n} of ${matches.length} ${matches.length===1?'person':'people'}`;
 document.querySelector('#panel-list').innerHTML=matches.slice(0,n).map(({row,index})=>node(row,index,panelState.direction,true)).join('')||'<p class="panel-empty">No names match. Try another spelling or clear the search.</p>';
 document.querySelector('#panel-actions').innerHTML=n<matches.length?`<button class="more-button panel-more" data-panel-more aria-controls="panel-list"><span>Show more</span><span class="remaining">${matches.length-n} remaining +</span></button>`:'';
}
document.addEventListener('click',event=>{
 const modeButton=event.target.closest('[data-mode]');if(modeButton){mode=modeButton.dataset.mode;load();return;}
 const more=event.target.closest('[data-more]');if(more){const direction=more.dataset.more;if(mode==='panel'){openPanel(direction);return;}const previous=directionCount(direction);shown[direction]=mode==='all'?artist[direction].length:Math.min(previous+5,artist[direction].length);renderSide(direction);scheduleDraw();document.querySelector(`#${direction}-nodes .node[data-row="${previous}"]`)?.focus({preventScroll:true});document.querySelector('#announcement').textContent=`${directionCount(direction)} of ${artist[direction].length} people shown in ${titles[direction]}.`;return;}
 const less=event.target.closest('[data-less]');if(less){const direction=less.dataset.less;shown[direction]=5;renderSide(direction);scheduleDraw();document.querySelector(`[data-more="${direction}"]`)?.focus({preventScroll:true});document.querySelector(`#${direction}-heading`).scrollIntoView({block:'nearest',behavior:'instant'});document.querySelector('#announcement').textContent=`${titles[direction]} returned to five people.`;return;}
 const person=event.target.closest('[data-row]');if(person){showEvidence(person.dataset.direction,Number(person.dataset.row),person.hasAttribute('data-panel-row'));return;}
 const panelMore=event.target.closest('[data-panel-more]');if(panelMore){const previous=panelState.limit;panelState.limit+=20;renderPanelList();document.querySelectorAll('#panel-list .node')[previous]?.focus({preventScroll:true});}
});
document.querySelector('#dataset').addEventListener('change',event=>{datasetKey=event.target.value;load();});
document.querySelector('#close-dialog').addEventListener('click',()=>dialog.close());
dialog.addEventListener('close',()=>{lastTrigger?.focus({preventScroll:true});panelState=null;});
dialog.addEventListener('click',event=>{if(event.target===dialog){const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close();}});
document.querySelector('#back-to-list').addEventListener('click',()=>{const index=panelState.lastIndex,scroll=panelState.scroll;showPanel();dialog.scrollTop=scroll;document.querySelector(`#panel-list [data-row="${index}"]`)?.focus({preventScroll:true});});
new ResizeObserver(scheduleDraw).observe(document.querySelector('#map-grid'));
window.addEventListener('resize',scheduleDraw);
load();

dialog.addEventListener('keydown',event=>{if(event.key==='Escape'){event.preventDefault();event.stopPropagation();dialog.close();}},true);
