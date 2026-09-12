#!/usr/bin/env sh
set -eu

if [ "$#" -ne 3 ]; then
  echo "usage: $0 <gcp-project-id> <region> <image-tag>" >&2
  exit 2
fi

project_id="$1"
region="$2"
image_tag="$3"
image_root="${region}-docker.pkg.dev/${project_id}/artline"
repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

gcloud builds submit "${repo_root}/apps/server" --project "${project_id}" \
  --config "${repo_root}/ops/cloudbuild-api.yaml" \
  --gcs-source-staging-dir "gs://${project_id}-build-source/source" \
  --substitutions "_IMAGE=${image_root}/api:${image_tag}"
gcloud builds submit "${repo_root}/apps/web" --project "${project_id}" \
  --config "${repo_root}/ops/cloudbuild-web.yaml" \
  --gcs-source-staging-dir "gs://${project_id}-build-source/source" \
  --substitutions "_IMAGE=${image_root}/web:${image_tag}"

echo "Built ${image_root}/api:${image_tag}"
echo "Built ${image_root}/web:${image_tag}"
