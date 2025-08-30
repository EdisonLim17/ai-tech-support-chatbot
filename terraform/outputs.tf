output "websocket_api_endpoint" {
  description = "The endpoint of the WebSocket API"
  value       = module.api.websocket_url
}

output "s3_bucket_name" {
  description = "The name of the S3 bucket"
  value       = module.frontend.s3_bucket_name
}

output "cloudfront_distribution_id" {
  description = "The ID of the CloudFront distribution"
  value       = module.frontend.cloudfront_distribution_id
}

output "website_url" {
  description = "The URL of the website"
  value       = module.frontend.website_url
}