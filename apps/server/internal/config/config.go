package config

import (
	"fmt"
	"os"
	"strings"
)

type Config struct {
	Port                  string
	DatabaseURL           string
	FrontendOrigin        string
	EditorToken           string
	PublicResearchPreview bool
}

func Load() Config {
	return Config{
		Port:                  valueOrDefault("PORT", "8080"),
		DatabaseURL:           valueOrDefault("DATABASE_URL", "postgres://localhost/artline?sslmode=disable"),
		FrontendOrigin:        valueOrDefault("FRONTEND_ORIGIN", "http://localhost:3000"),
		EditorToken:           strings.TrimSpace(os.Getenv("ARTLINE_EDITOR_TOKEN")),
		PublicResearchPreview: strings.TrimSpace(os.Getenv("ARTLINE_PUBLIC_RESEARCH_PREVIEW")) == "true",
	}
}

func (c Config) Validate() error {
	if strings.TrimSpace(c.DatabaseURL) == "" {
		return fmt.Errorf("DATABASE_URL is required")
	}
	if strings.TrimSpace(c.Port) == "" {
		return fmt.Errorf("PORT is required")
	}
	return nil
}

func valueOrDefault(key, fallback string) string {
	if value := strings.TrimSpace(os.Getenv(key)); value != "" {
		return value
	}
	return fallback
}
