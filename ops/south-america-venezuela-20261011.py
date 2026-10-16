import importlib.util,collections
s=importlib.util.spec_from_file_location('k','ops/south-america-curation-20261011.py');k=importlib.util.module_from_spec(s);s.loader.exec_module(k);c=k.c;d=k.d
url='https://www.mincultura.gob.ve/noticias/hoy-16-de-junio-el-museo-arturo-michelena-celebra-su-60-aniversario/'
x=c.probe(url);rc=x['evidence'];museum='Museo Arturo Michelena';slug='museo-arturo-michelena-caracas'
d.save(c.RUN/'institution-registry-wave2.json',{museum:dict(slug=slug,website=url,country_code='VE',city='Caracas')})
d.save(c.RUN/'geography-evidence'/(slug+'.json.gz'),dict(city='Caracas',country_code='VE',evidence=rc,basis='Official Ministry article explicitly gives Urapal 82, La Pastora, Caracas, Venezuela.'))
creator=next(x for x in d.load(c.RUN/'BREADTH/manual-facts.json.gz')['records'] if x['country_code']=='VE')['verified_artist_id']
rows=[]
for title,year,circa in [('Autorretrato con Corguera',1888,False),('Estudio para el niño enfermo',1886,True),('Lastenia Tello de Michelena',1890,False),('Estudio de Jesús para la multiplicación de los panes',1897,True),('Estudio para la noche',1896,True),('La alcoba',1890,True),('La pulpería',1898,False),('Boceto II para Lucrecia Borga',1890,False),('Señoritas en el campo',1895,False),('Lola Herrera Ramella',1896,True),('Estudio de ciervo y jauría para Diana Cazadora',1896,True),('Los cisnes de El Calvario',1893,True),('Estudio para Virgen Bizantina',1896,True),('Niña y perro',1894,True),('Boceto para Dante y Beatriz',1889,True)]:
 row=k.f.f.fact('venezuela-mppc',museum,'mam-2023-'+d.sha(title.encode())[:16],url,title,'Arturo Michelena',('hacia ' if circa else '')+str(year),None,None,None,'painting',rc,dict(source_caption=title+' ('+('hacia ' if circa else '')+str(year)+')',identity='Named painting/study in official MAM collection list. Preparatory work is not conflated with the finished composition. No inventory, dimensions or medium invented.',date_basis='Source creation caption; not the 1963 museum opening date.',source_key_basis='Stable hash of exact collection-list title; no museum inventory number implied.'),country_code='VE',verified_artist_id=creator,creator_link_hold=True,source_provider_name='Ministerio del Poder Popular para la Cultura — Museo Arturo Michelena / Fundación Museos Nacionales',holding_confidence=.97,holding_basis='Official museum anniversary article names these paintings in the museum collection. Historical permanent exhibition wording is not imported as current display.')
 rows.append(row)
with d.connect() as db:
 existing=list(db.execute('SELECT a.id::text,a.title,a.creation_year_start,a.creation_year_end,a.dimensions_text FROM artworks a JOIN artwork_artists aa ON aa.artwork_id=a.id WHERE aa.artist_id=%s AND a.status<>%s',(creator,'archived')))
print('Existing Michelena works',existing,flush=True)
d.save(c.RUN/'VE/mppc-facts.json.gz',dict(records=rows,existing_artist_scope=existing,omitted=[dict(title='La vara rota',reason='Known WikiArt finished work/related sketches require source identity reconciliation; not counted new in this list.')]))
k.plan('VE','mppc','VE-wave1',10)
