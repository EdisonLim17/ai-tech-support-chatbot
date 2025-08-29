output "sns_topic_arn" {
  description = "The ARN of the SNS topic for escalations"
  value       = aws_sns_topic.escalation_topic.arn
}