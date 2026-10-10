#!/usr/bin/env python3
"""Additional verified museum branches and rural collections; separate immutable wave."""
import argparse,importlib.util,os,shutil
from pathlib import Path
s=importlib.util.spec_from_file_location('institutions',Path(__file__).with_name('cyprus-island-institutions-20261007.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i)
PASS=os.environ.get('ARTLINE_CYPRUS_INSTITUTION_PASS','003');assert PASS in ['003','004']
ROOT=i.R;i.R=ROOT/'waves'/('cyprus-island-institutions-'+PASS+'-20261007');i.B=i.B/i.R.name;i.n.ROOT=i.R;i.n.BACKUP=i.B;i.h.RUN=i.R;i.h.BACKUP=i.B
ROWS=[
 ('hambis-platanisteia','Hambis Printmaking Museum, Platanisteia','Platanisteia','hambis-printmaking-museum-platanisteia'),
 ('musan','MUSAN — Museum of Underwater Sculpture Ayia Napa','Ayia Napa','musan-underwater-museum-ayia-napa'),
 ('art-nest','Art Nest — Philippos Yiapanis Sculpture Collection','Fasoula','art-nest-yiapanis-fasoula'),
 ('limassol-education','Elementary Education History Museum, Vasa Koilaniou','Vasa Koilaniou','elementary-education-museum-vasa'),
 ('limassol-zivania','Zivania Museum, Vasa Koilaniou','Vasa Koilaniou','zivania-museum-vasa'),
 ('limassol-kyperounta-folk','Museum of Rural and Traditional Life, Kyperounta','Kyperounta','kyperounta-rural-traditional-life-museum'),
 ('limassol-kyperounta-eoka','EOKA Struggle Museum, Kyperounta','Kyperounta','kyperounta-eoka-struggle-museum'),
 ('limassol-oleastro','Oleastro Olive Museum','Anogyra','oleastro-olive-museum-anogyra'),
 ('maa-palaeokastro','Maa–Palaeokastro Archaeological Site and Museum','Peyia','maa-palaeokastro-museum'),
 ('foini','Pilavakeion Folk Art Museum','Foini','pilavakeion-folk-art-museum-foini'),
]
OMODOS=[('Byzantine Art Museum','byzantine-art'),('Folkloric Art Museum','folkloric-art'),('Art Gallery','art-gallery'),('1955–1959 Struggle Museum','struggle'),('Lace Museum','lace'),('Photography Museum','photography')]
if PASS=='004':
    OMODOS=[]
    ROWS=[('limassol-tourism','Commandaria Museum, Silikou','Silikou','commandaria-museum-silikou'),('limassol-tourism','Laneia Museum','Laneia','laneia-museum'),('limassol-tourism','Commandaria Museum, Zoopigi','Zoopigi','commandaria-museum-zoopigi'),('minia-cyprus','Minia Cyprus Museum','Tatlısu','minia-cyprus-museum-tatlisu'),('pomos-reported','Natural History Museum of Pomos','Pomos','pomos-natural-history-museum')]
def prepare():
    rows=[]
    for source,name,place,slug in ROWS+ [('limassol-omodos',name+', Holy Cross Monastery, Omodos','Omodos','omodos-'+slug+'-museum')for name,slug in OMODOS]:
        p=i.h.load(ROOT/'pages'/(source+'.json'));sources=[i.proof(p,name)]
        if source=='art-nest':
            api=i.h.load(ROOT/'indexes/visitcyprus-museums.json');record=next(r for r in api['records']if r['id']==557945)
            sources.append(i.proof(dict(url=record['link'],receipt=api['receipt']),'Mikri Salamina Sculpture Park — Yiapanis Art Studio','557945'))
        notes=''
        if source=='hambis-platanisteia':notes='Separate Platanisteia branch; shared collection does not establish a branch-specific artwork holding.'
        if source=='musan':notes='Official museum source gives 93 sculptures and creation in 2021; these works fall outside the catalogue creation cutoff.'
        if source=='limassol-omodos':notes='One of six separately named collections in the Holy Cross Monastery; institutional evidence uses the written Omodos address, not inconsistent nearby-map markers.'
        if source=='pomos-reported':notes='Museum identity documented in a local newspaper report; municipal website returned a certificate-origin error. No current opening or operating-status assertion.'
        rows.append(dict(slug=slug,name=name,place=place,kind='historic_site'if source=='maa-palaeokastro'else'museum',existing_slug=None,sources=sources,notes=notes,region='Cyprus; locality documented in source text',address=None))
    i.h.save(i.R/'institution-registry.json',dict(at=i.h.now(),records=rows,held=[],minimum=500,upper_target=1000))
    shutil.copy2(ROOT/'production-backup.json',i.R/'production-backup.json');print('Prepared',len(rows),'additional institution identities',flush=True)
def verify():
    p=i.h.load(i.R/'institution-plan.json.gz');receipt=i.h.load(i.R/'institutions-applied.json')
    with i.d.connect()as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        rows={r['v']['id']:r['v']for r in db.execute('SELECT to_jsonb(i)v FROM institutions i WHERE id=ANY(%s::uuid[])',(receipt['institution_ids'],))};assert len(rows)==len(p['records'])
        for row in p['records']:assert all(rows[row['institution']['id']][k]==v for k,v in row['institution'].items()if k!='updated_at')
        citations=db.execute('SELECT count(*)n FROM citations WHERE source_id=%s',(i.n.uid('institutions-source'),)).fetchone()['n']
        # Source name is read from the committed source row to avoid a naming assumption.
        source=db.execute('SELECT id::text FROM sources WHERE slug=%s',(i.R.name+'-museum-identities',)).fetchone();assert source
        citations=db.execute('SELECT count(*)n FROM citations WHERE source_id=%s',(source['id'],)).fetchone()['n'];assert citations==sum(len(r['facts']['sources'])for r in p['records'])
    i.h.save(i.R/'institution-verification.json',dict(at=i.h.now(),verified=True,institutions=len(rows),citations=citations))
    print('VERIFIED',len(rows),'institutions;',citations,'source citations',flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','plan','apply','verify']);a=p.parse_args()
    globals()[a.phase]()if a.phase in ['prepare','verify']else getattr(i,a.phase)()
