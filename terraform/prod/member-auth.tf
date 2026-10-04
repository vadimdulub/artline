variable "enable_google_signin" {
  description = "Enable member sign-in only after OAuth credentials, secrets, migration and public origin are ready"
  type        = bool
  default     = false
}

variable "google_oauth_client_id" {
  type        = string
  default     = ""
  description = "Google Auth Platform Web application client ID (public identifier)"
}

variable "google_oauth_secret_version" {
  type        = string
  default     = "1"
  description = "Existing Secret Manager version of artline-google-client-secret; secret values stay outside Terraform"
}

variable "auth_cookie_key_version" {
  type        = string
  default     = "1"
  description = "Existing Secret Manager version of artline-auth-cookie-key"
}

resource "google_secret_manager_secret_iam_member" "member_auth" {
  for_each  = var.enable_google_signin ? toset(["artline-google-client-secret", "artline-auth-cookie-key"]) : toset([])
  project   = var.project_id
  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.runtime.email}"
}
