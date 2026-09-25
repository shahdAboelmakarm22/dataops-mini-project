terraform {
  required_version = ">= 1.5.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

# Terraform talks to the local Docker Engine.
# Linux/macOS default: unix:///var/run/docker.sock
# Windows (Docker Desktop): npipe:////./pipe/docker_engine
provider "docker" {
  host = var.docker_host
}
