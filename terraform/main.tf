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