#!/usr/bin/env python3
"""Museum coverage campaign: read-only audit and bounded, source-pinned selection.

The collection target is a research objective, never evidence of eligibility.
No image downloads, publication, new institutions or fabricated artist profiles.
"""
import argparse
import collections
import csv
import gzip
import hashlib
import importlib.util
import json
import re
import time
import unicodedata
import uuid
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs

import psycopg
import requests
from bs4 import BeautifulSoup
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'docs/research/museum-expansion-20261006'
BACKUP = Path.home() / 'Library/Application Support/Artline/backups/museum-expansion-20261006'
ACTOR = 'local-european-research'
SNAPSHOT = ROOT / 'content/imports/joconde-20260910/joconde.csv'
SNAPSHOT_SHA = '499aab59e4c9fb4bea94ed7066d4dce1f51092c74d3c8a370b8fab53039767ef'


def now():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def norm(value):
    value = ''.join(c for c in unicodedata.normalize('NFKD', value or '').casefold() if not unicodedata.combining(c))
    return ' '.join(re.findall(r'[^\W_]+', value))


def acc(value):
    return {norm(x.split('(')[0]).replace(' ', '') for x in (value or '').split(';') if norm(x)}


def save(path, value):
    raw = json.dumps(value, ensure_ascii=False, indent=2, default=str).encode()
    if path.suffix == '.gz':
        raw = gzip.compress(raw, mtime=0)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == raw, 'Preserve existing evidence: ' + str(path)
    else:
        path.write_bytes(raw)


def load(path):
    return json.loads(gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_bytes())


def connect():
    return psycopg.connect('postgresql://localhost/artline', autocommit=True, row_factory=dict_row,
        options='-c timezone=UTC -c default_transaction_read_only=on -c statement_timeout=180000')


# Individually read museum descriptions. These are creation statements, not
# acquisition, depicted-event, restoration, publication or artist life dates.
ATHENS_DATES={
    '12':('Painting with the Last Judgment, September 15, 1855.',1855,1855,'exact','September 15, 1855','ΒΧΜ 22634'),
    '22':('Copper engraving coming from Moscow and dated in 1849.',1849,1849,'exact','1849','ΒΧΜ 18758'),
    '26':('Painted by Defterevon Sifnios. 1825.',1825,1825,'exact','1825','ΒΧΜ 01590'),
    '81':('Copper engraving, 1819.',1819,1819,'exact','1819','ΒΧΜ 18815'),
    '220':('Chronology:19th century',1801,1900,'century','19th century','ΒΧΜ 22608'),
}


def athens_fields(raw):
    soup=BeautifulSoup(raw,'html.parser')
    titles=[n.get_text(' ',strip=True) for n in soup.select('h2')]
    result={'headings':titles,'descriptions':[n.get_text(' ',strip=True) for n in soup.select('.description')]}
    labels=['Collection','Type','Origin','Creator','Measurement','Exhibit Number']
    for node in soup.select('li,p'):
        if node.select('li,p,ul,ol'):continue
        text=node.get_text(' ',strip=True)
        for label in labels:
            match=re.fullmatch(re.escape(label)+r'\s*:\s*(.+)',text)
            if match:
                assert label not in result,'Repeated object field'
                result[label]=match[1]
    return result


def athens_inventory(value):
    value=(value or '').upper().translate(str.maketrans('ΒΧΜ','BXM'))
    match=re.fullmatch(r'\s*BXM\s*0*(\d+)\s*',value)
    return str(int(match[1])) if match else None


def athens_facts(source_id,raw):
    f=athens_fields(raw);anchor,first,last,precision,literal,inventory=ATHENS_DATES[source_id]
    assert len(f['headings'])==1 and f['headings'][0]
    assert any(anchor in text for text in f['descriptions']),'Reviewed creation statement missing'
    assert f['Exhibit Number']==inventory
    assert f['Collection'] in ['Paintings','Manuscripts, Codices, Early Printed Books, Engravings and Drawings']
    kind={'PAINTING':'painting','ENGRAVING':'print'}[f['Type']]
    return dict(title=f['headings'][0],creator_label=f.get('Creator') or None,first=first,last=last,date_precision=precision,
        date_display=literal,work_type=kind,medium='Copper engraving' if kind=='print' else None,
        dimensions=f.get('Measurement') or None,accession=inventory,
        source_url='https://www.ebyzantinemuseum.gr/?i=bxm.en.exhibit&id='+source_id,
        cultural_context='Byzantine and Christian Museum: post-Byzantine painting and print collection',
        holding_basis='Official museum collection object with exact BXM inventory and collection category. Individually reviewed creation statement retained. Collection holding only; catalogue display labels are not a fresh display observation.')


