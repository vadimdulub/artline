#!/usr/bin/env python3
"""Literal current Joconde facts, separating source fields from type derivation."""
import copy,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-france-tenth-native-v2-20261008.py'));n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
m=n.m;RUN=n.RUN;ref=n.ref;checked=n.checked;QUEUE=n.QUEUE;QUEUES=[RUN/'selected-metadata-queue-001.json',QUEUE]
def body(x):
    import gzip,hashlib
    raw=gzip.decompress((m.ROOT/x['body_path']).read_bytes());assert x['receipt']['status']==200 and hashlib.sha256(raw).hexdigest()==x['receipt']['sha256'];assert json.loads(raw)['data']==x['data'];return raw
def parse(item,path):
    x=m.load(path);body(x);d=next(r for r in x['data'] if r['Reference']==item['source_id']);assert x['queue_reference'] in [ref(q) for q in QUEUES] and item in m.load(checked(x['queue_reference']))['selected']
    old=item['raw_source_record'];flags=[]
    for k in ['Titre','Auteur','Numero_inventaire','Code_Museofile','Millesime_de_creation','Periode_de_creation','Denomination','Domaine','Localisation','Statut_juridique']:
        if m.norm(d.get(k))!=m.norm(old.get(k)):flags.append('source_changed_'+k)
    parsed,issue=n.screen(d);assert parsed is not None,(d['Reference'],issue)
    museum=item['museum'];assert d['Code_Museofile']==museum['slug'].removeprefix('joconde-').upper()
    context=m.load(checked(parsed['holding_context_reference']))['museums'][d['Code_Museofile']]
    assert context['institution_id']==museum['id'] and m.norm(d['Ville'])==m.norm(context['city']) and (not museum['city'] or m.norm(museum['city'])==m.norm(context['city']))
    assert m.norm(d['Nom_officiel_musee']) in [m.norm(v) for v in context['names']]
    v=parsed['facts'];first=v.get('first',v.get('year'));last=v.get('last',v.get('year'));precision=v.get('date_precision','exact');creator=v['creator_label'];text=m.norm(' '.join(d.get(k) or '' for k in ['Historique','Description','Commentaires','Genese','Titre','Denomination','Domaine','Precisions_sur_l_auteur']))
    if re.search(r'\b(?:depot|depose|disparu|vole|restitution|restitue|pret|prete|manquant)\b',text):flags.append('custody_narrative_review')
    if re.search(r'\b(?:album|suite|ensemble|serie|element|folio|page|fragment|recto|verso|epreuve|etat|tirage|posthume|copie|reproduction|fonte|moulage|modele|plaque|planche|edition|encadre)\b',text):flags.append('physical_version_or_unit_review')
    if re.search(r'attribu|ecole|atelier|d apres|imprimeur|editeur|lithographe|graveur',m.norm(creator)):flags.append('creator_roles_or_qualifications_preserved')
    if not creator or m.norm(creator) in ['anonyme','inconnu','manufacture indeterminee']:flags.append('unknown_personal_creator')
    if first is None:flags.append('unknown_lower_creation_bound')
    labels=[re.sub(r'\([^)]*\)','',v).strip() for v in (creator or '').split(';') if v.strip()];titles=[t.strip() for t in v['title'].split(';') if t.strip()]
    facts=dict(source_id=d['Reference'],native_object_id=d['Reference'],source_url=v['source_url'],native_page_urls=[v['source_url'],v['source_url'].replace('://pop.', '://www.pop.')],native_metadata_urls=[],wikidata_ids=[],title=v['title'],titles=sorted(set([v['title']]+titles)),creator_label=creator,detail_creator_label=creator,identity_creator_labels=labels,date_display=v['date_display'],first=first,last=last,date_precision=precision,date_issue=None,date_basis='Literal object creation date or explicit source century/subdivision; before endpoints stay exclusive and lower bounds unknown. Compound eligible periods use their full conservative extent, without choosing a narrower period. Parenthetical circa or circa-range wording remains literal, with bounds only from separately supplied eligible periods, never an invented tolerance.',inventory=v['accession'],medium=v['medium'],dimensions_text=v['dimensions'],work_type=v['work_type'],object_form=None,credit_line=d['Statut_juridique'],source_fields=d,holding_context_reference=parsed.get('holding_context_reference'),type_derivations=parsed['derivations'],source_parser=parsed['parser'],source_note='Full current national catalogue record and original response retained. Museum identity, holdings, creation, creator roles and physical unit require individual review. Ownership labels are source statements; no Artline legal-title, current-display or image-use claim.')
    return dict(provider='joconde',institution_id=museum['id'],museum= museum,number=item['number'],source_id=item['source_id'],facts=facts,index=item,source_reference=ref(path),retrieved_at=x['receipt']['retrieved_at'],state='source_candidate',review_flags=sorted(set(flags)))
def main():
    dest=RUN/'native-candidates-001.json.gz';assert not dest.exists();qs=[m.load(q) for q in QUEUES]
    for q in qs:checked(q['selector_reference'])
    assert all((RUN/('capture-complete-'+suffix+'.json')).exists() for suffix in ['001','002']);paths=sorted(RUN.glob('current-*/batch-*.json.gz'));by={}
    for p in paths:
        x=m.load(p);body(x)
        for d in x['data']:assert d['Reference'] not in by;by[d['Reference']]=p
    out=[];missing=[]
    for item in [item for q in qs for item in q['selected']]:
        if item['source_id'] not in by:missing.append(item);continue
        out.append(parse(item,by[item['source_id']]))
    m.save(dest,dict(at=m.now(),rows=out,not_returned=missing,queue_references=[ref(q) for q in QUEUES],parser_reference=ref(Path(__file__).resolve()),dependencies=[ref(Path(n.__file__).resolve()),ref(Path(m.__file__).resolve())]+[q['selector_reference'] for q in qs],partial=False));print(json.dumps(dict(rows=len(out),missing=len(missing),flags={k:sum(k in r['review_flags'] for r in out) for k in sorted({k for r in out for k in r['review_flags']})})),flush=True)
if __name__=='__main__':main()
