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

        ports {
          container_port = 8080
        }

        resources {
          limits = {
            cpu    = "1"
            memory = "512Mi"
          }
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

output "cloud_run_url" {
  value = google_cloud_run_service.trading_ai.status[0].url
}