def capture_athens():
    spec=importlib.util.spec_from_file_location('byzantine_capture',ROOT/'ops/byzantine-russian-expansion.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.RUN=RUN/'athens';capture=module.Capture()
    museum=next(r for r in load(RUN/'after-wave-03.json')['institutions'] if r['slug']=='byzantine-christian-museum-athens')
    with connect() as db:
        rows=db.execute('''WITH ids AS MATERIALIZED (
          SELECT id FROM artworks WHERE current_institution_id=%s UNION SELECT artwork_id FROM artwork_location_assertions
          WHERE institution_id=%s AND superseded_by IS NULL)
          SELECT a.id::text,a.accession_number FROM ids JOIN artworks a USING(id)''',(museum['id'],museum['id'])).fetchall()
        urls=[r['source_url'] for r in db.execute("SELECT DISTINCT source_url FROM citations WHERE entity_type='artwork' AND source_url LIKE '%%ebyzantinemuseum.gr/%%'")]
    known={parse_qs(urlparse(u).query).get('id',[''])[0] for u in urls}
    inventories={athens_inventory(r['accession_number']) for r in rows};ready=[];held=[]
    for oid in ATHENS_DATES:
        if oid in known or athens_inventory(ATHENS_DATES[oid][-1]) in inventories:
            held.append(dict(source_record_id=oid,reason='existing_catalogue_identity_or_inventory'));continue
        url='https://www.ebyzantinemuseum.gr/?i=bxm.en.exhibit&id='+oid
        raw,receipt=capture.get(url);facts=athens_facts(oid,raw)
        ready.append(dict(source_record_id=oid,museum=museum,facts=facts,source_receipt=receipt,body_path=receipt['path'],
            raw_source_record=dict(fields=athens_fields(raw),reviewed_creation_statement=ATHENS_DATES[oid][0])))
        print('Athens individually verified',oid,facts['title'],flush=True)
    assert ready
    path=RUN/'athens-current-plan.json.gz'
    save(path,dict(at=now(),records=ready,held=held,policy='Five individually read museum catalogue objects, checked against existing BXM inventories and source IDs. Missing creator and material stay null. No image requests or current-display claims.'))
    print(json.dumps(dict(source='athens',ready=len(ready),plan_sha256=hashlib.sha256(path.read_bytes()).hexdigest())),flush=True)


def capture_athens_followup():
    spec=importlib.util.spec_from_file_location('byzantine_capture',ROOT/'ops/byzantine-russian-expansion.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.RUN=RUN/'athens';capture=module.Capture();held=[]
    reasons={
        '165':'No creation date stated; the named creator is not a dating field.',
        '209':'1893 is the donation and 1923 the museum accession; neither is a creation date.',
        '25':'Named creator and inventory, but no creation date stated.',
        '80':'1800 dates the depicted saint’s martyrdom, not production of this chromolithograph.',
        '166':'19th-century wording describes the depicted monument; 1920 dates its destruction. Object creation needs separate evidence.',
        '186':'19th-century wording describes the depicted monument; 1920 dates its destruction. Object creation needs separate evidence.',
        '205':'18th-century wording concerns the history of the term anthibolon, not this drawing’s creation.',
    }
    for oid,reason in reasons.items():
        raw,receipt=capture.get('https://www.ebyzantinemuseum.gr/?i=bxm.en.exhibit&id='+oid)
        held.append(dict(source_record_id=oid,reason=reason,source_receipt=receipt,body_path=receipt['path'],fields=athens_fields(raw)))
        print('Athens date review retained',oid,flush=True)
    save(RUN/'athens-followup-holds.json',dict(at=now(),records=held,scope='Seven individually read official collection pages; no invented creation years. These pages alone do not meet the eligible-date addition policy.'))


def audit(label='baseline'):
    with connect() as db, db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
        rows = db.execute('''WITH counts AS MATERIALIZED (
          SELECT current_institution_id institution_id,count(*) works,
            count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible') eligible_works,
            count(primary_media_id) illustrated_works FROM artworks WHERE status<>'archived' GROUP BY 1
          ), pending AS MATERIALIZED (
          SELECT l.institution_id,count(DISTINCT l.artwork_id) pending_associations
          FROM artwork_location_assertions l JOIN artworks a ON a.id=l.artwork_id
          WHERE l.claim_type='holding' AND l.review_state='review' AND l.superseded_by IS NULL
          AND a.status<>'archived' AND a.current_institution_id IS DISTINCT FROM l.institution_id GROUP BY 1
          ) SELECT i.id::text,i.slug,i.name,i.kind,i.status,i.website_url,i.wikidata_id,
          i.canonical_institution_id::text, p.name city, c.name country,
          coalesce(n.works,0) works,coalesce(n.eligible_works,0) eligible_works,
          coalesce(n.illustrated_works,0) illustrated_works,coalesce(h.pending_associations,0) pending_associations
          FROM institutions i LEFT JOIN places p ON p.id=i.place_id LEFT JOIN countries c ON c.code=p.country_code
          LEFT JOIN counts n ON n.institution_id=i.id LEFT JOIN pending h ON h.institution_id=i.id
          ORDER BY i.id''').fetchall()
        stats = db.execute('SELECT status,count(*) artworks FROM artworks GROUP BY status ORDER BY status').fetchall()
    for r in rows:
        r['gap_100'] = max(0, 100-r['works'])
        r['gap_200'] = max(0, 200-r['works'])
        r['eligible_gap_100'] = max(0, 100-r['eligible_works'])
        r['eligible_gap_200'] = max(0, 200-r['eligible_works'])
        r['source_family'] = next((k for k in ['joconde','arco','wikimedia'] if r['slug'].startswith(k+'-')), 'museum_specific')
        r['priority_tradition'] = bool(re.search(r'byzant|russian|tretyakov|hermitage|benaki|icon|greek|kremlin', r['name'], re.I) or r['country'] in ['Greece','Russia','Cyprus'])
        r['campaign_state'] = 'alias' if r['canonical_institution_id'] else 'archived' if r['status']=='archived' else 'target_200_already_met' if r['eligible_works']>=200 else 'research_required'
    museums = [r for r in rows if r['kind']=='museum' and r['status']!='archived' and not r['canonical_institution_id']]
    summary = dict(at=now(),read_only=True,artworks=stats,institution_rows=len(rows),canonical_museums=len(museums),
        museums_below_100=sum(r['works']<100 for r in museums),museums_below_200=sum(r['works']<200 for r in museums),
        additions_to_100=sum(r['gap_100'] for r in museums),additions_to_200=sum(r['gap_200'] for r in museums),
        eligible_additions_to_100=sum(r['eligible_gap_100'] for r in museums),eligible_additions_to_200=sum(r['eligible_gap_200'] for r in museums),
        pending_associations=sum(r['pending_associations'] for r in museums),
        policy='Counts distinguish linked records, pre-1971 eligible dates, images, and unaccepted museum associations. No quota overrides evidence. Foundations and historic sites retained as separate rows.')
    save(RUN/(label+'.json'),dict(summary=summary,institutions=rows))
    with (RUN/(label+'.csv')).open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    print(json.dumps(summary),flush=True)


def joconde_object_kind(row,sculpture=False):
    form=norm(row.get('Denomination'));domain=norm(row.get('Domaine'))
    material=norm(row.get('Materiaux_techniques'))
    if sculpture:
        if domain!='sculpture' or form not in {'sculpture','statue','statuette','buste','figurine','relief','bas relief','haut relief'}:
            return None,'sculpture_form_or_domain_requires_review'
        identity=norm(' '.join(row.get(k) or '' for k in ['Titre','Historique','Description','Commentaires','Genese']))
        if row.get('Periode_de_l_original_copie') or re.search(r'\b(?:fragments?|elements?|partie|ensemble|moulages?|surmoulages?|tirages?|fontes?|copies?|reproductions?|originale?s?|modeles?|editions?|reductions?|repliques?|posthume)\b',identity):
            return None,'sculpture_component_or_version_requires_review'
        if re.search(r'\b(?:d apres|copie|reproduction)\b',norm(row.get('Auteur'))):return None,'sculpture_attribution_version_requires_review'
        if re.search(r'\b(?:pret|depot|depose|deposee|restitution|restitue|restituee|disparu|vole|manquant)\b',identity):return None,'sculpture_narrative_custody_requires_review'
        if re.search(r'collage|assemblage|decoup|neon',material):return None,'sculpture_mixed_media_requires_review'
        return 'sculpture',None
    kind={'tableau':'painting','peinture':'painting','dessin':'drawing','aquarelle':'watercolor','estampe':'print','gravure':'print'}.get(form)
    if not kind or re.search(r'collage|assemblage|relief|sculpture|decoup|neon',material):return None,'object_type_or_multiple_components_review'
    if kind=='painting' and 'peinture' not in domain:return None,'painting_domain_conflict'
    return kind,None


def joconde_facts(row,sculpture=False):
    row={k:(v if v is not None else '') for k,v in row.items()}
    if row.get('MANQUANT') or row.get('MANQUANT_COM'):
        return None, 'missing_or_stolen_review'
    if not row.get('Titre','').strip() or not row.get('Numero_inventaire','').strip():
        return None, 'missing_title_or_inventory'
    raw=row.get('Millesime_de_creation','').strip()
    if not re.fullmatch(r'\d{3,4}',raw):
        return None, 'creation_date_requires_individual_review'
    year=int(raw)
    if not 100<=year<=1970:
        return None, 'creation_date_outside_scope'
    period=row.get('Periode_de_creation','')
    centuries=[int(v) for v in re.findall(r'(\d{1,2})e\s+siècle',period)]
    if centuries and any(not (c-1)*100<year<=c*100 for c in centuries):
        return None,'source_date_conflict'
    if re.search(r'apr[eè]s|avant|vers|entre|\?|siècle|copie|reproduction',raw,re.I):
        return None,'creation_date_qualification'
    creator=row.get('Auteur','').strip()
    life=re.search(r'\((\d{4})-(\d{4})\)',creator)
    if life and not int(life[1])<=year<=int(life[2]):
        return None,'source_date_lifespan_conflict'
    kind,reason=joconde_object_kind(row,sculpture)
    if reason:return None,reason
    legal=norm(row.get('Statut_juridique'))
    location=[norm(v) for v in row.get('Localisation','').split(';') if v.strip()]
    expected=[norm(row.get('Ville')),norm(row.get('Nom_officiel_musee'))]
    clear_holding=(not row.get('Lieu_de_depot','').strip() and location==expected
        and legal.startswith(('propriete de la commune','propriete de l etat','propriete du departement','propriete de la region','propriete d une association'))
        and not re.search(r'pret|depot|restitu|recuperation|privee|particulier',legal))
    if not clear_holding:
        return None,'holding_custody_or_deposit_requires_review'
    return dict(title=row['Titre'].strip(),creator_label=creator or None,year=year,date_display=raw,
        work_type=kind,medium=row.get('Materiaux_techniques') or None,dimensions=row.get('Mesures') or None,
        accession=row['Numero_inventaire'].strip(),source_url='https://pop.culture.gouv.fr/notice/joconde/'+row['Reference'],
        holding_basis='Joconde current conservation museum and city exactly agree with museum identity; public/association ownership, no deposit or missing flag. Dated snapshot evidence only; no current display claim.'),None


def french_period(raw):
    """Map explicit catalogue century subdivisions to conservative intervals."""
    if not raw or re.search(r'[?;]|\b(?:vers|avant|après|peut-être)\b',raw,re.I):
        return None,None,'unknown'
    clean=norm(raw)
    m=re.fullmatch(r'(?:(1er|[1-4]e) quart |(1ere|2e) moitie )?(\d{1,2})e siecle',clean)
    if not m:return None,None,'unknown'
    century=int(m[3]);first,last=(century-1)*100+1,century*100
    precision='century'
    if m[1]:
        first+=(int(m[1][0])-1)*25;last=first+24;precision='range'
    elif m[2]:
        first+=(int(m[2][0])-1)*50;last=first+49;precision='range'
    if first<100 or last>1970:return None,None,'unknown'
    return first,last,precision


def joconde_period_facts(row,sculpture=False):
    # This wave is explicitly limited to records with no numeric millesime and
    # one unqualified catalogue period. Semicolons/uncertainty are not ranges.
    row={k:(v if v is not None else '') for k,v in row.items()}
    if row.get('Millesime_de_creation','').strip():return None,'numeric_date_for_separate_wave'
    first,last,precision=french_period(row.get('Periode_de_creation'))
    if first is None:return None,'creation_period_requires_individual_review'
    if row.get('MANQUANT') or row.get('MANQUANT_COM'):return None,'missing_or_stolen_review'
    if not row.get('Titre','').strip() or not row.get('Numero_inventaire','').strip():return None,'missing_title_or_inventory'
    creator=row.get('Auteur','').strip()
    life=re.search(r'\((\d{4})-(\d{4})\)',creator)
    if life and (int(life[1])>last or int(life[2])<first):return None,'source_period_lifespan_conflict'
    kind,reason=joconde_object_kind(row,sculpture)
    if reason:return None,reason
    legal=norm(row.get('Statut_juridique'))
    location=[norm(v) for v in row.get('Localisation','').split(';') if v.strip()]
    expected=[norm(row.get('Ville')),norm(row.get('Nom_officiel_musee'))]
    if row.get('Lieu_de_depot','').strip() or location!=expected or not legal.startswith(('propriete de la commune','propriete de l etat','propriete du departement','propriete de la region','propriete d une association')) or re.search(r'pret|depot|restitu|recuperation|privee|particulier',legal):
        return None,'holding_custody_or_deposit_requires_review'
    return dict(title=row['Titre'].strip(),creator_label=creator or None,first=first,last=last,date_precision=precision,
        date_display=row['Periode_de_creation'],work_type=kind,medium=row.get('Materiaux_techniques') or None,
        dimensions=row.get('Mesures') or None,accession=row['Numero_inventaire'].strip(),
        source_url='https://pop.culture.gouv.fr/notice/joconde/'+row['Reference'],
        holding_basis='Current Joconde conservation museum/city exactly agree; ownership unqualified and no deposit/missing flag. Original century/quarter/half-century retained as a range, without a fabricated single year. Holding only, no current display claim.'),None


def joconde_parser(source):
    parsers={'joconde':joconde_facts,'joconde-periods':joconde_period_facts,
             'joconde-ranges':joconde_range_facts,'joconde-circa':joconde_circa_facts,
             'joconde-before':joconde_before_facts,'joconde-sculpture':joconde_sculpture_facts,
             'joconde-sculpture-reviewed':joconde_sculpture_facts}
    return parsers[source]


def joconde_interval_object(row,first,last,precision,sculpture=False):
    """Object and custody checks for separately reviewed creation statements."""
    row={k:(v if v is not None else '') for k,v in row.items()}
    if row.get('MANQUANT') or row.get('MANQUANT_COM'):return None,'missing_or_stolen_review'
    if not row.get('Titre','').strip() or not row.get('Numero_inventaire','').strip():return None,'missing_title_or_inventory'
    creator=row.get('Auteur','').strip()
    life=re.search(r'\((\d{4})-(\d{4})\)',creator)
    if life and (int(life[1])>last or (precision=='before' and int(life[1])>=last) or (first is not None and int(life[2])<first)):return None,'source_interval_lifespan_conflict'
    kind,reason=joconde_object_kind(row,sculpture)
    if reason:return None,reason
    legal=norm(row.get('Statut_juridique'))
    location=[norm(v) for v in row.get('Localisation','').split(';') if v.strip()]
    expected=[norm(row.get('Ville')),norm(row.get('Nom_officiel_musee'))]
    if row.get('Lieu_de_depot','').strip() or location!=expected or not legal.startswith(('propriete de la commune','propriete de l etat','propriete du departement','propriete de la region','propriete d une association')) or re.search(r'pret|depot|restitu|recuperation|privee|particulier',legal):
        return None,'holding_custody_or_deposit_requires_review'
    return dict(title=row['Titre'].strip(),creator_label=creator or None,first=first,last=last,date_precision=precision,
        date_display=row['Millesime_de_creation'].strip(),work_type=kind,medium=row.get('Materiaux_techniques') or None,
        dimensions=row.get('Mesures') or None,accession=row['Numero_inventaire'].strip(),
        source_url='https://pop.culture.gouv.fr/notice/joconde/'+row['Reference'],
        holding_basis='Joconde conservation museum and city agree exactly, public/association ownership and no deposit or missing flag. Literal creation wording and its source period retained in evidence. Holding only, no current-display claim.'),None


def joconde_range_facts(row,sculpture=False):
    raw=(row.get('Millesime_de_creation') or '').strip()
    match=re.fullmatch(r'(\d{3,4})\s*[-–]\s*(\d{3,4})',raw)
    if not match:return None,'not_a_single_explicit_creation_range'
    first,last=map(int,match.groups())
    if not 100<=first<=last<=1970:return None,'creation_range_outside_scope_or_reversed'
    period=row.get('Periode_de_creation') or ''
    # The numeric source range remains authoritative; a contradictory source
    # century is held. Multiple period statements require individual review.
    if ';' in period or re.search(r'[?]|avant|après|vers',period,re.I):return None,'qualified_or_multiple_source_periods_review'
    centuries={int(v) for v in re.findall(r'(\d{1,2})e\s+siècle',period)}
    if centuries and (len(centuries)!=1 or not (min(centuries)-1)*100<first<=last<=max(centuries)*100):return None,'source_range_century_conflict'
    return joconde_interval_object(row,first,last,'exact' if first==last else 'range',sculpture)


def joconde_circa_facts(row,sculpture=False):
    raw=(row.get('Millesime_de_creation') or '').strip()
    match=re.fullmatch(r'(?:vers\s+(\d{3,4})|(\d{3,4})\s+vers)',raw,re.I)
    if not match:return None,'not_a_single_source_circa_year'
    year=int(match[1] or match[2]);first,last,_=french_period(row.get('Periode_de_creation'))
    # Never invent +/- years around a circa date. The separate, unqualified
    # publisher period must supply finite bounds entirely before 1971.
    if first is None or not first<=year<=last:return None,'circa_year_without_consistent_eligible_source_period'
    life=re.search(r'\((\d{4})-(\d{4})\)',row.get('Auteur') or '')
    if life and not int(life[1])<=year<=int(life[2]):return None,'source_circa_lifespan_conflict'
    facts,reason=joconde_interval_object(row,first,last,'circa_range',sculpture)
    if facts:facts['holding_basis']+=' Creation bounds come from the publisher’s explicit period, not an invented tolerance around its circa year.'
    return facts,reason


def joconde_before_facts(row,sculpture=False):
    raw=(row.get('Millesime_de_creation') or '').strip()
    match=re.fullmatch(r'(?:avant\s+(\d{3,4})|(\d{3,4})\s+avant)',raw,re.I)
    if not match:return None,'not_a_single_explicit_before_year'
    upper=int(match[1] or match[2])
    if not 100<upper<=1971:return None,'before_date_does_not_establish_cutoff'
    period=row.get('Periode_de_creation') or ''
    if period:
        # A separately stated period may expose a contradiction, but it does
        # not justify inventing a lower endpoint for this before-only date.
        p=re.fullmatch(r'(?:(1er|[1-4]e) quart |(1ere|2e) moitie )?(\d{1,2})e siecle',norm(period))
        if not p:return None,'qualified_or_multiple_source_periods_review'
        earliest=(int(p[3])-1)*100+1
        if p[1]:earliest+=(int(p[1][0])-1)*25
        elif p[2]:earliest+=(int(p[2][0])-1)*50
        if earliest>=upper:return None,'source_before_period_conflict'
    f,reason=joconde_interval_object(row,None,upper,'before',sculpture)
    if f:f['holding_basis']+=' The explicit before year is retained as an exclusive upper bound, with an unknown lower bound. No creation year is inferred from accession, acquisition or creator lifespan.'
    return f,reason


def joconde_sculpture_facts(row):
    kind,reason=joconde_object_kind(row,True)
    if reason:return None,reason
    raw=(row.get('Millesime_de_creation') or '').strip()
    if not raw:return joconde_period_facts(row,True)
    if re.fullmatch(r'\d{3,4}',raw):return joconde_facts(row,True)
    if re.fullmatch(r'\d{3,4}\s*[-–]\s*\d{3,4}',raw):return joconde_range_facts(row,True)
    if re.fullmatch(r'(?:vers\s+\d{3,4}|\d{3,4}\s+vers)',raw,re.I):return joconde_circa_facts(row,True)
    if re.fullmatch(r'(?:avant\s+\d{3,4}|\d{3,4}\s+avant)',raw,re.I):return joconde_before_facts(row,True)
    return None,'sculpture_creation_or_cast_date_requires_review'


def select_joconde(source='joconde',label='baseline'):
    assert not (RUN/(source+'-selection.json.gz')).exists(), 'Selection already pinned'
    baseline=load(RUN/(label+'.json'))['institutions']
    targets={r['slug'].removeprefix('joconde-').upper():r for r in baseline if r['slug'].startswith('joconde-') and not r['canonical_institution_id'] and r['status']!='archived' and r['eligible_works']<200}
    with SNAPSHOT.open('rb') as f:
        assert hashlib.file_digest(f,'sha256').hexdigest()==SNAPSHOT_SHA
    with connect() as db:
        known_refs={r['external_id'] for r in db.execute("SELECT external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme ILIKE '%joconde%'")}
        for row in db.execute("SELECT DISTINCT source_url FROM citations WHERE entity_type='artwork' AND source_url LIKE '%/joconde/%'"):
            known_refs.add(row['source_url'].rstrip('/').rsplit('/',1)[-1])
        existing=db.execute('''SELECT DISTINCT a.id::text,a.title,a.alternate_title,a.accession_number,
           coalesce(a.current_institution_id,l.institution_id)::text institution_id
           FROM artworks a LEFT JOIN artwork_location_assertions l ON l.artwork_id=a.id
           AND l.institution_id=ANY(%s::uuid[]) AND l.superseded_by IS NULL
           WHERE a.current_institution_id=ANY(%s::uuid[]) OR l.institution_id IS NOT NULL''',([r['id'] for r in targets.values()],)*2).fetchall()
        all_titles={norm(r['title']) for r in db.execute('SELECT title FROM artworks')}
    existing_acc=collections.defaultdict(set)
    existing_titles=collections.defaultdict(set)
    for r in existing:
        existing_acc[r['institution_id']].update(acc(r['accession_number']))
        existing_titles[r['institution_id']].update([norm(r['title']),norm(r['alternate_title'])])
    stats=collections.defaultdict(collections.Counter)
    candidates=collections.defaultdict(list)
    source_acc=collections.Counter()
    csv.field_size_limit(8_000_000)
    with SNAPSHOT.open(encoding='utf-8-sig',newline='') as f:
        for n,row in enumerate(csv.DictReader(f,delimiter='|'),1):
            code=row.get('Code_Museofile')
            if code not in targets:continue
            stats[code]['source_rows']+=1
            for a in acc(row.get('Numero_inventaire')):source_acc[(code,a)]+=1
            if row['Reference'] in known_refs:
                stats[code]['already_catalogued_source_identity']+=1;continue
            facts,reason=joconde_parser(source)(row)
            if reason:stats[code][reason]+=1;continue
            target=targets[code]
            if acc(facts['accession']) & existing_acc[target['id']]:
                stats[code]['existing_inventory_requires_review']+=1;continue
            if norm(facts['title']) in all_titles or norm(facts['title']) in existing_titles[target['id']]:
                stats[code]['existing_title_requires_review']+=1;continue
            candidates[code].append(dict(source_record_id=row['Reference'],museum=target,facts=facts,raw_source_record=row))
    selected=[];reviews=[]
    for code,target in sorted(targets.items()):
        chosen=[];titles=set()
        for row in sorted(candidates[code],key=lambda r:(r['facts']['work_type']!='painting',r['source_record_id'])):
            if any(source_acc[(code,a)]>1 for a in acc(row['facts']['accession'])):
                stats[code]['shared_source_inventory_requires_review']+=1;continue
            if norm(row['facts']['title']) in titles:
                stats[code]['same_selected_title_requires_review']+=1;continue
            if len(chosen)>=target['eligible_gap_200']:
                stats[code]['beyond_bounded_target']+=1;continue
            titles.add(norm(row['facts']['title']));chosen.append(row)
        selected.extend(chosen)
        reviews.append(dict(code=code,slug=target['slug'],name=target['name'],linked_before=target['works'],eligible_before=target['eligible_works'],selected=len(chosen),eligible_projected=target['eligible_works']+len(chosen),counts=dict(stats[code])))
    receipt=load(SNAPSHOT.with_suffix('.csv.snapshot.json'))
    save(RUN/(source+'-selection.json.gz'),dict(at=now(),snapshot=receipt,source_path=str(SNAPSHOT.relative_to(ROOT)),records=selected,museum_reviews=reviews))
    save(RUN/(source+'-selection-summary.json'),dict(at=now(),museums_reviewed=len(reviews),museums_with_new_candidates=sum(r['selected']>0 for r in reviews),selected=len(selected),museums_reaching_100=sum(r['eligible_before']<100<=r['eligible_projected'] for r in reviews),museums_reaching_200=sum(r['eligible_before']<200<=r['eligible_projected'] for r in reviews),reviews=reviews))
    print(json.dumps(dict(selected=len(selected),museums_reviewed=len(reviews),museums_with_candidates=sum(r['selected']>0 for r in reviews),reaching100=sum(r['eligible_before']<100<=r['eligible_projected'] for r in reviews),reaching200=sum(r['eligible_before']<200<=r['eligible_projected'] for r in reviews))),flush=True)


def capture_joconde(source='joconde'):
    selection=load(RUN/(source+'-selection.json.gz'))
    records={r['source_record_id']:r for r in selection['records']}
    refs=sorted(records)
    url='https://tabular-api.data.gouv.fr/api/resources/7e3307c2-f2ff-455c-bbca-bb6f11aec7bb/data/'
    for start in range(0,len(refs),50):
        dest=RUN/(source+'-current')/f'{start:05d}.json.gz'
        if dest.exists():continue
        group=refs[start:start+50]
        resp=requests.get(url,params={'Reference__in':','.join(group),'page_size':50},
            headers={'User-Agent':'ArtlineMuseumResearch/1.0 (bounded selected museum metadata)'},timeout=(15,60))
        raw=resp.content
        receipt=dict(url=resp.url,status=resp.status_code,retrieved_at=now(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
        save(RUN/(source+'-current')/f'{start:05d}.receipt.json',receipt)
        body=RUN/(source+'-current')/f'{start:05d}.body.gz'
        body.write_bytes(gzip.compress(raw,mtime=0))
        resp.raise_for_status();data=resp.json()
        assert data['meta']['total']<=50 and not data['links'].get('next'), 'Unbounded source response'
        assert len({r['Reference'] for r in data['data']})==len(data['data'])
        assert all(r['Reference'] in group for r in data['data'])
        save(dest,dict(requested=group,receipt=receipt,body_path=str(body.relative_to(ROOT)),data=data['data']))
        print('Fresh primary object records',min(start+50,len(refs)),'/',len(refs),flush=True)
        time.sleep(1)
    current={}
    for path in sorted((RUN/(source+'-current')).glob('[0-9]*.json.gz')):
        batch=load(path)
        for row in batch['data']:current[row['Reference']]=(row,batch['receipt'],batch['body_path'])
    ready=[];held=[]
    for ref,item in records.items():
        if ref not in current:
            held.append(dict(ref=ref,reason='not_returned_by_current_primary_source'));continue
        row,receipt,body=current[ref]
        facts,reason=joconde_parser(source)(row)
        old=item['raw_source_record']
        if not reason and any(norm(row.get(k))!=norm(old.get(k)) for k in ['Titre','Auteur','Numero_inventaire','Code_Museofile','Millesime_de_creation','Periode_de_creation']):
            reason='identity_or_date_changed_since_discovery'
        if not reason and norm(row['Nom_officiel_musee']+' '+row['Ville'])!=norm(item['museum']['name']):
            reason='museum_registered_name_requires_alias_review'
        if reason:
            held.append(dict(ref=ref,reason=reason));continue
        ready.append(dict(source_record_id=ref,museum=item['museum'],facts=facts,raw_source_record=row,source_receipt=receipt,body_path=body))
    plan=dict(at=now(),records=ready,held=held,policy='Fresh official object metadata checked against pinned discovery identity. Review artworks; accepted documented holdings only. No publication, current display, photographs or creator biographies.')
    save(RUN/(source+'-current-plan.json.gz'),plan)
    print(json.dumps(dict(ready=len(ready),held=len(held),museums=len({r['museum']['id'] for r in ready}))),flush=True)


def icon_date(raw):
    """Only standalone creation fields; ambiguous/multiphase dates stay held."""
    clean=(raw or '').strip().replace('–','-').replace('—','-')
    m=re.fullmatch(r'(?:(c\.|ca\.|circa|about)\s*)?(\d{3,4})(?:\s*-\s*(\d{3,4}))?',clean,re.I)
    if m:
        first,last=int(m[2]),int(m[3] or m[2])
        return (first,last,('circa_range' if m[1] else 'range') if first!=last else ('circa' if m[1] else 'exact')) if first<=last<=1970 else (None,None,'unknown')
    m=re.fullmatch(r'(?:(early|mid|late|first half|second half)\s+)?(\d{1,2})(?:st|nd|rd|th)\s+century',clean,re.I)
    if m:
        century=int(m[2]);first,last=(century-1)*100+1,century*100
        if m[1] and m[1].lower()=='first half':last=first+49
        elif m[1] and m[1].lower()=='second half':first+=50
        # Early/mid/late remain within the full source century; no invented subrange.
        return (first,last,'century' if last-first==99 else 'range') if 1<=century and last<=1970 else (None,None,'unknown')
    return None,None,'unknown'


def capture_icons():
    spec=importlib.util.spec_from_file_location('previous_icons',ROOT/'ops/byzantine-russian-more.py')
    previous=importlib.util.module_from_spec(spec);spec.loader.exec_module(previous)
    previous.m.RUN=RUN/'priority-icons'
    cap=previous.m.Capture()
    museum=next(r for r in load(RUN/'baseline.json')['institutions'] if r['slug']=='icon-museum-and-study-center')
    with connect() as db:
        known_urls={r['canonical_url'].rstrip('/') for r in db.execute("SELECT canonical_url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url LIKE 'https://www.iconmuseum.org/collection/%'")}
        known_urls.update(r['source_url'].rstrip('/') for r in db.execute("SELECT source_url FROM citations WHERE entity_type='artwork' AND source_url LIKE 'https://www.iconmuseum.org/collection/%'"))
        existing_acc=set().union(*(acc(r['accession_number']) for r in db.execute('''SELECT a.accession_number FROM artworks a WHERE a.current_institution_id=%s OR EXISTS(SELECT 1 FROM artwork_location_assertions l WHERE l.artwork_id=a.id AND l.institution_id=%s AND l.superseded_by IS NULL)''',(museum['id'],museum['id']))))
    selected=[];held=[];inspected=0;seen=set();listings=[]
    for country,start,end in [('greece',6,10),('russia',17,30)]:
        for page in range(start,end+1):
            if len(selected)>=museum['eligible_gap_200'] or inspected>=100:break
            url=f'https://www.iconmuseum.org/country/{country}/page/{page}/'
            try:raw,receipt=cap.get(url)
            except Exception as e:
                held.append(dict(url=url,reason=str(e)[:300]));break
            soup=BeautifulSoup(raw,'html.parser')
            urls=sorted({urljoin(url,a['href']) for a in soup.select('a[href]') if re.search(r'/collection/[^/]+/$',a['href'])})
            listings.append(dict(url=url,receipt=receipt,object_links=urls))
            for obj_url in urls:
                if obj_url.rstrip('/') in known_urls or obj_url in seen:continue
                if len(selected)>=museum['eligible_gap_200'] or inspected>=100:break
                seen.add(obj_url);inspected+=1
                try:
                    body,rc=cap.get(obj_url);fields=previous.icon_museum_fields(body)
                    reason=None
                    if not fields.get('Title') or not fields.get('Inventory Number'):reason='missing_title_or_inventory'
                    elif acc(fields['Inventory Number']) & existing_acc:reason='existing_inventory'
                    elif re.search(r'\bloan\b',fields.get('Credit Line',''),re.I) or fields['Inventory Number'].startswith('L'):reason='loan_requires_custody_review'
                    elif not re.search(r'tempera|oil|paint|encaustic',fields.get('Medium',''),re.I):reason='medium_requires_icon_classification_review'
                    first,last,precision=icon_date(fields.get('Object Date'))
                    if first is None:reason=reason or 'creation_date_requires_review'
                    if reason:
                        held.append(dict(url=obj_url,reason=reason,fields=fields,source_receipt=rc));continue
                    existing_acc.update(acc(fields['Inventory Number']))
                    selected.append(dict(source_record_id=urlparse(obj_url).path,museum=museum,
                        facts=dict(title=fields['Title'],creator_label=fields.get('Artist') or None,first=first,last=last,date_precision=precision,
                          date_display=fields['Object Date'],work_type='painting',object_form='icon',medium=fields['Medium'],dimensions=fields.get('Metric Dims') or None,
                          cultural_context='Eastern Christian icon; source origin: '+fields.get('Country of Origin',''),accession=fields['Inventory Number'],source_url=obj_url,
                          holding_basis='Official collection object with unique museum inventory; no loan credit. Holding only; no display claim.'),
                        raw_source_record=fields,source_receipt=rc,body_path=rc['path']))
                except Exception as e:
                    held.append(dict(url=obj_url,reason=type(e).__name__+': '+str(e)[:250]))
                    # A source failure ends this bounded pass; do not retry around blocks.
                    save(RUN/'priority-icons-progress.json.gz',dict(at=now(),records=selected,held=held,listings=listings,inspected=inspected))
                    raise
            print('Icon museum',country,page,'new eligible',len(selected),'inspected',inspected,flush=True)
            if not any('/page/'+str(page+1)+'/' in a['href'] for a in soup.select('a[href]')):break
    save(RUN/'icons-current-plan.json.gz',dict(at=now(),records=selected,held=held,listings=listings,inspected=inspected,
        policy='Metadata only; preserve unnamed makers without invented profiles. One inventory is one artwork; no photos or current display claims.'))
    print(json.dumps(dict(ready=len(selected),held=len(held),inspected=inspected)),flush=True)


def uid(key):
    return str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/museum-expansion-20261006/'+key))


def validate_plan(source):
    assert source in ['joconde','joconde-periods','joconde-ranges','joconde-circa','joconde-before','joconde-sculpture','joconde-sculpture-reviewed','icons','athens'] or re.fullmatch(r'(?:arco|getty|mauritshuis|barnes|tretyakov|benaki|ireland|agsa|auckland|staedel|thessaloniki|goulandris)-\d{3}',source)
    path=RUN/(source+'-current-plan.json.gz')
    raw=path.read_bytes();plan=load(path);records=plan['records']
    assert records and len(records)<=20000
    assert len({r['source_record_id'] for r in records})==len(records)
    payloads={};source_inventory=set();arco=None;getty=None;native=None;barnes=None;tretyakov=None;benaki=None;ireland=None;agsa=None;auckland=None;staedel=None;thessaloniki=None;goulandris=None
    if source.startswith('arco-'):
        spec=importlib.util.spec_from_file_location('arco_campaign',ROOT/'ops/museum-expansion-arco-20261006.py')
        arco=importlib.util.module_from_spec(spec);spec.loader.exec_module(arco)
    if source.startswith('getty-'):
        spec=importlib.util.spec_from_file_location('getty_campaign',ROOT/'ops/museum-expansion-getty-20261006.py')
        getty=importlib.util.module_from_spec(spec);spec.loader.exec_module(getty)
    if source.startswith('mauritshuis-'):
        spec=importlib.util.spec_from_file_location('native_campaign',ROOT/'ops/museum-expansion-native-20261006.py')
        native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
    if source.startswith('barnes-'):
        spec=importlib.util.spec_from_file_location('barnes_campaign',ROOT/'ops/museum-expansion-barnes-20261006.py')
        barnes=importlib.util.module_from_spec(spec);spec.loader.exec_module(barnes)
    if source.startswith('tretyakov-'):
        spec=importlib.util.spec_from_file_location('tretyakov_campaign',ROOT/'ops/museum-expansion-tretyakov-20261006.py')
        tretyakov=importlib.util.module_from_spec(spec);spec.loader.exec_module(tretyakov)
    if source.startswith('benaki-'):
        spec=importlib.util.spec_from_file_location('benaki_campaign',ROOT/'ops/museum-expansion-benaki-20261006.py')
        benaki=importlib.util.module_from_spec(spec);spec.loader.exec_module(benaki)
    if source.startswith('ireland-'):
        spec=importlib.util.spec_from_file_location('ireland_campaign',ROOT/'ops/museum-expansion-ireland-20261006.py')
        ireland=importlib.util.module_from_spec(spec);spec.loader.exec_module(ireland)
    if source.startswith('agsa-'):
        spec=importlib.util.spec_from_file_location('agsa_campaign',ROOT/'ops/museum-expansion-agsa-20261006.py')
        agsa=importlib.util.module_from_spec(spec);spec.loader.exec_module(agsa)
    if source.startswith('auckland-'):
        spec=importlib.util.spec_from_file_location('auckland_campaign',ROOT/'ops/museum-expansion-auckland-20261006.py')
        auckland=importlib.util.module_from_spec(spec);spec.loader.exec_module(auckland)
    if source.startswith('staedel-'):
        spec=importlib.util.spec_from_file_location('staedel_campaign',ROOT/'ops/museum-expansion-staedel-20261006.py')
        staedel=importlib.util.module_from_spec(spec);spec.loader.exec_module(staedel)
    if source.startswith('thessaloniki-'):
        spec=importlib.util.spec_from_file_location('thessaloniki_campaign',ROOT/'ops/museum-expansion-thessaloniki-20261006.py')
        thessaloniki=importlib.util.module_from_spec(spec);spec.loader.exec_module(thessaloniki)
    if source.startswith('goulandris-'):
        spec=importlib.util.spec_from_file_location('goulandris_campaign',ROOT/'ops/museum-expansion-goulandris-20261006.py')
        goulandris=importlib.util.module_from_spec(spec);spec.loader.exec_module(goulandris)
    for r in records:
        f=r['facts'];rc=r['source_receipt'];bodypath=ROOT/r['body_path']
        if str(bodypath) not in payloads:
            body=gzip.decompress(bodypath.read_bytes()) if bodypath.suffix=='.gz' else bodypath.read_bytes()
            assert hashlib.sha256(body).hexdigest()==rc['sha256'] and rc['status']==200
            payloads[str(bodypath)]=body
        body=payloads[str(bodypath)]
        assert r['museum']['canonical_institution_id'] is None and r['museum']['status']!='archived'
        for key in acc(f['accession']):
            inventory=(r['museum']['id'],key)
            assert inventory not in source_inventory,'Repeated source inventory'
            source_inventory.add(inventory)
        if source.startswith('joconde'):
            matches=[v for v in json.loads(body)['data'] if v['Reference']==r['source_record_id']]
            assert len(matches)==1 and matches[0]==r['raw_source_record']
            facts,reason=joconde_parser(source)(matches[0]);assert not reason and facts==f
            assert norm(matches[0]['Nom_officiel_musee']+' '+matches[0]['Ville'])==norm(r['museum']['name'])
            if 'year' in f:f.update(first=f['year'],last=f['year'],date_precision='exact')
        elif source=='icons':
            assert f['first']<=f['last']<=1970 and f['work_type']=='painting' and f['object_form']=='icon'
            assert icon_date(r['raw_source_record']['Object Date'])==(f['first'],f['last'],f['date_precision'])
            assert f['title']==r['raw_source_record']['Title'] and f['accession']==r['raw_source_record']['Inventory Number']
            assert r['source_receipt']['url']==f['source_url']
        elif arco:
            assert arco.validate_record(r,body)==f
        elif getty:
            assert getty.validate_record(r,body)==f
        elif native:
            assert native.validate_record(r,body)==f
        elif barnes:
            assert barnes.validate_record(r,body)==f
        elif tretyakov:
            assert tretyakov.validate_record(r,body)==f
        elif benaki:
            assert benaki.validate_record(r,body)==f
        elif ireland:
            assert ireland.validate_record(r,body)==f
        elif agsa:
            assert agsa.validate_record(r,body)==f
        elif auckland:
            assert auckland.validate_record(r,body)==f
        elif staedel:
            assert staedel.validate_record(r,body)==f
        elif thessaloniki:
            assert thessaloniki.validate_record(r,body)==f
        elif goulandris:
            assert goulandris.validate_record(r,body)==f
        elif source=='athens':
            assert r['museum']['slug']=='byzantine-christian-museum-athens'
            assert athens_fields(body)==r['raw_source_record']['fields']
            assert athens_facts(r['source_record_id'],body)==f
            assert r['raw_source_record']['reviewed_creation_statement']==ATHENS_DATES[r['source_record_id']][0]
            assert rc['url']==f['source_url']
        else:raise ValueError('Unreviewed source')
        r['artwork_id']=uid(source+'/'+r['source_record_id'])
        r['slug']='museum-expansion-'+source+'-'+hashlib.sha256(r['source_record_id'].encode()).hexdigest()[:20]
    digest=hashlib.sha256(raw).hexdigest()
    return plan,digest


def apply(source,expected_sha):
    plan,digest=validate_plan(source)
    assert digest==expected_sha,'Reviewed plan changed'
    records=plan['records'];ids=[r['artwork_id'] for r in records];museum_ids=sorted({r['museum']['id'] for r in records})
    source_slug='museum-expansion-20261006-'+source;sid=uid('source/'+source)
    bases={'joconde':'https://pop.culture.gouv.fr/','joconde-periods':'https://pop.culture.gouv.fr/','icons':'https://www.iconmuseum.org/collection/'}
    if source.startswith('joconde'):bases[source]='https://pop.culture.gouv.fr/'
    if source.startswith('arco-'):bases[source]='https://catalogo.cultura.gov.it/'
    if source.startswith('ireland-'):bases[source]='https://onlinecollection.nationalgallery.ie/'
    if source.startswith('agsa-'):bases[source]='https://www.agsa.sa.gov.au/collection-publications/collection/'
    if source.startswith('auckland-'):bases[source]='https://www.aucklandartgallery.com/explore/art-and-artists'
    if source.startswith('staedel-'):bases[source]='https://sammlung.staedelmuseum.de/'
    if source.startswith('thessaloniki-'):bases[source]='https://www.mbp.gr/'
    if source.startswith('goulandris-'):bases[source]='https://goulandris.gr/en/collection/works-of-art'
    if source.startswith('getty-'):bases[source]='https://www.getty.edu/art/collection/'
    if source.startswith('mauritshuis-'):bases[source]='https://www.mauritshuis.nl/en/our-collection'
    if source.startswith('barnes-'):bases[source]='https://collection.barnesfoundation.org/'
    if source.startswith('tretyakov-'):bases[source]='https://my.tretyakov.ru/'
    if source.startswith('benaki-'):bases[source]='https://www.benaki.org/'
    if source=='athens':bases[source]='https://www.ebyzantinemuseum.gr/'
    with psycopg.connect('postgresql://localhost/artline',autocommit=True,row_factory=dict_row,
        options='-c timezone=UTC -c statement_timeout=180000') as db, db.transaction():
        db.execute("SET LOCAL lock_timeout='5s'")
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        old=db.execute('SELECT id::text,status,research_candidate,current_institution_id::text FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id',(ids,)).fetchall()
        if old:
            assert len(old)==len(records),'Partial batch requires review; no overwrite'
            evidence=db.execute("SELECT entity_id::text,evidence_note FROM citations WHERE source_id=%s AND field_name='museum_expansion_primary_metadata'",(sid,)).fetchall()
            assert {e['entity_id'] for e in evidence}==set(ids) and all(json.loads(e['evidence_note'])['plan_sha256']==digest for e in evidence)
            expected={r['artwork_id']:r['museum']['id'] for r in records}
            assert all(r['status']=='review' and r['research_candidate'] and r['current_institution_id']==expected[r['id']] for r in old)
            print('Unchanged replay:',len(old),'existing review records; zero inserts',flush=True);return
        institutions=db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE id=ANY(%s::uuid[]) ORDER BY id FOR SHARE',(museum_ids,)).fetchall()
        current={v['row']['id']:v['row'] for v in institutions}
        assert len(current)==len(museum_ids)
        for r in records:
            inst=current[r['museum']['id']]
            assert inst['slug']==r['museum']['slug'] and inst['name']==r['museum']['name'] and inst['status']!='archived' and inst['canonical_institution_id'] is None
        assert not db.execute('SELECT 1 FROM sources WHERE id=%s OR slug=%s',(sid,source_slug)).fetchone(),'Unexpected existing source'
        urls=[r['facts']['source_url'] for r in records]
        assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s) LIMIT 1",(urls,)).fetchone(),'Source URL already catalogued'
        assert not db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s) LIMIT 1",(urls,)).fetchone(),'Source citation already catalogued'
        scheme_pattern='%joconde%' if source.startswith('joconde') else '%arco%' if source.startswith('arco-') else '%getty%' if source.startswith('getty-') else '%mauritshuis%' if source.startswith('mauritshuis-') else '%barnes%' if source.startswith('barnes-') else '%tretyakov%' if source.startswith('tretyakov-') else '%benaki%' if source.startswith('benaki-') else '%ngi%' if source.startswith('ireland-') else '%athens%' if source=='athens' else '%icon-museum%'
        if source.startswith('agsa-'):scheme_pattern='%agsa%'
        if source.startswith('auckland-'):scheme_pattern='%auckland%'
        if source.startswith('staedel-'):scheme_pattern='%staedel%'
        if source.startswith('thessaloniki-'):scheme_pattern='%thessaloniki%'
        if source.startswith('goulandris-'):scheme_pattern='%goulandris%'
        assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND scheme ILIKE %s AND external_id=ANY(%s) LIMIT 1",(scheme_pattern,[r['source_record_id'] for r in records])).fetchone(),'Source ID already catalogued'
        scoped=db.execute('''WITH selected AS MATERIALIZED (
          SELECT id artwork_id,current_institution_id institution_id FROM artworks WHERE current_institution_id=ANY(%s::uuid[])
          UNION SELECT artwork_id,institution_id FROM artwork_location_assertions WHERE institution_id=ANY(%s::uuid[]) AND superseded_by IS NULL
          ) SELECT a.id::text,a.title,a.alternate_title,a.accession_number,s.institution_id::text FROM selected s JOIN artworks a ON a.id=s.artwork_id''',(museum_ids,museum_ids)).fetchall()
        inventories=collections.defaultdict(set);scoped_titles=collections.defaultdict(set)
        for row in scoped:
            inventories[row['institution_id']].update(acc(row['accession_number']))
            scoped_titles[row['institution_id']].update(norm(row[k]) for k in ['title','alternate_title'] if row[k])
        if source.startswith('arco-'):
            known_paths={r['source_url'].rstrip('/').split('/detail/',1)[1] for r in db.execute("SELECT DISTINCT source_url FROM citations WHERE entity_type='artwork' AND source_url LIKE '%/detail/%'")}
            assert not known_paths & {r['source_record_id'] for r in records},'Source identifier already cited through another catalogue hostname'
        if source=='athens':
            native_urls=[r['source_url'] for r in db.execute("SELECT DISTINCT source_url FROM citations WHERE entity_type='artwork' AND source_url LIKE '%%ebyzantinemuseum.gr/%%'")]
            known_ids={parse_qs(urlparse(u).query).get('id',[''])[0] for u in native_urls}
            assert not known_ids & {r['source_record_id'] for r in records},'Native object already catalogued'
            existing_bxm={athens_inventory(r['accession_number']) for r in scoped}
            assert not existing_bxm & {athens_inventory(r['facts']['accession']) for r in records},'BXM inventory variant already present'
        all_titles={norm(r['title']) for r in db.execute('SELECT title FROM artworks')} if source.startswith('joconde') else set()
        if source.startswith('getty-'):
            api_urls=['https://data.getty.edu/museum/collection/'+r['source_record_id'] for r in records]
            assert not db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s) LIMIT 1",(api_urls,)).fetchone(),'Getty API identity already catalogued'
            assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s) LIMIT 1",(api_urls,)).fetchone(),'Getty API identifier already catalogued'
            all_titles={norm(r[k]) for r in db.execute('SELECT title,alternate_title FROM artworks') for k in ['title','alternate_title'] if r[k]}
        if source.startswith('mauritshuis-'):
            spec=importlib.util.spec_from_file_location('native_identity',ROOT/'ops/museum-expansion-native-20261006.py')
            native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
            urls={v['source_url'] for v in db.execute("SELECT DISTINCT source_url FROM citations WHERE entity_type='artwork' AND source_url ILIKE '%mauritshuis.nl/%'")}
            urls.update(v['canonical_url'] for v in db.execute("SELECT canonical_url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url ILIKE '%mauritshuis.nl/%'"))
            assert not {native.source_id(u) for u in urls}&{r['source_record_id'] for r in records},'Localized Mauritshuis source identity already catalogued'
            all_titles={norm(r[k]) for r in db.execute('SELECT title,alternate_title FROM artworks') for k in ['title','alternate_title'] if r[k]}
            foreign_inventory_keys=set().union(*(acc(r['accession_number']) for r in native.foreign_inventory_records(db)))
            assert not any(acc(inv)&foreign_inventory_keys for r in records for inv in native.foreign_inventory_references(r['raw_source_record']['native_fields'])),'Foreign inventory already catalogued; reconcile existing work'
        if source.startswith('barnes-'):
            spec=importlib.util.spec_from_file_location('barnes_identity',ROOT/'ops/museum-expansion-barnes-20261006.py')
            barnes=importlib.util.module_from_spec(spec);spec.loader.exec_module(barnes)
            assert len(museum_ids)==1
            known,barnes_titles,barnes_inventories=barnes.existing_keys(db,museum_ids[0])
            assert not known & {r['source_record_id'] for r in records},'Barnes source identity already catalogued'
            assert not any(barnes.title_keys(r['facts']['title'])&barnes_titles for r in records),'Barnes translated title requires identity review'
            assert not any(acc(r['facts']['accession'])&barnes_inventories for r in records),'Barnes inventory already catalogued'
        if source.startswith('tretyakov-'):
            spec=importlib.util.spec_from_file_location('tretyakov_identity',ROOT/'ops/museum-expansion-tretyakov-20261006.py')
            tretyakov=importlib.util.module_from_spec(spec);spec.loader.exec_module(tretyakov)
            assert len(museum_ids)==1
            known,tretyakov_titles,tretyakov_inventories=tretyakov.existing_keys(db,museum_ids[0])
            assert not known & {r['source_record_id'] for r in records},'Tretyakov source identity already catalogued'
            assert not any(tretyakov.inventory_keys(r['facts']['accession'])&tretyakov_inventories for r in records),'Tretyakov inventory variant already catalogued'
            assert not any(norm(r['facts']['title']) in tretyakov_titles for r in records),'Tretyakov native title requires review'
            tretyakov.check_translated_title_identities(db,records)
        if source.startswith('benaki-'):
            spec=importlib.util.spec_from_file_location('benaki_identity',ROOT/'ops/museum-expansion-benaki-20261006.py')
            benaki=importlib.util.module_from_spec(spec);spec.loader.exec_module(benaki)
            assert len(museum_ids)==1
            known,benaki_titles,benaki_inventories=benaki.existing_keys(db,museum_ids[0])
            for r in records:
                aliases={r['source_record_id']}|set(r['raw_source_record']['native_fields']['language_variant_ids'])
                assert not aliases&known,'Benaki language variant already catalogued'
                assert not benaki.inventory_keys(r['facts']['accession'])&benaki_inventories,'Benaki inventory variant already catalogued'
            benaki.check_title_identities(db,records)
        if source.startswith('ireland-'):
            spec=importlib.util.spec_from_file_location('ireland_identity',ROOT/'ops/museum-expansion-ireland-20261006.py')
            ireland=importlib.util.module_from_spec(spec);spec.loader.exec_module(ireland)
            assert len(museum_ids)==1
            known,titles,ireland_inventories=ireland.existing_keys(db,museum_ids[0])
            assert not known & {r['source_record_id'] for r in records},'Ireland native object already catalogued'
            assert not any(ireland.inventory_keys(r['facts']['accession'])&ireland_inventories for r in records),'Ireland inventory variant already present'
            assert not any(norm(r['facts']['title']) in titles for r in records),'Ireland scoped title requires review'
            assert not ireland.title_collisions(db,records),'Ireland matching catalogue title requires review'
        if source.startswith('agsa-'):
            spec=importlib.util.spec_from_file_location('agsa_identity',ROOT/'ops/museum-expansion-agsa-20261006.py')
            agsa=importlib.util.module_from_spec(spec);spec.loader.exec_module(agsa)
            assert len(museum_ids)==1
            known,titles,agsa_inventories=agsa.existing_keys(db,museum_ids[0])
            assert not known & {r['source_record_id'] for r in records},'AGSA native object already catalogued'
            assert not any(agsa.inventory_keys(r['facts']['accession'])&agsa_inventories for r in records),'AGSA inventory already present'
            assert not any(norm(r['facts']['title']) in titles for r in records),'AGSA scoped title requires review'
            assert not agsa.title_collisions(db,records),'AGSA matching catalogue title requires review'
        if source.startswith('auckland-'):
            spec=importlib.util.spec_from_file_location('auckland_identity',ROOT/'ops/museum-expansion-auckland-20261006.py')
            auckland=importlib.util.module_from_spec(spec);spec.loader.exec_module(auckland)
            assert len(museum_ids)==1
            known,titles,auckland_inventories=auckland.existing_keys(db,museum_ids[0])
            assert not known & {r['source_record_id'] for r in records},'Auckland native or legacy identity already catalogued'
            assert not any(auckland.inventory_keys(r['facts']['accession'])&auckland_inventories for r in records),'Auckland inventory already present'
            assert not any(norm(r['facts']['title']) in titles for r in records),'Auckland scoped title requires review'
            assert not auckland.title_collisions(db,records),'Auckland matching catalogue title requires review'
        if source.startswith('staedel-'):
            spec=importlib.util.spec_from_file_location('staedel_identity',ROOT/'ops/museum-expansion-staedel-20261006.py')
            staedel=importlib.util.module_from_spec(spec);spec.loader.exec_module(staedel)
            assert len(museum_ids)==1
            known,titles,staedel_inventories=staedel.existing_keys(db,museum_ids[0])
            assert not known & {r['facts']['source_url'].rstrip('/') for r in records},'Städel native object already catalogued'
            assert not any(staedel.inventory_keys(r['facts']['accession'])&staedel_inventories for r in records),'Städel native or legacy inventory already present'
            assert not any(norm(r['facts']['title']) in titles for r in records),'Städel scoped title requires review'
            assert not staedel.title_collisions(db,records),'Städel matching catalogue title requires review'
        if source.startswith('thessaloniki-'):
            spec=importlib.util.spec_from_file_location('thessaloniki_identity',ROOT/'ops/museum-expansion-thessaloniki-20261006.py')
            thessaloniki=importlib.util.module_from_spec(spec);spec.loader.exec_module(thessaloniki)
            assert len(museum_ids)==1
            known,titles,inventories_native=thessaloniki.existing_keys(db,museum_ids[0])
            assert not known & {r['source_record_id'] for r in records},'Thessaloniki native identity already present'
            assert not any(thessaloniki.inventory_keys(r['facts']['accession'])&inventories_native for r in records),'Thessaloniki inventory variant already present'
            assert not any(norm(r['facts']['title']) in titles for r in records),'Thessaloniki scoped title requires review'
            assert not thessaloniki.title_collisions(db,records),'Thessaloniki catalogue title requires review'
        if source.startswith('goulandris-'):
            spec=importlib.util.spec_from_file_location('goulandris_identity',ROOT/'ops/museum-expansion-goulandris-20261006.py')
            goulandris=importlib.util.module_from_spec(spec);spec.loader.exec_module(goulandris)
            assert len(museum_ids)==1
            known,titles=goulandris.existing_keys(db,museum_ids[0])
            assert not known & {r['source_record_id'] for r in records},'Goulandris native identity already present'
            assert not any(goulandris.title_keys(r)&titles for r in records),'Goulandris scoped title requires review'
            goulandris.check_title_identities(db,records)
        for r in records:
            f=r['facts'];assert not acc(f['accession']) & inventories[r['museum']['id']],'Existing museum accession requires review'
            assert not source.startswith('joconde') or norm(f['title']) not in all_titles,'Concurrent matching title requires review'
            assert not source.startswith('getty-') or norm(f['title']) not in all_titles,'Concurrent Getty title requires identity review'
            assert not source.startswith('mauritshuis-') or norm(f['title']) not in all_titles,'Concurrent Mauritshuis title requires identity review'
            assert not source.startswith('arco-') or norm(f['title']) not in scoped_titles[r['museum']['id']],'Concurrent museum title requires identity review'
            scope=db.execute('SELECT artline_creation_scope(%s,%s,%s) scope',(f['first'],f['last'],f['date_precision'])).fetchone()['scope']
            assert scope=='eligible','PostgreSQL eligibility review required'
        # This operation only inserts new records. Preserve the absent IDs and
        # institution/source preimages before the atomic transaction writes.
        save(BACKUP/(source+'-preimages.json.gz'),dict(at=now(),plan_sha256=digest,new_artwork_ids=ids,existing_artworks=old,institutions=institutions,source_preimage=None,scoped_identity_checks=scoped))
        save(BACKUP/(source+'-reviewed-plan.json.gz'),plan)
        db.execute('INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,%s,%s)',
            (sid,source_slug,'Museum expansion — reviewed primary '+source+' records, 6 October 2026','collection_page' if source=='icons' else 'authority_data',bases[source]))
        for r in records:
            f=r['facts'];aid=r['artwork_id'];rc=r['source_receipt']
            db.execute('''INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,
              work_type,medium_text,dimensions_text,accession_number,status,research_candidate,unlinked_creator_label,object_form,cultural_context,created_by,updated_by)
              VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s,%s,%s,%s)''',
              (aid,r['slug'],f['title'],norm(f['title']),f['date_display'],f['first'],f['last'],f['date_precision'],f['work_type'],f['medium'],f['dimensions'],f['accession'],f['creator_label'],f.get('object_form'),f.get('cultural_context'),ACTOR,ACTOR))
            scheme='joconde-object' if source.startswith('joconde') else 'arco-object' if source.startswith('arco-') else 'getty-object' if source.startswith('getty-') else 'mauritshuis-object' if source.startswith('mauritshuis-') else 'barnes-object' if source.startswith('barnes-') else 'tretyakov-object' if source.startswith('tretyakov-') else 'benaki-object' if source.startswith('benaki-') else 'ngi-object' if source.startswith('ireland-') else 'athens-object' if source=='athens' else 'icon-museum-object'
            if source.startswith('agsa-'):scheme='agsa-object'
            if source.startswith('auckland-'):scheme='auckland-object'
            if source.startswith('staedel-'):scheme='staedel-object'
            if source.startswith('thessaloniki-'):scheme='thessaloniki-object'
            if source.startswith('goulandris-'):scheme='goulandris-object'
            db.execute('''INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at)
              VALUES('artwork',%s,%s,%s,%s,%s,%s)''',(aid,scheme,r['source_record_id'],f['source_url'],sid,rc['retrieved_at']))
            evidence=dict(plan_sha256=digest,raw_source_record=r['raw_source_record'],source_receipt=rc,body_path=r['body_path'],
                policy='New review artwork only. Literal source creator attribution retained at object level. No fabricated person, image, display, highlight or publication.')
            db.execute('''INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)
              VALUES('artwork',%s,'museum_expansion_primary_metadata',%s,%s,%s,%s,%s,%s)''',
              (aid,sid,r['source_record_id'],f['source_url'],json.dumps(evidence,ensure_ascii=False),rc['retrieved_at'],ACTOR))
            db.execute('''INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state)
              VALUES(%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')''',
              (aid,r['museum']['id'],sid,f['source_url'],f['holding_basis']+' Source capture SHA-256 '+rc['sha256']+'.',rc['retrieved_at']))
        verified=db.execute('''SELECT a.id::text,a.current_institution_id::text,a.status,a.research_candidate,a.primary_media_id,a.published_at,
            artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) scope,
            artline_has_selection_evidence(a.id) evidence FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY a.id''',(ids,)).fetchall()
        assert len(verified)==len(ids)
        expected={r['artwork_id']:r['museum']['id'] for r in records}
        assert all(r['status']=='review' and r['research_candidate'] and r['primary_media_id'] is None and r['published_at'] is None and r['scope']=='eligible' and r['evidence'] and r['current_institution_id']==expected[r['id']] for r in verified)
        assert db.execute("SELECT count(*) n FROM artwork_location_assertions WHERE artwork_id=ANY(%s::uuid[]) AND claim_type='display'",(ids,)).fetchone()['n']==0
    save(RUN/(source+'-applied.json'),dict(at=now(),plan_sha256=digest,created=len(records),museums=len(museum_ids),artworks=verified,local_only=True,images_added=0,published=0))
    print('Added',len(records),'review artworks to',len(museum_ids),'local collections; verified eligibility and source holdings',flush=True)


