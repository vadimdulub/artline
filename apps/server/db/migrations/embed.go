package migrations

import "embed"

// Files contains the append-only SQL migrations applied by the API and CLI.
//
//go:embed *.sql
var Files embed.FS
