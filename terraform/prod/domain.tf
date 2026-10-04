# Opt-in: this creates billable infrastructure. DNS changes are made in Cloudflare
# only after reviewing the plan and obtaining the assigned static IP output.
variable "enable_custom_domain" {
  description = "Provision a production HTTPS load balancer for artlines.org and www.artlines.org"
  type        = bool
  default     = false
}

resource "google_project_service" "domain_compute" {
  count              = var.enable_custom_domain ? 1 : 0
  project            = var.project_id
  service            = "compute.googleapis.com"
  disable_on_destroy = false
}

resource "google_compute_global_address" "web" {
  count      = var.enable_custom_domain ? 1 : 0
  name       = "artline-web-ip"
  ip_version = "IPV4"
  depends_on = [google_project_service.domain_compute]
}

resource "google_compute_region_network_endpoint_group" "web" {
  count                 = var.enable_custom_domain ? 1 : 0
  name                  = "artline-web-serverless"
  network_endpoint_type = "SERVERLESS"
  region                = var.region
  cloud_run {
    # Existing service name: keep domain provisioning independent of app releases.
    service = "artline-web"
  }
  depends_on = [google_project_service.domain_compute]
}

resource "google_compute_backend_service" "web" {
  count                 = var.enable_custom_domain ? 1 : 0
  name                  = "artline-web-backend"
  protocol              = "HTTP"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  enable_cdn            = true
  cdn_policy {
    cache_mode        = "USE_ORIGIN_HEADERS"
    negative_caching  = false
    serve_while_stale = 0
    cache_key_policy {
      include_host         = true
      include_protocol     = true
      include_query_string = true
    }
  }
  backend {
    group = google_compute_region_network_endpoint_group.web[0].id
  }
}

resource "google_compute_managed_ssl_certificate" "web" {
  count = var.enable_custom_domain ? 1 : 0
  name  = "artline-web-certificate"
  managed {
    domains = ["artlines.org", "www.artlines.org"]
  }
  depends_on = [google_project_service.domain_compute]
}

resource "google_compute_ssl_policy" "web" {
  count           = var.enable_custom_domain ? 1 : 0
  name            = "artline-web-tls"
  profile         = "MODERN"
  min_tls_version = "TLS_1_2"
  depends_on      = [google_project_service.domain_compute]
}

resource "google_compute_url_map" "web" {
  count = var.enable_custom_domain ? 1 : 0
  name  = "artline-web-https"
  default_url_redirect {
    host_redirect          = "artlines.org"
    https_redirect         = true
    strip_query            = false
    redirect_response_code = "MOVED_PERMANENTLY_DEFAULT"
  }
  host_rule {
    hosts        = ["artlines.org"]
    path_matcher = "artline"
  }
  path_matcher {
    name            = "artline"
    default_service = google_compute_backend_service.web[0].id
  }
}

resource "google_compute_target_https_proxy" "web" {
  count            = var.enable_custom_domain ? 1 : 0
  name             = "artline-web-https"
  url_map          = google_compute_url_map.web[0].id
  ssl_certificates = [google_compute_managed_ssl_certificate.web[0].id]
  ssl_policy       = google_compute_ssl_policy.web[0].id
}

resource "google_compute_global_forwarding_rule" "web_https" {
  count                 = var.enable_custom_domain ? 1 : 0
  name                  = "artline-web-https"
  ip_address            = google_compute_global_address.web[0].address
  target                = google_compute_target_https_proxy.web[0].id
  port_range            = "443"
  load_balancing_scheme = "EXTERNAL_MANAGED"
}

resource "google_compute_url_map" "web_http" {
  count = var.enable_custom_domain ? 1 : 0
  name  = "artline-web-http-redirect"
  default_url_redirect {
    host_redirect          = "artlines.org"
    https_redirect         = true
    strip_query            = false
    redirect_response_code = "MOVED_PERMANENTLY_DEFAULT"
  }
  depends_on = [google_project_service.domain_compute]
}

resource "google_compute_target_http_proxy" "web" {
  count   = var.enable_custom_domain ? 1 : 0
  name    = "artline-web-http-redirect"
  url_map = google_compute_url_map.web_http[0].id
}

resource "google_compute_global_forwarding_rule" "web_http" {
  count                 = var.enable_custom_domain ? 1 : 0
  name                  = "artline-web-http"
  ip_address            = google_compute_global_address.web[0].address
  target                = google_compute_target_http_proxy.web[0].id
  port_range            = "80"
  load_balancing_scheme = "EXTERNAL_MANAGED"
}

output "artlines_dns_ipv4" {
  description = "Cloudflare A record content for @ and www; use DNS only for managed certificate issuance and renewal"
  value       = var.enable_custom_domain ? google_compute_global_address.web[0].address : null
}
