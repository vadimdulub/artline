"""Freeze 455 individual provisional reviews and 450 checked native pages."""
import gzip,hashlib,importlib.util,json,re
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup
def module(name,file):
    s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
i=module('identity','museum-expansion-france-fourteenth-identity-20261008.py');f=i.f;m=f.m;RUN=f.RUN
notes=module('notes','museum-expansion-france-fourteenth-notes-20261008.py')
COLLECTIONS={'M1102':'Maison de Balzac','M1108':'Palais Galliera, musée de la Mode de la Ville de Paris','M1113':'Musée de la Vie romantique'}
def main():
    dest=RUN/'review-progress-checkpoint-002.json';pack=RUN/'paris-object-context-checked-002.json.gz';snapshot=RUN/'working-notes-through-455-002.py';decisions=RUN/'provisional-decisions-002.json.gz'
    assert not any(p.exists() for p in [dest,pack,snapshot,decisions])
    assert set(notes.NOTES).isdisjoint(notes.HOLDS) and set(notes.NOTES)|set(notes.HOLDS)==set(range(1,456))
    prior=RUN/'review-progress-checkpoint-001.json';old=m.load(prior)
    for dep in old['references']:f.checked(dep)
    candidates=RUN/'native-candidates-001.json.gz';rows=m.load(candidates)['rows'];deps={candidates,Path(__file__).resolve()};receipts=[]
    for lo,hi in [(6,155),(156,305),(306,455)]:
        path=RUN/f'paris-object-context-{lo:03d}-{hi:03d}-complete.json';complete=m.load(path)
        assert complete['candidate_reference']==f.ref(candidates) and len(complete['receipts'])==150
        deps.update([path,f.checked(complete['capture_script'])]);receipts+=complete['receipts']
    assert len({v['path'] for v in receipts})==450
    contexts=[]
    for r in rows[5:455]:
        stem=RUN/'paris-object-context-001'/f"{r['number']:03d}-{r['source_id']}"
        rp=Path(str(stem)+'.receipt.json');hp=Path(str(stem)+'.html.gz');tp=Path(str(stem)+'.txt')
        x=m.load(rp);assert f.ref(rp) in receipts and x['status']==200 and x['source_id']==r['source_id'] and x['number']==r['number']
        assert x['url']==r['facts']['source_fields']['Lien_site_associe'].strip()
        assert urlparse(x['final_url']).hostname=='www.parismuseescollections.paris.fr'
        raw=gzip.decompress(hp.read_bytes());assert len(raw)==x['bytes'] and hashlib.sha256(raw).hexdigest()==x['sha256']
        soup=BeautifulSoup(raw,'html.parser')
        for tag in soup(['script','style','noscript']):tag.decompose()
        text=soup.get_text('\n',strip=True);assert text==tp.read_text() and text.count('\nInformations détaillées\n')==2
        detail=text.rsplit('\nInformations détaillées\n',1)[1].split('\nIndexation\n')[0]
        institution=COLLECTIONS[r['facts']['source_fields']['Code_Museofile']]
        assert 'Institution\n:\n'+institution+'\n' in detail
        inv=detail.split('\nNuméro d’inventaire\n:\n',1)[1].splitlines()[0];national=r['facts']['inventory'];basis='Exact spelling' if inv==national else 'Whitespace-only inventory formatting; both literal forms retained'
        if r['number']==395:
            assert (national,inv)==('CSR AG 028','CSR AG 28') and r['source_id']=='M1113280000714'
            basis='Explicitly reviewed zero-padding difference: same native URL, named collection, maker, title, support and 59×49.5 cm dimensions; retain both spellings without metadata overwrite.'
        else:assert re.sub(r'\s+','',inv)==re.sub(r'\s+','',national),(r['number'],national,inv)
        contexts.append(dict(number=r['number'],source_id=r['source_id'],source_url=x['url'],final_url=x['final_url'],literal_detail_text=detail,native_inventory=inv,national_inventory=national,inventory_comparison_basis=basis,receipt_reference=f.ref(rp),body_reference=f.ref(hp),text_reference=f.ref(tp)))
        deps.update([rp,hp,tp])
    initial=m.load(RUN/'initial-scope-001.json.gz')
    with m.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on'
        assert i.snapshot(db,initial['scoped_ids'])==initial['snapshot'],'Selected museum baseline changed; reconcile before writes'
        counts=i.counts(db);assert counts==initial['counts']
    m.save(pack,dict(at=m.now(),rows=contexts,dependencies=[f.ref(p) for p in sorted(deps)],policy='450 selected native object pages checked against byte hashes, regenerated text, exact source URLs, explicit holding collection and literal inventory comparison. No images or current-display claims.'))
    snapshot.write_bytes(Path(notes.__file__).read_bytes())
    out=[dict(number=r['number'],source_id=r['source_id'],institution_id=r['institution_id'],state='provisional_supported_pending_final_identity' if r['number'] in notes.NOTES else 'editorial_hold',basis=notes.NOTES.get(r['number'],notes.HOLDS.get(r['number'])),native_qualified_label=notes.NATIVE_QUALIFIED.get(r['number']),supplemental_terms=notes.SUPPLEMENTAL_TERMS.get(r['source_id'],[])) for r in rows[:455]]
    m.save(decisions,dict(at=m.now(),rows=out,notes_reference=f.ref(snapshot),candidate_reference=f.ref(candidates),context_reference=f.ref(pack),database_writes=0,policy='Provisional individual editorial review, not an approved write plan. Supplemental native URLs, maker aliases, shortened/translated titles, historic inventory and within-batch identity comparisons remain.'))
    references=[f.ref(p) for p in [pack,decisions,snapshot,prior,RUN/'native-identity-001.json.gz',RUN/'identity-citations-001.json.gz',RUN/'identity-recomputed-001.json',RUN/'physical-comparison-context-001.json.gz',RUN/'continuation-002.json',RUN/'initial-scope-001.json.gz',Path(__file__).resolve()]]
    by={code:dict(reviewed=sum(r['facts']['source_fields']['Code_Museofile']==code for r in rows[:455]),provisional_supported=sum(r['facts']['source_fields']['Code_Museofile']==code and r['number'] in notes.NOTES for r in rows[:455]),held=sum(r['facts']['source_fields']['Code_Museofile']==code and r['number'] in notes.HOLDS for r in rows[:455])) for code in ['M0184','M1102','M1108','M1113']}
    m.save(dest,dict(at=m.now(),state='progress_not_delivered',database_writes=0,reviewed_objects=455,provisional_supported=len(notes.NOTES),held=len(notes.HOLDS),remaining_individual_reviews=150,source_candidates=605,checked_native_object_pages=450,by_museum=by,protected_initial_records=322,initial_scope_unchanged=True,counts=counts,references=references,pending_work=['Review Hugo 456–605; retain failed candidate 583 native fetch as a hold unless independently resolved.','Recompute supplemental identity scope using native Paris URLs/redirects, maker variants, short/translated titles and historical inventory inscriptions; separately inspect within-batch duplicates.','Resolve or retain the identified physical impression, duplicate, attribution, date and bound-unit holds.','Use pinned native qualifier/role evidence in the final object-label derivations, preserving national export differences; no artist authority writes.','Construct and validate the final review-only plan; protect 9350 prior campaign records, 322 initial records, the wave-68 delivery and all frozen checkpoints.','Apply supported local additions atomically only after identity gates; exact readback and zero-write replay remain required.'],policy='Research checkpoint only. No catalogue, image, artist authority, publication or current-display writes. Whole sketchbooks, if finally supported, count once and never by their leaf count. Goal remains all museums.'))
    print(json.dumps(dict(checkpoint=f.ref(dest),reviewed=455,provisional_supported=len(notes.NOTES),held=len(notes.HOLDS),remaining=150,native_pages=450,baseline_records_unchanged=322,database_writes=0,by_museum=by)),flush=True)
if __name__=='__main__':main()
