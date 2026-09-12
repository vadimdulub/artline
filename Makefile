.PHONY: server migrate test web web-install web-build fmt terraform-check

server:
	cd apps/server && set -a && . ./.env && set +a && go run ./cmd/api

migrate:
	cd apps/server && set -a && . ./.env && set +a && go run ./cmd/migrate

test:
	cd apps/server && go test ./...
	cd apps/web && npm test

web:
	cd apps/web && npm run dev

web-install:
	cd apps/web && npm install

web-build:
	cd apps/web && npm run build

fmt:
	cd apps/server && gofmt -w .
	cd terraform/prod && terraform fmt

terraform-check:
	terraform -chdir=terraform/prod fmt -check
	terraform -chdir=terraform/prod validate

