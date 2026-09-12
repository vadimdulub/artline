package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

const nationalmuseumMonetID = "2c50d912-d5c0-45c3-aad0-cd3bbf300e7a"
const nationalmuseumMonetURL = "https://collection.nationalmuseum.se/en/collection/item/19182/"
const nationalmuseumMonetCapture = "901099fe2967569ff0878c6884a5c63f457ca39116aae4fc067a07afa09f1207"
const nationalmuseumDateRecord = "nationalmuseum-date-review:19182:20260911"

func nationalmuseumItem(b []byte) (map[string]any, error) {
	matches := regexp.MustCompile(`<script id="__NEXT_DATA__" type="application/json">([\s\S]*?)</script>`).FindAllSubmatch(b, -1)
	if len(matches) != 1 {
		return nil, errors.New("ambiguous catalogue payload")
	}
	var doc map[string]any
	if err := json.Unmarshal(matches[0][1], &doc); err != nil {
		return nil, err
	}
	return obj(obj(obj(obj(doc["props"])["pageProps"])["data"])["item"]), nil
}

func validateNationalmuseumMonet(r map[string]any) error {
	if str(r, "Id") != "19182" || str(r, "ObjTitleMainTxt") != "View over the Sea" || str(r, "ObjInventoryNumberTxt") != "NM 2122" || str(r, "ObjFromYearTxt") != "1882" || str(r, "ObjToYearTxt") != "1882" || str(r, "ObjDateGroupTxt") != "Signed: Signed 1882" {
		return errors.New("museum identity/date changed")
	}
	creators, _ := obj(r["ObjPersonRef"])["Items"].([]any)
	if len(creators) != 1 || str(obj(creators[0]), "ReferencedId") != "7713" || str(obj(creators[0]), "LinkLabelTxt") != "Claude Monet (1840 - 1926)" || str(obj(obj(creators[0])["RoleVoc"]), "LabelTxt") != "Artist" {
		return errors.New("creator attribution changed")
	}
	// Signature alone was previously, correctly deferred. Require the independent
	// museum narrative explicitly linking this painting's creation to 1882.
	if !strings.Contains(str(r, "ObjDescriptionTxt_sv"), "In 1882, he went to the port town of Pourville, where he made this painting.") {
		return errors.New("signature alone does not establish creation date")
	}
	return nil
}

func reviewNationalmuseumDate(ctx context.Context, p *pgxpool.Pool, root, out string, apply bool) error {
	file := filepath.Join(root, "content/imports/popular-nationalmuseum-20260911/19182.html")
	b, err := os.ReadFile(file)
	if err != nil {
		return err
	}
	if hash(b) != nationalmuseumMonetCapture {
		return errors.New("unreviewed source capture")
	}
	sb, err := os.ReadFile(file + ".snapshot.json")
	if err != nil {
		return err
	}
	var snap struct {
		URL string
		SHA string    `json:"sha256"`
		At  time.Time `json:"retrieved_at"`
	}
	if err = json.Unmarshal(sb, &snap); err != nil {
		return err
	}
	if snap.URL != nationalmuseumMonetURL || snap.SHA != hash(b) || time.Since(snap.At) > 24*time.Hour || time.Until(snap.At) > 5*time.Minute {
		return errors.New("stale or mismatched source evidence")
	}
	r, err := nationalmuseumItem(b)
	if err != nil {
		return err
	}
	if err = validateNationalmuseumMonet(r); err != nil {
		return err
	}
	if err = os.MkdirAll(filepath.Dir(out), 0755); err != nil {
		return err
	}
	receipt, err := os.OpenFile(out, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if err != nil {
		return err
	}
	defer receipt.Close()
	tx, err := p.Begin(ctx)
	if err != nil {
		return err
	}
	defer tx.Rollback(ctx)
	var replay bool
	if err = tx.QueryRow(ctx, "SELECT EXISTS(SELECT 1 FROM citations WHERE entity_id=$1 AND source_record_id=$2 AND field_name='creation_date')", nationalmuseumMonetID, nationalmuseumDateRecord).Scan(&replay); err != nil {
		return err
	}
	if replay {
		return json.NewEncoder(receipt).Encode(map[string]any{"applied": false, "outcome": "already reviewed; later editorial changes preserved"})
	}
	var fingerprint, sid string
	if err = tx.QueryRow(ctx, `SELECT md5(to_jsonb(a)::text),e.source_id::text FROM artworks a JOIN external_identifiers e ON e.entity_id=a.id AND e.entity_type='artwork'
 WHERE a.id=$1 AND e.scheme='european-nationalmuseum-object' AND e.external_id='NM 2122' AND e.canonical_url=$2
 AND EXISTS(SELECT 1 FROM artwork_artists aa JOIN artists p ON p.id=aa.artist_id JOIN artist_discovery_selection d ON d.artist_id=p.id AND d.is_popular WHERE aa.artwork_id=a.id AND aa.attribution_role='primary' AND p.display_name='Claude Monet')
 AND (SELECT count(*) FROM artwork_artists aa WHERE aa.artwork_id=a.id)=1
 FOR UPDATE OF a`, nationalmuseumMonetID, nationalmuseumMonetURL).Scan(&fingerprint, &sid); err != nil {
		return err
	}
	if fingerprint != "49791ffe16798913a0836be7b559c83e" {
		return errors.New("record changed since review; no automatic overwrite")
	}
	note := "Nationalmuseum object 19182, inventory NM 2122: the museum's descriptive text explicitly identifies creation in Pourville in 1882, independently of the signature date. Reviewed 2026-09-11. Source HTML SHA256 " + nationalmuseumMonetCapture + ". Existing signature wording and editorial description preserved; no image or current-display assertion added."
	if apply {
		if _, err = tx.Exec(ctx, `UPDATE artworks SET creation_year_start=1882,creation_year_end=1882,date_precision='exact',revision=revision+1,updated_at=now(),updated_by='local-european-research' WHERE id=$1`, nationalmuseumMonetID); err != nil {
			return err
		}
		if _, err = tx.Exec(ctx, `INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,page_or_locator,evidence_note,retrieved_at,created_by)
 VALUES('artwork',$1,'creation_date',$2,$3,$4,'ObjDescriptionTxt_sv: bilingual museum description',$5,$6,'local-european-research')`, nationalmuseumMonetID, sid, nationalmuseumDateRecord, nationalmuseumMonetURL, note, snap.At); err != nil {
			return err
		}
		if err = tx.Commit(ctx); err != nil {
			return err
		}
	}
	fmt.Printf("Monet creation-date review: apply=%t, 1882; existing description/signature wording preserved.\n", apply)
	return json.NewEncoder(receipt).Encode(map[string]any{"applied": apply, "artwork_id": nationalmuseumMonetID, "year": 1882, "source_url": nationalmuseumMonetURL, "source_sha256": nationalmuseumMonetCapture, "evidence": note})
}
