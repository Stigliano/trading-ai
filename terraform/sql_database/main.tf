variable "project_id" {
  description = "ID del progetto Google Cloud"
  type        = string
}

variable "region" {
  description = "Regione per il database"
  type        = string
}

variable "db_instance_name" {
  description = "Nome dell'istanza Cloud SQL"
  type        = string
}

variable "db_user" {
  description = "Nome utente del database"
  type        = string
}

variable "db_password" {
  description = "Password del database"
  type        = string
}

variable "db_name" {
  description = "Nome del database"
  type        = string
}

resource "google_sql_database_instance" "trading_ai" {
  name             = var.db_instance_name
  project          = var.project_id
  region           = var.region
  database_version = "POSTGRES_13"  # corretto da MYSQL_8_0

  deletion_protection = false  # aggiunto per permettere la cancellazione

  settings {
    tier = "db-f1-micro"
    ip_configuration {
      ipv4_enabled = true
    }
  }
}

resource "google_sql_user" "trading_ai_user" {
  name     = var.db_user
  instance = google_sql_database_instance.trading_ai.name
  project  = var.project_id
  password = var.db_password
}

resource "google_sql_database" "trading_ai_db" {
  name     = var.db_name
  instance = google_sql_database_instance.trading_ai.name
  project  = var.project_id
}

