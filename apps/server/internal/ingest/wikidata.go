package ingest

import (
	"context"
	"fmt"
	"net/url"
	"sort"
	"strings"
)

type wdText struct {
	Value string `json:"value"`
}
type wdClaim struct {
	Rank string `json:"rank"`
	Snak struct {
		Type  string `json:"snaktype"`
		Value struct {
			Value struct {
				ID string `json:"id"`
			} `json:"value"`
		} `json:"datavalue"`
	} `json:"mainsnak"`
}
type wdEntity struct {
	ID           string                      `json:"id"`
	Labels       map[string]wdText           `json:"labels"`
	Descriptions map[string]wdText           `json:"descriptions"`
	Aliases      map[string][]wdText         `json:"aliases"`
	Claims       map[string][]map[string]any `json:"claims"`
}

func wdMovements(e wdEntity) []string {
	seen := map[string]bool{}
	var out []string
	for _, claim := range e.Claims["P135"] {
		if value(claim, "rank") == "deprecated" {
			continue
		}
		snak, _ := claim["mainsnak"].(map[string]any)
		if value(snak, "snaktype") != "value" {
			continue
		}
		dv, _ := snak["datavalue"].(map[string]any)
		v, _ := dv["value"].(map[string]any)
		id := value(v, "id")
		if id != "" && !seen[id] {
			out = append(out, id)
			seen[id] = true
		}
	}
	return out
}

func (c *Client) wdEntities(ctx context.Context, ids []string, props string) (map[string]wdEntity, error) {
	var out struct {
		Entities map[string]wdEntity `json:"entities"`
		Error    any                 `json:"error"`
	}
	u := "https://www.wikidata.org/w/api.php?" + url.Values{"action": {"wbgetentities"}, "ids": {strings.Join(ids, "|")}, "props": {props}, "languages": {"en"}, "format": {"json"}, "maxlag": {"5"}}.Encode()
	if _, err := c.JSON(ctx, u, &out); err != nil {
		return nil, err
	}
	if out.Error != nil {
		return nil, fmt.Errorf("Wikidata API requested pause or returned an error")
	}
	return out.Entities, nil
}

