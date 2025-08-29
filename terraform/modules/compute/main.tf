resource "aws_lambda_function" "websocket_handler" {
  function_name = "WebsocketHandler"
  role          = var.lambda_role_arn
  handler       = "websocket_handler.handler"
  runtime       = "python3.13"
  timeout = 15
  filename      = data.archive_file.lambda_zip.output_path

  environment {
    variables = {
      SNS_TOPIC_ARN           = var.sns_topic_arn
    }
  }
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file  = "${path.module}/../../../lambda/websocket_handler.py"
  output_path = "${path.module}/../../../lambda/websocket_handler.zip"
}

resource "aws_lambda_permission" "allow_apigw_invoke" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.websocket_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${var.api_gateway_execution_arn}/*"
}