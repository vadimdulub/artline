"""Selected BYZART originals and captioned official catalogue illustrations."""
import importlib.util,json,re,gzip
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('m','ops/cyprus-deep-20261010.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
b=m.h.load(m.RUN/'baseline.json.gz');works={a['id']:a for a in b['artworks']};mus={i['id']:i for i in b['museums']};out=[]
def api(url,name):
    p=m.RUN/'historica'/name
    if p.exists():return m.h.load(p)
    raw,rc=m.h.capture(url);v=dict(data=json.loads(raw),receipt=rc);m.h.save(p,v);return v
def image_url(i):
    bundles=api(f'https://historica.unibo.it/server/api/core/items/{i}/bundles',i+'-bundles.json')['data']['_embedded']['bundles']
    bundle=next(x for x in bundles if x['name']=='ORIGINAL')
    streams=api(bundle['_links']['bitstreams']['href'],i+'-bitstreams.json')['data']['_embedded']['bitstreams']
    assert streams
    # Select only the first numbered photograph; remaining originals are not downloaded.
    selected=sorted(streams,key=lambda x:x['name'])[0]
    return selected['_links']['content']['href']
def fact(key,slug,title,a,z,display,typ,**kw):
    f=dict(key=key,museum_slug=slug,title=title,start=a,end=z,precision='unknown'if a is None else'exact'if a==z else'range',date_display=display,accession=None,creator=None,work_type=typ,medium=None,dimensions=None,image_eligible=z is not None and z<=1955,view_label='Complete supplied object photograph')
    f.update(kw);out.append(f);return f
def existing(a,**kw):
    return fact('existing:'+a['id'],mus[a['current_institution_id']]['slug'],a['title'],a['creation_year_start'],a['creation_year_end'],a['date_display'],a['work_type'],existing_id=a['id'],precision=a['date_precision'],accession=a['accession_number'],creator=a['unlinked_creator_label'],medium=a['medium_text'],dimensions=a['dimensions_text'],**kw)
def hist(i,slug,title,acc,typ,existing_id=None,**overrides):
    v=m.h.load(m.RUN/'historica/objects'/f'{i}.json');md=v['record']['metadata'];val=lambda k:', '.join(x['value']for x in md.get(k,[]))or None
    desc=BeautifulSoup(val('dc.description')or'','html.parser').get_text(' ',strip=True)
    a=int(val('dc.date.start'));z=int(val('dc.date.end'));src='https://historica.unibo.it/entities/publication/'+i
    extra=dict(source_url=src,source_record_id=i,source_receipt=v['receipt'],locator='Museum inventory '+str(acc)+'; BYZART item '+i,description=desc,source_original_title=val('dc.title'),source_date_start=a,source_date_end=z,rights_label=val('dc.rights.license'),rights_holder=val('dcterms.rightsHolder'),image_url=image_url(i),identity_basis='Museum-provided BYZART object record with inventory and individually linked original photograph; other views/details excluded. No current-display assertion.')
    if existing_id:f=existing(works[existing_id],**extra)
    else:
        f=fact('byzart:'+slug+':'+acc,slug,title,a,z,f'{a}–{z}'if a!=z else str(a),typ,accession=acc,medium=val('dc.format.medium'),dimensions=val('dc.format.extent'),**extra)
        if 'ca. 'in desc:f['precision']='circa'if a==z else'circa_range';f['date_display']='c. '+f['date_display']
    f.update(overrides);print('SELECTED',title,flush=True)
T='cyprus-byzantine-museum-of-the-holy-bishopric-of-tamasos-and-oreinis-2';K='kykkos-monastery-museum'
hist('d24d0167-7193-4920-a9fb-b6eb2ad586a4',T,'Mother of God Blachernitissa','TE2263','painting',date_display='13th–14th century (source range 1200–1399)')
hist('6441aa1e-27e2-46cc-967b-41e953dcb7f3',T,'Saint George (?) — fragmentary icon','TE2262','painting',date_display='Late 13th–early 14th century; structured source range 1200–1399',precision='circa_range')
hist('93442733-bd9c-4d40-bb9a-042f0707ea2b',T,'Reliquary cross with the Virgin Kyriotissa and Evangelists','TA080','metalwork',date_display='10th–11th century (source range 900–1099)',view_label='Exterior with the Virgin Kyriotissa and Evangelists')
hist('80275d22-c22c-43e4-b92b-dcb1a92eea1c',T,'Wooden painted cross with the Crucifixion','TE2233','painting',view_label='Obverse; the reverse is the same object')
for i,title,acc in [
('93b41ce4-c8ed-4e43-9da7-6039a8dcffcb','Saints Barbara and Marina','E 810'),
('579c647a-e2b7-49eb-a619-d73c8a8ae179','Saint Andronikos','E 809'),
('7cc77730-7f8e-4a2f-ba70-396da83a67e9','Enthroned Virgin and Child with an unidentified female saint','E 812'),
('e7496422-306e-4b72-8684-704d86efff09','Enthroned Virgin holding the blessing Christ','E 814'),
('541220bd-4e19-441c-b0b8-fa214de9e02f','Standing Virgin and Child with an unidentified monk saint','E 811'),
('01e984ff-acd9-410d-b75f-bd4b4822ae3c','Unidentified bishop saint','E 813'),
('f416483c-8ed9-4bb4-9f56-e93de2c7019e','Crucifixion and fragment of the Deposition','E 808')]:hist(i,K,title+' — detached mural from Saint Anthony, Kellia',acc,'fresco')
for i,aid,acc in [
('ba828e38-925c-48f6-8934-14739ca3e0b9','001ad345-d985-536b-aa2b-dcdec1bc9834','Δ 113'),
('db23d138-68eb-4025-b9b8-fbd58890de96','5d53821c-3f41-5c0c-a068-ee0425d7abf8','E 807'),
('ae52b4f1-3ce6-4b1c-b5ef-fe0f0a2c8e1f','194f4e6e-7c88-55f0-8aea-310225978d3e',None),
('3047456b-e996-43d1-b13d-8a0480161318','779ee0f0-3774-5a2e-924e-067d4f75a222',None),
('50ae1fff-6035-473b-816a-de3d8150295f','95b6583b-d8b8-57a6-b0f8-52181e4f6205','Δ 218'),
('96195943-ef4b-4ef1-8fb7-93e4d6a93a3a','70fb26b1-6087-5bea-91d5-da63112b45c4','Ρ 10'),
('1ae946d0-c79f-43c1-8341-1e682ee37866','a74cd962-729d-5f61-88ff-31b669d1ab39','Δ 244')]:hist(i,K,works[aid]['title'],acc,works[aid]['work_type'],existing_id=aid)

# The larger source PDF has captions separate from its original embedded images.
pdf=m.h.load(m.RUN/'saints-pdf.json');raw=__import__('pathlib').Path(pdf['path']).read_bytes();assert m.h.sha(raw)==pdf['sha256']
body=m.RUN/'captures/island-of-saints.body.gz';body.write_bytes(gzip.compress(raw));rc=dict(url=pdf['url'],status=200,sha256=pdf['sha256'],bytes=len(raw),body_path=str(body.relative_to(m.ROOT)),retrieved_at=m.h.now())
for aid,xref,fig in [('0aafe2e5-6f0a-567a-82a1-aa83b39dad03',1877,110),('a68fa84b-57d4-53a5-9979-a03f1a2865d6',1878,109)]:
    existing(works[aid],source_url=pdf['url'],source_record_id='figure-'+str(fig),source_receipt=rc,locator='Printed p. 65, fig. '+str(fig),pdf_path=pdf['path'],pdf_page_index=66,pdf_xref=xref,view_label='Complete embedded object photograph, figure '+str(fig),rights_label='Cyprus Tourism Organisation publication; no open reuse licence stated')
existing(works['5352164e-0b14-5d18-a0dc-57a0dade3ab3'],source_url=pdf['url'],source_record_id='figure-98',source_receipt=rc,locator='Printed p. 62, fig. 98: Smyrna 1801, 35.5 × 25.5 × 8.5 cm',pdf_path=pdf['path'],pdf_page_index=63,pdf_xref=1876,view_label='Complete supplied photograph of the open book-shaped reliquary',rights_label='Cyprus Tourism Organisation publication; no open reuse licence stated',identity_basis='Exact title, 1801 inscription/date, Smyrna origin and dimensions match the existing 1801 object. Not the separate unknown-date accession 5949.')
for slug,title,a,z,creator,xref,fig,view in [('cyprus-museum-of-byzantine-heritage-palaichori-village','Man of Sorrows — The King of Glory',1501,1600,'Philippou (source signature; identity unresolved)',1867,95,'Complete embedded object photograph'),('saint-john-lampadistis-museum','Saint John Lampadistis',1201,1300,None,1866,96,'Detail supplied by the source; not the complete icon')]:
    fact('saints:figure:'+str(fig),slug,title,a,z,'16th century'if a==1501 else'13th century','painting',precision='century',creator=creator,source_url=pdf['url'],source_record_id='figure-'+str(fig),source_receipt=rc,locator='Printed p. 61, fig. '+str(fig),pdf_path=pdf['path'],pdf_page_index=62,pdf_xref=xref,view_label=view,rights_label='Cyprus Tourism Organisation publication; no open reuse licence stated')
met=m.h.load(m.RUN/'met-pedoulas-illustration-pdf.json')
fact('met-faith-power:93','pedoulas-byzantine-museum','Virgin Kykkotissa',1501,1600,'16th century','painting',precision='century',creator='Loukas (signed; the historical painter, not the traditional Saint Luke attribution of the prototype)',medium='Tempera and gold leaf on wood support, primed with cloth, gesso and bole',dimensions='89.5 × 54.4 cm',source_url=met['receipt']['url'],source_record_id='Byzantium Faith and Power catalogue 93',source_receipt=met['receipt'],locator='Byzantium: Faith and Power (Metropolitan Museum of Art, 2004), catalogue 93, pp. 171–172',pdf_path=met['path'],pdf_page_index=0,pdf_xref=12,view_label='Complete supplied catalogue page 172; object 93 is the large icon at upper left. Adjacent text also describes a different artwork.',rights_label='Metropolitan Museum of Art catalogue, 2004; no open reuse licence stated for this reproduction',metadata_source=m.h.load(m.RUN/'met-pedoulas-pdf.json'),identity_basis='Catalogue 93 explicitly identifies the Pedoulas museum lender, signed Loukas, dimensions and date. Distinct from existing 13th-century Hodegetria and 14th-century Eleousa; not the miraculous Kykkos prototype. Historical holding, no fresh current display claim.')
for f in out:
    if 'historica.unibo.it'in f['source_url']:
        f['image_eligible']=False
        f['image_hold']='Original content endpoint returned HTTP 401. Metadata retained; no alternate content route attempted.'
m.h.save(m.RUN/'selection-wave2.json',dict(at=m.h.now(),records=out,held=[dict(reason='Kykkos Christ Saviour E 820 has a different date/version from existing 1641 Christ; not merged or added without reconciliation.'),dict(reason='Kykkos processional crosses Δ214/Δ205 differ in dating from existing 14th–15th-century cross; not substituted.')]))
print('TOTAL',len(out))
