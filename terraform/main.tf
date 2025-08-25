module "iam" {
  source = "./modules/iam"

  dynamodb_table_arn = module.database.dynamodb_table_arn
}

module "database" {
  source = "./modules/database"
}

module "compute" {
  source = "./modules/compute"

  lambda_role_arn = module.iam.lambda_role_arn
}

module "ai" {
  source = "./modules/ai"
}

module "api" {
  source = "./modules/api"

  lambda_function_arn = module.compute.lambda_function.arn
}

module "monitoring" {
  source = "./modules/monitoring"
}