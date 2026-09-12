resource "google_sql_database_instance" "artline" {
  name             = "artline-postgres"
  region           = var.region
  database_version = "POSTGRES_17"

  deletion_protection = true

  settings {
    edition                     = "ENTERPRISE"
    deletion_protection_enabled = true
    tier                        = var.database_tier
    availability_type           = "ZONAL"
    disk_type                   = "PD_SSD"
    disk_size                   = 10
    disk_autoresize             = true

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
      start_time                     = "03:00"
    }

    ip_configuration {
      ipv4_enabled = true
    }

    database_flags {
      name  = "max_connections"
      value = "100"
    }
  }

  depends_on = [google_project_service.required]
}

resource "google_sql_database" "artline" {
  name     = var.database_name
  instance = google_sql_database_instance.artline.name
}

resource "random_password" "database" {
  length  = 32
  special = true
}

resource "google_sql_user" "artline" {
  name     = var.database_user
  instance = google_sql_database_instance.artline.name
  password = random_password.database.result
}

locals {
  encoded_database_password = urlencode(random_password.database.result)
  database_url              = "postgres://${var.database_user}:${local.encoded_database_password}@/${var.database_name}?host=${urlencode("/cloudsql/${google_sql_database_instance.artline.connection_name}")}&sslmode=disable"
}
