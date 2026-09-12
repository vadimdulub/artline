#!/usr/bin/env sh
set -eu
# Use the active gcloud login without persisting an OAuth token in configuration.
repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
GOOGLE_OAUTH_ACCESS_TOKEN=$(gcloud auth print-access-token)
export GOOGLE_OAUTH_ACCESS_TOKEN
exec terraform -chdir="${repo_root}/terraform/prod" "$@"
