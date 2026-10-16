const escapeHTML = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const work = index => mockupData.works.find(w => w.asset === `assets/work-${index}.jpg`);
const picture = (index, cls = '') => `<img class="${cls}" src="${work(index).asset}" alt="${escapeHTML(work(index).title)} — ${escapeHTML(work(index).artist)}">`;
const arrow = '<svg aria-hidden="true" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M3 10h13M11 4l6 6-6 6"/></svg>';
const action = text => `<span class="action">${text}${arrow}</span>`;
const link = (kind, cls, content) => `<a class="${cls}" href="${escapeHTML(mockupData.links[kind])}" target="_blank" rel="noopener">${content}</a>`;
const strip = (indices = [2,10,3]) => `<div class="art-strip">${indices.map(i => `<figure${i===2?' class="wide"':''}>${picture(i)}</figure>`).join('')}</div>`;
const person = (index, name, years) => `<figure class="person">${picture(index)}<figcaption>${name}<small>${years}</small></figcaption><span class="life-rule" aria-hidden="true"></span></figure>`;
const portraits = () => `<div class="people-preview">${person(0,'Albrecht Dürer','1471–1528')}${person(9,'Rembrandt','1606–1669')}</div>`;
const copy = (title, desc, count, cta) => `<div class="copy"><h3>${title}</h3><p>${desc}</p><div class="bottom-line"><span class="count">${count}</span>${action(cta)}</div></div>`;
const heading = (title, desc, stacked=false) => `<header class="section-head${stacked?' stacked':''}"><h2>${title}</h2><p>${desc}</p></header>`;
const contextStill = (asset, title, kind) => `<figure><div class="still-image"><img src="${asset}" alt="${escapeHTML(title)}"></div><figcaption><strong>${kind}</strong><span>${title}</span></figcaption></figure>`;
const staticContext = () => `<div class="static-context">${contextStill(work(10).asset,'Sunflowers','Artwork')}${staticContextAssets.map(x=>contextStill(x.asset,x.title,x.kind)).join('')}</div>`;
const staticArtist = () => `<figure class="static-artist">${picture(0)}<figcaption>Albrecht Dürer · Self-Portrait</figcaption></figure>`;
const a = heading('Explore beyond the guide','See the works together, then discover the artists behind them.') + `<div class="destinations">${link('all','destination',strip()+copy('Explore the artworks','Discover all 30 works alongside the books and history of their time.','30 selected works','Open collection'))}${link('painters','destination',portraits()+copy('Artists across time','See when the artists lived and whose lives overlapped.','25 artists in this guide','Explore timeline'))}</div>`;
const b = heading('See the collection in a new way','Two ways to continue your visit.',true) + `<div class="destinations">${link('all','destination',`<div class="exhibition-wall">${picture(10,'hero-work')}<div class="side-works">${picture(2)}${picture(11)}</div></div>`+copy('Explore the collection','Bring the guide’s 30 works together, with the world around them.','Art, books & history','Open collection'))}${link('painters','destination',`<div class="portrait-wall"><figure>${picture(0)}<figcaption>Albrecht Dürer</figcaption></figure><figure>${picture(9)}<figcaption>Rembrandt</figcaption></figure></div>`+copy('Meet the artists','Follow 25 artists through an interactive timeline of their lives.','Their lives, side by side','Explore timeline'))}</div>`;
const c = heading('Keep exploring','The guide is a starting point. Choose where to go next.') + `<div class="compact-destinations">${link('all','compact-link',strip([2,10,3])+`<div><h3>View the collection</h3><p>30 works, with the books and history that share their time.</p></div>`+action('Open collection'))}${link('painters','compact-link',`<div class="compact-portraits">${picture(0)}<span class="portrait-line" aria-hidden="true"></span>${picture(9)}</div><div><h3>Follow the artists</h3><p>Explore 25 lives on a timeline. See who lived at the same time.</p></div>`+action('See the timeline'))}</div>`;
const d = heading('Find your next connection','A glimpse of what you can explore in Artline.') + `<div class="destinations">${link('all','destination',staticContext()+copy('Artworks in context','Follow the guide’s works through time, with art, books and history together.','30 works to explore','Explore the collection'))}${link('painters','destination',staticArtist()+copy('Who lived when?','Place the artists on one timeline and discover their contemporaries.','25 artists in this guide','Open artist timeline'))}</div>`;
const descriptions = {
  a:'<strong>A · Gallery pair — recommended.</strong> Two equally inviting destinations. Large pictures make both choices clear, with familiar Artline styling.',
  b:'<strong>B · Exhibition spread.</strong> Gives the artworks more space and uses self-portraits to draw visitors into the artist timeline.',
  c:'<strong>C · Compact invitations.</strong> Two short, illustrated rows. A smaller footprint within a long guide, while keeping both destinations visible.',
  d:'<strong>D · Revised with static imagery.</strong> An artwork, a book and an event illustrate the collection. A single self-portrait illustrates “Who lived when?”'
};
document.getElementById('concepts').innerHTML = Object.entries({a,b,c,d}).map(([key,content]) => `<section id="concept-${key}" class="board board-${key}" aria-label="Mockup ${key.toUpperCase()}" hidden>${content}</section>`).join('');
document.getElementById('credits').innerHTML = mockupData.works.map(w => `<li><a target="_blank" rel="noopener" href="${escapeHTML(w.imageSource)}">${escapeHTML(w.title)} — ${escapeHTML(w.artist)}</a><span>${escapeHTML(w.credit)}</span></li>`).join('');
document.getElementById('credits').innerHTML += staticContextAssets.map(x => `<li><a target="_blank" rel="noopener" href="${escapeHTML(x.sourceUrl)}">${escapeHTML(x.title)} — ${escapeHTML(x.label)}</a><span>${escapeHTML(x.credit)} · ${escapeHTML(x.license)}</span></li>`).join('');
function choose(view, update=true) {
  if (!descriptions[view]) view='a';
  document.querySelectorAll('.board').forEach(e => e.hidden=e.id!==`concept-${view}`);
  document.querySelectorAll('[data-view]').forEach(e => e.setAttribute('aria-pressed',String(e.dataset.view===view)));
  document.getElementById('design-note').innerHTML=descriptions[view];
  if(update) history.replaceState(null,'',`?view=${view}`);
}
document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click',() => choose(button.dataset.view)));
choose(new URLSearchParams(location.search).get('view')||'d',false);
