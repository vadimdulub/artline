import importlib.util,json
s=importlib.util.spec_from_file_location('b','ops/continuous-greek-batch-000286.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;i=b.i
assert not (b.E/'page5-index-capture.json').exists()
q=h.load(b.E/'source-queue-preimage.json');route=next(x for x in q['sources'] if x['source_id']=='national_gallery_athens');assert route['resume_cursor']['next_page']==5
url='https://www.nationalgallery.gr/wp-admin/admin-ajax.php';data={'creteria[language]':'en','creteria[artwork_name]':'','creteria[artwork_type]':'64','creteria[permanent_exhibition]':'','creteria[location]':'','creteria[extra_filters]':'false','page':'5','action':'get_artworks'}
i.provider_slot('www.nationalgallery.gr');r=i.session().post(url,data=data,timeout=(15,45));p=b.S/'page5-index.json';p.write_bytes(r.content)
b.save('page5-index-capture.json',dict(at=h.now(),url=url,request=data,status=r.status_code,sha256=h.sha(r.content),body_path=str(p),retry_after=r.headers.get('Retry-After')))
assert r.status_code==200
v=r.json();b.save('page5-index.json',v);urls=[x['link'] for x in v['results']];assert len(urls)==len(set(urls))<=50
b.save('page5-all-object-urls.json',urls);print(json.dumps(v,ensure_ascii=False)[:10000])