def report(label):
    before=load(RUN/'baseline.json');after=load(RUN/(label+'.json'))
    old={r['id']:r for r in before['institutions']};current={r['id']:r for r in after['institutions']}
    sources=['joconde','icons','joconde-periods']
    sources+=[s for s in ['joconde-ranges','joconde-circa','joconde-before','joconde-sculpture','joconde-sculpture-reviewed'] if (RUN/(s+'-applied.json')).exists()]
    if (RUN/'athens-applied.json').exists():sources.append('athens')
    sources+=sorted(p.name.removesuffix('-applied.json') for p in RUN.glob('arco-???-applied.json'))
    sources+=sorted(p.name.removesuffix('-applied.json') for p in RUN.glob('getty-???-applied.json'))
    sources+=sorted(p.name.removesuffix('-applied.json') for p in RUN.glob('mauritshuis-???-applied.json'))
    sources+=sorted(p.name.removesuffix('-applied.json') for p in RUN.glob('barnes-???-applied.json'))
    sources+=sorted(p.name.removesuffix('-applied.json') for p in RUN.glob('tretyakov-???-applied.json'))
    sources+=sorted(p.name.removesuffix('-applied.json') for p in RUN.glob('benaki-???-applied.json'))
    sources+=sorted(p.name.removesuffix('-applied.json') for p in RUN.glob('ireland-???-applied.json'))
    sources+=sorted(p.name.removesuffix('-applied.json') for p in RUN.glob('agsa-???-applied.json'))
    sources+=sorted(p.name.removesuffix('-applied.json') for p in RUN.glob('auckland-???-applied.json'))
    sources+=sorted(p.name.removesuffix('-applied.json') for p in RUN.glob('staedel-???-applied.json'))
    sources+=sorted(p.name.removesuffix('-applied.json') for p in RUN.glob('thessaloniki-???-applied.json'))
    sources+=sorted(p.name.removesuffix('-applied.json') for p in RUN.glob('goulandris-???-applied.json'))
    plans={s:validate_plan(s) for s in sources}
    expected={r['artwork_id']:r for plan,_ in plans.values() for r in plan['records']}
    ids=sorted(expected)
    with connect() as db:
        actual=db.execute('''SELECT a.id::text,a.title,a.date_display,a.creation_year_start,a.creation_year_end,a.date_precision,
          a.work_type,a.medium_text,a.dimensions_text,a.accession_number,a.object_form,a.cultural_context,
          a.current_institution_id::text,a.status,a.research_candidate,a.unlinked_creator_label,a.primary_media_id,a.published_at,
          artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) scope,artline_has_selection_evidence(a.id) evidence,
          (SELECT count(*) FROM artwork_location_assertions l WHERE l.artwork_id=a.id AND l.claim_type='display') display_claims,
          (SELECT count(*) FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id) identifiers,
          (SELECT count(*) FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id) citations
          FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id''',(ids,)).fetchall()
        actual_citations={r['entity_id']:r for r in db.execute("SELECT entity_id::text,source_record_id,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))}
        actual_identifiers={r['entity_id']:r for r in db.execute("SELECT entity_id::text,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))}
    assert len(actual)==len(expected)
    for a in actual:
        r=expected[a['id']];f=r['facts']
        assert a['title']==f['title'] and a['date_display']==f['date_display'] and a['unlinked_creator_label']==f['creator_label']
        assert (a['creation_year_start'],a['creation_year_end'],a['date_precision'])==(f['first'],f['last'],f['date_precision'])
        assert a['current_institution_id']==r['museum']['id'] and a['status']=='review' and a['research_candidate']
        assert a['scope']=='eligible' and a['evidence'] and not a['primary_media_id'] and not a['published_at'] and a['display_claims']==0
        assert a['identifiers']==1 and a['citations']==1
        for column,field in [('work_type','work_type'),('medium_text','medium'),('dimensions_text','dimensions'),('accession_number','accession'),('object_form','object_form'),('cultural_context','cultural_context')]:
            assert a[column]==f.get(field),(a['id'],column)
        citation=actual_citations[a['id']];identifier=actual_identifiers[a['id']]
        assert citation['source_record_id']==identifier['external_id']==r['source_record_id']
        assert citation['source_url']==identifier['canonical_url']==f['source_url']
        note=json.loads(citation['evidence_note'])
        assert note['raw_source_record']==r['raw_source_record'] and note['source_receipt']==r['source_receipt']
    added=collections.Counter(r['museum']['id'] for r in expected.values())
    reconciled=collections.Counter();reconciliation_checks=[]
    if (RUN/'getty/getty-existing-exaltation-holding-applied.json').exists():
        spec=importlib.util.spec_from_file_location('getty_holding',ROOT/'ops/museum-expansion-getty-holding-20261006.py')
        holding=importlib.util.module_from_spec(spec);spec.loader.exec_module(holding)
        holding_plan=load(holding.PLAN)
        assert holding.evidence()==holding_plan['evidence']
        with connect() as db:holding.verify(db,holding_plan)
        reconciled[holding.IID]+=1
        reconciliation_checks.append(dict(artwork_id=holding.AID,institution_id=holding.IID,source_url=holding_plan['evidence']['facts']['source_url'],verified_existing_metadata_unchanged=True))
    reviewed=set()
    for source in [s for s in sources if s.startswith('joconde')]:
        reviewed.update(r['slug'] for r in load(RUN/(source+'-selection-summary.json'))['reviews'])
    object_passes=[load(p) for p in (RUN/'arco').glob('**/museums/*.json.gz')]
    object_reviews={r['museum']['slug']:r for r in sorted(object_passes,key=lambda r:r['at'])}
    index_passes=[load(p) for p in (RUN/'arco').glob('**/index-reviews/*.json.gz')]
    latest_index={ (r['authority']['source_institution_uri'],r['authority']['catalogue_city']):r for r in sorted(index_passes,key=lambda r:r['at']) }
    index_reviews=list(latest_index.values())
    if 'icons' in sources:reviewed.add('icon-museum-and-study-center')
    if 'athens' in sources:reviewed.add('byzantine-christian-museum-athens')
    if any(s.startswith('getty-') for s in sources):reviewed.add('spain-research-museum-q731126')
    if any(s.startswith('mauritshuis-') for s in sources):reviewed.add('mauritshuis')
    if any(s.startswith('barnes-') for s in sources):reviewed.add('barnes-foundation')
    if any(s.startswith('tretyakov-') for s in sources):reviewed.add('wikimedia-museum-q183334')
    if any(s.startswith('benaki-') for s in sources):reviewed.add('wikimedia-museum-q816669')
    if any(s.startswith('ireland-') for s in sources):reviewed.add('national-gallery-ireland')
    if any(s.startswith('agsa-') for s in sources):reviewed.add('wikimedia-museum-q705557')
    if any(s.startswith('auckland-') for s in sources):reviewed.add('wikimedia-museum-q4819492')
    if any(s.startswith('staedel-') for s in sources):reviewed.add('staedel-museum')
    if any(s.startswith('thessaloniki-') for s in sources):reviewed.add('museum-of-byzantine-culture-thessaloniki')
    if any(s.startswith('goulandris-') for s in sources):reviewed.add('basil-elise-goulandris-athens')
    index_by_museum=collections.defaultdict(list)
    for row in index_reviews:index_by_museum[row['museum']['slug']].append(row)
    native_probes={}
    if (RUN/'native/source-probe-status.json').exists():
        native_probes={r['museum_slug']:r for r in load(RUN/'native/source-probe-status.json')['reviews']}
    ledger=[]
    for iid,r in current.items():
        state='new_review_artworks_added' if added[iid] else 'bounded_primary_source_pass_no_approved_additions' if r['slug'] in reviewed else 'target_200_eligible_already_met' if r['eligible_works']>=200 else 'source_research_pending'
        if r['canonical_institution_id']:state='canonical_alias_not_separate_target'
        if r['status']=='archived':state='archived'
        source_rows=index_by_museum.get(r['slug'],[])
        object_review=object_reviews.get(r['slug'],{})
        if state=='source_research_pending' and source_rows:
            state='bounded_source_index_reviewed_object_checks_pending' if any(v['status']=='bounded_primary_index_reviewed' for v in source_rows) else 'source_unavailable_followup_required'
        if not added[iid] and object_review:state='bounded_object_review_no_approved_additions'
        native_probe=native_probes.get(r['slug'],{})
        if state=='source_research_pending' and native_probe.get('status')=='direct_catalogue_capture_unavailable':state='source_unavailable_followup_required'
        ledger.append(dict(**r,works_before=old[iid]['works'],eligible_before=old[iid]['eligible_works'],added_this_campaign=added[iid],existing_artworks_linked_this_campaign=reconciled[iid],research_state=state,
            native_source_probe_status=native_probe.get('status',''),
            italian_index_scopes_reviewed=len(source_rows),italian_source_failures=sum(v['status']=='source_failure' for v in source_rows),
            italian_object_review_status=object_review.get('research_status','')))
    # Reports are snapshots: retain every wave, including its counts and gaps.
    coverage=RUN/('museum-coverage-'+label+'.csv')
    with coverage.open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(ledger[0]));writer.writeheader();writer.writerows(sorted(ledger,key=lambda r:(not r['priority_tradition'],r['eligible_works'],r['name'])))
    with (RUN/('added-artworks-'+label+'.csv')).open('x',newline='') as f:
        fields=['artwork_id','museum','museum_slug','title','creator_label','date_display','creation_year_start','creation_year_end','accession','source_url','status']
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for r in sorted(expected.values(),key=lambda r:(r['museum']['name'],r['facts']['title'])):
            f=r['facts'];writer.writerow(dict(artwork_id=r['artwork_id'],museum=r['museum']['name'],museum_slug=r['museum']['slug'],title=f['title'],creator_label=f['creator_label'],date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],accession=f['accession'],source_url=f['source_url'],status='review'))
    source_passes=reviewed|set(object_reviews)
    source_museums={r['slug'] for r in current.values() if r['kind']=='museum'}&source_passes
    summary=dict(at=now(),verified_new_artworks=len(actual),institutions_expanded=len(added),museums_expanded=sum(current[iid]['kind']=='museum' for iid in added),
        expanded_institution_kinds=dict(collections.Counter(current[iid]['kind'] for iid in added)),source_pass_museums=len(source_museums),source_pass_institutions=len(source_passes),
        verified_existing_artworks_linked=sum(reconciled.values()),existing_holding_verifications=reconciliation_checks,
        native_source_probe_issues=list(native_probes.values()),
        italian_index_scopes_reviewed=len(index_reviews),italian_index_museums_reviewed=len(index_by_museum),
        italian_index_source_failures=sum(r['status']=='source_failure' for r in index_reviews),
        italian_object_review_museums=len(object_reviews),
        by_source={s:dict(new_artworks=len(p['records']),held=len(p['held']),plan_sha256=d) for s,(p,d) in plans.items()},
        before=before['summary'],after=after['summary'],
        museums_crossing_100=[dict(name=r['name'],before=old[iid]['works'],after=r['works']) for iid,r in current.items() if r['kind']=='museum' and old[iid]['works']<100<=r['works']],
        museums_crossing_200=[dict(name=r['name'],before=old[iid]['works'],after=r['works']) for iid,r in current.items() if r['kind']=='museum' and old[iid]['works']<200<=r['works']],
        other_collections_crossing_200=[dict(name=r['name'],kind=r['kind'],before=old[iid]['works'],after=r['works']) for iid,r in current.items() if r['kind']!='museum' and old[iid]['works']<200<=r['works']],
        verified_review_only=True,verified_dates_and_provenance=True,photos_downloaded=0,production_changed=False,
        remaining='Goal remains active. Every museum is counted; detailed source review has covered the listed source passes, not every museum. Zero candidates is not evidence that a museum has fewer than 100 eligible artworks.')
    save(RUN/('verification-'+label+'.json'),summary)
    # Preserve reviewed ArCo institution identities for the next bounded source group.
    if not (RUN/'arco-research-roster.json').exists():
        authorities=load(ROOT/'docs/research/artwork-locations-20261004/arco-institution-resolutions-20261005b.json')
        roster=[]
        for authority in authorities:
            museum=current.get(authority['institution']['id'])
            if museum and museum['kind']=='museum' and museum['status']!='archived' and not museum['canonical_institution_id'] and museum['eligible_works']<200:
                roster.append(dict(museum=museum,authority=authority,scope='Scope source queries by BOTH institute URI and catalogue city; the ArCo URI alone can group same-name sites. Require current-location graph and original creation-date evidence before any addition.'))
        save(RUN/'arco-research-roster.json',dict(at=now(),scopes=roster,distinct_museums=len({r['museum']['id'] for r in roster}),status='scoped follow-up queue; no new ArCo artworks yet researched or imported in this campaign'))
    print(json.dumps({k:summary[k] for k in ['verified_new_artworks','museums_expanded','source_pass_museums']}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['audit','select-joconde','capture-joconde','capture-icons','capture-athens','capture-athens-followup','apply','report'])
    p.add_argument('--label',default='baseline')
    p.add_argument('--source')
    p.add_argument('--plan-sha')
    a=p.parse_args()
    if a.command=='audit':audit(a.label)
    elif a.command=='select-joconde':select_joconde(a.source or 'joconde',a.label)
    elif a.command=='capture-joconde':capture_joconde(a.source or 'joconde')
    elif a.command=='capture-icons':capture_icons()
    elif a.command=='capture-athens':capture_athens()
    elif a.command=='capture-athens-followup':capture_athens_followup()
    elif a.command=='report':report(a.label)
    else:
        assert a.source and a.plan_sha
        apply(a.source,a.plan_sha)
