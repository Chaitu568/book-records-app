# main.tf
terraform {
  required_providers {
    heroku = {
      source  = "heroku/heroku"
      version = "~> 5.0"
    }
  }
}

provider "heroku" {}

# Create a new Heroku app
resource "heroku_app" "fastapi_app" {
  name   = var.app_name
  region = var.region

  config_vars = {
    PYTHON_VERSION = "3.10.13"
  }

  buildpacks = [
    "heroku/python"
  ]
}

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