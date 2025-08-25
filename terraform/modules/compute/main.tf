resource "aws_lambda_function" "websocket_handler" {
  function_name = "WebsocketHandler"
  role          = var.lambda_role_arn
  handler       = "index.handler"
  runtime       = "python3.13"
  filename      = data.archive_file.lambda_zip.output_path
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file  = "${path.module}/../../../lambda/websocket_handler.py"
  output_path = "${path.module}/../../../lambda/websocket_handler.zip"
}