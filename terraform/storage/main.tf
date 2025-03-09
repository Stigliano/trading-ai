variable "project_id" {
  description = "ID del progetto Google Cloud"
  type        = string
}

variable "region" {
  description = "Regione per il bucket di storage"
  type        = string
}

resource "google_storage_bucket" "trading_ai" {
  name          = "${var.project_id}-trading-ai-bucket"
  project       = var.project_id
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 365  # Elimina oggetti più vecchi di 1 anno
    }
  }
}


output "storage_bucket_name" {
  value = google_storage_bucket.trading_ai.name
}
