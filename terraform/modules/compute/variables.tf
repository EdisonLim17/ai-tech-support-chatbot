variable "lambda_role_arn" {
  description = "The ARN of the IAM role for Lambda functions"
  type        = string
}

variable "api_gateway_execution_arn" {
  description = "The execution ARN of the API Gateway for setting Lambda permissions"
  type        = string
}