variable "project_id" {
  description = "ID del progetto Google Cloud"
  type        = string
}

variable "region" {
  description = "Regione predefinita"
  type        = string
}

variable "cloud_run_service_name" {
  description = "Nome del servizio Cloud Run"
  type        = string
}

resource "google_cloud_run_service" "trading_ai" {
  name     = var.cloud_run_service_name
  location = var.region
  project  = var.project_id

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/trading-ai-service"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

