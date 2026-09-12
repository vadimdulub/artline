resource "google_service_account" "runtime" {
  account_id   = "artline-runtime"
  display_name = "Artline Cloud Run runtime"
}

resource "google_service_account" "web" {
  account_id   = "artline-web"
  display_name = "Artline web runtime (no database or secret access)"
}

resource "google_project_iam_member" "runtime_cloudsql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_secret_manager_secret_iam_member" "database_url" {
  secret_id = google_secret_manager_secret.database_url.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_secret_manager_secret_iam_member" "editor_token" {
  secret_id = google_secret_manager_secret.editor_token.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.runtime.email}"
}
