const descriptions={
  context:{title:'Clear destination, quiet appearance',reason:'“Back to Louvre guide” tells the visitor exactly what will happen. It shares the existing context line above the work, without a boxed button or a separate strip.',tradeoff:'Best for Artlines’ reading and discovery journeys. Long destination names need a short label on phones.'},
  breadcrumb:{title:'Familiar control, clearer hierarchy',reason:'A 28px outlined button sits in a 44px click area beside the existing artist breadcrumb. History and the permanent parent destination remain distinct.',tradeoff:'The most conservative change. It adds some visual weight, and “Back” alone is less informative than a named destination.'},
  header:{title:'More room for the artwork',reason:'A small return arrow uses space in the existing header. The content starts with its usual artist link; there is no extra return row.',tradeoff:'The cleanest content area, but the arrow is farther from the artwork and can be mistaken for global site navigation.'}
};
const controls={concept:'context',screen:'artwork',origin:'guide',size:'desktop'};
const params=new URLSearchParams(location.search);for(const k of Object.keys(controls))if(params.has(k))controls[k]=params.get(k);
if(!descriptions[controls.concept])controls.concept='context';
function update(){
  document.querySelectorAll('[data-concept]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.concept===controls.concept)));
  document.querySelectorAll('[data-size]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.size===controls.size)));
  for(const id of ['screen','origin'])document.getElementById(id).value=controls[id];
  const d=descriptions[controls.concept];document.getElementById('reason-title').textContent=d.title;document.getElementById('reason').textContent=d.reason;document.getElementById('tradeoff').textContent=d.tradeoff;
  const q=new URLSearchParams({concept:controls.concept,screen:controls.screen,origin:controls.origin});const url='preview.html?'+q;
  const frame=document.getElementById('preview');frame.src=url;frame.classList.toggle('mobile',controls.size==='mobile');document.getElementById('open-preview').href=url;
  document.getElementById('origin').disabled=controls.screen!=='artwork';
  document.getElementById('preview-note').textContent=controls.screen==='home'?'The main timeline has no Back control in any concept.':'Try the return control in the preview. These are local demonstration journeys.';
  history.replaceState(null,'','?'+new URLSearchParams(controls));
}
document.querySelectorAll('[data-concept]').forEach(b=>b.addEventListener('click',()=>{controls.concept=b.dataset.concept;update()}));
document.querySelectorAll('[data-size]').forEach(b=>b.addEventListener('click',()=>{controls.size=b.dataset.size;update()}));
for(const id of ['screen','origin'])document.getElementById(id).addEventListener('change',e=>{controls[id]=e.target.value;update()});
update();
