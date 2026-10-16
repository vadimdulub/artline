import importlib.util
s=importlib.util.spec_from_file_location('b','ops/continuous-auckland-images-000113.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);i=b.i;h=b.h
notes={
'27df4e98':('accept','Entire oval landscape: standing figure with paddle on foreground rock, water and wooded shoreline, oval boundary and white surround intact. Physical/image ratio differs 1.6 percent; complete supplied composition.'),
'2dd6769a':('hold','Landscape with scattered groups and central foreground gathering, tall trees left and distant mountains. Image/physical ratio differs 7.8 percent; framed dimensions possible but full-frame uncertainty unresolved.'),
'34da1df2':('accept','Tall interior with clustered women and children, nurse bending over central child; full supplied canvas including lower edge and upper figures. Ratio differs 2.3 percent, no apparent detail crop.'),
'3fb5ffcd':('accept','White saddled horse and five dogs in wooded clearing, game birds and basket below saddle. Full supplied canvas and foreground retained; ratio differs 3.0 percent.'),
'46d22b5b':('hold','Dark mountain valley with sunlit clouds and rock-strewn river foreground. Native 480-pixel view has 9 percent physical/pixel proportion discrepancy; no correction invented.'),
'4fc3cd0c':('hold','Vertical rocky stream below wooded gorge. Distinct sketch identity retained; 5.3 percent physical/pixel discrepancy unresolved.'),
'5499e6c9':('hold','Wooded Italian landscape with river, foreground figures, distant buildings and mountains. Native 480-pixel view differs 26.6 percent from stated physical ratio; full composition cannot be assured.')}
audit=b.load(i.folder(b.B)/'quality-audit.json');ds=[]
for im in audit['prepared_images']:
 decision,note=notes[im['artwork_id'][:8]];ds.append(dict(artwork_id=im['artwork_id'],sha256=im['sha256'],artist=im['artist'],decision=decision,viewed_individually=True,tool='functions tools.view_image',path=im['path'],notes=note,flags_resolved=im['flags'] if decision=='accept' else [],original_separately_viewed=False))
rv=dict(at=h.now(),batch=b.B,batch_quality_decision='accept',decisions=ds,review_scope='All seven prepared JPEGs actually viewed individually. Three accepted; four held for unresolved physical/image proportion conflicts. Originals not separately visually inspected.',accepted_count=3,held_count=4)
b.save('batches/'+b.B+'/visual-review.json',rv);b.save('actual-visual-review.json',rv)
