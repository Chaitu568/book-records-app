# variables.tf
variable "app_name" {
  description = "Name of the Heroku application"
  type        = string
}

variable "region" {
  description = "Heroku region"
  type        = string
  default     = "us"
}


# outputs.tf
output "app_url" {
  value       = "https://${heroku_app.fastapi_app.name}.herokuapp.com"
  description = "Application URL"
}