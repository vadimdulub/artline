package ingest

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

type Options struct {
	Painters, MaxWorks    int
	Root, Run, OnlySource string
	Apply, Images         bool
}
type Report struct {
	Run                                 string `json:"run"`
	Cohort                              int    `json:"cohort"`
	Selected, Created, Existing, Images int
	Reasons                             map[string]int `json:"reasons"`
	PaintersWithSelectedWorks           int            `json:"painters_with_selected_works"`
	Gaps                                []Painter      `json:"painters_without_selected_work_in_this_run"`
	Errors                              []string       `json:"errors"`
	CompletedAt                         time.Time      `json:"completed_at"`
}

func Run(ctx context.Context, pool *pgxpool.Pool, o Options, log func(...any)) (runErr error) {
	if o.Painters < 1 || o.Painters > 1000 || o.MaxWorks < 1 || o.MaxWorks > 10 || !regexp.MustCompile(`^[a-z0-9-]{1,80}$`).MatchString(o.Run) {
		return fmt.Errorf("invalid bounded import options")
	}
	if o.Images && !o.Apply {
		return fmt.Errorf("image downloads require -apply")
	}
	if o.OnlySource != "all" {
		if _, ok := sources[o.OnlySource]; !ok {
			return fmt.Errorf("unknown source")
		}
	}
	if _, e := os.Stat(filepath.Join(o.Root, "AGENTS.md")); e != nil {
		return fmt.Errorf("root must be the Artline project")
	}
	// Serialize owner imports without locking catalogue tables during HTTP calls.
	conn, err := pool.Acquire(ctx)
	if err != nil {
		return err
	}
	defer conn.Release()
	var locked bool
	if err = conn.QueryRow(ctx, `SELECT pg_try_advisory_lock(hashtext('artline-curated-import'))`).Scan(&locked); err != nil {
		return err
	}
	if !locked {
		return fmt.Errorf("another curated import is running")
	}
	defer conn.Exec(context.Background(), `SELECT pg_advisory_unlock(hashtext('artline-curated-import'))`)
	cache := filepath.Join(o.Root, "content", "imports", o.Run, "cache")
	client := NewClient(cache)
	store := Store{pool}
	if o.OnlySource == "prado" {
		return RunPrado(ctx, client, store, o, log)
	}
	if _, ok := reviewedMuseums[o.OnlySource]; ok {
		return RunReviewedMuseum(ctx, client, store, o, log)
	}
	progress := func(s string) { log(s) }
	b, err := client.Get(ctx, PantheonURL, 32<<20)
	if err != nil {
		return err
	}
	painters, err := ReadCohort(b, o.Painters)
	if err != nil {
		return err
	}
	log(fmt.Sprintf("Selected %d painter candidates by Pantheon 2025 HPI; first: %s. Dataset SHA256 %s", len(painters), painters[0].Name, checksum(b)))
	base := fmt.Sprintf("%s:%s:%d:%d:%s", Version, o.Run, o.Painters, o.MaxWorks, checksum(b))
	var cohortJob string
	if o.Apply {
		sid, e := store.Source(ctx, "pantheon")
		if e != nil {
			return e
		}
		cohortJob, err = store.Job(ctx, sid, base+":painters", map[string]any{"dataset": PantheonURL, "sha256": checksum(b), "painters": o.Painters, "attribution": PantheonAttribution})
		if err != nil {
			return err
		}
		for i := range painters {
			if err = store.Painter(ctx, cohortJob, sid, &painters[i]); err != nil {
				store.Finish(context.Background(), cohortJob, "failed", err)
				return err
			}
			if (i+1)%100 == 0 {
				log(fmt.Sprintf("Painter records reconciled: %d/%d", i+1, len(painters)))
			}
		}
		if err = store.Finish(ctx, cohortJob, "needs_review", nil); err != nil {
			return err
		}
	}
	if err = writeNew(filepath.Join(o.Root, "content", "imports", o.Run, "cohort-source.json"), rawJSON(struct {
		Attribution string    `json:"attribution"`
		Painters    []Painter `json:"painters"`
	}{PantheonAttribution, withoutIDs(painters)})); err != nil {
		return err
	}
	if o.OnlySource == "pantheon" {
		return nil
	}
	if o.OnlySource == "wikidata" {
		if !o.Apply {
			return fmt.Errorf("use -apply for bounded Wikidata enrichment of the imported cohort")
		}
		return EnrichWikidata(ctx, client, store, base, painters, progress)
	}
	report := Report{Run: o.Run, Cohort: len(painters), Reasons: map[string]int{}, Errors: []string{}}
	counts := map[string]int{}
	for _, key := range []string{"cleveland", "aic", "met"} {
		if o.OnlySource != "all" && o.OnlySource != key {
			continue
		}
		var sid, job, institution string
		if o.Apply {
			sid, err = store.Source(ctx, key)
			if err != nil {
				return err
			}
			job, err = store.Job(ctx, sid, base+":"+key, map[string]any{"cohort_job": cohortJob, "cutoff": 1970, "highlights_only": true, "max_works_per_painter": o.MaxWorks, "images": o.Images})
			if err != nil {
				return err
			}
			institution, err = store.Institution(ctx, key, sid)
			if err != nil {
				return err
			}
		}
		var works []Work
		switch key {
		case "met":
			works, err = client.Met(ctx, progress)
		case "cleveland":
			works, err = client.Cleveland(ctx, progress)
		case "aic":
			works, err = client.AIC(ctx, progress)
		}
		sourceErr := err
		if sourceErr != nil {
			report.Errors = append(report.Errors, key+": "+err.Error())
			if o.Apply {
				store.Finish(context.Background(), job, "failed", err)
			}
			if ctx.Err() != nil {
				return ctx.Err()
			}
			log("Source paused: ", key, ": ", err)
			if len(works) == 0 {
				continue
			}
		}
		// Deterministic bounded choice among genuine institutional selections, with
		// reusable reproductions preferred. Never label this order a museum ranking.
		sort.Slice(works, func(i, j int) bool {
			if works[i].ImageAllowed() != works[j].ImageAllowed() {
				return works[i].ImageAllowed()
			}
			return works[i].ID < works[j].ID
		})
		seen := map[string]bool{}
		imageFailures := 0
		for _, w := range works {
			if seen[w.ID] {
				continue
			}
			seen[w.ID] = true
			reason := w.Eligible()
			p := MatchPainter(w, painters)
			if reason == "eligible" && p == nil {
				reason = "no_confident_cohort_identity_match"
			}
			if reason == "eligible" && counts[p.QID] >= o.MaxWorks {
				reason = "per_painter_selection_cap"
			}
			if reason != "eligible" {
				report.Reasons[reason]++
				if o.Apply {
					if err = store.Outcome(ctx, job, w, reason); err != nil {
						return err
					}
				}
				continue
			}
			counts[p.QID]++
			report.Selected++
			if !o.Apply {
				continue
			}
			var img *ImageFile
			imageNote := "Image not downloaded; rights are link-only or images mode was not requested."
			if o.Images && w.ImageAllowed() && imageFailures < 3 {
				has, e := store.ExistingMedia(ctx, w)
				if e != nil {
					return e
				}
				if !has {
					file, e := client.DownloadImage(ctx, w, filepath.Join(o.Root, "apps", "web", "public", "assets", "artworks", "imported"))
					if e != nil {
						imageFailures++
						imageNote = e.Error()
						report.Reasons["image_download_failed"]++
						log("Image deferred ", key, ":", w.ID, ": ", e)
					} else {
						imageFailures = 0
						img = &file
						report.Images++
						imageNote = "CC0 image verified against the exact source record and saved locally."
					}
				} else {
					imageNote = "Existing image preserved."
				}
			} else if imageFailures >= 3 && w.ImageAllowed() {
				imageNote = "Image source paused after repeated failures; retry later."
				report.Reasons["image_source_paused"]++
			} else if !w.ImageAllowed() {
				report.Reasons["image_link_only"]++
			}
			created, e := store.Work(ctx, job, sid, institution, *p, w, img, imageNote)
			if e != nil {
				store.Finish(context.Background(), job, "failed", e)
				return e
			}
			if created {
				report.Created++
			} else {
				report.Existing++
			}
			if err = store.Checkpoint(ctx, job, w); err != nil {
				return err
			}
			if report.Selected%10 == 0 {
				log(fmt.Sprintf("Selected %d highlights; %d new records; %d new local images", report.Selected, report.Created, report.Images))
			}
		}
		if o.Apply {
			status := "needs_review"
			if sourceErr != nil {
				status = "failed"
			}
			if err = store.Finish(ctx, job, status, sourceErr); err != nil {
				return err
			}
		}
	}
	for _, p := range painters {
		if counts[p.QID] == 0 {
			report.Gaps = append(report.Gaps, p)
		} else {
			report.PaintersWithSelectedWorks++
		}
	}
	report.CompletedAt = time.Now().UTC()
	// Reports are append-only per execution; the cohort and source snapshots are stable.
	name := "report-" + strings.ReplaceAll(report.CompletedAt.Format("20060102T150405.000000000Z"), ".", "-") + ".json"
	if err = writeNew(filepath.Join(o.Root, "content", "imports", o.Run, name), rawJSON(report)); err != nil {
		return err
	}
	log(fmt.Sprintf("Finished: %d painter candidates; %d selected highlights for %d painters; %d new artworks; %d images. %d source errors. Report: %s", report.Cohort, report.Selected, report.PaintersWithSelectedWorks, report.Created, report.Images, len(report.Errors), name))
	if len(report.Errors) > 0 {
		return fmt.Errorf("partial import: %d source(s) paused; rerun the same command to resume", len(report.Errors))
	}
	return nil
}
func withoutIDs(p []Painter) []Painter {
	out := append([]Painter(nil), p...)
	for i := range out {
		out[i].ID = ""
	}
	return out
}
