output "image_name" {
  description = "Docker image managed by Terraform"
  value       = docker_image.pipeline.name
}

output "image_id" {
  description = "ID of the Docker image"
  value       = docker_image.pipeline.image_id
}

output "container_name" {
  description = "Name of the Docker container managed by Terraform"
  value       = docker_container.pipeline.name
}

output "container_id" {
  description = "ID of the Docker container"
  value       = docker_container.pipeline.id
}

output "network_name" {
  description = "Docker network the container is attached to"
  value       = docker_network.pipeline.name
}
