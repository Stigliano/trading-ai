variable "project_id" {
  description = "ID del progetto Google Cloud"
  type        = string
}

variable "region" {
  description = "Regione per il Cloud Scheduler"
  type        = string
}

variable "service_account_email" {
  description = "Email del service account usato dal Cloud Scheduler"
  type        = string
}

variable "cloud_run_url" {
  description = "URL del servizio Cloud Run da chiamare"
  type        = string
}

resource "google_cloud_scheduler_job" "daily_job" {
  name        = "trading-ai-daily-job"
  project     = var.project_id
  region      = var.region
  schedule    = "0 22 * * *"  # Esegue ogni giorno alle 22:00 UTC
  time_zone   = "Etc/UTC"
  description = "Job per eseguire il trading giornaliero"

  http_target {
    uri         = var.cloud_run_url
    http_method = "POST"

    oauth_token {
      service_account_email = var.service_account_email
    }
  }
}

resource "google_cloud_scheduler_job" "intraday_job" {
  name        = "trading-ai-intraday-job"
  project     = var.project_id
  region      = var.region
  schedule    = "0 * * * *"  # Esegue ogni ora UTC
  time_zone   = "Etc/UTC"
  description = "Job per eseguire il trading intraday"

  http_target {
    uri         = var.cloud_run_url
    http_method = "POST"

    oauth_token {
      service_account_email = var.service_account_email
    }
  }
}

