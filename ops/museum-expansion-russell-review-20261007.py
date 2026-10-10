#!/usr/bin/env python3
"""Record the bounded Russell-Cotes holding review; database reads only."""
import gzip
import hashlib
import importlib.util
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup

s=importlib.util.spec_from_file_location('w',Path(__file__).with_name('museum-expansion-russell-holdings-20261007.py'))
w=importlib.util.module_from_spec(s);s.loader.exec_module(w);m=w.m


def compact(value):
    return re.sub(r'[^a-z0-9]', '', (value or '').lower())


def parse(raw):
    soup=BeautifulSoup(raw,'html.parser');heads=soup.select('h2');assert len(heads)==1
    heading=heads[0];caption=heading.find_next_sibling('p');main=soup.find('main');article=main.find('article',recursive=False) if main else None;canon=soup.select('link[rel="canonical"]')
    return dict(title=heading.get_text(' ',strip=True),caption_lines=[x.strip() for x in caption.get_text('\n',strip=True).splitlines() if x.strip()] if caption else [],narrative=article.get_text(' ',strip=True) if article else None,canonical=canon[0]['href'] if len(canon)==1 else None)


def checked_page(ref):
    w.checked_reference(ref);x=m.load(m.ROOT/ref['path']);cap=x['capture'];raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes())
    assert cap['receipt']['status']==200 and hashlib.sha256(raw).hexdigest()==cap['receipt']['sha256']
    assert x['url']==cap['receipt']['url']==cap['receipt']['final_url']
    assert x['parsed']['canonical'] in [None,x['url']]
    assert x['url'].startswith('https://russellcotes.com/collection-piece/')
    assert parse(raw)==x['parsed']
    return x


NOTES={
'Q119147652': 'The native BORGM00924 oil-on-board study is distinct from Gregory’s finished painting at the Lady Lever and from his other studies. Caption says “from 1882”; narrative says the larger project ran 1882–1897. Existing 1896–1898 is preserved with that discrepancy; no date correction or display assertion. Native short creator forms John/Edward Gregory are retained as source text.',
'Q119140460': 'Native BORGM01224 identifies Knowles’s copy of Beaumont’s Little Timidity; this holding is the Knowles object, not the Beaumont original. Native caption 1865 conflicts with existing 1885 and with its own narrative referencing the 1885 original and Knowles’s 1863 birth. Preserve existing 1885 and all source dates; no chronology correction is inferred from this clear caption inconsistency.',
'Q119143581': 'Native BORGM00166, same 1890 date and oil panel, matches this physical object. Museum calls the painter Reginald Edward Arnold (1853–1928), while imported authority says Reginald Ernest Arnold. Preserve both source labels and the existing artist link; this pass does not reconcile biography or rename the artist.',
'Q119134946': 'Native BORGM00168 explicitly identifies Arnold’s 1881 copy after Meissonier. Existing title already preserves “after Ernest Meissonier” and existing primary artist is Arnold, the maker of this copy. Do not link it as a Meissonier original. Museum caption gives 1853–1938, while another native Arnold object uses 1853–1928 and Edward versus imported Ernest; retain these source discrepancies without biography changes.',
'Q119710615': 'Native BORGM00033 explicitly identifies Henry Justice Ford’s copy of Anna Lea Merritt, distinguishing it from Merritt’s Tate original. Existing primary artist is Ford. Preserve the native copy label in this citation. Native caption 1889 differs from existing 1890–1910 and may refer to the prototype; no date is corrected. Historical Merton ownership ended 1921; it does not contradict the separately referenced collection.',
'Q119141126': 'Native BORGM01201 has the same object title and creator Henry John Yeend King, but no creation date. Its artist biography is not an artwork date. Existing sourced 1886 is preserved.',
'Q119148272': 'Native BORGM00962 matches the title and Joshua Anderson Hague; no creation date is supplied on the object caption. Preserve existing sourced 1898; do not derive an artwork date from his biography.',
'Q119205047': 'The native gallery also lists two sculptures called The Bathers (SC42 Andreoni and SC24 Stephens). Neither is this Alfred Palmer 1925 painting BORGM01696. Title-only pages are retained as rejected identity leads.',
'Q119144560': 'Native BORGM02428 identifies Charles Wyllie, explicitly distinguished from his brother William Lionel Wyllie in the narrative. Keep this 1891 painting distinct from William Lionel’s Tate Battle of the Nile.',
'Q119147423': 'Native BORGM01968 describes clothing added to this same Byam Shaw Jezebel painting, not a separate surviving version. No extra artwork is created for the earlier nude state.',
'Q119141838': 'Native BORGM00112 describes a historic sale and repurchase by Merton. The current official object page corroborates the referenced collection. A past sale is not treated as a current disposal.',
'Q119870844': 'Merton Russell-Cotes is the explicitly historical owner, ending 1921; the collection and location assertions independently identify Russell-Cotes. No current ownership assertion is added.',
'Q119141497': 'Merton Russell-Cotes is the explicitly historical owner, ending 1921; the collection and location assertions independently identify Russell-Cotes. No current ownership assertion is added.',
'Q119122111': 'Merton Russell-Cotes ownership is explicitly bounded 1876–1921; this is compatible with the separately referenced museum collection. Do not infer a present owner from the historical claim.',
'Q119870066': 'The collection reference uses the exact Art UK object URL through P854 rather than an Art UK identifier snak. The URL exactly agrees with P1679 for A Yard in Ringwood; retain 1883–1935 as a source range.',
}


