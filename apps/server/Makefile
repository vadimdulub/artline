.DEFAULT_GOAL := dev

-include .env
export PORT DATABASE_URL FRONTEND_ORIGIN ARTLINE_EDITOR_TOKEN

.PHONY: dev build test migrate fmt

dev:
	go run ./cmd/api

build:
	go build -o bin/artline-api ./cmd/api

test:
	go test ./...

migrate:
	go run ./cmd/migrate

fmt:
	gofmt -w .
