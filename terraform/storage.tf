resource "google_storage_bucket" "trading_ai" {
  name     = "${var.project_id}-trading-ai-bucket"
  location = var.region
}
