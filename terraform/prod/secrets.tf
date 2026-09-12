resource "google_secret_manager_secret" "database_url" {
  secret_id = "artline-database-url"
  replication {
    auto {}
  }
  depends_on = [google_project_service.required]
}

resource "google_secret_manager_secret_version" "database_url" {
  secret      = google_secret_manager_secret.database_url.id
  secret_data = local.database_url
}

resource "google_secret_manager_secret" "editor_token" {
  secret_id = "artline-editor-token"
  replication {
    auto {}
  }
  depends_on = [google_project_service.required]
}

resource "google_secret_manager_secret_version" "editor_token" {
  secret      = google_secret_manager_secret.editor_token.id
  secret_data = var.editor_token
}
