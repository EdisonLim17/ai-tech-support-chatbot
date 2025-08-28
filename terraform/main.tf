module "iam" {
  source = "./modules/iam"

  dynamodb_table_arn        = module.database.dynamodb_table_arn
  api_gateway_execution_arn = module.api.api_gateway_execution_arn
}

module "database" {
  source = "./modules/database"
}

module "compute" {
  source = "./modules/compute"

  lambda_role_arn           = module.iam.lambda_role_arn
  api_gateway_execution_arn = module.api.api_gateway_execution_arn
}

module "api" {
  source = "./modules/api"

  lambda_function_invoke_arn = module.compute.lambda_function_invoke_arn
}

module "monitoring" {
  source = "./modules/monitoring"
}