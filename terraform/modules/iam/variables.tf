variable "dynamodb_table_arn" {
  description = "The DynamoDB table"
  type        = string
}

variable "api_gateway_execution_arn" {
  description = "The API Gateway execution ARN for Lambda permission"
  type        = string
}