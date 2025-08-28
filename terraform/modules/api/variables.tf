variable "websocket_api_name" {
    description = "The name of the WebSocket API"
    type        = string
    default     = "chatbot-websocket-api"
}

variable "lambda_function_invoke_arn" {
    description = "The invocation ARN of the Lambda function"
    type        = string
}