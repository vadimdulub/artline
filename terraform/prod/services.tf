locals {
  required_services = toset([
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "iam.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "sqladmin.googleapis.com",
    "storage.googleapis.com",
  ])
}

resource "google_project_service" "required" {
  for_each           = local.required_services
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "artline" {
  location      = var.region
  repository_id = "artline"
  description   = "Artline production containers"
  format        = "DOCKER"

  depends_on = [google_project_service.required]
}

locals {
  image_root = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.artline.repository_id}"
}
