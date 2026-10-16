"""Persist the eight actual individual derivative reviews from batch277."""
import importlib.util,fcntl
s=importlib.util.spec_from_file_location('b','ops/continuous-norway-images-000277.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);i=b.i
notes={
'17170cd6-bcdc-5705-842d-69052dcd5d2f':'Wide pen drawing of a canal from a boat, boatman at right, poles and distant buildings; entire narrow paper sheet, folds and signature retained. Authentic pictorial drawing, no placeholder or introduced crop.',
'17647fc0-84d1-5732-b82c-47befd9d51be':'Young woman in black head covering and regional costume with white blouse and dark bodice, hands at waist. Entire supplied painted rectangle and lower inscription visible; full native portrait composition.',
'178ae7d7-6365-5703-a371-0634ecfe4b96':'Lightly coloured landscape drawing with fenced fields, trees, a hill and distant castle, large blank upper paper. Full supplied sheet and lower-left inscription retained. Sparse drawing is not a placeholder.',
'183e3a3f-5158-57b2-90a6-3592652b6123':'Dark wooden interior with seated figure beside open leaded window, papers and equipment on desk, panelled door at right. Whole painted rectangle and lower inscription retained. Dark tones contain authentic detail.',
'18766f66-796a-5c53-8ccb-6a2f919aa0a2':'Rocky road with walking figure and laden donkey, small structure and trees beyond. Full painted image with worn edges and dated inscription at lower left; no introduced crop.',
'18d722f4-060b-5444-9c44-7f70686e0940':'Pencil cafe drawing with seated man in top hat and woman, further figures and open doorway behind. Complete sheet boundaries, lower-right signature and foreground legs visible; no montage.',
'18dab1d1-5dfc-5e4b-afcf-6c3d34233a8d':'Coastal village with red-roofed buildings, rocky foreground paths and islands across the sea. Entire supplied landscape rectangle, surface wear and lower-right inscription retained.',
'19187a31-761c-5565-bf9b-e1262a52db0e':'Mountain ridge beneath storm clouds, reindeer on foreground rocks and along sunlit summit. Complete supplied painted rectangle with narrow visible top border; authentic painting, no detail crop.'}
with (b.RUNTIME/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 audit=b.load(i.folder(b.B)/'quality-audit.json');assert set(notes)==set(audit['sample_ids'])
 ds=[]
 for im in audit['prepared_images']:
  ds.append(dict(artwork_id=im['artwork_id'],sha256=im['sha256'],artist=im['artist'],decision='accept',viewed_individually=True,tool='functions tools.view_image',path=im['path'],notes=notes[im['artwork_id']],flags_resolved=im['flags'],original_separately_viewed=False))
 rv=dict(at=b.h.now(),batch=b.B,batch_quality_decision='accept',decisions=ds,review_scope='All eight actual prepared JPEGs viewed individually with tools.view_image in batch277. Originals technically decoded and hashed, not separately visually viewed. Generated contact sheet not viewed and not used as visual evidence.',full_supplied_composition_preserved=True,placeholder_flag_resolution='The workflow sets source_display_placeholder for every manual_visual_required record. All eight actual images are authentic pictorial museum reproductions, individually reviewed.')
 b.save(i.folder(b.B)/'visual-review.json',rv);b.save(b.E/'actual-visual-review.json',rv)
print('Eight actual individual image reviews recorded')
