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

variable "network_name" {
  description = "Name of the Docker network the container is attached to"
  type        = string
  default     = "dataops-network"
}

variable "pipeline_env" {
  description = "Environment label passed to the container as PIPELINE_ENV"
  type        = string
  default     = "dev"
}

variable "memory_mb" {
  description = "Memory limit for the container (MB)"
  type        = number
  default     = 256
}
