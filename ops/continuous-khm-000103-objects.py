import importlib.util,fcntl,json
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b','ops/continuous-khm-images-000103.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
p=b.mod('parser103','cesi-top100-20261010.py');p.capture=b.capture
urls=['https://www.wikiart.org/en/salomon-van-ruysdael/winterlandschaft-am-wasser-0','https://www.wikiart.org/en/salomon-van-ruysdael/winterlandschaft-am-wasser','https://www.wikiart.org/en/hieronymus-bosch/christ-carrying-the-cross-1490','https://www.wikiart.org/en/palma-il-giovane/the-lamentation-of-christ','https://www.wikiart.org/en/palma-il-giovane/the-lamentation-over-the-dead-christ','https://www.wikiart.org/en/pieter-claesz/vanitas-still-life-1660']
with (b.R/'worker.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 for url in urls:
  try:
   row=p.wiki_fields(url);b.save('objects/'+url.rsplit('/',1)[1]+'.json',row);print(json.dumps({k:row[k] for k in ['source_url','title','date','creator','fields','rights_label']}),flush=True)
  except AssertionError as e:print(str(e),flush=True)
