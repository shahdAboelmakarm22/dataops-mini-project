variable "docker_host" {
  description = "Docker Engine endpoint Terraform should talk to"
  type        = string
  default     = "unix:///var/run/docker.sock"
}

variable "image_name" {
  description = "Name of the Docker image for the data pipeline"
  type        = string
  default     = "dataops-pipeline"
}

variable "image_tag" {
  description = "Tag of the Docker image"
  type        = string
  default     = "latest"
}

variable "container_name" {
  description = "Name of the Docker container that runs the pipeline"
  type        = string
  default     = "dataops-pipeline-container"
}
