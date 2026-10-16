import importlib.util,fcntl
s=importlib.util.spec_from_file_location('b','ops/continuous-bavarian-images-000106.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);i=b.i;h=b.h
with (b.R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 audit=b.load(i.folder(b.B)/'quality-audit.json');assert len(audit['prepared_images'])==2
 notes={
 '6683ffc4-9dd2-5579-893d-95e818641239':'Original museum source and derivative actually viewed individually. Woman with braided hair, red/brown pleated dress, white bodice, white kerchief in her left hand at viewer right; patterned hanging at left and dark background. Full supplied painted rectangle retained. Clearly distinct from blue-dress Louvre La Belle Nani. Museum ca1570 is date evidence only; unknown catalogue year stays unchanged. Physical image ratio differs from catalogue measurements by about2%; exact object page and composition support identity, no stretch/crop correction made.',
 '84ba1814-09a7-5c56-8e9a-d9bb36297378':'Original museum source and derivative actually viewed individually. Dark interior, sleeping woman in red at left with white head wrap and pipe, a recumbent man in background bed, two background figures at right, tankard at lower left and shoes at bottom. Full supplied panel surface and all edges preserved. Agrees with exact official title/subject, 1640/1650 and inventory1280. Supplied image ratio differs from listed37x31cm by about3%; individually reviewed, no cropping or stretching introduced. Do not substitute another sleeping-woman painting.'}
 decisions=[]
 for im in audit['prepared_images']:
  decisions.append(dict(artwork_id=im['artwork_id'],sha256=im['sha256'],artist=im['artist'],decision='accept',viewed_individually=True,tool='functions tools.view_image',path=im['path'],original_viewed=True,original_separately_viewed=True,original_path=im['original_path'],original_sha256=im['source_sha256'],notes=notes[im['artwork_id']],flags_resolved=im['flags']))
 rv=dict(at=h.now(),batch=b.B,batch_quality_decision='accept',decisions=decisions,review_scope='Both selected museum originals and both derivatives actually viewed; no new viewing claim for the188 reserve derivatives, whose checksum-bound historical reviews were verified.',accepted_count=2,held_count=0)
 b.save('batches/'+b.B+'/visual-review.json',rv);b.save('actual-visual-review.json',rv)
 stop=b.ROOT/'docs/research/illustrated-300k-20261011/workers-stopped.json';b.save('completed-campaign-stop-preservation.json',dict(path=str(stop.relative_to(b.ROOT)),sha256=h.sha(stop.read_bytes()),separate_campaign=i.OP,restarted=False))
