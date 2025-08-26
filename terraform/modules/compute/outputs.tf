output "lambda_function_invoke_arn" {
  description = "The Lambda function"
  value       = aws_lambda_function.websocket_handler.invoke_arn
}