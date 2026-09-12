// Local-only research ledger: human decisions are separate from inventory checks.
package main

import (
	"context"
	"crypto/sha256"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/vadimdulub/artline/apps/server/internal/config"
)

func digest(b []byte) string { return fmt.Sprintf("%x", sha256.Sum256(b)) }
func encode(v any) []byte {
	b, e := json.Marshal(v)
	if e != nil {
		panic(e)
	}
	return b
}
func save(path string, b []byte) error {
	f, e := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if e != nil {
		return e
	}
	_, e = f.Write(b)
	ce := f.Close()
	if e != nil {
		return e
	}
	return ce
}
func main() {
	mode := flag.String("mode", "export", "export or import-greek")
	out := flag.String("out", "", "New, exclusive output directory or import receipt")
	decisions := flag.String("decisions", "", "Reviewed decision JSON; never inferred from existing images")
	input := flag.String("input", "", "Reviewed import manifest")
	pin := flag.String("sha256", "", "Reviewed import SHA256")
	apply := flag.Bool("apply", false, "Apply the selected local import; default is transaction rollback")
	root := flag.String("root", "../..", "Repository root")
	flag.Parse()
	if *out == "" {
		log.Fatal("-out required")
	}
	cfg, e := pgxpool.ParseConfig(config.Load().DatabaseURL)
	if e != nil {
		log.Fatal(e)
	}
	local := func(h string) bool {
		return h == "localhost" || h == "127.0.0.1" || h == "::1" || strings.HasPrefix(h, "/")
	}
	if !local(cfg.ConnConfig.Host) {
		log.Fatal("local database only")
	}
	for _, f := range cfg.ConnConfig.Fallbacks {
		if !local(f.Host) {
			log.Fatal("local database only")
		}
	}
	ctx := context.Background()
	p, e := pgxpool.NewWithConfig(ctx, cfg)
	if e != nil {
		log.Fatal(e)
	}
	defer p.Close()
	switch *mode {
	case "audit-receipts":
		e = auditReceipts(ctx, p, *root, *out)
	case "audit-library":
		e = auditLibrary(ctx, p, *root, *out)
	case "cycle-popular":
		e = runPopularCycle(ctx, p, *root, *out)
	case "export-popular":
		e = exportPopular(ctx, p, *root, *out)
	case "export":
		e = exportLedger(ctx, p, *root, *out, *decisions)
	case "import-greek":
		e = importGreek(ctx, p, *root, *input, *pin, *out, *apply)
	default:
		e = fmt.Errorf("unknown mode")
	}
	if e != nil {
		log.Fatal(e)
	}
}

func newSnapshot(out string) error {
	if e := os.MkdirAll(filepath.Dir(out), 0755); e != nil {
		return e
	}
	// Deliberately refuse an existing snapshot, including interrupted exports.
	return os.Mkdir(out, 0755)
}
