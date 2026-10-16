/* Isolated design preview. Browser-local records only; no catalogue or account writes. */
const escapeHTML = s => String(s ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const key='artlines:studies-design-concept:20261011:v2';
const kindNames={artwork:'Artwork',book:'Book',event:'Event'};
const kindPlurals={artwork:'Artworks',book:'Books',event:'Events'};
const searchIcon='<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10" cy="10" r="6.5"/><path d="m15 15 5 5"/></svg>';
function kindIcon(kind){return `<svg viewBox="0 0 24 24" aria-hidden="true">${kind==='book'?'<path d="M12 5v16M3 4h5a4 4 0 0 1 4 2 4 4 0 0 1 4-2h5v15h-5a4 4 0 0 0-4 2 4 4 0 0 0-4-2H3Z"/>':kind==='event'?'<rect x="3" y="5" width="18" height="16" rx="1"/><path d="M7 3v4m10-4v4M3 10h18m-13 5h3m3 0h3"/>':'<rect x="3" y="3" width="18" height="18" rx="1"/><circle cx="8" cy="8" r="1.5"/><path d="m3 17 5-5 4 4 4-6 5 7"/>'}</svg>`;}
function parseLink(value){
  const raw=String(value??'').trim();if(!raw)return null;
  try{const url=new URL(/^[a-z][a-z0-9+.-]*:/i.test(raw)?raw:`https://${raw}`);if(!['https:','http:'].includes(url.protocol)||!url.hostname.includes('.')||url.username||url.password)return null;return url;}catch{return null;}
}
let stored=null,persistenceError=false;
try{stored=JSON.parse(localStorage.getItem(key));}catch{persistenceError=true;}
if(!stored){
  try{const previous=JSON.parse(localStorage.getItem('artlines:studies-design-concept:20261011:v1'));if(previous)stored={...previous,set:[...(previous.set??[]),50001,50002]};}catch{persistenceError=true;}
}
let personal=Array.isArray(stored?.personal)?stored.personal.filter(w=>w&&Number.isSafeInteger(w.id)&&w.id>100000&&kindNames[w.kind]&&parseLink(w.source)).map(w=>({...w,image:null,own:true,intervals:Number.isInteger(w.year)?[[w.year,w.year]]:[]})):[];
const works=[...window.ARTWORKS.map(w=>({...w,kind:'artwork',sourceName:'Art Institute of Chicago',rowLabel:w.artist_title,rowType:'Painting'})),...window.CONTEXT_RECORDS,...personal];
const byId=id=>works.find(w=>w.id===Number(id));
let set=new Set((Array.isArray(stored?.set)?stored.set:works.map(w=>w.id)).filter(id=>byId(id)));
let selected=(Array.isArray(stored?.selected)?stored.selected:[20684,16571]).filter(id=>set.has(id)&&byId(id)?.kind==='artwork').slice(0,2);
let active=set.values().next().value??20684;
let notes=stored?.notes&&typeof stored.notes==='object'?stored.notes:{};
let pairNote=typeof stored?.pairNote==='string'?stored.pairNote:'';
let role=['Research','Teaching','Exhibitions'].includes(stored?.role)?stored.role:'Research';
let view=['gallery','timeline'].includes(stored?.view)?stored.view:innerWidth<768?'gallery':'timeline';
let query='',from=1870,to=1890,tab='set',pickerQuery='',pickerTab='catalogue',editing=null;
let types=new Set(['artwork','book','event']);
const screen=new URLSearchParams(location.search).get('screen');
let compare=screen==='compare',comparePair=selected.length===2?[...selected]:[20684,16571];
let priorScroll=0,noticeTimeout,modalTrigger;
if(screen==='timeline'||screen==='own')view='timeline';
if(screen==='gallery')view='gallery';
const guidance={Research:'Keep observations and evidence together.',Teaching:'Gather works and context for a lecture.',Exhibitions:'Study a grouping and record curatorial questions.'};
const placeholders={Research:'Record an observation or a question to investigate…',Teaching:'Add a discussion prompt or teaching note…',Exhibitions:'Add a curatorial question or grouping note…'};
const main=document.getElementById('main');
function save(){
  try{localStorage.setItem(key,JSON.stringify({set:[...set],selected,notes,pairNote,role,view,personal:works.filter(w=>w.own)}));persistenceError=false;}catch{persistenceError=true;}
  document.querySelectorAll('[data-save-state]').forEach(el=>el.textContent=persistenceError?'Couldn’t save in this browser. Keep this tab open.':'Saved in this browser');
}
function notify(message){clearTimeout(noticeTimeout);document.getElementById('notice').textContent=message;noticeTimeout=setTimeout(()=>document.getElementById('notice').textContent='',4500);}
function matchesText(w,q=query){return `${w.title} ${w.artist_title} ${w.sourceName??''}`.toLocaleLowerCase().includes(q.toLocaleLowerCase());}
function matchesDate(w){return !w.intervals.length||w.intervals.some(([a,b])=>a<=to&&b>=from);}
function matched(w,q=query){return matchesText(w,q)&&matchesDate(w)&&types.has(w.kind);}
function img(w){return w.image?`<img src="${escapeHTML(w.image)}" alt="${escapeHTML(w.title)} — ${escapeHTML(w.artist_title)}">`:`<span class="record-placeholder ${w.kind}">${kindIcon(w.kind)}<span>${w.own?'Your '+kindNames[w.kind].toLowerCase()+' link':kindNames[w.kind]}</span><small>${w.own?escapeHTML(new URL(w.source).hostname):'Reference record'}</small></span>`;}
function source(w){return `<a class="source-link" href="${escapeHTML(w.source)}" target="_blank" rel="noreferrer">${escapeHTML(w.sourceName??new URL(w.source).hostname)} ↗</a>`;}
function credit(w){
  if(w.own)return 'Personal link. Title and date are your notes; no source metadata or image has been imported.';
  if(w.kind!=='artwork')return `${escapeHTML(w.credit_line)} <a class="source-link" href="${escapeHTML(w.source)}" target="_blank" rel="noreferrer">Source record</a>`;
  const label=w.catalogue.rights_status==='cc0'?'CC0':'Public domain';
  return `${escapeHTML(w.credit_line)}. Image: ${label}. <a class="source-link" href="${escapeHTML(w.details.source_page_url||w.source)}" target="_blank" rel="noreferrer">Image source</a>`;
}
function noteField(w){return `<div class="notes-field"><label for="note-${w.id}">Your note</label><textarea id="note-${w.id}" data-note="${w.id}" placeholder="${placeholders[role]}">${escapeHTML(notes[w.id]??'')}</textarea><small data-save-state>${persistenceError?'Couldn’t save in this browser.':'Saved in this browser'}</small></div>`;}
function inspector(w,mobile=false){
  const facts=w.own?`<dt>Type</dt><dd>${kindNames[w.kind]} link</dd><dt>Date</dt><dd>${escapeHTML(w.date_display)}</dd><dt>Added by</dt><dd>You</dd>`:w.kind==='artwork'?`<dt>Date</dt><dd>${escapeHTML(w.date_display)}</dd><dt>Medium</dt><dd>${escapeHTML(w.medium_display)}</dd><dt>Held at</dt><dd>Art Institute of Chicago</dd>`:`<dt>Date</dt><dd>${escapeHTML(w.date_display)}</dd><dt>Type</dt><dd>${escapeHTML(w.medium_display)}</dd><dt>Source</dt><dd>${escapeHTML(w.sourceName)}</dd>`;
  return `<section class="inspector ${mobile?'':'desktop-inspector'}" aria-label="Selected record"><div class="inspector-top"><span>Record inspection</span><span class="record-kind">${kindNames[w.kind]}</span></div><div class="inspector-body">${w.image?`<div class="art-mat">${img(w)}</div>`:img(w)}<h2>${escapeHTML(w.title)}</h2><p class="byline muted">${escapeHTML(w.artist_title||'Creator not provided')}</p>${w.own?'<span class="personal-badge">Your link</span>':''}<dl class="facts">${facts}</dl><a class="source-record" href="${escapeHTML(w.source)}" target="_blank" rel="noreferrer"><span><strong>${w.own?'Open original link':'View source record'}</strong><small>${escapeHTML(w.sourceName)}</small></span><span aria-hidden="true">↗</span></a><button class="set-button ${set.has(w.id)?'':'primary'}" data-set="${w.id}">${set.has(w.id)?'Remove from research set':'+ Add to research set'}</button>${noteField(w)}${w.own?`<div class="personal-inspector"><p class="own-inspector-note">${w.intervals.length?'Date supplied by you.':'No date yet. Add a year to place this card on the timeline.'}</p><button data-edit="${w.id}">Edit link details</button></div>`:`<details><summary>Date &amp; source notes</summary><p class="credit">${escapeHTML(w.dateNote)}</p>${w.additionalSource?`<p>${source({...w,source:w.additionalSource,sourceName:'Serial publication record'})}</p>`:''}<p class="credit">${w.kind==='artwork'?'Holding collection is not confirmation of current display.':'A shared date does not establish influence.'}</p></details>${w.kind==='artwork'?`<details><summary>Image credit &amp; dimensions</summary><p class="credit">${credit(w)}</p><p class="credit">${escapeHTML(w.dimensions)}</p><p class="credit">Accession ${escapeHTML(w.main_reference_number)}</p></details>`:''}`}</div></section>`;
}
function selectionControl(w){return w.kind==='artwork'?`<label class="select-work"><input type="checkbox" data-compare="${w.id}" ${selected.includes(w.id)?'checked':''}>${selected.includes(w.id)?'Selected to compare':'Select to compare'}</label>`:`<span class="record-kind">${kindNames[w.kind]}</span>`;}
function card(w){return `<article class="work-card ${active===w.id?'inspected':''}"><button class="work-open" data-open="${w.id}" aria-label="Inspect ${escapeHTML(w.title)}" aria-pressed="${active===w.id}">${w.image?`<span class="art-mat">${img(w)}</span>`:img(w)}<span class="card-copy"><span class="card-kind"><i class="type-dot ${w.kind}"></i>${kindNames[w.kind]}${w.own?' · Your link':''}</span><span class="card-artist">${escapeHTML(w.artist_title||'Creator not provided')}</span><span class="card-title">${escapeHTML(w.title)}</span><span class="card-date">${escapeHTML(w.date_display)}</span></span></button><div class="card-controls">${selectionControl(w)}<button class="text" data-set="${w.id}" aria-label="Remove ${escapeHTML(w.title)} from research set">Remove</button></div></article>`;}
function linkCard(w){return `<article class="link-card"><div class="link-meta"><i class="type-dot ${w.kind}"></i>${kindNames[w.kind]}<span class="personal-badge">Your link</span></div><h3>${escapeHTML(w.title)}</h3><p>${escapeHTML(w.sourceName)}</p><p style="margin-top:6px">${escapeHTML(w.date_display)}</p><div class="link-actions"><a href="${escapeHTML(w.source)}" target="_blank" rel="noreferrer">Open link ↗</a><button data-open="${w.id}">View details</button></div>${w.kind==='artwork'?selectionControl(w):''}</article>`;}
function timeline(items){
  const dated=items.filter(w=>w.intervals.length),undated=items.filter(w=>!w.intervals.length);
  const span=to-from||1,pos=y=>Math.max(0,Math.min(100,(y-from)/span*100));
  const ticks=from===to?[from]:Array.from({length:5},(_,i)=>Math.round(from+(to-from)*i/4));
  const chart=`<div class="timeline-shell" tabindex="0" aria-label="Scrollable timeline of artworks, books and events"><div class="timeline-canvas"><div class="timeline-axis"><span>People &amp; context</span><div class="timeline-scale">${ticks.map((year,i)=>`<span style="left:${ticks.length===1?0:i/(ticks.length-1)*100}%">${year}</span>`).join('')}</div></div>${dated.map(w=>{
    const intervals=w.intervals.filter(([a,b])=>a<=to&&b>=from),p=pos(intervals[0][0]);
    return `<div class="context-row ${w.kind!=='artwork'?'compact-row':''}"><div class="person-label">${escapeHTML(w.rowLabel||w.artist_title||'Your reference')}<small>${escapeHTML(w.rowType||kindNames[w.kind])}${w.own?' · Your link':''}</small></div><div class="context-track">${[0,25,50,75,100].map(n=>`<span class="axis-rule" style="left:${n}%"></span>`).join('')}<button class="context-card ${w.kind} ${w.own?'own':''}" style="left:clamp(0px, ${p}%, calc(100% - 234px))" data-open="${w.id}" aria-label="Inspect ${escapeHTML(w.title)}, ${escapeHTML(w.date_display)}" aria-pressed="${active===w.id}">${w.image?img(w):''}<span class="context-copy"><strong>${escapeHTML(w.title)}</strong><small>${escapeHTML(w.date_display)}</small></span></button>${intervals.map(([a,b])=>`<span class="context-interval ${w.kind} ${a===b?'point':''}" title="${a===b?a:`${a}–${b}`}" style="left:${pos(a)}%;width:${pos(b)-pos(a)}%"></span>`).join('')}</div></div>`;
  }).join('')}</div></div>`;
  return `${dated.length?chart:''}${undated.length?`<section class="undated-links"><h3>Undated links <span class="count">${undated.length}</span></h3><p>Kept in your study. Add a year to place a card on the timeline.</p><div class="link-grid">${undated.map(linkCard).join('')}</div></section>`:''}<p class="timeline-footnote">Dates follow the cited records. A shared period suggests a comparison; it does not establish influence.</p>`;
}
function setFooter(){return `<div class="set-foot"><div class="selected-thumbs">${selected.filter(id=>byId(id)?.image).map(id=>img(byId(id))).join('')}<p>${selected.length} of 2 artworks selected${selected.length<2?'<br><span class="muted">Choose two different artworks</span>':''}</p></div><button class="primary" data-action="compare" ${selected.length!==2?'disabled':''}>Compare artworks</button></div>`;}
function renderResults(){
  const items=works.filter(w=>set.has(w.id)&&matched(w));
  const undated=items.filter(w=>!w.intervals.length).length;
  document.getElementById('result-count').textContent=`${items.length} ${items.length===1?'record':'records'} · ${from}–${to}${undated?` · ${undated} undated`:''}`;
  document.getElementById('results').innerHTML=items.length?(view==='timeline'?timeline(items):`<div class="gallery">${items.map(card).join('')}</div>`):`<div class="empty"><h2>${set.size?'No records match':'Start your research set'}</h2><p>${set.size?'Try another search, record type or date range.':'Add an artwork, book, event or a link of your own.'}</p><button data-action="${set.size?'reset':'add'}">${set.size?'Reset filters':'Add records'}</button></div>`;
  document.getElementById('set-footer').innerHTML=setFooter();
  const top=document.querySelector('.compare-top');if(top){top.textContent=`Compare (${selected.length})`;top.disabled=selected.length!==2;}
  for(const kind of Object.keys(kindNames)){const el=document.querySelector(`[data-type-count="${kind}"]`);if(el)el.textContent=works.filter(w=>w.kind===kind&&set.has(w.id)).length;}
}
function renderWorkspace(){
  main.innerHTML=`<div class="breadcrumbs"><a href="http://127.0.0.1:3000/account">Your account</a><span>/</span><a href="?screen=workspace">Studies</a><span>/</span><b style="font-weight:400">Paris, seen differently</b></div><div class="study-heading"><div><h1>Paris, seen differently</h1><p>Artworks, writing and events in one study.</p></div><div class="heading-actions"><button class="text export-top" data-action="export" ${!set.size?'disabled':''}>Export</button><button class="olive compare-top" data-action="compare" ${selected.length!==2?'disabled':''}>Compare (${selected.length})</button><button class="primary" data-action="add">+ Add records</button></div></div><div class="study-subnav"><div class="tabs" role="group" aria-label="Study sections"><button class="tab" data-tab="set" aria-pressed="${tab==='set'}">Research set <span class="count">${set.size}</span></button><button class="tab" data-tab="notes" aria-pressed="${tab==='notes'}">Notes</button><button class="tab" data-tab="sources" aria-pressed="${tab==='sources'}">Sources</button></div><p class="save-state"><span class="status-dot"></span><span data-save-state>${persistenceError?'Couldn’t save in this browser.':'Saved in this browser'}</span></p></div>${tab==='set'?`<div class="toolbar"><div class="search-field">${searchIcon}<input id="study-search" type="search" aria-label="Search this research set" placeholder="Search artists, works, books or events" value="${escapeHTML(query)}"><kbd aria-hidden="true">/</kbd></div><button class="years" data-action="filters">${from} — ${to} <span aria-hidden="true">⌄</span></button><button class="link-shortcut" data-action="link">+ Add your link</button></div><div class="record-types"><div class="type-filters" role="group" aria-label="Record types">${Object.keys(kindNames).map(kind=>`<label class="type-filter"><input type="checkbox" data-type="${kind}" ${types.has(kind)?'checked':''}><i class="type-dot ${kind}" aria-hidden="true"></i>${kindPlurals[kind]} <span class="type-count" data-type-count="${kind}"></span></label>`).join('')}</div><div class="view-switch typebar-view" role="group" aria-label="View"><button data-view="timeline" aria-pressed="${view==='timeline'}">Timeline</button><button data-view="gallery" aria-pressed="${view==='gallery'}">Gallery</button></div></div><div class="workspace-grid"><section class="results-panel" aria-label="Research set"><div class="results-head"><p id="result-count" role="status"></p><div class="date-legend"><span><i class="legend-range"></i>Date range</span><span><i class="legend-point"></i>Single year</span></div></div><div id="results"></div><div class="study-context-foot"><label class="role-row">For <select id="role" aria-label="Professional workflow">${Object.keys(guidance).map(r=>`<option ${r===role?'selected':''}>${r}</option>`).join('')}</select></label><p class="role-guidance">${guidance[role]}</p></div></section><div id="source-inspector">${inspector(byId(active))}</div></div><div id="set-footer"></div>`:`<div class="notes-page">${works.filter(w=>set.has(w.id)).map(w=>`<article><h2>${escapeHTML(w.title)}</h2><p class="muted">${escapeHTML(w.artist_title)} · ${escapeHTML(w.date_display)}${w.own?' · Your link':''}</p>${tab==='notes'?noteField(w):`<p>${source(w)}</p><p class="credit">${credit(w)}</p><p class="date-note">${escapeHTML(w.dateNote)}</p>`}</article>`).join('')}</div>`}<div class="study-footer"><p>References and notes export together. No image files included.</p><p>Personal study · saved in this browser</p></div>`;
  if(tab==='set')renderResults();
}
function comparisonColumn(id,index) {
  const w=byId(id),other=comparePair[1-index];
  return `<section class="compare-column" aria-label="Artwork ${index+1}"><label class="compare-select"><span class="number">0${index+1}</span><select data-pair="${index}" aria-label="Choose artwork ${index+1}">${works.filter(w=>w.kind==='artwork'&&(set.has(w.id)||comparePair.includes(w.id))).map(w=>`<option value="${w.id}" ${w.id===id?'selected':''} ${w.id===other?'disabled':''}>${escapeHTML(w.artist_title)} — ${escapeHTML(w.title)}</option>`).join('')}</select></label><div class="art-mat">${img(w)}</div><div class="compare-caption"><p>${escapeHTML(w.artist_title)}</p><h2>${escapeHTML(w.title)}</h2></div><dl class="facts compare-facts"><dt>Date</dt><dd>${escapeHTML(w.date_display)}</dd><dt>Medium</dt><dd>${escapeHTML(w.medium_display || 'Not provided')}</dd><dt>Dimensions</dt><dd>${escapeHTML((w.dimensions || 'Not provided').split(';')[0])}</dd><dt>Collection</dt><dd>${w.own?'Not provided':source(w)}</dd><dt>Accession</dt><dd>${escapeHTML(w.main_reference_number || 'Not provided')}</dd></dl><p class="credit">${credit(w)}</p>${w.id===11723||w.id===27992?`<p class="date-note">${escapeHTML(w.dateNote)}</p>`:''}</section>`;
}
function renderCompare() {
  main.innerHTML=`<div class="breadcrumbs"><button class="text" data-action="back">← Back to research set</button><span>/</span><span>Paris, seen differently</span></div><div class="study-heading compare-heading"><div><h1>Look closely, side by side.</h1><p>Compare two works from your research set.</p></div><button data-action="export">Export references</button></div><div class="compare-options"><p>Full compositions · Images fitted to each panel, not relative physical scale.</p><button class="text" data-action="swap">Swap artworks ⇄</button></div><div class="comparison">${comparePair.map(comparisonColumn).join('')}</div><div class="compare-note"><div><h3>Comparison notes</h3><p data-save-state>${persistenceError?'Couldn’t save in this browser.':'Saved in this browser'}</p></div><label><span class="muted" style="display:block;font-size:12px;margin-bottom:6px">Your observations</span><textarea id="pair-note" placeholder="What changes between these two works? Consider space, light, brushwork and viewpoint.">${escapeHTML(pairNote)}</textarea></label></div><div class="study-footer"><p>Holding collections are shown. Current display is not confirmed.</p><p>${comparePair.some(id=>byId(id).own)?'Personal link details supplied by you':'Sources checked 11 October 2026'}</p></div>`;
}
function render(){compare?renderCompare():renderWorkspace();}
function openDialog(id){modalTrigger=document.activeElement;document.getElementById(id).showModal();document.body.style.overflow='hidden';}
function closeDialog(id){document.getElementById(id).close();}
for(const id of ['picker','detail','filters'])document.getElementById(id).addEventListener('close',()=>{document.body.style.overflow='';if(modalTrigger?.isConnected)modalTrigger.focus();else document.querySelector('[data-action=add]')?.focus();});
function pickerCards(){
  const items=works.filter(w=>!w.own&&(pickerTab==='catalogue'||[20684,16571].includes(w.id))&&matchesText(w,pickerQuery));
  document.getElementById('picker-count').textContent=`${items.length} sample records`;
  document.getElementById('picker-cards').innerHTML=items.length?items.map(w=>`<article class="picker-card">${w.image?`<div class="art-mat">${img(w)}</div>`:img(w)}<span class="record-kind">${kindNames[w.kind]}</span><p style="margin-top:9px">${escapeHTML(w.artist_title)} · ${escapeHTML(w.date_display)}</p><h3>${escapeHTML(w.title)}</h3><p>${escapeHTML(w.sourceName)}</p><button class="${set.has(w.id)?'added':'primary'}" data-set="${w.id}" aria-pressed="${set.has(w.id)}">${set.has(w.id)?'✓ Added to research set':'+ Add to research set'}</button></article>`).join(''):'<div class="empty"><h2>No matching records</h2><button data-action="reset-picker">Clear search</button></div>';
  document.getElementById('picker-set-count').textContent=`${set.size} records in your research set`;
}
function personalPreview(){
  const form=document.getElementById('link-form');if(!form)return;
  const url=parseLink(form.elements.url.value),kind=form.elements.kind.value;
  const title=form.elements.title.value.trim()||(url?url.hostname.replace(/^www\./,''):'Your reference');
  document.getElementById('live-link-preview').innerHTML=`<div class="link-card"><div class="link-meta"><i class="type-dot ${kind}"></i>${kindNames[kind]}<span class="personal-badge">Your link</span></div><div class="link-symbol">${kindIcon(kind)}</div><h3>${escapeHTML(title)}</h3><p>${url?escapeHTML(url.hostname):'Paste a link to get started'}</p><p style="margin-top:13px">${escapeHTML(form.elements.year.value||'No date added')}</p><p class="link-info">${form.elements.year.value?'Appears at this year on your timeline.':'Saved as a card under Undated links.'}</p></div>`;
}
function renderPickerTab(){
  const container=document.getElementById('picker-body');
  if(pickerTab==='link'){
    const w=editing?byId(editing):null;
    container.innerHTML=`<div class="link-entry"><form id="link-form" class="link-form" novalidate><div class="field"><label for="link-kind">What are you adding?</label><select id="link-kind" name="kind">${Object.keys(kindNames).map(kind=>`<option value="${kind}" ${w?.kind===kind?'selected':''}>${kindNames[kind]}</option>`).join('')}</select></div><div class="field"><label for="link-url">Link <span class="muted">(required)</span></label><input id="link-url" name="url" type="url" value="${escapeHTML(w?.source||'')}" placeholder="https://…" aria-describedby="link-hint link-error" autocomplete="off" autofocus><p class="hint" id="link-hint">A museum page, book, article or another reference. A link is all you need.</p></div><details ${w?'open':''}><summary>Add a title, creator or year <span class="muted">(optional)</span></summary><div class="optional-fields"><div class="field"><label for="link-title">Title</label><input id="link-title" name="title" value="${escapeHTML(w?.title||'')}" maxlength="300" placeholder="A name you’ll recognise"></div><div class="field-grid"><div class="field"><label for="link-creator">Artist, author or context</label><input id="link-creator" name="creator" maxlength="200" value="${escapeHTML(w?.artist_title||'')}" placeholder="Optional"></div><div class="field"><label for="link-year">Year</label><input id="link-year" name="year" inputmode="numeric" value="${w?.year??''}" placeholder="Optional" aria-describedby="link-error"></div></div></div></details><p class="link-error" id="link-error" role="alert"></p><div class="link-dialog-action"><p>Added only to this study. Saved in this browser.</p><button class="primary" type="submit">${w?'Save details':'Add link to study'}</button></div></form><aside class="link-preview" aria-label="Your link card preview"><p>Card preview</p><div id="live-link-preview"></div><p class="link-info">You can edit the details later. The linked page opens in a new tab.</p></aside></div>`;
    document.getElementById('picker-bottom').hidden=true;personalPreview();
  }else{
    container.innerHTML=`<div class="search-field">${searchIcon}<input type="search" id="picker-search" aria-label="Find a record to add" placeholder="Search by title, artist or author" value="${escapeHTML(pickerQuery)}"></div><p id="picker-count" class="muted" style="font-size:12px;margin:16px 0"></p><div class="picker-grid" id="picker-cards"></div>`;
    document.getElementById('picker-bottom').hidden=false;pickerCards();
  }
  document.querySelectorAll('[data-picker-tab]').forEach(el=>el.setAttribute('aria-pressed',el.dataset.pickerTab===pickerTab));
}
function showPicker(target='catalogue',editId=null){
  pickerQuery='';pickerTab=target;editing=editId;
  document.getElementById('picker').innerHTML=`<header class="dialog-header"><div><h2 id="picker-title">${editing?'Edit your link':'Add to your study'}</h2><p>Artworks, books, events — and references of your own.</p></div><button class="icon" data-close="picker" aria-label="Close add records">×</button></header><div class="dialog-body"><div class="picker-tabs"><button class="tab" data-picker-tab="catalogue">Catalogue sample</button><button class="tab" data-picker-tab="bookmarks">Sample bookmarks</button><button class="tab" data-picker-tab="link">+ Your link</button></div><div id="picker-body"></div></div><div class="dialog-bottom" id="picker-bottom"><span id="picker-set-count"></span><button class="primary" data-close="picker">Done</button></div>`;
  renderPickerTab();openDialog('picker');
}
function showDetail(id){active=Number(id);document.getElementById('detail').innerHTML=`<header class="dialog-header"><button class="text" data-close="detail">← Back to research set</button><button class="icon" data-close="detail" aria-label="Close record details">×</button></header>${inspector(byId(id),true)}`;openDialog('detail');}
function exportCSV(){
  if(!set.size)return;
  const field=v=>`"${String(v??'').replace(/^[\s\uFEFF]*[=+@-]/,"'$&").replace(/"/g,'""')}"`;
  const rows=[['Type','Title','Creator or context','Date label','Origin','Source','Date note','Your notes','Comparison notes'],...works.filter(w=>set.has(w.id)).map(w=>[kindNames[w.kind],w.title,w.artist_title,w.date_display,w.own?'Your link':'Source-backed sample',w.source,w.dateNote,notes[w.id]??'',pairNote])];
  const url=URL.createObjectURL(new Blob(['\uFEFF'+rows.map(r=>r.map(field).join(',')).join('\r\n')],{type:'text/csv;charset=utf-8'}));
  const a=document.createElement('a');a.href=url;a.download='paris-seen-differently-references.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);notify('References, your links and notes exported. No image files included.');
}
function inspect(id){active=Number(id);if(innerWidth<1280)showDetail(active);else{const scroll=document.querySelector('.timeline-shell')?.scrollLeft??0;renderWorkspace();if(document.querySelector('.timeline-shell'))document.querySelector('.timeline-shell').scrollLeft=scroll;document.querySelector(`[data-open="${active}"]`)?.focus({preventScroll:true});}}
function showFilters(){
  document.getElementById('filters').innerHTML=`<header class="dialog-header"><h2 id="filter-title">Record dates</h2><button class="icon" data-close="filters" aria-label="Close date filters">×</button></header><form id="year-form"><div class="dialog-body"><p class="muted" style="margin-bottom:18px">Show records whose dates overlap this range. Undated personal links stay in a separate section.</p><div class="filter-fields"><label>From<input name="from" inputmode="numeric" value="${from}" aria-describedby="year-error"></label><label>To<input name="to" inputmode="numeric" value="${to}" aria-describedby="year-error"></label></div><p id="year-error" role="alert"></p></div><div class="dialog-bottom"><button type="button" data-close="filters">Cancel</button><button class="primary" type="submit">Apply dates</button></div></form>`;openDialog('filters');
}
document.addEventListener('click',event=>{
  const el=event.target.closest('button');if(!el)return;
  if(el.dataset.close){closeDialog(el.dataset.close);return;}
  if(el.dataset.edit){if(document.getElementById('detail').open)closeDialog('detail');showPicker('link',Number(el.dataset.edit));return;}
  if(el.dataset.set){
    const id=Number(el.dataset.set),adding=!set.has(id);adding?set.add(id):set.delete(id);selected=selected.filter(x=>set.has(x));save();render();
    if(document.getElementById('picker').open&&pickerTab!=='link')pickerCards();
    if(document.getElementById('detail').open)document.getElementById('detail').querySelector('.set-button').textContent=adding?'Remove from research set':'+ Add to research set';
    notify(adding?'Added to your research set.':'Removed from your research set.');return;
  }
  if(el.dataset.open){inspect(el.dataset.open);return;}
  if(el.dataset.tab){tab=el.dataset.tab;renderWorkspace();document.querySelector(`[data-tab="${tab}"]`).focus();return;}
  if(el.dataset.view){view=el.dataset.view;save();renderWorkspace();document.querySelector(`[data-view="${view}"]`).focus();return;}
  if(el.dataset.pickerTab){pickerTab=el.dataset.pickerTab;renderPickerTab();return;}
  switch(el.dataset.action){
    case 'add':showPicker();break;
    case 'link':showPicker('link');break;
    case 'export':exportCSV();break;
    case 'reset':query='';from=1870;to=1890;types=new Set(Object.keys(kindNames));renderWorkspace();break;
    case 'reset-picker':pickerQuery='';document.getElementById('picker-search').value='';pickerCards();break;
    case 'compare':if(selected.length===2){priorScroll=scrollY;comparePair=[...selected];compare=true;render();scrollTo(0,0);main.focus({preventScroll:true});}break;
    case 'back':compare=false;render();scrollTo(0,priorScroll);document.querySelector('[data-action=compare]')?.focus({preventScroll:true});break;
    case 'swap':comparePair.reverse();renderCompare();document.querySelector('[data-action=swap]').focus();break;
    case 'filters':showFilters();break;
  }
});
document.addEventListener('change',event=>{
  const el=event.target;
  if(el.dataset.type){el.checked?types.add(el.dataset.type):types.delete(el.dataset.type);renderResults();}
  if(el.dataset.compare){const id=Number(el.dataset.compare);if(byId(id)?.kind!=='artwork')return;if(el.checked&&selected.length===2){el.checked=false;notify('Two artworks are selected. Deselect one to choose another.');return;}selected=el.checked?[...selected,id]:selected.filter(x=>x!==id);save();renderResults();document.querySelector(`[data-compare="${id}"]`)?.focus({preventScroll:true});}
  if(el.id==='role'){role=el.value;save();renderWorkspace();document.getElementById('role').focus();}
  if(el.dataset.pair!==undefined){if(byId(el.value)?.kind!=='artwork'||comparePair[1-Number(el.dataset.pair)]===Number(el.value))return;comparePair[Number(el.dataset.pair)]=Number(el.value);renderCompare();document.querySelector(`[data-pair="${el.dataset.pair}"]`).focus();}
  if(el.closest('#link-form'))personalPreview();
});
document.addEventListener('input',event=>{
  const el=event.target;
  if(el.id==='study-search'){query=el.value;renderResults();}
  if(el.id==='picker-search'){pickerQuery=el.value;pickerCards();}
  if(el.dataset.note){notes[el.dataset.note]=el.value;save();}
  if(el.id==='pair-note'){pairNote=el.value;save();}
  if(el.closest('#link-form'))personalPreview();
});
document.addEventListener('submit',event=>{
  if(event.target.id==='link-form'){
    event.preventDefault();const form=event.target,fields=new FormData(form),url=parseLink(fields.get('url')),rawYear=String(fields.get('year')).trim(),kind=String(fields.get('kind'));
    const error=!url?'Enter a valid http or https link.':rawYear&&(!/^-?\d{1,4}$/.test(rawYear)||Number(rawYear)<-5000||Number(rawYear)>2100)?'Enter a year from −5000 to 2100, or leave it empty.':!kindNames[kind]?'Choose a record type.':'';
    document.getElementById('link-error').textContent=error;form.elements.url.setAttribute('aria-invalid',!url);if(error)return;
    const existing=editing?byId(editing):works.find(w=>w.own&&w.kind===kind&&w.source===url.href);
    if(existing&&!editing){set.add(existing.id);active=existing.id;save();closeDialog('picker');renderWorkspace();notify('This link is already in your study.');return;}
    const id=editing??Date.now(),year=rawYear?Number(rawYear):null;
    const record={id,kind,own:true,source:url.href,sourceName:url.hostname.replace(/^www\./,''),title:String(fields.get('title')).trim()||url.hostname.replace(/^www\./,''),artist_title:String(fields.get('creator')).trim(),date_display:year===null?'Date not added':String(year),year,intervals:year===null?[]:[[year,year]],image:null,dateNote:year===null?'Personal reference. No date supplied.':'Personal reference. Date supplied by the user.',rowLabel:String(fields.get('creator')).trim()||'Your reference',rowType:kindNames[kind]};
    if(editing)works.splice(works.findIndex(w=>w.id===id),1,record);else works.push(record);
    set.add(id);active=id;types.add(kind);query='';if(year!==null){from=Math.min(from,year);to=Math.max(to,year);}selected=selected.filter(x=>byId(x)?.kind==='artwork');save();closeDialog('picker');renderWorkspace();notify(editing?'Link details saved.':year===null?'Link added. Find it under Undated links.':'Link added to your timeline.');
    if(innerWidth>=1280&&year===null)document.querySelector('.undated-links')?.scrollIntoView({block:'nearest'});return;
  }
  if(event.target.id!=='year-form')return;event.preventDefault();
  const fields=new FormData(event.target),a=String(fields.get('from')).trim(),b=String(fields.get('to')).trim();
  const error=!/^-?\d{1,4}$/.test(a)||!/^-?\d{1,4}$/.test(b)?'Enter a numeric year in both fields.':Number(a)>Number(b)?'From must be earlier than or equal to To.':Number(a)<-5000||Number(b)>2100?'Use years from −5000 to 2100 in this preview.':'';
  document.getElementById('year-error').textContent=error;event.target.querySelectorAll('input').forEach(el=>el.setAttribute('aria-invalid',Boolean(error)));
  if(error)return;from=Number(a);to=Number(b);closeDialog('filters');renderWorkspace();document.querySelector('[data-action=filters]').focus();
});
document.addEventListener('keydown',event=>{if(event.key==='/'&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)&&!document.querySelector('dialog[open]')){const input=document.getElementById('study-search');if(input){event.preventDefault();input.focus();}}});
document.addEventListener('error',event=>{if(event.target instanceof HTMLImageElement){event.target.alt='Image unavailable';event.target.style.opacity='.5';}},true);
save();render();
if(screen==='add')showPicker();
if(screen==='link')showPicker('link');
if(screen==='record')showDetail(20684);
