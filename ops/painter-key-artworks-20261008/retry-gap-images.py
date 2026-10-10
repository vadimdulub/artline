from pathlib import Path
p=Path('/tmp/artline-key-artwork-20261008/download-gap-images.py');s=p.read_text()
s=s.replace("rows=m.base.load(m.RUN/'gap-reviewed-plan.json.gz')", "previous=m.base.load(m.RUN/'gap-image-preparation.json.gz'); failed={r['work_qid'] for r in previous if r.get('error')}; rows=[r for r in m.base.load(m.RUN/'gap-reviewed-plan.json.gz') if r['work_qid'] in failed]")
s=s.replace("info=row['image_info'];url=info.get('thumburl') or info['url'];original=", "info=row['image_info'];url=info.get('thumburl') or info['url'];\n  # Wikimedia asks external consumers to use its standard thumbnail sizes.\n  # Request a cached 500px derivative when imageinfo returned a full original.\n  if '/thumb/' not in url and info.get('width',0)>500:\n   url=info['url'].split('?')[0].replace('/wikipedia/commons/','/wikipedia/commons/thumb/')+'/500px-'+info['url'].split('?')[0].split('/')[-1]\n  original=")
s=s.replace('max_workers=2','max_workers=1').replace('time.sleep(.5)','time.sleep(1.5)')
s=s.replace('results=[]','results=[r for r in previous if r.get("prepared")]').replace('gap-image-preparation.json.gz\',results','gap-image-preparation-retry.json.gz\',results')
s=s.replace("review-%03d.jpg", "review-retry-%03d.jpg")
Path('/tmp/artline-key-artwork-20261008/retry-gap-images-run.py').write_text(s)
