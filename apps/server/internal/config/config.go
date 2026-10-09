package config

import (
	"fmt"
	"net"
	"net/url"
	"os"
	"strings"
)

type Config struct {
	Port           string
	DatabaseURL    string
	FrontendOrigin string

	GoogleClientID     string
	GoogleClientSecret string
	AuthCookieKey      string
	AuthOrigin         string
	LocalDebug         bool
}

func Load() Config {
	cfg := Config{
		Port:           valueOrDefault("PORT", "8080"),
		DatabaseURL:    valueOrDefault("DATABASE_URL", "postgres://localhost/artline?sslmode=disable"),
		FrontendOrigin: valueOrDefault("FRONTEND_ORIGIN", "http://localhost:3000"),

		GoogleClientID:     strings.TrimSpace(os.Getenv("ARTLINE_GOOGLE_CLIENT_ID")),
		GoogleClientSecret: strings.TrimSpace(os.Getenv("ARTLINE_GOOGLE_CLIENT_SECRET")),
		AuthCookieKey:      strings.TrimSpace(os.Getenv("ARTLINE_AUTH_COOKIE_KEY")),
		AuthOrigin:         strings.TrimSuffix(strings.TrimSpace(os.Getenv("ARTLINE_AUTH_ORIGIN")), "/"),
	}
	// Native local development is fully unlocked. Cloud/container runtimes must
	// never infer member access from a hostname or a request header.
	local := os.Getenv("K_SERVICE") == "" && os.Getenv("ARTLINE_ENV") != "production" && loopbackURL(cfg.DatabaseURL) && loopbackURL(cfg.FrontendOrigin)
	cfg.LocalDebug = local && os.Getenv("ARTLINE_LOCAL_DEBUG") != "false"
	if os.Getenv("ARTLINE_LOCAL_DEBUG") == "true" {
		cfg.LocalDebug = true
	}
	return cfg
}

func (c Config) Validate() error {
	if strings.TrimSpace(c.DatabaseURL) == "" {
		return fmt.Errorf("DATABASE_URL is required")
	}
	if strings.TrimSpace(c.Port) == "" {
		return fmt.Errorf("PORT is required")
	}
	if c.LocalDebug {
		if os.Getenv("K_SERVICE") != "" || os.Getenv("ARTLINE_ENV") == "production" || !loopbackURL(c.DatabaseURL) || !loopbackURL(c.FrontendOrigin) {
			return fmt.Errorf("local debug requires a local database and frontend and is forbidden in production")
		}
		return nil // Local development does not need Google credentials.
	}
	if c.GoogleClientID != "" || c.GoogleClientSecret != "" || c.AuthCookieKey != "" || c.AuthOrigin != "" {
		if c.GoogleClientID == "" || c.GoogleClientSecret == "" || len(c.AuthCookieKey) < 32 || c.AuthOrigin == "" {
			return fmt.Errorf("Google sign-in requires ARTLINE_GOOGLE_CLIENT_ID, ARTLINE_GOOGLE_CLIENT_SECRET, ARTLINE_AUTH_COOKIE_KEY (at least 32 characters) and ARTLINE_AUTH_ORIGIN")
		}
		u, err := url.Parse(c.AuthOrigin)
		if err != nil || u.Host == "" || u.User != nil || u.Path != "" || u.RawQuery != "" || u.Fragment != "" || u.ForceQuery || (u.Scheme != "https" && !(u.Scheme == "http" && (u.Hostname() == "localhost" || u.Hostname() == "127.0.0.1" || u.Hostname() == "::1"))) {
			return fmt.Errorf("ARTLINE_AUTH_ORIGIN must be an HTTPS origin (HTTP is allowed only on localhost), without a path, query, fragment or credentials")
		}
	}
	return nil
}

func (c Config) ListenAddress() string {
	if c.LocalDebug {
		return net.JoinHostPort("127.0.0.1", c.Port)
	}
	return ":" + c.Port
}

func loopbackURL(raw string) bool {
	u, err := url.Parse(raw)
	if err != nil || u.Hostname() == "" || u.Query().Has("host") || u.Query().Has("hostaddr") {
		return false
	}
	return u.Hostname() == "localhost" || net.ParseIP(u.Hostname()).IsLoopback()
}

func valueOrDefault(key, fallback string) string {
	if value := strings.TrimSpace(os.Getenv(key)); value != "" {
		return value
	}
	return fallback
}
