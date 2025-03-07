variable "project_id" {
  description = "ID del progetto Google Cloud"
  type        = string
}

variable "region" {
  description = "Regione predefinita per la VM"
  type        = string
}

resource "google_compute_instance" "trading_ai" {
  name         = "trading-ai-instance"
  project      = var.project_id
  zone         = "${var.region}-a"
  machine_type = "n1-standard-2"

  boot_disk {
    initialize_params {
      image = "ubuntu-2004-focal-v20230606"
      size  = 50
      type  = "pd-balanced"
    }
  }

  network_interface {
    network = "default"
    access_config {}
  }
}

