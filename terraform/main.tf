
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

# Usando o recurso aws_s3_object
resource "aws_s3_object" "raw_pastas" {
  count  = length(var.raw_folders)
  bucket = aws_s3_bucket.raw.id
  key    = "${var.raw_folders[count.index]}/"
  source = "empty_file" 
  etag   = filemd5("empty_file")
}

resource "aws_s3_bucket" "trusted" {
  bucket = "trusted-analise-voos-grupo2"
}

# Usando o recurso aws_s3_object
resource "aws_s3_object" "trusted_pastas" {
  count  = length(var.trusted_folders)
  bucket = aws_s3_bucket.trusted.id
  key    = "${var.trusted_folders[count.index]}/"
  source = "empty_file"
  etag   = filemd5("empty_file")
}

resource "aws_s3_bucket" "refined" {
  bucket = "refined-analise-voos-grupo2"
}

# Usando o recurso aws_s3_object
resource "aws_s3_object" "refined_pastas" {
  count  = length(var.refined_folders)
  bucket = aws_s3_bucket.refined.id
  key    = "${var.refined_folders[count.index]}/"
  source = "empty_file"
  etag   = filemd5("empty_file")
}

# Variáveis para as pastas
variable "raw_folders" {
  description = "Lista de pastas a serem criadas no bucket raw."
  type        = list(string)
  default     = ["dados_atividade", "dados_voos_atualizados"]
}

variable "trusted_folders" {
  description = "Lista de pastas a serem criadas no bucket trusted."
  type        = list(string)
  default     = ["empresas_aereas", "reclamacoes", "voos"]
}

variable "refined_folders" {
  description = "Lista de pastas a serem criadas no bucket refined."
  type        = list(string)
  default     = ["imagens"]
}