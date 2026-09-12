package main

import (
	"github.com/jackc/pgx/v5"
	"testing"
)

func TestExplicitCloudTarget(t *testing.T) {
	c, e := pgx.ParseConfig("postgres://artline_app@127.0.0.1:55432/artline?sslmode=disable")
	if e != nil {
		t.Fatal(e)
	}
	if validateTarget("local", c) == nil {
		t.Fatal("cloud proxy accepted as local")
	}
	if e = validateTarget("cloud-sql-proxy", c); e != nil {
		t.Fatal(e)
	}
	c.Database = "other"
	if validateTarget("cloud-sql-proxy", c) == nil {
		t.Fatal("wrong database accepted")
	}
}
