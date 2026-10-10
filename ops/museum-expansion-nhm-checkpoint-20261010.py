"""Wave 131: verify and preserve the NHM delivery; the nationwide goal stays active."""
import hashlib
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('delivery', Path(__file__).with_name('museum-expansion-nhm-delivery-20261010.py'))
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)
a, c, m, RUN = d.a, d.c, d.m, d.RUN


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    dest = RUN / 'delivery-checkpoint-001.json'
    assert not dest.exists()
    report = m.load(RUN / 'delivery-001.json')
    checks = m.load(RUN / 'checks-001.json')
    public = m.load(RUN / 'public-delivery-001.json')
    assert report['added'] == 238 and report['existing_links'] == 0 and report['new_images'] == 176
    assert checks['readback_passed'] and checks['replay_zero_writes'] and checks['local_unchanged']
    assert public['public_artwork_samples'] == 6 and public['public_image_hashes_matched'] == 176
    plan, digest = a.validate_plan()
    assert digest == d.EXPECTED and c.ref(c.CP)['sha256'] == c.CP_SHA
    prior = m.load(c.CP)
    oldpins = {x['path']: x for x in prior['artifacts']}
    oldext = {x['path']: x for x in prior['external_artifacts']}
    pins, external = dict(oldpins), dict(oldext)

    def add(pin, target):
        assert pin['path'] not in target or target[pin['path']] == pin, pin['path']
        target[pin['path']] = pin

    paths = {c.CP, a.PLAN, Path(__file__).resolve()}
    paths |= {x for x in RUN.rglob('*') if x.is_file()}
    paths |= {x for x in (m.ROOT / 'ops').glob('*nhm*20261010.py')}
    for path in sorted(paths):
        add(c.ref(path), pins)
    for pin in plan['evidence']:
        add(pin, pins)
    for pin in plan['external_evidence']:
        add(pin, external)
    external_paths = {x for x in c.PROOF.rglob('*') if x.is_file()}
    external_paths |= set(m.BACKUP.glob('nhm-production-*.json*'))
    for path in sorted(external_paths):
        add(dict(path=str(path), sha256=sha(path)), external)
    newpins = [x for x in pins.values() if oldpins.get(x['path']) != x]
    newext = [x for x in external.values() if oldext.get(x['path']) != x]
    for pin in newpins:
        c.checked(pin)
    for pin in newext:
        assert sha(pin['path']) == pin['sha256'], pin['path']
    protected = m.load(RUN / 'protected-production-ids-001.json')['ids']
    assert len(protected) == 2515
    assert set(protected) == set(plan['prior_ids']) | {v['artwork_id'] for v in plan['records'] + plan['holdings']}
    queue = m.load(RUN / 'priority-museum-queue-001.json')
    assert len(queue['rows']) == 225 and not any(x['id'] == c.IID for x in queue['rows'])
    assert sum(x['country_code'] == 'GR' for x in queue['rows']) == 65
    assert report['remaining_pending_total'] == 0

    next_work = """Wave 131 delivered 238 new review artworks, 176 authentic source thumbnails and44 existing James Skene artist links to National Historical Museum, IID5d1bc5d4-0e01-5e7b-8669-1411c393a158. Museum13 catalogue /8 numeric-date eligible /8 primary images ->251 catalogue /184 numeric /184 primary. Catalogue100and200targets reached;62new and5old dates unresolved. No ready NHM candidates remain. Every-museum goal ACTIVE and incomplete. Campaign2491newworks +7existinglinks across15museums; protect2515IDs =2498campaignrecords+17oldKilkisimage-only. Local real database unchanged.

Use ops/museum-expansion-nhm-apply-20261010.py directly for validate_plan and verify. Plan nhm-production-001-plan-001.json.gz SHAab9ccdeceb16b962c6c8cccd67c155e25b4d9074df7a45d082a8686647dcd3a7. Sixteen offline checks, atomic transaction verification, independent readback, zero-write replay,176public image hashes and6public review-artwork samples passed. Backup receipt cloud-backup-001.json must stay pinned. All176new storage objects generation-match=0 and MD5/receipt checked. Preserve78old comparator records and2277priorIDs unchanged; no oldtitles/dates/primaries/statuses/creatorlinks changed. No publication or current-display claims.

Source EIM SearchCulture4727 mixed entries; paintingfacet1006, YEAR_ASC paintingresult580 excludes426undated. First8pages240paintingleads reviewed, including oldPiccarelli1and oldRoux159; append11oldphotocomparators ->251individual source records.238newworks:176explicit caption-dated and62unknown. All251thumbnails and11sourcecontacts reviewed. Eight preparedcontacts reviewed. Nativebridge comparisons establish210SC354572=inventory15153-52,0.42x0.21m,1838, and230SC354589=15153-7,0.30x0.24m,1838-1845 as different physicalworks. Different landscapeviewpoints also distinguish209/239Navarino and233/235Kaisariani. Pitzamanos compositions counted once per catalogued work, not per depicted figure or building; exactalbum/sheet/rectoversocollation remainsunknown.

Dates: native/publication fields with2009/2014fulltimestamps concern digital-record context. Index date often sitter lifespan, event or prototype. Sitterdate numbers2-6,8,9,11-20,23-29,35,36,42,43,67-69,185 remainnull. Event/office/building dates10,21,45,164,167,172,173,186 remainnull.30-32Pelekasis copies afterKallivokas;33,34,165afterHess;174afterGarneray;179,182,183,188-193,196HansHankeafterKollnberger,184copyistunidentifiedafterKollnberger. Prototype1830s notcopydate;1909commission notexactexecution.68Ioannidisattribution tentative. FourIatridisworks168-171 object/nativepages say1824, collectionpaintingnarrative datesfourBotsarisinkworks1828-1832; conflictkeptnumericnull, noimages. Native inventories4542-1,4542-3,4543-.,4542-2 retainedexactly. No inventeduniondate orcopydate.

Only44Skeneviews197-240 linked toexisting0b969b0e-ec3e-5c85-8772-d5768b521db8, JamesSkeneofRubislaw1775-1864,Q4421861. Native2017calendarpublication and GettyULAN500016543 corroborate. Allothermakerlabels retainedunlinked; NikosGeorgiadisnotAndreas, Hankey/SchankerfalsepositivesnotHanke, Hess/Garnerayprototypeartistsnotdirectmakers. Garnerayduplicateauthorities remainunresolved. Bounded reconciliation78artworks/185citations; no establishednewsource/title/accessionduplicates; known6nativeinventorieschecked. ExistingSkeneAberdeenKeratia1841andSwissChristening/Funeral1821distinctsubjects/dates/inventories. Generic titlescheckedonlywithinmaker/source scope; no exhaustiveglobalduplicate or10million-rowperformanceclaim.

All176deliveredimages are authentic380pxwide museum-supplied SearchCulturethumbnails, fullsourceframes, noresize/upscale/crop/retouch/generation.14JPEGsrecompressed;max99508bytes. SourceoriginalTIFFrouteheldafter5HTTP500responses(22,37,38,39,40); neverretriedand remainingwrapperrequestsnotattempted. Prior7wrapper had200,57.0MBTIFF link and3759x5300advertiseddimensions butoriginalnotdownloaded. Tiny256x181previewprobe notdelivered.176higherresolutionimprovements remainagap. MuseumitemCCBYNCND4 conflictswithSCbadge/filewrapperCCBY4; preserveboth, classifyrestricted. SitefooterBYSA notobjectlicense. UserapprovedGreekmuseumimageworkflow recordedseparately,notcopyright-holderlicence. Noimagesforunresolveddates. Originals/proofs/backupsLibraryonly.

Failedresearchstepsimmutable: initialEIMonlyFacetPanelHTTP500; ordinaryobservedpublicadvancedsearch/paintingcontrol worked. Digitalfilewrapperstep5HTTP500 stoppedwith nofinalselected-digital-files-001manifest; digital-file-route-hold-001recordsdecisions. HPS exhibitionhostdirectcaptureConnectionReset54, noHTTP/no retry. First7wrapperDNSfailure resolvedsameURL onceDNSrecovered beforeHTTP; noaccessdenial. ProductionoldproxyPID7614gone causedidentityscriptconnectionrefusedbeforeSQL, thenexistingverifiedcloud-sql-proxy2.26.0startedPID5785port55519--gcloud-auth. Identityquerycompletedread-only: production-identity-001.json.gz at17:26:19Z. Connectionresume receipt retained; subsequentfreshSQLplan/apply/readbackproveconnectivity. Do noteditexecuted/pinnedscriptsoroutputs; correctionsneednewversions.

NEXT War Museum, Athens IIDa4b7823c-f659-5413-9766-60c2306d8844, historical12catalogue/12numeric. Freshproduction/localbaseline beforeobjectreview. Source https://www.searchculture.gr/aggregator/portal/collections/DigWAR?language=en HTTP200,1888mixedentries1501-2017. ObservedGET /aggregator/portal/collections/DigWAR/search; sortSCORE/YEAR_ASC/YEAR_DESC/TITLE. Native https://exhibition.warmuseumdigital.gr/ and https://warmuseum.gr/ observed. First30cards includeart,medals,uniforms,equipment; selectrealart/engraveddecorativeobjects, notadministrativedocumentsorutilitypadding.20th-century1901-2000rangesneedreview,notautomatic1970eligibility. Inspectactualtype/datecontrols, objectversion andcreatorrole beforeimage selection. Greekimages<=1955, catalogue<=1970orunknownreview. Discoveryfile NHMnext-source-discovery-001.json.gz storesrawreceipts,forms,30cardsandnativeURLs forWar,Nikaia,Spathario; noindividualnextmuseumobjects/imagesdownloaded.

Otherdiscovery: Nikaia IID612b52d8-d6b9-5cfe-b068-5caf0d070653,last16works,101sourceentries1924-2016,manypost1970; native https://viewer.app.repo.pinakothiki-nikaiarentis.gr/el/objects. Spathario IIDecc56326-95ff-5063-9e7c-defe30001f0f,last16works,450searchableresultswhiledescription453artifacts,1929-2019; authenticshadowpuppetsmixedold1944/1969andpost1970; native https://karagiozismuseum.gr/. Noneofsourcecounts guarantees100eligibleworks.225inheritedunder100priorityrowsremain,65Greek,notnewglobalcensus. NHM184numeric/67unknown; allremainingobject/date/resolutiongapsrecorded. PriorASFA258/251, AthensCity208/111,Chania192/117,etc inheritpriorcheckpointwithoutrewriting.

Allinheritedproviderholdsremain. ArtUK403,ArCo3timeouts,LombardiaTLS,MuseiReali403,Bristol403/robots/500,Perth3timeouts,LondonPictureArchive403,Smartify403,Salfordrefusal,Glasgow3timeouts,www.rct.uk403,www.iwm.org.uk403,Met429,nga403,watercolourworldrobots,nationalgalleries403,FreiburgAnubis,Brestoeuvres500,ElGrecoBaptism500/Commons403,kazantzaki.grarchive403,anemoyannis.gr403,ejournals.epublishingarticle19335/PDF17357403,zongolopoulos.gr403,collection.zongolopoulos.groneTimeout,Larissa46/67/92native404/SC46nonimage/native7timeout,ChaniaAsklipios403,AIC159136403,Averoffzografiki403,Athensartlion42nonimage. No retriesviaalternatemechanism. AthensnativeSPAclientauthmustnotbeused/printed. NHMnew500andHPSresetrecordedabove.

ProductionproxyPID5785,127.0.0.1:55519--gcloud-auth; leaveitandunrelatedproxiesalone. Localpostgresql://localhost/artline READONLY;nofixtures/testdatabases. Researchvenv/proofs/backupsLibrary/ApplicationSupport/Artline. Noagents,commits,deployment. AGENTSSHAad0d8067ebf9a99e3198d1d6d0c9853e6acdd8932c5a5a0a9e5bb006416d0241. Selectedproductionadditions/imagesauthorized,norepeatedapproval. Fullhistoricalarchiveproofinheriteda0480d7954d528917245e1a8158bcc542078d9346d5aae701a4ace2666ba3205; verifynewpins/relevantsnapshots,notallhistoricalfiles. BroadergoalACTIVE."""

    result = dict(prior)
    result.update(
        at=m.now(), wave=131, goal_complete=False, goal_status='active', previous_goal_turn='progress',
        production_only=True, local_unchanged=True, new_additions=238, new_existing_links=0, new_images=176,
        verification=report['verification'], production_museum_before=report['museum_before'],
        production_museum_after=report['museum_after'], production_campaign_totals=report['production_campaign_totals'],
        global_production_counts_refreshed=False, global_production_thresholds_refreshed=False,
        new_tests_passed=16, plan_sha256=digest, plan_reference=c.ref(a.PLAN),
        prior_checkpoint_reference=c.ref(c.CP), artifacts=list(pins.values()), external_artifacts=list(external.values()),
        baseline_reference=c.ref(RUN / 'baseline-verification-001.json'), review_reference=c.ref(a.REVIEW),
        checks_reference=c.ref(RUN / 'checks-001.json'), public_delivery_reference=c.ref(RUN / 'public-delivery-001.json'),
        production_institution_register_reference=c.ref(RUN / 'production-institution-register-001.json.gz'),
        priority_museum_queue_reference=c.ref(RUN / 'priority-museum-queue-001.json'),
        protected_production_ids_reference=c.ref(RUN / 'protected-production-ids-001.json'),
        pending_candidates={}, pending_candidate_total=0,
        global_threshold_summary_note='Only NHM refreshed:251 catalogue/184 numeric-date eligible. Catalogue200 target reached;225 inherited priority rows remain, not a fresh global census.',
        source_availability=report['source_access'], remaining_research_reference=c.ref(RUN / 'remaining-research-001.json'),
        next_source_discovery_reference=c.ref(RUN / 'next-source-discovery-001.json.gz'),
        preferred_target_remaining=dict(institution_id=c.IID, catalogue=251, gap_to100=0, gap_to200=0, target_reached=True, numeric_eligible=184),
        public_api_date_scope=public['date_scope_note'], next_work=next_work,
    )
    result.pop('previous_research_checkpoint', None)
    m.save(dest, result)
    m.save(RUN / 'final-checkpoint-verification-001.json', dict(
        at=m.now(), checkpoint=c.ref(dest), verified_new_artifact_pins=len(newpins),
        verified_new_external_pins=len(newext), inherited_unchanged_artifact_pins=len(pins)-len(newpins),
        inherited_unchanged_external_pins=len(external)-len(newext),
        full_historical_proof=prior['initial_full_historical_verification_reference'], plan_sha256=digest,
        goal_complete=False, actual_added=238, actual_existing_links=0, actual_images=176,
        protected_production_ids=2515, pending_candidates=0, local_unchanged=True,
    ))
    print(json.dumps(dict(checkpoint=c.ref(dest), artifacts=len(pins), external=len(external),
        verified_new=len(newpins), verified_external=len(newext), added=238, links=0, images=176, pending=0)), flush=True)


if __name__ == '__main__':
    main()
