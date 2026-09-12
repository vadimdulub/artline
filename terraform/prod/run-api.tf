resource "google_cloud_run_v2_service" "api" {
  name                 = "artline-api"
  location             = var.region
  deletion_protection  = true
  ingress              = "INGRESS_TRAFFIC_ALL"
  invoker_iam_disabled = true

  template {
    service_account = google_service_account.runtime.email
    annotations = {
      "artline.dev/deploy-nonce" = var.deploy_nonce
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }

    containers {
      image = "${local.image_root}/api:${var.image_tag}"

      ports {
        container_port = 8080
      }

      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.database_url.id
            version = google_secret_manager_secret_version.database_url.version
          }
        }
      }

      env {
        name = "ARTLINE_EDITOR_TOKEN"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.editor_token.id
            version = google_secret_manager_secret_version.editor_token.version
          }
        }
      }

      env {
        name  = "FRONTEND_ORIGIN"
        value = "https://artline.invalid"
      }

      env {
        name  = "ARTLINE_PUBLIC_RESEARCH_PREVIEW"
        value = tostring(var.public_research_preview)
      }

      resources {
        cpu_idle = true
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.artline.connection_name]
      }
    }
  }

  depends_on = [
    google_project_service.required,
    google_project_iam_member.runtime_cloudsql,
    google_secret_manager_secret_iam_member.database_url,
    google_secret_manager_secret_iam_member.editor_token,
    google_sql_database.artline,
    google_sql_user.artline,
  ]
}
