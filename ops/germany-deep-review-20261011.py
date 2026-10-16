"""Field and object review. Draft parsers remain immutable source evidence."""
import runpy,re,json,collections,copy
b=runpy.run_path('ops/germany-deep-facts-20261011.py');m=b['m'];F=[];M={};D=[];H=[]
names=['staedel-reviewed','pinakothek','regional','barberini-reviewed','expanded','icons','final-sources']
for name in names:
    x=m.h.load(m.RUN/('selection-'+name+'.json'));F.extend(copy.deepcopy(x['records']));M.update({x['slug']:x for x in x['museums']});H.extend(dict(x,draft_selection=name)for x in x['held'])
# Recover six Wallraf entries whose main image captions omit "Inv." but include WRM.
v=runpy.run_path('ops/germany-deep-final-sources-20261011.py')
for h in H:
    if h.get('parser')=='wallraf':v['wallraf'](*h['args'])
F.extend(v['F'])
def amend(f,reason,**changes):
    before={k:f.get(k)for k in changes};f.update(changes);D.append(dict(key=f['key'],reason=reason,before=before,after=changes))
mainz={
'hieronymus-hack-schreibzeug-des-kurfuersten':('Hieronymus Hack','Schreibzeug des Kurfürsten Wolfgang von Dalberg'),
'lorenzo-di-credi-madonna-mit-dem-christuskind':('Lorenzo di Credi','Madonna mit dem Christuskind'),
'philipp-veit-selbstbildnis':('Philipp Veit','Selbstbildnis'),
'isaac-luttichuys-bildnis-einer-dame':('Isaac Luttichuys','Bildnis einer Dame'),
'wilhelm-lindenschmit-der-aeltere-der-kuenstler-mit-seiner-familie':('Wilhelm Lindenschmit der Ältere','Der Künstler mit seiner Familie'),
'nach-albrecht-duerer-adam-und-eva':('Unbekannter Meister nach Albrecht Dürer','Adam und Eva'),
'martin-caldenbach-gen-hess-mittelteil-und-rechter-fluegel-eines-klappaltars-dreikoenigsretabel':('Martin Caldenbach (gen. Hess)','Dreikönigsretabel – Mittelteil und rechter Flügel'),
'joseph-karl-stieler-bildnis-der-wiener-malerin-therese-wohlgemuth':('Joseph Karl Stieler','Bildnis der Wiener Malerin Therese Wohlgemuth'),
'wilhelm-lehmbruck-die-kniende':('Wilhelm Lehmbruck','Große Kniende'),
'max-slevogt-bal-pare':('Max Slevogt','Bal paré – Selbstbildnis mit Gattin'),
}
for f in F:
    f['creator']=' '.join(f['creator'].split());f['title']=' '.join(f['title'].split())
    dt=f['date_display'];mu=f['museum_slug']
    if mu=='de-staedel':
        upd=b['date'](dt);amend(f,'Parse the complete visible catalogue date; retain qualifiers and ranges.',**upd)
        if f['title']=='Eve':amend(f,'Date the physical bronze by the explicit casting range; preserve the 1881 model date separately.',start=1928,end=1942,precision='circa_range',model_date='1881',date_evidence_note='Model 1881; this cast circa 1928–1942, as stated by Städel.')
        if f['title']=='Orchestra Musicians':amend(f,'Preserve both stated phases; bounds cover 1872 and the 1874–1876 revisions.',start=1872,end=1876,precision='multiple_phases',date_evidence_note='Source: 1872 (1874–1876); no single creation year substituted.')
        if f.get('source_fields',{}).get('Object Type')=='textiles':f['work_type']='textile'
    if mu=='de-lenbachhaus'and f['creator']=='Paul Klee'and re.fullmatch(r'\d{4}, \d+',dt):
        year=int(dt[:4]);amend(f,'The value after the comma is Klee’s annual work number, not a second date.',start=year,end=year,precision='exact',date_evidence_note='Catalogue date and annual work number retained verbatim: '+dt)
    if 'Raffael' in f['creator']and dt=='1. Hälfte 16. Jhdt.':amend(f,'Explicit first-half-century date; copy attribution retained.',start=1501,end=1550,precision='half_century')
    if 'search.smb.museum'in f['source_url']:
        if 'Alte Nationalgalerie'in f['creator_credit']:
            amend(f,'Object image credit identifies Alte Nationalgalerie; related-object footer links do not identify this holding.',museum_slug='de-alte-nationalgalerie',holding_note='Staatliche Museen zu Berlin, Alte Nationalgalerie')
            M['de-alte-nationalgalerie']=dict(slug='de-alte-nationalgalerie',name='Alte Nationalgalerie',city='Berlin',state='Berlin',country_code='DE',website_url='https://www.smb.museum/museen-einrichtungen/alte-nationalgalerie/')
        if dt.startswith('Ausführung: '):amend(f,'The field prefix describes execution; it is not part of the date.',**b['date'](dt.removeprefix('Ausführung: ')),original_date_label=dt)
        creator=f['creator'].removeprefix('Ausführung: ');creator=re.sub(r'\s*\((?:um )?\d{4}(?:/\d{4})? - \d{4}\)\s*,?\s*Maler\*in','',creator)
        f['creator']=creator.strip()
    if mu=='de-landesmuseum-mainz':
        tail=f['source_url'].rstrip('/').rsplit('/',1)[-1]
        if tail in mainz:cr,title=mainz[tail]
        elif 'max-slevogt-bal'in tail:cr,title='Max Slevogt','Bal paré – Selbstbildnis mit Gattin'
        else:
            cr,title=f['creator'].split(', ',1)if', 'in f['creator']else(f['creator'],f['title'])
            if cr=='Ernst Ludwig Kircher':cr='Ernst Ludwig Kirchner'
        amend(f,'Separate artwork title and maker from the photographed-object caption; audio instructions are interface labels.',creator=cr,title=title)
        inv=f.get('accession','');inv=re.sub(r'^-?Nr\.\s*','',inv);inv=inv.replace('n. 414','414');inv=inv.split('  Dauerleihgabe')[0].strip();amend(f,'Normalize inventory label punctuation without changing the number.',accession=inv,source_record_id=inv)
        if title=='Vor der deutschen Kommandantur in Douai (19.10.1914)':f['work_type']='drawing_or_print';f['view_label']='Selected sheet from Slevogt’s war diary; complete source photograph retained'
        if 'Große Kniende'in title:f['image_hold_reason']='Physical casting year unresolved'
        if 'Dauerleihgabe'in f['original_caption']:f['holding_note']=f['original_caption']
    if mu=='de-wallraf-richartz':
        s,p=b['soup'](f['source_url']);ma=re.search(r'Inv\. Nr\.\s*([^\n]+)',p['text']);inv=ma[1]if ma else f['accession']
        if inv:amend(f,'Use full inventory including deposit prefix; punctuation is meaningful.',accession=inv,source_record_id=inv)
        if f['title']=='Triptychon mit Darstellung der Heilsgeschichte':amend(f,'Object image caption specifies circa 1340–1350; index says circa 1350. Keep both as evidence.',**b['date']('um 1340–1350'),date_evidence_note='Index: circa 1350; object caption: circa 1340–1350.')
        if f['title']=='Pfeifer und Trommler':amend(f,'Object caption and page specify circa 1503–1504; index extends to 1505.',**b['date']('um 1503–1504'),date_evidence_note='Index: circa 1503–1505; full object record: circa 1503–1504.')
        if f['title']=='Die Angorakatze':f['date_evidence_note']='Page text says circa 1783; image caption says circa 1783–1785. Joint authorship retained.'
        if f['title']=='Paulus Eremita':amend(f,'Full object metadata uses circa 1647.',**b['date']('um 1647'))
        f['holding_note']=f['original_caption']
    if mu=='de-ikonenmuseum-frankfurt':
        f['creator']='; '.join(dict.fromkeys(f['creator'].split('; ')))
        if f['accession']in['IM1047','IM546abc']:f['work_type']='liturgical_object'
    if f['creator']=='Fritzvon Uhde (?)':amend(f,'Restore the visible word boundary; attribution question mark retained.',creator='Fritz von Uhde (?)')
    # Date parsing may newly enable a picture; explicit version holds take precedence.
    f['image_eligible']=bool((f.get('image_url')or f.get('pdf_image'))and f['end']is not None and f['end']<=1955)
    if f.get('image_hold_reason')or(mu=='de-kunsthalle-bremen'and f['creator']=='Auguste Rodin')or(mu=='de-pinakothek-der-moderne'and f['title']=='Ascension'):f['image_eligible']=False
    f['status']='review';f['current_display']='Not asserted';f['holding_review']='Source-backed collection or stated loan; live production reconciliation pending'
