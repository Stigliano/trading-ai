# ID del progetto Google Cloud
variable "project_id" {
  description = "ID del progetto Google Cloud"
  type        = string
}

# Regione predefinita per tutte le risorse
variable "region" {
  description = "Regione predefinita"
  type        = string
  default     = "us-central1"
}

# Nome dell'istanza Cloud SQL
variable "db_instance_name" {
  description = "Nome dell'istanza Cloud SQL"
  type        = string
  default     = "trading-ai-db"
}

# Nome utente del database
variable "db_user" {
  description = "Nome utente del database"
  type        = string
  default     = "trading_ai_user"
}

# Password del database (deve essere fornita manualmente o tramite Terraform Cloud)
variable "db_password" {
  description = "Password del database"
  type        = string
  sensitive   = true
}

# Nome del database
variable "db_name" {
  description = "Nome del database"
  type        = string
  default     = "trading_ai_data"
}

# Nome del servizio Cloud Run
variable "cloud_run_service_name" {
  description = "Nome del servizio Cloud Run"
  type        = string
  default     = "trading-ai-service"
}

# Nome del bucket di Cloud Storage
variable "storage_bucket_name" {
  description = "Nome del bucket Cloud Storage"
  type        = string
  default     = "trading-ai-storage"
}

# Nome del repository Artifact Registry
variable "artifact_registry_name" {
  description = "Nome del repository Artifact Registry"
  type        = string
  default     = "trading-ai-repo"
}

# Nome del Cloud Scheduler Job per il trading giornaliero
variable "cloud_scheduler_daily_job" {
  description = "Nome del job di Cloud Scheduler per i dati giornalieri"
  type        = string
  default     = "trading-ai-daily-job"
}

# Nome del Cloud Scheduler Job per il trading intraday
variable "cloud_scheduler_intraday_job" {
  description = "Nome del job di Cloud Scheduler per i dati intraday"
  type        = string
  default     = "trading-ai-intraday-job"
}

