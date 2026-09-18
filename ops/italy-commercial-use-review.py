#!/usr/bin/env python3
"""Bounded follow-up to the user's confirmed public/potentially commercial use.

Preserves the four-hour completion snapshot. This preparation phase changes only
research files; exact guarded image withdrawal is a separate reviewed operation.
"""
import collections
import importlib.util
import json
from pathlib import Path
import subprocess
from urllib.parse import urlparse
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('capture', ROOT/'ops/italy-catalogue-pdf-evidence.py')
p = importlib.util.module_from_spec(spec); spec.loader.exec_module(p)
c = p.c
OUT = c.RUN/'commercial-use-review-20260917'
PRIVATE = c.BACKUP/'commercial-use-review-20260917'
LABEL = 'commercial-use-20260917'
HOLD_SLUGS = {'accademia-brera-collections','galleria-arte-moderna-milano',
    'musei-civici-monza','musei-civici-pavia','castello-sforzesco-art-collections'}
GUIDANCE = 'https://docs.italia.it/italia/icdp/icdp-pnd-circolazione-riuso-docs/it/v1.0-giugno-2022/acquisizione-circolazione-e-riuso-delle-riproduzioni-dei-beni-culturali-in-ambiente-digitale/tipologie-duso-delle-riproduzioni-di-beni-culturali.html'
DECREE = 'https://asmo.cultura.gov.it/fileadmin/risorse/normativa/DM_21_marzo_2024_rep._108-signed.pdf'
SOURCES = [
    ('national-guidance', GUIDANCE, '.html'),
    ('ministry-decree-2024', DECREE, '.pdf'),
    ('current-ministry-practice', 'https://asmo.cultura.gov.it/servizi-al-pubblico/pubblicazione-e-concessione-duso-di-immagini', '.html'),
    ('poldi-statute', 'https://museopoldipezzoli.it/wp-content/uploads/2024/01/Statuto_marzo_2018.pdf', '.pdf'),
    ('poldi-botticelli-ownership', 'https://www.lombardiabeniculturali.it/schede-complete/index.php?idk=RL480-00030&sezione=opere-arte', '.pdf'),
    ('cc-by-3', 'https://creativecommons.org/licenses/by/3.0/', '.html'),
    ('cc-by-4', 'https://creativecommons.org/licenses/by/4.0/', '.html'),
    ('cc-by-sa-4', 'https://creativecommons.org/licenses/by-sa/4.0/', '.html'),
]

