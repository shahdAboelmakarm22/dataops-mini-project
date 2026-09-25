locals {
  project_root = abspath("${path.module}/..")

  # Files that end up inside the image. If any of them change,
  # Terraform rebuilds the image on the next apply.
  source_files = fileset(local.project_root, "{Dockerfile,requirements.txt,src/**,data/**}")
  source_hash  = sha1(join("", [for f in local.source_files : filesha1("${local.project_root}/${f}")]))
}

# ------------------------------------------------------------------
# Docker image: built from the project's Dockerfile
# ------------------------------------------------------------------
resource "docker_image" "pipeline" {
  name         = "${var.image_name}:${var.image_tag}"
  keep_locally = false

  build {
    context    = local.project_root
    dockerfile = "Dockerfile"
  }

  triggers = {
    source_hash = local.source_hash
  }
}

# ------------------------------------------------------------------
# Docker network (bonus)
# ------------------------------------------------------------------
resource "docker_network" "pipeline" {
  name = var.network_name
}

# ------------------------------------------------------------------
# Docker container: runs the pipeline once using the image above
# ------------------------------------------------------------------
resource "docker_container" "pipeline" {
  name  = var.container_name
  image = docker_image.pipeline.image_id

  # The pipeline is a batch job: it runs, writes output and exits.
  must_run = false
  restart  = "no"

  env = [
    "INPUT_PATH=/app/data/transactions.csv",
    "OUTPUT_DIR=/app/output",
    "PIPELINE_ENV=${var.pipeline_env}",
  ]

  # Resource limits (bonus)
  memory = var.memory_mb

  networks_advanced {
    name = docker_network.pipeline.name
  }

  # Mount the project's output/ folder so results appear on the host (bonus)
  volumes {
    host_path      = "${local.project_root}/output"
    container_path = "/app/output"
  }
}
