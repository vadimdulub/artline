variable "project_id" {
  description = "Google Cloud project ID for Artline production"
  type        = string
}

variable "region" {
  description = "Region for Cloud Run, Artifact Registry, and Cloud SQL"
  type        = string
  default     = "europe-west1"
}

variable "database_name" {
  description = "Application PostgreSQL database"
  type        = string
  default     = "artline"
}

variable "database_user" {
  description = "Application PostgreSQL role"
  type        = string
  default     = "artline_app"
}

variable "database_tier" {
  description = "Cloud SQL machine tier"
  type        = string
  default     = "db-f1-micro"
}

variable "image_tag" {
  description = "Container tag deployed to both services"
  type        = string
  default     = "latest"
}

variable "api_image" {
  description = "Optional API image URI or digest for API-only releases; null uses image_tag"
  type        = string
  default     = null
}

variable "web_image" {
  description = "Optional web image URI or digest for configuration-only or web-only releases; null uses image_tag"
  type        = string
  default     = null
}

variable "editor_token" {
  description = "Long random bearer token for the first-owner editing flow"
  type        = string
  sensitive   = true
  validation {
    condition     = length(var.editor_token) >= 32
    error_message = "Use a production editor token with at least 32 characters."
  }
}

variable "deploy_nonce" {
  description = "Change to force a new Cloud Run revision when reusing an image tag"
  type        = string
  default     = ""
}

variable "site_url" {
  description = "Canonical public HTTPS origin after domain purchase; empty retains the documented Cloud Run origin"
  type        = string
  default     = ""
  validation {
    condition     = var.site_url == "" || can(regex("^https://[a-zA-Z0-9.-]+/?$", var.site_url))
    error_message = "Use an HTTPS origin without a path, query, fragment or credentials."
  }
}

variable "google_site_verification" {
  description = "Public Google Search Console HTML verification token, if using HTML verification"
  type        = string
  default     = ""
}

variable "bing_site_verification" {
  description = "Public Bing Webmaster Tools HTML verification token, if using HTML verification"
  type        = string
  default     = ""
}
