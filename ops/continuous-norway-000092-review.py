import importlib.util,json,fcntl
s=importlib.util.spec_from_file_location('b','ops/continuous-norway-images-000092.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);i=b.i
notes={
'125da468-ef20-502e-9ec1-96e4282de1b7':'Loose black drawing on cream paper, outdoor tables/chairs and foliage; lower-left location/date inscription visible. Whole supplied rectangular sheet image, not placeholder.',
'129b44f8-578a-52df-9ff2-aed30ce8ff08':'Pencil figure studies on cream sheet: reclining figures below, upright/hovering figures above, dark rectangular study at bottom. Distinct drawing sheet, not finished sculpture.',
'12fad210-94d7-5e62-9ab2-76d1efeb87cf':'Red vine covers white house, blue-green windows, green garden and blue sky. Painted boundaries visible; complete frontal reproduction.',
'132622b4-74ae-5cc6-a9fa-b8acdff43b65':'Broad grey-blue mountain above red and ochre rocky terrain; complete landscape composition with lower-right signature region retained.',
'1333a137-763a-50da-8a82-a46a159fb790':'Wide Funchal coastal landscape: ships at left, settlement across centre, tall spreading tree and figures at right. First of four native views is the frontal painting, not reverse/detail.',
'134a8425-e300-5c24-9e7b-bb6a8bee1d85':'Pencil sheet of winged figures and a relief study with handwritten notes; multiple sketches are integral to this single drawing sheet. No montage or substituted finished relief.',
'1361ca58-bad7-5f24-8b59-df8ba8eaeb8a':'Two figures in dark prison interior, chain and column at left, straw below, Gastaldi signature at lower right. Dark image retains painted scene and outer edges; no blank placeholder.',
'13c50f99-4930-5c88-8ffd-ace4a38fad3d':'Reclining cow in pencil, head facing left, complete animal and surrounding paper; Dahl 1825 inscription visible below. Paper stains retained, no crop.'}
with (b.RUNTIME/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 audit=b.load(i.folder(b.B)/'quality-audit.json');assert set(notes)==set(audit['sample_ids'])
 ds=[]
 for im in audit['prepared_images']:
  assert im['artwork_id'] in notes
  ds.append(dict(artwork_id=im['artwork_id'],sha256=im['sha256'],artist=im['artist'],decision='accept',viewed_individually=True,tool='functions tools.view_image',path=im['path'],notes=notes[im['artwork_id']],flags_resolved=im['flags'],original_separately_viewed=False))
 rv=dict(at=b.h.now(),batch=b.B,batch_quality_decision='accept',decisions=ds,review_scope='All eight actual prepared JPEGs viewed individually with the image tool in this worker. Source originals technically decoded and hashed, not separately visually viewed. Generated sheet was not used as review evidence.',full_supplied_composition_preserved=True)
 b.save(i.folder(b.B)/'visual-review.json',rv);b.save(b.E/'actual-visual-review.json',rv)
print('Eight actual individual image reviews recorded')
