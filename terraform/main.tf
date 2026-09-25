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
