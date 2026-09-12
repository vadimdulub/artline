package ingest

import (
	"errors"
	"fmt"
	"strings"
	"time"
)

// Structured dates are permitted only in a checksum-pinned reviewed snapshot.
// Literal source wording remains independently visible; no year is derived from
// a sitter's lifespan, an acquisition date, or a signature without further evidence.
func europeanWorkDate(w europeanWork) (europeanDate, error) {
	if w.CreationDate == nil {
		return europeanCreationDate(w.DateDisplay)
	}
	d := *w.CreationDate
	if strings.TrimSpace(w.DateDisplay) == "" {
		return d, errors.New("missing literal date")
	}
	for _, v := range []*int{d.First, d.Last} {
		if v != nil && (*v < 1100 || *v > 1970) {
			return d, errors.New("structured date outside approved cutoff")
		}
	}
	switch d.Precision {
	case "unknown":
		if d.First != nil || d.Last != nil {
			return d, errors.New("unknown date has invented bounds")
		}
	case "before":
		if d.First != nil || d.Last == nil {
			return d, errors.New("before requires only an exclusive upper bound")
		}
	case "exact", "circa":
		if d.First == nil || d.Last == nil || *d.First != *d.Last {
			return d, errors.New("single year requires equal bounds")
		}
	case "range", "circa_range", "decade", "century":
		if d.First == nil || d.Last == nil || *d.First > *d.Last {
			return d, errors.New("invalid closed interval")
		}
	default:
		return d, fmt.Errorf("unsupported structured precision %s", d.Precision)
	}
	return d, nil
}

func (s europeanImport) details(w europeanWork, id, inst, sid, recordID, note string) (bool, error) {
	if w.UpdatedOn != "" {
		v, e := time.Parse("2006-01-02", w.UpdatedOn)
		if e != nil || v.After(s.checked) {
			return false, errors.New("invalid source modification date")
		}
	}
	var replay bool
	if err := s.tx.QueryRow(s.ctx, `SELECT EXISTS(SELECT 1 FROM import_records WHERE import_job_id=$1 AND source_record_id=$2)`, s.job, recordID).Scan(&replay); err != nil {
		return false, err
	}
	// A cleared field or removed museum selection after this batch is an editorial
	// choice. Replaying the same evidence must not repopulate either.
	if replay {
		return false, nil
	}
	tag, err := s.tx.Exec(s.ctx, `UPDATE artworks SET
 medium_text=coalesce(medium_text,NULLIF($2,'')), dimensions_text=coalesce(dimensions_text,NULLIF($3,'')),
 alternate_title=coalesce(alternate_title,NULLIF($4,'')), accession_number=coalesce(accession_number,NULLIF($5,'')),
 creation_place_display=CASE WHEN creation_place_display IS NULL AND creation_place_unknown_reason='Creation place not established by this research.' THEN NULLIF($6,'') ELSE creation_place_display END,
 creation_place_unknown_reason=CASE WHEN creation_place_display IS NULL AND creation_place_unknown_reason='Creation place not established by this research.' AND $6<>'' THEN NULL ELSE creation_place_unknown_reason END,
 revision=revision+1,updated_at=now(),updated_by=$7
 WHERE id=$1 AND status IN ('draft','review') AND (
 (medium_text IS NULL AND $2<>'') OR (dimensions_text IS NULL AND $3<>'') OR
 (alternate_title IS NULL AND $4<>'') OR (accession_number IS NULL AND $5<>'') OR
 (creation_place_display IS NULL AND creation_place_unknown_reason='Creation place not established by this research.' AND $6<>''))`, id, w.Medium, w.Dimensions, strings.Join(w.Aliases, "; "), w.Accession, w.CreationPlaceText, europeanActor)
	if err != nil {
		return false, err
	}
	evidence := note + " Source material: " + w.Medium + ". Object dimensions: " + w.Dimensions + ". Creation-place metadata (not inferred from subject): " + w.CreationPlaceText + ". Original/alternate titles: " + strings.Join(w.Aliases, "; ") + ". Source publisher: " + w.Publisher + ". Source updated: " + w.UpdatedOn + ". Source date: " + w.DateDisplay + ". Existing nonempty values, title and dates not overwritten."
	if err = s.cite("artwork", id, "research_details", sid, recordID, w.URL, evidence); err != nil {
		return false, err
	}
	if w.MuseumHighlightURL != "" {
		if !europeanAllowedURL(s.batch.Definitions, w.Institution, w.MuseumHighlightURL) {
			return false, errors.New("unapproved museum designation source")
		}
		// Parent collection stays in review. Never add to owner's must-see list.
		t, e := s.tx.Exec(s.ctx, `INSERT INTO curated_collection_items(collection_id,artwork_id,position,reason,source_id,source_url,checked_at)
 SELECT c.id,$1,coalesce((SELECT max(position) FROM curated_collection_items WHERE collection_id=c.id),0)+1,
 'Selected in the museum-authored highlights/masterpieces page; not an independent ranking or current-display claim.',$3,$4,$5
 FROM curated_collections c WHERE c.institution_id=$2 AND c.curator_kind='museum' AND c.status IN ('draft','review')
 AND EXISTS(SELECT 1 FROM artworks a WHERE a.id=$1 AND a.status IN ('draft','review'))
 ON CONFLICT(collection_id,artwork_id) DO NOTHING`, id, inst, sid, w.MuseumHighlightURL, s.checked)
		if e != nil {
			return false, e
		}
		s.report.AddedHighlights += int(t.RowsAffected())
	}
	return tag.RowsAffected() > 0, nil
}
