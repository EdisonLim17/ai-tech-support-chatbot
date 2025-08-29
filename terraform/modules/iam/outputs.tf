output "lambda_role_arn" {
  description = "The ARN of the IAM role for Lambda functions"
  value       = aws_iam_role.lambda_exec.arn
}

output "sns_delivery_status_role_arn" {
  description = "The ARN of the IAM role for SNS delivery status logging"
  value       = aws_iam_role.sns_delivery_status_role.arn
}