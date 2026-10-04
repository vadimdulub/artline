#!/usr/bin/env python3
"""A selected global history focus. Local, source-backed review records only.

plan audits the real catalogue read-only; apply inserts only the pinned new
events and museum objects after a verified backup. No updates or publication.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
import uuid

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'docs/research/womens-rights-20260926'
BACKUP = Path('/Users/vadimdulub/Library/Application Support/Artline/backups/womens-rights-20260926')
PRESETS = ROOT / 'apps/server/internal/atlas/presets.json'
ACTOR = 'local-european-research'

SOURCES = {
 'un': ('UN Women — Women unite', 'https://interactive.unwomen.org/multimedia/timeline/womenunite/en/index.html'),
 'footprint': ('UN Women — Women’s footprint in history', 'https://interactive.unwomen.org/multimedia/timeline/womensfootprintinhistory/en/index.html'),
 'ndl-literature': ('National Diet Library — Women writers', 'https://www.ndl.go.jp/portrait/e/pickup/011'),
 'ndl-vote': ('National Diet Library — General elections', 'https://www.ndl.go.jp/modern/e/cha5/description05.html'),
 'nz': ('New Zealand History — Women’s suffrage', 'https://nzhistory.govt.nz/politics/womens-suffrage/brief-history'),
 'maori': ('New Zealand History — Māori women', 'https://nzhistory.govt.nz/women-together/theme/maori'),
 'nz-vote': ('New Zealand History — Women vote', 'https://nzhistory.govt.nz/page/women-vote-first-general-election'),
 'parliament': ('UK Parliament — Women’s suffrage archive', 'https://www.parliament.uk/about/living-heritage/transformingsociety/electionsvoting/womenvote/unesco/'),
 'equal-franchise': ('UK Parliament — Equal Franchise Act', 'https://www.parliament.uk/about/living-heritage/transformingsociety/electionsvoting/womenvote/unesco/equal-franchise-act-1928/'),
 'nara': ('US National Archives — Nineteenth Amendment', 'https://www.archives.gov/milestone-documents/19th-amendment'),
 'sa': ('South African History Online — Women’s march', 'https://sahistory.org.za/dated-event/20-000-women-march-union-buildings-protest-pass-laws'),
 'atelier': ('London Museum — Suffrage Atelier', 'https://www.londonmuseum.org.uk/collections/v/object-967741/the-prehistoric-argument/'),
}

# Date, geography, source and original editorial description, not copied prose.
EVENTS = [
 ('sor-juana',1691,'Sor Juana defends women’s learning',['Mexico'],'footprint','Sor Juana Inés de la Cruz answers criticism of her intellectual work and defends women’s education.'),
 ('seneca-falls',1848,'Seneca Falls women’s rights convention',['United States'],'un','The Declaration of Sentiments demands women’s civil and political equality.'),
 ('sojourner-truth',1851,'Sojourner Truth speaks for women’s rights',['United States'],'un','Truth challenges racial and gender exclusion. Later versions of her speech differ.'),
 ('british-petition',1866,'Women’s suffrage petition reaches Parliament',['United Kingdom'],'parliament','A petition brings the demand for women’s parliamentary voting rights before the House of Commons.'),
 ('meri-mangakahia',1893,'Meri Mangakāhia addresses the Māori Parliament',['New Zealand'],'maori','Mangakāhia calls for women to vote and stand in Te Kotahitanga, the Māori Parliament.'),
 ('new-zealand-act',1893,'New Zealand’s Electoral Act enfranchises women',['New Zealand'],'nz','The Electoral Act becomes law on 19 September. Eligibility includes Māori women but does not remove every citizenship restriction.'),
 ('new-zealand-vote',1893,'Women vote in New Zealand’s general election',['New Zealand'],'nz-vote','On 28 November, women exercise their newly won parliamentary voting rights in a general election.'),
 ('suffrage-atelier',1909,'Suffrage Atelier is founded',['United Kingdom'],'atelier','Artists organise to make posters, postcards and prints for the Votes for Women campaign.'),
 ('international-womens-day',1911,'First International Women’s Day',['Austria','Denmark','Germany','Switzerland'],'un','Women organise internationally for political participation and equality.'),
 ('seito',1911,'Seitō creates a forum for Japanese women writers',['Japan'],'ndl-literature','Hiratsuka Raichō and her collaborators launch a literary magazine that opens debate about women’s lives and emancipation.'),
 ('nineteenth-amendment',1920,'United States ratifies the Nineteenth Amendment',['United States'],'nara','Ratified on 18 August, the amendment prohibits denying the vote on grounds of sex. Racial discrimination still obstructs many women’s voting.'),
 ('equal-franchise',1928,'Britain adopts equal parliamentary voting ages',['United Kingdom'],'equal-franchise','The Equal Franchise Act receives Royal Assent on 2 July, extending the vote to women on the same age terms as men.'),
 ('nyonin-geijutsu',1928,'Nyonin geijutsu opens a women’s literary network',['Japan'],'ndl-literature','Hasegawa Shigure launches the magazine’s second series, bringing together women writers with different artistic and political approaches.'),
 ('aba-women',1929,'Women’s War in southeastern Nigeria',['Nigeria'],'un','Women organise against colonial administration and feared taxation.'),
 ('japan-electoral-law',1945,'Japan’s electoral reform grants women the vote',['Japan'],'ndl-vote','The electoral law reform of 17 December extends voting rights to women; the first election under it follows in 1946.'),
 ('japan-first-vote',1946,'Japanese women vote and enter the Diet',['Japan'],'ndl-vote','Women vote in the 10 April general election, and 39 women are elected to the House of Representatives.'),
 ('commission-status-women',1946,'UN Commission on the Status of Women is established',[],'un','A dedicated international body advances women’s equality.'),
 ('doria-shafik',1951,'Doria Shafik leads a women’s protest at Egypt’s parliament',['Egypt'],'footprint','Shafik and other women demand political rights and access to public decision-making.'),
 ('south-africa-march',1956,'South African women march against pass laws',['South Africa'],'sa','On 9 August, women converge on Pretoria’s Union Buildings to oppose apartheid pass laws.'),
 ('mirabal-sisters',1960,'The Mirabal sisters are assassinated',['Dominican Republic'],'un','Their killing becomes a reference point for campaigns against violence toward women.'),
 ('iceland-day-off',1975,'Women’s Day Off in Iceland',['Iceland'],'un','Women withhold paid and unpaid work to demonstrate its social importance.'),
 ('cedaw',1979,'Convention on the Elimination of Discrimination against Women',[],'un','The United Nations adopts CEDAW, an international framework against discrimination.'),
 ('unity-dow',1992,'Unity Dow challenges discriminatory citizenship rules',['Botswana'],'footprint','Dow’s case challenges unequal rules governing women’s ability to pass nationality to their children.'),
 ('violence-declaration',1993,'UN declaration addresses violence against women',[],'un','An international declaration recognises violence against women as a human-rights concern.'),
 ('beijing',1995,'Beijing Declaration and Platform for Action',[],'un','Governments adopt a broad agenda for women’s equality.'),
 ('resolution-1325',2000,'Security Council Resolution 1325 on women, peace and security',[],'un','The resolution addresses women’s participation in peace and security.'),
]

# Curated object-level connections; being made by a woman alone is insufficient.
ARTWORKS = [
 ('ab18c302-3c54-4632-a943-47a61849f344','Women’s access to artistic education: an artist presents herself teaching two pupils.'),
 ('76fff0b1-e308-4e8d-b640-44975d117155','A pupil portrayed by her teacher; women’s training and artistic networks.'),
 ('3f7c48c9-eaaf-553f-bb90-c0a001b2ed2d','Women training together in an artist’s studio.'),
 ('672a786f-4f8b-53c9-852b-a6ab67ac75ca','Professional identity and mutual portraiture between women artists.'),
 ('63acba80-71c6-5590-ad2b-57a81e5b678f','A woman portrayed in her professional identity as an artist.'),
 ('91466d2e-dfa3-5777-b583-241c35dd2a44','A woman artist faces financial and institutional exclusion.'),
 ('38b6fcc8-f86d-5160-915e-34bc4dc04fc1','Preparatory work for the painting about a woman artist’s economic vulnerability.'),
 ('f9b13529-712b-598b-a0b6-067583a6e85c','Women’s industrial labour; social context for economic rights.'),
 ('5e8f1d7a-d4d7-5ed9-af96-4f9f40c2a89d','Self-portrait painting a nude model, a subject barred during Knight’s formal training.'),
 ('4e158cfd-ba19-5c72-b5d1-f48d91f81e3c','Domestic confinement and women’s freedom; the De Morgan Foundation connects this painting with suffrage.'),
 ('089467a0-14ba-57da-ae32-3ae0090dad8e','Portrait of suffrage campaigner Christabel Pankhurst.'),
 ('12f4fe59-4aef-5cb5-a3a4-56ea8ba76d43','Enslavement, reproductive exploitation and a woman’s survival, as discussed by Smithsonian American Art Museum.'),
 ('059a9b15-4857-5b67-a329-b6241c6e95da','A woman artist claims the professional and allegorical identity of Painting.'),
 ('7175a56c-6989-4f26-bd30-bd5026845bc0','Women’s presence in modern public transport; social context, not a campaign poster.'),
 ('b8f8917e-f200-4ca0-9a73-e251d9ca4eb4','Women’s shared activity and labour; read beside Cassatt’s work on the Modern Woman mural.'),
 ('ee71a9df-a4d1-48c4-8c22-ed6b3fe1e13c','Women as participants in public cultural life.'),
 ('2e23d054-af6d-4839-b06b-574f894010c2','A woman’s writing and private communication.'),
 ('faeef9a6-48eb-4ff6-8f2d-9f18cccf94e6','Women’s musical learning and teaching.'),
 ('3cd3868e-1da9-56e9-bacc-ab89dabadcdc','Reading and intergenerational education.'),
 ('e000e90d-89b1-4442-bb2f-7524e903bc00','Girlhood represented outside formal portrait conventions; contextual selection.'),
 ('559e132a-fa4a-579f-8fe8-ca32e1b819cb','Pregnancy, poverty and despair; social conditions affecting women’s autonomy.'),
 ('59f5b0aa-1394-450d-9fd9-3fe6f80e49b7','A working woman depicted as an individual rather than an idealised figure.'),
 ('46c95b48-355c-4747-a51c-4039fd573c9b','Hunger and care work; economic context for women’s rights.'),
 ('7472877a-7e76-43ae-b53c-34c0f7425970','Campaign imagery addressing child hunger and the burden on families.'),
 ('81c3bc4b-cf2f-43a6-b332-bb5dde750f6a','Unemployment and household insecurity; economic context.'),
 ('387be0b9-699d-4959-88c5-ca1fa0a9906a','A woman preparing for rebellion in Kollwitz’s Peasants’ War cycle.'),
 ('54c1a938-4c10-429c-81ac-678519587c5e','Women and children surviving war; context for social protection and peace movements.'),
 ('d059bcc8-bfa2-59bb-b5d1-05d071bc32e2','Young women’s interior lives in Sher-Gil’s representation of India.'),
 ('0061ae26-7e3d-5447-be6a-c550c5efae90','Women’s experience of marriage and collective preparation.'),
 ('804324cb-b5ba-5d90-9941-938fdab242ef','Child marriage as a subject for considering girls’ agency.'),
 ('34b53477-a0e2-5149-a1c1-fa58789cb321','Rural women’s lived experience; social context without attributing campaign intent.'),
 ('24eeb08d-3517-5e1c-9734-766ce6300822','A woman’s everyday bodily experience outside idealised portraiture.'),
 ('9ca7c0dc-9361-5039-81ba-d9b2af3228bf','A woman artist’s self-representation across cultural conventions.'),
 ('7747a7ff-17a4-5e4e-bbbc-8704c1673710','Women beyond metropolitan elite society; social context.'),
 ('634281bb-cf30-4b54-97e3-90061988b8af','A woman engaged in reading; education and intellectual life.'),
 ('6545dcb5-dbe5-442c-a916-f8c66cfc617e','A woman artist’s self-definition in a profession with unequal access.'),
 ('e7c49a43-edc6-48e2-a6ab-339d93ef3e38','The domestic spaces within which many women could work and be represented.'),
 ('a2098470-f41b-526e-b029-461efac2f1c2','An unconventional representation of a woman at ease, accompanied by books.'),
 ('c1fc8933-edac-5cc6-a7b0-efe78875f610','Self-representation and a woman artist’s control of her image.'),
]
CONTEXT_ART = [
 ('ccdb79fc-585d-5c0a-b8d0-963cfacf66ba','Katsushika Ōi’s professional practice in Edo Japan; not evidence of suffrage activism.'),
 ('b14d4d5c-723f-59d6-ac67-a61646305baf','Kiyohara Yukinobu’s professional practice in early modern Japan; broader historical context.'),
 ('56cd9741-5067-48b0-b8e2-1638510b79a2','Ikeda Shōen’s representation of women’s social life; context for the Japanese literary and political events.'),
]
BOOK_IDS = '''wd-q1479512 wd-q16765210 wd-q3113189 wd-q300646 wd-q890170 wd-q3407659 wd-q7775461 wd-q8031357 wd-q462373 wd-q7636766 wd-q5739278 wd-q1204366 wd-q470098 wd-q2438791 wd-q7733656 wd-q7531252 wd-q5442867 wd-q23307340 wd-q517172 wd-q44701 wd-q523076 wd-q1567505 wd-q1514807 wd-q1629456 wd-q752584 wd-q478016 wd-q1476619 wd-q784986 wd-q1213085 wd-q2268151 wd-q7731579 wd-q3202654 wd-q1897870 wd-q1541914'''.split()
EXISTING_EVENTS = ['event-q1967499','event-q104866764','event-q23035649','event-q7813','event-q21070462','event-q7099022']

def encode(x):
    return json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2,default=str).encode()

def save(name,x):
    p=RUN/name; p.parent.mkdir(parents=True,exist_ok=True)
    raw=x if isinstance(x,bytes) else encode(x)
    if p.exists():
        assert p.read_bytes()==raw, 'Evidence changed: '+str(p)
    else:
        p.write_bytes(raw)

def connect(readonly=True):
    return psycopg.connect('postgresql://localhost/artline',autocommit=True,row_factory=dict_row,
        options='-c statement_timeout=120000'+(' -c default_transaction_read_only=on' if readonly else ''))

def event_records():
    out=[]
    for key,year,title,countries,source,description in EVENTS:
        name,url=SOURCES[source]
        out.append(dict(id='event-womens-rights-'+key,sourceId='artline-womens-rights-'+key,
            title=title,startYear=year,endYear=year,years=str(year),kind='Event',status='review',top100=False,
            description=description,significance='',searchTerms='women women’s rights suffrage education equality '+title,
            countries=countries,regions=[],topics=['Women’s rights'],people=[],locations=[],connections=[],
            sources=[dict(name=name,url=url)],sourceUrl=url,approximate=False,
            dateBasis='Year of the specified event, not the duration of the wider movement.',
            geographyBasis='Selected place associations; not an exhaustive list of participants or historical borders.',
            selectionBasis='Selected for Artline’s global history of women’s rights. Inclusion is thematic, not a ranking.'))
    return out

def plan():
    with connect() as db:
        arts=db.execute('''SELECT to_jsonb(a) record,artline_has_selection_evidence(a.id) selected,
          m.storage_path, ARRAY(SELECT ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id) creators
          FROM artworks a LEFT JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id''',([x[0] for x in ARTWORKS+CONTEXT_ART],)).fetchall()
        assert len(arts)==len(ARTWORKS+CONTEXT_ART)
        for a in arts:
            assert a['selected'] and a['storage_path'] and a['record']['creation_year_end']<=1970
        books=db.execute('SELECT record FROM book_records WHERE id=ANY(%s) ORDER BY id',(BOOK_IDS,)).fetchall()
        assert len(books)==len(BOOK_IDS)
        existing=db.execute('SELECT record FROM event_records WHERE id=ANY(%s) ORDER BY id',(EXISTING_EVENTS,)).fetchall()
        assert len(existing)==len(EXISTING_EVENTS)
        events=event_records()
        assert not db.execute('SELECT 1 FROM event_records WHERE id=ANY(%s) OR title=ANY(%s)',([e['id'] for e in events],[e['title'] for e in events])).fetchone()
    save('selection.json',dict(artworks=[dict(id=i,reason=r,relationship='related') for i,r in ARTWORKS]+[dict(id=i,reason=r,relationship='context') for i,r in CONTEXT_ART],books=BOOK_IDS,existing_events=EXISTING_EVENTS))
    save('existing-records.json',dict(artworks=arts,books=books,events=existing))
    save('events.json',events)
    save('plan-pin.json',{'sha256':hashlib.sha256((RUN/'events.json').read_bytes()).hexdigest()})
    save('presets-before.json',PRESETS.read_bytes())
    print('Planned',len(arts),'illustrated artworks,',len(books),'books,',len(events),'new and',len(existing),'existing events.')

def backup():
    BACKUP.mkdir(parents=True,exist_ok=True)
    path=BACKUP/'local-before.dump'
    if not path.exists():
        temporary=BACKUP/'local-before.incomplete'
        subprocess.run(['pg_dump','-h','localhost','-d','artline','-Fc','-f',str(temporary)],check=True)
        subprocess.run(['pg_restore','--list',str(temporary)],check=True,stdout=subprocess.DEVNULL)
        temporary.rename(path)
    subprocess.run(['pg_restore','--list',str(path)],check=True,stdout=subprocess.DEVNULL)
    save('backup.json',dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size))

def apply():
    raw=(RUN/'events.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==json.loads((RUN/'plan-pin.json').read_bytes())['sha256']
    b=json.loads((RUN/'backup.json').read_bytes()); assert hashlib.sha256(Path(b['path']).read_bytes()).hexdigest()==b['sha256']
    events=json.loads(raw)
    with connect(False) as db,db.transaction():
        db.execute('SELECT pg_advisory_xact_lock(559220260915)')
        db.execute('SELECT pg_advisory_xact_lock(20250907001)')
        for e in events:
            old=db.execute('SELECT record,status FROM event_records WHERE id=%s',(e['id'],)).fetchone()
            if old:
                assert old==dict(record=e,status='review'), 'Existing event changed; refusing overwrite.'
                continue
            assert not db.execute('SELECT 1 FROM event_records WHERE title=%s',(e['title'],)).fetchone()
            db.execute('INSERT INTO event_records(id,source_id,status,record,source_checksum,topics,countries,regions) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)',
                (e['id'],e['sourceId'],'review',Jsonb(e),hashlib.sha256(encode(e)).hexdigest(),e['topics'],e['countries'],e['regions']))
    save('applied.json',dict(target='local',events=len(events),review_only=True,events_sha256=hashlib.sha256(raw).hexdigest()))
    print('Inserted/verified',len(events),'source-backed events in local review.')

def preset():
    events=json.loads((RUN/'events.json').read_bytes())
    with connect() as db:
        assert db.execute('SELECT count(*) n FROM event_records WHERE id=ANY(%s)',([e['id'] for e in events],)).fetchone()['n']==len(events)
    ps=json.loads(PRESETS.read_bytes()); assert not any(p['id']=='womens-rights' for p in ps)
    p=dict(id='womens-rights',name='Women’s rights',group='Revolutions and modern life',
        period=dict(start=1780,end=2000),context=dict(start=1400,end=2000),
        description='Explore women’s struggles for education, work, political voice and bodily autonomy around the world, including Japan. Campaigns and feminist writing meet art about women’s lives and access to artistic careers.',
        sources=[dict(name=SOURCES[k][0],url=SOURCES[k][1]) for k in ['un','ndl-literature','ndl-vote','nara']],
        startingScope='Global history, including Japan',startingHighlights=False,
        coverArtworkID='ab18c302-3c54-4632-a943-47a61849f344',
        focus=dict(label='A selected global history of women’s rights. Art includes direct advocacy and broader context about education, work and self-representation; inclusion does not make every artist or artwork a campaigner. The timeline ends at the catalogue’s 2000 boundary, not the end of the movement.',
            countries=[],selectedBooks=True,selectedEvents=True,
            related=dict(artwork=[i for i,_ in ARTWORKS],book=BOOK_IDS,event=EXISTING_EVENTS+[e['id'] for e in events]),
            context=dict(artwork=[i for i,_ in CONTEXT_ART])))
    # Insert by period near Enlightenment; preserve every existing preset object.
    idx=next((i for i,v in enumerate(ps) if v['id']=='french-revolution'),len(ps))
    ps.insert(idx,p)
    PRESETS.write_text(json.dumps(ps,ensure_ascii=False,indent=2)+'\n')
    save('preset.json',p)
    print('Added global Women’s rights historical preset.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=['plan','backup','apply','preset'])
    globals()[parser.parse_args().phase]()
