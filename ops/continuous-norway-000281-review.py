"""Persist actual view_image observations for batch281, not automated visual claims."""
import importlib.util,fcntl
s=importlib.util.spec_from_file_location('b','ops/continuous-norway-images-000281.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);i=b.i
notes={
'1ac1419c-98eb-59f5-9f43-c3541028aa9f':'Woman in red dress sewing beside a table with jug under leafy arbour; bench, fence, foreground and lower-right signature retained. Complete supplied painting rectangle, authentic image.',
'1b18530d-2ae6-5e16-8cb3-96081a506bf6':'Dark-clothed man seated sideways on pale chair, chin on hand, name and signature across upper edge. Full supplied vertical painted composition retained.',
'1b42bec5-a6d3-5d79-81a8-318fabfa36b6':'Dim interior, figure silhouetted against window, table in foreground and lower-right signature. Soft dark detail is painted content, not a blank or placeholder.',
'1bc03ef4-2a4f-5fd6-9b41-e2b828ab1c94':'Frontal portrait with white lace bonnet and black dress against brown background. Full supplied portrait rectangle retained; no merchandise or detail substitute.',
'1bc6ae63-76b9-5ef2-b414-597b5faf0ee9':'Oslo townscape with industrial chimneys on left, large dark house on right, rooflines and foreground tracks. Entire supplied landscape composition retained.',
'1bd37239-7707-50b1-ac15-25649f40c4ca':'Log farm buildings with turf roofs before lake and mountain valley; original pale edge border retained on all sides. Complete supplied image.',
'1beb2abc-4b88-5b7c-8cf8-386ecc72c064':'Detailed pencil drawing of beech trunks and dense canopy, pale paper margins and GVI lower-left mark. Full supplied sheet retained.',
'1c0b68ed-cd96-57c0-9306-f7f811aaf321':'Cannon and small boat beside mountain lake under cloudy sky, inscription along lower edge. Full supplied landscape painting retained.',
'1c0dd6b1-4004-50fc-be70-3bedc9792668':'Young man with white pleated collar on oval painted support. Original and derivative viewed separately: complete oval and black surrounding source background preserved. Questioned sitter identification and presumed1827 source wording remain unchanged.',
'1c27c669-b88d-5b2e-8dac-5290ed2027bb':'Pencil study of seated man seen from behind, holding paper; Dahl1830 inscription and broad blank right/lower margins retained. Authentic full-sheet reproduction.',
'1c31f143-5a3d-5e0c-9a46-3e4ded32b3e0':'Sparse pencil plant study with buds, curving stem and Ep.80 inscription on narrow vertical sheet. Original and derivative separately viewed; extensive blank paper, top edge wear and complete source composition retained.',
'1c8b4bc9-e27a-55bf-9c2c-f67addb03b49':'Watercolour/pencil tree cluster above green park lawn and curving path. Unpainted paper and lower signature/marks retained in complete supplied sheet.',
'1c9740df-10f8-5a1f-804d-2a249188778f':'Pale pencil drawing of arched road bridge beside bay, right-side tree and lower-right1834 inscription. Original separately viewed: torn upper-right paper corner and blank sky belong to source; full supplied sheet retained without added crop.',
'1cc15ccf-ac1b-5dd2-a100-f00bf8af7801':'Colourful painted building site, stacked timber across foreground, roof frame behind shed, trees and small dogs. Complete supplied painting rectangle retained.'}
originals={'1c0dd6b1-4004-50fc-be70-3bedc9792668','1c31f143-5a3d-5e0c-9a46-3e4ded32b3e0','1c9740df-10f8-5a1f-804d-2a249188778f'}
with (b.RUNTIME/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 audit=b.load(i.folder(b.B)/'quality-audit.json');assert set(notes)==set(audit['sample_ids']) and len(notes)==14
 ds=[]
 for im in audit['prepared_images']:
  aid=im['artwork_id'];ds.append(dict(artwork_id=aid,sha256=im['sha256'],artist=im['artist'],decision='accept',viewed_individually=True,tool='functions tools.view_image',path=im['path'],notes=notes[aid],flags_resolved=im['flags'],original_separately_viewed=aid in originals,original_path=im['original_path'] if aid in originals else None,original_sha256=im['source_sha256'] if aid in originals else None))
 rv=dict(at=b.h.now(),batch=b.B,batch_quality_decision='accept',decisions=ds,review_scope='All14 prepared derivatives individually viewed using view_image; three originals separately viewed. Other11 originals technically decoded and hashed, not visually inspected. Generated contact sheet not viewed.',full_supplied_composition_preserved=True,placeholder_flag_resolution='manual_visual_required mechanically creates source_display_placeholder flag; all14 observed images are actual pictorial reproductions.')
 b.save(i.folder(b.B)/'visual-review.json',rv);b.save(b.E/'actual-visual-review.json',rv)
 b.save(b.E/'research-hold-clarification.json',dict(at=b.h.now(),records=[dict(artwork_id='1afee20b-4d01-5b2b-8e91-61649cda85b1',reason='English William II and source Vilhelm/Guillaume II appear to be translated aliases, not an established identity conflict. Current selection conservatively retains this as individual alias review; no image downloaded and metadata unchanged.'),dict(artwork_id='1c322da5-5b21-500a-9456-f7d2c8b0064e',reason='Current source names Evelina Stading. Missing unlinked creator label does not imply anonymous authorship. Historical native/source crosswalk needs separate reconciliation; no invented painter and no creator changes.')]))
print('14 derivative and3 original actual reviews saved')
