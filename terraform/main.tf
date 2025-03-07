module "cloud_run" {
  source                 = "./cloud_run"
  project_id             = var.project_id
  cloud_run_service_name = var.cloud_run_service_name
  region                 = var.region
}

module "sql_database" {
  source           = "./sql_database"
  project_id       = var.project_id
  db_instance_name = var.db_instance_name
  region           = var.region
  db_user          = var.db_user
  db_password      = var.db_password
  db_name          = var.db_name
}

module "storage" {
  source     = "./storage"
  project_id = var.project_id
  region     = var.region
}
