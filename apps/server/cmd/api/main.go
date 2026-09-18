package main

import (
	"context"
	"errors"
	"flag"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/vadimdulub/artline/apps/server/internal/config"
	"github.com/vadimdulub/artline/apps/server/internal/database"
	"github.com/vadimdulub/artline/apps/server/internal/httpapi"
	"github.com/vadimdulub/artline/apps/server/internal/migrate"
)

func main() {
	skipMigrations := flag.Bool("skip-migrations", false, "Use an existing schema without running migrations (for read-only local previews)")
	flag.Parse()
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))
	slog.SetDefault(logger)

	cfg := config.Load()
	if err := cfg.Validate(); err != nil {
		logger.Error("invalid configuration", "error", err)
		os.Exit(1)
	}

	startupCtx, startupCancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer startupCancel()
	pool, err := database.Open(startupCtx, cfg.DatabaseURL)
	if err != nil {
		logger.Error("database startup failed", "error", err)
		os.Exit(1)
	}
	defer pool.Close()
	if !*skipMigrations {
		if err := migrate.Run(startupCtx, pool); err != nil {
			logger.Error("migration failed", "error", err)
			os.Exit(1)
		}
	}

	server := &http.Server{
		Addr:              ":" + cfg.Port,
		Handler:           httpapi.New(cfg, pool),
		ReadHeaderTimeout: 5 * time.Second,
		ReadTimeout:       15 * time.Second,
		WriteTimeout:      30 * time.Second,
		IdleTimeout:       60 * time.Second,
	}

	shutdownCtx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	go func() {
		<-shutdownCtx.Done()
		ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		if err := server.Shutdown(ctx); err != nil {
			logger.Error("graceful shutdown failed", "error", err)
		}
	}()

	logger.Info("Artline API listening", "port", cfg.Port)
	if err := server.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
		logger.Error("server stopped unexpectedly", "error", err)
		os.Exit(1)
	}
}