// Short descriptions are source-labelled review text, not generated biographies.
// Never replace existing prose or claim movement/influence editorial review.
func EnrichWikidata(ctx context.Context, c *Client, s Store, base string, painters []Painter, progress func(string)) (runErr error) {
	sid, err := s.Source(ctx, "wikidata")
	if err != nil {
		return err
	}
	job, err := s.Job(ctx, sid, base+":wikidata", map[string]any{"painters": len(painters), "fields": []string{"labels", "aliases", "description", "P135"}, "licence": "CC0"})
	if err != nil {
		return err
	}
	defer func() {
		status := "needs_review"
		if runErr != nil {
			status = "failed"
		}
		s.Finish(context.Background(), job, status, runErr)
	}()
	movementLabels := map[string]string{}
	for start := 0; start < len(painters); start += 50 {
		end := min(start+50, len(painters))
		ids := []string{}
		for _, p := range painters[start:end] {
			ids = append(ids, p.QID)
		}
		entities, err := c.wdEntities(ctx, ids, "labels|descriptions|aliases|claims")
		if err != nil {
			return err
		}
		var movementIDs []string
		for _, id := range ids {
			for _, m := range wdMovements(entities[id]) {
				if _, ok := movementLabels[m]; !ok {
					movementLabels[m] = ""
					movementIDs = append(movementIDs, m)
				}
			}
		}
		sort.Strings(movementIDs)
		for i := 0; i < len(movementIDs); i += 50 {
			batch := movementIDs[i:min(i+50, len(movementIDs))]
			ms, err := c.wdEntities(ctx, batch, "labels")
			if err != nil {
				return err
			}
			for _, id := range batch {
				movementLabels[id] = ms[id].Labels["en"].Value
			}
		}
		for _, p := range painters[start:end] {
			e := entities[p.QID]
			if e.ID != p.QID {
				tx, err := s.Pool.Begin(ctx)
				if err != nil {
					return err
				}
				err = record(ctx, tx, job, p.QID, e, nil, "conflict", "artist", p.ID, "Missing/redirected authority identity; no enrichment applied.")
				if err != nil {
					tx.Rollback(ctx)
					return err
				}
				if err = tx.Commit(ctx); err != nil {
					return err
				}
				continue
			}
			tx, err := s.Pool.Begin(ctx)
			if err != nil {
				return err
			}
			applyErr := func() error {
				if desc := e.Descriptions["en"].Value; desc != "" {
					_, err = tx.Exec(ctx, `UPDATE artists SET biography_md=$2,revision=revision+1,updated_at=now()
 WHERE id=$1 AND status IN ('review','draft') AND created_by='local-curated-import' AND nullif(trim(biography_md),'') IS NULL`, p.ID, desc+".\n\nSource: [Wikidata](https://www.wikidata.org/wiki/"+p.QID+") (CC0). Short authority description; full biography awaits editorial review.")
					if err != nil {
						return err
					}
				}
				aliases := append([]wdText{{e.Labels["en"].Value}}, e.Aliases["en"]...)
				for _, a := range aliases {
					if a.Value == "" || a.Value == p.Name {
						continue
					}
					_, err = tx.Exec(ctx, `INSERT INTO artist_aliases(artist_id,alias,normalized_alias,language_code,alias_type) VALUES($1,$2,$3,'en','alternate') ON CONFLICT DO NOTHING`, p.ID, a.Value, normalize(a.Value))
					if err != nil {
						return err
					}
				}
				movementIDs := wdMovements(e)
				for _, id := range movementIDs {
					label := movementLabels[id]
					if label == "" {
						continue
					}
					var mid string
					err = tx.QueryRow(ctx, `SELECT id::text FROM movements WHERE slug=$1`, slug(label)).Scan(&mid)
					if err != nil {
						palette := []string{"#55705e", "#55798f", "#873d48", "#79629a", "#b56c3f", "#3f7180", "#a14f55"}
						idx := 0
						for _, r := range id {
							idx += int(r)
						}
						err = tx.QueryRow(ctx, `INSERT INTO movements(slug,name,color_hex,status) VALUES($1,$2,$3,'review') ON CONFLICT(slug) DO UPDATE SET slug=EXCLUDED.slug RETURNING id::text`, slug(label), label, palette[idx%len(palette)]).Scan(&mid)
						if err != nil {
							return err
						}
					}
					_, err = tx.Exec(ctx, `INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('movement',$1,'wikidata',$2,$3,$4,now()) ON CONFLICT DO NOTHING`, mid, id, "https://www.wikidata.org/wiki/"+id, sid)
					if err != nil {
						return err
					}
					role := "associated"
					if len(movementIDs) == 1 {
						role = "primary"
					}
					_, err = tx.Exec(ctx, `INSERT INTO artist_movements(artist_id,movement_id,role)
 SELECT $1,$2,CASE WHEN $3='primary' AND NOT EXISTS(SELECT 1 FROM artist_movements WHERE artist_id=$1 AND role='primary') THEN 'primary' ELSE 'associated' END ON CONFLICT DO NOTHING`, p.ID, mid, role)
					if err != nil {
						return err
					}
				}
				_, err = tx.Exec(ctx, `INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)
 SELECT 'artist',$1,'authority_enrichment',$2,$3,$4,'Wikidata CC0: aliases, short description and non-deprecated P135 movement associations. No influence claims inferred. Review required.',now(),'local-curated-import'
 WHERE NOT EXISTS(SELECT 1 FROM citations WHERE entity_type='artist' AND entity_id=$1 AND source_id=$2 AND field_name='authority_enrichment')`, p.ID, sid, p.QID, "https://www.wikidata.org/wiki/"+p.QID)
				if err != nil {
					return err
				}
				return record(ctx, tx, job, p.QID, e, e, "updated", "artist", p.ID, "Source-labelled review enrichment; existing prose/dates/classifications preserved.")
			}()
			if applyErr != nil {
				tx.Rollback(ctx)
				return applyErr
			}
			if err = tx.Commit(ctx); err != nil {
				return err
			}
		}
		progress(fmt.Sprintf("Wikidata descriptions/aliases/movements: %d/%d", end, len(painters)))
	}
	return nil
}
