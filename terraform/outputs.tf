output "cloud_run_url" {
  value = google_cloud_run_service.trading_ai.status[0].url
}

output "database_instance_connection" {
  value = google_sql_database_instance.trading_ai.connection_name
}

output "database_public_ip" {
  value = google_sql_database_instance.trading_ai.public_ip_address
}

output "storage_bucket_name" {
  value = google_storage_bucket.trading_ai.name
}
