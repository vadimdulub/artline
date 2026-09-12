output "web_url" {
  description = "Public Artline web URL"
  value       = google_cloud_run_v2_service.web.uri
}

output "api_url" {
  description = "Public API URL; writes still require the editor bearer token"
  value       = google_cloud_run_v2_service.api.uri
}

output "artifact_repository" {
  description = "Artifact Registry repository root"
  value       = local.image_root
}

output "database_instance" {
  description = "Cloud SQL connection name"
  value       = google_sql_database_instance.artline.connection_name
}

output "images_bucket" {
  value = google_storage_bucket.images.name
}
