output "cloud_run_url" {
  value = module.cloud_run.cloud_run_url
}

output "database_instance_connection" {
  value = module.sql_database.database_instance_connection
}

output "database_public_ip" {
  value = module.sql_database.database_public_ip
}

output "storage_bucket_name" {
  value = module.storage.storage_bucket_name
}
