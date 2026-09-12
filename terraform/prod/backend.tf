terraform {
  backend "gcs" {
    bucket = "artline-508319-terraform-state"
    prefix = "artline/prod"
  }
}
