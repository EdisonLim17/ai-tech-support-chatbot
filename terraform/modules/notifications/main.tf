resource "aws_sns_topic" "escalation_topic" {
  name = "escalation_topic"
}

resource "aws_sns_topic_subscription" "escalation_sms_subscription" {
  topic_arn = aws_sns_topic.escalation_topic.arn
  protocol  = "sms"
  endpoint  = local.phone_number
}

resource "aws_sns_sms_preferences" "default" {
  default_sender_id = "TechSuppBot"

  delivery_status_iam_role_arn = var.sns_delivery_status_role_arn
  delivery_status_success_sampling_rate = 100
  monthly_spend_limit = 1
}

data "aws_secretsmanager_secret_version" "phone_number_secret" {
  secret_id = "arn:aws:secretsmanager:us-east-1:415730361496:secret:personal/PII-NoilGK"
}

locals {
    phone_number = jsondecode(data.aws_secretsmanager_secret_version.phone_number_secret.secret_string)["phone-number"]
}