def main():
    assert not w.REVIEW.exists()
    scope=m.load(w.RUN/'initial-scope-001.json.gz');identity=m.load(w.RUN/'identity-comparison-001.json.gz');baseline=w.baseline();arts={r['id']:r for r in baseline['artworks']}
    refs=[w.reference(p) for p in sorted((w.RUN/'native-objects-001').glob('*.gz'))];assert len(refs)==140
    pages=[(ref,checked_page(ref)) for ref in refs]
    disposal=m.load(w.RUN/'disposal-review-001.json');assert disposal['proposal_not_completed'] and not disposal['existing_scope_inventory_matches']
    assert not any(compact(a['accession_number']) in compact(disposal['full_extracted_text']) for a in arts.values() if a['accession_number'])
    native=[]
    for r in identity['selected']:
        a=arts[r['artwork_id']];matches=[];titleonly=[]
        for ref,page in pages:
            p=page['parsed'];record=dict(reference=ref,url=page['url'],parsed=p)
            if any(compact(a['accession_number'])==compact(line) for line in p['caption_lines']):matches.append(record)
            elif m.norm(a['title'])==m.norm(p['title']):titleonly.append(record)
        assert len(matches)<=1
        native.append(dict(artwork_id=a['id'],qid=r['qid'],exact_inventory_sources=matches,title_only_sources=titleonly))
    m.save(w.RUN/'native-holding-comparison-001.json.gz',dict(at=m.now(),capture_files=refs,rows=native,source_count=140,disposal_reference=w.reference(w.RUN/'disposal-review-001.json'),scope_count=115,policy='Exact object inventories distinguish native corroboration from same-title false matches. All original captions and narratives retained. No object photos downloaded.'))
    extra=m.load(w.RUN/'additional-identity-review-001.json.gz');ctx=m.load(w.RUN/'additional-identity-context-001.json.gz')
    for q in ctx['creator_qids']:
        assert len([r for r in ctx['authorities'] if r['external_id']==q])<=1, 'Duplicate creator authority'
    for a in arts.values():
        for l in [x for x in identity['creator_links'] if x['artwork_id']==a['id']]:
            c=next(x for x in extra['artists'] if x['id']==l['artist_id'])
            assert not c['birth_year'] or a['creation_year_end']>=c['birth_year']
            assert not c['death_year'] or a['creation_year_start']<=c['death_year']
    decisions=[]
    for r in w.evaluate():
        if r['decision']=='hold':decisions.append(r);continue
        f=r['facts'];a=arts[r['artwork_id']];nr=next(x for x in native if x['artwork_id']==a['id'])
        version='Exact artwork authority, catalogue title, museum-qualified inventory and one matching creator authority identify this physical record. No duplicate artwork authority or exact inventory conflict found. Creator-scoped records, surname-label candidates and exact-title records were compared; generic titles alone are not identity evidence.'
        if f['qid'] in NOTES:version+=' '+NOTES[f['qid']]
        if f['inventory'].startswith(':') or ':' in f['inventory']:version+=' Source inventory punctuation is retained exactly; the BORGM museum namespace is explicit.'
        if nr['exact_inventory_sources']:version+=' The museum’s native object caption independently agrees on the inventory; its complete wording and any discrepancies are retained below.'
        # These closely named works have distinct inventory identities, dates or subjects.
        if f['creator_label'] in ['George Walter Harris','Arthur Henry Davis','Alfred Lys Baldry','Albert Durer Lucas','John Robertson Reid']:
            version+=' Similar titles by this creator were reviewed as distinct museum inventory objects; no source states that they are faces, components or aliases of one another.'
        decisions.append(dict(artwork_id=a['id'],qid=r['qid'],title=a['title'],decision='accept_holding',facts=f,confidence=0.8,
          basis='Current Wikidata object capture explicitly references this museum collection through the exact Art UK object record, and agrees with the existing artwork identity, creator authority, inventory and pre-1971 creation statement. The museum’s own collections-enquiries page identifies Art UK as its external collection catalogue. Its current proposed-disposals list contains no matching inventory.',
          version_review=version,native_comparison=nr,
          limitation='Editorial confidence, not a calibrated probability. Most records remain referenced secondary-catalogue evidence; a fresh direct Art UK object-page check is not claimed. Native evidence, where present, is separately retained. Holding only: no ownership, custody, current display, artwork metadata or publication change. The future 26 October 2026 disposal decision remains unobserved.'))
    assert sum(r['decision']=='accept_holding' for r in decisions)==98
    m.save(w.REVIEW,dict(at=m.now(),decisions=decisions,review_scope=dict(existing_records=166,eligible_pending=115,accepted=98,held=17,native_pages=140,creator_scoped_records=len(identity['artist_artworks']),unlinked_label_candidates=len(identity['unlinked']),exact_title_records=len(extra['exact_title_lookup'])),references=[w.reference(w.RUN/n) for n in ['collections-enquiries-source-001.json.gz','collection-context-source-001.json.gz','disposal-review-001.json','additional-identity-review-001.json.gz','additional-identity-context-001.json.gz','native-holding-comparison-001.json.gz']],policy='Existing local holdings only. Keep all 166 catalogue records and relations unchanged except the 98 accepted holding assignments and superseded pending claims. Preserve full qualified copy and study evidence, source dates and unresolved creator biographical labels.'))
    print('Reviewed 98 holdings; 17 held; zero database writes')


if __name__=='__main__':main()