# Identity keys prefer museum + inventory, else native object identity.
seen={};dedup=[]
for f in F:
    ident=(f['museum_slug'],f['accession'])if f.get('accession')else(f['museum_slug'],f['key'])
    if ident in seen:dedup.append(dict(kept=seen[ident]['key'],duplicate=f['key'],reason='Same museum and inventory/native identity'));continue
    seen[ident]=f
F=list(seen.values());assert len({f['key']for f in F})==len(F)
assert all(f['end']is None or f['end']<=1970 for f in F)
assert not any('Tippe auf'in f['title']for f in F)
M={k:v for k,v in M.items()if any(f['museum_slug']==k for f in F)}
m.h.save(m.RUN/'selection-reviewed.json',dict(at=m.h.now(),records=F,museums=list(M.values()),decisions=D,duplicates=dedup,draft_holds=H,scope='Selected source-backed artworks. Complete association directory is a discovery ledger, not complete German museum/artwork coverage.',production_state='No Germany production writes or uploads; Google Cloud reauthentication required; live duplicate and image preimage check still required.',local_database='Read-only reference audit; zero mutations'))
print('REVIEWED',len(F),'works',len(M),'museums',len({x['state']for x in M.values()}),'states','image eligible',sum(f['image_eligible']for f in F),'duplicate rows removed',len(dedup))
print(collections.Counter(f['museum_slug']for f in F))
