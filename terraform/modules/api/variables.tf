variable "websocket_api_name" {
    description = "The name of the WebSocket API"
    type        = string
    default     = "chatbot-websocket-api"
}

variable "lambda_function_arn" {
    description = "The ARN of the Lambda function"
    type        = string
}