def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    snapshots=[]
    for name in ['README.md','FINDINGS.md','REMAINING-GAPS.md','GALLERY.html',
                 'status.json','image-credit-ledger.json','held-artworks.json',
                 'gallery-verification.json','gallery-content-check.json']:
        source=c.RUN/name; dest=PRIVATE/'before'/name
        if not dest.exists(): c.save(dest,source.read_bytes())
        snapshots.append({'file':name,'private_backup':str(dest),'sha256':c.core.sha(dest.read_bytes())})
    if not (OUT/'before-snapshot.json').exists():c.save(OUT/'before-snapshot.json',snapshots)
    if not (OUT/'four-hour-completion.json').exists():
        c.save(OUT/'four-hour-completion.json',c.load(PRIVATE/'before/status.json'))
    use={'recorded_at':c.core.now(),'user_confirmation':'Public or potentially commercial app',
         'scope':'Italy image research; exact images selected in this campaign',
         'commercial_compatibility_required':True,
         'rules':['Review underlying artwork copyright and photograph licence separately.',
                  'Review custodian/owner cultural-property reuse requirements independently of CC labels.',
                  'NC, personal-study-only, permission-required or unresolved commercial reuse stays held.',
                  'Retain attribution, licence links, change notices and applicable ShareAlike obligations.',
                  'No museum correspondence, payment, new artwork import or publication authorized by this clarification.']}
    if not (OUT/'intended-use.json').exists():c.save(OUT/'intended-use.json',use)
    p.OUT=OUT/'sources'
    sources=[]
    for name,url,suffix in SOURCES:
        result=OUT/'sources'/(name+'.json')
        if result.exists():sources.append(c.load(result));continue
        p.HOST=urlparse(url).hostname
        path,receipt=p.capture(url,suffix,12000000)
        txt=path.with_suffix('.txt')
        if suffix=='.pdf':subprocess.run(['pdftotext','-layout',str(path),str(txt)],check=True)
        else:txt.write_text(BeautifulSoup(path.read_text(),'html.parser').get_text(' ',strip=True))
        row={'name':name,'capture':receipt,'text_path':str(txt.relative_to(ROOT)),
             'text_sha256':c.core.sha(txt.read_bytes())}
        c.save(result,row);sources.append(row)
        print('Captured',name,flush=True)
    ledger=c.load(PRIVATE/'before/image-credit-ledger.json')
    assert len(ledger)==59 and len({r['artwork_id'] for r in ledger})==59
    decisions=[];held=[];retained=[]
    for entry in ledger:
        im=c.load(c.RUN/entry['receipt']); raw=im['raw']
        text_path=raw.get('primary_catalogue_text_path')
        if entry['institution_slug']=='museo-poldi-pezzoli' and not text_path:
            text_path=next(s['text_path'] for s in sources if s['name']=='poldi-botticelli-ownership')
        ownership={}
        if text_path:
            text=Path(text_path).read_text();start=text.find('CONDIZIONE GIURIDICA E VINCOLI')
            if start<0:start=text.find('CONDIZIONE GIURIDICA')
            excerpt=text[start:start+900] if start>=0 else ''
            ownership={'text_path':text_path,'text_sha256':c.core.sha(Path(text_path).read_bytes()),'catalogue_section':excerpt}
        hold=entry['institution_slug'] in HOLD_SLUGS
        if hold:
            reason='Commercial cultural-property reuse permission unresolved for the public holding institution; file-level copyright terms remain preserved and are not declared invalid.'
            held.append(im)
        elif entry['institution_slug']=='museo-poldi-pezzoli':
            assert 'Indicazione generica: proprietà privata' in ownership.get('catalogue_section','')
            assert entry['rights_status'] in ('cc_by','cc_by_sa')
            assert any(s in entry['creator_credit'] for s in ['Own work','Self-photographed'])
            reason='Independently photographed CC BY/CC BY-SA image of a work identified by SIRBeC as privately owned. Museum supply-contract restrictions were reviewed and not extended to an independently licensed visitor photograph. No public-collection concession is asserted.'
            retained.append(entry)
        else:
            assert entry['institution_slug'] in ('the-met','wikimedia-museum-q414219')
            assert entry['rights_status'] in ('cc0','cc_by','public_domain')
            reason='Italian artist held abroad; exact museum image released under CC0 (Met) or CC BY 4.0 (Vienna), with original source and licence evidence preserved.'
            retained.append(entry)
        decisions.append({**entry,'intended_use':'Public or potentially commercial app',
            'commercial_review_decision':'hold' if hold else 'retain_with_licence_conditions',
            'reason':reason,'ownership_evidence':ownership,'source_receipt':entry['receipt']})
    assert len(held)==49 and len(retained)==10
    policy={'checked_at':c.core.now(),'institution_slug':'commercial-use-review-exact-campaign',
        'institution_slugs':sorted(HOLD_SLUGS),
        'affected_campaign_artworks':[r['artwork_id'] for r in held],
        'source_url':GUIDANCE,'additional_sources':[DECREE,'https://www.museicivicimonza.it/servizi/concessione-immagini/'],
        'decision':'Hold pending documented permission covering public and potentially commercial Artline reuse, or an applicable documented exception. Preserve artwork records, photographic copyright evidence and private image backups.',
        'rights_basis':'HOLD: user confirmed public/potentially commercial app use. Additional cultural-property reuse clearance is unresolved for the public collection; this is not a finding that the original photographic copyright licence is invalid.',
        'finding':'National guidance addresses paid commercial apps; DM108/2024 applies to Ministry institutions, not automatically to municipal or private museums. Artline has no commercial concession for these 49 selected images. Public status is not alone the reason for holding: the intended possible commercial reuse is unresolved. Ownership, custody and deposit distinctions are recorded per object.',
        'interpretation':'Operational clearance hold, not a categorical legal prohibition or a finding that every public app is commercial.',
        'intended_use_record':'commercial-use-review-20260917/intended-use.json',
        'object_decisions':'commercial-use-review-20260917/image-decisions.json',
        'captures':[r['capture'] for r in sources[:3]]}
    c.save(OUT/'image-decisions.json',decisions)
    c.save(OUT/'retained-images.json',retained)
    c.save(c.RUN/'institution-rights-holds'/(LABEL+'.json'),policy)
    c.save(c.RUN/(LABEL+'-rights-hold')/'affected-images.json',held)
    c.save(OUT/'prepared.json',{'checked_at':c.core.now(),'reviewed':59,'hold':49,'retain':10,
        'held_by_institution':dict(collections.Counter(i['institution_name'] for i in held)),
        'retained_by_institution':dict(collections.Counter(i['institution_name'] for i in retained)),
        'database_writes':False})
    print('Prepared exact image decisions: 49 holds, 10 retained. No database writes.',flush=True)

if __name__=='__main__':prepare()
