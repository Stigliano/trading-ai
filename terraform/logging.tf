resource "google_logging_metric" "error_count" {
  name   = "trading-ai-error-logs"
  filter = "resource.type=\"cloud_run_revision\" severity>=ERROR"
}
