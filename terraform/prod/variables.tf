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

variable "public_research_preview" {
  description = "Show non-archived research records publicly without publishing them; editor operations remain authenticated"
  type        = bool
  default     = false
}
