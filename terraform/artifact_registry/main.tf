variable "project_id" {
  description = "ID del progetto Google Cloud"
  type        = string
}

variable "region" {
  description = "Regione predefinita"
  type        = string
}

resource "google_artifact_registry_repository" "trading_ai" {
  provider      = google
  project       = var.project_id
  location      = var.region
  repository_id = "trading-ai-repo"
  format        = "DOCKER"
}

