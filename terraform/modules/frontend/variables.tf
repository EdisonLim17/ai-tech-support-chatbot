variable "root_domain_name" {
  description = "The root domain name"
  type        = string
  default = "edisonlim.ca"
}

variable "subdomain_name" {
  description = "The subdomain name for the frontend"
  type        = string
  default     = "chatbot.edisonlim.ca"
}

variable "origin_id" {
  description = "The origin ID for the CloudFront distribution"
  type        = string
  default     = "s3-chatbot"
}

variable "s3_bucket_name" {
  description = "The name of the S3 bucket for the frontend"
  type        = string
  default     = "aitechsupportchatbot-frontend"
}