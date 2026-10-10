"""Freeze all 605 provisional reviews; validate 149 new Hugo native captures."""
import gzip,hashlib,importlib.util,json,re
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup
def module(name,file):
    s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
i=module('identity','museum-expansion-france-fourteenth-identity-20261008.py');f=i.f;m=f.m;RUN=f.RUN
notes=module('notes','museum-expansion-france-fourteenth-notes-20261008.py')
def main():
    dest=RUN/'review-progress-checkpoint-003.json';pack=RUN/'paris-object-context-checked-003.json.gz';snapshot=RUN/'working-notes-through-605-003.py';decisions=RUN/'provisional-decisions-003.json.gz'
    assert not any(p.exists() for p in [dest,pack,snapshot,decisions])
    assert set(notes.NOTES).isdisjoint(notes.HOLDS) and set(notes.NOTES)|set(notes.HOLDS)==set(range(1,606))
    prior=RUN/'review-progress-checkpoint-002.json';old=m.load(prior)
    assert f.ref(prior)['sha256']=='25ac1fca6b15565bccfdd26c7b06dcd3039eb89240d27d6e4cf0cf12494b323d'
    for dep in old['references']:f.checked(dep)
    prevpack=RUN/'paris-object-context-checked-002.json.gz';prev=m.load(prevpack)
    for dep in prev['dependencies']:f.checked(dep)
    candidates=RUN/'native-candidates-001.json.gz';rows=m.load(candidates)['rows']
    contexts=list(prev['rows']);assert len(contexts)==450
    continuation=RUN/'hugo-partial-capture-continuation-001.json';cont=m.load(continuation)
    error=f.checked(cont['error_reference']);f.checked(cont['capture_script'])
    assert error.name=='583-M1114240011320.error.json' and 583 in notes.HOLDS
    assert not list((RUN/'paris-object-context-001').glob('583-*.receipt.json'))
    tail=RUN/'paris-object-context-584-605-complete.json';taildata=m.load(tail)
    assert len(taildata['receipts'])==22 and taildata['candidate_reference']==f.ref(candidates)
    deps={prior,prevpack,candidates,continuation,error,tail,f.checked(cont['capture_script']),f.checked(taildata['capture_script']),Path(__file__).resolve()}
    for r in rows[455:]:
        n=r['number']
        if n==583:continue
        stem=RUN/('paris-object-context-001' if n<583 else 'paris-object-context-002')/f"{n:03d}-{r['source_id']}"
        rp=Path(str(stem)+'.receipt.json');hp=Path(str(stem)+'.html.gz');tp=Path(str(stem)+'.txt')
        x=m.load(rp);assert x['status']==200 and x['source_id']==r['source_id'] and x['number']==n
        if n>=584:assert f.ref(rp) in taildata['receipts']
        assert x['url']==r['facts']['source_fields']['Lien_site_associe'].strip()
        assert urlparse(x['final_url']).hostname=='www.parismuseescollections.paris.fr'
        raw=gzip.decompress(hp.read_bytes());assert len(raw)==x['bytes'] and hashlib.sha256(raw).hexdigest()==x['sha256']
        soup=BeautifulSoup(raw,'html.parser')
        for tag in soup(['script','style','noscript']):tag.decompose()
        text=soup.get_text('\n',strip=True);assert text==tp.read_text() and text.count('\nInformations détaillées\n')==2
        detail=text.rsplit('\nInformations détaillées\n',1)[1].split('\nIndexation\n')[0]
        assert 'Institution\n:\nMaison de Victor Hugo - Hauteville House\n' in detail
        inv=detail.split('\nNuméro d’inventaire\n:\n',1)[1].splitlines()[0];national=r['facts']['inventory']
        assert re.sub(r'\s+','',inv)==re.sub(r'\s+','',national),(n,national,inv)
        contexts.append(dict(number=n,source_id=r['source_id'],source_url=x['url'],final_url=x['final_url'],literal_detail_text=detail,native_inventory=inv,national_inventory=national,inventory_comparison_basis='Exact spelling' if inv==national else 'Whitespace-only formatting; both literal forms retained',receipt_reference=f.ref(rp),body_reference=f.ref(hp),text_reference=f.ref(tp)))
        deps.update([rp,hp,tp])
    assert len(contexts)==599 and {v['number'] for v in contexts}==set(range(6,606))-{583}
    initial=m.load(RUN/'initial-scope-001.json.gz')
    with m.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on'
        assert i.snapshot(db,initial['scoped_ids'])==initial['snapshot'],'Selected museum baseline changed'
        counts=i.counts(db);assert counts==initial['counts']
    m.save(pack,dict(at=m.now(),rows=contexts,dependencies=[f.ref(p) for p in sorted(deps)],missing_native_pages=[dict(number=583,source_id=rows[582]['source_id'],error_reference=f.ref(error),state='held_no_native_response')],policy='599 selected native pages validated against raw byte hashes, regenerated text, literal requested URL, holding collection and inventory. Prior450 checked pages retained transitively;149 new Hugo pages verified. No claim of a complete456–605 capture; failed583 preserved.'))
    snapshot.write_bytes(Path(notes.__file__).read_bytes())
    out=[dict(number=r['number'],source_id=r['source_id'],institution_id=r['institution_id'],state='provisional_supported_pending_final_identity' if r['number'] in notes.NOTES else 'editorial_hold',basis=notes.NOTES.get(r['number'],notes.HOLDS.get(r['number'])),native_qualified_label=notes.NATIVE_QUALIFIED.get(r['number']),supplemental_terms=notes.SUPPLEMENTAL_TERMS.get(r['source_id'],[])) for r in rows]
    m.save(decisions,dict(at=m.now(),rows=out,notes_reference=f.ref(snapshot),candidate_reference=f.ref(candidates),context_reference=f.ref(pack),database_writes=0,policy='All605 individual preliminary reviews complete; supplemental identity and final review/write plan still required. These are not approved database additions.'))
    by={code:dict(reviewed=sum(r['facts']['source_fields']['Code_Museofile']==code for r in rows),provisional_supported=sum(r['facts']['source_fields']['Code_Museofile']==code and r['number'] in notes.NOTES for r in rows),held=sum(r['facts']['source_fields']['Code_Museofile']==code and r['number'] in notes.HOLDS for r in rows)) for code in ['M0184','M1102','M1108','M1113','M1114']}
    refs=[f.ref(p) for p in [pack,decisions,snapshot,prior,RUN/'native-identity-001.json.gz',RUN/'identity-citations-001.json.gz',RUN/'identity-recomputed-001.json',RUN/'physical-comparison-context-001.json.gz',RUN/'continuation-002.json',RUN/'initial-scope-001.json.gz',Path(__file__).resolve()]]
    m.save(dest,dict(at=m.now(),state='progress_not_delivered',database_writes=0,reviewed_objects=605,provisional_supported=len(notes.NOTES),held=len(notes.HOLDS),remaining_individual_reviews=0,source_candidates=605,checked_native_object_pages=599,failed_native_page=583,by_museum=by,protected_initial_records=322,initial_scope_unchanged=True,counts=counts,references=refs,pending_work=['Recompute supplemental identity using native URLs/redirects, maker aliases, short/translated titles, historic inventory inscriptions and within-batch physical groups.','Inspect new comparison leads, preserve unresolved holds, and verify all native role/qualification derivations.','Construct and validate final review-only plan, protecting9350 prior campaign records,322 initial records and frozen wave68/checkpoints.','Apply supported additions atomically only after identity gates; exact readback and zero-write replay required.'],policy='Research progress only. Whole bound volumes count once; constituent notebook pages remain held. No catalogue, image, authority, publication or current-display writes. Goal remains all museums.'))
    print(json.dumps(dict(checkpoint=f.ref(dest),reviewed=605,provisional_supported=len(notes.NOTES),held=len(notes.HOLDS),native_pages=599,baseline_records_unchanged=322,database_writes=0,by_museum=by)),flush=True)
if __name__=='__main__':main()
