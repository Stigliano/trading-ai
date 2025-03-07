resource "google_cloud_run_service" "trading_ai" {
  name     = var.cloud_run_service_name
  location = var.region

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/trading-ai-service"
      }
    }
  }
}
