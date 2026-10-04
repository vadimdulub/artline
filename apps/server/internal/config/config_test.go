package config

import (
	"strings"
	"testing"
)

func TestAuthConfiguration(t *testing.T) {
	base := Config{Port: "8080", DatabaseURL: "unused"}
	if err := base.Validate(); err != nil {
		t.Fatal(err)
	}
	base.GoogleClientID = "client"
	if base.Validate() == nil {
		t.Fatal("partial authentication configuration accepted")
	}
	base.GoogleClientSecret = "secret"
	base.AuthCookieKey = strings.Repeat("k", 32)
	for _, origin := range []string{"https://artlines.org", "http://localhost:3000", "http://127.0.0.1:3000"} {
		base.AuthOrigin = origin
		if err := base.Validate(); err != nil {
			t.Fatalf("%s: %v", origin, err)
		}
	}
	for _, origin := range []string{"http://artlines.org", "https://artlines.org/path", "https://user:pass@artlines.org", "https://artlines.org?next=x", "https://artlines.org?", "//artlines.org", "https://artlines.org#fragment"} {
		base.AuthOrigin = origin
		if base.Validate() == nil {
			t.Fatalf("unsafe origin accepted: %s", origin)
		}
	}
}

func TestLocalDebugDefaultsAndProductionBoundary(t *testing.T) {
	for _, key := range []string{"K_SERVICE", "ARTLINE_ENV", "ARTLINE_LOCAL_DEBUG", "ARTLINE_GOOGLE_CLIENT_ID", "ARTLINE_GOOGLE_CLIENT_SECRET", "ARTLINE_AUTH_COOKIE_KEY", "ARTLINE_AUTH_ORIGIN"} {
		t.Setenv(key, "")
	}
	t.Setenv("DATABASE_URL", "postgres://localhost/artline?sslmode=disable")
	t.Setenv("FRONTEND_ORIGIN", "http://localhost:3000")
	cfg := Load()
	if !cfg.LocalDebug || cfg.Validate() != nil || cfg.ListenAddress() != "127.0.0.1:"+cfg.Port {
		t.Fatal("local development must be unlocked and listen only on loopback")
	}
	for _, key := range []string{"K_SERVICE", "ARTLINE_ENV"} {
		t.Run(key, func(t *testing.T) {
			t.Setenv(key, "production")
			if Load().LocalDebug {
				t.Fatal("production automatically enabled local debug")
			}
			t.Setenv("ARTLINE_LOCAL_DEBUG", "true")
			if Load().Validate() == nil {
				t.Fatal("production accepted a forced local-debug flag")
			}
		})
	}
	for _, database := range []string{"postgres://remote.example/artline", "postgres://localhost/artline?host=remote.example", "postgres://localhost/artline?hostaddr=203.0.113.1"} {
		t.Setenv("DATABASE_URL", database)
		if Load().LocalDebug {
			t.Fatal("remote database enabled local debug")
		}
	}
	t.Setenv("DATABASE_URL", "postgres://localhost/artline")
	t.Setenv("FRONTEND_ORIGIN", "https://artlines.org")
	if Load().LocalDebug {
		t.Fatal("public frontend enabled local debug")
	}
	t.Setenv("FRONTEND_ORIGIN", "http://localhost:3000")
	t.Setenv("ARTLINE_LOCAL_DEBUG", "false")
	if Load().LocalDebug {
		t.Fatal("explicit OAuth test opt-out ignored")
	}
}
