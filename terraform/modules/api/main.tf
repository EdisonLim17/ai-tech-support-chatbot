resource "aws_apigatewayv2_api" "websocket_api" {
  name          = var.websocket_api_name
  protocol_type = "WEBSOCKET"
  route_selection_expression = "$request.body.action"
}

resource "aws_apigatewayv2_stage" "websocket_stage" {
  api_id      = aws_apigatewayv2_api.websocket_api.id
  name        = "prod"
  auto_deploy = true
}

resource "aws_apigatewayv2_integration" "websocket_integration" {
  api_id             = aws_apigatewayv2_api.websocket_api.id
  integration_type   = "AWS_PROXY"
  integration_uri    = var.lambda_function_arn
  integration_method = "POST"
  content_handling_strategy = "CONVERT_TO_TEXT"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "connect_route" {
  api_id    = aws_apigatewayv2_api.websocket_api.id
  route_key = "$connect"
  target = "integrations/${aws_apigatewayv2_integration.websocket_integration.id}"
}

resource "aws_apigatewayv2_route" "disconnect_route" {
  api_id    = aws_apigatewayv2_api.websocket_api.id
  route_key = "$disconnect"
  target = "integrations/${aws_apigatewayv2_integration.websocket_integration.id}"
}

resource "aws_apigatewayv2_route" "message_route" {
  api_id    = aws_apigatewayv2_api.websocket_api.id
  route_key = "sendMessage"
  target = "integrations/${aws_apigatewayv2_integration.websocket_integration.id}"
}