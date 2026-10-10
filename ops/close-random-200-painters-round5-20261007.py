#!/usr/bin/env python3
"""Close this operation's proxy and record the verified production outcome."""
import datetime,hashlib,json,os,signal,subprocess,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'docs/research/random-200-painters-round5-20261007'

def main():
    load=lambda name:json.loads((RUN/name).read_text())
    checked=load('report-verification.json');proof=load('final-verification.json');summary=load('summary.json')
    assert checked['complete'] and summary['complete'] and not checked['errors'] and not proof['errors']
    assert checked['painters']==proof['painters']==200
    assert checked['new_review_records']==proof['new_review_records']==summary['totals']['created']
    assert checked['images_uploaded_and_verified']==proof['images_verified']==summary['totals']['images_added']
    for folder in ['applied','verified']:assert len(list((RUN/folder).glob('*.json')))==200
    assert checked['report_sha256']==hashlib.sha256((RUN/'report.html').read_bytes()).hexdigest()
    pid=load('authentication-resumed.json')['proxy_pid']
    expected='/tmp/artline-release-20261001-evening/cloud-sql-proxy --gcloud-auth --address 127.0.0.1 --port 55474 artline-508319:europe-west1:artline-postgres'
    command=subprocess.run(['ps','-p',str(pid),'-o','command='],capture_output=True,text=True)
    if command.returncode==0:
        assert command.stdout.strip()==expected,'Refuse to stop an unrelated process'
        os.kill(pid,signal.SIGTERM)
        for _ in range(20):
            if subprocess.run(['ps','-p',str(pid),'-o','pid='],capture_output=True).returncode:break
            time.sleep(.25)
    assert subprocess.run(['ps','-p',str(pid),'-o','pid='],capture_output=True).returncode!=0
    totals=summary['totals']
    receipt={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'operation':'random-200-painters-round5-20261007','complete':True,'painters':200,'new_review_records':proof['new_review_records'],'images_uploaded_and_verified':proof['images_verified'],'related_work_leads':totals['related_artwork_leads'],'source_entries':totals['source_entries'],'own_proxy_pid':pid,'own_proxy_port':55474,'own_proxy_stopped':True,'all_new_records_remain_review':True,'local_database_changed':False,'report_verification_sha256':hashlib.sha256((RUN/'report-verification.json').read_bytes()).hexdigest(),'final_proof_sha256':hashlib.sha256((RUN/'final-verification.json').read_bytes()).hexdigest(),'errors':[]}
    target=RUN/'completion-receipt.json';assert not target.exists();target.write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
    text=f'''# Fifth random 200-painter batch

Completed and verified in production on 7 October 2026: **{proof['new_review_records']:,} new artwork review records and {proof['images_verified']:,} images**, covering another 200 painters. The research also records **{totals['related_artwork_leads']:,} related-work leads**.

- [Complete production report](report.html)
- [Selected 200 painters](selected-200-painters.csv)
- [Per-painter outcomes](painters.csv)
- [New artwork records](new-review-records.csv)
- [Uploaded images and source rights](uploaded-images.csv)
- [Every indexed source disposition](source-dispositions.csv)
- [Related-work leads](related-artwork-leads.csv)
- [Final production verification](final-verification.json)
- [Report cross-check](report-verification.json)
- [Completion receipt](completion-receipt.json)

The frozen random cohort excludes Otto Dix and the 800 individual creators covered by the preceding four rounds. Seed: `46ac8ca771e308ebf56c912e205da6a7`. Selection used no popularity or artwork-count weighting. The source pass accounts for all {totals['source_entries']:,} indexed entries and preserves available translated indexes and original retrieval evidence.

Every uploaded image passed decoding, dimensions, aspect-ratio, byte-budget and checksum checks. Each public URL returned the expected image bytes. Review covered 46 contact sheets, eight duplicate pairs and 164 source notes; it does not claim manual viewing of every image. Final verification checked production records, source identifiers, media rights evidence, review notes and every delivered image in the live, bounded painter gallery API.

All new artworks remain in review in the personal owner collection. Existing images, catalogue metadata, creator links, accepted holdings, current-display assertions and publication states were preserved. Concurrent changes by other workflows are recorded separately. Actual WikiArt rights labels remain distinct from user approval. Thirty-nine images were deferred for unresolved object/version/date questions while their named source records were retained in review. Unknown creation dates remain unknown and their images are deferred.

Related-work entries include named subjects, copies, collaborations, existing object-level creator labels and unresolved attribution leads. These are research leads, not automatically validated creator links. The source coverage is not a claim to every artwork or relationship worldwide.

The successful pre-import Cloud SQL backup is `1791368721734`. Originals and recovery snapshots are under the Artline Library data locations, outside Documents; served derivatives retain the full supplied composition and are at most 100,000 bytes. The local database was not modified. The operation's dedicated loopback proxy has been stopped.

A temporary authentication pause was resolved by the user's sign-in confirmation; [the resumption receipt](authentication-resumed.json) preserves that history. [The preflight](production-preflight.json), [source-review decisions](reviewed-source-discrepancies.json), [image holds](manual-image-holds.json) and [identity holds](manual-identity-holds.json) remain available. Current query plans do not establish performance at ten million artworks; large-scale load testing remains separate backend work.
'''
    temp=RUN/'README.md.partial';temp.write_text(text);temp.replace(RUN/'README.md')
    print(json.dumps(receipt),flush=True)

if __name__=='__main__':main()
