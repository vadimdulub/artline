"""Freeze the first 155 provisional reviews and checked native object evidence."""
import collections,gzip,hashlib,importlib.util,json,re
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup
def module(name,file):
    s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
i=module('identity','museum-expansion-france-fourteenth-identity-20261008.py');f=i.f;m=f.m;RUN=f.RUN
notes=module('notes','museum-expansion-france-fourteenth-notes-20261008.py')
def main():
    dest=RUN/'review-progress-checkpoint-001.json';pack=RUN/'paris-object-context-checked-001.json.gz';snapshot=RUN/'working-notes-through-155-001.py';decisions=RUN/'provisional-decisions-001.json.gz'
    assert not any(p.exists() for p in [dest,pack,snapshot,decisions])
    assert set(notes.NOTES).isdisjoint(notes.HOLDS) and set(notes.NOTES)|set(notes.HOLDS)==set(range(1,156))
    candidates=RUN/'native-candidates-001.json.gz';rows=m.load(candidates)['rows'];complete=RUN/'paris-object-context-006-155-complete.json';completed=m.load(complete)
    assert completed['candidate_reference']==f.ref(candidates);f.checked(completed['capture_script'])
    assert len(completed['receipts'])==150
    deps={candidates,complete,Path(__file__).resolve(),f.checked(completed['capture_script'])};contexts=[]
    for r in rows[5:155]:
        stem=RUN/'paris-object-context-001'/f"{r['number']:03d}-{r['source_id']}"
        rp=Path(str(stem)+'.receipt.json');hp=Path(str(stem)+'.html.gz');tp=Path(str(stem)+'.txt')
        x=m.load(rp);assert f.ref(rp) in completed['receipts'] and x['status']==200 and x['source_id']==r['source_id'] and x['number']==r['number']
        assert x['url']==r['facts']['source_fields']['Lien_site_associe'].strip()
        assert urlparse(x['final_url']).hostname=='www.parismuseescollections.paris.fr'
        raw=gzip.decompress(hp.read_bytes());assert len(raw)==x['bytes'] and hashlib.sha256(raw).hexdigest()==x['sha256']
        soup=BeautifulSoup(raw,'html.parser')
        for tag in soup(['script','style','noscript']):tag.decompose()
        text=soup.get_text('\n',strip=True);assert text==tp.read_text()
        assert text.count('\nInformations détaillées\n')==2
        detail=text.rsplit('\nInformations détaillées\n',1)[1].split('\nIndexation\n')[0]
        assert 'Institution\n:\nMaison de Balzac\n' in detail
        assert re.search(r'(?:^|\n)Numéro d’inventaire\n:\n'+re.escape(r['facts']['inventory'])+r'(?:\n|$)',detail),(r['number'],r['facts']['inventory'])
        contexts.append(dict(number=r['number'],source_id=r['source_id'],source_url=x['url'],final_url=x['final_url'],literal_detail_text=detail,receipt_reference=f.ref(rp),body_reference=f.ref(hp),text_reference=f.ref(tp)))
        deps.update([rp,hp,tp])
    m.save(pack,dict(at=m.now(),rows=contexts,dependencies=[f.ref(p) for p in sorted(deps)],policy='150 selected object pages, with byte hashes, regenerated text, exact source URLs, native inventory and named holding collection verified. No images fetched; no display claim.'))
    snapshot.write_bytes(Path(notes.__file__).read_bytes())
    out=[dict(number=r['number'],source_id=r['source_id'],institution_id=r['institution_id'],state='provisional_supported_pending_final_identity' if r['number'] in notes.NOTES else 'editorial_hold',basis=notes.NOTES.get(r['number'],notes.HOLDS.get(r['number'])),native_qualified_label=notes.NATIVE_QUALIFIED.get(r['number']),supplemental_terms=notes.SUPPLEMENTAL_TERMS.get(r['source_id'],[])) for r in rows[:155]]
    m.save(decisions,dict(at=m.now(),rows=out,notes_reference=f.ref(snapshot),candidate_reference=f.ref(candidates),context_reference=f.ref(pack),database_writes=0,policy='Working editorial decisions only; supplemental maker/native-URL/short-title and within-batch identity gates remain before any import plan.'))
    initial=m.load(RUN/'initial-scope-001.json.gz')
    with m.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on'
        assert i.snapshot(db,initial['scoped_ids'])==initial['snapshot'],'The selected museum baseline changed; preserve and reconcile instead of overwriting'
        counts=i.counts(db);assert counts==initial['counts']
    references=[f.ref(p) for p in [pack,decisions,snapshot,RUN/'native-identity-001.json.gz',RUN/'identity-citations-001.json.gz',RUN/'identity-recomputed-001.json',RUN/'physical-comparison-context-001.json.gz',RUN/'continuation-002.json',RUN/'initial-scope-001.json.gz',Path(__file__).resolve()]]
    m.save(dest,dict(at=m.now(),state='progress_not_delivered',database_writes=0,reviewed_objects=155,provisional_supported=len(notes.NOTES),held=len(notes.HOLDS),remaining_individual_reviews=450,source_candidates=605,checked_native_object_pages=150,identity_scope_artworks=55155,identity_citations=121316,protected_initial_records=322,initial_scope_unchanged=True,counts=counts,references=references,pending_work=['Review Galliera 156–305, Vie romantique 306–455, Hugo 456–605 using selected native object metadata.','Run supplemental creator aliases, inscription names, native Paris URLs and short-title searches; Bugeaud example shows whole-title fuzzy matching alone misses shortened captions.','Review within-batch repeats and constituent album/page relationships; provisional notes already hold the identified ambiguous duplicates.','Preserve native Attribué à for Hédouin 47/113 and copied-drawing qualification for 128 with pinned native text, while keeping literal export evidence.','Build and validate a final plan allowing blank/acquisition-only Paris credit fields without inventing ownership, preserving the joint Hugo collection limitation.','Only then apply supported local review additions atomically, verify exact readback and zero-write replay, preserve 9350 prior campaign records and frozen wave-68 delivery.'],policy='This is research progress, not delivered additions or goal completion. No source access hold bypass. No images, publication, artist authority or current-display writes.'))
    print(json.dumps(dict(checkpoint=f.ref(dest),reviewed=155,provisional_supported=len(notes.NOTES),held=len(notes.HOLDS),remaining=450,native_pages=150,baseline_records_unchanged=322,database_writes=0)),flush=True)
if __name__=='__main__':main()
