resource "aws_iam_role" "lambda_exec" {
  name = "lambda_exec_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "dynamodb_read_write" {
  name        = "DynamoDBReadWritePolicy"
  description = "IAM policy allowing read/write to the chat history DynamoDB table"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Effect   = "Allow"
        Resource = var.dynamodb_table_arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_dynamodb" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.dynamodb_read_write.arn
}

resource "aws_iam_policy" "bedrock_invoke" {
  name        = "BedrockInvokePolicy"
  description = "IAM policy allowing invoking Amazon Bedrock"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "bedrock:InvokeModel",
          "bedrock:ListFoundationModels"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_bedrock" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.bedrock_invoke.arn
}

resource "aws_iam_policy" "apigw_management" {
  name        = "APIGatewayManagementPolicy"
  description = "IAM policy allowing management of API Gateway connections"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "execute-api:ManageConnections"
        ]
        Effect   = "Allow"
        Resource = "${var.api_gateway_execution_arn}/*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_apigw" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.apigw_management.arn
}

resource "aws_iam_policy" "sns_publish" {
  name        = "SNSPublishPolicy"
  description = "IAM policy allowing publishing to SNS topics"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "sns:Publish"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_sns" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.sns_publish.arn
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}



resource "aws_iam_role" "sns_delivery_status_role" {
  name = "sns_delivery_status_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "sns.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "sns_delivery_status_policy" {
  name        = "SNSDeliveryStatusPolicy"
  description = "IAM policy allowing principal to write delivery status logs to CloudWatch"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "sns_delivery_status" {
  role       = aws_iam_role.sns_delivery_status_role.name
  policy_arn = aws_iam_policy.sns_delivery_status_policy.arn
}