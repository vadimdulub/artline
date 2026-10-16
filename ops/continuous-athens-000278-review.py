"""Record only the actual eight derivative and two original visual inspections."""
import importlib.util,fcntl,re
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-athens-images-000278.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
notes={
'1f1864a3-54f0-546f-b768-64b5580c9671':'Two people on a cliff ledge above foaming waves; tall composition with storm sky and lower-left signature. Native image boundary and complete supplied composition retained.',
'292f3586-7fa5-5c7d-a2fa-7ce774fd6618':'Moonlit sea with rowboat, distant vessels and temple on right headland; narrow outer edges and lower-right signature visible. Complete native seascape, distinct from the Sounion tempest.',
'42e32859-1626-58f0-9d43-20d21cb100b1':'Wrecked sailing ship and two lifeboats amid waves, signature/date lower right. Derivative and source original viewed individually; complete supplied file preserved, but source pixel ratio differs by about5.3 percent from physical dimensions93x145cm. Hold until source geometry/version discrepancy independently resolved.',
'455c4212-2e04-58f2-869b-962012d01b32':'Burning ship at left with several men in foreground boat at right and dark cliffs beyond. Entire supplied scene preserved; exact inventory differentiates the separate same-title work.',
'4da4f9b1-9c27-5a56-a278-a8780dbfa6c8':'Figure clinging to spar in heavy green waves under dark storm sky; signature/date lower right. Source original and derivative viewed individually. Pixel ratio differs by about26 percent from stated94x114cm; cannot resolve whether source geometry or dimensions are wrong. Hold image, preserve metadata.',
'904e6846-3355-550d-bbb3-32167300de5b':'Bright explosion at monastery on right with crowded figures below; quieter sea and mountain at left. Full supplied composition and lower-left inscription retained; no detail crop introduced.',
'cefcf664-3d0b-5a33-8f27-5339bbc29158':'Sailing vessel beneath moon with temple on high cliff at left, rowboat and lone swimmer. Whole native rectangle and worn edges preserved; composition distinct from The Sea at Sounion.',
'e20f47d4-a6bd-5bf1-be6e-978adea505ae':'Monochrome drawing: artist seated at lower left, leafy tree, shore and boat with figures at lower right. Full paper field, faint detail and lower inscription preserved; not a blank placeholder. Existing unknown type retained without metadata change.'}
held={'42e32859-1626-58f0-9d43-20d21cb100b1','4da4f9b1-9c27-5a56-a278-a8780dbfa6c8'}
with (b.RUNTIME/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 audit=b.load(i.folder(b.B)/'quality-audit.json');assert set(notes)==set(audit['sample_ids']);ds=[];dimensions=[]
 for im in audit['prepared_images']:
  aid=im['artwork_id'];orig=aid in held
  ds.append(dict(artwork_id=aid,sha256=im['sha256'],artist=im['artist'],decision='hold' if aid in held else 'accept',viewed_individually=True,tool='functions tools.view_image',path=im['path'],notes=notes[aid],flags_resolved=im['flags'],original_separately_viewed=orig,original_path=im['original_path'] if orig else None))
  r=next(v for v in i.selected(b.B)['rows'] if v['artwork_id']==aid);desc=r['image']['source']['description'];m=re.search(r'([\d,]+) x ([\d,]+) cm',desc);ph,pw=[float(x.replace(',','.')) for x in m.groups()];pix=im['original_dimensions'][0]/im['original_dimensions'][1];delta=abs(pix/(pw/ph)-1)
  dimensions.append(dict(artwork_id=aid,physical_dimensions_cm=[ph,pw],source_pixel_dimensions=im['original_dimensions'],relative_aspect_discrepancy=delta,individual_source_original_viewed=orig,outcome='held_source_geometry_unresolved' if aid in held else 'accepted_exact_native_object_and_full_supplied_composition',source_dimensions_unchanged=True))
 rv=dict(at=h.now(),batch=b.B,batch_quality_decision='accept',decisions=ds,review_scope='Eight actual prepared JPEGs viewed individually; two flagged originals additionally viewed. Six accepted; two held. Generated contact sheet was not viewed.',full_supplied_composition_preserved=True)
 b.save(i.folder(b.B)/'visual-review.json',rv);b.save(b.E/'actual-visual-review.json',rv)
 b.save(b.E/'physical-dimension-review.json',dict(at=h.now(),records=dimensions))
 b.save(b.E/'research-holds.json',dict(at=h.now(),records=[dict(artwork_id=aid,reason=notes[aid],next_step='Require independent museum geometry or full-work/version corroboration; do not repeat unchanged file download.') for aid in sorted(held)]))
 old=b.load(b.E.parent/'000044/independent-campaign-stop-verification.json');files=[]
 for v in old['files']:
  p=b.ROOT/v['path'];assert h.sha(p.read_bytes())==v['sha256'];files.append(dict(path=v['path'],sha256=v['sha256']))
 b.save(b.E/'independent-campaign-stop-verification.json',dict(at=h.now(),files=files,all_unchanged=True,separate_campaign=b.OP,no_completed_controller_invoked=True))
 print('Actual visual review:8 derivatives,2 originals,6 accepted,2 held')
