package ingest

import (
	"context"
	"encoding/json"
	"errors"
	"regexp"

	"github.com/jackc/pgx/v5/pgxpool"
)

const EuropeanDeepSnapshotSHA = "1c871c57b9f02ac05977c0c5b5bcdcb0f20806df4c381ed1db4ab65973c4ca4a"
const EuropeanDeepPath = "docs/research/european-deep-expansion/inventory.json"

func deepEuropeanBatch(data []byte) (europeanBatch, error) {
	b := europeanBatch{SHA: EuropeanDeepSnapshotSHA, Version: "european-deep-research-2026-09-09-v2", Path: EuropeanDeepPath, Schema: 2, Works: 157, Museums: 28}
	if checksum(data) != b.SHA {
		return b, errors.New("unreviewed deep European snapshot: checksum mismatch")
	}
	var m struct {
		Definitions map[string]europeanDefinition
		Painters    map[string]string
	}
	if err := json.Unmarshal(data, &m); err != nil {
		return b, err
	}
	if len(m.Definitions) != b.Museums || len(m.Painters) != 41 {
		return b, errors.New("invalid authority crosswalk")
	}
	for k, v := range m.Painters {
		if k != v || !regexp.MustCompile(`^Q[1-9][0-9]*$`).MatchString(v) {
			return b, errors.New("invalid painter authority")
		}
	}
	b.Definitions, b.Painters = m.Definitions, m.Painters
	return b, nil
}

// ImportEuropeanDeep accepts only this reviewed offline version, never arbitrary
// remote URLs or a live scrape. All mutations remain transactional and review-only.
func ImportEuropeanDeep(ctx context.Context, pool *pgxpool.Pool, data []byte, apply bool) (EuropeanImportReport, error) {
	b, err := deepEuropeanBatch(data)
	if err != nil {
		return EuropeanImportReport{}, err
	}
	return importEuropeanBatch(ctx, pool, data, apply, b)
}
