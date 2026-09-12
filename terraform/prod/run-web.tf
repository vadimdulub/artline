resource "google_cloud_run_v2_service" "web" {
  name                 = "artline-web"
  location             = var.region
  deletion_protection  = true
  ingress              = "INGRESS_TRAFFIC_ALL"
  invoker_iam_disabled = true

  template {
    service_account = google_service_account.web.email
    annotations = {
      "artline.dev/deploy-nonce" = var.deploy_nonce
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }

    containers {
      image = "${local.image_root}/web:${var.image_tag}"

      ports {
        container_port = 8080
      }

      env {
        name  = "API_INTERNAL_URL"
        value = google_cloud_run_v2_service.api.uri
      }

      env {
        name  = "ARTLINE_IMAGES_BUCKET"
        value = google_storage_bucket.images.name
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
    }
  }

  depends_on = [google_project_service.required, google_storage_bucket_iam_member.images_web]
}
