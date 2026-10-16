import importlib.util
s=importlib.util.spec_from_file_location('b','ops/continuous-greek-batch-000286.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
rs=h.load(b.E/b.PHASE/'source-records.json.gz');fix={}
for r in rs:
 k='athens/'+r['source_id'];fix[k]={}
 if 'Koutlidis' in r['credit']:fix[k]['editorial_hold']='Koutlidis Foundation collection credit; ownership/custody must be reconciled separately. Not equated to National Gallery ownership.'
 if r['source_id']=='two-horses':fix[k]['editorial_hold']='Existing undated Rosa Bonheur horse compositions (Grazing Horses; Horses near the Seaside; Two Horses in a Stable; Two Horses for a Cart) lack identifying metadata. Hold this new accession until composition/version reconciliation; do not risk a duplicate.'
 if r['source_id']=='palette-and-fruit-bowl':fix[k].update(creator_link_hold=True,verified_artist_id=None,creator_identity_note='Two existing Francisco Bores artist UUIDs share source life dates1898–1972; original label preserved without forced link or a third artist.')
 if r['source_id']=='portrait-of-aimilia-salvagou':fix[k].update(verified_artist_id='db42e25e-4d28-4527-a3df-2ed140dde2c5',creator_identity_note='Unique existing Leon Bonnat aliases; museum birth1834 conflicts with current artist1833. Both labels preserved; no painter metadata update. Exact named sitter and1894 inventory distinct from existing artist works.')
h.save(b.E/b.PHASE/'source-field-corrections.json.gz',fix)
v=h.load(b.E/'global-artwork-version-reconciliation.json');assert not v['global_accession_matches'] and not v['native_matches'] and not v['source_citation_matches']
b.save('artwork-version-decisions.json',dict(at=h.now(),decision='Two exact museum inventories selected: Bonnat Π.4383 portrait of Aimilia Salvagou1894 and Bores Π.1340 Palette and Fruit Bowl1946. Global accession, native URL, source citations, exact titles, linked creator and unlinked-label works reviewed. No corresponding sitter/1946 composition exists in scoped candidates. Four Foundation records and Bonheur horse identity held separately.',creator_conflicts={'Bonnat':'Birth1834 in museum versus1833 in existing catalogue; retain source evidence without metadata rewrite','Bores':'Duplicate existing profiles; retain object-level label and leave artist connection unresolved'},selected_source_ids=['portrait-of-aimilia-salvagou','palette-and-fruit-bowl'],existing_compared=len(h.load(b.E/'other-identity-candidates-before.json.gz')['artworks']),no_current_display_assertion=True))
with h.connect() as db:
 inst=db.execute('SELECT slug,website_url FROM institutions WHERE id=%s',(b.MID,)).fetchone();h.museums=lambda:{b.MUSEUM:(inst['slug'],inst['website_url'])}
 h.plan(b.PHASE)
p,pin=h.pinned(b.PHASE);assert len(p['records'])==2 and len(p['held'])==5 and all(not x['before'] for x in p['records'])
assert next(r for r in p['records'] if r['source_id']=='palette-and-fruit-bowl')['artist_id'] is None
print('Frozen 2 objects,5 held; no new painters; immutable plan',pin)
