terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.92"
    }
  }

  required_version = ">= 1.2"
}

provider "aws" {
  region = "us-east-1"
}


resource "aws_s3_bucket" "raw" {
  bucket = "raw-analise-voos-grupo2"
}

resource "aws_s3_bucket" "trusted" {
  bucket = "trusted-analise-voos-grupo2"
}
resource "aws_s3_bucket" "refined" {
  bucket = "refined-analise-voos-grupo2"
}