provider "google" {
  project = "trading-ai-project"
  region  = "us-central1"
}

resource "google_compute_instance" "trading_ai" {
  name         = "trading-ai-instance"
  machine_type = "n1-standard-2"
  zone         = "us-central1-a"

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
