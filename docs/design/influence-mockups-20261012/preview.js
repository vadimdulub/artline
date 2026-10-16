const params = new URLSearchParams(location.search);
const view = ['a','b','c','d'].includes(params.get('view')) ? params.get('view') : 'a';
const rows = window.CONNECTIONS;
const incoming = rows.filter(x => x.direction === 'incoming');
const outgoing = rows.filter(x => x.direction === 'outgoing');
const e = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const labels = {teacher_of:'Teacher', influenced:'Influence', documented_admiration:'Admiration'};
const info = {
 a:['Paired lists','Both directions visible. Compact rows open to reveal the evidence.'],
 b:['Relationship map','Fragonard at the centre. Follow each connection to its evidence.'],
 c:['Tabbed sidebar','A quieter companion to the biography, with one direction at a time.'],
 d:['Evidence explorer','Choose an artist on the left. Read their claims and sources on the right.']
};
document.body.className = `view-${view}`;
document.querySelector('#concept-letter').textContent = view.toUpperCase();
document.querySelector('#concept-name').textContent = info[view][0];
document.querySelector('#concept-description').textContent = info[view][1];
document.querySelector('#recommended').hidden = view !== 'a';
document.title = `${info[view][0]} · Artline influence mockups`;
const status = claim => `<span class="status ${claim.evidence_level === 'documented' ? 'documented' : ''}">${claim.evidence_level === 'documented' ? 'Documented' : 'Editorial inference'}</span>`;
const claimLines = row => row.claims.map(claim => `<span class="claim-line"><span>${labels[claim.relationship_type]}</span><span class="status-separator" aria-hidden="true">·</span>${status(claim)}</span>`).join('');
const nameAndClaims = row => `<span><span class="artist-name">${e(row.name)}</span>${claimLines(row)}</span>`;
const claimDetail = claim => `<section class="evidence-claim"><div class="claim-top"><h4>${labels[claim.relationship_type]}</h4>${status(claim)}</div><p>${e(claim.evidence_note)}</p><div class="source-links">${claim.sources.map(s => `<a href="${e(s.url)}" target="_blank" rel="noopener">${e(s.name)} ↗</a>`).join('')}</div></section>`;
const artistLink = row => `<a class="artist-link" href="https://artlines.org/artists/${e(row.slug)}" target="_blank" rel="noopener">Explore ${e(row.name)} ↗</a>`;
const evidence = (row, dialog=false) => `<span class="detail-count">${row.claims.length} ${row.claims.length===1?'claim':'separate claims'}</span><h3 class="evidence-heading" ${dialog?'id="dialog-title"':''}>${e(row.name)}</h3><p class="evidence-context">${row.direction==='incoming'?'Teacher of Jean-Honoré Fragonard':'Connection to Jean-Honoré Fragonard'}</p>${row.claims.map(claimDetail).join('')}${artistLink(row)}`;
const disclosure = row => `<details class="connection-row"><summary aria-label="${e(row.name)}: show connection evidence">${nameAndClaims(row)}<span class="chevron" aria-hidden="true">›</span></summary><div class="inline-evidence">${row.claims.map(claimDetail).join('')}${artistLink(row)}</div></details>`;
const biography = () => `<section class="biography" id="biography"><h2>Biography</h2><p>Jean-Honoré Fragonard (5 April 1732 – 22 August 1806) was a French painter and printmaker whose late Rococo manner was distinguished by remarkable facility, exuberance, and hedonism. One of the most prolific artists active in the last decades of the Ancien Régime, Fragonard produced more than 550 paintings (not counting drawings and etchings), of which only five are dated. Among his most popular works are genre paintings conveying an atmosphere of intimacy and veiled eroticism.</p><p class="credit"><a href="https://en.wikipedia.org/wiki/Jean-Honor%C3%A9_Fragonard" target="_blank" rel="noopener">Wikipedia contributors</a>. Opening excerpt, shortened for this preview. <a href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank" rel="noopener">CC BY-SA 4.0</a>.</p></section>`;
const sectionHeading = (desc='') => `<header class="section-heading"><h2>Artistic connections</h2>${desc?`<p>${desc}</p>`:'<span class="count">7 artists · 8 claims</span>'}</header>`;
const groupHeading = (title,n) => `<header class="column-heading"><h3>${title}</h3><span class="count">${n} artists</span></header>`;
const mapNode = row => `<button class="map-node" data-evidence="${row.key}" aria-label="${e(row.name)}: read connection evidence">${nameAndClaims(row)}</button>`;
const map = () => `<section class="connections">${sectionHeading('Lines show the recorded relationship.<br>Select an artist to read its evidence.')}<div class="map-headings"><span>Teachers & influences</span><span>Influence & legacy</span></div><div class="map" id="relationship-map"><svg class="map-svg" aria-hidden="true"></svg><div class="map-col map-in"><span class="map-mobile-note">Teachers & influences · 2 artists</span>${incoming.map(mapNode).join('')}</div><div class="map-center"><p class="focus-label">You are exploring</p><h3>Jean-Honoré<br>Fragonard</h3><p>1732–1806</p></div><div class="map-col map-out"><span class="map-mobile-note">Influence & legacy · 5 artists</span>${outgoing.map(mapNode).join('')}</div></div><div class="legend"><span><i></i>Editorial inference</span><span><i class="solid"></i>Documented admiration</span></div></section>`;
const listSelector = row => `<button class="select-artist" aria-pressed="${row.key==='morisot'}" data-select="${row.key}"><span><span class="artist-name">${e(row.name)}</span>${row.key==='morisot'?'<span class="claim-line">Admiration & influence · 2 claims</span>':''}</span><span class="mini-dot ${row.claims.some(c=>c.evidence_level==='documented')?'documented':''}" aria-hidden="true"></span></button>`;
const compositions = {
 a:() => `${biography()}<section class="connections">${sectionHeading()}<div class="paired"><section>${groupHeading('Teachers & influences',2)}${incoming.map(disclosure).join('')}<p class="group-hint">Teaching relationships and artistic influence retain their own evidence.</p></section><section>${groupHeading('Influence & legacy',5)}${outgoing.map(disclosure).join('')}</section></div></section>`,
 b:() => biography()+map(),
 c:() => `<div class="sidebar-layout">${biography()}<section class="sidebar-panel"><header class="section-heading"><div><h2>Artistic connections</h2><p>Explore the people around Fragonard.</p></div></header><div class="tabs" role="tablist" aria-label="Connection direction"><button id="incoming-tab" role="tab" aria-selected="false" aria-controls="sidebar-list" tabindex="-1" data-direction="incoming">Teachers <span class="tab-count">2</span></button><button id="outgoing-tab" role="tab" aria-selected="true" aria-controls="sidebar-list" tabindex="0" data-direction="outgoing">Influence & legacy <span class="tab-count">5</span></button></div><div id="sidebar-list" role="tabpanel" aria-labelledby="outgoing-tab">${outgoing.map(disclosure).join('')}</div><p class="panel-footnote">Open a connection for its claims and sources.</p></section></div>`,
 d:() => `${biography()}<section class="connections">${sectionHeading('Every relationship keeps its own claim type, evidence level and sources.')}<div class="explorer"><label class="mobile-select">Choose a connection<select id="connection-choice"><optgroup label="Teachers & influences">${incoming.map(r=>`<option value="${r.key}">${e(r.name)}</option>`).join('')}</optgroup><optgroup label="Influence & legacy">${outgoing.map(r=>`<option value="${r.key}" ${r.key==='morisot'?'selected':''}>${e(r.name)}</option>`).join('')}</optgroup></select></label><div class="explorer-list" aria-label="Choose an artist"><h3>Teachers & influences <span>2 artists</span></h3>${incoming.map(listSelector).join('')}<h3>Influence & legacy <span>5 artists</span></h3>${outgoing.map(listSelector).join('')}</div><div class="explorer-detail" id="explorer-detail" role="region" aria-label="Selected connection evidence" aria-live="polite">${evidence(rows.find(r=>r.key==='morisot'))}</div></div></section>`
};
document.querySelector('#composition').innerHTML = compositions[view]();
const dialog = document.querySelector('#evidence-dialog');
document.querySelector('#close-dialog').addEventListener('click',()=>dialog.close());
dialog.addEventListener('click',event=>{if(event.target===dialog){const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close();}});
document.addEventListener('click',event=>{
 const node=event.target.closest('[data-evidence]');
 if(node){document.querySelector('#dialog-content').innerHTML=evidence(rows.find(r=>r.key===node.dataset.evidence),true);dialog.showModal();}
 const selector=event.target.closest('[data-select]');
 if(selector){document.querySelector('#connection-choice').value=selector.dataset.select;document.querySelectorAll('[data-select]').forEach(b=>b.setAttribute('aria-pressed',String(b===selector)));document.querySelector('#explorer-detail').innerHTML=evidence(rows.find(r=>r.key===selector.dataset.select));}
 const tab=event.target.closest('[data-direction]');
 if(tab){document.querySelectorAll('[data-direction]').forEach(b=>{b.setAttribute('aria-selected',String(b===tab));b.tabIndex=b===tab?0:-1;});document.querySelector('#sidebar-list').innerHTML=(tab.dataset.direction==='incoming'?incoming:outgoing).map(disclosure).join('');document.querySelector('#sidebar-list').setAttribute('aria-labelledby',tab.id);}
});
document.querySelector('.tabs')?.addEventListener('keydown',event=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(event.key)){event.preventDefault();const tabs=[...document.querySelectorAll('[data-direction]')];const current=tabs.indexOf(document.activeElement);const index=event.key==='Home'?0:event.key==='End'?tabs.length-1:(current+1)%tabs.length;tabs[index].click();tabs[index].focus();}});
function drawMap(){
 const box=document.querySelector('#relationship-map');if(!box||innerWidth<=720)return;
 const svg=box.querySelector('svg');const base=box.getBoundingClientRect();const center=box.querySelector('.map-center').getBoundingClientRect();
 const cx1=center.left-base.left, cx2=center.right-base.left, cy=center.top-base.top+center.height/2;
 const curve=(x1,y1,x2,y2,solid=false)=>`<path d="M${x1},${y1} C${(x1+x2)/2},${y1} ${(x1+x2)/2},${y2} ${x2},${y2}" fill="none" stroke="${solid?'#345c46':'#a09789'}" stroke-width="1.25" ${solid?'':'stroke-dasharray="4 4"'} marker-end="url(#${solid?'arrow-solid':'arrow'})"/>`;
 let paths='<defs><marker id="arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0 0L7 3.5L0 7" fill="none" stroke="#a09789"/></marker><marker id="arrow-solid" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0 0L7 3.5L0 7" fill="none" stroke="#345c46"/></marker></defs>';
 box.querySelectorAll('.map-in .map-node').forEach(n=>{const r=n.getBoundingClientRect();paths+=curve(r.right-base.left,r.top-base.top+r.height/2,cx1,cy);});
 box.querySelectorAll('.map-out .map-node').forEach(n=>{const r=n.getBoundingClientRect(),y=r.top-base.top+r.height/2;paths+=curve(cx2,cy,r.left-base.left,y,n.dataset.evidence==='morisot');if(n.dataset.evidence==='morisot')paths+=curve(cx2,cy+7,r.left-base.left,y+9);});
 svg.innerHTML=paths;svg.setAttribute('viewBox',`0 0 ${base.width} ${base.height}`);
}
if(view==='b'){new ResizeObserver(drawMap).observe(document.querySelector('#relationship-map'));requestAnimationFrame(drawMap);}

document.querySelector('#connection-choice')?.addEventListener('change',event=>{const key=event.target.value;document.querySelectorAll('[data-select]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.select===key)));document.querySelector('#explorer-detail').innerHTML=evidence(rows.find(r=>r.key===key));});
