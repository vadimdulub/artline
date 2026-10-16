"""Persist actual individual view_image review of all 15 prepared native images."""
import importlib.util,fcntl
s=importlib.util.spec_from_file_location('b','ops/continuous-auckland-images-000101.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);i=b.i
notes={
'2680394c': 'Profile of a dark-haired girl facing left, cream scarf over green clothing, light background and signature at lower right. Complete supplied portrait with dimensions agreeing within one percent.',
'2807e7f2': 'Seated woman in pink at left, bearded man behind reclining bare-shouldered youth at right, metal ewer foreground. Complete multi-figure interior including foreground floor; native proportions agree.',
'2bd4de8c': 'Dark-haired woman in a high-neck violet dress against green-blue brushwork, signature upper left. Complete bust composition, native dimensions agree within one percent.',
'2e352705': 'Blue rapids and white foam between rocks and wooded banks, distant hills. Full supplied landscape and lower-right signature; native 480-pixel source has limited detail, not upscaled.',
'2e96c01e': 'Sailing boats on water at left and ruined shore fort at right under cloudy sky. Full supplied bitmap, but its 480x234 proportions differ by 12.5 percent from 1473/808 museum dimensions. Possible frame measurement or source crop unresolved; HOLD, no attachment.',
'3301e574': 'Patchwork ochre/green fields and village buildings in a mountain valley. Complete supplied composition with lower-right signature; native 480-pixel source retained without upscaling.',
'343a6772': 'Reclining figure on yellow cloth, standing robed celebrant with raised vessel, dancers behind under an awning and large foliage at right. Complete wide painted study including foreground and signature.',
'3aa516af': 'Timber mill buildings and stream in a forested valley, large tree trunks and foreground foliage, signature lower left. Full supplied landscape; native 480-pixel source, no upscaling.',
'3e5b9829': 'Harbour and rooftops viewed through foreground pines, water and distant ridge. Complete supplied landscape, including foreground path and lower canvas edge; proportions agree within one percent.',
'3fc4f088': 'Golden turbulent stream and rocks in foreground, two cattle on green slope, cloud-wrapped mountain beyond. Full supplied vertical view. Museum dimensions include a 20-mm third dimension; 3.4-percent aspect difference retained as measurement uncertainty, no apparent montage/detail crop. Native 480-pixel source, not upscaled.',
'405bf142': 'Sunlit jagged rock formation beyond a wooded valley; foreground track and small travellers, tall trees at right. Complete wide landscape including sky, wooded foreground and native lower edge; 2.3-percent measurement difference retained.',
'4ad93678': 'Moon reflected across still harbour, boats and dark shore rocks, cloud bands overhead. Complete supplied landscape, 2.3-percent native dimension difference retained. Native 480-pixel source not upscaled.',
'4cd94087': 'Woman and children with armed escorts in a boat approaching a monastery doorway; monk at left, oar and water foreground. Complete supplied final-canvas composition, not the smaller oil study. Native accession MU/81, 1897 and canvas dimensions agree.',
'4f1f43f5': 'Pale bare tree trunk and branching limbs over a stylized hill valley, artist signature lower right. Entire supplied rectangular painting; branch reaching upper edge is preserved as supplied, no added crop.',
'56dc700d': 'Three women under a portico at dawn; standing figure at left, central figure shading her eyes and seated red-clad figure at right. Full supplied composition including overhead drapery and foreground. Native 480-pixel source not upscaled.'}
with (b.R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);audit=b.load(i.folder(b.B)/'quality-audit.json');ds=[]
 for im in audit['prepared_images']:
  key=im['artwork_id'][:8];d='hold' if key=='2e96c01e' else 'accept'
  ds.append(dict(artwork_id=im['artwork_id'],sha256=im['sha256'],artist=im['artist'],decision=d,viewed_individually=True,tool='functions tools.view_image',path=im['path'],notes=notes[key],flags_resolved=im['flags'] if d=='accept' else [],original_separately_viewed=False,dimension_discrepancy_review=key=='3fc4f088'))
 rv=dict(at=b.h.now(),batch=b.B,batch_quality_decision='accept',decisions=ds,review_scope='All 15 prepared native JPEGs actually viewed individually in this worker. Fourteen accepted, one held for physical/pixel proportion conflict. Originals separately archived and technically decoded; not represented as separately viewed.',accepted_count=14,held_count=1)
 b.save('batches/'+b.B+'/visual-review.json',rv);b.save('actual-visual-review.json',rv)
print('Actual individual visual review: 14 accepted, 1 full-frame hold')
